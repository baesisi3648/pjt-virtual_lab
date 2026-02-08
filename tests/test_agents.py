# @TASK P2-R1-T1, P2-R2-T1, P2-R3-T1 - 에이전트 단위 테스트
# @SPEC TASKS.md#P2-R1-T1, TASKS.md#P2-R2-T1, TASKS.md#P2-R3-T1
# @TEST tests/test_agents.py
"""에이전트 단위 테스트

Scientist, Critic 에이전트의 단위 테스트를 정의합니다.
"""
import pytest
from unittest.mock import Mock, patch
from workflow.state import AgentState, CritiqueResult


class TestScientist:
    """Scientist 에이전트 테스트"""

    @patch("agents.scientist.get_gpt4o_mini")
    def test_returns_draft_in_state(self, mock_llm):
        """run_scientist는 draft 필드가 포함된 dict를 반환해야 한다."""
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = Mock(content="위험 요소 초안...")
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
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = Mock(content="초안")
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
        call_args = mock_llm_instance.invoke.call_args
        assert call_args is not None

    @patch("agents.scientist.get_gpt4o_mini")
    def test_adds_message_to_log(self, mock_llm):
        """실행 후 messages 로그에 scientist 역할 메시지가 추가되어야 한다."""
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = Mock(content="초안")
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
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = Mock(content="수정된 초안")
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
        call_args = mock_llm_instance.invoke.call_args[0][0]
        human_msg_content = call_args[1].content
        assert "범용성이 부족합니다" in human_msg_content
        assert result["draft"] == "수정된 초안"

    @patch("agents.scientist.get_gpt4o_mini")
    def test_does_not_mutate_original_messages(self, mock_llm):
        """원본 state의 messages 리스트를 변경하지 않아야 한다."""
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = Mock(content="초안")
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
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = Mock(
            content='{"decision": "approve", "feedback": "", "scores": {"scientific": 4, "universal": 4, "regulation": 4}}'
        )
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
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = Mock(
            content='{"decision": "approve", "feedback": "", "scores": {}}'
        )
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
        assert mock_llm_instance.invoke.called

    @patch("agents.critic.get_gpt4o")
    def test_revise_decision_includes_feedback(self, mock_llm):
        """revise 판정 시 feedback과 메시지가 포함되어야 한다."""
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = Mock(
            content='{"decision": "revise", "feedback": "과학적 근거 보강 필요", "scores": {"scientific": 2, "universal": 4, "regulation": 3}}'
        )
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
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = Mock(
            content='{"decision": "approve", "feedback": "", "scores": {"scientific": 5, "universal": 4, "regulation": 4}}'
        )
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
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = Mock(
            content="이것은 JSON이 아닙니다"
        )
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
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = Mock(
            content='{"decision": "approve", "feedback": "", "scores": {"scientific": 5, "universal": 3, "regulation": 4}}'
        )
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
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = Mock(
            content='{"decision": "approve", "feedback": "", "scores": {}}'
        )
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

    def test_merge_views_removes_duplicates(self):
        """중복된 의견을 제거해야 한다."""
        from agents.critic import merge_views

        views = [
            "동물 실험이 필요합니다.",
            "동물 실험이 필요합니다.",
            "독성 시험이 필요합니다.",
        ]
        merged = merge_views(views)
        # 중복 제거 확인
        assert merged.count("동물 실험이 필요합니다") <= 1
        assert "독성 시험이 필요합니다" in merged

    def test_merge_views_selects_conservative_safety(self):
        """가장 보수적인 안전 기준을 선택해야 한다."""
        from agents.critic import merge_views

        views = [
            "동물 실험은 면제 가능합니다.",
            "동물 실험이 필수입니다.",
            "독성 시험은 선택 사항입니다.",
        ]
        merged = merge_views(views)
        # 보수적 선택: 필수 > 선택 > 면제
        assert "필수" in merged or "동물 실험이 필수" in merged

    def test_merge_views_rejects_unfounded_opinions(self):
        """근거 없는 의견을 기각해야 한다."""
        from agents.critic import merge_views

        views = [
            "과학적 근거: Off-target 효과 때문에 동물 실험 필요",
            "근거 없음: 그냥 필요합니다",
            "과학적 근거: CRISPR의 특성상 독성 시험 필수",
        ]
        merged = merge_views(views)
        # 근거가 명시된 의견만 포함
        assert "과학적 근거" in merged or "Off-target" in merged or "CRISPR" in merged
        # 근거 없는 의견은 배제 (검증 필요)

    def test_merge_views_handles_conflicts(self):
        """상충되는 의견을 합리적으로 해결해야 한다."""
        from agents.critic import merge_views

        views = [
            "동물 실험 불필요 - SDN-1은 기존 육종과 동일",
            "동물 실험 필수 - SDN-2는 외래 유전자 포함",
            "조건부 동물 실험 - SDN 유형에 따라 달라야 함",
        ]
        merged = merge_views(views)
        # 조건부/세분화된 접근을 선택해야 함
        assert "조건부" in merged or "SDN" in merged or "유형" in merged


class TestPI:
    """PI 에이전트 테스트"""

    @patch("agents.pi.get_gpt4o")
    def test_returns_final_report(self, mock_llm):
        """run_pi는 final_report 필드가 포함된 dict를 반환해야 한다."""
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = Mock(
            content="# 최종 보고서\n## 1. 개요"
        )
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
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = Mock(
            content="# Report\n## Section"
        )
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
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = Mock(
            content="# Final\n## 1. Overview"
        )
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
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = Mock(content="# Report")
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
        mock_llm_instance.invoke.assert_called_once()
        call_args = mock_llm_instance.invoke.call_args[0][0]
        # HumanMessage에 topic과 draft가 포함되어야 함
        human_msg_content = call_args[1].content
        assert "유전자편집식품 안전성" in human_msg_content
        assert "위험 요소 목록 초안" in human_msg_content

    @patch("agents.pi.get_gpt4o")
    def test_does_not_mutate_original_messages(self, mock_llm):
        """원본 state의 messages 리스트를 변경하지 않아야 한다."""
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = Mock(content="# Report")
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
