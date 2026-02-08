# @TASK P3-T1 - Parallel Meeting Architecture 테스트
# @SPEC Phase 3 - Map-Reduce 패턴 테스트
"""Parallel Workflow 테스트

3개 에이전트가 동시에 위험 분석을 수행하고,
PI가 결과를 통합하는 Map-Reduce 패턴을 검증합니다.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from workflow.state import AgentState


class TestParallelRiskAnalysis:
    """병렬 위험 분석 테스트"""

    @patch("workflow.parallel_graph.get_gpt4o_mini")
    @patch("workflow.parallel_graph.get_gpt4o")
    def test_parallel_execution(self, mock_gpt4o, mock_gpt4o_mini):
        """3개 에이전트가 동시에 위험 분석을 수행하는지 검증"""
        # Mock LLM instances with ainvoke for async calls
        mock_mini_instance = Mock()
        mock_mini_instance.ainvoke = AsyncMock(return_value=Mock(content="Scientist analysis"))
        mock_gpt4o_mini.return_value = mock_mini_instance

        # Mock GPT-4o for both critic and PI calls
        mock_4o_instance = Mock()
        mock_4o_instance.ainvoke = AsyncMock(return_value=Mock(content="Critic/PI analysis"))
        mock_4o_instance.invoke.return_value = Mock(content="# Final Report")
        mock_gpt4o.return_value = mock_4o_instance

        from workflow.parallel_graph import create_parallel_workflow
        workflow = create_parallel_workflow()

        initial_state: AgentState = {
            "topic": "대두 위험 요소",
            "constraints": "합리적 규제",
            "draft": "",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
            "parallel_views": [],
        }

        result = workflow.invoke(initial_state)

        # 검증: parallel_views가 3개 존재
        assert "parallel_views" in result
        assert len(result["parallel_views"]) == 3

        # 검증: 각 view에 agent_name과 analysis가 있음
        for view in result["parallel_views"]:
            assert "agent_name" in view
            assert "analysis" in view

        # 검증: 최종 보고서가 생성됨
        assert result["final_report"] != ""
        assert "#" in result["final_report"]  # Markdown 헤더 확인


class TestMapReducePattern:
    """Map-Reduce 패턴 검증"""

    @patch("workflow.parallel_graph.get_gpt4o_mini")
    @patch("workflow.parallel_graph.get_gpt4o")
    def test_map_phase_produces_multiple_views(self, mock_gpt4o, mock_gpt4o_mini):
        """Map 단계에서 여러 관점의 분석이 생성되는지 검증"""
        # Mock 설정
        mock_mini_instance = Mock()
        mock_mini_instance.ainvoke = AsyncMock(return_value=Mock(content="Analysis A"))
        mock_gpt4o_mini.return_value = mock_mini_instance

        mock_4o_instance = Mock()
        mock_4o_instance.ainvoke = AsyncMock(return_value=Mock(content="Analysis B"))
        mock_4o_instance.invoke.return_value = Mock(content="# Merged Report")
        mock_gpt4o.return_value = mock_4o_instance

        from workflow.parallel_graph import create_parallel_workflow
        workflow = create_parallel_workflow()

        initial_state: AgentState = {
            "topic": "NGT 위험",
            "constraints": "",
            "draft": "",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
            "parallel_views": [],
        }

        result = workflow.invoke(initial_state)

        # Map 단계 검증
        assert len(result["parallel_views"]) == 3
        agent_names = {view["agent_name"] for view in result["parallel_views"]}
        assert "scientist" in agent_names
        assert "critic" in agent_names
        assert "pi" in agent_names


class TestParallelIntegration:
    """PI 통합 로직 테스트"""

    @patch("workflow.parallel_graph.get_gpt4o_mini")
    @patch("workflow.parallel_graph.get_gpt4o")
    def test_pi_merges_parallel_views(self, mock_gpt4o, mock_gpt4o_mini):
        """PI가 병렬 분석 결과를 통합하는지 검증"""
        # Mock 설정
        mock_mini_instance = Mock()
        mock_mini_instance.ainvoke = AsyncMock(return_value=Mock(content="Risk A"))
        mock_gpt4o_mini.return_value = mock_mini_instance

        mock_4o_instance = Mock()
        mock_4o_instance.ainvoke = AsyncMock(return_value=Mock(content="Risk B"))
        mock_4o_instance.invoke.return_value = Mock(
            content="# Integrated Report\n\nRisk A and B combined"
        )
        mock_gpt4o.return_value = mock_4o_instance

        from workflow.parallel_graph import create_parallel_workflow
        workflow = create_parallel_workflow()

        initial_state: AgentState = {
            "topic": "대두",
            "constraints": "",
            "draft": "",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
            "parallel_views": [],
        }

        result = workflow.invoke(initial_state)

        # PI 통합 검증
        assert result["final_report"] != ""
        assert len(result["final_report"]) > 0

        # PI invoke가 1회만 호출되었는지 확인 (merge 단계)
        assert mock_4o_instance.invoke.call_count == 1
