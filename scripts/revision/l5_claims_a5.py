"""L5 citation audit, part 2: key claims of the representative run (A_5, main_v1) under the frozen selection rule.

    python -B scripts/revision/l5_claims_a5.py

Rule (analysis_criteria.json, L5_citation_audit): (a) each Core Question 1 sentence that assigns a category to an
assessment route; (b) the first hazard sentence per technique category in Core Question 2; (c) the decision or
condition sentence of each Core Question 5 step; (d) every waiver, stop or closure statement in Core Questions 4-5.
Uncited claims are included; multi-claim sentences are split into single claims; duplicates are kept once at the
first occurrence; one stratum per claim by priority d > c > a > b; sampling only if more than 30 remain.

Every candidate sentence is logged with the decision (included / excluded / duplicate) and the reason. Quotes are
verbatim substrings of the report. The selection is a draft by Claude (revised after Codex review, 2026-11-08) for
author confirmation. Citation status is read from the report; no source is attached after the fact.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "experiments" / "runs_rev" / "main_v1"
REPORT = MAIN / "A_5" / "attempt_01" / "final_report.md"
OUT = ROOT / "experiments" / "runs_rev" / "results_v1"

# (id, decision, stratum, location, verbatim quote, reason)
CANDIDATES = [
    ("x1", "excluded", "", "CQ1 lead", "classifies New Genomic Techniques", "general classification principle; does not assign a category to a route"),
    ("a2a", "included", "a", "CQ1 SDN-1", "Safety relevance centres on local gene function and pathway context in edible tissues", "split 1/2"),
    ("a2b", "included", "a", "CQ1 SDN-1", "no new DNA remains", "split 2/2"),
    ("a3a", "included", "a", "CQ1 SDN-2", "consider whether the change creates or alters open reading frames", "split 1/2"),
    ("a3b", "included", "a", "CQ1 SDN-2", "or modifies protein behaviour relevant to diet", "split 2/2"),
    ("a4", "included", "a", "CQ1 SDN-3", "This aligns with the established recombinant‑DNA paradigm: insert identity and junctions, inheritance, and any new protein in the diet.", ""),
    ("a5", "included", "a", "CQ1 ODM", "In food contexts, outcomes resemble SDN‑2 and are treated accordingly.", ""),
    ("a6", "included", "a", "CQ1 base/prime editors", "these are handled as nearby on‑target considerations", ""),
    ("b1a", "included", "b", "CQ2 SDN-1 and ODM", "whether the edit changes a pathway in edible tissues in ways that increase exposure to endogenous toxins", "split 1/2 (categories grouped as in the report)"),
    ("b1b", "included", "b", "CQ2 SDN-1 and ODM", "or anti‑nutrients (natural compounds that reduce the absorption or use of nutrients)", "split 2/2"),
    ("b2", "included", "b", "CQ2 SDN-2", "A small intended change can alter an endogenous protein’s sequence or stability.", ""),
    ("b3", "included", "b", "CQ2 SDN-3", "New proteins enter the foreground.", ""),
    ("c1", "included", "c", "CQ5 Step 1", "This sets outcome class (SDN‑1/SDN‑2/SDN‑3/ODM) and links immediately to plausible exposure routes in the food.", ""),
    ("c2a", "included", "c", "CQ5 Step 2", "SDN‑1/ODM emphasise local confirmation", "split 1/3; ODM route differs from CQ1 (a5), so not a duplicate"),
    ("c2b", "included", "c", "CQ5 Step 2", "SDN‑2 adds a continuity‑based read of any altered endogenous protein", "split 2/3; differs from b2"),
    ("c2c", "duplicate", "", "CQ5 Step 2", "SDN‑3 follows the recombinant‑DNA path with insertion/junction characterisation and any new protein", "split 3/3; duplicate of a4"),
    ("c3", "included", "c", "CQ5 Step 3", "Co‑occurring triggers are read as convergence on specific hazard–exposure chains (for example, structural complexity at or near the locus), guiding which checks will add clarity rather than tallying flags.", ""),
    ("c4", "included", "c", "CQ5 Step 4", "The exact sequence change, allelic pattern (which gene copies carry which change), and local structure at the target site are established.", "decision without a condition"),
    ("c5a", "included", "c", "CQ5 Step 5", "Prediction‑informed shortlists are confirmed at priority candidates", "split 1/2"),
    ("c5b", "included", "c", "CQ5 Step 5", "with escalation to whole‑genome sequencing (WGS; comprehensive DNA sequencing across the genome) and long‑read methods when triggers suggest dispersed or structural changes", "split 2/2"),
    ("c6a", "included", "c", "CQ5 Step 6", "Where pathway rewiring is plausible, targeted metabolite panels are added", "split 1/2"),
    ("c6b", "included", "c", "CQ5 Step 6", "where unexplained differences persist, repeating under like conditions helps separate environment from genetics", "split 2/2"),
    ("c7", "included", "c", "CQ5 Step 7", "If a novel or materially altered protein is plausibly present in edible tissues, a weight‑of‑evidence protein appraisal is run.", ""),
    ("c8", "included", "c", "CQ5 Step 8", "When composition shows plausible increases in known hazard classes or when protein appraisal signals concern, targeted toxicology focuses on the relevant class", ""),
    ("x2", "excluded", "", "CQ5 Step 8", "serves as an interpretive aid rather than a gate", "second sentence of the step; not a waiver, stop or closure statement"),
    ("c9", "included", "c", "CQ5 Step 9", "Where processing concentrates constituents, assessment aligns with the product forms consumers will encounter.", "explicit condition of the step"),
    ("d1", "included", "d", "CQ4 composition", "discovery‑style profiling (for example, broad metabolite panels) is added deliberately rather than by default", "omission of a default assessment"),
    ("x3", "excluded", "", "CQ4 triggers", "governs when to widen molecular scope, consider genome‑wide or long‑read sequencing, or add pathway‑aware omics", "condition for widening; no explicit waiver in the text"),
    ("d3", "included", "d", "CQ4 register", "Together they document both targeted data requests and supported waivers with clear, trait‑anchored reasoning.", "waiver documentation"),
    ("x4", "duplicate", "", "CQ4 closing", "This supplementation replaces broad, untargeted defaults", "duplicate of d1"),
    ("d4", "included", "d", "CQ5 lead", "Each step below is activated when it adds explanatory power to a plausible hazard–exposure chain", "activation/omission rule"),
    ("x5", "duplicate", "", "CQ5 lead", "expansions and supported omissions are documented in the uncertainty register and decision log", "duplicate of d3"),
    ("d5a", "included", "d", "CQ5 Step 10", "(a) whether a coherent chain links any gap to increased dietary exposure to a harmful agent", "closure criterion 1/3 ('govern closure or expansion')"),
    ("d5b", "included", "d", "CQ5 Step 10", "(b) whether a wrong assumption would tend to under‑estimate risk", "closure criterion 2/3"),
    ("d5c", "included", "d", "CQ5 Step 10", "(c) whether resolving the gap could change the conclusion", "closure criterion 3/3"),
    ("x6", "duplicate", "", "CQ5 Step 11", "the decision log records additional data requested or supported omissions with short, trait‑anchored justifications", "duplicate of d3"),
    ("d6", "included", "d", "CQ5 Step 11", "When expansions add clarity or when supported omissions leave only low‑leverage uncertainty, the dossier closes with transparent reasoning", "closure statement"),
]
# Explicit claim-source citations: bracketed source tags, numbered references, or parenthetical agency/document
# citations with a year or document number. Mentions of a guideline as a subject are not counted.
CITE = re.compile(r"\[(?:Source|source|Ref|ref)[^\]]{0,160}\]|\[\d+(?:[,–-]\d+)*\]"
                  r"|\((?:[^()]{0,40})(?:EFSA|Codex|CAC/GL|CXG|FDA|FSANZ|Health Canada|MHLW|European Commission|et al\.)"
                  r"[^()]{0,60}(?:\b(?:19|20)\d{2}\b|GL ?\d+|CXG ?\d+)[^()]{0,40}\)")


def count_inline_citations() -> dict:
    out = {}
    for d in sorted(MAIN.iterdir()):
        t = (d / "attempt_01" / "final_report.md").read_text(encoding="utf-8")
        cq = "".join(s for s in re.split(r"(?m)^(?=## )", t) if s.startswith("## Core Question"))
        out[d.name] = CITE.findall(cq)
    return out


def main() -> int:
    text = REPORT.read_text(encoding="utf-8")
    rows = []
    for cid, decision, stratum, loc, quote, reason in CANDIDATES:
        i = text.find(quote)
        if i < 0:
            raise SystemExit(f"{cid}: quote not found verbatim in the report")
        start, end = text.rfind("\n", 0, i) + 1, text.find("\n", i)
        cites = CITE.findall(text[start:end])
        rows.append({"candidate_id": cid, "decision": decision, "stratum": stratum, "location": loc, "claim": quote,
                     "reason": reason, "citation_in_report": "; ".join(cites) if cites else "none",
                     "support": ("not judged: uncited" if not cites else "to judge") if decision == "included" else "",
                     "draft_by": "Claude", "confirmed_by": ""})
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "l5_claims_a5.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    inc = [r for r in rows if r["decision"] == "included"]
    inline = count_inline_citations()
    summary = {
        "representative_run": "A_5 (main_v1)",
        "candidates_logged": len(rows), "decisions": dict(Counter(r["decision"] for r in rows)),
        "claims": len(inc), "by_stratum": dict(Counter(r["stratum"] for r in inc)),
        "sampling": "not needed (30 claims after splitting and de-duplication; threshold: more than 30)",
        "cited_claims": sum(1 for r in inc if r["citation_in_report"] != "none"),
        "uncited_claims": sum(1 for r in inc if r["citation_in_report"] == "none"),
        "support_rate": "not computable (no cited claims); this is not 0% support",
        "inline_citations_cq1_5_all_reports": {k: len(v) for k, v in inline.items()},
        "inline_citations_examples": {k: v[:3] for k, v in inline.items() if v},
        "inline_citation_definition": "bracketed source tags, numbered references, or parenthetical agency/document citations "
                                      "with a year or document number in Core Questions 1-5; a guideline named as a subject is not counted",
        "status": "selection drafted by Claude (revised after Codex review); author confirmation pending",
    }
    (OUT / "l5_claims_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("candidates_logged", "decisions", "claims", "by_stratum", "cited_claims",
                                              "uncited_claims", "inline_citations_cq1_5_all_reports")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
