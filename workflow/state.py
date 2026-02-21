"""LangGraph StateGraph 상태 스키마

에이전트 간 공유되는 상태(State)와 비평 결과(CritiqueResult)를 정의합니다.
3라운드 팀 회의 워크플로우용 상태 구조.
"""
from dataclasses import dataclass, field
from typing import TypedDict


@dataclass
class CritiqueResult:
    """Critic 에이전트의 비평 결과 - 전문가별 평가"""

    decision: str  # "continue" | "approve" (참고용, 3라운드 고정 루프)
    feedback: str  # 전체 요약 피드백
    scores: dict = field(default_factory=dict)  # 전문가별 점수 {"역할명": 1-5}
    specialist_feedback: dict = field(default_factory=dict)  # 전문가별 상세 피드백


class AgentState(TypedDict):
    """LangGraph 에이전트 공유 상태 - 3라운드 팀 회의

    Phase 1 최적화: 검색 캐싱 필드 추가
    """

    topic: str  # 연구 주제
    constraints: str  # 제약 조건
    team: list[dict]  # PI가 결정한 전문가 팀 (role, focus)
    specialist_outputs: list[dict]  # 현재 라운드의 전문가 결과물
    draft: str  # PI의 라운드별 임시 결론 / 최종보고서
    critique: CritiqueResult | None  # Critic의 비평 결과
    current_round: int  # 1, 2, 3 (라운드 번호)
    meeting_history: list[dict]  # 라운드별 기록 아카이브
    final_report: str  # PI가 확정한 최종 보고서
    messages: list[dict]  # 에이전트 간 메시지 로그
    parallel_views: list[dict]  # 병렬 분석 결과 (Map-Reduce)
    sources: list[str]  # 참조 출처 목록 (웹 검색 URL, RAG 문헌)
    cached_rag_context: str  # Phase 1: Round 1 RAG 검색 캐시
    cached_web_context: str  # Phase 1: Round 1 Web 검색 캐시
