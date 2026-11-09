"""L6 dissent analysis (revision_plan section 11, L6) for the revised-protocol runs of main_v1.

    python -B scripts/revision/l6_dissent.py

1. Representative run (A_5): substantive disagreement among specialists, traced as initial position -> Critic
   comment -> revised position -> final handling (resolved with reasons / retained as uncertainty / disappeared
   without reasons / cannot be judged). Topic positions are located by keyword in the round-1 outputs and checked by
   reading; the judgements below are drafts by Claude for author confirmation.
2. All five revised-protocol runs: number of "Open Issues" items in the PI summaries (reported as issues recorded by
   the PI, not as disagreements), and Critic remarks on inconsistency between specialists, with a category.
Outputs: experiments/runs_rev/results_v1/l6_dissent.json and l6_open_issues.csv.
"""
from __future__ import annotations

import ast
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "experiments" / "runs_rev" / "main_v1"
OUT = ROOT / "experiments" / "runs_rev" / "results_v1"
RUNS = ["A_1", "A_2", "A_3", "A_4", "A_5"]
TOPICS = {
    "genome-wide sequencing": r"whole.genome|genome-wide|\bWGS\b",
    "whole-food animal studies": r"animal (?:stud|feed|test)|feeding stud|whole-food",
    "residual DNA and delivery": r"residual (?:DNA|vector|exogenous)|vector backbone|foreign DNA",
    "untargeted omics": r"\bomics\b|untargeted",
}
CUE = re.compile(r"[^.]*\b(inconsisten\w*|contradict\w*|conflict\w*|disagree\w*|at odds|differs? from|tension)\b[^.]*\.", re.I)
AGENTS = re.compile(r"specialist|contribution|layer|panel|across|between|Genetics|Toxicology|Regulatory|Risk|Bioinformatics")


def category(s: str) -> str:
    if re.search(r"cit|CXG|CAC/GL|Codex|EFSA (?:document|opinion)|title|date|numbering|source|reference|entry|Health Canada", s, re.I):
        return "citation"
    if re.search(r"gloss|term|acronym|explain|phrasing|wording|vocabulary|expanded|named|described", s, re.I):
        return "terminology or readability"
    return "other (read)"


# Draft judgements for A_5 (read from the round texts; author confirmation pending)
A5_TRACE = [
    {"topic": "genome-wide sequencing",
     "round1_positions": "Genetics, Bioinformatics and Regulatory state targeted confirmation by default and genome-wide sequencing when triggers apply (multiplexing, persistent editor expression or DNA vectors, extended tissue culture, repetitive targets, polyploidy). Long-read and trigger provisions are present from round 1.",
     "critic": "R1 notes that the view of genome-wide sequencing as a routine baseline is never engaged and that the argument is one-directional.",
     "later": "R2 Bioinformatics and R6-R7 Risk state the sequence-everything-by-default view and answer it. R4-R5 Bioinformatics adds a passage conceding that prediction-led searches can miss structural or mismatch-tolerant changes.",
     "handling": "No disagreement between specialists. The opposing view was introduced at the Critic's request and answered within one contribution."},
    {"topic": "conditions for widening to genome-wide or omics analysis",
     "round1_positions": "Genetics and Bioinformatics consider widening on process or molecular triggers alone.",
     "critic": "No comment on this difference.",
     "later": "R7 Risk describes widening in a combined-trigger example only when a composition outlier persists.",
     "handling": "Difference in conditions that cannot be judged as a disagreement, because the Risk passage may apply only to its example."},
    {"topic": "whole-food animal studies",
     "round1_positions": "Toxicology, Risk and Regulatory state that such studies are not a default and are considered only for a specific testable hypothesis. Genetics and Bioinformatics do not address them. No specialist proposes them as a default.",
     "critic": "R4 calls the treatment exemplary and requests no opposing view.",
     "later": "Unchanged through R7.",
     "handling": "No disagreement observed."},
    {"topic": "unintended edits after transient delivery",
     "round1_positions": "Specialists treat transient ribonucleoprotein delivery as narrowing the window for unintended edits.",
     "critic": "R1 asks that the view that transient delivery does not fully exclude unintended change be aired.",
     "later": "Aired and answered from R2 (Genetics, Risk).",
     "handling": "No disagreement between specialists. Counter-view introduced at the Critic's request."},
    {"topic": "residual DNA from DNA-based delivery",
     "round1_positions": "Genetics, Bioinformatics, Regulatory and Risk link the depth of characterisation to the presence of foreign DNA and the delivery route.",
     "critic": "R5 asks for a clause on why DNA-free delivery cannot leave a DNA residue.",
     "later": "Added in later rounds.",
     "handling": "No disagreement observed."},
    {"topic": "divergence among regulatory frameworks",
     "round1_positions": "Regulatory asserts convergence among Codex, EFSA, Health Canada and Japan.",
     "critic": "R1 notes that convergence is asserted without examining where the frameworks diverge.",
     "later": "From R2, Regulatory names divergences (comparator breadth, protein-testing conventions, the foreign-DNA trigger in Japan, stability emphasis) and proposes a core-plus-annex dossier. R5-R6 add how the scaffold reads where foreign-DNA presence is decisive.",
     "handling": "Divergence between jurisdictions, not between agents. Retained in the report as a described difference."},
    {"topic": "citation of EFSA documents",
     "round1_positions": "Not applicable.",
     "critic": "R4-R7 note that the EFSA opinion on SDN-1, SDN-2 and ODM is cited with different years and titles across specialists.",
     "later": "Partly aligned and still flagged in R7.",
     "handling": "Inconsistency in citation, not a scientific disagreement. Unresolved at the end."},
]


def main() -> int:
    rows, runs = [], {}
    for run in RUNS:
        conv = json.loads((MAIN / run / "attempt_01" / "conversations.json").read_text(encoding="utf-8"))
        counts, cues = [], []
        for e in conv:
            t = e["pi_summary"]
            oi = t.split("### Open Issues")[1].split("###")[0] if "### Open Issues" in t else ""
            items = [ln[2:].strip() for ln in oi.splitlines() if ln.startswith("- ")]
            counts.append(len(items))
            for it in items:
                rows.append({"run": run, "round": e["round"], "open_issue": it})
            crit = str(e.get("critique_feedback") or e.get("critique", "")) + str(e.get("specialist_feedback", ""))
            for m in CUE.finditer(crit):
                s = m.group(0).strip().replace("\\n", " ")
                if AGENTS.search(s):
                    cues.append({"round": e["round"], "category_by_keyword": category(s), "text": s})
        runs[run] = {"open_issue_items_per_round": counts, "open_issue_items_total": sum(counts),
                     "critic_cross_specialist_inconsistency_remarks": len(cues),
                     "remarks_by_keyword_category": {c: sum(1 for x in cues if x["category_by_keyword"] == c) for c in sorted({x["category_by_keyword"] for x in cues})},
                     "remarks": cues}
    # A_5 round-1 topic positions (keyword hits per specialist)
    conv = json.loads((MAIN / "A_5" / "attempt_01" / "conversations.json").read_text(encoding="utf-8"))
    so = conv[0]["specialist_outputs"]
    so = so if isinstance(so, list) else ast.literal_eval(so)
    hits = {t: {s["role"]: len(re.findall(p, s["output"], re.I)) for s in so} for t, p in TOPICS.items()}
    out = {
        "scope": "revised-protocol runs of main_v1; detailed tracing for the representative run A_5",
        "a5_round1_topic_mentions": hits,
        "a5_trace": A5_TRACE,
        "a5_summary": "No pair of incompatible positions between specialists was identified. On the main "
                      "proportionality questions the specialists who addressed them stated compatible positions from round 1. "
                      "The opposing views observed entered as counter-arguments that a specialist stated and answered after "
                      "the Critic asked for them. One difference in the conditions for widening to genome-wide analysis could "
                      "not be judged. PI open issues combined editorial clean-up with requests on assessment conditions, "
                      "uncertainty handling and further evidence. Absence of observed dissent does not show that conformity "
                      "was absent.",
        "runs": runs,
        "counting_notes": {"open_issue_items": "list entries in the Open Issues section of each round summary, summed over rounds; includes repeated entries and assigned actions, so not a count of distinct issues or of issues left at the end",
                           "critic_remarks": "automatic keyword extraction of candidate remarks on inconsistency between specialists; not validated, includes substantive review requests and praise; not reported as a statistic"},
        "status": "draft judgements by Claude; author confirmation pending",
    }
    (OUT / "l6_dissent.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT / "l6_open_issues.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["run", "round", "open_issue"])
        w.writeheader()
        w.writerows(rows)
    for r, v in runs.items():
        print(r, v["open_issue_items_per_round"], v["open_issue_items_total"], v["remarks_by_keyword_category"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
