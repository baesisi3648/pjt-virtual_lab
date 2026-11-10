"""Decision-tree structure indices from the blinded reports. Deterministic: no LLM.

Replaces the planned field-level coding of the 17 decision points (analysis_criteria.json
L4_structure), which was not completed. Two parts:
1. content-neutral counts from the Mermaid source (no keyword rules on the 17 points);
2. between-report agreement of the primary judge's L3 status on the 17 decision-point items.
Exact-label overlap measures shared wording, not semantic or structural equivalence.
The per-condition split reads the blinding key and runs only with --unblind.
Usage: python scripts/revision/l4_structure_metrics.py [--unblind]
"""
import collections as C
import itertools as IT
import json
import re
import statistics as st
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).parent))
import l4_extract as L  # noqa: E402

CRITERIA = L.ROOT / "experiments" / "runs_rev" / "analysis_criteria.json"
OUT = L.ROOT / "experiments" / "runs_rev" / "results_v1" / "l4_structure.json"
SENT = L.ROOT / "reference" / "revision" / "judging_v1"
PRIMARY = L.ROOT / "reference" / "판정시트"
IDS = [f"R{i:02d}" for i in range(1, 11)]
ADDITIONAL = r"additional data|further data|more data|request.{0,20}data|defer"
COUNTS = ["diagrams", "nodes", "arrows", "decision_nodes", "terminal_nodes", "additional_data_nodes", "additional_data_to_terminal_only"]


def key(s):
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s.lower()).split())


def structure(rid):
    _, ts = L.report_trees(rid)
    c = C.Counter(diagrams=len(ts))
    labels, triples = set(), set()
    for _, nodes, edges in ts:
        out = C.Counter(s for s, _, _ in edges)
        ids = set(nodes) | {x for s, _, t in edges for x in (s, t)}
        c["nodes"] += len(ids)
        c["arrows"] += len(edges)
        c["decision_nodes"] += sum(v >= 2 for v in out.values())
        c["terminal_nodes"] += sum(i not in out for i in ids)
        for i, label in nodes.items():
            labels.add(key(label))
            if re.search(ADDITIONAL, label, re.I):
                c["additional_data_nodes"] += 1
                if i in out and all(t not in out for s, _, t in edges if s == i):
                    c["additional_data_to_terminal_only"] += 1
        triples |= {(key(nodes.get(s, s)), key(b), key(nodes.get(t, t))) for s, b, t in edges}
    return {k: c[k] for k in COUNTS}, labels, triples


def summary(x):
    return {"mean": sum(x) / len(x), "min": min(x), "max": max(x), "n_pairs": len(x)}


def jaccard(a, b):
    return len(a & b) / len(a | b)


def analyse(ids, per, lab, tri, status, points, overlap):
    pairs = list(IT.combinations(ids, 2))
    agree = {cb: [status[a, cb] == status[b, cb] for a, b in pairs] for cb in points}
    pair_all = [sum(agree[cb][i] for cb in points) / len(points) for i in range(len(pairs))]
    model = [cb for cb in points if not overlap[cb]]
    pair_model = [sum(agree[cb][i] for cb in model) / len(model) for i in range(len(pairs))]
    return {
        "counts": {k: {"median": st.median(per[r][k] for r in ids), "min": min(per[r][k] for r in ids), "max": max(per[r][k] for r in ids)} for k in COUNTS},
        "node_label_jaccard": summary([jaccard(lab[a], lab[b]) for a, b in pairs]),
        "arrow_triple_jaccard": summary([jaccard(tri[a], tri[b]) for a, b in pairs]),
        "l3_status_agreement_17_points": summary(pair_all),
        "l3_status_agreement_excluding_template_points": dict(summary(pair_model), n_points=len(model)),
        "modal_status_share_by_point": {cb: C.Counter(status[r, cb] for r in ids).most_common(1)[0][1] / len(ids) for cb in points},
    }


def main():
    items = json.loads(CRITERIA.read_text(encoding="utf-8"))["items"]
    points = [i["id"] for i in items if i.get("decision_point")]
    overlap = {i["id"]: i.get("template_overlap") for i in items}
    ws = openpyxl.load_workbook(next(PRIMARY.glob("주판정*.xlsx")), data_only=True)["L3 판정"]
    rows = list(ws.iter_rows(values_only=True))
    d = [dict(zip(rows[0], r)) for r in rows[1:] if r[0] is not None]
    status = {(x["보고서 ID"], x["항목 ID"]): x["반영 상태"] for x in d}
    assert len(points) == 17 and len(status) == 300
    per, lab, tri = {}, {}, {}
    for r in IDS:
        per[r], lab[r], tri[r] = structure(r)
    res = {"note": "Exact-label overlap reflects shared wording only. L3 status agreement compares human judgements of guideline conformity, not branch structure. Pooled values are over 45 anonymous pairs and are not a condition comparison.",
           "per_report": per, "pooled": analyse(IDS, per, lab, tri, status, points, overlap)}
    if "--unblind" in sys.argv:
        key_map = json.loads((SENT / "blinding_key.json").read_text(encoding="utf-8"))["key"]
        inv = {v: k for k, v in key_map.items()}
        res["per_condition"] = {c: analyse([r for r in IDS if inv[r][0] == c], per, lab, tri, status, points, overlap) for c in "AB"}
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    r = main()["pooled"]
    print(json.dumps(r, ensure_ascii=False, indent=1))
