# @TASK P3-T4 - Dynamic Workflow Execution
# @SPEC TASKS.md#P3-T4
# @TEST tests/test_dynamic_workflow.py
"""Dynamic Workflow Execution - 결정된 팀으로 워크플로우 동적 실행

PI가 결정한 팀 구성에 따라 동적으로 워크플로우를 생성하고 실행합니다.
P3-T1의 parallel_graph.py, P3-T2의 factory.py, P3-T3의 decide_team()을 통합합니다.
"""
import asyncio
from typing import List

from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

from agents.factory import create_specialist


class DynamicWorkflowState(TypedDict):
    """동적 워크플로우 상태"""

    query: str  # 사용자 질문
    team_profiles: List[dict]  # 전문가 프로필 리스트
    specialist_responses: List[str]  # 각 전문가의 응답
    final_synthesis: str  # PI의 최종 종합 보고서


async def _parallel_specialist_analysis_async(state: DynamicWorkflowState) -> dict:
    """병렬로 전문가 분석 수행 (비동기)

    Args:
        state: 워크플로우 상태

    Returns:
        dict: specialist_responses가 포함된 상태 업데이트
    """
    query = state["query"]
    team_profiles = state["team_profiles"]

    # 동적으로 전문가 에이전트 생성
    specialists = [create_specialist(profile) for profile in team_profiles]

    # 비동기 작업 리스트 생성
    async def invoke_specialist(specialist):
        # create_specialist는 동기 invoke를 제공하므로 executor에서 실행
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, specialist.invoke, query)

    # 병렬 실행
    responses = await asyncio.gather(
        *[invoke_specialist(specialist) for specialist in specialists]
    )

    return {
        "specialist_responses": list(responses),
    }


def parallel_specialist_analysis(state: DynamicWorkflowState) -> dict:
    """병렬로 전문가 분석 수행 (동기 래퍼)

    Args:
        state: 워크플로우 상태

    Returns:
        dict: specialist_responses가 포함된 상태 업데이트
    """
    return asyncio.run(_parallel_specialist_analysis_async(state))


def synthesize_specialist_views(state: DynamicWorkflowState) -> dict:
    """전문가들의 응답을 종합하여 최종 보고서 생성

    Args:
        state: 워크플로우 상태

    Returns:
        dict: final_synthesis가 포함된 상태 업데이트
    """
    from utils.llm import call_gpt4o

    query = state["query"]
    team_profiles = state["team_profiles"]
    specialist_responses = state["specialist_responses"]

    # 전문가 응답 포맷팅
    responses_text = "\n\n".join([
        f"[{team_profiles[i]['role']}의 분석]\n{response}"
        for i, response in enumerate(specialist_responses)
    ])

    system_prompt = """
당신은 연구 프로젝트 총괄 책임자(PI)입니다.

여러 전문가들이 각자의 관점에서 사용자 질문에 답변했습니다.
이들의 답변을 종합하여 통합된 최종 보고서를 작성하세요.

## 보고서 작성 원칙
1. 각 전문가의 핵심 통찰을 반영하세요.
2. 공통점과 차이점을 명확히 하세요.
3. 실무에 즉시 활용 가능한 형태로 작성하세요.
4. Markdown 형식으로 작성하세요.

## 보고서 포맷
```
# 종합 분석 보고서

## 질문 요약
(사용자 질문 요약)

## 전문가 통합 분석
(각 전문가의 핵심 통찰 종합)

## 결론 및 제언
(종합 결론 및 실무 제언)
```
""".strip()

    user_message = f"""
사용자 질문: {query}

{responses_text}

위 전문가들의 분석을 종합하여 최종 보고서를 작성하세요.
""".strip()

    final_synthesis = call_gpt4o(system_prompt, user_message)

    return {
        "final_synthesis": final_synthesis,
    }


def build_dynamic_workflow(team_profiles: List[dict]):
    """팀 구성에 따라 동적으로 워크플로우 생성

    주어진 전문가 프로필 리스트를 바탕으로 LangGraph 워크플로우를 동적으로 구성합니다.

    워크플로우 구조:
        parallel_analysis (전문가 병렬 분석) -> synthesize (PI 종합) -> END

    Args:
        team_profiles: 전문가 프로필 리스트
            각 프로필은 다음 필드를 포함:
            - role (str): 전문가 역할
            - focus (str): 집중 분야

    Returns:
        CompiledStateGraph: 컴파일된 LangGraph 워크플로우

    Raises:
        ValueError: 팀이 비어있거나 프로필 형식이 잘못된 경우

    Example:
        >>> from agents.pi import decide_team
        >>> team = decide_team("고올레산 대두의 안전성 평가")
        >>> graph = build_dynamic_workflow(team)
        >>> result = await graph.ainvoke({
        ...     "query": "고올레산 대두의 안전성 평가",
        ...     "team_profiles": team,
        ...     "specialist_responses": [],
        ...     "final_synthesis": "",
        ... })
    """
    # 입력 검증
    if not team_profiles:
        raise ValueError("최소 1명 이상의 전문가가 필요합니다.")

    for profile in team_profiles:
        if "role" not in profile or "focus" not in profile:
            raise ValueError("각 프로필은 'role'과 'focus' 필드가 필요합니다.")

    # 워크플로우 생성
    workflow = StateGraph(DynamicWorkflowState)

    # 노드 추가
    workflow.add_node("parallel_analysis", parallel_specialist_analysis)
    workflow.add_node("synthesize", synthesize_specialist_views)

    # 엣지 설정
    workflow.set_entry_point("parallel_analysis")
    workflow.add_edge("parallel_analysis", "synthesize")
    workflow.add_edge("synthesize", END)

    return workflow.compile()
