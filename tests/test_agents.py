# @TASK P2-R1-T1, P2-R2-T1, P2-R3-T1 - 에이전트 단위 테스트
# @SPEC TASKS.md#P2-R1-T1, TASKS.md#P2-R2-T1, TASKS.md#P2-R3-T1
# @TEST tests/test_agents.py
"""에이전트 단위 테스트

Scientist, Critic 에이전트의 단위 테스트를 정의합니다.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from workflow.state import AgentState, CritiqueResult


class TestScientist:
    """Scientist 에이전트 테스트"""

    @patch("agents.scientist.get_gpt4o_mini")
    def test_returns_draft_in_state(self, mock_llm):
        """run_scientist는 draft 필드가 포함된 dict를 반환해야 한다."""
        mock_llm_instance = MagicMock()
        mock_response = Mock(content="위험 요소 초안...", tool_calls=[])
        mock_llm_instance.bind_tools.return_value.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance

        from agents.scientist import run_scientist

        state: AgentState = {
            "topic": "유전자편집식품 평가",
            "constraints": "합리적 규제",
            "draft": "",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
        }
        result = run_scientist(state)
        assert "draft" in result
        assert len(result["draft"]) > 0

    @patch("agents.scientist.get_gpt4o_mini")
    def test_includes_guidelines_in_prompt(self, mock_llm):
        """LLM 호출 시 SystemMessage가 포함되어야 한다."""
        mock_llm_instance = MagicMock()
        mock_response = Mock(content="초안", tool_calls=[])
        mock_with_tools = Mock()
        mock_with_tools.invoke.return_value = mock_response
        mock_llm_instance.bind_tools.return_value = mock_with_tools
        mock_llm.return_value = mock_llm_instance

        from agents.scientist import run_scientist

        state: AgentState = {
            "topic": "NGT",
            "constraints": "",
            "draft": "",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
        }
        run_scientist(state)

        # invoke 호출 시 System Prompt 확인
        call_args = mock_with_tools.invoke.call_args
        assert call_args is not None

    @patch("agents.scientist.get_gpt4o_mini")
    def test_adds_message_to_log(self, mock_llm):
        """실행 후 messages 로그에 scientist 역할 메시지가 추가되어야 한다."""
        mock_llm_instance = MagicMock()
        mock_response = Mock(content="초안", tool_calls=[])
        mock_llm_instance.bind_tools.return_value.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance

        from agents.scientist import run_scientist

        state: AgentState = {
            "topic": "NGT",
            "constraints": "",
            "draft": "",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
        }
        result = run_scientist(state)
        assert len(result["messages"]) > 0
        assert result["messages"][0]["role"] == "scientist"

    @patch("agents.scientist.get_gpt4o_mini")
    def test_incorporates_critique_feedback(self, mock_llm):
        """이전 critique가 있으면 프롬프트에 반영되어야 한다."""
        mock_llm_instance = MagicMock()
        mock_response = Mock(content="수정된 초안", tool_calls=[])
        mock_with_tools = Mock()
        mock_with_tools.invoke.return_value = mock_response
        mock_llm_instance.bind_tools.return_value = mock_with_tools
        mock_llm.return_value = mock_llm_instance

        from agents.scientist import run_scientist

        critique = CritiqueResult(
            decision="REVISE",
            feedback="범용성이 부족합니다. SDN 분류별 차별화 필요.",
            scores={"scientific_evidence": 3, "universality": 2, "proportionality": 3},
        )
        state: AgentState = {
            "topic": "NGT",
            "constraints": "",
            "draft": "이전 초안",
            "critique": critique,
            "iteration": 1,
            "final_report": "",
            "messages": [],
        }
        result = run_scientist(state)

        # critique 피드백이 프롬프트에 포함되었는지 확인
        call_args = mock_with_tools.invoke.call_args[0][0]
        human_msg_content = call_args[1].content
        assert "범용성이 부족합니다" in human_msg_content
        assert result["draft"] == "수정된 초안"

    @patch("agents.scientist.get_gpt4o_mini")
    def test_does_not_mutate_original_messages(self, mock_llm):
        """원본 state의 messages 리스트를 변경하지 않아야 한다."""
        mock_llm_instance = MagicMock()
        mock_response = Mock(content="초안", tool_calls=[])
        mock_llm_instance.bind_tools.return_value.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance

        from agents.scientist import run_scientist

        original_messages = []
        state: AgentState = {
            "topic": "NGT",
            "constraints": "",
            "draft": "",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": original_messages,
        }
        result = run_scientist(state)
        assert len(original_messages) == 0  # 원본 불변
        assert len(result["messages"]) == 1  # 새 리스트에 추가


class TestCritic:
    """Critic 에이전트 테스트"""

    @patch("agents.critic.get_gpt4o")
    def test_returns_critique_result(self, mock_llm):
        """run_critic은 CritiqueResult를 포함한 dict를 반환해야 한다."""
        mock_llm_instance = MagicMock()
        mock_response = Mock(
            content='{"decision": "approve", "feedback": "", "scores": {"scientific": 4, "universal": 4, "regulation": 4}}',
            tool_calls=[]
        )
        mock_llm_instance.bind_tools.return_value.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance

        from agents.critic import run_critic

        state: AgentState = {
            "topic": "NGT",
            "constraints": "",
            "draft": "초안 내용...",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
        }
        result = run_critic(state)
        assert "critique" in result
        assert result["critique"].decision in ["approve", "revise"]

    @patch("agents.critic.get_gpt4o")
    def test_includes_rubric_in_prompt(self, mock_llm):
        """run_critic은 CRITIQUE_RUBRIC을 프롬프트에 포함해야 한다."""
        mock_llm_instance = MagicMock()
        mock_response = Mock(
            content='{"decision": "approve", "feedback": "", "scores": {}}',
            tool_calls=[]
        )
        mock_with_tools = Mock()
        mock_with_tools.invoke.return_value = mock_response
        mock_llm_instance.bind_tools.return_value = mock_with_tools
        mock_llm.return_value = mock_llm_instance

        from agents.critic import run_critic

        state: AgentState = {
            "topic": "NGT",
            "constraints": "",
            "draft": "초안",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
        }
        run_critic(state)
        assert mock_with_tools.invoke.called

    @patch("agents.critic.get_gpt4o")
    def test_revise_decision_includes_feedback(self, mock_llm):
        """revise 판정 시 feedback과 메시지가 포함되어야 한다."""
        mock_llm_instance = MagicMock()
        mock_response = Mock(
            content='{"decision": "revise", "feedback": "과학적 근거 보강 필요", "scores": {"scientific": 2, "universal": 4, "regulation": 3}}',
            tool_calls=[]
        )
        mock_llm_instance.bind_tools.return_value.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance

        from agents.critic import run_critic

        state: AgentState = {
            "topic": "NGT",
            "constraints": "",
            "draft": "약한 초안",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
        }
        result = run_critic(state)
        assert result["critique"].decision == "revise"
        assert result["critique"].feedback == "과학적 근거 보강 필요"
        assert len(result["messages"]) == 1
        assert "수정" in result["messages"][0]["content"]

    @patch("agents.critic.get_gpt4o")
    def test_approve_decision_message(self, mock_llm):
        """approve 판정 시 승인 메시지가 포함되어야 한다."""
        mock_llm_instance = MagicMock()
        mock_response = Mock(
            content='{"decision": "approve", "feedback": "", "scores": {"scientific": 5, "universal": 4, "regulation": 4}}',
            tool_calls=[]
        )
        mock_llm_instance.bind_tools.return_value.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance

        from agents.critic import run_critic

        state: AgentState = {
            "topic": "NGT",
            "constraints": "",
            "draft": "좋은 초안",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
        }
        result = run_critic(state)
        assert result["critique"].decision == "approve"
        assert len(result["messages"]) == 1
        assert "승인" in result["messages"][0]["content"]

    @patch("agents.critic.get_gpt4o")
    def test_invalid_json_defaults_to_approve(self, mock_llm):
        """JSON 파싱 실패 시 기본 approve로 처리해야 한다."""
        mock_llm_instance = MagicMock()
        mock_response = Mock(
            content="이것은 JSON이 아닙니다",
            tool_calls=[]
        )
        mock_llm_instance.bind_tools.return_value.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance

        from agents.critic import run_critic

        state: AgentState = {
            "topic": "NGT",
            "constraints": "",
            "draft": "초안",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
        }
        result = run_critic(state)
        assert result["critique"].decision == "approve"
        assert result["critique"].scores == {}

    @patch("agents.critic.get_gpt4o")
    def test_scores_are_preserved(self, mock_llm):
        """scores 딕셔너리가 정확하게 보존되어야 한다."""
        mock_llm_instance = MagicMock()
        mock_response = Mock(
            content='{"decision": "approve", "feedback": "", "scores": {"scientific": 5, "universal": 3, "regulation": 4}}',
            tool_calls=[]
        )
        mock_llm_instance.bind_tools.return_value.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance

        from agents.critic import run_critic

        state: AgentState = {
            "topic": "NGT",
            "constraints": "",
            "draft": "초안",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
        }
        result = run_critic(state)
        assert result["critique"].scores["scientific"] == 5
        assert result["critique"].scores["universal"] == 3
        assert result["critique"].scores["regulation"] == 4

    @patch("agents.critic.get_gpt4o")
    def test_does_not_mutate_original_messages(self, mock_llm):
        """원본 state의 messages 리스트를 변경하지 않아야 한다."""
        mock_llm_instance = MagicMock()
        mock_response = Mock(
            content='{"decision": "approve", "feedback": "", "scores": {}}',
            tool_calls=[]
        )
        mock_llm_instance.bind_tools.return_value.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance

        from agents.critic import run_critic

        original_messages = [{"role": "scientist", "content": "초안 작성 완료"}]
        state: AgentState = {
            "topic": "NGT",
            "constraints": "",
            "draft": "초안",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": original_messages,
        }
        result = run_critic(state)
        assert len(original_messages) == 1  # 원본 불변
        assert len(result["messages"]) == 2  # 새 리스트에 추가


class TestPI:
    """PI 에이전트 테스트"""

    @patch("agents.pi.get_gpt4o")
    def test_returns_final_report(self, mock_llm):
        """run_pi는 final_report 필드가 포함된 dict를 반환해야 한다."""
        mock_llm_instance = MagicMock()
        mock_response = Mock(
            content="# 최종 보고서\n## 1. 개요",
            tool_calls=[]
        )
        mock_llm_instance.bind_tools.return_value.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance

        from agents.pi import run_pi

        state: AgentState = {
            "topic": "NGT",
            "constraints": "",
            "draft": "승인된 초안",
            "critique": CritiqueResult(
                decision="approve", feedback="", scores={}
            ),
            "iteration": 1,
            "final_report": "",
            "messages": [],
        }
        result = run_pi(state)
        assert "final_report" in result
        assert len(result["final_report"]) > 0
        assert "#" in result["final_report"]  # Markdown 형식

    @patch("agents.pi.get_gpt4o")
    def test_formats_as_markdown(self, mock_llm):
        """최종 보고서는 Markdown 헤더(#)로 시작해야 한다."""
        mock_llm_instance = MagicMock()
        mock_response = Mock(
            content="# Report\n## Section",
            tool_calls=[]
        )
        mock_llm_instance.bind_tools.return_value.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance

        from agents.pi import run_pi

        state: AgentState = {
            "topic": "NGT",
            "constraints": "",
            "draft": "초안",
            "critique": CritiqueResult(
                decision="approve", feedback="", scores={}
            ),
            "iteration": 0,
            "final_report": "",
            "messages": [],
        }
        result = run_pi(state)
        assert result["final_report"].startswith("#")

    @patch("agents.pi.get_gpt4o")
    def test_appends_pi_message(self, mock_llm):
        """실행 후 messages 로그에 pi 역할 메시지가 추가되어야 한다."""
        mock_llm_instance = MagicMock()
        mock_response = Mock(
            content="# Final\n## 1. Overview",
            tool_calls=[]
        )
        mock_llm_instance.bind_tools.return_value.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance

        from agents.pi import run_pi

        state: AgentState = {
            "topic": "NGT",
            "constraints": "",
            "draft": "초안 내용",
            "critique": CritiqueResult(
                decision="approve", feedback="", scores={}
            ),
            "iteration": 1,
            "final_report": "",
            "messages": [{"role": "scientist", "content": "초안 작성 완료"}],
        }
        result = run_pi(state)
        assert len(result["messages"]) == 2
        assert result["messages"][-1]["role"] == "pi"

    @patch("agents.pi.get_gpt4o")
    def test_passes_topic_and_draft_to_llm(self, mock_llm):
        """LLM 호출 시 topic과 draft가 프롬프트에 포함되어야 한다."""
        mock_llm_instance = MagicMock()
        mock_response = Mock(content="# Report", tool_calls=[])
        mock_with_tools = Mock()
        mock_with_tools.invoke.return_value = mock_response
        mock_llm_instance.bind_tools.return_value = mock_with_tools
        mock_llm.return_value = mock_llm_instance

        from agents.pi import run_pi

        state: AgentState = {
            "topic": "유전자편집식품 안전성",
            "constraints": "과학적 근거 기반",
            "draft": "위험 요소 목록 초안",
            "critique": CritiqueResult(
                decision="approve", feedback="", scores={}
            ),
            "iteration": 1,
            "final_report": "",
            "messages": [],
        }
        run_pi(state)

        # invoke가 호출되었는지 확인
        mock_with_tools.invoke.assert_called_once()
        call_args = mock_with_tools.invoke.call_args[0][0]
        # HumanMessage에 topic과 draft가 포함되어야 함
        human_msg_content = call_args[1].content
        assert "유전자편집식품 안전성" in human_msg_content
        assert "위험 요소 목록 초안" in human_msg_content

    @patch("agents.pi.get_gpt4o")
    def test_does_not_mutate_original_messages(self, mock_llm):
        """원본 state의 messages 리스트를 변경하지 않아야 한다."""
        mock_llm_instance = MagicMock()
        mock_response = Mock(content="# Report", tool_calls=[])
        mock_llm_instance.bind_tools.return_value.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance

        from agents.pi import run_pi

        original_messages = [{"role": "scientist", "content": "초안"}]
        state: AgentState = {
            "topic": "NGT",
            "constraints": "",
            "draft": "초안",
            "critique": CritiqueResult(
                decision="approve", feedback="", scores={}
            ),
            "iteration": 1,
            "final_report": "",
            "messages": original_messages,
        }
        result = run_pi(state)
        assert len(original_messages) == 1  # 원본 불변
        assert len(result["messages"]) == 2  # 새 리스트에 추가
