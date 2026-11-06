"""Scientific Critic Agent.

Reviews each specialist contribution along four axes (evidence, universality,
proportionality, readability) and emits per-specialist scores plus structured
feedback. The system prompt and reference rubric are loaded from external
prompt assets so they can be kept private when publishing the codebase.
"""
import json
import logging
import re

from data.guidelines import CRITIQUE_RUBRIC, ACADEMIC_TONE_GUIDE
from utils.llm import call_gpt
from utils.prompt_loader import load_system, render
from utils.search_query import disambiguate
from workflow.state import AgentState, CritiqueResult
from tools.web_search import web_search
from utils.errors import CritiqueValidationError

logger = logging.getLogger(__name__)


SYSTEM_PROMPT: str = render(
    load_system("critic"),
    CRITIQUE_RUBRIC=CRITIQUE_RUBRIC,
    ACADEMIC_TONE_GUIDE=ACADEMIC_TONE_GUIDE,
).strip()


SCORE_AXES = ("evidence", "universality", "proportionality", "readability")

# Same-input retries allowed when the Critic response fails validation (C3).
CRITIC_VALIDATION_RETRIES = 1


def parse_and_validate_critique(response_content: str, expected_roles: list[str]) -> CritiqueResult:
    """Parse the Critic JSON and require complete, in-range scores for every role.

    Raises CritiqueValidationError if the JSON is malformed, if any team role is
    missing or an unknown role appears, if any of the four axes is missing, if a
    score is not an integer from 1 to 5, or if per-specialist feedback is missing.
    No default scores are substituted.
    """
    content = response_content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1])
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise CritiqueValidationError(f"invalid JSON: {e}") from e
    if not isinstance(data, dict):
        raise CritiqueValidationError("top-level JSON is not an object")

    raw_scores = data.get("scores")
    if not isinstance(raw_scores, dict):
        raise CritiqueValidationError("'scores' is missing or not an object")
    expected = set(expected_roles)
    got = set(raw_scores)
    if got != expected:
        raise CritiqueValidationError(
            f"score keys do not match the team (missing={sorted(expected - got)}, "
            f"unexpected={sorted(got - expected)})"
        )

    scores: dict[str, dict[str, int]] = {}
    for role in expected_roles:
        val = raw_scores[role]
        if not isinstance(val, dict) or set(val) != set(SCORE_AXES):
            raise CritiqueValidationError(f"{role}: axes must be exactly {SCORE_AXES}, got {val!r}")
        axis_scores = {}
        for axis in SCORE_AXES:
            s = val[axis]
            if isinstance(s, bool) or not isinstance(s, int) or not 1 <= s <= 5:
                raise CritiqueValidationError(f"{role}.{axis}: score must be an integer 1-5, got {s!r}")
            axis_scores[axis] = s
        scores[role] = axis_scores

    specialist_feedback = data.get("specialist_feedback")
    if not isinstance(specialist_feedback, dict):
        raise CritiqueValidationError("'specialist_feedback' is missing or not an object")
    for role in expected_roles:
        fb = specialist_feedback.get(role)
        if not isinstance(fb, str) or not fb.strip():
            raise CritiqueValidationError(f"{role}: per-specialist feedback is missing")

    return CritiqueResult(
        decision=str(data.get("decision", "continue")),
        feedback=str(data.get("feedback", "")),
        scores=scores,
        specialist_feedback={r: specialist_feedback[r] for r in expected_roles},
    )


def run_critic(state: AgentState) -> dict:
    """Run the Critic agent — produces per-specialist scores and feedback."""
    current_round = state.get("current_round", 1)
    specialist_outputs = state.get("specialist_outputs", [])
    expected_roles = [m["role"] for m in state.get("team", [])]
    if not expected_roles or len(set(expected_roles)) != len(expected_roles):
        raise CritiqueValidationError(f"team roles are empty or duplicated: {expected_roles}")
    expected_keys = ", ".join(f'"{r}"' for r in expected_roles)

    print(f"\n{'#'*80}")
    print(f"[CRITIC] Starting Critic agent — Round {current_round}")
    print(f"  Specialist outputs: {len(specialist_outputs)}")
    print(f"{'#'*80}\n")

    # Step 1: gather verification context via web search
    # C12 (revision): a failed search raises SearchError instead of being skipped.
    web_context = ""
    web_result = web_search.invoke({"query": disambiguate(state["topic"], "regulatory verification")})
    if web_result:
        web_context = f"\n\n## [Web search results — verification context]\n{web_result}"
    logger.info("Critic web search completed")

    # Step 2: assemble specialist outputs
    specialist_context = ""
    for so in specialist_outputs:
        specialist_context += (
            f"\n\n### [{so.get('role', 'Specialist')}] ({so.get('focus', '')})\n"
            f"{so.get('output', '')}\n"
        )

    # prior-round records (per-specialist scores and feedback accumulated)
    meeting_history = state.get("meeting_history", [])
    history_context = ""
    if meeting_history:
        for record in meeting_history:
            round_num = record.get("round", 0)
            scores = record.get("critique_scores", {})
            feedback = record.get("critique_feedback", "")
            spec_fb = record.get("specialist_feedback", {})
            history_context += f"\n[Round {round_num} critique record]\n"
            history_context += f"Overall feedback: {feedback}\n"
            if scores:
                history_context += "Per-specialist scores:\n"
                for role, score in scores.items():
                    history_context += f"  - {role}: {score}/5\n"
            if spec_fb:
                history_context += "Per-specialist detailed feedback:\n"
                for role, fb in spec_fb.items():
                    history_context += f"  - {role}: {fb}\n"

    # Step 3: build the user message
    user_message = f"""[Team meeting Round {current_round} — critique stage]

[Per-specialist analyses]
{specialist_context}
{web_context}

{f'[Prior-round critique records]{history_context}' if history_context else ''}

Review each specialist's analysis individually and respond in JSON.
Use each specialist's role name as the key, exactly as written here: {expected_keys}.

★ Round {current_round} scoring rules:
- If a weakness flagged in a previous round has been resolved, raise the score.
- If previously credited strengths persist, do not lower the score.
- Include in `specialist_feedback` the items "what improved", "remaining weaknesses", and "concrete actions to reach 5/5"."""

    # Step 4: call the Critic model and validate the response (C3, revision).
    # The submitted version filled missing or malformed scores with a default of 3
    # and continued with empty scores when JSON parsing failed. The revision retries
    # once with the same input and otherwise fails closed.
    attempts: list[str] = []
    critique = None
    last_error: Exception | None = None
    for attempt in range(1 + CRITIC_VALIDATION_RETRIES):
        print(f"[CRITIC] Calling Critic model (attempt {attempt + 1})")
        response_content = call_gpt(SYSTEM_PROMPT, user_message)
        attempts.append(response_content)
        try:
            critique = parse_and_validate_critique(response_content, expected_roles)
            break
        except CritiqueValidationError as e:
            last_error = e
            logger.warning(f"Critic response invalid (attempt {attempt + 1}): {e}")
    if critique is None:
        raise CritiqueValidationError(
            f"Critic response invalid after {len(attempts)} attempts: {last_error}"
        )

    for role, axis_scores in critique.scores.items():
        axis_str = " ".join(f"{a[0].upper()}={s}" for a, s in axis_scores.items())
        print(f"[CRITIC] {role}: {axis_str}")

    # message log
    messages = list(state.get("messages", []))
    scores_parts = []
    for role, axis_scores in (critique.scores or {}).items():
        if isinstance(axis_scores, dict):
            avg = sum(axis_scores.values()) / len(axis_scores) if axis_scores else 0
            scores_parts.append(f"{role}=avg{avg:.1f}")
        else:
            scores_parts.append(f"{role}={axis_scores}")
    scores_str = ", ".join(scores_parts)
    messages.append({
        "role": "critic",
        "content": f"[Round {current_round}] Reviewed specialist analyses. (scores: {scores_str})\n{critique.feedback}",
    })

    # Reproducibility: append a structured snapshot for this round.
    score_history = list(state.get("critic_score_history", []))
    score_history.append({
        "round": current_round,
        "scores": critique.scores or {},
        "specialist_feedback": critique.specialist_feedback or {},
    })

    return {
        "critique": critique,
        "messages": messages,
        "critic_score_history": score_history,
    }
