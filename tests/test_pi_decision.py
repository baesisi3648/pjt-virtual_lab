# @TASK P3-T3 - PI Decision Logic 테스트
# @SPEC TASKS.md#P3-T3
# @TEST tests/test_pi_decision.py
"""PI Decision Logic 테스트

PI가 쿼리를 분석하여 필요한 전문가 팀을 결정하는 로직을 테스트합니다.
"""
import json
import sys
import importlib.util
import pytest
from unittest.mock import Mock, patch

# 순환 import 방지를 위해 직접 파일에서 로드
_spec = importlib.util.spec_from_file_location(
    "agents_pi",
    "C:/Users/배성우/Desktop/pjt-virtual_lab/worktree/phase-3-api-ui/agents/pi.py"
)
_pi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pi)


class TestPIDecisionLogic:
    """PI 팀 구성 결정 로직 테스트"""

    def test_decide_team_returns_list(self):
        """decide_team은 전문가 프로필 리스트를 반환해야 한다."""
        with patch.object(_pi, 'get_gpt4o') as mock_llm_func:
            mock_llm = Mock()
            mock_response = Mock()
            mock_response.content = json.dumps([
                {"role": "Metabolomics Expert", "focus": "lipid analysis"},
                {"role": "Toxicologist", "focus": "safety assessment"}
            ])
            mock_llm.invoke.return_value = mock_response
            mock_llm_func.return_value = mock_llm

            team = _pi.decide_team("고올레산 대두 안전성 평가")

            assert isinstance(team, list)
            assert len(team) > 0

    def test_decide_team_includes_metabolomics_for_lipid_query(self):
        """지방산 관련 질문에는 Metabolomics 전문가가 포함되어야 한다."""
        with patch.object(_pi, 'get_gpt4o') as mock_llm_func:
            mock_llm = Mock()
            mock_response = Mock()
            mock_response.content = json.dumps([
                {"role": "Metabolomics Expert", "focus": "fatty acid composition"},
                {"role": "Nutrition Toxicologist", "focus": "lipid safety"}
            ])
            mock_llm.invoke.return_value = mock_response
            mock_llm_func.return_value = mock_llm

            team = _pi.decide_team("고올레산 대두 안전성 평가")

            # Metabolomics 전문가가 포함되어 있는지 확인
            assert any("Metabol" in expert['role'] for expert in team)

    def test_decide_team_validates_profile_structure(self):
        """각 전문가 프로필은 role과 focus를 포함해야 한다."""
        with patch.object(_pi, 'get_gpt4o') as mock_llm_func:
            mock_llm = Mock()
            mock_response = Mock()
            mock_response.content = json.dumps([
                {"role": "Expert 1", "focus": "area 1"},
                {"role": "Expert 2", "focus": "area 2"}
            ])
            mock_llm.invoke.return_value = mock_response
            mock_llm_func.return_value = mock_llm

            team = _pi.decide_team("test query")

            for expert in team:
                assert "role" in expert
                assert "focus" in expert
                assert isinstance(expert["role"], str)
                assert isinstance(expert["focus"], str)

    def test_decide_team_handles_code_block_response(self):
        """LLM이 ```json``` 코드 블록으로 감싼 응답도 처리해야 한다."""
        with patch.object(_pi, 'get_gpt4o') as mock_llm_func:
            mock_llm = Mock()
            mock_response = Mock()
            # 코드 블록으로 감싼 형식
            mock_response.content = """```json
[
  {"role": "Expert 1", "focus": "area 1"}
]
```"""
            mock_llm.invoke.return_value = mock_response
            mock_llm_func.return_value = mock_llm

            team = _pi.decide_team("test query")

            assert isinstance(team, list)
            assert len(team) == 1
            assert team[0]["role"] == "Expert 1"

    def test_decide_team_raises_error_on_invalid_json(self):
        """유효하지 않은 JSON 응답은 ValueError를 발생시켜야 한다."""
        with patch.object(_pi, 'get_gpt4o') as mock_llm_func:
            mock_llm = Mock()
            mock_response = Mock()
            mock_response.content = "This is not JSON"
            mock_llm.invoke.return_value = mock_response
            mock_llm_func.return_value = mock_llm

            with pytest.raises(ValueError, match="JSON으로 파싱할 수 없습니다"):
                _pi.decide_team("test query")

    def test_decide_team_raises_error_on_missing_fields(self):
        """role이나 focus가 누락된 프로필은 ValueError를 발생시켜야 한다."""
        with patch.object(_pi, 'get_gpt4o') as mock_llm_func:
            mock_llm = Mock()
            mock_response = Mock()
            # focus 필드 누락
            mock_response.content = json.dumps([
                {"role": "Expert 1"}
            ])
            mock_llm.invoke.return_value = mock_response
            mock_llm_func.return_value = mock_llm

            with pytest.raises(ValueError, match="role과 focus 필드가 필요"):
                _pi.decide_team("test query")

    def test_decide_team_limits_expert_count(self):
        """전문가 수는 1명 이상 5명 이하여야 한다."""
        with patch.object(_pi, 'get_gpt4o') as mock_llm_func:
            mock_llm = Mock()
            mock_response = Mock()
            mock_response.content = json.dumps([
                {"role": f"Expert {i}", "focus": f"area {i}"}
                for i in range(1, 6)
            ])
            mock_llm.invoke.return_value = mock_response
            mock_llm_func.return_value = mock_llm

            team = _pi.decide_team("complex query requiring multiple experts")

            assert len(team) >= 1
            assert len(team) <= 5

    def test_decide_team_uses_gpt4o(self):
        """decide_team은 GPT-4o 모델을 사용해야 한다."""
        with patch.object(_pi, 'get_gpt4o') as mock_llm_func:
            mock_llm = Mock()
            mock_response = Mock()
            mock_response.content = json.dumps([
                {"role": "Expert", "focus": "area"}
            ])
            mock_llm.invoke.return_value = mock_response
            mock_llm_func.return_value = mock_llm

            _pi.decide_team("test query")

            # get_gpt4o가 호출되었는지 확인
            mock_llm_func.assert_called_once()

    def test_decide_team_includes_query_in_prompt(self):
        """사용자 질문이 LLM 프롬프트에 포함되어야 한다."""
        with patch.object(_pi, 'get_gpt4o') as mock_llm_func:
            mock_llm = Mock()
            mock_response = Mock()
            mock_response.content = json.dumps([
                {"role": "Expert", "focus": "area"}
            ])
            mock_llm.invoke.return_value = mock_response
            mock_llm_func.return_value = mock_llm

            user_query = "고올레산 대두 안전성 평가"
            _pi.decide_team(user_query)

            # invoke 호출 확인
            assert mock_llm.invoke.called
            call_args = mock_llm.invoke.call_args[0][0]

            # HumanMessage에 사용자 질문이 포함되어 있는지 확인
            human_msg = call_args[1]
            assert user_query in human_msg.content


class TestPITeamDecisionIntegration:
    """PI 팀 구성 결정과 Factory 통합 테스트"""

    def test_decided_team_can_be_used_with_factory(self):
        """decide_team이 반환한 프로필은 create_specialist에 사용 가능해야 한다."""
        # factory 모듈 로드
        _spec_factory = importlib.util.spec_from_file_location(
            "agents_factory",
            "C:/Users/배성우/Desktop/pjt-virtual_lab/worktree/phase-3-api-ui/agents/factory.py"
        )
        _factory = importlib.util.module_from_spec(_spec_factory)
        _spec_factory.loader.exec_module(_factory)

        with patch.object(_pi, 'get_gpt4o') as mock_llm_func_pi, \
             patch.object(_factory, 'get_gpt4o') as mock_llm_func_factory:

            # PI Mock
            mock_llm_pi = Mock()
            mock_response_pi = Mock()
            mock_response_pi.content = json.dumps([
                {"role": "Metabolomics Expert", "focus": "lipid analysis"}
            ])
            mock_llm_pi.invoke.return_value = mock_response_pi
            mock_llm_func_pi.return_value = mock_llm_pi

            # Factory Mock
            mock_llm_factory = Mock()
            mock_llm_func_factory.return_value = mock_llm_factory

            # 1. PI가 팀 구성
            team = _pi.decide_team("고올레산 대두 안전성")

            # 2. 각 전문가를 Factory로 생성
            for profile in team:
                agent = _factory.create_specialist(profile)
                assert agent is not None
                assert hasattr(agent, 'invoke')
