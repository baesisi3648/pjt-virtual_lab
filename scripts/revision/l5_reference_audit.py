"""L5 citation audit, part 1: existence of every reference in the five condition-A reports (main_v1).

    python -B scripts/revision/l5_reference_audit.py

Each reference is matched to one document (doc_group) by URL, RAG source name or the rules below, then:
- input_route: direct (retrieved URL or RAG chunk in the snapshot) / indirect (the document is named inside a
  retrieved text) / not in retrieved inputs (cannot be attributed to prior knowledge with certainty);
- exists, with a verification link;
- title: accurate / descriptive label (a description instead of a title) / different title;
- domain note (e.g. human gene therapy).
Being listed is not evidence of use: the pipeline adds retrieved sources to the References (agents/pi.py).
Drafts by Claude, checked with Codex (2026-11-10); no human author has confirmed them (confirmed_by stays empty). Outputs in experiments/runs_rev/results_v1/.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "experiments" / "runs_rev" / "main_v1"
SNAP = ROOT / "experiments" / "runs_rev" / "retrieval_snapshot_v1.json"
OUT = ROOT / "experiments" / "runs_rev" / "results_v1"

# doc_group -> (document, verification link, title as published, domain note)
DOCS = {
    "pmc12660440": ("Spaans et al. 2025, review, PMC12660440", "https://pmc.ncbi.nlm.nih.gov/articles/PMC12660440", "Advancements in genomic crop techniques and", ""),
    "sd_s1871678426001172": ("ScienceDirect S1871678426001172", "https://www.sciencedirect.com/science/article/pii/S1871678426001172", "A Perspective on the New Genomic Techniques Framework", ""),
    "sd_s2666833526001942": ("ScienceDirect S2666833526001942", "https://www.sciencedirect.com/science/article/pii/S2666833526001942", "Safety assessment of emerging food technologies", ""),
    "npj_s44264": ("npj Sustainable Agriculture, s44264-026-00154-9", "https://www.nature.com/articles/s44264-026-00154-9", "How the proposal for a new regulation for new genomic techniques affects", ""),
    "fda_gene_therapy": ("FDA draft guidance: Safety Assessment of Genome Editing in Human Gene Therapy Products Using NGS (retrieved item: FDA press announcement)",
                         "https://www.fda.gov/news-events/press-announcements/fda-issues-draft-guidance-genome-editing-safety-standards-advance-gene-therapy-development",
                         "FDA Issues Draft Guidance on Genome Editing Safety Standards", "human gene-therapy guidance; outside the food-safety domain"),
    "efsa_2021_6314": ("EFSA GMO Panel 2021, overview of opinions on NGT plants, EFSA J 19(4):6314", "https://doi.org/10.2903/j.efsa.2021.6314", "Overview of EFSA and European national authorities", ""),
    "efsa_2025_9566": ("EFSA GMO Panel 2025, NGT animals, EFSA J 23(8):e9566", "https://doi.org/10.2903/j.efsa.2025.9566", "New developments in biotechnology applied to animals", ""),
    "efsa_2026_e240901": ("EFSA 2026 editorial, EFSA J e240901", "https://doi.org/10.2903/j.efsa.2026.e240901", "EFSA needs for scientific excellence and regulatory readiness", ""),
    "efsa_2025_9619": ("EFSA 2025 literature horizon scan, EFSA J 9619", "https://doi.org/10.2903/j.efsa.2025.9619", "Literature horizon scan for new scientific data on plants", ""),
    "pmc13396206": ("Review, PMC13396206", "https://pmc.ncbi.nlm.nih.gov/articles/PMC13396206", "Beyond GMOs: transgene-free gene-edited crops", ""),
    "usda_th2025": ("USDA FAS GAIN report TH2025-0032 (Thailand)", "https://apps.fas.usda.gov/newgainapi/api/Report/DownloadReportByFileName?fileName=Biotechnology+and+Other+New+Production+Technologies+Annual_Bangkok_Thailand_TH2025-0032.pdf",
                    "Biotechnology and Other New Production Technologies Annual", "report on Thailand (US agency)"),
    "efsa_2024_8895": ("EFSA GMO Panel 2024, NGT microorganisms, EFSA J 22(7):e8895", "https://doi.org/10.2903/j.efsa.2024.8895", "New developments in biotechnology applied to microorganisms", ""),
    "codex_cxg45": ("Codex CXG 45-2003", "corpus v1 (FAO PDF)", "Guideline for the Conduct of Food Safety Assessment of Foods Derived from Recombinant-DNA Plants", ""),
    "health_canada": ("Health Canada, Guidelines for the Safety Assessment of Novel Foods (2006; 2022 appendices)", "corpus v1 (canada.ca)", "Guidelines for the Safety Assessment of Novel Foods", ""),
    "japan_mhlw": ("Japan MHLW procedures 2019, amended 2020", "corpus v1 (mhlw.go.jp)", "Food Hygiene Handling Procedures for Food and Additives Derived from Genome Editing Technology", ""),
    "efsa_2019_5708": ("EFSA Scientific Committee 2019, TTC guidance, EFSA J 17(6):5708", "https://doi.org/10.2903/j.efsa.2019.5708", "Guidance on the use of the Threshold of Toxicological Concern approach", ""),
    "efsa_2017_4862": ("EFSA GMO Panel 2017, allergenicity guidance for GM plants, EFSA J 15(6):4862", "https://doi.org/10.2903/j.efsa.2017.4862", "Guidance on allergenicity assessment of genetically modified plants", ""),
    "efsa_2012_2561": ("EFSA GMO Panel 2012, cisgenesis and intragenesis, EFSA J 10(2):2561", "https://doi.org/10.2903/j.efsa.2012.2561", "Scientific opinion addressing the safety assessment of plants developed through cisgenesis and intragenesis", ""),
    "efsa_2011_2150": ("EFSA GMO Panel 2011, GM plant food and feed guidance, EFSA J 9(5):2150", "https://doi.org/10.2903/j.efsa.2011.2150", "Guidance for risk assessment of food and feed from genetically modified plants", ""),
    "codex_cxg44": ("Codex CXG 44-2003", "corpus v1 (FAO PDF)", "Principles for the Risk Analysis of Foods Derived from Modern Biotechnology", ""),
    "eu_com_2023_411": ("European Commission COM(2023) 411", "corpus v1 (EUR-Lex)", "Proposal for a Regulation on plants obtained by certain new genomic techniques", ""),
    "efsa_2020_6299": ("EFSA GMO Panel 2020, applicability of the SDN-3 opinion to SDN-1, SDN-2 and ODM, EFSA J 18(11):6299", "https://doi.org/10.2903/j.efsa.2020.6299",
                       "Applicability of the EFSA Opinion on site-directed nucleases type 3", ""),
}
# identifiers used to find a document inside retrieved text (indirect route)
NAMED = {"efsa_2020_6299": r"6299|SDN-1, SDN-2 and ODM|site-directed nucleases type 1 and 2",
         "efsa_2011_2150": r"2150|food and feed from genetically modified plants",
         "efsa_2012_2561": r"2561|cisgen\w*sis(?: and |/)intragenesis", "efsa_2017_4862": r"4862|allergenicity assessment of genetically modified",
         "efsa_2019_5708": r"5708|Threshold of Toxicological Concern", "codex_cxg44": r"GL ?44|CXG ?44|Principles for the Risk Analysis",
         "eu_com_2023_411": r"COM\(2023\) ?411|2023/0226|Proposal for a Regulation[^.]{0,120}new genomic"}
URL_KEYS = {"PMC12660440": "pmc12660440", "S1871678426001172": "sd_s1871678426001172", "S2666833526001942": "sd_s2666833526001942",
            "s44264-026-00154-9": "npj_s44264", "fda.gov/news-events": "fda_gene_therapy", "2021.6314": "efsa_2021_6314",
            "2025.9566": "efsa_2025_9566", "e240901": "efsa_2026_e240901", "2025.9619": "efsa_2025_9619",
            "PMC13396206": "pmc13396206", "apps.fas.usda.gov": "usda_th2025"}
RULES = [  # (pattern on the reference text, doc_group) for references without a URL
    (r"biotechnology applied to animals|NGT animals", "efsa_2025_9566"),
    (r"allergenicity", "efsa_2017_4862"),
    (r"microorganisms", "efsa_2024_8895"),
    (r"CXG 45|CAC/GL 45|Recombinant.DNA Plants", "codex_cxg45"),
    (r"Health Canada", "health_canada"), (r"MHLW|Ministry of Health, Labour", "japan_mhlw"),
    (r"Threshold of Toxicological Concern", "efsa_2019_5708"),
    (r"cisgenesis", "efsa_2012_2561"), (r"genetically modified plants", "efsa_2011_2150"),
    (r"CAC/GL 44|CXG 44|Principles for the Risk Analysis", "codex_cxg44"),
    (r"European Commission|2023 Proposal", "eu_com_2023_411"),
    (r"SDN.1, SDN.2 and ODM|\(2020\)", "efsa_2020_6299"),
    (r"Overview of EFSA and European national authorities", "efsa_2021_6314"),
    (r"needs for scientific excellence", "efsa_2026_e240901"), (r"horizon scan", "efsa_2025_9619"),
]
RAG_GROUPS = {"efsa_2025_9566", "efsa_2024_8895", "codex_cxg45", "health_canada", "japan_mhlw"}
# title judgements after reading each reference: (run, start of reference) -> (title, reason)
TITLE_OVERRIDES = [
    (("A_5", "FDA. Safety Assessment of Genome Editing in Human Gene Therapy"), "accurate",
     "cites the guidance title; the retrieved item is the press announcement of that guidance"),
    (("A_5", "EFSA (2026). Needs for scientific excellence"), "accurate", "title without the leading word 'EFSA'"),
    (("A_5", "EFSA GMO Panel (2017)"), "different title", "adds 'and microorganisms' to the 2017 GM-plant guidance title"),
    (("A_2", "EFSA GMO Panel (2017)"), "accurate", "title as published"),
    (("A_5", "EFSA GMO Panel (2020)"), "different title", "cited as a 'statement on applicability of existing guidance'"),
    (("A_4", "EFSA 2024 — Overview of developments"), "different title", "paraphrased title of e8895"),
    (("A_5", "Scientific literature on"), "descriptive label", "description in place of the title"),
    (("A_3", "ScienceDirect. Article record"), "descriptive label", "description in place of the title"),
]


def _norm(x: str) -> str:
    for a, b in (("‑", "-"), ("‐", "-"), ("–", "-"), ("—", "-"), ("’", "'")):
        x = x.replace(a, b)
    return re.sub(r"[^a-z0-9]+", " ", x.lower()).strip()


def group_of(ref: str) -> str:
    for key, g in URL_KEYS.items():
        if key in ref:
            return g
    for pat, g in RULES:
        if re.search(pat, ref, re.I):
            return g
    return ""


def route_of(ref: str, g: str, snap_urls: set, retrieved_text: str) -> str:
    url = re.search(r"https?://\S+", ref)
    if url:
        u0 = url.group(0).rstrip(".,")
        if any(u0.split("?")[0] in u or u.split("?")[0] in u0 for u in snap_urls):
            return "direct: retrieved web/EFSA result"
    if g in RAG_GROUPS:
        return "direct: RAG chunk"
    if g == "efsa_2021_6314":
        return "direct: retrieved web/EFSA result"
    if g and g in NAMED and re.search(NAMED[g], retrieved_text, re.I):
        return "indirect: named in a retrieved text"
    return "not in retrieved inputs"


def main() -> int:
    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    retrieved_text = "\n".join(e["result"] for e in snap["entries"].values())
    snap_urls = {u.rstrip(".,") for u in re.findall(r"https?://[^\s)\]>\"']+", retrieved_text)}
    rows = []
    for run in ("A_1", "A_2", "A_3", "A_4", "A_5"):
        t = (MAIN / run / "attempt_01" / "final_report.md").read_text(encoding="utf-8")
        body = re.sub(r"(?ms)^## References.*?(?=^## |\Z)", "", t)
        seen_in_run = Counter()
        for sec in [s for s in re.split(r"(?m)^(?=## )", t) if s.startswith("## References")]:
            for line in sec.splitlines():
                m = re.match(r"^\s*(?:\d+[.)]|[-*])\s+(.+)$", line)
                if not m:
                    continue
                ref = m.group(1).strip()
                g = group_of(ref)
                doc, link, pub_title, domain = DOCS.get(g, ("", "", "", ""))
                route = route_of(ref, g, snap_urls, retrieved_text)
                if re.match(r"^\s*https?://", ref):
                    title = "descriptive label"
                elif pub_title and _norm(pub_title)[:28] in _norm(ref):
                    title = "accurate"
                else:
                    title = "different title"
                reason = ""
                for (orun, start), tt, why in TITLE_OVERRIDES:
                    if run == orun and ref.startswith(start):
                        title, reason = tt, why
                seen_in_run[g] += 1
                in_body = bool(g) and bool(pub_title) and _norm(pub_title)[:25] in _norm(body)
                rows.append({"run": run, "reference": ref, "doc_group": g or "UNMATCHED", "identified_document": doc,
                             "input_route": route, "exists": "yes" if g else "cannot verify", "verification": link,
                             "title": title, "title_note": reason, "domain_note": domain,
                             "duplicate_in_run": "yes" if seen_in_run[g] > 1 else "",
                             "title_found_in_body": "yes" if in_body else "no",
                             "draft_by": "Claude", "confirmed_by": ""})
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "l5_reference_audit.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    runs = ("A_1", "A_2", "A_3", "A_4", "A_5")
    unique = {}
    for x in rows:
        unique.setdefault(x["doc_group"], x)
    summary = {
        "reference_entries": len(rows),
        "unique_documents": len(unique),
        "unique_documents_per_report": {r: len({x["doc_group"] for x in rows if x["run"] == r}) for r in runs},
        "duplicate_entries_within_reports": sum(1 for x in rows if x["duplicate_in_run"]),
        "entries_by_input_route": dict(Counter(x["input_route"] for x in rows)),
        "unique_documents_by_input_route": dict(Counter(x["input_route"] for x in unique.values())),
        "exists": dict(Counter(x["exists"] for x in rows)),
        "title": dict(Counter(x["title"] for x in rows)),
        "domain_notes": dict(Counter(x["domain_note"] for x in rows if x["domain_note"])),
        "reports_listing_fda_gene_therapy": sorted({x["run"] for x in rows if x["doc_group"] == "fda_gene_therapy"}),
        "note": "Listing is not evidence of use: retrieved sources are added to the References by the pipeline. "
                "'not in retrieved inputs' does not establish generation from prior knowledge. "
                "title_found_in_body is a rough text check, not a claim-citation link.",
        "status": "draft judgements by Claude, checked with Codex; no human author confirmation",
    }
    (OUT / "l5_reference_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for x in rows:
        if x["doc_group"] == "UNMATCHED":
            print("UNMATCHED", x["run"], x["reference"][:120])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
