"""LangGraph Workflow Module

3라운드 팀 회의 워크플로우:
  planning -> researching -> critique -> pi_summary -> [check_round]
                                ↑                          ↓ (round < 3)
                                └── round_revision ← increment_round
                                                           ↓ (round >= 3)
                                                      final_synthesis -> END
"""
# 순환 import 방지: 직접 import하지 않음
# 사용 시: from workflow.graph import create_workflow

__all__ = []
