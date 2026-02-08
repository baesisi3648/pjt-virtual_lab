# @TASK P2-R4-T1 - LangGraph StateGraph 워크플로우
# @SPEC TASKS.md#P2-R4-T1
# @TEST tests/test_workflow.py
"""LangGraph StateGraph 워크플로우

Scientist -> Critic -> (revise loop or approve) -> PI 의 흐름을 구현합니다.
최대 2회 반복 후 강제로 PI(finalizing) 단계로 이동합니다.
"""
from typing import Literal

from langgraph.graph import StateGraph, END

from workflow.state import AgentState
from agents.scientist import run_scientist
from agents.critic import run_critic
from agents.pi import run_pi

MAX_ITERATIONS = 2


def should_continue(state: AgentState) -> Literal["drafting", "finalizing"]:
    """Critic 결과에 따라 다음 노드 결정

    - 최대 반복 횟수(2회) 도달 시 -> finalizing
    - Critic이 revise 판정 시 -> drafting (재작성)
    - Critic이 approve 판정 시 -> finalizing (최종 보고서)
    """
    critique = state.get("critique")
    iteration = state.get("iteration", 0)

    # 최대 반복 제한
    if iteration >= MAX_ITERATIONS:
        return "finalizing"

    # Critic 결과 확인
    if critique and critique.decision == "revise":
        return "drafting"

    return "finalizing"


def increment_iteration(state: AgentState) -> dict:
    """반복 횟수 증가 (revise 루프 진입 시 호출)"""
    return {"iteration": state.get("iteration", 0) + 1}


def create_workflow():
    """LangGraph 워크플로우 생성 및 컴파일

    그래프 구조:
        drafting -> critique -> [should_continue]
                                    |-> drafting (via increment)
                                    |-> finalizing -> END

    Returns:
        CompiledStateGraph: 컴파일된 LangGraph 워크플로우
    """
    workflow = StateGraph(AgentState)

    # 노드 추가
    workflow.add_node("drafting", run_scientist)
    workflow.add_node("critique", run_critic)
    workflow.add_node("increment", increment_iteration)
    workflow.add_node("finalizing", run_pi)

    # 엣지 설정
    workflow.set_entry_point("drafting")
    workflow.add_edge("drafting", "critique")
    workflow.add_conditional_edges(
        "critique",
        should_continue,
        {
            "drafting": "increment",
            "finalizing": "finalizing",
        },
    )
    workflow.add_edge("increment", "drafting")
    workflow.add_edge("finalizing", END)

    return workflow.compile()
