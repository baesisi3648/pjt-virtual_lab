"""Reference text-asset tests.

# @TASK P1-R2-T1 — Regulatory text asset implementation
# @SPEC docs/planning/02-trd.md#regulatory-guidelines

Updated for English-first prompts (paper revision branch); accepts the
Korean originals as a fallback so the tests survive prompt-language toggles.
"""
import pytest


def _any(text: str, *needles: str) -> bool:
    """Return True if any case-insensitive needle is present in text."""
    lowered = text.lower()
    return any(n.lower() in lowered for n in needles)


class TestResearchObjective:
    """Research-objective asset tests."""

    def test_exists(self):
        from data.guidelines import RESEARCH_OBJECTIVE
        assert RESEARCH_OBJECTIVE is not None

    def test_is_string(self):
        from data.guidelines import RESEARCH_OBJECTIVE
        assert isinstance(RESEARCH_OBJECTIVE, str)

    def test_contains_category_keyword(self):
        from data.guidelines import RESEARCH_OBJECTIVE
        assert _any(RESEARCH_OBJECTIVE, "category", "카테고리")

    def test_not_product_specific(self):
        from data.guidelines import RESEARCH_OBJECTIVE
        assert _any(RESEARCH_OBJECTIVE, "universal", "category-level", "범용", "개별 제품")


class TestCodexPrinciples:
    """Codex principles asset tests."""

    def test_exists(self):
        from data.guidelines import CODEX_PRINCIPLES
        assert CODEX_PRINCIPLES is not None

    def test_contains_four_principles(self):
        from data.guidelines import CODEX_PRINCIPLES
        en_keywords = ["molecular", "toxic", "allerg", "nutrition"]
        ko_keywords = ["분자", "독성", "알레르기", "영양"]
        en_found = sum(1 for k in en_keywords if k.lower() in CODEX_PRINCIPLES.lower())
        ko_found = sum(1 for k in ko_keywords if k in CODEX_PRINCIPLES)
        assert max(en_found, ko_found) >= 3, (
            f"Only {max(en_found, ko_found)} of the four principles found"
        )


class TestRegulatoryTrends:
    """Regulatory-trends asset tests."""

    def test_exists(self):
        from data.guidelines import REGULATORY_TRENDS
        assert REGULATORY_TRENDS is not None

    def test_mentions_process_or_product_based(self):
        from data.guidelines import REGULATORY_TRENDS
        assert _any(REGULATORY_TRENDS, "process", "product")


class TestCritiqueRubric:
    """Critique-rubric asset tests."""

    def test_exists(self):
        from data.guidelines import CRITIQUE_RUBRIC
        assert CRITIQUE_RUBRIC is not None

    def test_contains_scoring_criteria(self):
        from data.guidelines import CRITIQUE_RUBRIC
        assert _any(CRITIQUE_RUBRIC, "scientific", "evidence", "과학적", "근거")

    def test_contains_universality_check(self):
        from data.guidelines import CRITIQUE_RUBRIC
        assert _any(CRITIQUE_RUBRIC, "universality", "category", "범용", "카테고리")

    def test_contains_overregulation_check(self):
        from data.guidelines import CRITIQUE_RUBRIC
        assert _any(
            CRITIQUE_RUBRIC,
            "proportionality",
            "over-regulation",
            "excessive",
            "과도",
            "과잉",
        )


class TestAllGuidelines:
    """Aggregate sanity checks."""

    def test_all_four_assets_exist(self):
        from data.guidelines import (
            RESEARCH_OBJECTIVE,
            CODEX_PRINCIPLES,
            REGULATORY_TRENDS,
            CRITIQUE_RUBRIC,
        )
        assets = [RESEARCH_OBJECTIVE, CODEX_PRINCIPLES, REGULATORY_TRENDS, CRITIQUE_RUBRIC]
        assert all(asset and len(asset) > 50 for asset in assets), (
            "All assets must be at least 50 characters long"
        )
