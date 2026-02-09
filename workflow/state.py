# @TASK P2-R1 - LangGraph 상태 스키마 정의
# @SPEC TASKS.md#P2-R1
"""LangGraph StateGraph 상태 스키마

에이전트 간 공유되는 상태(State)와 비평 결과(CritiqueResult)를 정의합니다.
"""
from dataclasses import dataclass, field
from typing import TypedDict


@dataclass
class CritiqueResult:
    """Critic 에이전트의 비평 결과"""

    decision: str  # "APPROVE" or "REVISE"
    feedback: str  # 상세 피드백
    scores: dict = field(default_factory=dict)  # 항목별 점수


class AgentState(TypedDict):
    """LangGraph 에이전트 공유 상태"""

    topic: str  # 연구 주제
    constraints: str  # 제약 조건
    team: list[dict]  # PI가 결정한 전문가 팀 (role, focus)
    specialist_outputs: list[dict]  # 각 전문가 분석 결과
    draft: str  # Scientist가 작성한 초안
    critique: CritiqueResult | None  # Critic의 비평 결과
    iteration: int  # 현재 반복 횟수
    final_report: str  # PI가 확정한 최종 보고서
    messages: list[dict]  # 에이전트 간 메시지 로그
    parallel_views: list[dict]  # 병렬 분석 결과 (Map-Reduce)
    sources: list[str]  # 참조 출처 목록 (웹 검색 URL, RAG 문헌)
