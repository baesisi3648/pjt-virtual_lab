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

    # 이전 라운드 누적 피드백 수집
    meeting_history = state.get("meeting_history", [])

    def _build_cumulative_feedback(role: str) -> str:
        """모든 이전 라운드의 피드백을 누적 수집"""
        cumulative = []
        for record in meeting_history:
            round_num = record.get("round", 0)
            prev_fb = record.get("specialist_feedback", {}).get(role, "")
            prev_sc = record.get("critique_scores", {}).get(role, "")
            if prev_fb or prev_sc:
                cumulative.append(f"  [라운드 {round_num}] 점수: {prev_sc}/5\n  피드백: {prev_fb}")
        return "\n".join(cumulative)

    def _run_single_revision(profile: dict, index: int) -> dict:
        """단일 전문가 수정 실행 (병렬화용)"""
        role = profile.get("role", f"전문가 {index+1}")
        focus = profile.get("focus", "")

        # Critic의 이 전문가에 대한 피드백 추출
        my_feedback = ""
        my_score = ""
        my_score_val = 3
        if critique and critique.specialist_feedback:
            my_feedback = critique.specialist_feedback.get(role, "")
        if critique and critique.scores:
            score_val = critique.scores.get(role, "")
            if score_val:
                my_score_val = int(score_val)
                my_score = f" (이전 점수: {score_val}/5)"

        # 누적 피드백 (모든 이전 라운드)
        cumulative_fb = _build_cumulative_feedback(role)

        # 점수별 목표 지시
        if my_score_val >= 5:
            score_guidance = "현재 5/5 만점입니다. 이 수준을 유지하세요."
        elif my_score_val >= 4:
            score_guidance = (
                "현재 4/5입니다. 5/5를 받으려면:\n"
                "- 최신 peer-reviewed 연구를 추가 인용하세요\n"
                "- 반론에 대한 과학적 반박을 포함하세요\n"
                "- 다양한 작물/식품 유형에 적용 가능한 예시를 추가하세요"
            )
        elif my_score_val >= 3:
            score_guidance = (
                "현재 3/5입니다. 4/5 이상을 받으려면:\n"
                "- 구체적 실험 데이터나 사례 연구를 포함하세요\n"
                "- SDN-1/SDN-2/SDN-3 각각에 대한 차별화된 평가를 제시하세요\n"
                "- 비례성 원칙을 명시적으로 설명하고 과학적으로 정당화하세요"
            )
        else:
            score_guidance = (
                "현재 2/5 이하입니다. 반드시 개선이 필요합니다:\n"
                "- Codex, EFSA, FDA 등 공인 기관의 가이드라인을 인용하세요\n"
                "- 주장마다 과학적 근거를 반드시 제시하세요\n"
                "- NGT 카테고리 전반에 적용 가능하도록 범용적으로 작성하세요"
            )

        print(f"  [{index+1}/{len(team)}] START {role}: {focus} (Round {current_round}){my_score} (parallel execution...)")

        try:
            agent = create_specialist(profile)

            query = (
                f"[라운드 {current_round}/3 - 수정/보완 단계]\n"
                f"연구 주제: {topic}\n"
                f"제약 조건: {constraints}\n"
                f"당신의 전문 분야: {focus}\n\n"
                f"[당신의 이전 분석]\n{prev_map.get(role, '')}\n\n"
                f"[비평가의 최신 피드백]{my_score}\n{my_feedback}\n\n"
                f"{'[이전 라운드 누적 피드백]' + chr(10) + cumulative_fb + chr(10) if cumulative_fb else ''}"
                f"[PI의 이전 라운드 결론]\n{pi_summary}\n\n"
                f"[채점 기준 (Rubric)]\n"
                f"1. 과학적 근거: 공인기관 가이드라인 인용(3점) → 구체적 실험 데이터 포함(4점) → 최신 연구+반론 반박(5점)\n"
                f"2. 범용성: NGT 카테고리 전반 적용(3점) → SDN-1/2/3별 차별화(4점) → 다양한 적용 예시+확장성(5점)\n"
                f"3. 비례성: 합리적 수준 자료 요구(3점) → 면제 사유 과학적 정당화(4점) → 국제 동향 정합성+균형(5점)\n\n"
                f"[목표 점수 가이드]\n{score_guidance}\n\n"
                f"[수정 지시]\n"
                f"1. 이전 분석에서 강점으로 평가된 부분은 반드시 유지·보강하세요.\n"
                f"2. 비평가가 지적한 약점을 하나씩 명시적으로 해결하세요.\n"
                f"3. 각 주장에 과학적 근거와 출처를 [출처: ...] 형식으로 명시하세요.\n"
                f"4. 이전 분석보다 반드시 더 깊이 있고 구체적인 내용을 작성하세요.\n"
            )
            output = agent.invoke(query, max_tokens=32768)

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
