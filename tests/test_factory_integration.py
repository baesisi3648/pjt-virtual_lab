# @TASK P3-T2 - Dynamic Agent Factory 통합 테스트
# @SPEC TASKS.md#P3-T2 - 검증 기준
"""Dynamic Agent Factory 통합 테스트

실제 LLM을 사용하지 않고 모킹하여 완전한 시나리오를 테스트합니다.
"""
import importlib.util
import pytest
from unittest.mock import Mock, patch

# 순환 import 방지를 위해 직접 파일에서 로드
_spec = importlib.util.spec_from_file_location(
    "agents_factory",
    "C:/Users/배성우/Desktop/pjt-virtual_lab/worktree/phase-3-api-ui/agents/factory.py"
)
_factory = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_factory)


class TestFactoryIntegration:
    """Factory 통합 테스트 - 검증 기준 확인"""

    def test_allergy_specialist_example(self):
        """검증 기준: Allergy Specialist 프로필로 대두 P34 단백질 분석 수행"""
        with patch.object(_factory, 'get_gpt4o') as mock_llm:
            # 실제 LLM 응답을 모킹
            mock_llm_instance = Mock()
            mock_llm_instance.invoke.return_value = Mock(
                content="""대두 P34 단백질(Gly m Bd 30K)은 대두의 주요 알레르겐 중 하나입니다.

주요 특징:
1. 분자량: 약 34 kDa
2. 열 안정성: 가열에도 알레르겐성이 유지됨
3. 교차반응성: 다른 콩과 식물과 교차반응 가능

NGT 안전성 평가 시 고려사항:
- 유전자편집으로 P34 발현량이 변경되었는지 확인
- 새로운 알레르겐 생성 가능성 평가
- IgE 결합 패턴 변화 분석

규제 제언:
- P34 단백질 정량 분석 필수
- 혈청학적 시험 권장
- 민감 집단에 대한 임상 평가 고려
"""
            )
            mock_llm.return_value = mock_llm_instance

            # 전문가 프로필 생성
            profile = {
                "role": "Allergy Specialist",
                "focus": "protein allergenicity and cross-reactivity",
                "tools": []
            }

            # 전문가 에이전트 생성
            expert = _factory.create_specialist(profile)

            # 질의 수행
            response = expert.invoke("대두 P34 단백질 분석")

            # 검증
            assert "P34" in response
            assert "알레르겐" in response
            assert len(response) > 100  # 충분히 상세한 답변

            # LLM이 호출되었는지 확인
            assert mock_llm_instance.invoke.called

            # System Prompt에 전문가 역할이 포함되었는지 확인
            call_args = mock_llm_instance.invoke.call_args[0][0]
            system_msg = call_args[0]
            assert "Allergy Specialist" in system_msg.content

    def test_multiple_experts_scenario(self):
        """시나리오: 여러 전문가를 동시에 활용"""
        with patch.object(_factory, 'get_gpt4o') as mock_llm:
            mock_llm_instance = Mock()

            # 각 전문가별 응답 준비
            responses = [
                "독성학적 관점: 급성 독성 평가 필요...",
                "영양학적 관점: 지방산 조성 변화 분석...",
                "알레르겐 관점: 교차반응성 평가 필요..."
            ]
            mock_llm_instance.invoke.side_effect = [
                Mock(content=r) for r in responses
            ]
            mock_llm.return_value = mock_llm_instance

            # 3명의 전문가 생성
            toxicologist = _factory.create_specialist({
                "role": "Toxicologist",
                "focus": "acute and chronic toxicity assessment"
            })

            nutritionist = _factory.create_specialist({
                "role": "Nutritionist",
                "focus": "nutrient composition and bioavailability"
            })

            allergist = _factory.create_specialist({
                "role": "Allergy Specialist",
                "focus": "allergen cross-reactivity"
            })

            # 각 전문가에게 질의
            tox_response = toxicologist.invoke("유전자편집 대두 안전성")
            nut_response = nutritionist.invoke("유전자편집 대두 안전성")
            allergy_response = allergist.invoke("유전자편집 대두 안전성")

            # 검증: 각 전문가가 다른 관점의 답변 제공
            assert "독성학" in tox_response
            assert "영양학" in nut_response
            assert "알레르겐" in allergy_response

            # 3번의 LLM 호출 확인
            assert mock_llm_instance.invoke.call_count == 3

    def test_profile_template_consistency(self):
        """프로필 템플릿이 일관된 형식을 유지하는지 확인"""
        with patch.object(_factory, 'get_gpt4o') as mock_llm:
            mock_llm_instance = Mock()
            mock_llm.return_value = mock_llm_instance

            profiles = [
                {"role": "Metabolomics Expert", "focus": "metabolite profiling"},
                {"role": "Genomics Specialist", "focus": "off-target effects"},
                {"role": "Regulatory Consultant", "focus": "compliance assessment"}
            ]

            prompts = []
            for profile in profiles:
                agent = _factory.create_specialist(profile)
                # System prompt를 확인하기 위해 generate_system_prompt 직접 호출
                prompt = _factory.generate_system_prompt(profile)
                prompts.append(prompt)

            # 모든 프롬프트가 역할과 전문 분야를 포함하는지 확인
            for i, profile in enumerate(profiles):
                assert profile["role"] in prompts[i]
                assert profile["focus"] in prompts[i]
                assert "당신은" in prompts[i]  # 한국어 형식 확인
                assert "임무" in prompts[i]

    def test_error_handling(self):
        """에러 처리 테스트"""
        with patch.object(_factory, 'get_gpt4o') as mock_llm:
            mock_llm_instance = Mock()
            mock_llm.return_value = mock_llm_instance

            # 필수 필드 누락 시 ValueError 발생
            with pytest.raises(ValueError, match="role"):
                _factory.create_specialist({"focus": "test"})

            with pytest.raises(ValueError, match="focus"):
                _factory.create_specialist({"role": "Expert"})
