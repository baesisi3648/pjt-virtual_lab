"""Revision step 3: fail-closed behaviour (C3, C12-C15, C18) with mocked I/O.

No network or paid API calls are made.
"""
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
# Prompts are loaded at import time; use the revision set (which lacks the three
# unused data files) to also verify C18.
os.environ["VIRTUAL_LAB_PROMPTS_DIR"] = str(ROOT / "prompts_A")

from agents import critic as critic_mod  # noqa: E402
from agents import scientist as scientist_mod  # noqa: E402
from utils import llm as llm_mod  # noqa: E402
from utils.errors import (  # noqa: E402
    AgentFailureError,
    CritiqueValidationError,
    LLMIncompleteError,
    SearchError,
)
from workflow import graph as graph_mod  # noqa: E402
from workflow.state import CritiqueResult  # noqa: E402

ROLES = ["Alpha Specialist", "Beta Specialist"]
AXES = ("evidence", "universality", "proportionality", "readability")


def _critic_json(scores=None, feedback=None, drop=None):
    scores = scores or {r: {a: 4 for a in AXES} for r in ROLES}
    feedback = feedback or {r: "fb" for r in ROLES}
    if drop:
        scores.pop(drop, None)
    return json.dumps({"decision": "continue", "feedback": "ok", "scores": scores,
                       "specialist_feedback": feedback})


# ---------- C3: Critic validation ----------

def test_valid_critique_parses():
    c = critic_mod.parse_and_validate_critique(_critic_json(), ROLES)
    assert set(c.scores) == set(ROLES) and c.scores["Alpha Specialist"]["evidence"] == 4


@pytest.mark.parametrize("bad", [
    _critic_json(drop="Beta Specialist"),                                            # missing role
    _critic_json(scores={**{r: {a: 4 for a in AXES} for r in ROLES}, "Gamma": {a: 4 for a in AXES}}),  # extra role
    _critic_json(scores={r: {"evidence": 4} for r in ROLES}),                        # missing axes
    _critic_json(scores={r: {a: 6 for a in AXES} for r in ROLES}),                   # out of range
    _critic_json(scores={r: {a: 4.0 for a in AXES} for r in ROLES}),                 # float
    _critic_json(scores={r: {a: True for a in AXES} for r in ROLES}),                # bool
    _critic_json(feedback={"Alpha Specialist": "fb"}),                               # missing feedback
    "not json",
])
def test_invalid_critique_rejected(bad):
    with pytest.raises(CritiqueValidationError):
        critic_mod.parse_and_validate_critique(bad, ROLES)


def _critic_state():
    return {"topic": "t", "current_round": 1, "team": [{"role": r, "focus": "f"} for r in ROLES],
            "specialist_outputs": [{"role": r, "focus": "f", "output": "x"} for r in ROLES],
            "meeting_history": [], "messages": [], "critic_score_history": []}


def test_run_critic_retries_once_then_succeeds():
    replies = iter(["not json", _critic_json()])
    with patch.object(critic_mod, "web_search") as ws, \
         patch.object(critic_mod, "call_gpt", side_effect=lambda *a, **k: next(replies)) as cg:
        ws.invoke.return_value = ""
        out = critic_mod.run_critic(_critic_state())
    assert cg.call_count == 2 and set(out["critique"].scores) == set(ROLES)


def test_run_critic_fails_closed_after_retry():
    with patch.object(critic_mod, "web_search") as ws, \
         patch.object(critic_mod, "call_gpt", return_value=_critic_json(drop="Beta Specialist")):
        ws.invoke.return_value = ""
        with pytest.raises(CritiqueValidationError):
            critic_mod.run_critic(_critic_state())


def test_run_critic_search_failure_aborts():
    with patch.object(critic_mod, "web_search") as ws:
        ws.invoke.side_effect = SearchError("down")
        with pytest.raises(SearchError):
            critic_mod.run_critic(_critic_state())


# ---------- C3: early-stop decision ----------

def _round_state(rnd, scores):
    return {"current_round": rnd, "team": [{"role": r} for r in ROLES],
            "critique": CritiqueResult(decision="continue", feedback="", scores=scores)}


def test_all_five_stops_early():
    s = {r: {a: 5 for a in AXES} for r in ROLES}
    assert graph_mod.check_round(_round_state(2, s)) == "final_synthesis"


def test_not_all_five_continues_until_cap():
    s = {r: {a: 5 for a in AXES} for r in ROLES}
    s["Beta Specialist"]["readability"] = 4
    assert graph_mod.check_round(_round_state(3, s)) == "increment_round"
    assert graph_mod.check_round(_round_state(graph_mod.MAX_ROUNDS, s)) == "final_synthesis"


def test_incomplete_scores_never_stop_or_continue():
    s = {"Alpha Specialist": {a: 5 for a in AXES}}            # Beta missing
    with pytest.raises(CritiqueValidationError):
        graph_mod.check_round(_round_state(2, s))
    with pytest.raises(CritiqueValidationError):
        graph_mod.check_round(_round_state(2, {}))


# ---------- C13: truncated / empty LLM responses ----------

def _http_response(content, finish_reason):
    r = MagicMock()
    r.status_code = 200
    r.json.return_value = {"model": "m", "usage": {},
                           "choices": [{"message": {"content": content}, "finish_reason": finish_reason}]}
    return r


def test_llm_retries_truncated_then_succeeds(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    client = MagicMock()
    client.post.side_effect = [_http_response("partial", "length"), _http_response("full", "stop")]
    with patch.object(llm_mod, "_get_http_client", return_value=client):
        assert llm_mod.call_llm("s", "u", model="gpt-5") == "full"


@pytest.mark.parametrize("content,reason", [("", "stop"), ("partial", "length")])
def test_llm_fails_closed_on_repeated_incomplete(monkeypatch, content, reason):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    client = MagicMock()
    client.post.return_value = _http_response(content, reason)
    with patch.object(llm_mod, "_get_http_client", return_value=client):
        with pytest.raises(LLMIncompleteError):
            llm_mod.call_llm("s", "u", model="gpt-5")
    assert client.post.call_count == 1 + llm_mod.MAX_INCOMPLETE_RETRIES


# ---------- C12: search tools ----------

def test_web_search_error_raises():
    import importlib
    ws_mod = importlib.import_module("tools.web_search")
    client = MagicMock()
    client.search_sync.side_effect = RuntimeError("api down")
    with patch.object(ws_mod, "get_tavily_client", return_value=client):
        with pytest.raises(SearchError):
            ws_mod.web_search.invoke({"query": "q"})
        with pytest.raises(SearchError):
            ws_mod.efsa_search.invoke({"query": "q"})


def test_web_search_empty_returns_nothing():
    import importlib
    ws_mod = importlib.import_module("tools.web_search")
    client = MagicMock()
    client.search_sync.return_value = {}
    with patch.object(ws_mod, "get_tavily_client", return_value=client):
        assert ws_mod.web_search.invoke({"query": "q"}) == ""


# ---------- C14: specialist failures ----------

def test_specialist_round1_failure_raises():
    agent = MagicMock()
    agent.invoke.side_effect = RuntimeError("boom")
    with patch.object(scientist_mod, "create_specialist", return_value=agent):
        with pytest.raises(AgentFailureError):
            scientist_mod._run_single_specialist({"role": "Alpha Specialist", "focus": "f"},
                                                 "t", "c", "", "", 0, 1)


# ---------- C18: unused assets removed ----------

def test_unused_assets_not_loaded():
    import data.guidelines as g
    for name in ("RESEARCH_OBJECTIVE", "CODEX_PRINCIPLES", "REGULATORY_TRENDS"):
        assert not hasattr(g, name)
    for f in ("research_objective.md", "codex_principles.md", "regulatory_trends.md"):
        assert not (ROOT / "prompts_A" / "data" / f).exists()
