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


MIN_SCORE = 3  # 모든 항목이 이 점수 이상이어야 approve


def should_continue(state: AgentState) -> Literal["researching", "finalizing"]:
    """Critic 결과에 따라 다음 노드 결정

    - 최대 반복 횟수(5회) 도달 시 -> finalizing
    - 점수가 모두 MIN_SCORE 이상이고 approve면 -> finalizing
    - 그 외 -> researching (전문가 재분석)
    """
    critique = state.get("critique")
    iteration = state.get("iteration", 0)

    print(f"\n{'='*60}")
    print(f"[SHOULD_CONTINUE] Evaluating next step")
    print(f"  iteration={iteration}, MAX_ITERATIONS={MAX_ITERATIONS}, MIN_SCORE={MIN_SCORE}")

    # 최대 반복 제한
    if iteration >= MAX_ITERATIONS:
        print(f"  -> FINALIZING (max iterations reached)")
        print(f"{'='*60}\n")
        return "finalizing"

    if critique:
        scores = critique.scores or {}
        score_values = list(scores.values()) if scores else []
        print(f"  decision={critique.decision}, scores={scores}")
        print(f"  score_values={score_values}")

        # 점수 기반 강제 검증: 하나라도 MIN_SCORE 미만이면 무조건 revise
        if score_values and any(s < MIN_SCORE for s in score_values):
            low = {k: v for k, v in scores.items() if v < MIN_SCORE}
            print(f"  -> RESEARCHING (scores below {MIN_SCORE}: {low})")
            print(f"{'='*60}\n")
            return "researching"

        # Critic의 decision 확인
        if critique.decision == "revise":
            print(f"  -> RESEARCHING (critic says revise)")
            print(f"{'='*60}\n")
            return "researching"

        print(f"  -> FINALIZING (all scores >= {MIN_SCORE}, approved)")
    else:
        print(f"  -> FINALIZING (no critique available)")

    print(f"{'='*60}\n")
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
