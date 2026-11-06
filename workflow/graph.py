"""LangGraph StateGraph 워크플로우 - 3라운드 팀 회의

3라운드 팀 회의 워크플로우:
  planning -> researching -> critique -> pi_summary -> [check_round]
                                ↑                          ↓ (round < 3)
                                └── round_revision ← increment_round
                                                           ↓ (round >= 3)
                                                      final_synthesis -> END

모든 에이전트(Specialists + Critic + PI)가 3라운드 팀 회의에 참여하고,
최종 보고서 작성 시 모든 라운드의 베스트 파트를 선별합니다.
"""
from typing import Literal

from langgraph.graph import StateGraph, END

from workflow.state import AgentState
from agents.scientist import run_specialists, run_round_revision
from agents.critic import run_critic, SCORE_AXES
from utils.errors import CritiqueValidationError
from agents.pi import run_pi_planning, run_pi_summary, run_final_synthesis
from agents.translator import run_translation

MAX_ROUNDS = 7


def check_round(state: AgentState) -> Literal["increment_round", "final_synthesis"]:
    """라운드 확인: 만점 시 조기 종료, 최대 7라운드까지 진행"""
    current_round = state.get("current_round", 1)
    critique = state.get("critique")

    print(f"\n{'='*60}")
    print(f"[CHECK_ROUND] current_round={current_round}, MAX_ROUNDS={MAX_ROUNDS}")

    # 조기 종료: 모든 전문가의 모든 축이 5점
    # C3 (revision): evaluate early stopping only on a complete score set
    # (every team role, all four axes, integers 1-5). An incomplete set is a
    # technical failure, never a silent "continue" or an early stop.
    team_roles = [m["role"] for m in state.get("team", [])]
    if critique is None or not critique.scores:
        raise CritiqueValidationError(f"Round {current_round}: no Critic scores available")
    if set(critique.scores) != set(team_roles):
        raise CritiqueValidationError(
            f"Round {current_round}: Critic scores do not cover the team "
            f"(scores={sorted(critique.scores)}, team={sorted(team_roles)})"
        )
    for role, axis_scores in critique.scores.items():
        if (
            not isinstance(axis_scores, dict)
            or set(axis_scores) != set(SCORE_AXES)
            or any(isinstance(s, bool) or not isinstance(s, int) or not 1 <= s <= 5
                   for s in axis_scores.values())
        ):
            raise CritiqueValidationError(f"Round {current_round}: invalid scores for {role}: {axis_scores!r}")
    all_perfect = all(s == 5 for axis_scores in critique.scores.values() for s in axis_scores.values())
    if all_perfect:
        print(f"  -> EARLY STOP: All axes 5/5 at round {current_round}")
        print(f"{'='*60}\n")
        return "final_synthesis"

    if current_round < MAX_ROUNDS:
        print(f"  -> INCREMENT_ROUND (round {current_round} < {MAX_ROUNDS})")
        print(f"{'='*60}\n")
        return "increment_round"

    print(f"  -> FINAL_SYNTHESIS (round {current_round} >= {MAX_ROUNDS})")
    print(f"{'='*60}\n")
    return "final_synthesis"


def increment_round(state: AgentState) -> dict:
    """라운드 증가 + 현재 라운드 기록을 meeting_history에 아카이브"""
    current_round = state.get("current_round", 1)
    meeting_history = list(state.get("meeting_history", []))
    critique = state.get("critique")

    # 현재 라운드 기록 아카이브
    round_record = {
        "round": current_round,
        "specialist_outputs": state.get("specialist_outputs", []),
        "critique_feedback": critique.feedback if critique else "",
        "critique_scores": critique.scores if critique else {},
        "specialist_feedback": critique.specialist_feedback if critique else {},
        "pi_summary": state.get("draft", ""),
    }
    meeting_history.append(round_record)

    print(f"[INCREMENT_ROUND] Round {current_round} -> {current_round + 1}")
    print(f"  Meeting history: {len(meeting_history)} rounds archived")

    return {
        "current_round": current_round + 1,
        "meeting_history": meeting_history,
    }


def create_workflow():
    """3라운드 팀 회의 LangGraph 워크플로우 생성 및 컴파일

    그래프 구조:
        planning -> researching -> critique -> pi_summary -> [check_round]
                                      ↑                          ↓ (round < 3)
                                      └── round_revision ← increment_round
                                                                 ↓ (round >= 3)
                                                            final_synthesis -> END

    Returns:
        CompiledStateGraph: 컴파일된 LangGraph 워크플로우
    """
    workflow = StateGraph(AgentState)

    # 노드 추가
    workflow.add_node("planning", run_pi_planning)
    workflow.add_node("researching", run_specialists)
    workflow.add_node("critique", run_critic)
    workflow.add_node("pi_summary", run_pi_summary)
    workflow.add_node("increment_round", increment_round)
    workflow.add_node("round_revision", run_round_revision)
    workflow.add_node("final_synthesis", run_final_synthesis)
    workflow.add_node("translation", run_translation)

    # 엣지 설정
    workflow.set_entry_point("planning")
    workflow.add_edge("planning", "researching")
    workflow.add_edge("researching", "critique")
    workflow.add_edge("critique", "pi_summary")
    workflow.add_conditional_edges(
        "pi_summary",
        check_round,
        {
            "increment_round": "increment_round",
            "final_synthesis": "final_synthesis",
        },
    )
    workflow.add_edge("increment_round", "round_revision")
    workflow.add_edge("round_revision", "critique")
    workflow.add_edge("final_synthesis", "translation")
    workflow.add_edge("translation", END)

    return workflow.compile()
