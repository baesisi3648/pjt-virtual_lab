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
from tools.web_search import web_search, efsa_search
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


def _perform_searches(topic: str, state: AgentState) -> tuple[str, str, str]:
    """RAG + Web + EFSA 검색을 병렬로 수행하고 캐싱합니다.

    Returns:
        tuple[str, str, str]: (rag_context, web_context, efsa_context)
    """
    current_round = state.get("current_round", 1)

    # Round 2 이상이면 캐시 사용
    if current_round > 1:
        cached_rag = state.get("cached_rag_context", "")
        cached_web = state.get("cached_web_context", "")
        cached_efsa = state.get("cached_efsa_context", "")
        if cached_rag or cached_web:
            print(f"  [CACHE] Using cached search results from Round 1")
            logger.info(f"Using cached search results (Round {current_round})")
            return cached_rag, cached_web, cached_efsa

    # Round 1: 검색 수행 (병렬)
    print(f"  [SEARCH] Running parallel RAG + Web + EFSA searches...")

    rag_context = ""
    web_context = ""
    efsa_context_result = ""

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

    def do_efsa_search():
        try:
            result = efsa_search.invoke({"query": f"{topic} NGT safety assessment EFSA"})
            logger.info(f"EFSA search completed")
            return f"\n\n[EFSA Journal 검색 결과]\n{result}"
        except Exception as e:
            logger.warning(f"EFSA search failed: {e}")
            return ""

    # 병렬 실행
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
            f"위 연구 주제에 대해 당신의 전문 분야 관점에서 해석 중심의 분석을 수행하세요.\n"
            f"'무엇을 해야 하는가'보다 '왜 이 평가가 필요한가'를 설명하는 데 초점을 두세요.\n"
            f"약어·전문 용어는 처음 사용 시 풀네임과 의미 설명을 반드시 포함하세요.\n"
            f"수치·임계값·프로토콜은 포함하지 말고, 과학적 맥락과 출처를 [출처: ...] 형식으로 명시하세요."
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
    rag_context, web_context, efsa_context = _perform_searches(topic, state)

    # 전문가들 병렬 실행
    specialist_outputs = []
    messages = list(state.get("messages", []))

    print(f"\n  [PARALLEL EXECUTION] Launching {len(team)} specialist threads...")

    with ThreadPoolExecutor(max_workers=len(team)) as executor:
        futures = []
        for i, profile in enumerate(team):
            # EFSA context를 web_context에 합쳐서 전달
            combined_web = web_context + efsa_context
            future = executor.submit(
                _run_single_specialist,
                profile, topic, constraints, rag_context, combined_web, i, len(team)
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
        # 검색 결과 캐싱 (Round 2, 3에서 재사용)
        "cached_rag_context": rag_context,
        "cached_web_context": web_context,
        "cached_efsa_context": efsa_context,
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

    AXIS_LABELS = {
        "evidence": "과학적 근거",
        "universality": "범용성",
        "proportionality": "비례성",
        "readability": "가독성",
    }

    def _build_cumulative_feedback(role: str) -> str:
        """모든 이전 라운드의 피드백을 누적 수집"""
        cumulative = []
        for record in meeting_history:
            round_num = record.get("round", 0)
            prev_fb = record.get("specialist_feedback", {}).get(role, "")
            prev_sc = record.get("critique_scores", {}).get(role, "")
            if prev_fb or prev_sc:
                # 축별 점수 형태면 보기 좋게 표시
                if isinstance(prev_sc, dict):
                    sc_str = ", ".join(f"{AXIS_LABELS.get(a, a)}={s}" for a, s in prev_sc.items())
                else:
                    sc_str = str(prev_sc)
                cumulative.append(f"  [라운드 {round_num}] 점수: {sc_str}\n  피드백: {prev_fb}")
        return "\n".join(cumulative)

    def _run_single_revision(profile: dict, index: int) -> dict:
        """단일 전문가 수정 실행 (병렬화용)"""
        role = profile.get("role", f"전문가 {index+1}")
        focus = profile.get("focus", "")

        # Critic의 이 전문가에 대한 축별 점수 추출
        my_feedback = ""
        my_axis_scores = {}
        my_score_text = ""
        if critique and critique.specialist_feedback:
            my_feedback = critique.specialist_feedback.get(role, "")
        if critique and critique.scores:
            score_val = critique.scores.get(role, {})
            if isinstance(score_val, dict):
                my_axis_scores = score_val
                parts = [f"{AXIS_LABELS.get(a, a)}={s}/5" for a, s in score_val.items()]
                my_score_text = f" (축별 점수: {', '.join(parts)})"
            elif score_val:
                my_axis_scores = {a: int(score_val) for a in AXIS_LABELS}
                my_score_text = f" (이전 점수: {score_val}/5)"

        # 가장 낮은 축 = 최우선 개선 대상
        min_score = min(my_axis_scores.values()) if my_axis_scores else 3
        weak_axes = [AXIS_LABELS.get(a, a) for a, s in my_axis_scores.items() if s == min_score] if my_axis_scores else []

        # 누적 피드백 (모든 이전 라운드)
        cumulative_fb = _build_cumulative_feedback(role)

        # 축별 목표 지시 — 가장 약한 축에 초점
        score_guidance_parts = []
        for axis, label in AXIS_LABELS.items():
            s = my_axis_scores.get(axis, 3)
            if s >= 5:
                score_guidance_parts.append(f"- {label}: 5/5 만점. 유지하세요.")
            elif s >= 4:
                score_guidance_parts.append(f"- {label}: {s}/5. 5점을 위해 더 정교하게 다듬으세요.")
            elif s >= 3:
                score_guidance_parts.append(f"- {label}: {s}/5. ★ 개선 필요. 이 축에 집중하세요.")
            else:
                score_guidance_parts.append(f"- {label}: {s}/5. ★★ 반드시 개선 필요!")
        score_guidance = "\n".join(score_guidance_parts)
        if weak_axes:
            score_guidance += f"\n\n최우선 개선 대상: {', '.join(weak_axes)} ({min_score}/5)"

        print(f"  [{index+1}/{len(team)}] START {role}: {focus} (Round {current_round}){my_score_text} (parallel execution...)")

        try:
            agent = create_specialist(profile)

            query = (
                f"[라운드 {current_round} - 수정/보완 단계]\n"
                f"연구 주제: {topic}\n"
                f"제약 조건: {constraints}\n"
                f"당신의 전문 분야: {focus}\n\n"
                f"[당신의 이전 분석]\n{prev_map.get(role, '')}\n\n"
                f"[비평가의 최신 피드백]{my_score_text}\n{my_feedback}\n\n"
                f"{'[이전 라운드 누적 피드백]' + chr(10) + cumulative_fb + chr(10) if cumulative_fb else ''}"
                f"[PI의 이전 라운드 결론]\n{pi_summary}\n\n"
                f"[축별 채점 기준 (Rubric)]\n"
                f"1. 과학적 근거(evidence): 과학적 맥락+해석(3점) → 개념 설명+예시 균형(4점) → 대안적 해석+완결성(5점)\n"
                f"2. 범용성(universality): NGT 카테고리 전반 적용(3점) → SDN-1/2/3별 차별화 관점(4점) → 일반화 프레임워크+확장성(5점)\n"
                f"3. 비례성(proportionality): 합리적 개념적 접근(3점) → 간소화 사유 논리 정당화(4점) → 국제 동향 정합성+균형(5점)\n"
                f"4. 가독성(readability): 약어 설명+수치 없음(3점) → 비전문가도 이해 가능(4점) → '왜 필요한가'가 자연스럽게 전달(5점)\n\n"
                f"[당신의 축별 점수 및 목표]\n{score_guidance}\n\n"
                f"[수정 지시]\n"
                f"1. 이전 분석에서 강점으로 평가된 부분은 반드시 유지·보강하세요.\n"
                f"2. 비평가가 지적한 약점을 하나씩 명시적으로 해결하세요.\n"
                f"3. 과학적 맥락과 출처를 [출처: ...] 형식으로 명시하되, 수치·프로토콜은 지양하세요.\n"
                f"4. 이전 분석보다 '왜 필요한가' 해석이 더 깊어진 내용을 작성하세요.\n"
                f"5. 설명 없이 사용한 약어·전문 용어가 있다면 풀네임+의미 설명을 추가하세요.\n"
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
