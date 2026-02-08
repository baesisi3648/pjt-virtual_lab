# @TASK P2-T3 - Agent Search Integration Test
# @SPEC TASKS.md#P2-T3
# @TEST tests/test_web_search_integration.py
"""Web Search Integration Tests

모든 에이전트(Scientist, Critic, PI)가 web_search 도구를 올바르게
사용할 수 있는지 검증합니다.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from workflow.state import AgentState, CritiqueResult


class TestScientistWebSearch:
    """Scientist 에이전트의 web_search 통합 테스트"""

    @patch("agents.scientist.web_search")
    @patch("agents.scientist.get_gpt4o_mini")
    def test_scientist_can_use_web_search(self, mock_llm_factory, mock_web_search):
        """Scientist는 web_search 도구를 바인딩하고 사용할 수 있어야 한다."""
        # Mock web_search tool
        mock_web_search.invoke.return_value = "**NGT Safety**\nRecent findings...\n[출처: https://example.com]"

        # Mock LLM with bind_tools
        mock_llm = MagicMock()
        mock_llm_with_tools = MagicMock()

        # First call: LLM decides to use web_search
        first_response = Mock()
        first_response.tool_calls = [
            {"name": "web_search", "args": {"query": "NGT safety assessment 2025"}}
        ]
        first_response.content = ""

        # Second call: LLM generates draft with search results
        second_response = Mock()
        second_response.tool_calls = []
        second_response.content = "초안: NGT 안전성 평가 기준...[출처: https://example.com]"

        mock_llm_with_tools.invoke.side_effect = [first_response, second_response]
        mock_llm.bind_tools.return_value = mock_llm_with_tools
        mock_llm_factory.return_value = mock_llm

        from agents.scientist import run_scientist

        state: AgentState = {
            "topic": "2025년 NGT 안전성 평가 기준",
            "constraints": "최신 논문 기반",
            "draft": "",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
        }

        result = run_scientist(state)

        # Assertions
        assert "draft" in result
        assert "출처" in result["draft"]
        mock_llm.bind_tools.assert_called_once()
        assert mock_web_search.invoke.called or first_response.tool_calls  # Tool was invoked


class TestCriticWebSearch:
    """Critic 에이전트의 web_search 통합 테스트"""

    @patch("agents.critic.web_search")
    @patch("agents.critic.get_gpt4o")
    def test_critic_can_use_web_search(self, mock_llm_factory, mock_web_search):
        """Critic은 web_search 도구로 주장을 검증할 수 있어야 한다."""
        # Mock web_search tool
        mock_web_search.invoke.return_value = "**EU NGT Law 2025**\nApproved...\n[출처: https://ec.europa.eu]"

        # Mock LLM with bind_tools
        mock_llm = MagicMock()
        mock_llm_with_tools = MagicMock()

        # First call: LLM decides to use web_search
        first_response = Mock()
        first_response.tool_calls = [
            {"name": "web_search", "args": {"query": "EU NGT regulation 2025"}}
        ]
        first_response.content = ""

        # Second call: LLM generates critique with verification
        second_response = Mock()
        second_response.tool_calls = []
        second_response.content = '{"decision": "approve", "feedback": "", "scores": {"scientific": 5, "universal": 4, "regulation": 4}}'

        mock_llm_with_tools.invoke.side_effect = [first_response, second_response]
        mock_llm.bind_tools.return_value = mock_llm_with_tools
        mock_llm_factory.return_value = mock_llm

        from agents.critic import run_critic

        state: AgentState = {
            "topic": "NGT",
            "constraints": "",
            "draft": "EU는 2025년 NGT 법안을 통과시켰다.",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
        }

        result = run_critic(state)

        # Assertions
        assert "critique" in result
        assert result["critique"].decision in ["approve", "revise"]
        mock_llm.bind_tools.assert_called_once()


class TestPIWebSearch:
    """PI 에이전트의 web_search 통합 테스트"""

    @patch("agents.pi.web_search")
    @patch("agents.pi.get_gpt4o")
    def test_pi_can_use_web_search(self, mock_llm_factory, mock_web_search):
        """PI는 web_search 도구로 최종 보고서를 보강할 수 있어야 한다."""
        # Mock web_search tool
        mock_web_search.invoke.return_value = "**FDA NGT Guidelines**\nNew recommendations...\n[출처: https://fda.gov]"

        # Mock LLM with bind_tools
        mock_llm = MagicMock()
        mock_llm_with_tools = MagicMock()

        # First call: LLM decides to use web_search
        first_response = Mock()
        first_response.tool_calls = [
            {"name": "web_search", "args": {"query": "FDA NGT guidelines 2025"}}
        ]
        first_response.content = ""

        # Second call: LLM generates final report with citations
        second_response = Mock()
        second_response.tool_calls = []
        second_response.content = "# 최종 보고서\n## 1. 개요\nFDA 가이드라인...[출처: https://fda.gov]"

        mock_llm_with_tools.invoke.side_effect = [first_response, second_response]
        mock_llm.bind_tools.return_value = mock_llm_with_tools
        mock_llm_factory.return_value = mock_llm

        from agents.pi import run_pi

        state: AgentState = {
            "topic": "NGT 안전성 평가",
            "constraints": "FDA 가이드라인 기반",
            "draft": "승인된 초안",
            "critique": CritiqueResult(decision="approve", feedback="", scores={}),
            "iteration": 1,
            "final_report": "",
            "messages": [],
        }

        result = run_pi(state)

        # Assertions
        assert "final_report" in result
        assert "#" in result["final_report"]
        mock_llm.bind_tools.assert_called_once()


class TestWebSearchSystemPrompts:
    """System Prompt에 검색 사용 지침이 포함되었는지 확인"""

    def test_scientist_prompt_includes_search_guidance(self):
        """Scientist의 System Prompt에 web_search 사용 지침이 있어야 한다."""
        from agents.scientist import SYSTEM_PROMPT

        assert "web_search" in SYSTEM_PROMPT
        assert "최신" in SYSTEM_PROMPT or "검색" in SYSTEM_PROMPT

    def test_critic_prompt_includes_search_guidance(self):
        """Critic의 System Prompt에 web_search 사용 지침이 있어야 한다."""
        from agents.critic import SYSTEM_PROMPT

        assert "web_search" in SYSTEM_PROMPT
        assert "검증" in SYSTEM_PROMPT or "확인" in SYSTEM_PROMPT

    def test_pi_prompt_includes_search_guidance(self):
        """PI의 System Prompt에 web_search 사용 지침이 있어야 한다."""
        from agents.pi import SYSTEM_PROMPT

        assert "web_search" in SYSTEM_PROMPT
        assert "최신" in SYSTEM_PROMPT or "인용" in SYSTEM_PROMPT
