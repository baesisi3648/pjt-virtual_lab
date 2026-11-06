"""Report translator — generates a Korean rendering of the final English report.

Runs as the last node of the workflow, after `final_synthesis`. The English
report is the primary artefact; the Korean translation is produced once at
generation time and persisted as a sidecar so that the UI language toggle is
instantaneous (no per-toggle API calls).
"""
from __future__ import annotations

import logging

from utils.llm import call_gpt
from utils.prompt_loader import load_system
from workflow.state import AgentState

logger = logging.getLogger(__name__)


_TRANSLATOR_SYSTEM_PROMPT: str = load_system("translator_en_to_ko")


def translate_en_to_ko(report_en: str) -> str:
    """Translate an English research report into formal academic Korean.

    Mermaid diagrams, tables, headings, and code fences must be preserved
    verbatim — only human-readable text is translated. The system prompt
    encodes that contract.
    """
    if not report_en or not report_en.strip():
        return ""
    # Lower temperature for translation faithfulness.
    return call_gpt(
        _TRANSLATOR_SYSTEM_PROMPT,
        report_en,
        temperature=0.2,
        max_tokens=65536,
        tag={"agent": "Translator", "step": "translation"},
    )


def run_translation(state: AgentState) -> dict:
    """Workflow node — produce the Korean translation of `final_report`."""
    report_en = state.get("final_report", "")

    print(f"\n{'#'*80}")
    print(f"[TRANSLATION] Translating final report to Korean")
    print(f"  English report: {len(report_en)} chars")
    print(f"{'#'*80}\n")

    if not report_en.strip():
        logger.warning("Translation skipped: empty final_report")
        return {"final_report_ko": ""}

    # Revision: the Korean translation is a secondary artefact. A failure does not
    # abort the run, but it is recorded in the state (and in meta.json).
    translation_error = ""
    try:
        report_ko = translate_en_to_ko(report_en)
        print(f"[TRANSLATION] Korean rendering: {len(report_ko)} chars")
    except Exception as e:
        logger.warning(f"Translation failed: {e}")
        report_ko = ""
        translation_error = f"{type(e).__name__}: {e}"[:1000]

    messages = list(state.get("messages", []))
    messages.append({
        "role": "translator",
        "content": (
            "Generated Korean translation of the final report."
            if report_ko
            else "Translation failed; only the English report is available."
        ),
    })

    return {
        "final_report_ko": report_ko,
        "translation_error": translation_error,
        "messages": messages,
    }
