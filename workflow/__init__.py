# @TASK P2-R4-T1, P3-T4 - LangGraph 워크플로우 패키지
"""LangGraph Workflow Module

이 모듈은 세 가지 워크플로우를 제공합니다:

1. **Sequential Workflow** (graph.py)
   - Scientist → Critic → PI (순차 실행, 최대 2회 반복)
   - 정밀한 검증과 피드백 루프가 필요한 경우 사용

2. **Parallel Workflow** (parallel_graph.py)
   - [Scientist, Critic, PI] → Merge (병렬 실행, 1회)
   - 빠른 다각도 분석이 필요한 경우 사용

3. **Dynamic Workflow** (dynamic_graph.py)
   - PI가 결정한 팀으로 동적 워크플로우 생성 및 실행
   - 질문에 따라 유연하게 전문가 팀을 구성해야 하는 경우 사용
"""
# 순환 import 방지: 직접 import하지 않음
# 사용 시:
#   from workflow.graph import create_workflow
#   from workflow.parallel_graph import create_parallel_workflow
#   from workflow.dynamic_graph import build_dynamic_workflow

__all__ = []
