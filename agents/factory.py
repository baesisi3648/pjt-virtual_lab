# @TASK P3-T2 - Dynamic Agent Factory
# @SPEC TASKS.md#P3-T2
# @TEST tests/test_factory.py
"""Dynamic Agent Factory — the PI assembles specialist agents at runtime.

The factory builds a system prompt from an external template
(`prompts/system/specialist.md`), populates the role-specific fields, and
returns a callable specialist agent backed by `utils.llm.call_gpt`.
"""
from typing import Any

from utils.llm import call_gpt
from utils.prompt_loader import load_system, render
from data.guidelines import RESEARCH_AGENDA, ACADEMIC_TONE_GUIDE


def generate_system_prompt(profile: dict) -> str:
    """Build the specialist system prompt from the externalised template."""
    role = profile.get("role", "")
    focus = profile.get("focus", "")

    template = load_system("specialist")
    return render(
        template,
        role=role,
        focus=focus,
        RESEARCH_AGENDA=RESEARCH_AGENDA,
        ACADEMIC_TONE_GUIDE=ACADEMIC_TONE_GUIDE,
    )


class SpecialistAgent:
    """Dynamically generated specialist agent."""

    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt

    def invoke(self, query: str, max_tokens: int = 32768, tag: dict | None = None) -> str:
        return call_gpt(self.system_prompt, query, max_tokens=max_tokens, tag=tag)


def create_specialist(profile: dict) -> SpecialistAgent:
    """Create a specialist agent from a `{role, focus}` profile."""
    if "role" not in profile:
        raise ValueError("profile is missing 'role' field.")
    if "focus" not in profile:
        raise ValueError("profile is missing 'focus' field.")

    system_prompt = generate_system_prompt(profile)
    return SpecialistAgent(system_prompt=system_prompt)
