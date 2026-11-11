"""Internal critical-case check sheet (replaces the follow-up request to the primary judge).

Candidate passages were located by Codex (read-only, 2026-11-11). Locations and the Korean
"what to check" notes were written by Claude from the report context. The human reviewer (S.B.)
makes every judgement in the yellow cells. Anonymous report IDs only.

    python -B scripts/revision/build_internal_critical_sheet.py
"""
import json
import sys
from pathlib import Path

import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[2]
PRIMARY = next((ROOT / "reference" / "판정시트").glob("주판정*.xlsx"))
CRITERIA = ROOT / "experiments" / "runs_rev" / "analysis_criteria.json"
OUT = ROOT / "reference" / "revision" / "packages_v1" / "6_내부_중대사례검토" / "중대사례_내부확인표.xlsx"
INPUT = PatternFill("solid", fgColor="FFF4CC")
WRAP = Alignment(wrap_text=True, vertical="top")

# (report, CB, where (Korean), English passage, what to check (Korean))
TREE = "보고서 끝 '통합 의사결정 트리'"
CLOSURE = [
    ("R01", "CB11", TREE,
     '"Any decision-relevant uncertainty remains?" → Yes → "Additional data required" → "Assessment complete"',
     "결정에 영향을 줄 불확실성이 남았다고 답해도 '추가 자료 필요'를 거쳐 그대로 '평가 완료'로 끝납니다. 자료를 받은 뒤 다시 평가하는 단계가 없습니다."),
    ("R02", "CB19", TREE + "의 단백질 평가 부분",
     '"Uncertainty resolved?" → No → "Additional data required" → "Assessment complete"',
     "단백질 안전성의 불확실성이 해소되지 않았는데도 '추가 자료 필요'에서 바로 '평가 완료'로 이어집니다."),
    ("R03", "CB22", TREE + "의 성분 비교 부분",
     '"Signals outside normal comparator ranges?" → Yes → "Additional data required - targeted pathway profiling and exposure" → "Assessment complete"',
     "성분이 비교 대상의 정상 범위를 벗어나면 추가 분석을 요청하지만, 결과를 해석하는 단계 없이 '평가 완료'로 끝납니다."),
    ("R04", "CB19", TREE + "의 단백질 평가 부분",
     '"Uncertainty closed by weight-of-evidence?" → No → "Decision deferred pending further data" → "Assessment complete"',
     "증거 가중으로 불확실성이 해소되지 않으면 '결정 보류'인데, 그 노드가 바로 '평가 완료'로 이어집니다."),
    ("R05", "CB20", TREE + "의 단백질 평가 부분",
     '"Signals of concern persist after weight-of-evidence" → Yes → "Additional data required - serum screening or focused toxicology" → "Assessment complete"',
     "우려 신호가 남아 혈청 시험이나 독성 시험을 요청하지만, 그 결과를 보는 단계 없이 '평가 완료'로 끝납니다."),
    ("R06", "CB19", TREE + "의 단백질 평가 부분",
     '"Uncertainty resolved?" → No → "Additional data required" → "Assessment complete"',
     "R02와 같은 구조입니다. 불확실성이 해소되지 않아도 '추가 자료 필요'에서 바로 '평가 완료'로 이어집니다."),
    ("R07", "CB03", TREE + "의 잔류 외래 DNA 확인 부분",
     '"Residual DNA detected?" → Yes → "Decision deferred pending further data" → "Assessment complete"',
     "외래 DNA가 남아 있으면 GMO 경로로 보내야 하는데, '결정 보류'를 거쳐 그대로 '평가 완료'로 끝납니다."),
    ("R08", "CB19", TREE,
     '"Decision-relevant uncertainty remains?" → Yes → "Additional data required" → "Assessment complete"',
     "R01과 같은 구조입니다. 불확실성이 남아도 '추가 자료 필요'에서 바로 '평가 완료'로 이어집니다."),
    ("R09", "CB19·CB22", TREE + "의 단백질·성분 평가 부분",
     '"Any unresolved protein or composition concerns?" → Yes → "Additional data required" → "Assessment complete"',
     "단백질이나 성분 우려가 해소되지 않았는데도 '추가 자료 필요'에서 바로 '평가 완료'로 이어집니다."),
    ("R10", "CB22", "SDN-3 의사결정 트리의 마지막 부분",
     '"Any unexplained deviations from expectations?" → Yes → "Decision deferred pending further data" → "Assessment complete"',
     "설명되지 않는 편차가 있으면 '결정 보류'인데, 그 노드가 바로 '평가 완료'로 이어집니다."),
]
OMISSION = [
    ("R01", "CB28", "질문 5(단계별 프레임워크)의 7단계 '증거 가중 통합과 종결'",
     'Integrate molecular, comparative, toxicology, allergenicity, and nutrition strands ... Record each waived module as a closed hazard hypothesis with exposure bounds; where a live question remains, note "Additional data required" ...',
     "자료가 부족할 때 전체 식품 동물실험을 선택지로 둔다는 내용이 이 단계와 보고서 어디에도 없는지 봅니다. 약한 후보입니다."),
    ("R02", "CB04", "질문 1(분류 기준)의 기법별 목록 중 SDN-3 설명",
     "SDN-3 (site-directed nuclease class 3; insertion of longer DNA): may express a new or modified protein; border regions can create new short coding stretches that need a simple boundary check.",
     "삽입 DNA가 육종가 유전자풀에서 왔는지 가르는 판단이 없습니다. 유전자풀 안의 시스제닉 삽입과 밖의 형질전환 삽입을 구분하지 않습니다."),
    ("R02", "CB06", "질문 2(기법별 우선 위해) 중 SDN-3 삽입부 설명",
     "Junctions where the insert meets host DNA can, in principle, create short hybrid coding stretches; a simple boundary scan addresses this point.",
     "경계부의 새 ORF만 보고, 삽입이 기존 내재 유전자를 끊었는지는 평가하지 않습니다. '간단한 경계 확인으로 충분하다'는 표현이 근거 없는 축소인지 봅니다."),
    ("R03", "CB20", "질문 5(단계별 프레임워크)의 5단계 '단백질 평가 관문'",
     "In silico similarity screens to curated toxin and allergen datasets; if indicated, biochemical characterisation (e.g., stability, digestibility surrogates), and, where decision-relevant, in vitro assays ...",
     "알레르겐 상동성이 나와도 환자 혈청 IgE 결합 시험이 언급되지 않습니다. 'in vitro assays'를 혈청 시험으로 볼 수 있는지 봅니다."),
    ("R04", "CB04", "질문 3(기존 지침의 적용 가능성) 첫 문단",
     "SDN-3 follows the established recombinant-DNA path without modification.",
     "SDN-3을 출처 판단 없이 모두 재조합 DNA 경로로 보냅니다. 함 박사님은 이미 '누락'으로 판정했습니다."),
    ("R04", "CB20", "질문 3(기존 지침 검토) 중 '알레르기성과 단백질 안전성' 항목",
     "Where database coverage is thin or biology suggests possible cross-reactivity, targeted confirmatory work is considered in light of actual exposure and processing.",
     "교차 반응 가능성이 있을 때 '확인 시험을 고려한다'고만 하고 혈청 IgE 시험을 명시하지 않습니다."),
    ("R05", "CB06", "질문 1(분류 기준) 중 SDN-3 설명",
     "Structural rearrangements at or near the insertion site receive proportionate attention, especially with DNA-vector delivery or extended regeneration.",
     "삽입 부위 재배열은 언급하지만, 기존 내재 유전자가 끊겼는지와 그 결과를 평가하라는 뜻인지 봅니다. 약한 후보입니다."),
    ("R06", "CB20", "질문 5(단계별 프레임워크)의 6단계 '가식부의 단백질 존재와 특성'",
     "How to verify: immunoblotting or targeted proteomics for presence; in silico similarity to allergen/toxin databases; in vitro digestion in relevant food matrices; in chemico assays ...",
     "알레르겐 상동성 검색과 소화 시험만 있고 환자 혈청 IgE 시험은 없습니다."),
    ("R07", "CB28", "질문 5(단계별 프레임워크)의 8단계 '불확실성 기록과 면제 근거'",
     "Purpose: document low-plausibility pathways without escalation and focus any new studies on credible hazard-exposure routes. Convert omissions into short, evidence-linked waiver notes ...",
     "동물실험을 선택지로 두는 내용이 없습니다. 함 박사님은 이미 '누락'으로 판정했습니다."),
    ("R08", "CB04", "질문 1(분류 기준) 첫 문단의 SDN 유형 설명",
     "SDN-3 (insertion of a larger DNA fragment at a defined site).",
     "삽입 DNA의 유전자풀 출처를 가르는 판단이 없습니다. 함 박사님은 이미 '누락'으로 판정했습니다."),
    ("R08", "CB20", "질문 5(단계별 프레임워크)의 5단계 '단백질 고려 사항'",
     "when a novel protein is plausible, a modern weight-of-evidence package applies (bioinformatics, source history, digestibility/stability, and exposure).",
     "새 단백질이 있을 때 생물정보·출처·소화성·노출만 보고, 혈청 IgE 시험은 없습니다."),
    ("R09", "CB20", "질문 5(단계별 프레임워크)의 8단계 '단백질 안전성 흐름'",
     "Elements include in silico similarity to known allergens and toxins, in vitro digestibility or stability indicators, and exposure reasoning ... Techniques include sequence homology tools, simulated digestion assays, Western blotting, and targeted ELISA when expression data are needed.",
     "ELISA는 발현량 측정용이고, 환자 혈청 IgE 시험은 없습니다."),
    ("R10", "CB20", "질문 5(단계별 프레임워크)의 7단계 '새 단백질이 있을 때의 단백질 안전성'",
     "integrate source, homology to known allergens and toxins, expected abundance, and digestibility/stability in the food matrix ... Illustrative tools include bioinformatic homology searches, in vitro digestibility assays, Western blot, and exposure-centred use narratives.",
     "상동성·소화성·발현량만 보고, 환자 혈청 IgE 시험은 없습니다."),
]
CONFLICT = [
    ("R03", "CB04", "질문 1(분류 기준)의 두 번째 문단",
     "For SDN-3, established recombinant-DNA practice applies: characterise the inserted sequence, its junctions to the genome ..., and its genomic context ...",
     "SDN-3이면 출처와 상관없이 재조합 DNA 평가를 적용한다고 합니다. 지침은 유전자풀 안의 삽입(시스제닉)을 형질전환과 구분하므로 상충 근거가 맞는지 봅니다."),
    ("R05", "CB04", "질문 5(단계별 프레임워크)의 2단계",
     "SDN-3 follows the recombinant-DNA path with insertion/junction characterisation and any new protein.",
     "R03과 같은 내용입니다. SDN-3을 모두 재조합 DNA 경로로 보냅니다."),
    ("R06", "CB04", "질문 1(분류 기준)의 마지막 문단",
     "SDN-3 aligns with established insert assessments used for recombinant-DNA plants, with additional attention to novel proteins, junction ORFs, and expression in edible parts.",
     "SDN-3을 재조합 DNA 식물의 삽입 평가와 같게 봅니다. 출처 구분이 없습니다."),
    ("R10", "CB04", "질문 1(분류 기준)의 두 번째 문단",
     "SDN-3 aligns with classical recombinant-DNA transgenesis because it can introduce a novel or altered protein and creates new DNA junctions ...",
     "SDN-3을 고전적 형질전환과 같다고 봅니다. 출처 구분이 없습니다."),
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
    ws.freeze_panes = "B2"
    dv = DataValidation(type="list", formula1='"' + ",".join(choices) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    col = chr(64 + len(head) - 1)
    dv.add(f"{col}2:{col}{ws.max_row}")


def main():
    st = primary_status()
    ko = {i["id"]: i["item_ko"] for i in json.loads(CRITERIA.read_text(encoding="utf-8"))["items"]}
    wb = Workbook()
    ws = wb.active
    ws.title = "안내"
    for line in [
        "함준혁 박사님께 보내려던 보완 요청을 내부에서 처리하기 위한 확인표입니다.",
        "후보 문장은 Codex가 보고서에서 찾았고, 위치와 설명은 Claude가 원문 맥락을 보고 썼습니다. 판정은 사람이 노란 칸에 합니다.",
        "원문 전체는 reference/revision/judging_v1/reports/ 의 Rxx_en.md(영문)와 Rxx_ko.md(국문)에 있습니다.",
        "'주판정'은 함 박사님의 기존 L3 판정입니다. 이미 누락·상충이면 '기존 판정과 같음'을 고르시면 됩니다.",
        "① 조기 종료: '추가 자료 필요'나 '결정 보류'가 다시 평가하지 않고 '평가 완료'로 이어지는 곳입니다.",
        "② 누락·근거 없는 면제: 중대 항목의 평가가 빠졌거나 근거 없이 줄어든 곳입니다. '약한 후보'라고 적은 행은 아닐 가능성이 큽니다.",
        "③ 상충 근거: 기존 CB04 상충 판정의 근거 문장 후보입니다.",
    ]:
        ws.append([line])
    ws.column_dimensions["A"].width = 110
    item = lambda cbs: "\n".join(f"{c}: {ko[c]}" for c in cbs.split("·"))
    look = lambda rid, cbs: ", ".join(str(st.get((rid, c), "?")) for c in cbs.split("·"))
    rows = lambda data: [(r, item(cb), look(r, cb), where, text, why) for r, cb, where, text, why in data]
    head = ["보고서", "관련 항목", "주판정", "어디에", "원문", "무엇을 보면 되나", "판정", "메모"]
    widths = [7, 34, 9, 28, 55, 45, 16, 30]
    sheet(wb, "① 조기 종료", head, widths, rows(CLOSURE), ["중대 사례", "아님", "기존 판정과 같음"])
    sheet(wb, "② 누락·면제", head, widths, rows(OMISSION), ["중대 사례", "아님", "기존 판정과 같음"])
    sheet(wb, "③ 상충 근거", head, widths, rows(CONFLICT), ["근거 맞음", "재검토"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    return OUT


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(main())
