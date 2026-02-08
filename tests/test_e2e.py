# @TASK P4-V1 - E2E 통합 검증
# @SPEC TASKS.md#P4-V1
# @TEST tests/test_e2e.py
"""End-to-End 통합 테스트

전체 시스템의 통합 동작을 검증합니다:
1. 전체 워크플로우 (Scientist -> Critic -> PI)
2. 수정 루프 (revise 시나리오)
3. FastAPI 서버 API 응답
4. 실제 스크립트 시나리오 (Over-regulation 지적)
"""
import pytest
from unittest.mock import patch, Mock
from workflow.graph import create_workflow
from workflow.state import AgentState, CritiqueResult


class TestE2EWorkflow:
    """전체 워크플로우 E2E 테스트"""

    @patch("agents.scientist.get_gpt4o_mini")
    @patch("agents.critic.get_gpt4o")
    @patch("agents.pi.get_gpt4o")
    def test_full_pipeline_approve_immediately(self, mock_pi, mock_critic, mock_scientist):
        """즉시 승인 시나리오

        Scientist가 초안 작성 -> Critic이 즉시 승인 -> PI가 최종 보고서 생성
        """
        # Scientist mock
        scientist_llm = Mock()
        scientist_llm.invoke.return_value = Mock(
            content="NGT 기술의 주요 위험 요소는 Off-target 효과입니다."
        )
        mock_scientist.return_value = scientist_llm

        # Critic mock (즉시 승인)
        critic_llm = Mock()
        critic_llm.invoke.return_value = Mock(
            content='{"decision": "approve", "feedback": "", "scores": {"scientific": 4, "universal": 4, "regulation": 4}}'
        )
        mock_critic.return_value = critic_llm

        # PI mock
        pi_llm = Mock()
        pi_llm.invoke.return_value = Mock(
            content="# 유전자편집식품 표준 안전성 평가 프레임워크\n## 1. 개요\n## 2. 위험 식별\n## 3. 최소 자료 요건\n## 4. 결론"
        )
        mock_pi.return_value = pi_llm

        # 워크플로우 실행
        workflow = create_workflow()
        initial_state: AgentState = {
            "topic": "유전자편집식품(NGT) 표준 안전성 평가",
            "constraints": "합리적 규제",
            "draft": "",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
        }

        result = workflow.invoke(initial_state)

        # 검증
        assert result["final_report"] != ""
        assert "#" in result["final_report"]
        assert "개요" in result["final_report"]
        assert "위험 식별" in result["final_report"]
        assert "최소 자료 요건" in result["final_report"]
        assert "결론" in result["final_report"]
        assert result["iteration"] == 0
        assert len(result["messages"]) >= 3  # scientist, critic, pi

    @patch("agents.scientist.get_gpt4o_mini")
    @patch("agents.critic.get_gpt4o")
    @patch("agents.pi.get_gpt4o")
    def test_full_pipeline_with_revision(self, mock_pi, mock_critic, mock_scientist):
        """수정 루프 시나리오

        Scientist 초안 -> Critic이 수정 요청 -> Scientist 재작성 -> Critic 승인 -> PI 최종 보고서
        """
        # Scientist mock (초안 + 수정)
        scientist_llm = Mock()
        scientist_llm.invoke.side_effect = [
            Mock(content="초안"),
            Mock(content="수정된 초안"),
        ]
        mock_scientist.return_value = scientist_llm

        # Critic mock (첫 번째: revise, 두 번째: approve)
        critic_llm = Mock()
        critic_llm.invoke.side_effect = [
            Mock(content='{"decision": "revise", "feedback": "범용성 부족", "scores": {}}'),
            Mock(content='{"decision": "approve", "feedback": "", "scores": {}}'),
        ]
        mock_critic.return_value = critic_llm

        # PI mock
        pi_llm = Mock()
        pi_llm.invoke.return_value = Mock(content="# 보고서\n## 1. 개요\n## 2. 위험\n## 3. 자료\n## 4. 결론")
        mock_pi.return_value = pi_llm

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
        assert result["iteration"] >= 1
        # Scientist가 최소 2회 호출 (초안 + 수정)
        assert scientist_llm.invoke.call_count >= 2


class TestE2EFastAPI:
    """FastAPI 서버 E2E 테스트"""

    @patch("server.create_workflow")
    def test_api_returns_valid_response(self, mock_workflow):
        """API가 올바른 응답을 반환하는지 검증"""
        from fastapi.testclient import TestClient
        from server import app

        # Mock workflow
        mock_wf = Mock()
        mock_wf.invoke.return_value = {
            "final_report": "# 보고서\n## 1. 개요",
            "messages": [
                {"role": "scientist", "content": "초안 작성"},
                {"role": "critic", "content": "승인"},
                {"role": "pi", "content": "보고서 생성"},
            ],
            "iteration": 0,
        }
        mock_workflow.return_value = mock_wf

        client = TestClient(app)
        response = client.post(
            "/api/research",
            json={"topic": "NGT 평가", "constraints": "합리적 규제"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "report" in data
        assert "messages" in data
        assert "iterations" in data
        assert data["report"] == "# 보고서\n## 1. 개요"
        assert len(data["messages"]) == 3
        assert data["iterations"] == 0


class TestE2EScriptScenario:
    """스크립트 시나리오 재현 테스트"""

    @patch("agents.scientist.get_gpt4o_mini")
    @patch("agents.critic.get_gpt4o")
    @patch("agents.pi.get_gpt4o")
    def test_over_regulation_critique_scenario(self, mock_pi, mock_critic, mock_scientist):
        """Over-regulation 지적 -> 수정 시나리오

        Scientist가 모든 NGT에 독성실험 요구 -> Critic이 과도한 규제로 지적
        -> Scientist가 조건부 제출로 수정 -> Critic 승인 -> PI 최종 보고서
        """
        # Scientist mock (GMO 기준 그대로 제안 -> 조건부 제출로 수정)
        scientist_llm = Mock()
        scientist_llm.invoke.side_effect = [
            Mock(content="모든 NGT는 전신 독성 실험(동물 90일) 필수"),
            Mock(content="신규 단백질 발현 시에만 독성 실험 필수 (SDN-1 면제)"),
        ]
        mock_scientist.return_value = scientist_llm

        # Critic mock (첫 번째: Over-regulation 지적, 두 번째: 승인)
        critic_llm = Mock()
        critic_llm.invoke.side_effect = [
            Mock(content='{"decision": "revise", "feedback": "과도한 규제입니다. 유전자편집은 외래 유전자가 없는 경우가 많으므로 조건부 제출로 변경하세요.", "scores": {"scientific": 3, "universal": 2, "regulation": 1}}'),
            Mock(content='{"decision": "approve", "feedback": "", "scores": {"scientific": 4, "universal": 4, "regulation": 4}}'),
        ]
        mock_critic.return_value = critic_llm

        # PI mock
        pi_llm = Mock()
        pi_llm.invoke.return_value = Mock(
            content="# NGT 표준 평가 프레임워크\n## 3. 최소 제출 자료 요건\n- **독성 실험**: 신규 단백질 발현 시에만 필수 (SDN-1 면제)"
        )
        mock_pi.return_value = pi_llm

        workflow = create_workflow()
        initial_state: AgentState = {
            "topic": "유전자편집식품 표준 평가 가이드라인",
            "constraints": "기존 GMO 대비 합리적 완화",
            "draft": "",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
        }

        result = workflow.invoke(initial_state)

        # 검증
        assert result["iteration"] >= 1  # 최소 1회 수정
        assert "SDN-1 면제" in result["final_report"] or "조건부" in result["final_report"]

        # Critic이 "과도한 규제" 지적 또는 "조건부" 제출 언급
        assert len(result["messages"]) >= 4  # scientist(초안), critic(수정요청), scientist(재작성), critic(승인), pi
