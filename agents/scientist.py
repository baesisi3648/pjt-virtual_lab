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
    """PI가 구성한 전문가 팀이 각자 분석을 수행합니다."""
    team = state.get("team", [])
    topic = state["topic"]
    constraints = state.get("constraints", "")

    print(f"\n{'#'*80}")
    print(f"[SPECIALISTS] Running {len(team)} specialist agents")
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

    # 이전 초안 및 critique 피드백
    critique_context = ""
    previous_draft = state.get("draft", "")
    iteration = state.get("iteration", 0)

    if state.get("critique"):
        critique = state["critique"]
        scores_str = ", ".join(f"{k}={v}" for k, v in (critique.scores or {}).items())
        critique_context = (
            f"\n\n{'='*60}\n"
            f"[★ 이전 검토 결과 - 반복 {iteration}회차]\n"
            f"판정: {critique.decision}\n"
            f"점수: {scores_str}\n"
            f"피드백:\n{critique.feedback}\n"
            f"{'='*60}\n"
            f"위 피드백의 각 지적사항을 반드시 하나씩 해결하여 개선된 분석을 작성하세요.\n"
            f"특히 점수가 낮은 항목을 집중적으로 보완하세요."
        )

    # 이전 전문가 결과를 role 기준으로 매핑 (반복 시 자기 결과만 참조)
    prev_specialist_outputs = state.get("specialist_outputs", [])
    prev_output_map = {}
    for so in prev_specialist_outputs:
        prev_output_map[so.get("role", "")] = so.get("output", "")

    # 각 전문가별 분석 수행
    specialist_outputs = []
    messages = list(state.get("messages", []))

    for i, profile in enumerate(team):
        role = profile.get("role", f"전문가 {i+1}")
        focus = profile.get("focus", "")

        print(f"  [{i+1}/{len(team)}] {role}: {focus} (iteration {iteration})")

        try:
            agent = create_specialist(profile)

            # 이 전문가의 이전 결과 찾기
            my_previous = prev_output_map.get(role, "")

            if my_previous and iteration > 0:
                # 반복 개선: 자기 이전 결과 + 비평 피드백만 전달
                query = (
                    f"연구 주제: {topic}\n"
                    f"제약 조건: {constraints}\n"
                    f"당신의 전문 분야: {focus}\n\n"
                    f"[당신의 이전 분석 결과]\n{my_previous}\n\n"
                    f"위는 당신이 이전에 작성한 분석입니다.\n"
                    f"아래 검토 의견을 반영하여 개선된 분석을 작성하세요.\n"
                    f"이전 내용 중 좋은 부분은 유지하고, 지적된 부분만 보완·강화하세요.\n"
                    f"과학적 근거와 출처를 [출처: ...] 형식으로 명시하세요."
                    f"{critique_context}"
                    f"{rag_context}{web_context}"
                )
            else:
                query = (
                    f"연구 주제: {topic}\n"
                    f"제약 조건: {constraints}\n"
                    f"당신의 전문 분야: {focus}\n\n"
                    f"위 연구 주제에 대해 당신의 전문 분야 관점에서 심층 분석을 수행하세요.\n"
                    f"유전자편집식품(NGT)의 안전성 평가 프레임워크 도출에 기여할 수 있는 구체적 분석을 제공하세요.\n"
                    f"과학적 근거와 출처를 [출처: ...] 형식으로 명시하세요."
                    f"{rag_context}{web_context}{critique_context}"
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

    # 출처 수집: 도구 결과 + 전문가 텍스트에서 추출
    collected_sources = list(state.get("sources", []))
    collected_sources.extend(_extract_sources(rag_context))
    collected_sources.extend(_extract_sources(web_context))
    # 전문가 결과 텍스트에서도 출처 추출
    for so in specialist_outputs:
        collected_sources.extend(_extract_sources(so.get("output", "")))
    # 중복 제거
    seen = set()
    unique_sources = []
    for s in collected_sources:
        if s not in seen:
            seen.add(s)
            unique_sources.append(s)

    # 전문가 결과를 통합하여 draft 생성
    draft_sections = []
    for so in specialist_outputs:
        draft_sections.append(f"## [{so['role']}] ({so['focus']})\n\n{so['output']}")
    combined_draft = "\n\n---\n\n".join(draft_sections)

    print(f"\n[SPECIALISTS] All {len(team)} specialists completed")
    print(f"  Combined draft: {len(combined_draft)} chars")
    print(f"  Sources collected: {len(unique_sources)}\n")

    return {
        "draft": combined_draft,
        "specialist_outputs": specialist_outputs,
        "messages": messages,
        "sources": unique_sources,
    }
