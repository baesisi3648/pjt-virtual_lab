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
# research_objective / codex_principles / regulatory_trends were loaded here in the
# submitted version but never passed to any agent; they were removed in the revision
# (revision_plan F20, C18).
RESEARCH_AGENDA: str = load_data("research_agenda")
ACADEMIC_TONE_GUIDE: str = load_data("academic_tone_guide")
CRITIQUE_RUBRIC: str = load_data("critique_rubric")
