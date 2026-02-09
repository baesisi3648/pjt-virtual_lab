# @TASK P2-R4-T1 - LangGraph StateGraph 워크플로우
# @SPEC TASKS.md#P2-R4-T1
# @TEST tests/test_workflow.py
"""LangGraph StateGraph 워크플로우

PI 중심 워크플로우:
  planning -> researching -> critique -> [should_continue]
                                            |-> researching (via increment)
                                            |-> finalizing -> END

PI가 먼저 팀을 구성하고, 전문가들이 분석하며,
Critic이 검증한 뒤, PI가 최종 보고서를 작성합니다.
"""
from typing import Literal

from langgraph.graph import StateGraph, END

from workflow.state import AgentState
from agents.scientist import run_specialists
from agents.critic import run_critic
from agents.pi import run_pi_planning, run_pi

MAX_ITERATIONS = 5


def should_continue(state: AgentState) -> Literal["researching", "finalizing"]:
    """Critic 결과에 따라 다음 노드 결정

    - 최대 반복 횟수(5회) 도달 시 -> finalizing
    - Critic이 revise 판정 시 -> researching (전문가 재분석)
    - Critic이 approve 판정 시 -> finalizing (최종 보고서)
    """
    critique = state.get("critique")
    iteration = state.get("iteration", 0)

    # 최대 반복 제한
    if iteration >= MAX_ITERATIONS:
        return "finalizing"

    # Critic 결과 확인
    if critique and critique.decision == "revise":
        return "researching"

    return "finalizing"


def increment_iteration(state: AgentState) -> dict:
    """반복 횟수 증가 (revise 루프 진입 시 호출)"""
    return {"iteration": state.get("iteration", 0) + 1}


def create_workflow():
    """LangGraph 워크플로우 생성 및 컴파일

    그래프 구조:
        planning -> researching -> critique -> [should_continue]
                                                   |-> researching (via increment)
                                                   |-> finalizing -> END

    Returns:
        CompiledStateGraph: 컴파일된 LangGraph 워크플로우
    """
    workflow = StateGraph(AgentState)

    # 노드 추가
    workflow.add_node("planning", run_pi_planning)
    workflow.add_node("researching", run_specialists)
    workflow.add_node("critique", run_critic)
    workflow.add_node("increment", increment_iteration)
    workflow.add_node("finalizing", run_pi)

    # 엣지 설정
    workflow.set_entry_point("planning")
    workflow.add_edge("planning", "researching")
    workflow.add_edge("researching", "critique")
    workflow.add_conditional_edges(
        "critique",
        should_continue,
        {
            "researching": "increment",
            "finalizing": "finalizing",
        },
    )
    workflow.add_edge("increment", "researching")
    workflow.add_edge("finalizing", END)

    return workflow.compile()
