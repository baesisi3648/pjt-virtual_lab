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


# Tests for research_objective / codex_principles / regulatory_trends were removed
# together with those unused assets (revision_plan C18).


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
    """Aggregate sanity checks for the assets actually injected into agents."""

    def test_all_injected_assets_exist(self):
        from data.guidelines import RESEARCH_AGENDA, ACADEMIC_TONE_GUIDE, CRITIQUE_RUBRIC
        assets = [RESEARCH_AGENDA, ACADEMIC_TONE_GUIDE, CRITIQUE_RUBRIC]
        assert all(asset and len(asset) > 50 for asset in assets)

    def test_unused_assets_removed(self):
        import data.guidelines as g
        for name in ("RESEARCH_OBJECTIVE", "CODEX_PRINCIPLES", "REGULATORY_TRENDS"):
            assert not hasattr(g, name)
