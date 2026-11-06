"""Revision step 5: retrieval snapshot record/replay (C4, 9.1). Tools are mocked."""
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
os.environ["VIRTUAL_LAB_PROMPTS_DIR"] = str(ROOT / "prompts_A")

from utils import retrieval_snapshot as rs  # noqa: E402
from utils.errors import SearchError  # noqa: E402


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    rs.reset()
    for k in ("VIRTUAL_LAB_RETRIEVAL_MODE", "VIRTUAL_LAB_RETRIEVAL_SNAPSHOT"):
        monkeypatch.setenv(k, "x")
        monkeypatch.delenv(k)
    yield
    rs.reset()


def _tool(result="RESULT", name="web_search"):
    t = MagicMock()
    t.name = name
    t.invoke.return_value = result
    return t


def test_live_mode_calls_tool_every_time():
    t = _tool()
    assert rs.retrieve("critic_web", t, "q") == "RESULT"
    assert rs.retrieve("critic_web", t, "q") == "RESULT"
    assert t.invoke.call_count == 2


def test_record_then_replay(tmp_path, monkeypatch):
    snap = tmp_path / "snap.json"
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_SNAPSHOT", str(snap))
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_MODE", "record")
    t = _tool("fixed text")
    assert rs.retrieve("critic_web", t, "q") == "fixed text"
    assert rs.retrieve("critic_web", t, "q") == "fixed text"      # reused, not re-queried
    assert t.invoke.call_count == 1
    entry = json.loads(snap.read_text(encoding="utf-8"))["entries"]["critic_web"]
    assert entry["query"] == "q" and entry["result"] == "fixed text" and entry["empty"] is False

    rs.reset()
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_MODE", "replay")
    live = _tool("SHOULD NOT BE USED")
    before = snap.read_bytes()
    assert rs.retrieve("critic_web", live, "q") == "fixed text"
    live.invoke.assert_not_called()
    assert snap.read_bytes() == before                             # replay never writes
    info = rs.info()
    assert info["mode"] == "replay" and info["keys_used"] == ["critic_web"] and info["sha256"]


def test_empty_result_is_recorded_as_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_SNAPSHOT", str(tmp_path / "s.json"))
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_MODE", "record")
    assert rs.retrieve("specialist_efsa", _tool(""), "q") == ""
    rs.reset()
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_MODE", "replay")
    assert rs.retrieve("specialist_efsa", _tool("x"), "q") == ""   # empty, not missing


def test_replay_missing_key_or_file_or_query_fails(tmp_path, monkeypatch):
    snap = tmp_path / "s.json"
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_SNAPSHOT", str(snap))
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_MODE", "replay")
    with pytest.raises(SearchError):                               # no file
        rs.retrieve("critic_web", _tool(), "q")
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_MODE", "record")
    rs.reset()
    rs.retrieve("critic_web", _tool(), "q")
    rs.reset()
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_MODE", "replay")
    with pytest.raises(SearchError):                               # missing key
        rs.retrieve("pi_final_web", _tool(), "q")
    with pytest.raises(SearchError):                               # different query (topic changed)
        rs.retrieve("critic_web", _tool(), "another query")


def test_record_failure_is_not_stored(tmp_path, monkeypatch):
    snap = tmp_path / "s.json"
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_SNAPSHOT", str(snap))
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_MODE", "record")
    t = _tool()
    t.invoke.side_effect = SearchError("down")
    with pytest.raises(SearchError):
        rs.retrieve("critic_web", t, "q")
    assert not snap.exists()


def test_unknown_key_and_mode_rejected(monkeypatch):
    with pytest.raises(SearchError):
        rs.retrieve("other", _tool(), "q")
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_MODE", "sometimes")
    with pytest.raises(ValueError):
        rs.mode()


def test_agents_use_snapshot_keys(tmp_path, monkeypatch):
    """Critic and PI read their context from the snapshot in replay mode."""
    from agents import critic as critic_mod
    snap = tmp_path / "s.json"
    snap.write_text(json.dumps({"format_version": 1, "entries": {
        "critic_web": {"key": "critic_web", "query": critic_mod.disambiguate("t", "regulatory verification"),
                       "result": "SNAPSHOT CONTEXT"}}}), encoding="utf-8")
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_SNAPSHOT", str(snap))
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_MODE", "replay")
    seen = {}
    roles = ["Alpha Specialist"]
    valid = json.dumps({"scores": {"Alpha Specialist": {a: 4 for a in critic_mod.SCORE_AXES}},
                        "specialist_feedback": {"Alpha Specialist": "fb"}})

    def fake(system, user, tag=None):
        seen["user"] = user
        return valid

    state = {"topic": "t", "current_round": 1, "team": [{"role": r, "focus": "f"} for r in roles],
             "specialist_outputs": [{"role": r, "focus": "f", "output": "x"} for r in roles],
             "meeting_history": [], "messages": [], "critic_score_history": []}
    with patch.object(critic_mod, "web_search") as ws, patch.object(critic_mod, "call_critic", side_effect=fake):
        critic_mod.run_critic(state)
    ws.invoke.assert_not_called()
    assert "SNAPSHOT CONTEXT" in seen["user"]


def test_run_refuses_replay_without_snapshot(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith("VIRTUAL_LAB_")}
    r = subprocess.run([sys.executable, "run_experiment.py", "--condition", "A", "--run-id", "x",
                        "--out-dir", str(tmp_path), "--retrieval-snapshot", str(tmp_path / "none.json")],
                       cwd=ROOT, env=env, capture_output=True, text=True)
    assert r.returncode != 0 and "retrieval snapshot not found" in r.stderr
    assert not (tmp_path / "A_x").exists()                         # nothing created, attempt can be rerun


# ---------- review follow-ups ----------

def _write_snapshot(path, entries):
    path.write_text(json.dumps({"format_version": 1, "entries": {
        k: {"key": k, "query": q, "result": r} for k, (q, r) in entries.items()}}), encoding="utf-8")


def test_specialist_round1_reads_three_keys(tmp_path, monkeypatch):
    from agents import scientist as sci
    snap = tmp_path / "s.json"
    _write_snapshot(snap, {
        "specialist_rag": (sci.disambiguate("t", "safety assessment"), "RAG TEXT"),
        "specialist_web": (sci.disambiguate("t", "regulation 2025"), "WEB TEXT"),
        "specialist_efsa": (sci.disambiguate("t", "EFSA opinion"), "EFSA TEXT"),
    })
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_SNAPSHOT", str(snap))
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_MODE", "replay")
    with patch.object(sci, "rag_search_tool") as r, patch.object(sci, "web_search") as w, \
         patch.object(sci, "efsa_search") as e:
        rag, web, efsa = sci._perform_searches("t", {"current_round": 1})
    for m in (r, w, e):
        m.invoke.assert_not_called()
    assert "RAG TEXT" in rag and "WEB TEXT" in web and "EFSA TEXT" in efsa
    assert sorted(rs.info()["keys_used"]) == ["specialist_efsa", "specialist_rag", "specialist_web"]


@pytest.mark.parametrize("cached,expected_key", [("CACHED EFSA", None), ("", "pi_final_efsa")])
def test_pi_final_efsa_branches(tmp_path, monkeypatch, cached, expected_key):
    from agents import pi as pi_mod
    snap = tmp_path / "s.json"
    _write_snapshot(snap, {
        "pi_final_web": (pi_mod.disambiguate("t", "safety framework 2025"), "PI WEB"),
        "pi_final_efsa": (pi_mod.disambiguate("t", "EFSA opinion"), "PI EFSA"),
    })
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_SNAPSHOT", str(snap))
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_MODE", "replay")
    seen = {}

    def fake(system, user, **kw):
        seen["user"] = user
        return "REPORT"

    state = {"topic": "t", "meeting_history": [], "current_round": 1, "messages": [], "specialist_outputs": [],
             "sources": [], "critic_score_history": [], "cached_efsa_context": cached}
    with patch.object(pi_mod, "call_gpt", side_effect=fake):
        pi_mod.run_final_synthesis(state)
    used = rs.info()["keys_used"]
    assert "pi_final_web" in used and ("pi_final_efsa" in used) == (expected_key is not None)
    assert ("PI EFSA" in seen["user"]) == (expected_key is not None)


def test_critic_uses_same_context_every_round(tmp_path, monkeypatch):
    from agents import critic as critic_mod
    snap = tmp_path / "s.json"
    _write_snapshot(snap, {"critic_web": (critic_mod.disambiguate("t", "regulatory verification"), "FIXED")})
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_SNAPSHOT", str(snap))
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_MODE", "replay")
    for _ in range(3):
        assert rs.retrieve("critic_web", _tool("LIVE"), critic_mod.disambiguate("t", "regulatory verification")) == "FIXED"


@pytest.mark.parametrize("bad", [
    {"format_version": 1, "entries": {"critic_web": {"query": "q", "result": None}}},
    {"format_version": 1, "entries": {"unknown_key": {"query": "q", "result": "r"}}},
    {"format_version": 2, "entries": {}},
    {"format_version": 1},
])
def test_malformed_snapshot_rejected(tmp_path, monkeypatch, bad):
    snap = tmp_path / "s.json"
    snap.write_text(json.dumps(bad), encoding="utf-8")
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_SNAPSHOT", str(snap))
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_MODE", "replay")
    with pytest.raises(SearchError):
        rs.retrieve("critic_web", _tool(), "q")


def test_snapshot_removed_after_load_is_not_reused(tmp_path, monkeypatch):
    snap = tmp_path / "s.json"
    _write_snapshot(snap, {"critic_web": ("q", "R")})
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_SNAPSHOT", str(snap))
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_MODE", "replay")
    assert rs.retrieve("critic_web", _tool(), "q") == "R"
    snap.unlink()
    with pytest.raises(SearchError):
        rs.retrieve("critic_web", _tool(), "q")


def test_record_queries_each_key_once_under_concurrency(tmp_path, monkeypatch):
    import threading
    import time as _time
    from concurrent.futures import ThreadPoolExecutor
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_SNAPSHOT", str(tmp_path / "s.json"))
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_MODE", "record")
    calls = {"n": 0}
    lock = threading.Lock()

    def slow(_args):
        with lock:
            calls["n"] += 1
            n = calls["n"]
        _time.sleep(0.05)
        return f"result {n}"

    t = _tool()
    t.invoke.side_effect = slow
    with ThreadPoolExecutor(8) as ex:
        results = list(ex.map(lambda _: rs.retrieve("critic_web", t, "q"), range(8)))
    assert calls["n"] == 1 and len(set(results)) == 1


# ---------- build script ----------

def _build_tools(fail_key=None):
    def make(kind):
        t = MagicMock()
        t.name = kind

        def inv(args):
            if fail_key and kind == fail_key:
                raise SearchError("down")
            return f"{kind}:{args['query'][:10]}"
        t.invoke.side_effect = inv
        return t
    return {"rag": make("rag"), "web": make("web"), "efsa": make("efsa")}


def test_build_records_six_keys(tmp_path, monkeypatch):
    sys.path.insert(0, str(ROOT / "scripts" / "revision"))
    import build_retrieval_snapshot as b
    out = tmp_path / "snap.json"
    digest = b.build(out, "t", tools=_build_tools())
    data = json.loads(out.read_text(encoding="utf-8"))
    assert sorted(data["entries"]) == sorted(rs.KEYS) and data["build"]["topic"] == "t" and len(digest) == 64
    assert not out.with_name(out.name + ".lock").exists() and not out.with_name(out.name + ".building").exists()
    with pytest.raises(SystemExit):                       # never overwritten
        b.build(out, "t", tools=_build_tools())


def test_build_failure_leaves_nothing(tmp_path, monkeypatch):
    sys.path.insert(0, str(ROOT / "scripts" / "revision"))
    import build_retrieval_snapshot as b
    out = tmp_path / "snap.json"
    with pytest.raises(SearchError):
        b.build(out, "t", tools=_build_tools(fail_key="efsa"))
    assert not out.exists() and not out.with_name(out.name + ".building").exists()
    assert not out.with_name(out.name + ".lock").exists()


def test_build_refuses_when_locked(tmp_path, monkeypatch):
    sys.path.insert(0, str(ROOT / "scripts" / "revision"))
    import build_retrieval_snapshot as b
    out = tmp_path / "snap.json"
    out.with_name(out.name + ".lock").write_text("busy")
    with pytest.raises(SystemExit):
        b.build(out, "t", tools=_build_tools())
    assert not out.exists()


def test_run_critic_multiple_rounds_injects_same_context(tmp_path, monkeypatch):
    from agents import critic as critic_mod
    snap = tmp_path / "s.json"
    _write_snapshot(snap, {"critic_web": (critic_mod.disambiguate("t", "regulatory verification"), "FIXED CTX")})
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_SNAPSHOT", str(snap))
    monkeypatch.setenv("VIRTUAL_LAB_RETRIEVAL_MODE", "replay")
    roles = ["Alpha Specialist"]
    valid = json.dumps({"scores": {"Alpha Specialist": {a: 4 for a in critic_mod.SCORE_AXES}},
                        "specialist_feedback": {"Alpha Specialist": "fb"}})
    prompts = []

    def fake(system, user, tag=None):
        prompts.append(user)
        return valid

    with patch.object(critic_mod, "web_search") as ws, patch.object(critic_mod, "call_critic", side_effect=fake):
        for rnd in (1, 2, 3):
            critic_mod.run_critic({"topic": "t", "current_round": rnd, "team": [{"role": r, "focus": "f"} for r in roles],
                                   "specialist_outputs": [{"role": r, "focus": "f", "output": "x"} for r in roles],
                                   "meeting_history": [], "messages": [], "critic_score_history": []})
    ws.invoke.assert_not_called()
    assert len(prompts) == 3 and all("FIXED CTX" in p for p in prompts)
