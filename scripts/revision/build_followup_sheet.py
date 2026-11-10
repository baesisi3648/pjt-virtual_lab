"""Short follow-up workbook for the primary judge without the L4 sheet. Deterministic (no LLM).

Asks only for critical cases per report and the evidence sentence of the four conflict rows.
Anonymous report IDs only.
"""
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment

sys.path.insert(0, str(Path(__file__).parent))
import build_l4_supplement as B  # noqa: E402

OUT = B.OUT.with_name("주판정_보완시트_L4제외.xlsx")


def main():
    wb = Workbook()
    ws = wb.active
    ws.title = "안내"
    for line in [
        "노란 칸에 답하시면 됩니다. 분기 코딩(L4)은 요청하지 않습니다.",
        "① 중대 사례: 필수 평가 생략, 근거 없는 면제, 불확실한 채 종료가 있는지 보고서별로 있음/없음을 고르고, 있으면 사례마다 한 줄(위치, 이유, 관련 CB)을 적어 주세요. 이미 판정한 중대 항목의 누락·상충과 겹치면 관련 CB만 적으면 됩니다.",
        "② 상충 위치: 4건만 근거 문장 번호를 고르세요. 여러 개여도 됩니다. 근거가 아니면 '재검토'라고 적어 주세요.",
        "생성형 AI로 판정하지 말아 주세요.",
    ]:
        ws.append([line])
        ws.cell(ws.max_row, 1).alignment = Alignment(wrap_text=True)
    ws.column_dimensions["A"].width = 110

    ws = wb.create_sheet("① 중대 사례")
    B.header(ws, ["보고서", "중대 사례", "있으면 사례마다 한 줄 (위치, 이유, 관련 CB)"], [8, 10, 100])
    for rid in B.IDS:
        ws.append([rid, "", ""])
    B.add_list(ws, ["없음", "있음"], "B2:B11")
    for r in range(2, 12):
        ws[f"B{r}"].fill = B.INPUT
        ws[f"C{r}"].fill = B.INPUT
        ws[f"C{r}"].alignment = B.WRAP

    ws = wb.create_sheet("② 상충 위치")
    B.header(ws, ["보고서", "항목", "후보 1", "후보 2", "후보 3", "근거 번호 (없으면 위치, 근거 아니면 재검토)"], [8, 8, 50, 50, 50, 20])
    for rid in B.CONFLICTS:
        text, _ = B.L.report_trees(rid)
        c = B.conflict_candidates(text)
        ws.append([rid, "CB04"] + c + [""] * (3 - len(c)) + [""])
        r = ws.max_row
        ws[f"F{r}"].fill = B.INPUT
        for col in "CDE":
            ws[f"{col}{r}"].alignment = B.WRAP
        B.fit(ws, r, {"C": 50, "D": 50, "E": 50})
    wb.save(OUT)
    return OUT


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(main())
