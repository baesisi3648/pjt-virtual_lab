# @TASK P3-T3 - PI Decision Logic 통합 테스트 (실제 LLM 호출)
# @SPEC TASKS.md#P3-T3
# @TEST tests/test_pi_decision_integration.py
"""PI Decision Logic 실제 LLM 통합 테스트

실제 OpenAI API를 호출하여 decide_team 함수의 동작을 검증합니다.
환경 변수에 OPENAI_API_KEY가 설정되어 있어야 합니다.
"""
import os
import sys
import importlib.util
import pytest
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수 확인
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY 환경 변수가 필요합니다."
)

# 순환 import 방지를 위해 직접 파일에서 로드
_spec = importlib.util.spec_from_file_location(
    "agents_pi",
    "C:/Users/배성우/Desktop/pjt-virtual_lab/worktree/phase-3-api-ui/agents/pi.py"
)
_pi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pi)


class TestPIDecisionIntegration:
    """PI 팀 구성 결정 실제 LLM 통합 테스트"""

    def test_decide_team_with_real_llm_lipid_query(self):
        """실제 LLM으로 지방산 관련 쿼리 처리"""
        team = _pi.decide_team("고올레산 대두의 지방산 조성 변화에 대한 안전성 평가")

        # 결과 검증
        assert isinstance(team, list)
        assert len(team) >= 1
        assert len(team) <= 5

        # 각 전문가는 role과 focus를 가져야 함
        for expert in team:
            assert "role" in expert
            assert "focus" in expert
            assert len(expert["role"]) > 0
            assert len(expert["focus"]) > 0

        # 지방산/대사체 관련 전문가가 포함되어야 함
        roles = [expert["role"].lower() for expert in team]
        focuses = [expert["focus"].lower() for expert in team]
        all_text = " ".join(roles + focuses)
        assert any(
            keyword in all_text
            for keyword in ["metabol", "lipid", "fatty", "nutrition", "지방", "대사", "영양"]
        ), f"Expected metabolomics/lipid expert, but got: {team}"

    def test_decide_team_with_real_llm_allergen_query(self):
        """실제 LLM으로 알레르겐 관련 쿼리 처리"""
        team = _pi.decide_team("유전자편집 대두의 알레르겐성 평가")

        # 결과 검증
        assert isinstance(team, list)
        assert len(team) >= 1
        assert len(team) <= 5

        # 알레르기 관련 전문가가 포함되어야 함
        roles = [expert["role"].lower() for expert in team]
        focuses = [expert["focus"].lower() for expert in team]
        all_text = " ".join(roles + focuses)
        assert any(
            keyword in all_text
            for keyword in ["allerg", "immunolog", "toxicolog", "protein", "알레르", "독성", "단백질", "면역"]
        ), f"Expected allergy/immunology expert, but got: {team}"

    def test_decide_team_with_real_llm_general_safety_query(self):
        """실제 LLM으로 일반 안전성 쿼리 처리"""
        team = _pi.decide_team("NGT 식품의 표준 안전성 평가 프레임워크 개발")

        # 결과 검증
        assert isinstance(team, list)
        assert len(team) >= 2  # 일반적인 주제이므로 여러 전문가 필요
        assert len(team) <= 5

        # 각 전문가는 role과 focus를 가져야 함
        for expert in team:
            assert "role" in expert
            assert "focus" in expert

    def test_decide_team_profiles_are_factory_compatible(self):
        """decide_team이 반환한 프로필은 create_specialist와 호환되어야 함"""
        # factory 모듈 로드
        _spec_factory = importlib.util.spec_from_file_location(
            "agents_factory",
            "C:/Users/배성우/Desktop/pjt-virtual_lab/worktree/phase-3-api-ui/agents/factory.py"
        )
        _factory = importlib.util.module_from_spec(_spec_factory)
        _spec_factory.loader.exec_module(_factory)

        # 1. PI가 팀 구성
        team = _pi.decide_team("고올레산 대두 안전성 평가")

        # 2. 각 전문가를 Factory로 생성 가능해야 함
        for profile in team:
            agent = _factory.create_specialist(profile)
            assert agent is not None
            assert hasattr(agent, 'invoke')
            assert callable(agent.invoke)
