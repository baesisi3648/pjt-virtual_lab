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
from workflow.state import AgentState, CritiqueResult
from tools.web_search import web_search

logger = logging.getLogger(__name__)


SYSTEM_PROMPT: str = render(
    load_system("critic"),
    CRITIQUE_RUBRIC=CRITIQUE_RUBRIC,
    ACADEMIC_TONE_GUIDE=ACADEMIC_TONE_GUIDE,
).strip()


def run_critic(state: AgentState) -> dict:
    """Run the Critic agent — produces per-specialist scores and feedback."""
    current_round = state.get("current_round", 1)
    specialist_outputs = state.get("specialist_outputs", [])

    print(f"\n{'#'*80}")
    print(f"[CRITIC] Starting Critic agent — Round {current_round}")
    print(f"  Specialist outputs: {len(specialist_outputs)}")
    print(f"{'#'*80}\n")

    # Step 1: gather verification context via web search
    web_context = ""
    try:
        web_result = web_search.invoke({"query": f"{state['topic']} NGT safety regulation verification"})
        web_context = f"\n\n## [Web search results — verification context]\n{web_result}"
        logger.info("Critic web search completed")
    except Exception as e:
        logger.warning(f"Critic web search failed: {e}")

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
Use each specialist's role name as the key.

★ Round {current_round} scoring rules:
- If a weakness flagged in a previous round has been resolved, raise the score.
- If previously credited strengths persist, do not lower the score.
- Include in `specialist_feedback` the items "what improved", "remaining weaknesses", and "concrete actions to reach 5/5"."""

    # Step 4: call OpenAI
    print(f"[CRITIC] Calling OpenAI API via call_gpt")
    logger.info("Critic: Calling OpenAI directly...")

    try:
        response_content = call_gpt(SYSTEM_PROMPT, user_message)
        print(f"[CRITIC] OpenAI call succeeded — Response: {len(response_content)} chars")
    except Exception as e:
        print(f"[CRITIC ERROR] {type(e).__name__}: {e}")
        raise

    # JSON parsing — per-axis scores (evidence, universality, proportionality, readability)
    SCORE_AXES = ("evidence", "universality", "proportionality", "readability")
    DEFAULT_AXIS_SCORES = {axis: 3 for axis in SCORE_AXES}

    def _normalize_scores(raw: dict) -> dict:
        """Normalise per-specialist scores to `{role: {axis: int}}`."""
        normalized = {}
        for role, val in raw.items():
            if isinstance(val, dict):
                axis_scores = {}
                for axis in SCORE_AXES:
                    try:
                        axis_scores[axis] = int(val.get(axis, 3))
                    except (ValueError, TypeError):
                        axis_scores[axis] = 3
                normalized[role] = axis_scores
            elif isinstance(val, (int, float)):
                int_val = int(val)
                normalized[role] = {axis: int_val for axis in SCORE_AXES}
            else:
                m = re.search(r'(\d)', str(val))
                int_val = int(m.group(1)) if m else 3
                normalized[role] = {axis: int_val for axis in SCORE_AXES}
        return normalized

    try:
        content = response_content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])

        data = json.loads(content)
        raw_scores = data.get("scores", {})
        scores = _normalize_scores(raw_scores)

        decision = data.get("decision", "continue")
        feedback = data.get("feedback", "")
        specialist_feedback = data.get("specialist_feedback", {})

        if not scores and specialist_feedback:
            for role in specialist_feedback:
                scores[role] = dict(DEFAULT_AXIS_SCORES)
            logger.info(f"Critic scores empty, assigned defaults for {list(scores.keys())}")

        for role in specialist_feedback:
            if role not in scores:
                scores[role] = dict(DEFAULT_AXIS_SCORES)

        critique = CritiqueResult(
            decision=decision,
            feedback=feedback,
            scores=scores,
            specialist_feedback=specialist_feedback,
        )

        for role, axis_scores in scores.items():
            axis_str = " ".join(f"{a[0].upper()}={s}" for a, s in axis_scores.items())
            print(f"[CRITIC] {role}: {axis_str}")

    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Critic JSON parse failed: {e}, defaulting to continue")
        critique = CritiqueResult(
            decision="continue",
            feedback=response_content[:500],
            scores={},
            specialist_feedback={},
        )

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
