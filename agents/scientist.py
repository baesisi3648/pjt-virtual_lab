"""Specialist Agents for NGT Safety Analysis.

The PI-composed specialist team performs domain analyses in parallel.
All system prompts and user-message templates are loaded from external prompt
assets so they can be kept private when publishing the codebase.

Optimisations:
- Specialists run concurrently (ThreadPoolExecutor).
- RAG / Web / EFSA searches run in parallel and are cached for later rounds.
"""
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from workflow.state import AgentState
from tools.rag_search import rag_search_tool
from tools.web_search import web_search, efsa_search
from agents.factory import create_specialist
from utils.prompt_loader import load_system, render

logger = logging.getLogger(__name__)


# Per-axis labels used both in revision messages and downstream UIs.
AXIS_LABELS = {
    "evidence": "scientific evidence",
    "universality": "universality",
    "proportionality": "proportionality",
    "readability": "readability",
}


def _extract_sources(text: str) -> list[str]:
    """Extract source citations from search-result text."""
    sources = []
    for match in re.findall(r'\[Source:\s*(https?://[^\]]+)\]', text):
        source = f"[Web] {match.strip()}"
        if source not in sources:
            sources.append(source)
    for match in re.findall(r'\[출처:\s*(https?://[^\]]+)\]', text):
        source = f"[Web] {match.strip()}"
        if source not in sources:
            sources.append(source)
    for match in re.findall(r'\*\*Source\*\*:\s*(.+?)(?:\n|$)', text):
        source = f"[Document] {match.strip()}"
        if source not in sources:
            sources.append(source)
    for match in re.findall(r'\*\*출처\*\*:\s*(.+?)(?:\n|$)', text):
        source = f"[Document] {match.strip()}"
        if source not in sources:
            sources.append(source)
    return sources


def _perform_searches(topic: str, state: AgentState) -> tuple[str, str, str]:
    """Run RAG / Web / EFSA searches in parallel; cache for later rounds."""
    current_round = state.get("current_round", 1)

    if current_round > 1:
        cached_rag = state.get("cached_rag_context", "")
        cached_web = state.get("cached_web_context", "")
        cached_efsa = state.get("cached_efsa_context", "")
        if cached_rag or cached_web:
            print(f"  [CACHE] Using cached search results from Round 1")
            logger.info(f"Using cached search results (Round {current_round})")
            return cached_rag, cached_web, cached_efsa

    print(f"  [SEARCH] Running parallel RAG + Web + EFSA searches...")

    def do_rag_search() -> str:
        try:
            result = rag_search_tool.invoke({"query": f"{topic} NGT safety assessment"})
            logger.info("RAG search completed")
            return f"\n\n[Reference regulatory documents]\n{result}"
        except Exception as e:
            logger.warning(f"RAG search failed: {e}")
            return ""

    def do_web_search() -> str:
        try:
            result = web_search.invoke({"query": f"{topic} NGT regulation 2025"})
            logger.info("Web search completed")
            return f"\n\n[Recent web search results]\n{result}"
        except Exception as e:
            logger.warning(f"Web search failed: {e}")
            return ""

    def do_efsa_search() -> str:
        try:
            result = efsa_search.invoke({"query": f"{topic} NGT safety assessment EFSA"})
            logger.info("EFSA search completed")
            return f"\n\n[EFSA Journal search results]\n{result}"
        except Exception as e:
            logger.warning(f"EFSA search failed: {e}")
            return ""

    with ThreadPoolExecutor(max_workers=3) as executor:
        rag_future = executor.submit(do_rag_search)
        web_future = executor.submit(do_web_search)
        efsa_future = executor.submit(do_efsa_search)

        rag_context = rag_future.result()
        web_context = web_future.result()
        efsa_context_result = efsa_future.result()

    print(f"  [SEARCH] Parallel searches completed")
    print(f"    - RAG: {len(rag_context)} chars")
    print(f"    - Web: {len(web_context)} chars")
    print(f"    - EFSA: {len(efsa_context_result)} chars")

    return rag_context, web_context, efsa_context_result


def _run_single_specialist(
    profile: dict,
    topic: str,
    constraints: str,
    rag_context: str,
    web_context: str,
    index: int,
    total: int,
) -> dict:
    """Execute a single specialist's initial analysis (Round 1)."""
    role = profile.get("role", f"Specialist {index+1}")
    focus = profile.get("focus", "")

    print(f"  [{index+1}/{total}] START {role}: {focus} (parallel execution...)")

    try:
        agent = create_specialist(profile)

        query_template = load_system("specialist_query")
        query = render(
            query_template,
            TOPIC=topic,
            CONSTRAINTS=constraints,
            FOCUS=focus,
            RAG_CONTEXT=rag_context,
            WEB_CONTEXT=web_context,
        )
        output = agent.invoke(query)

        output_preview = output[:200] + "..." if len(output) > 200 else output
        message = {
            "role": "specialist",
            "name": role,
            "content": f"[{role}] Analysis complete.\n\n{output_preview}",
        }

        print(f"  [{index+1}/{total}] DONE {role}: {len(output)} chars")

        return {
            "role": role,
            "focus": focus,
            "output": output,
            "message": message,
        }

    except Exception as e:
        logger.error(f"Specialist {role} failed: {e}")
        print(f"  [{index+1}/{total}] FAILED {role}: {e}")

        return {
            "role": role,
            "focus": focus,
            "output": f"Analysis failed: {str(e)}",
            "message": None,
        }


def run_specialists(state: AgentState) -> dict:
    """Round 1 — every specialist performs an initial domain analysis."""
    team = state.get("team", [])
    topic = state["topic"]
    constraints = state.get("constraints", "")

    print(f"\n{'#'*80}")
    print(f"[SPECIALISTS] Running {len(team)} specialist agents (Round 1)")
    print(f"  Topic: {topic}")
    print(f"  PARALLEL MODE: {len(team)} specialists running concurrently")
    print(f"{'#'*80}\n")

    rag_context, web_context, efsa_context = _perform_searches(topic, state)

    specialist_outputs = []
    messages = list(state.get("messages", []))

    print(f"\n  [PARALLEL EXECUTION] Launching {len(team)} specialist threads...")

    with ThreadPoolExecutor(max_workers=len(team)) as executor:
        futures = []
        for i, profile in enumerate(team):
            combined_web = web_context + efsa_context
            future = executor.submit(
                _run_single_specialist,
                profile, topic, constraints, rag_context, combined_web, i, len(team)
            )
            futures.append(future)

        for future in as_completed(futures):
            result = future.result()
            specialist_outputs.append({
                "role": result["role"],
                "focus": result["focus"],
                "output": result["output"],
            })
            if result["message"]:
                messages.append(result["message"])

    collected_sources = list(state.get("sources", []))
    collected_sources.extend(_extract_sources(rag_context))
    collected_sources.extend(_extract_sources(web_context))
    collected_sources.extend(_extract_sources(efsa_context))
    for so in specialist_outputs:
        collected_sources.extend(_extract_sources(so.get("output", "")))
    seen = set()
    unique_sources = []
    for s in collected_sources:
        if s not in seen:
            seen.add(s)
            unique_sources.append(s)

    print(f"\n[SPECIALISTS] All {len(team)} specialists completed (PARALLEL)")
    print(f"  Sources collected: {len(unique_sources)}\n")

    return {
        "specialist_outputs": specialist_outputs,
        "messages": messages,
        "sources": unique_sources,
        "cached_rag_context": rag_context,
        "cached_web_context": web_context,
        "cached_efsa_context": efsa_context,
    }


def run_round_revision(state: AgentState) -> dict:
    """Specialists revise their analyses using prior-round critique and PI synthesis."""
    team = state.get("team", [])
    current_round = state.get("current_round", 2)
    critique = state.get("critique")
    pi_summary = state.get("draft", "")
    prev_outputs = state.get("specialist_outputs", [])
    topic = state["topic"]
    constraints = state.get("constraints", "")

    print(f"\n{'#'*80}")
    print(f"[ROUND REVISION] Running {len(team)} specialist revisions - Round {current_round}")
    print(f"  Topic: {topic}")
    print(f"  PARALLEL MODE: {len(team)} specialists running concurrently")
    print(f"{'#'*80}\n")

    prev_map = {so.get("role", ""): so.get("output", "") for so in prev_outputs}

    specialist_outputs = []
    messages = list(state.get("messages", []))

    meeting_history = state.get("meeting_history", [])

    revision_template = load_system("specialist_revision_query")

    def _build_cumulative_feedback(role: str) -> str:
        """Concatenate every prior round's per-specialist feedback for `role`."""
        cumulative = []
        for record in meeting_history:
            round_num = record.get("round", 0)
            prev_fb = record.get("specialist_feedback", {}).get(role, "")
            prev_sc = record.get("critique_scores", {}).get(role, "")
            if prev_fb or prev_sc:
                if isinstance(prev_sc, dict):
                    sc_str = ", ".join(
                        f"{AXIS_LABELS.get(a, a)}={s}" for a, s in prev_sc.items()
                    )
                else:
                    sc_str = str(prev_sc)
                cumulative.append(
                    f"  [Round {round_num}] scores: {sc_str}\n  feedback: {prev_fb}"
                )
        return "\n".join(cumulative)

    def _run_single_revision(profile: dict, index: int) -> dict:
        role = profile.get("role", f"Specialist {index+1}")
        focus = profile.get("focus", "")

        my_feedback = ""
        my_axis_scores = {}
        my_score_text = ""
        if critique and critique.specialist_feedback:
            my_feedback = critique.specialist_feedback.get(role, "")
        if critique and critique.scores:
            score_val = critique.scores.get(role, {})
            if isinstance(score_val, dict):
                my_axis_scores = score_val
                parts = [
                    f"{AXIS_LABELS.get(a, a)}={s}/5" for a, s in score_val.items()
                ]
                my_score_text = f" (axis scores: {', '.join(parts)})"
            elif score_val:
                my_axis_scores = {a: int(score_val) for a in AXIS_LABELS}
                my_score_text = f" (previous score: {score_val}/5)"

        min_score = min(my_axis_scores.values()) if my_axis_scores else 3
        weak_axes = (
            [AXIS_LABELS.get(a, a) for a, s in my_axis_scores.items() if s == min_score]
            if my_axis_scores
            else []
        )

        cumulative_fb = _build_cumulative_feedback(role)

        score_guidance_parts = []
        for axis, label in AXIS_LABELS.items():
            s = my_axis_scores.get(axis, 3)
            if s >= 5:
                score_guidance_parts.append(f"- {label}: 5/5. Maintain.")
            elif s >= 4:
                score_guidance_parts.append(
                    f"- {label}: {s}/5. Refine further toward 5/5."
                )
            elif s >= 3:
                score_guidance_parts.append(
                    f"- {label}: {s}/5. ★ Improvement needed; focus here."
                )
            else:
                score_guidance_parts.append(
                    f"- {label}: {s}/5. ★★ Substantial improvement required."
                )
        score_guidance = "\n".join(score_guidance_parts)
        if weak_axes:
            score_guidance += (
                f"\n\nTop priority for improvement: {', '.join(weak_axes)} "
                f"({min_score}/5)"
            )

        cumulative_block = (
            f"[Cumulative prior-round feedback]\n{cumulative_fb}\n\n"
            if cumulative_fb
            else ""
        )

        print(
            f"  [{index+1}/{len(team)}] START {role}: {focus} "
            f"(Round {current_round}){my_score_text} (parallel execution...)"
        )

        try:
            agent = create_specialist(profile)

            query = render(
                revision_template,
                ROUND=str(current_round),
                TOPIC=topic,
                CONSTRAINTS=constraints,
                FOCUS=focus,
                PREVIOUS_OUTPUT=prev_map.get(role, ""),
                SCORE_TEXT=my_score_text,
                MY_FEEDBACK=my_feedback,
                CUMULATIVE_FEEDBACK_BLOCK=cumulative_block,
                PI_SUMMARY=pi_summary,
                SCORE_GUIDANCE=score_guidance,
            )
            output = agent.invoke(query, max_tokens=32768)

            output_preview = output[:200] + "..." if len(output) > 200 else output
            message = {
                "role": "specialist",
                "name": role,
                "content": (
                    f"[Round {current_round}] [{role}] Revised analysis complete.\n\n"
                    f"{output_preview}"
                ),
            }

            print(
                f"  [{index+1}/{len(team)}] DONE {role}: {len(output)} chars (revised)"
            )

            return {
                "role": role,
                "focus": focus,
                "output": output,
                "message": message,
            }

        except Exception as e:
            logger.error(f"Specialist {role} revision failed: {e}")
            print(f"  [{index+1}/{len(team)}] FAILED {role}: {e}")

            return {
                "role": role,
                "focus": focus,
                "output": prev_map.get(role, f"Revision failed: {str(e)}"),
                "message": None,
            }

    print(f"\n  [PARALLEL EXECUTION] Launching {len(team)} revision threads...")

    with ThreadPoolExecutor(max_workers=len(team)) as executor:
        futures = []
        for i, profile in enumerate(team):
            future = executor.submit(_run_single_revision, profile, i)
            futures.append(future)

        for future in as_completed(futures):
            result = future.result()
            specialist_outputs.append({
                "role": result["role"],
                "focus": result["focus"],
                "output": result["output"],
            })
            if result["message"]:
                messages.append(result["message"])

    collected_sources = list(state.get("sources", []))
    for so in specialist_outputs:
        collected_sources.extend(_extract_sources(so.get("output", "")))
    seen = set()
    unique_sources = []
    for s in collected_sources:
        if s not in seen:
            seen.add(s)
            unique_sources.append(s)

    print(f"\n[ROUND REVISION] All {len(team)} specialists revised (PARALLEL)")
    print(f"  Sources collected: {len(unique_sources)}\n")

    return {
        "specialist_outputs": specialist_outputs,
        "messages": messages,
        "sources": unique_sources,
    }
