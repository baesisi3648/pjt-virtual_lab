"""Step 9: experiment manifest and the run-time check (mocked, no API calls)."""
import importlib.util
import json
import subprocess
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

from utils import manifest as mf

ROOT = Path(__file__).resolve().parents[2]


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_manifest", ROOT / "scripts" / "revision" / "build_manifest.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    for rel, text in {
        "agents/critic.py": "CRITIC_VALIDATION_RETRIES = 1\n",
        "agents/pi.py": "INTRO_MAX_TOKENS = 8192\n",
        "utils/llm.py": 'MAX_INCOMPLETE_RETRIES = 1\nMAX_HTTP_RETRIES = 5  # note\nDEFAULT_CRITIC_MODEL = "claude-opus-5"\n'
                        'DEFAULT_CRITIC_EFFORT = "high"\nCRITIC_MAX_TOKENS = 64000\n',
        "workflow/graph.py": "MAX_ROUNDS = 7\n",
        "tools/t.py": "x = 1\n",
        "run_experiment.py": "print(1)\n",
        "requirements.txt": "httpx\n",
        "experiments/reproducibility/analyze_revision.py": "y = 2\n",
        "prompts_A/system/critic.md": "A\n",
        "prompts_B/system/critic.md": "B\n",
        "snap.json": "{}",
    }.items():
        (r / rel).parent.mkdir(parents=True, exist_ok=True)
        (r / rel).write_text(text, encoding="utf-8")
    for cmd in (["init", "-q"], ["add", "-A"], ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x"]):
        subprocess.check_call(["git", *cmd], cwd=r)
    return r


def _manifest(r: Path) -> dict:
    return {
        "manifest_version": mf.MANIFEST_VERSION,
        "code": {"file_hashes": mf.file_hashes(mf.CODE_PATHS, r)},
        "prompts": {c: {"file_hashes": mf.prompt_hashes(c, r)} for c in "AB"},
        "retrieval": {"mode": "replay", "snapshot_sha256": mf.sha256_file(r / "snap.json")},
        "models": {"generation_model_requested": "gpt-5", "critic_model_requested": "claude-opus-5",
                   "critic_effort": "high"},
        "retry_policy": {"max_attempts_per_run": 3},
        "order": [{"seq": 1, "condition": "A", "run_id": "1"}, {"seq": 2, "condition": "B", "run_id": "1"}],
        "inputs": {"topic": "T", "constraints": "C"},
        "environment": {"python": mf.python_version(), "packages": mf.installed_packages()},
    }


def _verify(r, m, **kw):
    args = dict(condition="A", run_id="1", attempt=1, retrieval_mode="replay", snapshot_path=r / "snap.json",
                topic="T", constraints="C", runs_dir=None, root=r)
    args.update(kw)
    return mf.verify(m, **args)


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("GPT_MODEL", "gpt-5")
    monkeypatch.delenv("CRITIC_MODEL", raising=False)
    monkeypatch.delenv("CRITIC_EFFORT", raising=False)
    return monkeypatch


def test_verify_ok_and_constants(tmp_path, env):
    r = _repo(tmp_path)
    assert _verify(r, _manifest(r)) == []
    c = mf.read_constants(r)
    assert c["MAX_ROUNDS"] == 7 and c["MAX_HTTP_RETRIES"] == 5 and c["DEFAULT_CRITIC_MODEL"] == "claude-opus-5"


def test_verify_detects_each_mismatch(tmp_path, env):
    r = _repo(tmp_path)
    m = _manifest(r)
    (r / "agents/critic.py").write_text("CRITIC_VALIDATION_RETRIES = 2\n", encoding="utf-8")
    (r / "prompts_A/system/critic.md").write_text("A2\n", encoding="utf-8")
    (r / "snap.json").write_text('{"x": 1}', encoding="utf-8")
    env.setenv("GPT_MODEL", "gpt-4o")
    env.setenv("CRITIC_MODEL", "claude-opus-5-5")
    m["environment"]["python"] = "0.0.0"
    m["environment"]["packages"] = {**m["environment"]["packages"], "httpx": "0.0.1"}
    env.setenv("VIRTUAL_LAB_TEMPERATURE", "0.2")
    problems = _verify(r, m, run_id="6", attempt=4, retrieval_mode="live", constraints="other")
    text = "\n".join(problems)
    for needle in ("A_6 is not in", "attempt 4", "retrieval mode", "snapshot hash", "prompt set",
                   "agents/critic.py", "GPT_MODEL", "CRITIC_MODEL", "--constraints", "VIRTUAL_LAB_TEMPERATURE",
                   "!= 0.0.0", "httpx 0.0.1"):
        assert needle in text, needle


def test_new_tracked_code_file_is_detected(tmp_path, env):
    r = _repo(tmp_path)
    m = _manifest(r)
    (r / "utils/extra.py").write_text("z = 3\n", encoding="utf-8")
    subprocess.check_call(["git", "add", "utils/extra.py"], cwd=r)
    assert any("utils/extra.py" in p for p in _verify(r, m))


def test_uncommitted_lists_modified_tracked_files(tmp_path):
    r = _repo(tmp_path)
    assert mf.uncommitted(mf.CODE_PATHS, r) == []
    (r / "tools/t.py").write_text("x = 2\n", encoding="utf-8")
    assert any("tools/t.py" in line for line in mf.uncommitted(mf.CODE_PATHS, r))


def test_run_order_is_balanced_and_fixed():
    b = _load_builder()
    order = b.run_order()
    assert order == b.run_order()                                     # same seed -> same order
    assert Counter(e["condition"] for e in order) == {"A": 5, "B": 5}
    for blk in range(1, 6):
        assert sorted(e["condition"] for e in order if e["block"] == blk) == ["A", "B"]
    assert [e["seq"] for e in order] == list(range(1, 11))
    firsts = [e["condition"] for e in order if e["seq"] % 2 == 1]
    assert 2 <= firsts.count("A") <= 3


def test_second_judge_sample_has_both_conditions():
    s = _load_builder().second_judge_sample()
    conds = Counter(x[0] for x in s["reports"])
    assert sum(conds.values()) == 3 and set(conds) == {"A", "B"}


def test_run_experiment_requires_manifest_for_main(monkeypatch):
    import run_experiment as rex
    args = SimpleNamespace(out_dir="experiments/runs_rev/main", manifest=None)
    with pytest.raises(SystemExit, match="require --manifest"):
        rex._check_manifest(args)
    assert rex._check_manifest(SimpleNamespace(out_dir="experiments/runs_rev/pilot", manifest=None)) is None
    with pytest.raises(SystemExit, match="require --manifest"):
        rex._check_manifest(SimpleNamespace(out_dir="experiments/runs_rev/main/batch_01", manifest=None))
    with pytest.raises(SystemExit, match="require --manifest"):
        rex._check_manifest(SimpleNamespace(out_dir="experiments/runs_rev/main_v1", manifest=None))
    assert rex._check_manifest(SimpleNamespace(out_dir="experiments/runs_rev/main_logs", manifest=None)) is None


def test_run_root_comes_from_manifest(tmp_path):
    import run_experiment as rex
    v1 = tmp_path / "v1.json"
    v1.write_text(json.dumps({"retrieval": {"snapshot_path": "x.json"}}), encoding="utf-8")
    v2 = tmp_path / "v2.json"
    v2.write_text(json.dumps({"out_dir": "experiments/runs_rev/main_v1", "retrieval": {"snapshot_path": "x.json"}}),
                  encoding="utf-8")
    for out in ("experiments/runs_rev/main/batch_01", "experiments/runs_rev/pilot", "experiments/runs_rev/main_v1"):
        with pytest.raises(SystemExit, match="must use --out-dir experiments/runs_rev/main"):
            rex._check_manifest(SimpleNamespace(out_dir=out, manifest=str(v1)))
    for out in ("experiments/runs_rev/main", "experiments/runs_rev/main_v1/x"):
        with pytest.raises(SystemExit, match="must use --out-dir experiments/runs_rev/main_v1"):
            rex._check_manifest(SimpleNamespace(out_dir=out, manifest=str(v2)))


def test_run_experiment_rejects_mismatch(tmp_path, monkeypatch):
    import run_experiment as rex
    m = {"retrieval": {"snapshot_path": "experiments/runs_rev/retrieval_snapshot.json"}}
    path = tmp_path / "m.json"
    path.write_text(json.dumps(m), encoding="utf-8")
    monkeypatch.setattr(mf, "verify", lambda *a, **k: ["prompt set prompts_A differs from the manifest"])
    args = SimpleNamespace(out_dir="experiments/runs_rev/main", manifest=str(path), condition="A", run_id="1",
                           attempt=1, retrieval_mode="replay", topic="T", constraints="C",
                           retrieval_snapshot="experiments/runs_rev/retrieval_snapshot.json")
    with pytest.raises(SystemExit, match="run not started"):
        rex._check_manifest(args)
    args.retrieval_snapshot = "other.json"
    with pytest.raises(SystemExit, match="not the manifest snapshot"):
        rex._check_manifest(args)


def test_untracked_python_file_blocks(tmp_path, env):
    r = _repo(tmp_path)
    m = _manifest(r)
    (r / "agents" / "critic").mkdir()
    (r / "agents" / "critic" / "__init__.py").write_text("x = 1\n", encoding="utf-8")
    assert any("untracked Python files" in p and "agents/critic/__init__.py" in p for p in _verify(r, m))


def _attempt(runs: Path, name: str, n: int, status: str | None):
    d = runs / name / f"attempt_{n:02d}"
    d.mkdir(parents=True)
    if status is not None:
        (d / "meta.json").write_text(json.dumps({"status": status}), encoding="utf-8")


def test_order_and_attempt_rules(tmp_path):
    m = {"order": [{"seq": 1, "condition": "A", "run_id": "1"}, {"seq": 2, "condition": "B", "run_id": "1"},
                   {"seq": 3, "condition": "A", "run_id": "2"}],
         "retry_policy": {"max_attempts_per_run": 3}}
    runs = tmp_path / "main"
    assert mf.check_order(m, "A", "1", 1, runs) == []
    assert any("earlier run A_1" in p for p in mf.check_order(m, "B", "1", 1, runs))    # skipped ahead
    assert any("attempt must be 1" in p for p in mf.check_order(m, "A", "1", 3, runs))  # starts at 3
    _attempt(runs, "A_1", 1, "failed")
    _attempt(runs, "A_1", 2, None)                                                    # killed mid-run
    assert mf.check_order(m, "A", "1", 3, runs) == []
    assert any("earlier run A_1" in p for p in mf.check_order(m, "B", "1", 1, runs))  # A_1 still open
    _attempt(runs, "A_1", 3, "ok")
    assert any("already has a successful" in p for p in mf.check_order(m, "A", "1", 4, runs))
    assert mf.check_order(m, "B", "1", 1, runs) == []
    _attempt(runs, "A_2", 1, "ok")                                                    # ran out of order
    assert any("later run A_2" in p for p in mf.check_order(m, "B", "1", 1, runs))


def test_exhausted_earlier_run_does_not_block(tmp_path):
    m = {"order": [{"seq": 1, "condition": "A", "run_id": "1"}, {"seq": 2, "condition": "B", "run_id": "1"}],
         "retry_policy": {"max_attempts_per_run": 2}}
    runs = tmp_path / "main"
    _attempt(runs, "A_1", 1, "failed")
    _attempt(runs, "A_1", 2, "failed")
    assert mf.check_order(m, "B", "1", 1, runs) == []
    assert any("outside 1..2" in p for p in mf.check_order(m, "A", "1", 3, runs))


def test_run_experiment_accepts_matching_manifest(tmp_path, monkeypatch):
    import run_experiment as rex
    m = {"retrieval": {"snapshot_path": "experiments/runs_rev/retrieval_snapshot.json"}}
    path = tmp_path / "m.json"
    path.write_text(json.dumps(m), encoding="utf-8")
    seen = {}
    monkeypatch.setattr(mf, "verify", lambda *a, **k: seen.update(k) or [])
    args = SimpleNamespace(out_dir="experiments/runs_rev/main", manifest=str(path), condition="B", run_id="2",
                           attempt=1, retrieval_mode="replay", topic="T", constraints="C",
                           retrieval_snapshot="experiments/runs_rev/retrieval_snapshot.json")
    info = rex._check_manifest(args)
    assert info["verified"] and info["sha256"] == mf.sha256_file(path) and info["path"] == str(path.resolve())
    assert seen["runs_dir"] == rex.MAIN_OUT and seen["topic"] == "T" and seen["constraints"] == "C"


def test_root_level_shadowing_is_detected(tmp_path, env):
    r = _repo(tmp_path)
    (r / "config").mkdir()
    (r / "config" / "__init__.py").write_text("x = 1\n", encoding="utf-8")
    (r / "httpx.py").write_text("x = 1\n", encoding="utf-8")
    (r / "notes").mkdir()                                     # plain folder without __init__.py: fine
    found = mf.untracked_code(mf.CODE_PATHS, r)
    assert "config/__init__.py" in found and "httpx.py" in found and not any(f.startswith("notes") for f in found)


def test_environment_is_order_independent_and_clean():
    assert mf.installed_packages() == mf.installed_packages()
    assert mf.environment_problems() == []                   # the experiment venv has no duplicates or editables


def test_duplicate_and_editable_installs_are_rejected(monkeypatch):
    def dist(version, editable=False):
        return SimpleNamespace(metadata={"Name": "example"}, version=version,
                               read_text=lambda name: '{"dir_info": {"editable": true}}' if editable else None)
    for dists, needle in (([dist("1.0"), dist("1.0")], "duplicate"), ([dist("1.0"), dist("2.0")], "duplicate"),
                          ([dist("1.0", True)], "editable")):
        monkeypatch.setattr(mf.metadata, "distributions", lambda d=dists: list(d))
        assert any(needle in p for p in mf.environment_problems())
        monkeypatch.setattr(mf.metadata, "distributions", lambda d=dists: list(reversed(d)))
        assert any(needle in p for p in mf.environment_problems())


def test_amendment_excludes_attempts_from_counting(tmp_path):
    m = {"order": [{"seq": 1, "condition": "A", "run_id": "1"}, {"seq": 2, "condition": "B", "run_id": "1"},
                   {"seq": 3, "condition": "A", "run_id": "2"}],
         "retry_policy": {"max_attempts_per_run": 3}}
    runs = tmp_path / "main"
    _attempt(runs, "A_1", 1, "ok")
    for n in (1, 2, 3):
        _attempt(runs, "B_1", n, "failed")
    _attempt(runs, "A_2", 1, "failed")                        # later run already has a (lost) attempt
    assert mf.next_attempt(m, "B", "1", runs) == "exhausted"
    assert any("later run A_2" in p for p in mf.check_order(m, "B", "1", 4, runs))
    m["amendment"] = {"excluded_attempts": [{"attempt": a} for a in
                      ("B_1/attempt_01", "B_1/attempt_02", "B_1/attempt_03", "A_2/attempt_01")]}
    assert mf.next_attempt(m, "B", "1", runs) == "4"           # numbering continues
    assert mf.check_order(m, "B", "1", 4, runs) == []
    assert any("attempt must be 4" in p for p in mf.check_order(m, "B", "1", 1, runs))
    assert any("earlier run B_1" in p for p in mf.check_order(m, "A", "2", 2, runs))  # B_1 not finished yet
    _attempt(runs, "B_1", 4, "ok")
    assert mf.next_attempt(m, "B", "1", runs) == "done"
    assert mf.check_order(m, "A", "2", 2, runs) == []
    assert mf.next_attempt(m, "A", "2", runs) == "2"
    assert mf.next_attempt(m, "A", "1", runs) == "done"


def test_preparation_and_corpus_hashes_are_verified(tmp_path, env):
    r = _repo(tmp_path)
    m = _manifest(r)
    (r / "scripts").mkdir()
    (r / "scripts" / "build.py").write_text("a = 1\n", encoding="utf-8")
    (r / "corpus.json").write_text("{}", encoding="utf-8")
    m["preparation"] = {"file_hashes": {"scripts/build.py": mf.sha256_file(r / "scripts" / "build.py")}}
    m["corpus"] = {"manifest_path": "corpus.json", "manifest_sha256": mf.sha256_file(r / "corpus.json")}
    assert _verify(r, m) == []
    (r / "scripts" / "build.py").write_text("a = 2\n", encoding="utf-8")
    (r / "corpus.json").write_text('{"x": 1}', encoding="utf-8")
    text = "\n".join(_verify(r, m))
    assert "preparation file differs" in text and "corpus manifest differs" in text
