"""규제 가이드라인 텍스트 에셋 테스트
# @TASK P1-R2-T1 - 규제 가이드라인 텍스트 에셋 구현
# @SPEC docs/planning/02-trd.md#규제-가이드라인
"""
import pytest


class TestResearchObjective:
    """연구 목표 정의서 테스트"""

    def test_exists(self):
        from data.guidelines import RESEARCH_OBJECTIVE
        assert RESEARCH_OBJECTIVE is not None

    def test_is_string(self):
        from data.guidelines import RESEARCH_OBJECTIVE
        assert isinstance(RESEARCH_OBJECTIVE, str)

    def test_contains_category_keyword(self):
        from data.guidelines import RESEARCH_OBJECTIVE
        assert "카테고리" in RESEARCH_OBJECTIVE or "category" in RESEARCH_OBJECTIVE.lower()

    def test_not_product_specific(self):
        from data.guidelines import RESEARCH_OBJECTIVE
        assert "개별 제품" in RESEARCH_OBJECTIVE or "범용" in RESEARCH_OBJECTIVE


class TestCodexPrinciples:
    """국제 표준 요약 테스트"""

    def test_exists(self):
        from data.guidelines import CODEX_PRINCIPLES
        assert CODEX_PRINCIPLES is not None

    def test_contains_four_principles(self):
        from data.guidelines import CODEX_PRINCIPLES
        keywords = ["분자", "독성", "알레르기", "영양"]
        found = sum(1 for k in keywords if k in CODEX_PRINCIPLES)
        assert found >= 3, f"4대 원칙 중 {found}개만 포함됨"


class TestRegulatoryTrends:
    """규제 동향 테스트"""

    def test_exists(self):
        from data.guidelines import REGULATORY_TRENDS
        assert REGULATORY_TRENDS is not None

    def test_mentions_process_or_product_based(self):
        from data.guidelines import REGULATORY_TRENDS
        text = REGULATORY_TRENDS.lower()
        assert "process" in text or "product" in text


class TestCritiqueRubric:
    """비평 기준표 테스트"""

    def test_exists(self):
        from data.guidelines import CRITIQUE_RUBRIC
        assert CRITIQUE_RUBRIC is not None

    def test_contains_scoring_criteria(self):
        from data.guidelines import CRITIQUE_RUBRIC
        assert "과학적" in CRITIQUE_RUBRIC or "근거" in CRITIQUE_RUBRIC

    def test_contains_universality_check(self):
        from data.guidelines import CRITIQUE_RUBRIC
        assert "범용" in CRITIQUE_RUBRIC or "카테고리" in CRITIQUE_RUBRIC

    def test_contains_overregulation_check(self):
        from data.guidelines import CRITIQUE_RUBRIC
        assert "과도" in CRITIQUE_RUBRIC or "과잉" in CRITIQUE_RUBRIC


class TestAllGuidelines:
    """전체 가이드라인 통합 테스트"""

    def test_all_four_assets_exist(self):
        from data.guidelines import (
            RESEARCH_OBJECTIVE,
            CODEX_PRINCIPLES,
            REGULATORY_TRENDS,
            CRITIQUE_RUBRIC,
        )
        assets = [RESEARCH_OBJECTIVE, CODEX_PRINCIPLES, REGULATORY_TRENDS, CRITIQUE_RUBRIC]
        assert all(asset and len(asset) > 50 for asset in assets), "모든 에셋은 50자 이상이어야 합니다"
