"""PI (Principal Investigator) Agent.

Coordinator of the deliberation. Responsible for:
- Composing a specialist team via repeated team-generation simulations.
- Summarising each round's discussion and producing an interim conclusion.
- Synthesising the multi-round deliberation into the final research report.

All system prompts are loaded from the external prompt assets at
`prompts/system/` so they can be kept private when publishing the codebase.
"""
import json
import logging
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from utils.llm import call_gpt
from utils.prompt_loader import load_system, render
from utils.search_query import disambiguate
from data.guidelines import RESEARCH_AGENDA, ACADEMIC_TONE_GUIDE
from workflow.state import AgentState
from tools.web_search import web_search
from utils.errors import AgentFailureError


def _sanitize_mermaid(report: str) -> str:
    """Escape special characters inside Mermaid node labels.

    Parentheses and braces inside an unquoted node label confuse Mermaid's
    parser. Auto-wrap any such labels in double quotes.
    """
    def fix_mermaid_block(match: re.Match) -> str:
        block = match.group(0)
        block = re.sub(
            r'\[([^\]"]*[(){}][^\]"]*)\]',
            lambda m: '["' + m.group(1).replace('"', "'") + '"]',
            block,
        )
        block = re.sub(
            r'\{\{([^}"]*[()][^}"]*)\}\}',
            lambda m: '{{"' + m.group(1).replace('"', "'") + '"}}',
            block,
        )
        return block

    return re.sub(
        r'```mermaid\s*\n.*?```',
        fix_mermaid_block,
        report,
        flags=re.DOTALL,
    )


def _extract_sources(text: str) -> list[str]:
    """Extract source citations from search-result text."""
    sources = []
    for match in re.findall(r'\[Source:\s*(https?://[^\]]+)\]', text):
        source = f"[Web] {match.strip()}"
        if source not in sources:
            sources.append(source)
    # Backward-compatible Korean tag
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


logger = logging.getLogger(__name__)


# Pre-rendered system prompts (templates loaded at import time, with
# `{RESEARCH_AGENDA}` and `{ACADEMIC_TONE_GUIDE}` substitution applied).
SYSTEM_PROMPT: str = render(
    load_system("pi_report"),
    RESEARCH_AGENDA=RESEARCH_AGENDA,
    ACADEMIC_TONE_GUIDE=ACADEMIC_TONE_GUIDE,
).strip()

PI_SUMMARY_PROMPT: str = load_system("pi_summary")

TEAM_DECISION_PROMPT: str = render(
    load_system("pi_team_decision"),
    RESEARCH_AGENDA=RESEARCH_AGENDA,
).strip()


def decide_team(user_query: str) -> List[dict]:
    """PI analyses the query and proposes a specialist team."""
    user_message = (
        f"User question: {user_query}\n\n"
        "Compose a specialist team capable of answering this question.\n"
        "Reply only with a JSON array."
    )

    response = call_gpt(TEAM_DECISION_PROMPT, user_message)

    try:
        content = response.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])

        team = json.loads(content)

        if not isinstance(team, list):
            raise ValueError("Response is not a list.")

        for expert in team:
            if "role" not in expert or "focus" not in expert:
                raise ValueError("Each specialist must have 'role' and 'focus' fields.")

        return team

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {e}\nResponse: {response}")


def _cluster_similar_roles(unique_roles: list[str]) -> dict[str, str]:
    """Use the LLM to map similar role names to a canonical short label.

    Returns:
        dict: {original_role: canonical_role}
    """
    if len(unique_roles) <= 1:
        return {r: r for r in unique_roles}

    role_list = "\n".join(f"- {r}" for r in unique_roles)
    prompt = render(load_system("role_clustering"), ROLE_LIST=role_list)

    response = call_gpt(prompt, "Perform role-name clustering.", temperature=0.2)
    try:
        content = response.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
        data = json.loads(content)

        clusters = data["clusters"]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        # C15 (revision): no silent identity mapping; role-frequency statistics
        # would otherwise be computed on unclustered names without notice.
        raise AgentFailureError(f"Role clustering response could not be parsed: {e}") from e

    # C15 (revision): every input role must be assigned to exactly one cluster.
    # The submitted version silently mapped unassigned roles to themselves.
    mapping: dict[str, str] = {}
    if not isinstance(clusters, list) or not clusters:
        raise AgentFailureError("Role clustering returned no clusters")
    for cluster in clusters:
        canonical = cluster.get("canonical") if isinstance(cluster, dict) else None
        members = cluster.get("members") if isinstance(cluster, dict) else None
        if not isinstance(canonical, str) or not canonical.strip() or not isinstance(members, list) or not members:
            raise AgentFailureError(f"Role clustering returned a malformed cluster: {cluster!r}")
        for member in members:
            if member not in unique_roles:
                raise AgentFailureError(f"Role clustering returned an unknown role: {member!r}")
            if member in mapping:
                raise AgentFailureError(f"Role clustering assigned a role twice: {member!r}")
            mapping[member] = canonical
    missing = [r for r in unique_roles if r not in mapping]
    if missing:
        raise AgentFailureError(f"Role clustering left roles unassigned: {missing}")
    return mapping


def _shorten_role_name(role: str) -> str:
    """Apply a deterministic post-processing pass to enforce short, single-keyword roles.

    Reduces compound names like "Molecular Genetics and Genome Editing (NGT) Specialist"
    to "Molecular Genetics Specialist". Runs after LLM clustering as a safety net.
    """
    if not role:
        return role
    # Strip parenthetical qualifiers
    name = re.sub(r"\s*\([^)]*\)", "", role).strip()
    # Drop the trailing "Specialist" / "Expert" word for separator processing
    suffix = ""
    for s in (" Specialist", " Expert", " Scientist"):
        if name.endswith(s):
            suffix = s
            name = name[: -len(s)].strip()
            break
    # Take only the first segment before " and "/" & "/" / "
    for sep in (" and ", " & ", " / ", ", "):
        if sep in name:
            name = name.split(sep)[0].strip()
            break
    # Cap to first three words, then re-attach the suffix
    words = name.split()
    if len(words) > 3:
        name = " ".join(words[:3])
    return (name + (suffix or " Specialist")).strip()


def decide_team_statistically(user_query: str, n_trials: int = 10) -> dict:
    """Compose the final team via N independent trials and frequency analysis."""
    print(f"\n[STATISTICAL TEAM SELECTION] Running {n_trials} independent team compositions...")

    all_teams = []
    max_retries = n_trials * 3
    attempt = 0
    # Technical retry policy (revision_plan 7.3): a trial whose call fails or whose
    # response is not a valid team (1-5 members with role and focus) is regenerated,
    # up to max_retries attempts in total. Every failed attempt is recorded and
    # reported; the protocol is "n_trials valid compositions", not "n_trials calls".
    failed_trials: list[dict] = []

    def _single_trial(trial_idx: int) -> list[dict] | None:
        try:
            team = decide_team(user_query)
            if not 1 <= len(team) <= 5:
                raise ValueError(f"team size {len(team)} outside 1-5")
            print(f"  Trial {trial_idx+1}: {len(team)} specialists - {[m['role'] for m in team]}")
            return team
        except Exception as e:
            logger.warning(f"Trial {trial_idx+1} failed: {e}")
            failed_trials.append({"attempt_index": trial_idx, "error_type": type(e).__name__,
                                  "error": str(e)[:500]})
            return None

    while len(all_teams) < n_trials and attempt < max_retries:
        # Never exceed the total attempt budget (max_retries calls in all).
        batch = min(n_trials - len(all_teams), max_retries - attempt)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(_single_trial, attempt + i) for i in range(batch)]
            for future in as_completed(futures):
                result = future.result()
                if result and len(all_teams) < n_trials:
                    all_teams.append(result)
        attempt += batch
        if len(all_teams) < n_trials:
            print(f"  [RETRY] {len(all_teams)}/{n_trials} succeeded, retrying {n_trials - len(all_teams)} more...")

    if len(all_teams) < n_trials:
        raise RuntimeError(
            f"Team composition did not reach {n_trials} trials after {max_retries} attempts "
            f"({len(all_teams)} succeeded)."
        )

    # collect unique role names
    unique_roles = set()
    for team in all_teams:
        for member in team:
            unique_roles.add(member["role"])

    # LLM-driven clustering of similar roles
    role_mapping = _cluster_similar_roles(list(unique_roles))
    print(f"  [CLUSTERING] {len(unique_roles)} unique roles → {len(set(role_mapping.values()))} clusters")

    role_counter: Counter = Counter()
    role_team_counter: Counter = Counter()
    role_focus_map: dict[str, list[str]] = {}
    team_size_counter: Counter = Counter()

    for team in all_teams:
        team_size_counter[len(team)] += 1
        seen_roles_in_team: set[str] = set()
        for member in team:
            canonical_role = role_mapping.get(member["role"], member["role"])
            role_counter[canonical_role] += 1
            seen_roles_in_team.add(canonical_role)
            if canonical_role not in role_focus_map:
                role_focus_map[canonical_role] = []
            if member["focus"] not in role_focus_map[canonical_role]:
                role_focus_map[canonical_role].append(member["focus"])
        for role in seen_roles_in_team:
            role_team_counter[role] += 1

    frequency_table = []
    for role, count in role_counter.most_common():
        team_count = role_team_counter[role]
        frequency_table.append({
            "role": role,
            "count": count,
            "team_count": team_count,
            "frequency": f"{team_count}/{n_trials} teams",
            "percentage": round(team_count / n_trials * 100, 1),
            "focus_variants": role_focus_map.get(role, []),
        })

    most_common_size = team_size_counter.most_common(1)[0][0]

    freq_summary = "\n".join(
        f"- {ft['role']}: appeared in {ft['team_count']}/{n_trials} teams "
        f"({ft['percentage']}%), {ft['count']} total occurrences"
        for ft in frequency_table
    )
    size_summary = ", ".join(
        f"{size} members: {cnt} times" for size, cnt in team_size_counter.most_common()
    )

    selection_prompt = render(
        load_system("pi_team_selection"),
        N_TRIALS=str(n_trials),
        FREQUENCY_SUMMARY=freq_summary,
        SIZE_SUMMARY=size_summary,
        RECOMMENDED_SIZE=str(most_common_size),
    )

    response = call_gpt(selection_prompt, f"Research topic: {user_query}")
    try:
        content = response.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
        data = json.loads(content)
        final_team = data.get("team", [])
        rationale = data.get("rationale", "")
    except (json.JSONDecodeError, KeyError) as e:
        # C15 (revision): no silent frequency-table fallback; fail closed.
        raise AgentFailureError(f"PI final team selection could not be parsed: {e}") from e
    if not final_team or not all(m.get("role") and m.get("focus") for m in final_team):
        raise AgentFailureError("PI final team selection returned an empty or incomplete team")

    # Apply deterministic short-name post-processing
    for member in final_team:
        member["role"] = _shorten_role_name(member.get("role", ""))

    print(f"[STATISTICAL TEAM SELECTION] Final team: {len(final_team)} specialists")
    for m in final_team:
        print(f"  - {m['role']}: {m['focus']}")

    return {
        "all_teams": all_teams,
        "frequency_analysis": frequency_table,
        "final_team": final_team,
        "rationale": rationale,
        "frequency_table": freq_summary,
        "team_sizes": size_summary,
        "n_trials": n_trials,
        "failed_trial_attempts": failed_trials,
    }


INTRO_MAX_TOKENS = 8192


def generate_self_introductions(team: List[dict]) -> list[dict]:
    """Generate first-person self-introductions for each finalised specialist."""
    print(f"\n[INTRODUCTIONS] Generating self-introductions for {len(team)} specialists...")

    introductions = []
    intro_system = load_system("intro_generator")
    intro_user_template = load_system("intro_generator_user")

    def _generate_one(profile: dict, idx: int) -> dict:
        role = profile.get("role", "")
        focus = profile.get("focus", "")
        prompt = render(intro_user_template, ROLE=role, FOCUS=focus)
        # Revision: the submitted runs used max_tokens=500, which GPT-5 reasoning
        # tokens exhausted, leaving empty introductions in the saved metadata.
        # The limit is raised, and a failure aborts the run instead of inserting a
        # synthetic sentence (C15).
        try:
            intro = call_gpt(intro_system, prompt, max_tokens=INTRO_MAX_TOKENS)
        except Exception as e:
            logger.error(f"Introduction generation failed for {role}: {e}")
            raise AgentFailureError(f"Self-introduction failed for {role}: {e}") from e
        print(f"  [{idx+1}/{len(team)}] {role}: intro generated ({len(intro)} chars)")
        return {"role": role, "focus": focus, "introduction": intro.strip()}

    with ThreadPoolExecutor(max_workers=len(team)) as executor:
        futures = [executor.submit(_generate_one, p, i) for i, p in enumerate(team)]
        for future in as_completed(futures):
            introductions.append(future.result())

    return introductions


def run_pi_planning(state: AgentState) -> dict:
    """Compose the specialist team for the topic."""
    print(f"\n{'#'*80}")
    print(f"[PI PLANNING] Starting PI planning phase (Statistical Team Selection)")
    print(f"  Topic: {state.get('topic', 'N/A')}")
    print(f"{'#'*80}\n")

    topic = state["topic"]
    constraints = state.get("constraints", "")
    query = f"{topic}\nConstraints: {constraints}"

    # C15 (revision): the submitted version fell back to a hard-coded three-member
    # team when statistical selection failed. The revision fails closed instead.
    team_selection_data = decide_team_statistically(query)
    team = team_selection_data["final_team"]
    logger.info(
        f"PI decided team statistically: {len(team)} specialists "
        f"from {team_selection_data['n_trials']} trials"
    )

    introductions = generate_self_introductions(team)

    team_summary = "\n".join(
        [f"- **{m['role']}**: {m['focus']}" for m in team]
    )
    intro_summary = "\n".join(
        [f"- **{intro['role']}**: {intro['introduction']}" for intro in introductions]
    )
    messages = list(state.get("messages", []))
    messages.append({
        "role": "pi",
        "content": (
            f"Specialist team composed (statistical selection over 10 trials).\n\n"
            f"{team_summary}\n\n### Specialist Self-Introductions\n{intro_summary}"
        ),
    })

    print(f"[PI PLANNING] Team composed: {len(team)} specialists")
    for m in team:
        print(f"  - {m['role']}: {m['focus']}")

    return {
        "team": team,
        "messages": messages,
        "team_selection_data": team_selection_data,
        "specialist_introductions": introductions,
    }


def run_pi_summary(state: AgentState) -> dict:
    """Summarise the current round's discussion and produce an interim conclusion."""
    current_round = state.get("current_round", 1)
    specialist_outputs = state.get("specialist_outputs", [])
    critique = state.get("critique")
    meeting_history = state.get("meeting_history", [])

    print(f"\n{'#'*80}")
    print(f"[PI SUMMARY] Starting PI summary - Round {current_round}")
    print(f"  Specialist outputs: {len(specialist_outputs)}")
    print(f"{'#'*80}\n")

    prev_summaries = ""
    for record in meeting_history:
        prev_summaries += f"\n[Round {record['round']} interim conclusion]\n{record['pi_summary']}\n"

    specialist_context = ""
    for so in specialist_outputs:
        specialist_context += (
            f"\n### [{so.get('role', 'Specialist')}] ({so.get('focus', '')})\n"
            f"{so.get('output', '')}\n"
        )

    critique_text = ""
    if critique:
        critique_text = critique.feedback
        if critique.scores:
            critique_text += "\n\n[Per-specialist axis scores]\n"
            for role, score in critique.scores.items():
                if isinstance(score, dict):
                    axis_str = ", ".join(f"{a}={s}" for a, s in score.items())
                    critique_text += f"- {role}: {axis_str}\n"
                else:
                    critique_text += f"- {role}: {score}/5\n"
        if critique.specialist_feedback:
            critique_text += "\n[Per-specialist feedback]\n"
            for role, fb in critique.specialist_feedback.items():
                critique_text += f"- {role}: {fb}\n"

    user_message = (
        f"[Team meeting Round {current_round}]\n"
        f"Research topic: {state['topic']}\n\n"
        f"{'[Prior-round interim conclusions]' + prev_summaries if prev_summaries else ''}\n\n"
        f"[This round's specialist analyses]\n{specialist_context}\n\n"
        f"[Critic feedback]\n{critique_text}\n\n"
        f"Summarise the deliberation in Round {current_round}:\n"
        f"1. Key issues and points of agreement\n"
        f"2. Open issues to address in the next round\n"
        f"3. Interim conclusion\n"
    )

    print(f"[PI SUMMARY] Calling OpenAI API via call_gpt")
    logger.info("PI summary: Calling OpenAI directly...")

    try:
        summary = call_gpt(PI_SUMMARY_PROMPT, user_message)
        print(f"[PI SUMMARY] OpenAI call succeeded - Summary: {len(summary)} chars")
    except Exception as e:
        print(f"[PI SUMMARY ERROR] {type(e).__name__}: {e}")
        raise

    messages = list(state.get("messages", []))
    messages.append({
        "role": "pi",
        "content": f"[Round {current_round}] Round summary and interim conclusion generated.",
    })

    return {
        "draft": summary,
        "messages": messages,
    }


def _compute_word_counts(messages: list[dict]) -> dict:
    """Compute per-agent turn counts and character counts from the message log."""
    stats: dict[str, dict[str, int]] = {}

    for msg in messages:
        role = msg.get("role", "unknown")
        name = msg.get("name", role)
        content = msg.get("content", "")

        if role == "specialist":
            agent_key = name
        elif role == "pi":
            agent_key = "PI"
        elif role == "critic":
            agent_key = "Critic"
        else:
            agent_key = role

        if agent_key not in stats:
            stats[agent_key] = {"count": 0, "chars": 0}

        stats[agent_key]["count"] += 1
        stats[agent_key]["chars"] += len(content)

    return stats


def run_final_synthesis(state: AgentState) -> dict:
    """Synthesise the multi-round deliberation into the final research report."""
    meeting_history = state.get("meeting_history", [])
    current_round = state.get("current_round", 3)

    print(f"\n{'#'*80}")
    print(f"[PI FINAL SYNTHESIS] Starting final report synthesis")
    print(f"  Meeting history: {len(meeting_history)} rounds archived")
    print(f"  Current round: {current_round}")
    print(f"{'#'*80}\n")

    web_context = ""
    pi_sources = []
    # C12 (revision): a failed search raises SearchError instead of being skipped.
    web_result = web_search.invoke({"query": disambiguate(state["topic"], "safety framework 2025")})
    if web_result:
        web_context = f"\n\n## [Web search — recent context]\n{web_result}"
        pi_sources.extend(_extract_sources(web_context))
    logger.info("PI final synthesis web search completed")

    efsa_context = state.get("cached_efsa_context", "")
    if not efsa_context:
        from tools.web_search import efsa_search
        efsa_result = efsa_search.invoke({"query": disambiguate(state["topic"], "EFSA opinion")})
        if efsa_result:
            efsa_context = f"\n\n## [EFSA Journal search results]\n{efsa_result}"
            pi_sources.extend(_extract_sources(efsa_context))
        logger.info("PI final synthesis EFSA search completed")

    pi_summaries_text = ""
    for record in meeting_history:
        pi_summaries_text += (
            f"\n\n=== Round {record['round']} summary ===\n"
            f"{record.get('pi_summary', '')}\n"
        )
    current_draft = state.get("draft", "")
    if current_draft:
        pi_summaries_text += (
            f"\n\n=== Round {current_round} summary ===\n"
            f"{current_draft}\n"
        )

    round3_outputs = state.get("specialist_outputs", [])
    round3_text = ""
    for so in round3_outputs:
        round3_text += (
            f"\n### [{so.get('role', 'Specialist')}] ({so.get('focus', '')})\n"
            f"{so.get('output', '')}\n"
        )

    all_sources = list(state.get("sources", []))
    all_sources.extend(pi_sources)
    for so in round3_outputs:
        all_sources.extend(_extract_sources(so.get("output", "")))
    seen = set()
    unique_sources = []
    for s in all_sources:
        if s not in seen:
            seen.add(s)
            unique_sources.append(s)

    sources_text = ""
    if unique_sources:
        sources_list = "\n".join(f"{i+1}. {s}" for i, s in enumerate(unique_sources))
        sources_text = f"\n\n[Reference source list — must be included in the report]\n{sources_list}"

    print(f"[PI FINAL SYNTHESIS] Sources collected: {len(unique_sources)}")

    team_composition_text = ""
    tsd = state.get("team_selection_data")
    if tsd:
        n_trials = tsd.get('n_trials', 0)

        all_teams = tsd.get("all_teams", [])
        trials_detail = ""
        total_agents = 0
        if all_teams:
            trials_detail = "Per-trial team composition:\n"
            trials_detail += "| Trial | Team size | Member roles |\n|-------|-----------|--------------|\n"
            for i, trial_team in enumerate(all_teams):
                roles = [m.get("role", "?") for m in trial_team]
                total_agents += len(trial_team)
                trials_detail += f"| Trial {i+1} | {len(trial_team)} | {', '.join(roles)} |\n"
            trials_detail += (
                f"\nTotal generated specialist agents: {total_agents} across {n_trials} trials\n"
            )

        freq_analysis = tsd.get("frequency_analysis", [])
        freq_detail = ""
        if freq_analysis:
            freq_detail = "Role-frequency analysis:\n"
            freq_detail += (
                "| Role | Teams in which the role appeared | Appearance rate | "
                "Total occurrences | Focus variants |\n"
                "|------|----------------------------------|-----------------|"
                "-------------------|----------------|\n"
            )
            for ft in freq_analysis:
                variants = ", ".join(ft.get("focus_variants", [])[:3])
                freq_detail += (
                    f"| {ft['role']} | {ft['frequency']} | {ft['percentage']}% | "
                    f"{ft.get('count', '')} | {variants} |\n"
                )

        team_composition_text = (
            f"\n\n[Team-composition process — include in the 'Methods' section of the report]\n"
            f"Obtained {n_trials} valid independent team compositions "
            f"({len(tsd.get('failed_trial_attempts', []))} failed attempts were regenerated)\n\n"
            f"{trials_detail}\n"
            f"{freq_detail}\n"
            f"Team-size distribution: {tsd.get('team_sizes', '')}\n\n"
            f"PI's final selection rationale: {tsd.get('rationale', '')}\n"
        )

    intro_text = ""
    intros = state.get("specialist_introductions", [])
    if intros:
        intro_lines = "\n\n".join(
            f"**{intro['role']}**\n{intro['introduction']}" for intro in intros
        )
        intro_text = (
            f"\n\n[Specialist self-introductions — include verbatim in the 'Methods' section]\n"
            f"{intro_lines}\n"
        )

    all_messages = list(state.get("messages", []))
    word_counts = _compute_word_counts(all_messages)
    word_counts_text = ""
    if word_counts:
        wc_lines = "| Agent | Turns | Total characters |\n|---|---|---|\n"
        for agent, stats in sorted(word_counts.items()):
            wc_lines += f"| {agent} | {stats['count']} | {stats['chars']:,} |\n"
        word_counts_text = (
            f"\n\n[Per-agent contribution statistics — include in the 'Methods' section]\n{wc_lines}\n"
        )

    # Build the per-round, per-axis Critic score table for the
    # "Critic Score Trajectory" section of the report.
    critic_trajectory_text = ""
    score_axes = ("evidence", "universality", "proportionality", "readability")
    score_history = list(state.get("critic_score_history", []))
    # Append the final round's critique if not yet snapshotted (final round
    # exits via final_synthesis without going through increment_round).
    final_critique = state.get("critique")
    if final_critique and final_critique.scores:
        already_present = any(
            int(s.get("round", -1)) == int(current_round) for s in score_history
        )
        if not already_present:
            score_history.append({
                "round": current_round,
                "scores": final_critique.scores,
            })
    if score_history:
        round_axis_means: list[tuple[int, dict[str, float]]] = []
        for snap in sorted(score_history, key=lambda s: int(s.get("round", 0))):
            rnd = int(snap.get("round", 0))
            axis_lists: dict[str, list[int]] = {ax: [] for ax in score_axes}
            for _role, axis_scores in (snap.get("scores") or {}).items():
                if not isinstance(axis_scores, dict):
                    continue
                for ax in score_axes:
                    if ax in axis_scores and axis_scores[ax] is not None:
                        try:
                            axis_lists[ax].append(int(axis_scores[ax]))
                        except (TypeError, ValueError):
                            pass
            round_axis_means.append((
                rnd,
                {ax: (sum(v) / len(v)) if v else float("nan") for ax, v in axis_lists.items()},
            ))

        def _fmt(v: float) -> str:
            if v != v:  # NaN
                return "—"
            return f"{v:.1f}" if abs(v - round(v)) > 1e-6 else str(int(round(v)))

        # Markdown table
        ct_lines = ["| Round | Evidence | Universality | Proportionality | Readability |",
                    "|-------|----------|--------------|-----------------|-------------|"]
        for rnd, axis_means in round_axis_means:
            ct_lines.append(
                f"| R{rnd} | "
                + " | ".join(_fmt(axis_means[ax]) for ax in score_axes)
                + " |"
            )
        # Mermaid xychart-beta data — one line per axis
        x_labels = ", ".join(f'"R{rnd}"' for rnd, _ in round_axis_means)
        per_axis_series = {
            ax: [axis_means[ax] for _, axis_means in round_axis_means]
            for ax in score_axes
        }

        def _series_str(series: list[float]) -> str:
            return "[" + ", ".join("0" if v != v else f"{v:.2f}".rstrip("0").rstrip(".")
                                   for v in series) + "]"

        critic_trajectory_text = (
            "\n\n[Critic score trajectory — include in the 'Critic Score Trajectory (this run)' section.\n"
            "Use the table verbatim and replace the placeholder Mermaid xychart-beta with the values below.\n"
            "Do not invent additional rounds or axes.]\n\n"
            "Per-round, per-axis means (specialist-panel average):\n"
            + "\n".join(ct_lines)
            + "\n\nMermaid xychart-beta data (one line per axis, in the order Evidence, Universality, Proportionality, Readability):\n"
            f"x-axis: [{x_labels}]\n"
            f"line (Evidence):        {_series_str(per_axis_series['evidence'])}\n"
            f"line (Universality):    {_series_str(per_axis_series['universality'])}\n"
            f"line (Proportionality): {_series_str(per_axis_series['proportionality'])}\n"
            f"line (Readability):     {_series_str(per_axis_series['readability'])}\n"
        )

    user_message = (
        f"Research topic: {state['topic']}\n"
        f"Constraints: {state.get('constraints', '')}\n\n"
        f"[Full team-meeting summary — {current_round} rounds]\n{pi_summaries_text}\n\n"
        f"[Final-round specialist analyses (most refined)]\n{round3_text}\n\n"
        f"{web_context}\n\n"
        f"{efsa_context}\n\n"
        f"{team_composition_text}\n"
        f"{intro_text}\n"
        f"{word_counts_text}\n"
        f"{critic_trajectory_text}\n"
        f"{sources_text}\n\n"
        f"Synthesise all of the above into the final report.\n\n"
        f"★ Rule 1: Do not include round-level material (specialist analyses, Critic scores/feedback, "
        f"PI round summaries) in the report.\n"
        f"For each core question, write only the **PI's consolidated final conclusion** synthesising the full deliberation.\n"
        f"Let the necessity and context of each conclusion emerge naturally from the prose.\n\n"
        f"★ Rule 2: The 'Methods' section must include the team-composition process (full ten-trial results, "
        f"frequency table, selection rationale), the specialist self-introductions, and the per-agent contribution statistics.\n\n"
        f"★ Rule 3: Include the decision tree (Mermaid `graph TD`).\n"
        f"(1) one integrated decision tree + (2) one detailed per-category tree each for SDN-1, SDN-2, SDN-3, ODM = 5 in total.\n"
        f"All paths must end at a single 'Assessment complete' terminal node (no dangling nodes). "
        f"This node marks the end of the assessment pathway and does not by itself indicate that "
        f"safety has been established. Where evidence is insufficient or uncertainty remains, route "
        f"the path through a node such as 'Additional data required' or 'Decision deferred pending "
        f"further data' before the terminal node. The prohibition on normative phrasing does not "
        f"apply to wording that flags uncertainty, requests additional data, or defers a decision.\n"
        f"Use only concrete assessment keywords that a non-specialist can understand at a glance.\n"
        f"Forbidden: abstract phrasings such as 'Omics signal band', 'Minimal molecular-characterisation set', "
        f"'Target-flanking integrity supplementation'.\n\n"
        f"★ Rule 4: For each step of Question 5, include a 2–3 sentence explanation. "
        f"Where technical verification is needed, mention representative analytical techniques as examples "
        f"(e.g. WGS, LC–MS/MS, Western blot, PCR). Do not include numbers, protocols, or vendor names.\n\n"
        f"★ Rule 5: Organise the References section into Web, RAG, and EFSA sources.\n\n"
        f"★ Rule 6: Expand every acronym and technical term with a brief gloss on first use.\n"
        f"Do not include numerical thresholds or protocols. Write so that a non-specialist can follow the argument.\n\n"
        f"★ Rule 7: Write the entire report in formal academic English.\n"
    )

    print(f"[PI FINAL SYNTHESIS] Calling OpenAI API via call_gpt")
    logger.info("PI final synthesis: Calling OpenAI directly...")

    try:
        final_report = call_gpt(SYSTEM_PROMPT, user_message, max_tokens=65536)
        final_report = _sanitize_mermaid(final_report)
        print(f"[PI FINAL SYNTHESIS] OpenAI call succeeded - Final report: {len(final_report)} chars")
    except Exception as e:
        print(f"[PI FINAL SYNTHESIS ERROR] {type(e).__name__}: {e}")
        raise

    messages = list(state.get("messages", []))
    messages.append({
        "role": "pi",
        "content": (
            f"Final report synthesised from {current_round} rounds of team deliberation."
        ),
    })

    return {
        "final_report": final_report,
        "messages": messages,
        "sources": unique_sources,
        "word_counts": word_counts,
    }
