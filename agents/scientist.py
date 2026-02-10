"""Specialist Agents for NGT Safety Analysis

PI가 구성한 전문가 팀이 각자의 분야에서 분석을 수행합니다.
OpenAI SDK 직접 호출 방식으로 tool_calls 문제를 방지합니다.
"""
import logging
import re

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


def run_specialists(state: AgentState) -> dict:
    """PI가 구성한 전문가 팀이 각자 1차 분석을 수행합니다. (라운드 1 전용)"""
    team = state.get("team", [])
    topic = state["topic"]
    constraints = state.get("constraints", "")

    print(f"\n{'#'*80}")
    print(f"[SPECIALISTS] Running {len(team)} specialist agents (Round 1 - Initial Research)")
    print(f"  Topic: {topic}")
    print(f"{'#'*80}\n")

    # 공통 컨텍스트: RAG 검색
    rag_context = ""
    try:
        rag_result = rag_search_tool.invoke({"query": f"{topic} NGT safety assessment"})
        rag_context = f"\n\n[참고 규제 문서]\n{rag_result}"
        logger.info(f"Specialist RAG search completed")
    except Exception as e:
        logger.warning(f"Specialist RAG search failed: {e}")

    # 공통 컨텍스트: 웹 검색
    web_context = ""
    try:
        web_result = web_search.invoke({"query": f"{topic} NGT regulation 2025"})
        web_context = f"\n\n[최신 웹 검색 결과]\n{web_result}"
        logger.info(f"Specialist web search completed")
    except Exception as e:
        logger.warning(f"Specialist web search failed: {e}")

    # 각 전문가별 분석 수행
    specialist_outputs = []
    messages = list(state.get("messages", []))

    for i, profile in enumerate(team):
        role = profile.get("role", f"전문가 {i+1}")
        focus = profile.get("focus", "")

        print(f"  [{i+1}/{len(team)}] {role}: {focus}")

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

            specialist_outputs.append({
                "role": role,
                "focus": focus,
                "output": output,
            })

            output_preview = output[:200] + "..." if len(output) > 200 else output
            messages.append({
                "role": "specialist",
                "name": role,
                "content": f"[{role}] 분석을 완료했습니다.\n\n{output_preview}",
            })

            print(f"    -> Output: {len(output)} chars")

        except Exception as e:
            logger.error(f"Specialist {role} failed: {e}")
            specialist_outputs.append({
                "role": role,
                "focus": focus,
                "output": f"분석 실패: {str(e)}",
            })

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

    print(f"\n[SPECIALISTS] All {len(team)} specialists completed")
    print(f"  Sources collected: {len(unique_sources)}\n")

    return {
        "specialist_outputs": specialist_outputs,
        "messages": messages,
        "sources": unique_sources,
    }


def run_round_revision(state: AgentState) -> dict:
    """전문가들이 이전 라운드 피드백을 반영하여 분석을 수정/보완합니다."""
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
    print(f"{'#'*80}\n")

    # 이전 결과를 role 기준 매핑
    prev_map = {so.get("role", ""): so.get("output", "") for so in prev_outputs}

    specialist_outputs = []
    messages = list(state.get("messages", []))

    for i, profile in enumerate(team):
        role = profile.get("role", f"전문가 {i+1}")
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

        print(f"  [{i+1}/{len(team)}] {role}: {focus} (Round {current_round}){my_score}")

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
            output = agent.invoke(query)

            specialist_outputs.append({
                "role": role,
                "focus": focus,
                "output": output,
            })

            output_preview = output[:200] + "..." if len(output) > 200 else output
            messages.append({
                "role": "specialist",
                "name": role,
                "content": f"[라운드 {current_round}] [{role}] 수정된 분석을 완료했습니다.\n\n{output_preview}",
            })

            print(f"    -> Revised output: {len(output)} chars")

        except Exception as e:
            logger.error(f"Specialist {role} revision failed: {e}")
            # 실패 시 이전 결과 유지
            specialist_outputs.append({
                "role": role,
                "focus": focus,
                "output": prev_map.get(role, f"수정 실패: {str(e)}"),
            })

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

    print(f"\n[ROUND REVISION] All {len(team)} specialists revised")
    print(f"  Sources collected: {len(unique_sources)}\n")

    return {
        "specialist_outputs": specialist_outputs,
        "messages": messages,
        "sources": unique_sources,
    }
