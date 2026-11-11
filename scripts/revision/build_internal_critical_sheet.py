"""Internal critical-case check sheet (replaces the follow-up request to the primary judge).

Candidate passages were located by Codex (read-only) and spot-checked by Claude against the reports.
The human reviewer (S.B.) makes every judgement in the yellow cells. Anonymous report IDs only.

    python -B scripts/revision/build_internal_critical_sheet.py
"""
import sys
from pathlib import Path

import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[2]
PRIMARY = next((ROOT / "reference" / "판정시트").glob("주판정*.xlsx"))
OUT = ROOT / "reference" / "revision" / "packages_v1" / "6_내부_중대사례검토" / "중대사례_내부확인표.xlsx"
INPUT = PatternFill("solid", fgColor="FFF4CC")
WRAP = Alignment(wrap_text=True, vertical="top")

# (report, type, CB, quote, location) located by Codex, 2026-11-11
CLOSURE = [
    ("R01", "CB11", "Any decision-relevant uncertainty remains?", "Integrated Decision Tree: C8 Yes → AX → AC (완료)"),
    ("R02", "CB19", "Uncertainty resolved?", "Integrated Decision Tree: E7 No → E8 'Additional data required' → Z (완료)"),
    ("R03", "CB22", "Signals outside normal comparator ranges?", "Integrated Decision Tree: C3 Yes → C5 → Z (완료)"),
    ("R04", "CB19", "Uncertainty closed by weight-of-evidence?", "Integrated Decision Tree: E10 No → E11 → Z (완료)"),
    ("R05", "CB20", "Signals of concern persist after weight-of-evidence", "Integrated Decision Tree: D2 Yes → D3 → Z (완료)"),
    ("R06", "CB19", "Uncertainty resolved?", "Integrated Decision Tree: D4 No → D5 → Z (완료)"),
    ("R07", "CB03", "Residual DNA detected?", "Integrated Decision Tree: D2 Yes → D3 'Decision deferred pending further data' → Z (완료)"),
    ("R08", "CB19", "Decision-relevant uncertainty remains?", "Integrated Decision Tree: O Yes → P → Q (완료)"),
    ("R09", "CB19·CB22", "Any unresolved protein or composition concerns?", "Integrated Decision Tree: E4 Yes → X1 → Z (완료)"),
    ("R10", "CB22", "Any unexplained deviations from expectations?", "SDN-3 Decision Tree: H3 Yes → I3 'Decision deferred pending further data' → Z3 (완료)"),
]
OMISSION = [
    ("R01", "CB28", "Integrate molecular, comparative, toxicology, allergenicity, and nutrition strands", "Core Question 5, Step 7"),
    ("R02", "CB04", "SDN-3 (site-directed nuclease class 3; insertion of longer DNA): may express a new or modified protein", "Core Question 1, SDN-3"),
    ("R02", "CB06", "a simple boundary scan addresses this point.", "Core Question 2, SDN-3 삽입부 평가"),
    ("R03", "CB20", "In silico similarity screens to curated toxin and allergen datasets", "첫 번째 Core Question 5, Step 5"),
    ("R04", "CB04", "SDN-3 follows the established recombinant-DNA path without modification.", "두 번째 Core Question 3"),
    ("R04", "CB20", "targeted confirmatory work is considered in light of actual exposure and processing.", "첫 번째 Core Question 4"),
    ("R05", "CB06", "Structural rearrangements at or near the insertion site receive proportionate attention", "Core Question 2, SDN-3 삽입부 평가"),
    ("R06", "CB20", "in silico similarity to allergen/toxin databases; in vitro digestion in relevant food matrices; ...", "Core Question 5, Step 6"),
    ("R07", "CB28", "focus any new studies on credible hazard-exposure routes.", "Core Question 5, Step 8"),
    ("R08", "CB04", "SDN-3 (insertion of a larger DNA fragment at a defined site).", "첫 번째 Core Question 1, 첫 문단"),
    ("R08", "CB20", "bioinformatics, source history, digestibility/stability, and exposure", "두 번째 Core Question 5, 단계 5"),
    ("R09", "CB20", "Techniques include sequence homology tools, simulated digestion assays, Western blotting, and targeted ELISA ...", "Core Question 5, 단계 8"),
    ("R10", "CB20", "Illustrative tools include bioinformatic homology searches, in vitro digestibility assays, Western blot, ...", "첫 번째 Core Question 5, 단계 7"),
]
CONFLICT = [
    ("R03", "For SDN-3, established recombinant-DNA practice applies: characterise the inserted sequence, its junctions to the genome ... and its genomic context ...", "첫 번째 Core Question 1, 두 번째 문단"),
    ("R05", "SDN-3 follows the recombinant-DNA path with insertion/junction characterisation and any new protein.", "Core Question 5, Step 2"),
    ("R06", "SDN-3 aligns with established insert assessments used for recombinant-DNA plants, with additional attention to novel proteins, junction ORFs, and expression in edible parts.", "Core Question 1, 마지막 문단"),
    ("R10", "SDN-3 aligns with classical recombinant-DNA transgenesis because it can introduce a novel or altered protein and creates new DNA junctions ...", "첫 번째 Core Question 1, 두 번째 문단"),
]


def primary_status():
    ws = openpyxl.load_workbook(PRIMARY, data_only=True)["L3 판정"]
    r = list(ws.iter_rows(values_only=True))
    rows = [dict(zip(r[0], x)) for x in r[1:] if x[0] is not None]
    return {(d["보고서 ID"], d["항목 ID"]): d["반영 상태"] for d in rows}


def sheet(wb, title, head, widths, data, choices):
    ws = wb.create_sheet(title)
    ws.append(head)
    for c in ws[1]:
        c.font = Font(bold=True)
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(65 + i)].width = w
    for row in data:
        ws.append(list(row) + ["", ""])
        n = ws.max_row
        for c in ws[n]:
            c.alignment = WRAP
        for col in (chr(64 + len(head) - 1), chr(64 + len(head))):
            ws[f"{col}{n}"].fill = INPUT
    dv = DataValidation(type="list", formula1='"' + ",".join(choices) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    col = chr(64 + len(head) - 1)
    dv.add(f"{col}2:{col}{ws.max_row}")


def main():
    st = primary_status()
    look = lambda rid, cbs: ", ".join(f"{c} {st.get((rid, c), '?')}" for c in cbs.split("·"))
    wb = Workbook()
    ws = wb.active
    ws.title = "안내"
    for line in [
        "함준혁 박사님께 보내려던 보완 요청을 내부에서 처리하기 위한 확인표입니다.",
        "후보 문장은 Codex가 보고서에서 찾았고 Claude가 일부를 원문과 대조했습니다. 판정은 사람이 노란 칸에 합니다.",
        "'주판정 상태'는 함 박사님의 기존 L3 판정입니다. 이미 누락·상충이면 새 사례로 세지 않고 '기존 판정과 같음'을 고르시면 됩니다.",
        "① 조기 종료: '추가 자료 필요'나 '결정 보류' 노드가 재평가 없이 '평가 완료'로 이어지는지 봅니다.",
        "② 누락·근거 없는 면제: 중대 항목의 평가가 빠졌거나 근거 없이 생략됐는지 봅니다.",
        "③ 상충 근거: 기존 CB04 상충 판정의 근거 문장이 맞는지 봅니다.",
    ]:
        ws.append([line])
    ws.column_dimensions["A"].width = 110
    head = ["보고서", "CB", "주판정 상태", "후보 문장", "위치", "판정", "메모"]
    widths = [8, 10, 18, 60, 45, 18, 40]
    sheet(wb, "① 조기 종료", head, widths, [(r, cb, look(r, cb), q, loc) for r, cb, q, loc in CLOSURE],
          ["중대 사례", "아님", "기존 판정과 같음"])
    sheet(wb, "② 누락·면제", head, widths, [(r, cb, look(r, cb), q, loc) for r, cb, q, loc in OMISSION],
          ["중대 사례", "아님", "기존 판정과 같음"])
    sheet(wb, "③ 상충 근거", ["보고서", "CB", "주판정 상태", "후보 문장", "위치", "판정", "메모"], widths,
          [(r, "CB04", look(r, "CB04"), q, loc) for r, q, loc in CONFLICT], ["근거 맞음", "재검토"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    return OUT


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(main())
