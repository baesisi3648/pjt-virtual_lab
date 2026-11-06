"""Revision step 4: tests for the Codex review findings (score leakage, redaction,
attempt logging, partial and failed-run records). All external calls are mocked."""
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]
os.environ["VIRTUAL_LAB_PROMPTS_DIR"] = str(ROOT / "prompts_A")

from agents import critic as critic_mod  # noqa: E402
from utils import call_log  # noqa: E402
from utils import llm as llm_mod  # noqa: E402
from utils.errors import AgentFailureError  # noqa: E402

AXES = ("evidence", "universality", "proportionality", "readability")
ROLES = ["Alpha Specialist", "Beta Specialist"]


@pytest.fixture(autouse=True)
def _reset_log():
    call_log.reset()
    yield
    call_log.reset()


# ---------- score leakage into the condition-A Critic ----------

@pytest.mark.parametrize("text", [
    "Readability (4)", "Universality is 5", "evidence: **4**", "increased from 3 to 4",
    "Previously readability 4/5", "scored 3 last round", "rating of 2",
])
def test_extended_masking(text):
    masked, n = critic_mod.mask_score_mentions(text)
    assert n >= 1 and not any(d in masked for d in "12345"), masked


@pytest.mark.parametrize("text", [
    "SDN-1, SDN-2 and SDN-3 products", "five assessment pillars", "variation up to 20 nucleotides",
    "Codex CXG 45-2003", "step 3 of the workflow",
])
def test_masking_leaves_scientific_numbers(text):
    assert critic_mod.mask_score_mentions(text) == (text, 0)


def _state_with_leaky_outputs():
    return {"topic": "t", "current_round": 2, "team": [{"role": r, "focus": "f"} for r in ROLES],
            "specialist_outputs": [{"role": r, "focus": "f",
                                    "output": "Previously my readability was 4/5; I now gloss acronyms."}
                                   for r in ROLES],
            "meeting_history": [], "messages": [], "critic_score_history": []}


def _valid():
    return json.dumps({"decision": "continue", "feedback": "ok",
                       "scores": {r: {a: 4 for a in AXES} for r in ROLES},
                       "specialist_feedback": {r: "fb" for r in ROLES}})


@pytest.mark.parametrize("mode,leaks", [("independent", False), ("cumulative", True)])
def test_specialist_texts_masked_only_in_condition_a(monkeypatch, mode, leaks):
    monkeypatch.setenv("VIRTUAL_LAB_CRITIC_MODE", mode)
    seen = {}

    def fake(system, user, tag=None):
        seen["user"] = user
        return _valid()

    with patch.object(critic_mod, "web_search") as ws, patch.object(critic_mod, "call_critic", side_effect=fake):
        ws.invoke.return_value = ""
        critic_mod.run_critic(_state_with_leaky_outputs())
    assert ("4/5" in seen["user"]) is leaks
    assert "I now gloss acronyms" in seen["user"]


# ---------- redaction ----------

def test_error_bodies_are_redacted(tmp_path, monkeypatch):
    fake_key = "sk-proj-" + "Z" * 40
    monkeypatch.setenv("OPENAI_API_KEY", fake_key)
    call_log.configure(tmp_path / "calls.jsonl", {"condition": "A"})
    r = MagicMock()
    r.status_code = 401
    r.headers = {}
    r.text = f'{{"error": "Incorrect API key provided: {fake_key}"}}'
    client = MagicMock()
    client.post.return_value = r
    with patch.object(llm_mod, "_get_http_client", return_value=client):
        with pytest.raises(RuntimeError):
            llm_mod.call_llm("s", "u", model="gpt-5")
    logged = (tmp_path / "calls.jsonl").read_text(encoding="utf-8")
    assert fake_key not in logged and "[REDACTED]" in logged


def test_redaction_keeps_ordinary_words():
    from utils.redact import redact
    assert redact("risk-assessment and task-specific") == "risk-assessment and task-specific"


# ---------- attempt logging ----------

def _ok_http(content="done"):
    r = MagicMock()
    r.status_code = 200
    r.headers = {"x-request-id": "req_ok"}
    r.json.return_value = {"model": "gpt-5-x", "usage": {},
                           "choices": [{"message": {"content": content}, "finish_reason": "stop"}]}
    return r


def test_openai_transport_errors_are_recorded(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(llm_mod.time, "sleep", lambda s: None)
    call_log.configure(tmp_path / "calls.jsonl", {})
    client = MagicMock()
    client.post.side_effect = [httpx.ConnectError("refused"), _ok_http()]
    with patch.object(llm_mod, "_get_http_client", return_value=client):
        assert llm_mod.call_llm("s", "u", model="gpt-5") == "done"
    row = json.loads((tmp_path / "calls.jsonl").read_text(encoding="utf-8"))
    assert [a.get("error_type") for a in row["attempts"]] == ["ConnectError", None]


def _anthropic_conn_error():
    import anthropic
    e = anthropic.APIConnectionError.__new__(anthropic.APIConnectionError)
    Exception.__init__(e, "connection reset")
    e.message = "connection reset"
    return e


def test_anthropic_transport_retries_and_request_id(tmp_path, monkeypatch):
    monkeypatch.setattr(llm_mod.time, "sleep", lambda s: None)
    call_log.configure(tmp_path / "calls.jsonl", {})
    msg = SimpleNamespace(id="msg", model="claude-opus-5", stop_reason="end_turn", stop_details=None,
                          content=[SimpleNamespace(type="text", text="ok")],
                          usage=SimpleNamespace(model_dump=lambda: {}), model_dump=lambda: {"id": "msg"})
    outcomes = [_anthropic_conn_error(), msg]

    def stream(**kw):
        o = outcomes.pop(0)
        cm = MagicMock()
        if isinstance(o, Exception):
            cm.__enter__.side_effect = o
        else:
            s = cm.__enter__.return_value
            s.get_final_message.return_value = o
            s.request_id = "req_from_stream"
        return cm

    client = MagicMock()
    client.messages.stream.side_effect = stream
    with patch.object(llm_mod, "_get_anthropic_client", return_value=client):
        assert llm_mod.call_claude("s", "u") == "ok"
    row = json.loads((tmp_path / "calls.jsonl").read_text(encoding="utf-8"))
    assert row["attempts"][0]["error_type"] == "APIConnectionError"
    assert row["request_id"] == "req_from_stream" and row["attempts"][1]["raw_message"] == {"id": "msg"}


def test_models_from_rejected_attempts_are_counted(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    call_log.configure(tmp_path / "calls.jsonl", {})
    bad = _ok_http("")
    bad.json.return_value["model"] = "gpt-5-other"
    client = MagicMock()
    client.post.side_effect = [bad, bad]
    with patch.object(llm_mod, "_get_http_client", return_value=client):
        with pytest.raises(Exception):
            llm_mod.call_llm("s", "u", model="gpt-5")
    assert call_log.summary()["response_models"] == {"openai": ["gpt-5-other"]}


# ---------- failed-run records ----------

class _Workflow:
    def __init__(self, events, exc):
        self.events, self.exc = events, exc

    def stream(self, state, config=None):
        yield from self.events
        raise self.exc


def _run(monkeypatch, tmp_path, workflow, argv=("--condition", "A", "--run-id", "9")):
    import run_experiment
    for k in ("VIRTUAL_LAB_PROMPTS_DIR", "VIRTUAL_LAB_CRITIC_MODE", "VIRTUAL_LAB_CRITIC_PROVIDER",
              "VIRTUAL_LAB_RETRIEVAL_MODE", "VIRTUAL_LAB_RETRIEVAL_SNAPSHOT"):
        monkeypatch.setenv(k, "placeholder")
        monkeypatch.delenv(k)
    monkeypatch.setattr(sys, "argv", ["run_experiment.py", *argv, "--out-dir", str(tmp_path), "--retrieval-mode", "live"])
    with patch("workflow.graph.create_workflow", return_value=workflow):
        return run_experiment.main()


def test_failure_after_increment_does_not_duplicate_round(monkeypatch, tmp_path):
    from workflow.state import CritiqueResult
    crit = CritiqueResult("continue", "ok", {r: {a: 4 for a in AXES} for r in ROLES}, {r: "fb" for r in ROLES})
    r1 = {"round": 1, "specialist_outputs": [{"role": r, "output": "o1"} for r in ROLES],
          "critique_feedback": "ok", "critique_scores": crit.scores, "specialist_feedback": crit.specialist_feedback,
          "pi_summary": "s1"}
    events = [
        {"planning": {"team": [{"role": r, "focus": "f"} for r in ROLES]}},
        {"researching": {"specialist_outputs": r1["specialist_outputs"]}},
        {"critique": {"critique": crit}},
        {"pi_summary": {"draft": "s1"}},
        {"increment_round": {"current_round": 2, "meeting_history": [r1]}},
    ]
    assert _run(monkeypatch, tmp_path, _Workflow(events, AgentFailureError("revision failed"))) == 1
    d = tmp_path / "A_9" / "attempt_01"
    conv = json.loads((d / "conversations.json").read_text(encoding="utf-8"))
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    assert [r["round"] for r in conv] == [1]
    assert meta["rounds_completed"] == 1 and meta["round_at_end"] == 2 and meta["status"] == "failed"


def test_partial_team_selection_is_kept(monkeypatch, tmp_path):
    partial = {"team_selection_data": {"all_teams": [[{"role": "X", "focus": "f"}]],
                                       "failed_trial_attempts": [{"error_type": "ValueError"}] * 3}}
    exc = AgentFailureError("clustering failed", partial=partial)
    assert _run(monkeypatch, tmp_path, _Workflow([], exc)) == 1
    d = tmp_path / "A_9" / "attempt_01"
    tsd = json.loads((d / "team_selection.json").read_text(encoding="utf-8"))
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    assert len(tsd["all_teams"]) == 1 and meta["failed_team_trial_attempts"] == 3


def test_initialisation_failure_writes_meta(monkeypatch, tmp_path):
    with patch("utils.prompt_loader.active_prompts_dir", side_effect=RuntimeError("prompt set broken")):
        assert _run(monkeypatch, tmp_path, _Workflow([], RuntimeError("unused"))) == 1
    meta = json.loads((tmp_path / "A_9" / "attempt_01" / "meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "failed_init" and "prompt set broken" in meta["error"]["message"]


# ---------- re-review follow-ups ----------

@pytest.mark.parametrize("text", ["Readability: 3 -> 4", "| Readability | 3 | 4 |", "evidence at 4 and readability at 3."])
def test_masking_arrows_and_tables(text):
    masked, n = critic_mod.mask_score_mentions(text)
    assert n >= 1 and not any(d in masked for d in "1234"), masked


@pytest.mark.parametrize("text", ["Evidence from 3 studies supports SDN-1.", "Evidence of 3 independent studies"])
def test_masking_keeps_evidence_counts(text):
    assert critic_mod.mask_score_mentions(text) == (text, 0)


def test_translation_error_is_redacted_in_meta(monkeypatch, tmp_path):
    fake_key = "sk-proj-" + "Q" * 40
    monkeypatch.setenv("OPENAI_API_KEY", fake_key)
    events = [{"translation": {"translation_error": f"RuntimeError: Incorrect API key {fake_key}"}}]
    _run(monkeypatch, tmp_path, _Workflow(events, RuntimeError("stop")))
    text = (tmp_path / "A_9" / "attempt_01" / "meta.json").read_text(encoding="utf-8")
    assert fake_key not in text and "[REDACTED]" in text


def test_unparseable_200_response_is_recorded(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    call_log.configure(tmp_path / "calls.jsonl", {})
    r = MagicMock()
    r.status_code = 200
    r.headers = {}
    r.text = "<html>gateway</html>"
    r.json.side_effect = ValueError("not json")
    client = MagicMock()
    client.post.return_value = r
    with patch.object(llm_mod, "_get_http_client", return_value=client):
        with pytest.raises(ValueError):
            llm_mod.call_llm("s", "u", model="gpt-5")
    row = json.loads((tmp_path / "calls.jsonl").read_text(encoding="utf-8"))
    assert row["status"] == "error" and row["attempts"][0]["error_type"] == "ValueError"


def test_partial_kept_for_generic_clustering_error():
    from agents import pi as pi_mod
    team = [{"role": "A Specialist", "focus": "f"}]
    with patch.object(pi_mod, "decide_team", return_value=team), \
         patch.object(pi_mod, "_cluster_similar_roles", side_effect=RuntimeError("HTTP 500")):
        with pytest.raises(AgentFailureError) as exc:
            pi_mod.decide_team_statistically("q", n_trials=2)
    assert len(exc.value.partial["team_selection_data"]["all_teams"]) == 2


def test_masking_bold_table_row():
    masked, n = critic_mod.mask_score_mentions("| **Readability** | **3** | **4** |")
    assert n == 1 and "3" not in masked and "4" not in masked


@pytest.mark.parametrize("bad_team", [
    [{"role": 123, "focus": "f"}],
    [{"role": "A and B Specialist", "focus": "f"}, {"role": "A Specialist", "focus": "g"}],  # duplicates after shortening
])
def test_selection_post_processing_errors_keep_partial(bad_team):
    from agents import pi as pi_mod
    team = [{"role": "A Specialist", "focus": "f"}]
    clusters = json.dumps({"clusters": [{"canonical": "A Specialist", "members": ["A Specialist"]}]})
    selection = json.dumps({"team": bad_team, "rationale": "r"})
    with patch.object(pi_mod, "decide_team", return_value=team), \
         patch.object(pi_mod, "call_gpt", side_effect=[clusters, selection]):
        with pytest.raises(AgentFailureError) as exc:
            pi_mod.decide_team_statistically("q", n_trials=2)
    assert len(exc.value.partial["team_selection_data"]["all_teams"]) == 2


# ---------- pilot-driven changes (2026-11-06): score-free feedback at the source ----------

def _closing(mode, monkeypatch):
    monkeypatch.setenv("VIRTUAL_LAB_CRITIC_MODE", mode)
    seen = {}

    def fake(system, user, tag=None):
        seen["user"] = user
        return _valid()

    with patch.object(critic_mod, "web_search") as ws, patch.object(critic_mod, "call_critic", side_effect=fake):
        ws.invoke.return_value = ""
        critic_mod.run_critic(_state_with_leaky_outputs())
    return seen["user"]


def test_condition_a_asks_for_score_free_feedback(monkeypatch):
    msg = _closing("independent", monkeypatch)
    assert "concrete actions to address the remaining weaknesses" in msg
    assert "Do not mention numeric scores" in msg and "reach 5/5" not in msg


def test_condition_b_closing_unchanged(monkeypatch):
    msg = _closing("cumulative", monkeypatch)
    assert "concrete actions to reach 5/5" in msg and "Do not mention numeric scores" not in msg
    assert "do not lower the score" in msg


def test_prompts_a_and_b_feedback_instructions():
    root = Path(__file__).resolve().parents[2]
    a = (root / "prompts_A" / "system" / "critic.md").read_text(encoding="utf-8")
    b = (root / "prompts_B" / "system" / "critic.md").read_text(encoding="utf-8")
    assert "Concrete actions to address the remaining weaknesses." in a and "do not mention numeric scores" in a
    assert "Concrete actions required to reach 5/5." in b and "do not mention numeric scores" not in b


@pytest.mark.parametrize("text", ["readability remains (4)", "Readability stays at 4.", "carry universality to 5."])
def test_narrow_backstop_catches_known_phrasings(text):
    masked, n = critic_mod.mask_score_mentions(text)
    assert n >= 1 and not any(d in masked for d in "12345"), masked


@pytest.mark.parametrize("text", [
    "SDN-1/2 edits", "SDN-1 and SDN-3 edits; CXG 45-2003; 20 nucleotides; (1) Gloss the term",
    "Round 2 feedback", "Step 3 applies", "Evidence from 3 studies supports SDN-1.",
])
def test_narrow_backstop_keeps_scientific_content(text):
    assert critic_mod.mask_score_mentions(text) == (text, 0)


def test_no_aggressive_rule_remains():
    assert not hasattr(critic_mod, "mask_feedback_scores")


def test_narrow_backstop_holds_at():
    masked, n = critic_mod.mask_score_mentions("readability holds at (4).")
    assert n == 1 and "4" not in masked
