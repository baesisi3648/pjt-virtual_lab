"""Revision step 3: additional fail-closed tests requested in review (C13, C12, C14, C15, C18)."""
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
os.environ["VIRTUAL_LAB_PROMPTS_DIR"] = str(ROOT / "prompts_A")

from agents import pi as pi_mod  # noqa: E402
from agents import scientist as scientist_mod  # noqa: E402
from utils import llm as llm_mod  # noqa: E402
from utils.errors import AgentFailureError, LLMIncompleteError, SearchError  # noqa: E402
from workflow.state import CritiqueResult  # noqa: E402


def _http(status, content="", finish_reason="stop"):
    r = MagicMock()
    r.status_code = status
    r.text = "err"
    r.json.return_value = {"model": "m", "usage": {},
                           "choices": [{"message": {"content": content}, "finish_reason": finish_reason}]}
    return r


# ---------- C13: separate retry budgets ----------

def test_rate_limits_do_not_consume_incomplete_budget(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(llm_mod.time, "sleep", lambda s: None)
    client = MagicMock()
    # 4 rate limits, then a truncated response, then a full one.
    client.post.side_effect = [_http(429)] * 4 + [_http(200, "part", "length"), _http(200, "full")]
    with patch.object(llm_mod, "_get_http_client", return_value=client):
        assert llm_mod.call_llm("s", "u", model="gpt-5") == "full"


def test_http_retry_exhaustion_is_not_incomplete_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(llm_mod.time, "sleep", lambda s: None)
    client = MagicMock()
    client.post.return_value = _http(503)
    with patch.object(llm_mod, "_get_http_client", return_value=client):
        with pytest.raises(RuntimeError) as exc:
            llm_mod.call_llm("s", "u", model="gpt-5")
    assert not isinstance(exc.value, LLMIncompleteError)


# ---------- C12: RAG and PI final-synthesis search ----------

def test_rag_error_raises_and_empty_returns_nothing():
    rag_mod = importlib.import_module("tools.rag_search")
    with patch("rag.pinecone_client.get_pinecone_client") as gpc:
        gpc.return_value.search.side_effect = RuntimeError("index down")
        with pytest.raises(SearchError):
            rag_mod.rag_search_tool.invoke({"query": "q"})
        gpc.return_value.search.side_effect = None
        gpc.return_value.search.return_value = []
        assert rag_mod.rag_search_tool.invoke({"query": "q"}) == ""


def test_pi_final_synthesis_search_failure_aborts():
    state = {"topic": "t", "meeting_history": [], "current_round": 1, "messages": [],
             "specialist_outputs": [], "sources": [], "critic_score_history": []}
    with patch.object(pi_mod, "web_search") as ws:
        ws.invoke.side_effect = SearchError("down")
        with pytest.raises(SearchError):
            pi_mod.run_final_synthesis(state)


# ---------- C14: revision-round failure ----------

def test_revision_round_failure_raises():
    state = {"team": [{"role": "Alpha Specialist", "focus": "f"}], "current_round": 2,
             "critique": CritiqueResult(decision="continue", feedback="",
                                        scores={"Alpha Specialist": {a: 4 for a in ("evidence", "universality", "proportionality", "readability")}},
                                        specialist_feedback={"Alpha Specialist": "fb"}),
             "draft": "pi", "specialist_outputs": [{"role": "Alpha Specialist", "focus": "f", "output": "prev"}],
             "topic": "t", "constraints": "c", "meeting_history": [], "messages": [], "sources": []}
    agent = MagicMock()
    agent.invoke.side_effect = RuntimeError("boom")
    with patch.object(scientist_mod, "create_specialist", return_value=agent):
        with pytest.raises(AgentFailureError):
            scientist_mod.run_round_revision(state)


# ---------- C15: PI clustering, selection, introductions ----------

ROLES = ["A Specialist", "B Specialist"]


@pytest.mark.parametrize("reply", [
    "{}",
    json.dumps({"clusters": []}),
    json.dumps({"clusters": [{"canonical": "A Specialist", "members": ["A Specialist"]}]}),          # B unassigned
    json.dumps({"clusters": [{"canonical": "X", "members": ["A Specialist", "B Specialist", "C"]}]}),  # unknown role
    json.dumps({"clusters": [{"canonical": "X", "members": ["A Specialist"]},
                             {"canonical": "Y", "members": ["A Specialist", "B Specialist"]}]}),       # assigned twice
    "not json",
])
def test_clustering_incomplete_fails_closed(reply):
    with patch.object(pi_mod, "call_gpt", return_value=reply):
        with pytest.raises(AgentFailureError):
            pi_mod._cluster_similar_roles(ROLES)


def test_clustering_complete_mapping_accepted():
    reply = json.dumps({"clusters": [{"canonical": "Merged Specialist", "members": ROLES}]})
    with patch.object(pi_mod, "call_gpt", return_value=reply):
        assert pi_mod._cluster_similar_roles(ROLES) == {r: "Merged Specialist" for r in ROLES}


def test_team_selection_parse_failure_fails_closed():
    team = [{"role": "A Specialist", "focus": "f"}]
    with patch.object(pi_mod, "decide_team", return_value=team), \
         patch.object(pi_mod, "call_gpt", return_value="not json"):
        with pytest.raises(AgentFailureError):
            pi_mod.decide_team_statistically("q", n_trials=2)


def test_failed_trials_are_recorded():
    team = [{"role": "A Specialist", "focus": "f"}]
    calls = {"n": 0}

    def flaky(_q):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ValueError("bad json")
        return team

    selection = json.dumps({"team": team, "rationale": "r"})
    with patch.object(pi_mod, "decide_team", side_effect=flaky), \
         patch.object(pi_mod, "call_gpt", return_value=selection):
        out = pi_mod.decide_team_statistically("q", n_trials=2)
    assert len(out["all_teams"]) == 2 and len(out["failed_trial_attempts"]) == 1


def test_planning_has_no_default_team():
    with patch.object(pi_mod, "decide_team_statistically", side_effect=AgentFailureError("x")):
        with pytest.raises(AgentFailureError):
            pi_mod.run_pi_planning({"topic": "t", "constraints": "c", "messages": []})


def test_introduction_failure_fails_closed():
    with patch.object(pi_mod, "call_gpt", side_effect=LLMIncompleteError("truncated")):
        with pytest.raises(AgentFailureError):
            pi_mod.generate_self_introductions([{"role": "A Specialist", "focus": "f"}])


# ---------- C18 and prompt-set selection, in fresh processes ----------

def _run(code, prompts_dir):
    env = {**os.environ, "VIRTUAL_LAB_PROMPTS_DIR": prompts_dir}
    return subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True)


def test_fresh_process_starts_without_unused_assets():
    r = _run("import workflow.graph, data.guidelines as g; "
             "assert not hasattr(g, 'CODEX_PRINCIPLES'); print('ok')", str(ROOT / "prompts_A"))
    assert r.returncode == 0 and "ok" in r.stdout, r.stderr[-500:]


def test_missing_prompt_dir_is_rejected():
    r = _run("import data.guidelines", str(ROOT / "prompts_DOES_NOT_EXIST"))
    assert r.returncode != 0 and "VIRTUAL_LAB_PROMPTS_DIR does not exist" in r.stderr


def test_trial_attempts_never_exceed_budget():
    team = [{"role": "A Specialist", "focus": "f"}]
    calls = {"n": 0}

    def mostly_failing(_q):
        calls["n"] += 1
        if calls["n"] <= 7:
            return team
        raise ValueError("bad json")

    with patch.object(pi_mod, "decide_team", side_effect=mostly_failing):
        with pytest.raises(RuntimeError):
            pi_mod.decide_team_statistically("q", n_trials=10)
    assert calls["n"] == 30
