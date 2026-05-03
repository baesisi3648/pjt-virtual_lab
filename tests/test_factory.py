# @TASK P3-T2 - Dynamic Agent Factory 테스트
# @SPEC TASKS.md#P3-T2
# @TEST tests/test_factory.py
"""Dynamic Agent Factory 테스트

PI가 전문가 프로필을 동적으로 생성하는 팩토리 함수를 테스트합니다.
"""
import sys
import importlib.util
import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import SystemMessage, HumanMessage

# 순환 import 방지를 위해 직접 파일에서 로드
_spec = importlib.util.spec_from_file_location(
    "agents_factory",
    "C:/Users/배성우/Desktop/pjt-virtual_lab/worktree/phase-3-api-ui/agents/factory.py"
)
_factory = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_factory)


class TestAgentFactory:
    """Dynamic Agent Factory 테스트"""

    def test_create_specialist_returns_callable(self):
        """create_specialist는 호출 가능한 에이전트를 반환해야 한다."""
        with patch.object(_factory, 'get_gpt4o') as mock_llm:
            mock_llm_instance = Mock()
            mock_llm.return_value = mock_llm_instance

            profile = {
                "role": "Plant Metabolomics Expert",
                "focus": "fatty acid composition",
                "tools": []
            }
            agent = _factory.create_specialist(profile)

            # 에이전트는 invoke 메서드를 가져야 함
            assert hasattr(agent, "invoke")
            assert callable(agent.invoke)

    def test_generates_system_prompt_from_profile(self):
        """프로필 정보가 system prompt에 반영되어야 한다."""
        with patch.object(_factory, 'get_gpt4o') as mock_llm:
            mock_llm_instance = Mock()
            mock_llm_instance.invoke.return_value = Mock(content="전문가 답변")
            mock_llm.return_value = mock_llm_instance

            profile = {
                "role": "Allergy Specialist",
                "focus": "allergen cross-reactivity",
                "tools": []
            }
            agent = _factory.create_specialist(profile)

            # 에이전트를 실행하여 LLM 호출 확인
            result = agent.invoke("대두 P34 단백질 분석")

            # invoke가 호출되었는지 확인
            assert mock_llm_instance.invoke.called
            call_args = mock_llm_instance.invoke.call_args[0][0]

            # SystemMessage에 프로필 정보가 포함되어야 함
            system_msg = call_args[0]
            assert isinstance(system_msg, SystemMessage)
            assert "Allergy Specialist" in system_msg.content
            assert "allergen cross-reactivity" in system_msg.content

    def test_specialist_responds_to_query(self):
        """생성된 전문가는 질문에 답변할 수 있어야 한다."""
        with patch.object(_factory, 'get_gpt4o') as mock_llm:
            mock_llm_instance = Mock()
            mock_llm_instance.invoke.return_value = Mock(
                content="P34 단백질은 대두의 주요 알레르겐입니다..."
            )
            mock_llm.return_value = mock_llm_instance

            profile = {
                "role": "Allergy Specialist",
                "focus": "protein allergenicity",
                "tools": []
            }
            agent = _factory.create_specialist(profile)

            response = agent.invoke("대두 P34 단백질 분석")

            assert "P34 단백질" in response
            assert len(response) > 0

    def test_profile_validation_requires_role(self):
        """프로필에는 role 필드가 필수여야 한다."""
        with patch.object(_factory, 'get_gpt4o') as mock_llm:
            mock_llm_instance = Mock()
            mock_llm.return_value = mock_llm_instance

            profile = {
                "focus": "something",
                "tools": []
            }

            with pytest.raises(ValueError, match="role"):
                _factory.create_specialist(profile)

    def test_profile_validation_requires_focus(self):
        """프로필에는 focus 필드가 필수여야 한다."""
        with patch.object(_factory, 'get_gpt4o') as mock_llm:
            mock_llm_instance = Mock()
            mock_llm.return_value = mock_llm_instance

            profile = {
                "role": "Expert",
                "tools": []
            }

            with pytest.raises(ValueError, match="focus"):
                _factory.create_specialist(profile)

    def test_uses_gpt4o_by_default(self):
        """기본적으로 GPT-4o 모델을 사용해야 한다."""
        with patch.object(_factory, 'get_gpt4o') as mock_llm:
            mock_llm_instance = Mock()
            mock_llm_instance.invoke.return_value = Mock(content="답변")
            mock_llm.return_value = mock_llm_instance

            profile = {
                "role": "Expert",
                "focus": "test",
                "tools": []
            }
            agent = _factory.create_specialist(profile)
            agent.invoke("질문")

            # get_gpt4o가 호출되었는지 확인
            mock_llm.assert_called_once()

    def test_multiple_specialists_have_different_prompts(self):
        """서로 다른 프로필로 생성된 전문가는 다른 system prompt를 가져야 한다."""
        with patch.object(_factory, 'get_gpt4o') as mock_llm:
            mock_llm_instance = Mock()
            mock_llm_instance.invoke.return_value = Mock(content="답변")
            mock_llm.return_value = mock_llm_instance

            profile1 = {
                "role": "Toxicologist",
                "focus": "acute toxicity",
                "tools": []
            }
            profile2 = {
                "role": "Nutritionist",
                "focus": "nutrient composition",
                "tools": []
            }

            agent1 = _factory.create_specialist(profile1)
            agent2 = _factory.create_specialist(profile2)

            agent1.invoke("test1")
            call1_system = mock_llm_instance.invoke.call_args_list[0][0][0][0]

            agent2.invoke("test2")
            call2_system = mock_llm_instance.invoke.call_args_list[1][0][0][0]

            # 각 에이전트는 고유한 system prompt를 가져야 함
            assert "Toxicologist" in call1_system.content
            assert "Nutritionist" in call2_system.content
            assert call1_system.content != call2_system.content

    def test_tools_parameter_is_optional(self):
        """tools 파라미터는 선택적이어야 한다."""
        with patch.object(_factory, 'get_gpt4o') as mock_llm:
            mock_llm_instance = Mock()
            mock_llm.return_value = mock_llm_instance

            profile = {
                "role": "Expert",
                "focus": "test"
            }

            # tools 없이도 생성 가능해야 함
            agent = _factory.create_specialist(profile)
            assert agent is not None


class TestSystemPromptGeneration:
    """System Prompt 생성 테스트"""

    def test_generate_system_prompt_includes_role(self):
        """생성된 프롬프트는 role을 포함해야 한다."""
        profile = {
            "role": "Toxicologist",
            "focus": "chemical safety"
        }
        prompt = _factory.generate_system_prompt(profile)

        assert "Toxicologist" in prompt
        assert len(prompt) > 0

    def test_generate_system_prompt_includes_focus(self):
        """생성된 프롬프트는 focus를 포함해야 한다."""
        profile = {
            "role": "Expert",
            "focus": "allergen assessment"
        }
        prompt = _factory.generate_system_prompt(profile)

        assert "allergen assessment" in prompt
