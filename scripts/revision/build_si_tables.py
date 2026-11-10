"""Draft Supplementary Information tables for the revision, generated from the result files (no hand-copied numbers).

    python -B scripts/revision/build_si_tables.py [--out reference/revision/manuscript_drafts/05_SI_tables.md]

Note S1 research agenda; Table S7 Critic rubric and scoring instructions; Table S8 corpus and retrieved sources;
Table S9 output volume per agent; Table S10 reference audit (draft, author confirmation pending);
Table S11 prompt changes from the original submission; Table S12 Critic scores by round and protocol.
Table numbers are provisional (S1-S6 are the existing tables of the original submission).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "experiments" / "runs_rev"
RES = RUNS / "results_v1"


def rows(p: Path) -> list[dict]:
    with p.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def table(head: list[str], body: list[list]) -> str:
    esc = lambda x: str(x).replace("|", "/").replace("\n", " ")
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(esc(c) for c in r) + " |" for r in body]
    return "\n".join(out)


def note_s1() -> str:
    t = (ROOT / "prompts_A" / "data" / "research_agenda.md").read_text(encoding="utf-8")
    t = t.split("## Mapping of Questions")[0].strip()
    t = re.sub(r"^\[(.*)\]$", r"\1", t, flags=re.M)
    t = t.replace("## ", "").replace("### ", "")
    return "## Supplementary Note S1. Research agenda given to all agents\n\nFull text as injected into the agent prompts (identical under both scoring protocols).\n\n" + "\n\n".join(
        p.strip() for p in t.split("\n\n") if p.strip())


def table_s7() -> str:
    rub = (ROOT / "prompts_A" / "data" / "critique_rubric.md").read_text(encoding="utf-8")
    axes = re.findall(r"^\d\. ([A-Za-z ]+?) — 1–5\n((?:\s+\[\d\].*\n?)+)", rub, flags=re.M)
    body = []
    for name, block in axes:
        for lvl, desc in re.findall(r"\[(\d)\]\s*(.+)", block):
            body.append([name.strip() if lvl == "1" else "", lvl, desc.strip()])
    ded = re.search(r"\[Deductions\]\n((?:- .*\n?)+)", rub).group(1).strip().splitlines()
    thr = re.search(r"\[Approval Threshold\]\n(.+?)\n\n", rub, flags=re.S).group(1).strip()
    parts = ["## Supplementary Table S7. Critic rubric and scoring instructions",
             "**(a) Score definitions.** Identical under both scoring protocols in the revision.",
             table(["Dimension", "Score", "Definition"], body),
             "Deductions: " + " ".join(d.lstrip("- ") for d in ded),
             "Approval threshold: " + thr,
             "**(b) Scoring instructions by protocol.**"]
    instr = [
        ["Previous numerical scores given to the Critic", "Yes", "Yes", "No"],
        ["Score-comparison rule (raise when a flagged weakness is resolved or strengths persist with new improvements; lower only for an explicit reason)", "Yes (described as non-decreasing scoring in the original manuscript)", "Yes", "No. Score each contribution on its current content alone"],
        ["Round 1 limit", "No dimension above 4; be especially strict", "Same", "None"],
        ["Award 5 only when no further improvement is possible on that dimension", "Yes", "Yes", "Yes"],
        ["Third item of the per-specialist feedback", "Concrete actions required to reach 5/5", "Same", "Concrete actions to address the remaining weaknesses; no scores, score levels or score targets in the feedback"],
        ["Definition of proportionality in the Critic prompt", "Avoidance of over-regulation", "Data requirements commensurate with the identified hazards (neither excessive nor insufficient)", "Same as comparison protocol"],
        ["Proportionality levels 1 and 2 of the rubric", "Penalise excessive data requirements only", "Penalise excessive or insufficient requirements and unjustified omissions", "Same as comparison protocol"],
        ["Early termination", "All dimensions 5 for all specialists", "Same, or seven rounds", "Same, or seven rounds"],
        ["Critic model", "GPT-5, as for the other agents (response identifier not recorded)", "Claude Opus 5 (claude-opus-5)", "Claude Opus 5 (claude-opus-5)"],
    ]
    parts.append(table(["Element", "Original submission", "Comparison protocol", "Revised protocol"], instr))
    return "\n\n".join(parts)


def table_s8() -> str:
    corpus = rows(RUNS / "results" / "corpus_v1" / "corpus_v1_table.csv")
    src = rows(RUNS / "results" / "corpus_v1" / "retrieval_sources.csv")
    delivered = {}
    for r in src:
        if r["kind"] == "rag":
            delivered[r["source"]] = r["page"]
    man = {d["id"]: d for d in json.loads((RUNS / "corpus_v1" / "corpus_manifest.json").read_text(encoding="utf-8"))["documents"]}
    body = []
    for r in corpus:
        source = man[r["doc_id"]]["source"]
        loc = delivered.get(source, "")
        body.append([r["citation"], r["agency"], r["jurisdiction"], r["year"], r["scope"], r["chunks"],
                     f"Yes ({loc})" if r["given_to_agents"] == "yes" else "No"])
    tot = sum(int(r["chunks"]) for r in corpus)
    juris = Counter()
    for r in corpus:
        juris[r["jurisdiction"]] += int(r["chunks"])
    urls = defaultdict(list)
    for r in src:
        if r["kind"] != "rag":
            u = r["source"].replace("/doi/abs/", "/doi/")
            urls[u].append(r["retrieval_key"])
    web = [[u, ", ".join(sorted(set(k)))] for u, k in urls.items()]
    used = set()
    for meta in (RUNS / "main_v1").glob("*/attempt_01/meta.json"):
        used |= set(json.loads(meta.read_text(encoding="utf-8"))["retrieval"]["keys_used"])
    snap_keys = set(json.loads((RUNS / "retrieval_snapshot_v1.json").read_text(encoding="utf-8"))["entries"])
    unused = sorted(snap_keys - used)
    used = sorted(used)
    return "\n\n".join([
        "## Supplementary Table S8. RAG corpus and retrieved sources",
        f"**(a) RAG corpus (19 documents, {tot:,} chunks).** Chunks of up to 1,000 characters per page or section. "
        "Delivered = the document contributed one of the five chunks given to all specialists in round 1 (location in parentheses). "
        "Chunks by jurisdiction: " + ", ".join(f"{k} {v:,} ({v / tot:.0%})" for k, v in juris.most_common()) + ".",
        table(["Document", "Issuing body", "Jurisdiction", "Year", "Scope", "Chunks", "Delivered"], body),
        f"**(b) Web and EFSA Journal results in the fixed retrieval inputs ({len(web)} distinct URLs).** "
        "Recorded once from live searches and replayed in every run. Retrieval calls used in the main runs: " + ", ".join(used) + "."
        + (" Recorded but not used: " + ", ".join(unused) + " (the PI reused the specialists' EFSA results)." if unused else ""),
        table(["URL", "Retrieval call"], web),
    ])


def table_s9() -> str:
    data = rows(RES / "output_stats.csv")
    order = ["PI", "Critic", "Genetics", "Toxicology", "Regulatory", "Risk", "Bioinformatics"]
    def key(agent):
        a = agent.replace("Genomics", "Genetics")
        return next((o for o in order if a.startswith(o)), agent)
    by = defaultdict(dict)
    for r in data:
        by[r["run"]][key(r["agent"])] = (int(r["turns"]), int(r["chars"]))
    body = [[run] + [f"{by[run][o][0]} / {by[run][o][1]:,}" if o in by[run] else "" for o in order] for run in sorted(by)]
    definition = json.loads((RES / "output_stats_definition.json").read_text(encoding="utf-8"))["definition"]
    definition = re.sub(r"\s+", " ", definition.replace("Definition:", "")).strip()
    return "\n\n".join(["## Supplementary Table S9. Output volume per agent (turns / characters)",
                        "Definition: " + definition + " The molecular specialist was labelled Genomics Specialist in three runs.",
                        table(["Run", "PI", "Critic", "Genetics", "Toxicology", "Regulatory", "Risk", "Bioinformatics"], body)])


def table_s10() -> str:
    data = rows(RES / "l5_reference_audit.csv")
    g = defaultdict(list)
    for r in data:
        g[r["doc_group"]].append(r)
    body = []
    for k, rs in sorted(g.items(), key=lambda kv: (-len({x["run"] for x in kv[1]}), kv[0])):
        titles = Counter(x["title"] for x in rs)
        body.append([rs[0]["identified_document"], rs[0]["input_route"], rs[0]["exists"],
                     len({x["run"] for x in rs}), len(rs), "; ".join(f"{t} {n}" for t, n in titles.most_common()),
                     rs[0]["domain_note"]])
    return "\n\n".join(["## Supplementary Table S10. Reference audit of the five revised-protocol reports",
                        "**Drafted with Claude and checked with Codex; no human author confirmation.** One row per distinct document. Reports = number of reports listing it; "
                        "entries = number of reference entries. Input route: direct (delivered by retrieval), indirect (named within a retrieved text), "
                        "or not in retrieved inputs. The entry-level audit is in l5_reference_audit.csv.",
                        table(["Document", "Input route", "Exists", "Reports", "Entries", "Title as given", "Note"], body)])


DESC = {
    "P1-constraint": ("run input (constraint sentence)", "\"Avoid the GMO-style blanket strictness; require additional data only when there is a clear scientific basis. Be proportionate and rational.\"",
                      "\"Be proportionate and science-based. Require additional data only when there is a scientific basis, and justify any decision to omit an assessment. Avoid both disproportionate data requirements and unsupported waivers.\""),
    "P2-rubric-1": ("rubric, proportionality level 1", "Excessively stringent data requirements; reads like a detailed regulatory protocol.",
                    "Data requirements are either excessively stringent or insufficient for the identified hazards; reads like a detailed regulatory protocol or omits assessments without justification."),
    "P2-rubric-2": ("rubric, proportionality level 2", "Some sections are over-prescriptive or burdened with unnecessary technical detail.",
                    "Some sections are over-prescriptive, burdened with unnecessary technical detail, or omit an assessment without a stated scientific rationale."),
    "P2-critic-axis": ("Critic prompt, proportionality", "avoidance of over-regulation", "data requirements commensurate with the identified hazards (neither excessive nor insufficient)"),
    "P3-team-decision-language": ("team decision prompt", "Example of a forbidden non-English role name", "Instruction to translate non-English role names"),
    "P3-team-decision-example": ("team decision prompt", "Example role names (Molecular Genetics, Toxicology, Regulatory Science Specialist)", "Format only: '<Discipline> Specialist'"),
    "P3-team-selection-example": ("team selection prompt", "Example role names (the five specialists of the original panel)", "Format only: '<Discipline> Specialist'"),
    "P3-role-clustering-example": ("role clustering prompt", "Example role names (the five specialists of the original panel)", "Format only: '<Discipline> Specialist'"),
    "P4-report-terminal-node": ("report template, decision-tree rule 3", "All paths must converge on a single \"Assessment complete\" terminal node.",
                                "All paths end at a single \"Assessment complete\" node, which does not by itself indicate that safety has been established. Paths with insufficient evidence or unresolved uncertainty pass first through a node such as \"Additional data required\" or \"Decision deferred pending further data\"."),
    "P4-tone-guide-exception": ("tone guide", "Prohibition of normative phrasing without exception", "Exception for wording that flags uncertainty, requests additional data, or defers a decision"),
    "P5-methods-critic": ("report template, Methods text", "Critic described as providing independent quantitative scrutiny", "Critic described as a separate agent on a model of a different family"),
    "P5-methods-web": ("report template, Methods text", "Live web search", "Web search recorded once and replayed"),
    "P5-methods-trials": ("report template, Methods text", "All ten team trials succeeded", "Ten valid trials obtained, failed attempts repeated"),
    "A-critic-scoring-rules": ("Critic prompt (revised protocol only)", "Score-comparison rule against previous scores", "Score each contribution on its current content alone"),
    "A-critic-round1-cap": ("Critic prompt (revised protocol only)", "Round 1: be especially strict, no dimension above 4", "Removed"),
    "A-critic-feedback-without-scores": ("Critic prompt (revised protocol only)", "Feedback item: concrete actions required to reach 5/5", "Concrete actions to address the remaining weaknesses; no scores or score targets in feedback"),
}


def table_s11() -> str:
    m = json.loads((RUNS / "prompt_sets" / "prompt_sets_manifest.json").read_text(encoding="utf-8"))
    sets = {s["condition"]: {c["change_id"] for c in s["changes"]} for s in m["sets"]}
    ids = ["P1-constraint"] + [c["change_id"] for s in m["sets"] if s["condition"] == "A" for c in s["changes"]]
    body = []
    for cid in ids:
        where, old, new = DESC[cid]
        applies = "Both" if cid == "P1-constraint" or (cid in sets["A"] and cid in sets["B"]) else "Revised only"
        body.append([cid, where, old, new, applies])
    unused = ", ".join(m["excluded_unused_data_files"])
    return "\n\n".join(["## Supplementary Table S11. Changes to the prompts and run inputs relative to the original submission",
                        "The full prompt sets of both protocols and the patches against the original prompts are in the repository. "
                        f"Three data files of the original code ({unused}) were read at start-up but never given to any agent and are not part of the prompt sets.",
                        table(["Change", "Location", "Original submission", "Revision", "Protocols"], body)])


def table_s12() -> str:
    data = rows(RES / "critic_by_round.csv")
    g = defaultdict(dict)
    for r in data:
        g[(r["condition"], int(r["round"]))][r["axis"]] = (float(r["mean"]), float(r["sd_population"]), int(r["n_runs"]))
    name = {"A": "Revised", "B": "Comparison"}
    axes = ["evidence", "universality", "proportionality", "readability"]
    body = []
    for (c, rd), ax in sorted(g.items()):
        body.append([name[c], rd, ax[axes[0]][2]] + [f"{ax[a][0]:.2f} ± {ax[a][1]:.2f}" for a in axes])
    return "\n\n".join(["## Supplementary Table S12. Critic scores by round and protocol",
                        "Mean ± population SD across runs of the run-level mean over the five specialists. n = runs that reached the round "
                        "(comparison-protocol runs stopped at rounds 3 or 4 when every score was 5). Per-round, per-specialist scores of every run are in the repository.",
                        table(["Protocol", "Round", "n", "Evidence", "Universality", "Proportionality", "Readability"], body)])


def table_s13() -> str:
    d = json.loads((RES / "l6_dissent.json").read_text(encoding="utf-8"))
    body = [[t["topic"], t["round1_positions"], t["critic"], t["later"], t["handling"]] for t in d["a5_trace"]]
    runs = [[r, " / ".join(map(str, v["open_issue_items_per_round"])), v["open_issue_items_total"]]
            for r, v in d["runs"].items()]
    return "\n\n".join(["## Supplementary Table S13. Disagreement among agents",
                        "**Drafted with Claude; the summary was reviewed by the two external experts.** (a) Main topics traced across the seven rounds of the representative run.",
                        table(["Topic", "Round 1 positions", "Critic", "Later rounds", "Handling"], body),
                        "(b) Entries in the Open Issues lists of the PI round summaries, summed over rounds, by revised-protocol run. Entries repeat across "
                        "rounds and include assigned actions, so they are not counts of distinct issues or of disagreements.",
                        table(["Run", "Open-issue entries per round", "Total entries"], runs)])


def table_s14() -> str:
    """Conformity by guidance element (primary judge, ten reports)."""
    s = json.loads((RES / "l3_summary.json").read_text(encoding="utf-8"))
    crit = json.loads((ROOT / "experiments" / "runs_rev" / "analysis_criteria.json").read_text(encoding="utf-8"))
    names = {i["id"]: i["item_en"] for i in crit["items"]}
    body = []
    for k, v in s["per_item"].items():
        c = v["counts"]
        body.append([k, names[k], "yes" if v["critical"] else "", c["일치"], c["부분"], c["누락"], c["상충"], f"{v['conformity'] * 100:.0f}%", f"{v['strict'] * 100:.0f}%"])
    return "\n\n".join(["## Supplementary Table S14. Conformity with guidance by element",
                        "Primary judge, ten reports. Weighted conformity counts partial as 0.5, and strict conformity counts present only.",
                        table(["Element", "Assessment element", "Critical", "Present", "Partial", "Absent", "Conflict", "Weighted", "Strict"], body)])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reference/revision/manuscript_drafts/05_SI_tables.md")
    a = ap.parse_args()
    doc = "\n\n".join(["# Supplementary Information (revision draft): new items",
                       "Generated by scripts/revision/build_si_tables.py from the result files. Table numbers are provisional.",
                       note_s1(), table_s7(), table_s8(), table_s9(), table_s10(), table_s11(), table_s12(), table_s13(), table_s14()])
    out = ROOT / a.out
    out.write_text(doc + "\n", encoding="utf-8")
    print("wrote", out, len(doc), "chars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
