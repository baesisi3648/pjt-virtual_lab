"""Specialist Agents for NGT Safety Analysis

PI가 구성한 전문가 팀이 각자의 분야에서 분석을 수행합니다.
OpenAI SDK 직접 호출 방식으로 tool_calls 문제를 방지합니다.

Phase 1 최적화:
- 전문가 병렬 실행 (5배 속도 향상)
- 검색 캐싱 + 병렬화 (20-30초 단축)
"""
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from workflow.state import AgentState
from tools.rag_search import rag_search_tool
from tools.web_search import web_search
from agents.factory import create_specialist

logger = logging.getLogger(__name__)


def _extract_sources(text: str) -> list[str]:
    """검색 결과 텍스트에서 출처 정보를 추출합니다."""
    sources = []
    # 웹 검색 출처: [출처: URL]
    for match in re.findall(r'\[출처:\s*(https?://[^\]]+)\]', text):
        source = f"[웹] {match.strip()}"
        if source not in sources:
            sources.append(source)
    # RAG 문헌 출처: **출처**: filename (p.N)
    for match in re.findall(r'\*\*출처\*\*:\s*(.+?)(?:\n|$)', text):
        source = f"[문헌] {match.strip()}"
        if source not in sources:
            sources.append(source)
    return sources


def _perform_searches(topic: str, state: AgentState) -> tuple[str, str]:
    """RAG + Web 검색을 병렬로 수행하고 캐싱합니다.

    Returns:
        tuple[str, str]: (rag_context, web_context)
    """
    current_round = state.get("current_round", 1)

    # Round 2 이상이면 캐시 사용
    if current_round > 1:
        cached_rag = state.get("cached_rag_context", "")
        cached_web = state.get("cached_web_context", "")
        if cached_rag or cached_web:
            print(f"  [CACHE] Using cached search results from Round 1")
            logger.info(f"Using cached search results (Round {current_round})")
            return cached_rag, cached_web

    # Round 1: 검색 수행 (병렬)
    print(f"  [SEARCH] Running parallel RAG + Web searches...")

    rag_context = ""
    web_context = ""

    def do_rag_search():
        try:
            result = rag_search_tool.invoke({"query": f"{topic} NGT safety assessment"})
            logger.info(f"RAG search completed")
            return f"\n\n[참고 규제 문서]\n{result}"
        except Exception as e:
            logger.warning(f"RAG search failed: {e}")
            return ""

    def do_web_search():
        try:
            result = web_search.invoke({"query": f"{topic} NGT regulation 2025"})
            logger.info(f"Web search completed")
            return f"\n\n[최신 웹 검색 결과]\n{result}"
        except Exception as e:
            logger.warning(f"Web search failed: {e}")
            return ""

    # 병렬 실행
    with ThreadPoolExecutor(max_workers=2) as executor:
        rag_future = executor.submit(do_rag_search)
        web_future = executor.submit(do_web_search)

        rag_context = rag_future.result()
        web_context = web_future.result()

    print(f"  [SEARCH] Parallel searches completed")
    print(f"    - RAG: {len(rag_context)} chars")
    print(f"    - Web: {len(web_context)} chars")

    return rag_context, web_context


def _run_single_specialist(
    profile: dict,
    topic: str,
    constraints: str,
    rag_context: str,
    web_context: str,
    index: int,
    total: int,
) -> dict:
    """단일 전문가 분석 실행 (병렬화용)

    Returns:
        dict: {"role": str, "focus": str, "output": str, "message": dict}
    """
    role = profile.get("role", f"전문가 {index+1}")
    focus = profile.get("focus", "")

    print(f"  [{index+1}/{total}] START {role}: {focus} (parallel execution...)")

    try:
        agent = create_specialist(profile)

        query = (
            f"연구 주제: {topic}\n"
            f"제약 조건: {constraints}\n"
            f"당신의 전문 분야: {focus}\n\n"
            f"위 연구 주제에 대해 당신의 전문 분야 관점에서 심층 분석을 수행하세요.\n"
            f"유전자편집식품(NGT)의 안전성 평가 프레임워크 도출에 기여할 수 있는 구체적 분석을 제공하세요.\n"
            f"과학적 근거와 출처를 [출처: ...] 형식으로 명시하세요."
            f"{rag_context}{web_context}"
        )
        output = agent.invoke(query)

        output_preview = output[:200] + "..." if len(output) > 200 else output
        message = {
            "role": "specialist",
            "name": role,
            "content": f"[{role}] 분석을 완료했습니다.\n\n{output_preview}",
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
            "output": f"분석 실패: {str(e)}",
            "message": None,
        }


def run_specialists(state: AgentState) -> dict:
    """PI가 구성한 전문가 팀이 각자 1차 분석을 수행합니다. (라운드 1 전용)

    Phase 1 최적화:
    - 검색 병렬화 + 캐싱
    - 전문가 병렬 실행 (5배 속도 향상)
    """
    team = state.get("team", [])
    topic = state["topic"]
    constraints = state.get("constraints", "")

    print(f"\n{'#'*80}")
    print(f"[SPECIALISTS] Running {len(team)} specialist agents (Round 1 - Initial Research)")
    print(f"  Topic: {topic}")
    print(f"  PARALLEL MODE: {len(team)} specialists running concurrently")
    print(f"{'#'*80}\n")

    # 검색 병렬 수행 + 캐싱
    rag_context, web_context = _perform_searches(topic, state)

    # 전문가들 병렬 실행
    specialist_outputs = []
    messages = list(state.get("messages", []))

    print(f"\n  [PARALLEL EXECUTION] Launching {len(team)} specialist threads...")

    with ThreadPoolExecutor(max_workers=len(team)) as executor:
        futures = []
        for i, profile in enumerate(team):
            future = executor.submit(
                _run_single_specialist,
                profile, topic, constraints, rag_context, web_context, i, len(team)
            )
            futures.append(future)

        # 완료된 순서대로 결과 수집
        for future in as_completed(futures):
            result = future.result()
            specialist_outputs.append({
                "role": result["role"],
                "focus": result["focus"],
                "output": result["output"],
            })
            if result["message"]:
                messages.append(result["message"])

    # 출처 수집
    collected_sources = list(state.get("sources", []))
    collected_sources.extend(_extract_sources(rag_context))
    collected_sources.extend(_extract_sources(web_context))
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
        # 검색 결과 캐싱 (Round 2, 3에서 재사용)
        "cached_rag_context": rag_context,
        "cached_web_context": web_context,
    }


def run_round_revision(state: AgentState) -> dict:
    """전문가들이 이전 라운드 피드백을 반영하여 분석을 수정/보완합니다.

    Phase 1 최적화:
    - 검색 캐싱 (Round 1 결과 재사용)
    - 전문가 병렬 실행 (5배 속도 향상)
    """
    team = state.get("team", [])
    current_round = state.get("current_round", 2)
    critique = state.get("critique")
    pi_summary = state.get("draft", "")  # PI의 이전 라운드 임시 결론
    prev_outputs = state.get("specialist_outputs", [])
    topic = state["topic"]
    constraints = state.get("constraints", "")

    print(f"\n{'#'*80}")
    print(f"[ROUND REVISION] Running {len(team)} specialist revisions - Round {current_round}/3")
    print(f"  Topic: {topic}")
    print(f"  PARALLEL MODE: {len(team)} specialists running concurrently")
    print(f"{'#'*80}\n")

    # 이전 결과를 role 기준 매핑
    prev_map = {so.get("role", ""): so.get("output", "") for so in prev_outputs}

    specialist_outputs = []
    messages = list(state.get("messages", []))

    def _run_single_revision(profile: dict, index: int) -> dict:
        """단일 전문가 수정 실행 (병렬화용)"""
        role = profile.get("role", f"전문가 {index+1}")
        focus = profile.get("focus", "")

        # Critic의 이 전문가에 대한 피드백 추출
        my_feedback = ""
        my_score = ""
        if critique and critique.specialist_feedback:
            my_feedback = critique.specialist_feedback.get(role, "")
        if critique and critique.scores:
            score_val = critique.scores.get(role, "")
            if score_val:
                my_score = f" (이전 점수: {score_val}/5)"

        print(f"  [{index+1}/{len(team)}] START {role}: {focus} (Round {current_round}){my_score} (parallel execution...)")

        try:
            agent = create_specialist(profile)

            query = (
                f"[라운드 {current_round}/3 - 수정/보완 단계]\n"
                f"연구 주제: {topic}\n"
                f"제약 조건: {constraints}\n"
                f"당신의 전문 분야: {focus}\n\n"
                f"[당신의 이전 분석]\n{prev_map.get(role, '')}\n\n"
                f"[비평가의 피드백]{my_score}\n{my_feedback}\n\n"
                f"[PI의 이전 라운드 결론]\n{pi_summary}\n\n"
                f"위 피드백을 반영하여 분석을 수정/보완하세요.\n"
                f"강점은 유지하고, 지적된 약점을 집중 개선하세요.\n"
                f"과학적 근거와 출처를 [출처: ...] 형식으로 명시하세요."
            )
            # Phase 1 최적화: Specialist는 8192 토큰으로 제한 (속도 향상)
            output = agent.invoke(query, max_tokens=8192)

            output_preview = output[:200] + "..." if len(output) > 200 else output
            message = {
                "role": "specialist",
                "name": role,
                "content": f"[라운드 {current_round}] [{role}] 수정된 분석을 완료했습니다.\n\n{output_preview}",
            }

            print(f"  [{index+1}/{len(team)}] DONE {role}: {len(output)} chars (revised)")

            return {
                "role": role,
                "focus": focus,
                "output": output,
                "message": message,
            }

        except Exception as e:
            logger.error(f"Specialist {role} revision failed: {e}")
            print(f"  [{index+1}/{len(team)}] FAILED {role}: {e}")

            # 실패 시 이전 결과 유지
            return {
                "role": role,
                "focus": focus,
                "output": prev_map.get(role, f"수정 실패: {str(e)}"),
                "message": None,
            }

    # 전문가들 병렬 실행
    print(f"\n  [PARALLEL EXECUTION] Launching {len(team)} revision threads...")

    with ThreadPoolExecutor(max_workers=len(team)) as executor:
        futures = []
        for i, profile in enumerate(team):
            future = executor.submit(_run_single_revision, profile, i)
            futures.append(future)

        # 완료된 순서대로 결과 수집
        for future in as_completed(futures):
            result = future.result()
            specialist_outputs.append({
                "role": result["role"],
                "focus": result["focus"],
                "output": result["output"],
            })
            if result["message"]:
                messages.append(result["message"])

    # 출처 수집 (기존 + 새로운)
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
