"""Short supplementary workbook for the primary judge. Deterministic (no LLM).

One sheet of proposed L4 codings (report x decision point) that the judge corrects
only where wrong, one sign-off row per report with the critical-case answer, and
candidate sentences for the four conflict rows. Anonymous report IDs only.
"""
import json
import re
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(Path(__file__).parent))
import l4_extract as L  # noqa: E402

OUT = L.ROOT / "reference" / "revision" / "packages_v1" / "5_주판정자_보완요청" / "주판정_보완시트.xlsx"
CRITERIA = L.ROOT / "experiments" / "runs_rev" / "analysis_criteria.json"
IDS = [f"R{i:02d}" for i in range(1, 11)]
CONFLICTS = ["R03", "R05", "R06", "R10"]
INPUT = PatternFill("solid", fgColor="FFF4CC")
WRAP = Alignment(wrap_text=True, vertical="top")
FIXES = ["없음으로", "있음으로", "조건 다름", "대상 다름", "결과 다름", "여러 칸", "범위 밖"]
MAX_LINES = 24  # one row must stay readable within Excel's row-height limit


def header(ws, names, widths):
    ws.append(names)
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(65 + i)].width = w
        c = ws.cell(1, i + 1)
        c.font = Font(bold=True)
        c.alignment = Alignment(wrap_text=True, vertical="center")
    ws.freeze_panes = "A2"


def add_list(ws, options, rng):
    v = DataValidation(type="list", formula1='"' + ",".join(options) + '"', allow_blank=True)
    ws.add_data_validation(v)
    v.add(rng)


def fit(ws, row, cols):
    """Row height from the longest wrapped cell (Excel does not auto-fit on open)."""
    lines = 1
    for col, width in cols.items():
        v = str(ws[f"{col}{row}"].value or "")
        lines = max(lines, sum(1 + len(x) // max(int(width * 0.95), 1) for x in v.split("\n")))
    ws.row_dimensions[row].height = min(409, 15 * lines)


def l4_row(rid, cb, text, ts):
    """Return the proposal status, the body text and the tree/code text split into readable chunks."""
    hits = L.tree_hits(ts, L.KEYWORDS[cb])
    body = L.text_hits(text, L.KEYWORDS[cb])
    chunks, tree_lines, class_lines = [], [], []
    for h in hits:
        block = [f"[{h['tree']} {h['node']}] {h['label']}"] + [f"   {b or '→'} → {t}" for b, t, _ in h["branches"]]
        code = f"[{h['node']}] " + ("; ".join(f"{b or '→'}: {L.target_class(t)} / {o}" for b, t, o in h["branches"]) or "분기 없음")
        if tree_lines and len(tree_lines) + len(block) > MAX_LINES:
            chunks.append(("\n".join(tree_lines), "\n".join(class_lines)))
            tree_lines, class_lines = [], []
        tree_lines += block
        class_lines.append(code)
    chunks.append(("\n".join(tree_lines), "\n".join(class_lines)))
    status = "후보 있음 (트리)" if hits else ("본문 후보" if body else "후보 없음")
    return status, chunks, "\n".join(f"[{b['place']}] {b['text']}" for b in body)


def conflict_candidates(text):
    m = re.search(r"## Core Question 1.*?(?=\n## References)", text, re.S)
    strong, weak, seen = [], [], set()
    for s in re.split(r"(?<=[.;])\s+|\n+", m.group(0) if m else text):
        t = L.norm(s)
        if t in seen or not 30 < len(t) < 400:
            continue
        seen.add(t)
        if re.search(r"gene.?pool|cisgen|intragen", t, re.I):
            strong.append(t)
        elif re.search(r"SDN.3", t) and re.search(r"transgen|GMO|\bGM\b|recombinant|foreign|exogenous", t, re.I):
            weak.append(t)
    return (strong + weak)[:3]


def main():
    items = {i["id"]: i for i in json.loads(CRITERIA.read_text(encoding="utf-8"))["items"]}
    wb = Workbook()
    ws = wb.active
    ws.title = "안내"
    for line in [
        "노란 칸에 답하시면 됩니다. 후보가 맞는지는 보고서 원문과 대조해 주세요.",
        "① L4 확인: 스크립트가 트리·본문에서 찾아 둔 후보입니다. 맞으면 그대로 두고, 틀린 줄만 '수정'을 고르고 고친 값을 옆 칸에 적으세요. 후보에 없는 분기도 옆 칸에 적으세요.",
        "그대로 둔 줄의 뜻: '후보 있음'은 후보대로 확인, '본문 후보'는 본문 서술만 있고 분기 구조는 없음, '후보 없음'은 해당 판단 지점 없음.",
        "② 보고서별 확인: 보고서 전체를 본 뒤 '예'를 고르세요. 중대 사례(필수 평가 생략, 근거 없는 면제, 불확실한 채 종료)는 있음/없음을 고르고, 있으면 사례마다 한 줄(위치, 이유, 관련 CB)을 적으세요. 이미 판정한 중대 항목의 누락·상충과 겹치면 관련 CB만 적으면 됩니다.",
        "③ 상충 위치: 4건만 근거 문장 번호를 고르세요. 여러 개여도 됩니다. 근거가 아니면 '재검토'라고 적어 주세요.",
        "생성형 AI로 판정하지 말아 주세요.",
    ]:
        ws.append([line])
        ws.cell(ws.max_row, 1).alignment = Alignment(wrap_text=True)
    ws.column_dimensions["A"].width = 110

    sheet = wb.create_sheet("① L4 확인")
    widths = {"A": 7, "B": 7, "C": 32, "D": 11, "E": 58, "F": 40, "G": 46, "H": 12, "I": 26}
    header(sheet, ["보고서", "판단 지점", "기준 (무엇을 보고 나누는가)", "후보 상태", "트리 원문 (노드와 분기)", "제안 코드 (분기: 대상 유형 / 결과)", "본문 후보 문장", "수정 (틀릴 때만)", "고친 값, 빠진 분기"], list(widths.values()))
    cols = {k: widths[k] for k in "CEFG"}
    counts = {"후보 있음 (트리)": 0, "본문 후보": 0, "후보 없음": 0}
    for rid in IDS:
        text, ts = L.report_trees(rid)
        for cb in L.KEYWORDS:
            status, chunks, body = l4_row(rid, cb, text, ts)
            counts[status] += 1
            for k, (tree, klass) in enumerate(chunks):
                sheet.append([rid, cb, items[cb]["branch"] if k == 0 else "(이어서)", status if k == 0 else "이어서", tree, klass, body if k == 0 else "", "", ""])
                r = sheet.max_row
                for col in "CEFGI":
                    sheet[f"{col}{r}"].alignment = WRAP
                sheet[f"H{r}"].fill = INPUT
                sheet[f"I{r}"].fill = INPUT
                fit(sheet, r, cols)
    add_list(sheet, FIXES, f"H2:H{sheet.max_row}")
    sheet.auto_filter.ref = f"A1:I{sheet.max_row}"

    ws = wb.create_sheet("② 보고서별 확인")
    header(ws, ["보고서", "트리·본문 전체를 보고 ①을 확인함", "중대 사례", "있으면 사례마다 한 줄 (위치, 이유, 관련 CB)"], [8, 16, 10, 90])
    for rid in IDS:
        ws.append([rid, "", "", ""])
    add_list(ws, ["예"], "B2:B11")
    add_list(ws, ["없음", "있음"], "C2:C11")
    for r in range(2, 12):
        for col in "BCD":
            ws[f"{col}{r}"].fill = INPUT
        ws[f"D{r}"].alignment = WRAP

    ws = wb.create_sheet("③ 상충 위치")
    header(ws, ["보고서", "항목", "후보 1", "후보 2", "후보 3", "근거 번호 (없으면 위치, 근거 아니면 재검토)"], [8, 8, 50, 50, 50, 20])
    candidates = {}
    for rid in CONFLICTS:
        text, _ = L.report_trees(rid)
        c = conflict_candidates(text)
        candidates[rid] = c
        ws.append([rid, "CB04"] + c + [""] * (3 - len(c)) + [""])
        r = ws.max_row
        ws[f"F{r}"].fill = INPUT
        for col in "CDE":
            ws[f"{col}{r}"].alignment = WRAP
        fit(ws, r, {"C": 50, "D": 50, "E": 50})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    return counts, candidates


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    c, cand = main()
    print(c)
    for rid, v in cand.items():
        print(rid, len(v), [x[:100] for x in v])
