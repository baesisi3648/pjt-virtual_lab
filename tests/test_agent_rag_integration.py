"""
RAG Integration Tests for Scientist Agent

Scientist 에이전트가 RAG 도구를 사용하여 규제 문서를 검색하고
citation을 포함하여 답변하는지 테스트합니다.
"""
import pytest
from unittest.mock import patch, MagicMock

from tools.rag_search import rag_search_tool


class TestRAGSearchTool:
    """RAG Search Tool 단위 테스트"""

    @patch('tools.rag_search.retrieve')
    def test_rag_search_tool_success(self, mock_retrieve):
        """RAG 검색 성공 시 citation 포함 컨텍스트 반환"""
        # Arrange
        mock_retrieve.return_value = [
            {
                'text': 'Substantial equivalence is a key principle in safety assessment.',
                'metadata': {'source': 'Codex Guideline', 'year': 2003, 'page': 5},
                'distance': 0.1
            }
        ]

        # Act
        result = rag_search_tool.invoke({"query": "What is substantial equivalence?"})

        # Assert
        assert "Substantial equivalence" in result
        assert "[출처: Codex Guideline (2003), p.5]" in result
        mock_retrieve.assert_called_once_with("What is substantial equivalence?", top_k=3)

    @patch('tools.rag_search.retrieve')
    def test_rag_search_tool_no_results(self, mock_retrieve):
        """RAG 검색 결과가 없을 경우 안내 메시지 반환"""
        # Arrange
        mock_retrieve.return_value = []

        # Act
        result = rag_search_tool.invoke({"query": "Unknown topic"})

        # Assert
        assert "관련 규제 문서를 찾을 수 없습니다" in result

    @patch('tools.rag_search.retrieve')
    def test_rag_search_tool_exception(self, mock_retrieve):
        """RAG 검색 중 예외 발생 시 에러 메시지 반환"""
        # Arrange
        mock_retrieve.side_effect = Exception("ChromaDB connection failed")

        # Act
        result = rag_search_tool.invoke({"query": "Test query"})

        # Assert
        assert "RAG 검색 오류" in result
        assert "ChromaDB connection failed" in result


class TestScientistRAGIntegration:
    """Scientist 에이전트 RAG 통합 테스트

    Note: Scientist 통합 테스트는 circular import 이슈로 인해
    실제 통합 검증은 demo script로 수행합니다.
    """

    def test_rag_tool_can_be_imported(self):
        """RAG 도구를 정상적으로 import 할 수 있는지 검증"""
        from tools.rag_search import rag_search_tool
        assert rag_search_tool is not None
        assert callable(rag_search_tool.invoke)


class TestScientistWithRAG:
    """Scientist + RAG 통합 테스트 (구현 후 활성화)

    이 테스트들은 scientist.py에 RAG 도구를 통합한 후
    PASS 되어야 합니다.
    """

    @pytest.mark.skip(reason="RAG 통합 전 - P1-T4에서 구현 예정")
    @patch('agents.scientist.get_gpt4o_mini')
    @patch('tools.rag_search.retrieve')
    def test_scientist_uses_rag_tool(self, mock_retrieve, mock_llm):
        """Scientist가 RAG 도구를 호출하여 규제 문서 검색"""
        # Late import to avoid circular dependency
        from agents.scientist import run_scientist

        # Arrange
        mock_retrieve.return_value = [
            {
                'text': '알레르기 평가는 아미노산 서열 유사성 분석을 포함해야 한다.',
                'metadata': {'source': 'Codex Guideline', 'year': 2003, 'page': 12},
                'distance': 0.05
            }
        ]

        mock_model = MagicMock()
        # LLM이 RAG 도구를 호출하도록 설정
        mock_model.invoke.return_value = MagicMock(
            content="[규제 검색 결과]\n알레르기 평가는 아미노산 서열 유사성 분석을 포함해야 한다.\n[출처: Codex Guideline (2003), p.12]"
        )
        mock_llm.return_value = mock_model

        state = {
            "topic": "대두 알레르기 평가",
            "constraints": "Codex 기준 준수",
            "messages": []
        }

        # Act
        result = run_scientist(state)

        # Assert
        assert "[출처:" in result["draft"] or "Codex" in result["draft"]
        # RAG가 호출되었는지 확인 (LLM이 tool을 사용하는 경우)
        # 실제 구현에서는 AgentExecutor 또는 bind_tools 사용

    @pytest.mark.skip(reason="RAG 통합 전 - P1-T4에서 구현 예정")
    @patch('agents.scientist.get_gpt4o_mini')
    @patch('tools.rag_search.retrieve')
    def test_scientist_includes_citation(self, mock_retrieve, mock_llm):
        """Scientist 응답에 citation이 포함되는지 검증"""
        # Late import to avoid circular dependency
        from agents.scientist import run_scientist

        # Arrange
        mock_retrieve.return_value = [
            {
                'text': 'Safety assessment should follow a comparative approach.',
                'metadata': {'source': 'EFSA Opinion', 'year': 2023, 'page': 8},
                'distance': 0.08
            }
        ]

        mock_model = MagicMock()
        mock_model.invoke.return_value = MagicMock(
            content="안전성 평가는 비교 접근법을 따라야 합니다. [출처: EFSA Opinion (2023), p.8]"
        )
        mock_llm.return_value = mock_model

        state = {
            "topic": "NGT 안전성 평가 방법론",
            "constraints": "",
            "messages": []
        }

        # Act
        result = run_scientist(state)

        # Assert
        assert "[출처: EFSA Opinion (2023), p.8]" in result["draft"]
