"""Build the revision prompt sets `prompts_A/` and `prompts_B/` from `prompts/`.

Reproducible, auditable construction of the two experimental conditions
described in `reference/revision/revision_plan.md` (sections 7-8):

- Common changes (A and B): P2 rubric proportionality, P3 neutral role-name
  examples, P4 "Assessment complete" definition + normative-phrasing exception.
  (P1 lives in `run_experiment.py`, and the P4 Rule 3 text in `agents/pi.py`;
  both are code changes made in a later step.)
- Condition A only: Critic scores each round on current content alone
  (no Round-1 cap, no score-comparison / non-decreasing rule).
- The three unused data files (F20) are not copied.

Every replacement must match exactly once in the source file; otherwise the
build aborts. The source `prompts/` directory is never modified.

Usage:
    python scripts/revision/build_prompt_sets.py            # build both sets
    python scripts/revision/build_prompt_sets.py --force    # overwrite existing sets
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "prompts"
OUT_DOC = ROOT / "experiments" / "runs_rev" / "prompt_sets"

UNUSED_DATA_FILES = ("research_objective.md", "codex_principles.md", "regulatory_trends.md")

# (change id, relative path, old text, new text)
COMMON_CHANGES: list[tuple[str, str, str, str]] = [
    (
        "P2-rubric-1",
        "data/critique_rubric.md",
        "[1] Excessively stringent data requirements; reads like a detailed regulatory protocol.",
        "[1] Data requirements are either excessively stringent or insufficient for the identified "
        "hazards; reads like a detailed regulatory protocol or omits assessments without justification.",
    ),
    (
        "P2-rubric-2",
        "data/critique_rubric.md",
        "[2] Some sections are over-prescriptive or burdened with unnecessary technical detail.",
        "[2] Some sections are over-prescriptive, burdened with unnecessary technical detail, or omit "
        "an assessment without a stated scientific rationale.",
    ),
    (
        "P2-critic-axis",
        "system/critic.md",
        "  - proportionality: avoidance of over-regulation",
        "  - proportionality: data requirements commensurate with the identified hazards "
        "(neither excessive nor insufficient)",
    ),
    (
        "P3-team-decision-language",
        "system/pi_team_decision.md",
        'Names like "식물 유전자편집 과학자" are forbidden — use "Plant Genome-Editing Scientist" instead.',
        "Translate any non-English role name into English.",
    ),
    (
        "P3-team-decision-example",
        "system/pi_team_decision.md",
        '- Use short, single-keyword canonical role names — e.g. "Molecular Genetics Specialist", '
        '"Toxicology Specialist", "Regulatory Science Specialist". Avoid long compound names with parentheticals.',
        "- Use short canonical role names in the form '<Discipline> Specialist' (a single discipline "
        "keyword followed by 'Specialist'). Avoid long compound names with parentheticals.",
    ),
    (
        "P3-team-selection-example",
        "system/pi_team_selection.md",
        '5. **Use short, single-keyword canonical role names** — e.g. "Molecular Genetics Specialist", '
        '"Toxicology Specialist", "Regulatory Science Specialist", "Risk Assessment Specialist", '
        '"Bioinformatics Specialist". Do **not** produce long compound names.',
        "5. **Use short canonical role names** in the form '<Discipline> Specialist' (a single discipline "
        "keyword followed by 'Specialist'). Do **not** produce long compound names.",
    ),
    (
        "P3-role-clustering-example",
        "system/role_clustering.md",
        '4. Canonical names should be **short** — ideally a single keyword followed by "Specialist" '
        '(e.g. "Molecular Genetics Specialist", "Toxicology Specialist", "Regulatory Science Specialist", '
        '"Risk Assessment Specialist", "Bioinformatics Specialist"). Avoid long compound names.',
        "4. Canonical names should be **short**, in the form '<Discipline> Specialist' (a single "
        "discipline keyword followed by 'Specialist'). Avoid long compound names.",
    ),
    (
        "P4-report-terminal-node",
        "system/pi_report.md",
        '3. **All paths must converge on a single "Assessment complete" terminal node. No dangling end nodes.**',
        '3. **All paths must end at a single "Assessment complete" terminal node. No dangling end nodes.** '
        "This node marks the end of the assessment pathway and does not by itself indicate that safety "
        "has been established. Where evidence is insufficient or uncertainty remains, route the path "
        'through a node such as "Additional data required" or "Decision deferred pending further data" '
        "before the terminal node. The prohibition on normative phrasing does not apply to wording that "
        "flags uncertainty, requests additional data, or defers a decision.",
    ),
    (
        "P4-tone-guide-exception",
        "data/academic_tone_guide.md",
        "     → Convey necessity through the flow of the argument itself, never through a meta-question.",
        "     → Convey necessity through the flow of the argument itself, never through a meta-question.\n"
        "   - Exception: the prohibition on normative phrasing does not apply to wording that flags uncertainty, requests "
        "additional data, or defers a decision (e.g. \"Additional data required\", \"Decision deferred "
        "pending further data\").",
    ),
]

A_ONLY_CHANGES: list[tuple[str, str, str, str]] = [
    (
        "A-critic-scoring-rules",
        "system/critic.md",
        "- Be especially strict in Round 1.\n"
        "- **Score-comparison rule**: when prior-round scores are provided, compare each specialist against their previous score.\n"
        "  - If a previously flagged weakness has been resolved, raise the score.\n"
        "  - If prior strengths persist alongside new improvements, the score must rise.\n"
        "  - To lower a score, you need an explicit reason (a previously credited strength was removed; a new error was introduced).\n",
        "- Score each contribution on its current content alone, independently of the scores given in previous rounds.\n",
    ),
    (
        "A-critic-round1-cap",
        "system/critic.md",
        "★ In Round 1, no axis may exceed 4.\n",
        "",
    ),
    # Added after the pilot leakage audit (revision_plan 7.6): the request for
    # "actions to reach 5/5" made the Critic restate score levels in its feedback,
    # which then reached the next round's Critic. Condition A asks for actions on the
    # remaining weaknesses and keeps scores out of the feedback text.
    (
        "A-critic-feedback-without-scores",
        "system/critic.md",
        "  3. Concrete actions required to reach 5/5.\n",
        "  3. Concrete actions to address the remaining weaknesses.\n"
        "- In `feedback` and in every entry of `specialist_feedback`, do not mention numeric scores, score "
        "levels or score targets (for example \"4/5\" or \"raise readability to 5\"). Give scores only in the "
        "`scores` object. Scientific quantities and citations are allowed.\n",
    ),
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _apply(base: Path, changes: list[tuple[str, str, str, str]], log: list[dict], condition: str) -> None:
    for change_id, rel, old, new in changes:
        path = base / rel
        text = path.read_text(encoding="utf-8")
        count = text.count(old)
        if count != 1:
            raise SystemExit(f"[{condition}] {change_id}: expected exactly 1 match in {rel}, found {count}")
        path.write_text(text.replace(old, new), encoding="utf-8")
        log.append({"condition": condition, "change_id": change_id, "file": rel})


def build(condition: str, force: bool) -> dict:
    dest = ROOT / f"prompts_{condition}"
    if dest.exists() and not force:
        raise SystemExit(f"{dest} already exists (use --force to rebuild)")
    # Build in a temporary directory first; replace the target only if every change applied.
    tmp = ROOT / f".prompts_{condition}.building"
    if tmp.exists():
        shutil.rmtree(tmp)
    shutil.copytree(SRC, tmp, ignore=shutil.ignore_patterns(*UNUSED_DATA_FILES, "__pycache__"))
    log: list[dict] = []
    try:
        _apply(tmp, COMMON_CHANGES, log, condition)
        if condition == "A":
            _apply(tmp, A_ONLY_CHANGES, log, condition)
    except SystemExit:
        shutil.rmtree(tmp)
        raise
    if dest.exists():
        shutil.rmtree(dest)
    tmp.rename(dest)
    return {
        "condition": condition,
        "changes": log,
        "files": {p.relative_to(dest).as_posix(): _sha256(p) for p in sorted(dest.rglob("*.md"))},
    }


def write_diff(condition: str) -> Path:
    dest = ROOT / f"prompts_{condition}"
    chunks: list[str] = []
    for src_file in sorted(SRC.rglob("*.md")):
        rel = src_file.relative_to(SRC).as_posix()
        new_file = dest / rel
        old_lines = src_file.read_text(encoding="utf-8").splitlines(keepends=True)
        new_lines = new_file.read_text(encoding="utf-8").splitlines(keepends=True) if new_file.exists() else []
        chunks.extend(difflib.unified_diff(old_lines, new_lines, f"prompts/{rel}", f"prompts_{condition}/{rel}"))
    out = OUT_DOC / f"diff_prompts_to_prompts_{condition}.patch"
    out.write_text("".join(chunks), encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    OUT_DOC.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source_dir": "prompts",
        "source_hashes": {p.relative_to(SRC).as_posix(): _sha256(p) for p in sorted(SRC.rglob("*.md"))},
        "excluded_unused_data_files": list(UNUSED_DATA_FILES),
        "sets": [build(c, args.force) for c in ("A", "B")],
    }
    (OUT_DOC / "prompt_sets_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    for c in ("A", "B"):
        print(f"prompts_{c}: diff -> {write_diff(c).relative_to(ROOT)}")
    print(f"changes A={len(manifest['sets'][0]['changes'])} B={len(manifest['sets'][1]['changes'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
