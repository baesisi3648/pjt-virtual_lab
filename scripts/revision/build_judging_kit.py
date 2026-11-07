"""Build the blinded judging kit for L3/L4 (revision_plan 11) from the main runs and the frozen codebook.

    python scripts/revision/build_judging_kit.py        (system Python: needs openpyxl and markdown;
                                                          the experiment venv is left untouched)

Outputs (reference/revision/judging/, not committed):
- blinding_key.json             run <-> anonymous ID (seed from the manifest). Judges must not open it.
- reports/Rxx.html, Rxx_en.md, Rxx_ko.md
                                 report as generated, minus the Methods section (it reveals rounds and
                                 statistics, hence the condition). Nothing else is edited.
- primary_judge_sheet.xlsx      all ten reports: L3 status and causes, critical cases, AI additions, L4
- second_judge_sheet.xlsx       the three manifest-sampled reports: L3 status only, no causes or flags
- external/<ID>/                 representative run for the external judges (report files)
"""
from __future__ import annotations

import hashlib
import html
import json
import random
import re
import sys
from pathlib import Path

import markdown
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "experiments" / "runs_rev"
MAIN = RUNS / "main"
OUT = ROOT / "reference" / "revision" / "judging"
CODEBOOK = RUNS / "analysis_criteria.json"
MANIFEST = RUNS / "experiment_manifest.json"
REPRESENTATIVE = RUNS / "results" / "representative.json"

STATUS = ["일치", "부분", "누락", "상충", "범위 밖"]
CAUSES = [("template", "양식"), ("model", "모델"), ("design_exclusion", "설계상 배제"),
          ("not_in_retrieval", "검색 자료 없음"), ("undetermined", "판단 불가")]
CRIT_TYPES = ["필수 평가 생략", "근거 없는 면제", "불확실한 상태의 종료", "기타"]
OUTCOME = ["추가 평가", "종료", "추가 자료 요구·판단 보류", "없음"]
METHODS_HEADINGS = ("## Methods", "## 방법")
STATUS_DEFS = [
    "일치: 항목의 핵심 요소가 모두 있고 기준 문헌과 맞음.",
    "부분: 평가는 있으나 핵심 요소가 하나 이상 빠졌거나, 기준 문헌보다 좁은 범위(일부 기술 범주)에만 적용.",
    "누락: 해당 평가나 자료 요구가 없음.",
    "상충: 기준 문헌과 반대되는 서술 (조건 없는 면제, 평가가 필요한데 종료 등). 부분과 상충이 함께 있으면 상충.",
    "범위 밖: 보고서가 명시적으로 다루지 않기로 한 대상에만 해당. 비고에 이유. 범주는 다루면서 그 평가만 없으면 누락 또는 부분.",
]
# Notes shown to judges who do not see cause tags (second judge, external judges).
NEUTRAL_NOTES = {
    "CB19": ("The 35%/80 amino-acid and 6-8 contiguous amino-acid thresholds are numeric criteria and are not "
             "judged; if the assessment itself is present, judge match or partial. Conditional serum testing is "
             "judged under CB20 and enteropathy under CB21, not here."),
}


def item_note(it: dict, neutral: bool) -> str:
    if neutral and it["id"] in NEUTRAL_NOTES:
        return NEUTRAL_NOTES[it["id"]]
    return it.get("note", "")


def ok_attempt(run: str) -> Path:
    for a in sorted((MAIN / run).glob("attempt_*")):
        if json.loads((a / "meta.json").read_text(encoding="utf-8")).get("status") == "ok":
            return a
    raise SystemExit(f"no successful attempt for {run}")


def strip_methods(text: str) -> str:
    parts = re.split(r"(?m)^(?=## )", text)
    head, sections = parts[0], parts[1:]
    return head + "".join(s for s in sections if not s.startswith(METHODS_HEADINGS))


def to_html(md_text: str) -> str:
    blocks = []

    def stash(m):
        blocks.append(m.group(1))
        return f"\n\nMERMAID{len(blocks) - 1}END\n\n"

    text = re.sub(r"```mermaid\s*\n(.*?)```", stash, md_text, flags=re.S).replace("<", "&lt;")
    out = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    for i, code in enumerate(blocks):
        pre = f'<pre class="mermaid">{html.escape(code.strip())}</pre>'
        out = out.replace(f"<p>MERMAID{i}END</p>", pre).replace(f"MERMAID{i}END", pre)
    return out


def report_page(rid: str, en: str, ko: str) -> str:
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>보고서 {rid}</title>
<style>
body{{font:16px/1.65 "Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif;color:#1c2422;background:#fbfcfb;margin:0}}
main{{max-width:960px;margin:0 auto;padding:24px 18px 64px}}
header{{position:sticky;top:0;background:#fbfcfb;border-bottom:1px solid #d5dcd9;padding:10px 0;display:flex;gap:12px;align-items:center;flex-wrap:wrap}}
header b{{font-size:18px}} button{{border:1px solid #9aa5a1;background:#fff;border-radius:6px;padding:5px 12px;cursor:pointer;font:inherit}}
button[aria-pressed=true]{{background:#24605a;color:#fff;border-color:#24605a}}
.note{{color:#5a6662;font-size:14px}} table{{border-collapse:collapse;display:block;overflow-x:auto}} td,th{{border:1px solid #d5dcd9;padding:4px 8px;vertical-align:top}}
pre.mermaid{{background:#fff;border:1px dashed #d5dcd9;padding:8px;overflow-x:auto}} h2{{border-top:1px solid #d5dcd9;padding-top:18px}}
</style></head><body><main>
<header><b>보고서 {rid}</b><button id="b-en" aria-pressed="true">English (원문, 판정 기준)</button><button id="b-ko" aria-pressed="false">한국어 (자동 번역, 참고용)</button>
<span class="note">Methods 절은 판정과 무관해 제외했습니다. 나머지는 생성된 그대로입니다.</span></header>
<article id="en" lang="en">{to_html(en)}</article><article id="ko" lang="ko" hidden>{to_html(ko)}</article>
</main>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<script>
mermaid.initialize({{startOnLoad:false,securityLevel:"strict"}});
const shown = new Set();
async function show(l){{for(const x of ["en","ko"]){{document.getElementById(x).hidden=x!==l;document.getElementById("b-"+x).setAttribute("aria-pressed",String(x===l));}}
 if(!shown.has(l)){{shown.add(l);await mermaid.run({{nodes:document.querySelectorAll("#"+l+" .mermaid")}});}}}}
document.getElementById("b-en").onclick=()=>show("en");document.getElementById("b-ko").onclick=()=>show("ko");show("en");
</script></body></html>"""


def style_header(ws, widths):
    fill = PatternFill("solid", fgColor="E3EEEB")
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = w
        c = ws.cell(1, i)
        c.font = Font(bold=True)
        c.fill = fill
        c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "C2"


def add_list(ws, values, rng):
    dv = DataValidation(type="list", formula1='"' + ",".join(values) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(rng)


def guide_sheet(wb, lines, title="안내"):
    ws = wb.active
    ws.title = title
    ws.column_dimensions["A"].width = 120
    for i, line in enumerate(lines, start=1):
        c = ws.cell(i, 1, line)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if i == 1:
            c.font = Font(bold=True, size=14)


def l3_sheet(wb, ids, items, primary: bool):
    ws = wb.create_sheet("L3 판정")
    cols = ["보고서 ID", "항목 ID", "영역", "기준 항목", "핵심 요소 (모두 있으면 일치)", "적용 대상", "항목 비고 (판정 규칙)"]
    if primary:
        cols += ["중대 항목", "판단 지점", "양식 노드"]
    cols += ["반영 상태"]
    if primary:
        cols += [f"원인: {ko}" for _, ko in CAUSES]
    cols += ["보고서 근거 위치", "비고"]
    ws.append(cols)
    for rid in ids:
        for it in items:
            row = [rid, it["id"], it["domain"], it["item_ko"], "\n".join("· " + c for c in it["core_elements"]),
                   it.get("applies_to", ""), item_note(it, neutral=not primary)]
            if primary:
                row += ["예" if it["critical"] else "", "예" if it["decision_point"] else "",
                        it.get("template_overlap") or ""]
            row += [""]
            if primary:
                row += [""] * len(CAUSES)
            row += ["", ""]
            ws.append(row)
    n = len(ids) * len(items) + 1
    status_col = cols.index("반영 상태") + 1
    letter = ws.cell(1, status_col).column_letter
    add_list(ws, STATUS, f"{letter}2:{letter}{n}")
    if primary:
        for k in range(len(CAUSES)):
            l2 = ws.cell(1, status_col + 1 + k).column_letter
            add_list(ws, ["O"], f"{l2}2:{l2}{n}")
    widths = [9, 8, 14, 46, 46, 30, 40] + ([8, 8, 22] if primary else []) + [11] + ([9] * len(CAUSES) if primary else []) + [22, 30]
    style_header(ws, widths)
    for r in ws.iter_rows(min_row=2):
        for c in r:
            c.alignment = Alignment(wrap_text=True, vertical="top")


def build_primary(ids, items, path):
    wb = Workbook()
    guide_sheet(wb, [
        "주 판정자용 판정 시트 (L3·L4)",
        f"보고서 {len(ids)}개({', '.join(ids)})를 기준표 {len(items)}개 항목으로 판정합니다. 보고서는 reports/ 폴더의 HTML(영문 원문 기준)로 보세요.",
        "판정 기준: experiments/runs_rev/analysis_criteria.json (확정본 v1.0). 기준표 페이지(확정본)의 정의와 규칙을 따르고, 각 행의 '항목 비고'에 적힌 항목별 규칙을 우선 적용합니다.",
        "반영 상태 정의:", *STATUS_DEFS,
        "원인: 해당하는 칸에 O (복수 가능). 수치 기준만 없을 때 설계상 배제는 항목 비고에 적힌 수치(CB19 서열 기준 등)에만 씁니다.",
        "근거 위치: 절·단계·노드 (예: CQ5 Step 4, SDN-3 tree node E5).",
        "일부 보고서는 모델이 본문을 두 번 썼습니다(두 번째는 짧은 판). 보고서 전체를 한 판정 단위로 보고 생성된 그대로 판정합니다. 반복을 추가 점수로 세지 않습니다. 두 판이 서로 다르면 비고에 적고, 반대되는 서술이면 상충 우선 규칙을 따릅니다.",
        "중대 사례 시트: 어느 항목이든 필수 평가 생략, 근거 없는 면제, 안전성 결론에 중요한 불확실성이 남았는데 종료한 서술을 모두 적습니다. 같은 사례가 중대 항목의 누락·상충과 겹치면 '관련 항목 ID'로 연결해 중복 집계를 막습니다.",
        "원인 '검색 자료 없음'은 검색 스냅샷(experiments/runs_rev/retrieval_snapshot.json)을 확인해야 정할 수 있습니다. 참고문헌 목록만으로 정하지 않습니다.",
        "AI 추가 제안 시트: 어느 항목에도 해당하지 않는 평가·제안과 근거 충분 여부.",
        "L4 시트: 판단 지점 17개마다 보고서에 나타난 분기를 한 행에 하나씩 적습니다 (행이 모자라면 복사해 추가). 위치(통합 트리, SDN-1·2·3·ODM 트리, 본문 단계)를 적고, 통합 트리와 개별 트리의 분기가 같으면 한 번만, 다르면 둘 다 적습니다. 지점 자체가 없으면 '유무=없음' 한 행. 범주가 보고서 범위 밖이면 '적용=범위 밖'.",
        "L4 정규화: 같은 뜻의 노드 표현은 '정규화 변환표' 시트에 원문 표현 → 정규화 코드로 등록하고, L4 시트의 정규화 열에는 그 코드를 씁니다.",
        "판정은 직접 합니다. GPT·Claude 등 파이프라인에 쓴 모델로 판정하지 않습니다. LLM으로 위치를 찾았다면 원문과 대조해 확정하고 비고에 적습니다.",
        "blinding_key.json은 판정이 끝날 때까지 열지 않습니다.",
    ])
    l3_sheet(wb, ids, items, primary=True)
    ws = wb.create_sheet("중대 사례")
    ws.append(["보고서 ID", "관련 항목 ID", "보고서 위치", "유형", "내용", "판단 근거"])
    add_list(ws, CRIT_TYPES, "D2:D500")
    style_header(ws, [9, 10, 22, 18, 60, 50])
    ws = wb.create_sheet("AI 추가 제안")
    ws.append(["보고서 ID", "보고서 위치", "내용", "근거", "판단 근거"])
    add_list(ws, ["근거 충분", "근거 부족"], "D2:D500")
    style_header(ws, [9, 22, 60, 12, 50])
    ws = wb.create_sheet("L4 구조")
    ws.append(["보고서 ID", "판단 지점", "분기 정의 (기준표)", "위치 (트리·단계)", "적용", "유무", "분기 조건 (보고서 원문)",
               "정규화 조건", "분기 값", "연결 대상 (보고서 원문)", "정규화 대상", "결과 유형", "양식 노드", "비고"])
    dps = [it for it in items if it["decision_point"]]
    for rid in ids:
        for it in dps:
            for value in ("Yes", "No"):  # two branch rows per decision point; copy rows for more branches
                ws.append([rid, it["id"], it.get("branch", ""), "", "", "", "", "", value, "", "", "",
                           it.get("template_overlap") or "", ""])
    n = len(ids) * len(dps) * 2 + 500
    add_list(ws, ["통합 트리", "SDN-1 트리", "SDN-2 트리", "SDN-3 트리", "ODM 트리", "본문 단계", "기타"], f"D2:D{n}")
    add_list(ws, ["적용", "범위 밖"], f"E2:E{n}")
    add_list(ws, ["있음", "없음"], f"F2:F{n}")
    add_list(ws, OUTCOME, f"L2:L{n}")
    style_header(ws, [9, 9, 42, 14, 9, 8, 34, 16, 9, 30, 16, 18, 20, 26])
    ws = wb.create_sheet("정규화 변환표")
    ws.append(["보고서 ID", "원문 표현 (노드·분기)", "정규화 코드", "종류", "비고"])
    add_list(ws, ["조건", "대상"], "D2:D1000")
    style_header(ws, [9, 50, 20, 8, 30])
    wb.save(path)


def build_second(ids, items, path):
    wb = Workbook()
    guide_sheet(wb, [
        "2차 판정자용 판정 시트 (L3, 표본 3개)",
        f"보고서 {', '.join(ids)}를 기준표 {len(items)}개 항목으로 판정합니다. 보고서는 reports/ 폴더의 HTML(영문 원문 기준)로 보세요.",
        "항목마다 반영 상태 하나만 고릅니다. 정의:", *STATUS_DEFS,
        "각 행의 '항목 비고'에 적힌 항목별 규칙을 우선 적용합니다. 수치 기준(서열 상동성 % 등)은 판정 대상이 아닙니다.",
        "명시적 오분류는 상충, 불완전한 구분은 부분입니다. 여러 기술 범주 중 일부에서만 충족하면 부분입니다.",
        "일부 보고서는 본문이 두 번 쓰여 있습니다. 보고서 전체를 한 단위로 판정하고, 두 판이 반대되면 상충 우선입니다.",
        "주 판정 결과, LLM 위치 표시 자료, blinding_key.json은 보지 않습니다. 다른 판정자와 상의하지 않습니다. 생성형 AI로 판정하지 않습니다.",
    ])
    l3_sheet(wb, ids, items, primary=False)
    wb.save(path)


def main() -> int:
    codebook = json.loads(CODEBOOK.read_text(encoding="utf-8"))
    if not codebook.get("status", "").startswith("FROZEN"):
        raise SystemExit("codebook is not frozen")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    runs = sorted(f'{e["condition"]}_{e["run_id"]}' for e in manifest["order"])
    rng = random.Random(manifest["analysis"]["blinding_seed"])
    shuffled = runs[:]
    rng.shuffle(shuffled)
    key = {run: f"R{i + 1:02d}" for i, run in enumerate(shuffled)}
    ids = sorted(key.values())

    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    for run, rid in key.items():
        att = ok_attempt(run)
        en = strip_methods((att / "final_report.md").read_text(encoding="utf-8"))
        ko = strip_methods((att / "final_report.ko.md").read_text(encoding="utf-8"))
        (OUT / "reports" / f"{rid}_en.md").write_text(en, encoding="utf-8")
        (OUT / "reports" / f"{rid}_ko.md").write_text(ko, encoding="utf-8")
        (OUT / "reports" / f"{rid}.html").write_text(report_page(rid, en, ko), encoding="utf-8")

    key_doc = {"seed": manifest["analysis"]["blinding_seed"], "rule": "random.Random(seed).shuffle(sorted run names); "
               "position i -> R{i+1:02d}", "key": dict(sorted(key.items())),
               "report_source": {run: str(ok_attempt(run).relative_to(ROOT)).replace("\\", "/") for run in runs}}
    key_path = OUT / "blinding_key.json"
    key_path.write_text(json.dumps(key_doc, ensure_ascii=False, indent=2), encoding="utf-8")

    items = codebook["items"]
    build_primary(ids, items, OUT / "primary_judge_sheet.xlsx")
    second_runs = manifest["analysis"]["second_judge_sample"]["reports"]
    second_ids = sorted(key[r] for r in second_runs)
    build_second(second_ids, items, OUT / "second_judge_sheet.xlsx")

    rep = json.loads(REPRESENTATIVE.read_text(encoding="utf-8"))["representative"]
    ext = OUT / "external" / key[rep]
    ext.mkdir(parents=True, exist_ok=True)
    for suffix in (".html", "_en.md", "_ko.md"):
        (ext / f"{key[rep]}{suffix}").write_bytes((OUT / "reports" / f"{key[rep]}{suffix}").read_bytes())

    print("blinding key sha256", hashlib.sha256(key_path.read_bytes()).hexdigest())
    print("ids", ids, "| second judge ids", second_ids, "| external id", key[rep])
    return 0


if __name__ == "__main__":
    sys.exit(main())
