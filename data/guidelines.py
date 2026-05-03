"""Reference text assets injected into agent system prompts.

Historically these constants were defined inline in this file. They have been
externalised to `prompts/data/*.md` (private) with a public placeholder set at
`prompts.example/data/*.md`. This module now loads them lazily from disk so
that the public repository ships only sanitised placeholders, while the full
study prompts remain available locally to the authors.

See `utils/prompt_loader.py` for the loading logic and override semantics.
"""
from __future__ import annotations

from utils.prompt_loader import load_data


# Lazy loaders — module-level constants populated on first import.
RESEARCH_OBJECTIVE: str = load_data("research_objective")
CODEX_PRINCIPLES: str = load_data("codex_principles")
REGULATORY_TRENDS: str = load_data("regulatory_trends")
RESEARCH_AGENDA: str = load_data("research_agenda")
ACADEMIC_TONE_GUIDE: str = load_data("academic_tone_guide")
CRITIQUE_RUBRIC: str = load_data("critique_rubric")
