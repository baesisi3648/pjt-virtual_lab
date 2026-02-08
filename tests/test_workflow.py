# @TASK P2-R4-T1 - LangGraph StateGraph 워크플로우 테스트
# @SPEC TASKS.md#P2-R4-T1
"""LangGraph 워크플로우 테스트

워크플로우의 3가지 시나리오를 검증합니다:
1. 단일 루프 (즉시 승인)
2. 수정 루프 (revise -> approve)
3. 최대 반복 제한 (2회 후 강제 종료)
"""
import pytest
from unittest.mock import Mock, patch
from workflow.state import AgentState, CritiqueResult


class TestWorkflowSingleLoop:
    """단일 루프 테스트 (approve 즉시)"""

    @patch("agents.scientist.get_gpt4o_mini")
    @patch("agents.critic.get_gpt4o")
    @patch("agents.pi.get_gpt4o")
    def test_approve_immediately(self, mock_pi_llm, mock_critic_llm, mock_scientist_llm):
        # Scientist mock
        mock_scientist_llm_instance = Mock()
        mock_scientist_llm_instance.invoke.return_value = Mock(content="초안")
        mock_scientist_llm.return_value = mock_scientist_llm_instance

        # Critic mock - 즉시 승인
        mock_critic_llm_instance = Mock()
        mock_critic_llm_instance.invoke.return_value = Mock(
            content='{"decision": "approve", "feedback": "", "scores": {"scientific": 4, "universal": 4, "regulation": 4}}'
        )
        mock_critic_llm.return_value = mock_critic_llm_instance

        # PI mock
        mock_pi_llm_instance = Mock()
        mock_pi_llm_instance.invoke.return_value = Mock(content="# 최종 보고서")
        mock_pi_llm.return_value = mock_pi_llm_instance

        from workflow.graph import create_workflow
        workflow = create_workflow()

        initial_state: AgentState = {
            "topic": "NGT 평가",
            "constraints": "합리적 규제",
            "draft": "",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
        }

        result = workflow.invoke(initial_state)

        assert result["final_report"] != ""
        assert "# 최종 보고서" in result["final_report"]
        assert result["iteration"] == 0  # 수정 없이 바로 승인


class TestWorkflowRevisionLoop:
    """수정 루프 테스트 (revise -> approve)"""

    @patch("agents.scientist.get_gpt4o_mini")
    @patch("agents.critic.get_gpt4o")
    @patch("agents.pi.get_gpt4o")
    def test_revise_then_approve(self, mock_pi_llm, mock_critic_llm, mock_scientist_llm):
        # Scientist mock
        mock_scientist_llm_instance = Mock()
        mock_scientist_llm_instance.invoke.return_value = Mock(content="수정된 초안")
        mock_scientist_llm.return_value = mock_scientist_llm_instance

        # Critic mock (첫 번째: revise, 두 번째: approve)
        mock_critic_llm_instance = Mock()
        mock_critic_llm_instance.invoke.side_effect = [
            Mock(content='{"decision": "revise", "feedback": "범용성 부족", "scores": {}}'),
            Mock(content='{"decision": "approve", "feedback": "", "scores": {}}'),
        ]
        mock_critic_llm.return_value = mock_critic_llm_instance

        # PI mock
        mock_pi_llm_instance = Mock()
        mock_pi_llm_instance.invoke.return_value = Mock(content="# 최종 보고서")
        mock_pi_llm.return_value = mock_pi_llm_instance

        from workflow.graph import create_workflow
        workflow = create_workflow()

        initial_state: AgentState = {
            "topic": "NGT",
            "constraints": "",
            "draft": "",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
        }

        result = workflow.invoke(initial_state)

        assert result["final_report"] != ""
        assert result["iteration"] >= 1  # 최소 1회 수정


class TestWorkflowMaxIterations:
    """최대 반복 테스트 (2회 후 강제 종료)"""

    @patch("agents.scientist.get_gpt4o_mini")
    @patch("agents.critic.get_gpt4o")
    @patch("agents.pi.get_gpt4o")
    def test_stops_at_max_iterations(self, mock_pi_llm, mock_critic_llm, mock_scientist_llm):
        # Scientist mock
        mock_scientist_llm_instance = Mock()
        mock_scientist_llm_instance.invoke.return_value = Mock(content="초안")
        mock_scientist_llm.return_value = mock_scientist_llm_instance

        # Critic이 계속 revise 반환
        mock_critic_llm_instance = Mock()
        mock_critic_llm_instance.invoke.return_value = Mock(
            content='{"decision": "revise", "feedback": "계속 수정 필요", "scores": {}}'
        )
        mock_critic_llm.return_value = mock_critic_llm_instance

        # PI mock
        mock_pi_llm_instance = Mock()
        mock_pi_llm_instance.invoke.return_value = Mock(content="# 보고서")
        mock_pi_llm.return_value = mock_pi_llm_instance

        from workflow.graph import create_workflow
        workflow = create_workflow()

        initial_state: AgentState = {
            "topic": "NGT",
            "constraints": "",
            "draft": "",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
        }

        result = workflow.invoke(initial_state)

        # 최대 2회 반복 후 강제 종료
        assert result["iteration"] <= 2
        assert result["final_report"] != ""
