"""L3 aggregation from the returned judging sheets (rules: analysis_criteria.json v1.0).

Reports stay under their anonymous IDs. The per-condition split reads the
blinding key and runs only with --unblind, after every judgement is final.
Usage: python scripts/revision/l3_aggregate.py [--unblind]
"""
import collections as C
import glob
import json
import statistics as st
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
IN = ROOT / "reference" / "판정시트"
SENT = ROOT / "reference" / "revision" / "judging_v1"
OUT = ROOT / "experiments" / "runs_rev" / "results_v1"
STATUS = ["일치", "부분", "누락", "상충", "범위 밖"]
FIXED_PRIMARY = ["보고서 ID", "항목 ID", "중대 항목", "판단 지점", "양식 노드"]


def rows(path, sheet):
    ws = openpyxl.load_workbook(path, data_only=True)[sheet]
    r = list(ws.iter_rows(values_only=True))
    return [dict(zip(r[0], x)) for x in r[1:] if x[0] is not None]


def rate(cnt):
    den = sum(cnt[s] for s in STATUS if s != "범위 밖")
    return {
        "n": den,
        "counts": {s: cnt[s] for s in STATUS},
        "conformity": (cnt["일치"] + 0.5 * cnt["부분"]) / den,
        "strict": cnt["일치"] / den,
    }


def kappa(pairs):
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    ma, mb = C.Counter(a for a, _ in pairs), C.Counter(b for _, b in pairs)
    pe = sum(ma[s] * mb[s] for s in STATUS) / n**2
    return {"n": n, "agree": sum(a == b for a, b in pairs), "percent": po, "kappa": (po - pe) / (1 - pe)}


def main():
    prim = rows(next(IN.glob("주판정*.xlsx")), "L3 판정")
    sec = rows(next(IN.glob("2차판정*.xlsx")), "L3 판정")
    sent = rows(SENT / "primary_judge_sheet.xlsx", "L3 판정")
    # returned fixed columns must equal what was sent
    changed = [(a["보고서 ID"], a["항목 ID"]) for a, b in zip(prim, sent)
               if any(a[k] != b[k] for k in FIXED_PRIMARY)]
    bad = [d for d in prim + sec if d["반영 상태"] not in STATUS]
    keys = [(d["보고서 ID"], d["항목 ID"]) for d in prim]
    keys2 = [(d["보고서 ID"], d["항목 ID"]) for d in sec]
    assert len(prim) == 300 and len(sec) == 90 and not changed and not bad, (changed, bad)
    assert len(set(keys)) == 300 and len(set(keys2)) == 90 and set(keys2) <= set(keys)

    wb = openpyxl.load_workbook(next(IN.glob("주판정*.xlsx")), data_only=True)
    filled = lambda name: sum(1 for r in wb[name].iter_rows(min_row=2, values_only=True) if any(v not in (None, "") for v in r))
    l4 = rows(next(IN.glob("주판정*.xlsx")), "L4 구조")
    res = {"completeness": {
        "status_cells": sum(1 for d in prim if d["반영 상태"]),
        "cause_cells": sum(1 for d in prim for k in d if k.startswith("원인") and d[k]),
        "location_cells": sum(1 for d in prim if d["보고서 근거 위치"]),
        "critical_case_rows": filled("중대 사례"),
        "ai_addition_rows": filled("AI 추가 제안"),
        "normalisation_rows": filled("정규화 변환표"),
        "l4_rows_judged": sum(1 for d in l4 if d["유무"] or d["적용"]),
        "l4_rows": len(l4),
    }}
    res["overall"] = rate(C.Counter(d["반영 상태"] for d in prim))
    per = {r: rate(C.Counter(d["반영 상태"] for d in prim if d["보고서 ID"] == r))
           for r in sorted({d["보고서 ID"] for d in prim})}
    res["per_report"] = per
    res["per_report_conformity"] = {
        "median": st.median(v["conformity"] for v in per.values()),
        "min": min(v["conformity"] for v in per.values()),
        "max": max(v["conformity"] for v in per.values()),
    }
    res["per_item"] = {}
    for it in sorted({d["항목 ID"] for d in prim}):
        g = [d for d in prim if d["항목 ID"] == it]
        res["per_item"][it] = {"area": g[0]["영역"], "critical": g[0]["중대 항목"] == "예",
                               **rate(C.Counter(d["반영 상태"] for d in g))}
    res["critical_omission_or_conflict"] = [
        {"report": d["보고서 ID"], "item": d["항목 ID"], "status": d["반영 상태"]}
        for d in prim if d["중대 항목"] == "예" and d["반영 상태"] in ("누락", "상충")]
    crit = json.loads((ROOT / "experiments" / "runs_rev" / "analysis_criteria.json").read_text(encoding="utf-8"))
    template = {i["id"] for i in crit["items"] if i.get("template_overlap")}
    res["sensitivity_excluding_template_items"] = {
        "note": "sensitivity only; not a causal correction for template influence",
        "items_excluded": sorted(template),
        **rate(C.Counter(d["반영 상태"] for d in prim if d["항목 ID"] not in template)),
    }

    m = {(d["보고서 ID"], d["항목 ID"]): d for d in prim}
    pairs = [(m[(d["보고서 ID"], d["항목 ID"])]["반영 상태"], d["반영 상태"]) for d in sec]
    ag = {"all": kappa(pairs), "note": "three-report sample between authors; not external validation"}
    for r in sorted({d["보고서 ID"] for d in sec}):
        ag[r] = kappa([(m[(d["보고서 ID"], d["항목 ID"])]["반영 상태"], d["반영 상태"])
                       for d in sec if d["보고서 ID"] == r])
    conf = C.Counter(pairs)
    ag["confusion_primary_by_second"] = {a: {b: conf[(a, b)] for b in STATUS[:4]} for a in STATUS[:4]}
    ag["disagreements"] = [
        {"report": d["보고서 ID"], "item": d["항목 ID"], "critical": m[(d["보고서 ID"], d["항목 ID"])]["중대 항목"] == "예",
         "primary": m[(d["보고서 ID"], d["항목 ID"])]["반영 상태"], "second": d["반영 상태"]}
        for d in sec if m[(d["보고서 ID"], d["항목 ID"])]["반영 상태"] != d["반영 상태"]]
    res["agreement"] = ag

    if "--unblind" in sys.argv:
        key = json.loads((SENT / "blinding_key.json").read_text(encoding="utf-8"))["key"]
        inv = {v: k for k, v in key.items()}
        res["per_condition"] = {}
        for c in "AB":
            v = [per[r]["conformity"] for r in per if inv[r][0] == c]
            s = [per[r]["strict"] for r in per if inv[r][0] == c]
            res["per_condition"][c] = {"conformity_median": st.median(v), "range": [min(v), max(v)],
                                       "strict_median": st.median(s), "strict_range": [min(s), max(s)]}
    OUT.mkdir(exist_ok=True)
    (OUT / "l3_summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    r = main()
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({k: r[k] for k in ("completeness", "overall", "per_report_conformity", "sensitivity_excluding_template_items")}, ensure_ascii=False))
    for k, v in r["per_report"].items():
        print(k, v["conformity"], v["strict"])
    for k, v in r["per_item"].items():
        print(k, v["area"], "C" if v["critical"] else "", v["conformity"], v["counts"])
    a = r["agreement"]
    print(a["all"], a["R03"], a["R08"], a["R10"], a["confusion_primary_by_second"])
    print("critical disagreements", sum(d["critical"] for d in a["disagreements"]), len(a["disagreements"]))
