"""Scientific Critic Agent.

Reviews each specialist contribution along four axes (evidence, universality,
proportionality, readability) and emits per-specialist scores plus structured
feedback. The system prompt and reference rubric are loaded from external
prompt assets so they can be kept private when publishing the codebase.
"""
import json
import os
import logging
import re

from data.guidelines import CRITIQUE_RUBRIC, ACADEMIC_TONE_GUIDE
from utils.llm import call_critic
from utils.prompt_loader import load_system, render
from utils.search_query import disambiguate
from workflow.state import AgentState, CritiqueResult
from tools.web_search import web_search
from utils.errors import CritiqueValidationError
from utils.retrieval_snapshot import retrieve

logger = logging.getLogger(__name__)


SYSTEM_PROMPT: str = render(
    load_system("critic"),
    CRITIQUE_RUBRIC=CRITIQUE_RUBRIC,
    ACADEMIC_TONE_GUIDE=ACADEMIC_TONE_GUIDE,
).strip()


SCORE_AXES = ("evidence", "universality", "proportionality", "readability")

CRITIC_MODES = ("cumulative", "independent")

# Score mentions hidden from the Critic input in the "independent" mode (condition A).
# Applied to prior feedback and to specialist texts, because specialists receive their
# scores (common design element) and may restate them in revised analyses.
# Covers "4/5", "4.5 / 5", "score of 4", "scored 3", "rated 5", "evidence=4",
# "readability: **4**", "Readability (4)", "Universality is 5", "from 3 to 4".
# Kept deliberately narrow so that scientific content ("Evidence from 3 studies",
# "SDN-1", "20 nucleotides") is never masked.
_AXIS = r"(?:evidence|universality|proportionality|readability)"
_N = r"[1-5](?:\.\d)?"
_SCORE_PATTERNS = [
    # "4/5", "4.5 / 5"
    re.compile(_N + r"\s*/\s*5\b"),
    # "from 3 to 4", "3 -> 4", "3 → 4"
    re.compile(r"\bfrom\s+" + _N + r"\s+to\s+" + _N + r"\b", re.IGNORECASE),
    re.compile(r"\b" + _N + r"\s*(?:->|→|=>)\s*" + _N + r"\b"),
    # table rows: "| Readability | 3 | 4 |"
    re.compile(r"\b" + _AXIS + r"\b\**\s*\|(?:\s*\**\s*" + _N + r"\s*\**\s*\|)+", re.IGNORECASE),
    # "scored 3", "rated a 4"
    re.compile(r"\b(?:scored|rated)\s+(?:a\s+)?" + _N + r"\b", re.IGNORECASE),
    # "score of 4", "scores: 3", "rating = 2"
    re.compile(r"\b(?:scores?|rating)\s*(?:of|at|is|was|=|:)?\s*\**\s*" + _N + r"\b", re.IGNORECASE),
    # "Readability: 4", "evidence: **4**", "Readability (4)", "Universality is 5", and (added
    # after the pilot leakage audit) the Critic's own phrasings "carry universality to 5",
    # "close the evidence axis at 5", "holding readability below 4", "universality 5." —
    # the number must end the phrase (punctuation, bracket, emphasis, arrow, dash, "and"/"or"
    # or end of line), so "Evidence of 3 independent studies" is left untouched.
    re.compile(r"\b" + _AXIS + r"\b(?:\s+axis)?(?:\s+score)?"
               r"(?:\s+(?:remains?|stays?|stayed|sits?|holds?|held|reaches?|reached|lands?|landed|is|was|now|currently|still)){0,2}\s*(?:\*\*)?\s*"
               r"(?:[:=(]|\b(?:is|was|at|of|to|below|above|under|over|beyond|from)\b)?\s*\(?\s*\**\s*"
               + _N + r"(?=\s*(?:$|[).,;:*|/\-→=—–]|\band\b|\bor\b))", re.IGNORECASE | re.MULTILINE),
]


def critic_mode() -> str:
    """Critic scoring mode from VIRTUAL_LAB_CRITIC_MODE (default: submitted 'cumulative')."""
    mode = os.environ.get("VIRTUAL_LAB_CRITIC_MODE", "cumulative")
    if mode not in CRITIC_MODES:
        raise ValueError(f"Unknown VIRTUAL_LAB_CRITIC_MODE: {mode}")
    return mode


def mask_score_mentions(text: str) -> tuple[str, int]:
    """Replace numeric score mentions with "[score]"; return the text and the count.

    Narrow rules applied to prior feedback and specialist texts in condition A, as a
    backstop: scientific numbers ("SDN-1/2", "Evidence from 3 studies") must survive.
    The primary safeguard is at the source: the condition-A Critic is instructed not
    to put scores or score targets in its feedback text (prompts_A/system/critic.md).
    A stricter digit-masking rule tried after the pilot was removed because it
    damaged scientific content (revision_plan 7.6).
    """
    total = 0
    for pat in _SCORE_PATTERNS:
        text, n = pat.subn("[score]", text)
        total += n
    return text, total

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
    # C4: in replay mode the same fixed verification context is used in every round.
    web_result = retrieve("critic_web", web_search, disambiguate(state["topic"], "regulatory verification"))
    if web_result:
        web_context = f"\n\n## [Web search results — verification context]\n{web_result}"
    logger.info("Critic web search completed")

    # Step 2: assemble specialist outputs
    # Condition (C2, revision): "cumulative" = submitted scoring rules (condition B);
    # "independent" = current content only (condition A): no prior numeric scores,
    # score mentions masked in specialist texts and prior feedback, no
    # score-comparison rules. The specialists themselves still receive their scores
    # in both conditions (common design element).
    mode = critic_mode()
    masked_total = 0

    specialist_context = ""
    for so in specialist_outputs:
        output = so.get('output', '')
        if mode == "independent":
            output, n = mask_score_mentions(output)
            masked_total += n
        specialist_context += (
            f"\n\n### [{so.get('role', 'Specialist')}] ({so.get('focus', '')})\n"
            f"{output}\n"
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
            if mode == "independent":
                feedback, n = mask_score_mentions(feedback)
                masked_total += n
            history_context += f"\n[Round {round_num} critique record]\n"
            history_context += f"Overall feedback: {feedback}\n"
            if scores and mode == "cumulative":
                history_context += "Per-specialist scores:\n"
                for role, score in scores.items():
                    history_context += f"  - {role}: {score}/5\n"
            if spec_fb:
                history_context += "Per-specialist detailed feedback:\n"
                for role, fb in spec_fb.items():
                    if mode == "independent":
                        fb, n = mask_score_mentions(fb)
                        masked_total += n
                    history_context += f"  - {role}: {fb}\n"

    if mode == "cumulative":
        closing = (
            f"★ Round {current_round} scoring rules:\n"
            "- If a weakness flagged in a previous round has been resolved, raise the score.\n"
            "- If previously credited strengths persist, do not lower the score.\n"
            "- Include in `specialist_feedback` the items \"what improved\", \"remaining weaknesses\", "
            "and \"concrete actions to reach 5/5\"."
        )
    else:
        # Condition A (revision_plan 7.6): actions on the remaining weaknesses, and no
        # scores or score targets in the feedback text, so prior feedback carries no
        # score information into the next round.
        closing = (
            "- Include in `specialist_feedback` the items \"what improved\", \"remaining weaknesses\", "
            "and \"concrete actions to address the remaining weaknesses\".\n"
            "- Do not mention numeric scores, score levels or score targets in `feedback` or "
            "`specialist_feedback`; give scores only in the `scores` object."
        )

    # Step 3: build the user message
    user_message = f"""[Team meeting Round {current_round} — critique stage]

[Per-specialist analyses]
{specialist_context}
{web_context}

{f'[Prior-round critique records]{history_context}' if history_context else ''}

Review each specialist's analysis individually and respond in JSON.
Use each specialist's role name as the key, exactly as written here: {expected_keys}.

{closing}"""

    # Step 4: call the Critic model and validate the response (C3, revision).
    # The submitted version filled missing or malformed scores with a default of 3
    # and continued with empty scores when JSON parsing failed. The revision retries
    # once with the same input and otherwise fails closed.
    attempts: list[str] = []
    critique = None
    last_error: Exception | None = None
    for attempt in range(1 + CRITIC_VALIDATION_RETRIES):
        print(f"[CRITIC] Calling Critic model (attempt {attempt + 1})")
        response_content = call_critic(
            SYSTEM_PROMPT, user_message,
            tag={"agent": "Critic", "step": "critique", "round": current_round,
                 "validation_attempt": attempt + 1, "critic_mode": mode,
                 "masked_score_mentions": masked_total},
        )
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
