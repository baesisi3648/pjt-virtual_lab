"""Revision step 4: Critic modes (C2), Claude Critic (C16), call log (C5), run outputs (C1, C6-C8).

All external calls are mocked.
"""
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
os.environ["VIRTUAL_LAB_PROMPTS_DIR"] = str(ROOT / "prompts_A")

from agents import critic as critic_mod  # noqa: E402
from utils import call_log  # noqa: E402
from utils import llm as llm_mod  # noqa: E402
from utils.errors import LLMIncompleteError  # noqa: E402

AXES = ("evidence", "universality", "proportionality", "readability")
ROLES = ["Alpha Specialist", "Beta Specialist"]


@pytest.fixture(autouse=True)
def _reset_log():
    call_log.reset()
    yield
    call_log.reset()


# ---------- C2: Critic modes ----------

def test_mask_score_mentions():
    text, n = critic_mod.mask_score_mentions(
        "Evidence 4/5; scored 3 on readability; readability: 4; reach 5/5. Five pillars remain.")
    assert n == 4 and "4/5" not in text and "scored 3" not in text and "Five pillars" in text


def _state_round2():
    fb = "Readability 4/5 because acronyms lack glosses. evidence=4."
    return {
        "topic": "t", "current_round": 2,
        "team": [{"role": r, "focus": "f"} for r in ROLES],
        "specialist_outputs": [{"role": r, "focus": "f", "output": "x"} for r in ROLES],
        "meeting_history": [{"round": 1,
                             "critique_scores": {r: {a: 4 for a in AXES} for r in ROLES},
                             "critique_feedback": "Overall 4/5.",
                             "specialist_feedback": {r: fb for r in ROLES}}],
        "messages": [], "critic_score_history": [],
    }


def _valid_json():
    return json.dumps({"decision": "continue", "feedback": "ok",
                       "scores": {r: {a: 4 for a in AXES} for r in ROLES},
                       "specialist_feedback": {r: "fb" for r in ROLES}})


def _captured_message(mode, monkeypatch):
    monkeypatch.setenv("VIRTUAL_LAB_CRITIC_MODE", mode)
    seen = {}

    def fake(system, user, tag=None):
        seen["user"], seen["tag"] = user, tag
        return _valid_json()

    with patch.object(critic_mod, "web_search") as ws, patch.object(critic_mod, "call_critic", side_effect=fake):
        ws.invoke.return_value = ""
        critic_mod.run_critic(_state_round2())
    return seen


def test_cumulative_mode_keeps_submitted_rules(monkeypatch):
    seen = _captured_message("cumulative", monkeypatch)
    assert "Per-specialist scores" in seen["user"]
    assert "do not lower the score" in seen["user"] and "raise the score" in seen["user"]
    assert "4/5" in seen["user"]


def test_independent_mode_hides_prior_scores(monkeypatch):
    seen = _captured_message("independent", monkeypatch)
    assert "Per-specialist scores" not in seen["user"]
    assert "do not lower the score" not in seen["user"] and "raise the score" not in seen["user"]
    assert "4/5" not in seen["user"] and "evidence=4" not in seen["user"]
    assert "acronyms lack glosses" in seen["user"]          # feedback content kept
    assert seen["tag"]["critic_mode"] == "independent" and seen["tag"]["masked_score_mentions"] >= 3


def test_unknown_mode_rejected(monkeypatch):
    monkeypatch.setenv("VIRTUAL_LAB_CRITIC_MODE", "lenient")
    with pytest.raises(ValueError):
        critic_mod.critic_mode()


# ---------- C16: Claude Critic ----------

def _claude_message(text, stop_reason="end_turn", model="claude-opus-5-5"):
    return SimpleNamespace(
        id="msg_1", model=model, stop_reason=stop_reason, stop_details=None, _request_id="req_1",
        content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)],
        usage=SimpleNamespace(model_dump=lambda: {"input_tokens": 10, "output_tokens": 5}),
    )


def _fake_client(messages, captured):
    client = MagicMock()

    def stream(**kwargs):
        captured.append(kwargs)
        cm = MagicMock()
        cm.__enter__.return_value.get_final_message.return_value = messages.pop(0)
        return cm

    client.messages.stream.side_effect = stream
    return client


def test_claude_call_parameters_and_text(monkeypatch):
    monkeypatch.delenv("CRITIC_MODEL", raising=False)
    monkeypatch.delenv("CRITIC_EFFORT", raising=False)
    captured = []
    client = _fake_client([_claude_message("hello")], captured)
    with patch.object(llm_mod, "_get_anthropic_client", return_value=client):
        assert llm_mod.call_claude("sys", "user") == "hello"
    kw = captured[0]
    assert kw["model"] == "claude-opus-5-5" and kw["output_config"] == {"effort": "high"}
    for forbidden in ("temperature", "top_p", "top_k", "thinking", "fallbacks", "betas"):
        assert forbidden not in kw


@pytest.mark.parametrize("stop_reason,text", [("refusal", ""), ("max_tokens", "partial"), ("end_turn", "")])
def test_claude_incomplete_fails_closed(stop_reason, text):
    captured = []
    client = _fake_client([_claude_message(text, stop_reason), _claude_message(text, stop_reason)], captured)
    with patch.object(llm_mod, "_get_anthropic_client", return_value=client):
        with pytest.raises(LLMIncompleteError):
            llm_mod.call_claude("sys", "user")
    assert len(captured) == 1 + llm_mod.MAX_INCOMPLETE_RETRIES


def test_critic_routing(monkeypatch):
    monkeypatch.setenv("VIRTUAL_LAB_CRITIC_PROVIDER", "anthropic")
    with patch.object(llm_mod, "call_claude", return_value="c") as cc, patch.object(llm_mod, "call_gpt") as cg:
        assert llm_mod.call_critic("s", "u") == "c"
    cc.assert_called_once()
    cg.assert_not_called()
    monkeypatch.setenv("VIRTUAL_LAB_CRITIC_PROVIDER", "other")
    with pytest.raises(ValueError):
        llm_mod.call_critic("s", "u")


# ---------- C5: call log ----------

def _http(content, finish_reason="stop"):
    r = MagicMock()
    r.status_code = 200
    r.headers = {"x-request-id": "req_x"}
    r.json.return_value = {"model": "gpt-5-2025-08-07", "system_fingerprint": "fp", "usage": {"total_tokens": 3},
                           "choices": [{"message": {"content": content}, "finish_reason": finish_reason}]}
    return r


def test_call_log_records_inputs_and_model(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")
    call_log.configure(tmp_path / "calls.jsonl", {"condition": "A", "run_id": "1", "attempt": 1})
    client = MagicMock()
    client.post.side_effect = [_http("part", "length"), _http("done")]
    with patch.object(llm_mod, "_get_http_client", return_value=client):
        llm_mod.call_llm("SYS", "USER", model="gpt-5", tag={"agent": "PI", "round": 2})
    rows = [json.loads(l) for l in (tmp_path / "calls.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row["status"] == "ok" and row["condition"] == "A" and row["tag"] == {"agent": "PI", "round": 2}
    assert row["system_prompt"] == "SYS" and row["user_message"] == "USER"
    assert row["response_model"] == "gpt-5-2025-08-07" and len(row["attempts"]) == 2
    assert "temperature" in row["omitted_parameters"] and "max_completion_tokens" in row["request"]
    assert "sk-test-not-a-real-key" not in (tmp_path / "calls.jsonl").read_text(encoding="utf-8")
    assert call_log.summary()["response_models"] == {"openai": ["gpt-5-2025-08-07"]}


def test_call_log_records_failures(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    call_log.configure(tmp_path / "calls.jsonl", {"condition": "B"})
    client = MagicMock()
    client.post.return_value = _http("", "stop")
    with patch.object(llm_mod, "_get_http_client", return_value=client):
        with pytest.raises(LLMIncompleteError):
            llm_mod.call_llm("s", "u", model="gpt-5")
    row = json.loads((tmp_path / "calls.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert row["status"] == "error" and row["error_type"] == "LLMIncompleteError"


def test_call_log_refuses_existing_file(tmp_path):
    p = tmp_path / "calls.jsonl"
    p.write_text("x")
    with pytest.raises(FileExistsError):
        call_log.configure(p, {})


# ---------- C1, C6-C8: run_experiment ----------

class _FakeWorkflow:
    def __init__(self, fail=False):
        self.fail = fail

    def stream(self, state, config=None):
        from workflow.state import CritiqueResult
        team = [{"role": r, "focus": "f"} for r in ROLES]
        crit = CritiqueResult("continue", "ok", {r: {a: 5 for a in AXES} for r in ROLES}, {r: "fb" for r in ROLES})
        yield {"planning": {"team": team, "team_selection_data": {"rationale": "r", "failed_trial_attempts": [{}]}}}
        yield {"researching": {"specialist_outputs": [{"role": r, "focus": "f", "output": "out" * 10} for r in ROLES]}}
        if self.fail:
            raise RuntimeError("boom")
        yield {"critique": {"critique": crit, "critic_score_history": [{"round": 1, "scores": crit.scores}]}}
        yield {"pi_summary": {"draft": "summary"}}
        yield {"final_synthesis": {"final_report": "REPORT"}}
        yield {"translation": {"final_report_ko": "", "translation_error": "RuntimeError: x"}}


def _run_main(monkeypatch, tmp_path, argv, fail=False):
    import run_experiment
    for k in ("VIRTUAL_LAB_PROMPTS_DIR", "VIRTUAL_LAB_CRITIC_MODE", "VIRTUAL_LAB_CRITIC_PROVIDER"):
        monkeypatch.setenv(k, "placeholder")  # registers the original value for restore
        monkeypatch.delenv(k)
    monkeypatch.setattr(sys, "argv", ["run_experiment.py", *argv, "--out-dir", str(tmp_path)])
    with patch("workflow.graph.create_workflow", return_value=_FakeWorkflow(fail)):
        return run_experiment.main()


def test_run_writes_records(monkeypatch, tmp_path):
    assert _run_main(monkeypatch, tmp_path, ["--condition", "A", "--run-id", "1"]) == 0
    d = tmp_path / "A_1" / "attempt_01"
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "ok" and meta["condition"] == "A"
    assert meta["critic"]["mode"] == "independent" and meta["critic"]["provider"] == "anthropic"
    assert meta["prompts_dir"] == "prompts_A" and "system/critic.md" in meta["prompt_hashes"]
    assert meta["translation_error"].startswith("RuntimeError") and meta["failed_team_trial_attempts"] == 1
    assert meta["output_stats"]["agents"]["Alpha Specialist"]["chars"] == 30
    assert "commit" in meta["code"] and "kst" in meta["started"]
    assert (d / "final_report.md").read_text(encoding="utf-8") == "REPORT"
    assert (d / "calls.jsonl").exists() and (d / "conversations.json").exists()
    assert os.environ["VIRTUAL_LAB_CRITIC_MODE"] == "independent"


def test_run_refuses_overwrite(monkeypatch, tmp_path):
    (tmp_path / "B_1" / "attempt_01").mkdir(parents=True)
    with pytest.raises(SystemExit):
        _run_main(monkeypatch, tmp_path, ["--condition", "B", "--run-id", "1"])


def test_run_rejects_conflicting_env(monkeypatch, tmp_path):
    import run_experiment
    monkeypatch.setenv("VIRTUAL_LAB_CRITIC_MODE", "cumulative")
    monkeypatch.setattr(sys, "argv", ["run_experiment.py", "--condition", "A", "--run-id", "1",
                                      "--out-dir", str(tmp_path)])
    with pytest.raises(SystemExit):
        run_experiment.main()


def test_failed_run_records_meta(monkeypatch, tmp_path):
    assert _run_main(monkeypatch, tmp_path, ["--condition", "B", "--run-id", "2"], fail=True) == 1
    meta = json.loads((tmp_path / "B_2" / "attempt_01" / "meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "failed" and meta["error"]["type"] == "RuntimeError"
    assert meta["critic"]["mode"] == "cumulative"
