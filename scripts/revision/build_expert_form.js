// Build the external expert evaluation form (revision_plan 11, L9) from the L3 codebook.
//   npm install docx@9.5.1   (anywhere on NODE_PATH)
//   node scripts/revision/build_expert_form.js <codebook.json> <out.docx> [report_id]
// The form is generated from the codebook so that external judges and the authors use the same items.
// Critical flags, causes and template information are deliberately not shown to external judges.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, AlignmentType, LevelFormat,
  HeadingLevel, BorderStyle, WidthType, ShadingType, PageOrientation, Footer, PageNumber, VerticalAlign,
} = require("docx");

const [, , SRC, OUT, REPORT_ID = "R-__"] = process.argv;
const cb = JSON.parse(fs.readFileSync(SRC, "utf8"));

const FONT = "Malgun Gothic";
const A4 = { width: 11906, height: 16838 };
const M = 1134; // 2 cm margins
const PORTRAIT_W = A4.width - 2 * M;   // 9638
const LAND_W = A4.height - 2 * M;      // 14570
const line = { style: BorderStyle.SINGLE, size: 4, color: "9AA5A1" };
const borders = { top: line, bottom: line, left: line, right: line };
const HEAD_FILL = "E3EEEB";
const BOX = "☐";

const DOMAIN_KO = {
  "Classification": "분류", "Host plant": "숙주 식물", "Molecular characterisation": "분자 특성",
  "Expressed substances": "발현 물질", "Unintended effects": "의도치 않은 효과", "Allele function": "대립유전자 기능",
  "History of safe use": "안전 사용 이력", "Toxicity": "독성", "Metabolites": "대사산물", "Donor": "공여 생물",
  "Allergenicity": "알레르기성", "Comparative analysis": "비교분석", "Processing": "가공",
  "Nutrition and exposure": "영양·노출", "Multiple modifications": "다중 변형", "Whole food studies": "전체 식품 시험",
  "Marker genes": "표지 유전자", "Conclusion and review": "결론·재검토",
};
const DOC_KO = { EFSA2022: "EFSA 2022", CXG45: "CXG 45" };

const t = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || 20, bold: o.bold, italics: o.italics, color: o.color });
const p = (runs, o = {}) => new Paragraph({
  children: Array.isArray(runs) ? runs : [t(runs, o)], spacing: { after: o.after ?? 80, before: o.before ?? 0, line: o.line || 300 },
  alignment: o.align, numbering: o.numbering, keepNext: o.keepNext,
});
const h1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text, font: FONT })] });
const h2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text, font: FONT })] });
const bullet = (text) => p([t(text)], { numbering: { reference: "bullets", level: 0 }, after: 40 });
const num = (text, ref = "numbers") => p([t(text)], { numbering: { reference: ref, level: 0 }, after: 40 });

function cell(children, width, o = {}) {
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA }, verticalAlign: o.valign || VerticalAlign.TOP,
    shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 70, bottom: 70, left: 100, right: 100 }, columnSpan: o.span,
    children: (Array.isArray(children) ? children : [children]).map(c => (typeof c === "string" ? p(c, { size: o.size || 18, after: 20 }) : c)),
  });
}
function table(widths, rows, o = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((r, i) => new TableRow({
      tableHeader: o.header && i === 0, cantSplit: true,
      children: r.map((c, j) => (c instanceof TableCell ? c : cell(c, widths[j], { fill: o.header && i === 0 ? HEAD_FILL : undefined, size: o.size }))),
    })),
  });
}
const blankLines = (n, width) => table([width], [[Array.from({ length: n }, () => p(" ", { after: 120 }))]]);

// ---------------------------------------------------------------- cover and instructions
const intro = [
  p([t("외부 전문가 평가서", { size: 36, bold: true })], { after: 60 }),
  p([t("AI가 생성한 유전자편집식품 안전성 평가체계 보고서", { size: 24 })], { after: 240 }),
  table([2600, PORTRAIT_W - 2600], [
    [cell(p([t("평가 대상 보고서 ID", { bold: true, size: 18 })]), 2600, { fill: HEAD_FILL }), p([t(REPORT_ID, { size: 20 })])],
    [cell(p([t("평가자 성명", { bold: true, size: 18 })]), 2600, { fill: HEAD_FILL }), " "],
    [cell(p([t("소속 · 직위", { bold: true, size: 18 })]), 2600, { fill: HEAD_FILL }), " "],
    [cell(p([t("전문 분야", { bold: true, size: 18 })]), 2600, { fill: HEAD_FILL }), " "],
    [cell(p([t("평가 완료일", { bold: true, size: 18 })]), 2600, { fill: HEAD_FILL }), " "],
  ]),
  p(" ", { after: 120 }),
  h1("평가 안내"),
  p("이 평가서는 생성형 AI 다중 에이전트 시스템이 작성한 유전자편집식품(NGT) 식품 안전성 평가체계 보고서 한 건을 전문가의 관점에서 독립적으로 평가하기 위한 것입니다. 평가 결과는 연구 논문의 외부 전문가 평가 절에 집계해 보고합니다."),
  h2("받으신 자료"),
  bullet(`평가 대상 보고서 1건 (보고서 ID ${REPORT_ID}, 영문 원문과 참고용 한국어 번역)`),
  bullet("기준 문헌 2건: EFSA Journal 2022;20(10):7618 (Criteria for risk assessment of plants produced by targeted mutagenesis, cisgenesis and intragenesis), Codex CAC/GL 45-2003 (Guideline for the conduct of food safety assessment of foods derived from recombinant-DNA plants)"),
  bullet("이 평가서"),
  h2("평가 범위"),
  p("식물 유래 식품의 식품 안전성 평가에 한정합니다. 환경 위해성, 사료, 무역상 미량 혼입은 평가하지 않습니다. 판정은 영문 원문을 기준으로 해 주십시오. 한국어 번역은 참고용이며 자동 번역이라 부정확할 수 있습니다."),
  h2("독립성을 위한 부탁"),
  bullet("다른 평가자와 평가 내용을 상의하지 말아 주십시오."),
  bullet("판정과 점수는 직접 해 주십시오. 생성형 AI 도구로 판정하거나 의견을 작성하지 말아 주십시오."),
  bullet("연구진은 평가가 끝날 때까지 시스템의 내부 점수, 저자 판정, 다른 분석 결과를 알려 드리지 않습니다. 보고서가 어떤 조건에서 생성되었는지도 알려 드리지 않습니다."),
  bullet("보고서와 이 평가서의 내용은 논문 출판 전까지 외부에 공유하지 말아 주십시오."),
  h2("평가 구성과 예상 소요 시간"),
  table([2400, 4838, 2400], [
    ["구성", "내용", "예상 시간"],
    ["Part 0", "이해상충 확인과 동의", "5분"],
    ["Part A", "기준 항목 30개별 반영 상태 판정", "2–3시간"],
    ["Part B", "다섯 가지 측면의 1–5점 평가", "20분"],
    ["Part C", "중대한 오류·누락, 강점, 보완할 점 서술", "30분"],
  ], { header: true }),
  p(" ", { after: 60 }),
  p("작성하신 평가서는 Word 파일 그대로 회신해 주십시오. 칸이 부족하면 행을 추가하거나 별지를 붙이셔도 됩니다. 선택 항목은 ☐를 ☒ 또는 ■로 바꾸거나 해당 칸에 표시해 주십시오."),
];

// ---------------------------------------------------------------- part 0
const part0 = [
  h1("Part 0. 이해상충 확인과 동의"),
  table([7200, 2438], [
    ["항목", "응답"],
    ["이 연구의 저자이거나, 시스템 개발·실험에 참여한 적이 있습니까?", `${BOX} 예   ${BOX} 아니요`],
    ["평가 대상 보고서와 관련해 밝혀야 할 이해관계(재정적·직업적)가 있습니까? 있다면 아래에 적어 주십시오.", `${BOX} 예   ${BOX} 아니요`],
    ["논문 사사(Acknowledgements)에 성명과 소속을 밝히는 데 동의하십니까?", `${BOX} 동의   ${BOX} 비동의`],
    ["서술 의견을 평가자를 밝히지 않고 논문이나 심사 답변서에 인용하는 데 동의하십니까?", `${BOX} 동의   ${BOX} 비동의`],
  ], { header: true }),
  p("이해관계 내용 (해당 시):", { before: 120 }),
  blankLines(2, PORTRAIT_W),
];

// ---------------------------------------------------------------- part A (landscape)
const STATUS = [
  ["일치", "항목의 핵심 요소가 모두 있고, 기준 문헌과 맞습니다."],
  ["부분", "평가는 있으나 핵심 요소가 하나 이상 빠졌거나, 기준 문헌보다 좁은 범위(일부 기술 범주)에만 적용했습니다."],
  ["누락", "해당 평가나 자료 요구가 보고서에 없습니다."],
  ["상충", "기준 문헌과 반대되는 서술이 있습니다 (예: 기준 문헌의 조건 없이 평가를 면제, 기준 문헌이 평가를 요구하는데 종료). 부분과 상충이 함께 있으면 상충으로 판정합니다."],
  ["범위 밖", "보고서가 명시적으로 다루지 않기로 한 대상에만 해당하는 항목입니다. 이유를 의견란에 적어 주십시오. 해당 범주를 다루면서 그 평가만 없으면 누락이나 부분입니다."],
];
const W = { id: 900, item: 5200, core: 3600, status: 1500, loc: 1300, note: 2070 };
const AW = [W.id, W.item, W.core, W.status, W.loc, W.note];
const statusBoxes = () => ["일치", "부분", "누락", "상충", "범위 밖"].map(s => p([t(`${BOX} ${s}`, { size: 17 })], { after: 10 }));

const itemRows = [[
  "ID", "기준 항목 (판정 대상 평가 · 적용 대상 · 근거 문헌)", "핵심 요소 (모두 있으면 일치)", "반영 상태", "보고서 위치", "의견",
]];
for (const it of cb.items) {
  const refs = it.sources.map(s => `${DOC_KO[s.doc]} ${s.loc}${s.page ? ` (p.${s.page})` : ""}`).join("; ");
  itemRows.push([
    cell([p([t(it.id, { bold: true, size: 17 })], { after: 10 }), p([t(DOMAIN_KO[it.domain] || it.domain, { size: 15, color: "5A6662" })])], W.id),
    cell([
      p([t(it.item_ko, { size: 17, bold: true })], { after: 30 }),
      p([t(it.item_en, { size: 15, italics: true, color: "444444" })], { after: 30 }),
      p([t("적용 대상: ", { size: 15, bold: true }), t(it.applies_to || "", { size: 15 })], { after: 20 }),
      p([t("근거: ", { size: 15, bold: true }), t(refs, { size: 15 })]),
    ], W.item),
    cell(it.core_elements.map(c => p([t("· " + c, { size: 15 })], { after: 10 })), W.core),
    cell(statusBoxes(), W.status),
    cell(" ", W.loc),
    cell(" ", W.note),
  ]);
}

const partA = [
  h1("Part A. 기준 항목별 판정"),
  p("EFSA 2022와 Codex CXG 45에서 뽑은 30개 기준 항목마다 보고서의 반영 상태를 하나 골라 주십시오. 근거가 된 보고서 위치(예: Core Question 5 Step 4, SDN-3 decision tree)를 적어 주시면 연구진이 판정을 재확인할 때 도움이 됩니다. 수치 기준(예: 서열 상동성 35%/80 아미노산)은 판정 대상이 아닙니다. 평가 자체가 있으면 수치가 없어도 일치나 부분으로 판정해 주십시오."),
  table([1500, LAND_W - 1500], [["반영 상태", "정의"], ...STATUS], { header: true }),
  p(" ", { after: 80 }),
  table(AW, itemRows, { header: true }),
  p(" ", { after: 80 }),
  h2("기준 항목에 없는 추가 내용"),
  p("보고서에 있는데 위 30개 항목 어디에도 해당하지 않는 평가나 제안이 있으면 적어 주십시오. 근거가 충분한 확장인지, 근거가 부족한 제안인지도 표시해 주십시오."),
  table([2600, 7570, 2200, 2200], [
    ["보고서 위치", "내용", "근거 충분", "근거 부족"],
    ...Array.from({ length: 4 }, () => [" ", " ", BOX, BOX]),
  ], { header: true }),
];

// ---------------------------------------------------------------- part B
const DIMS = [
  ["B1", "과학적 정확성", "서술된 위해, 평가 방법, 판단 근거가 현재 과학 지식에 비추어 정확한가", "중대한 사실 오류가 여러 곳에 있다", "사소한 부정확함이 있으나 결론에 영향은 없다", "사실 오류가 없다"],
  ["B2", "기존 지침 대비 완전성", "EFSA 2022와 Codex CXG 45가 요구하는 평가 요소를 빠짐없이 다루는가", "주요 평가 요소가 여럿 빠졌다", "대부분 다루나 일부가 빠졌다", "필요한 요소를 모두 다룬다"],
  ["B3", "판단 지점과 분기의 적절성", "의사결정 트리와 단계별 체계의 분기 조건과 연결이 타당하고 일관적인가", "분기가 부적절하거나 서로 모순된다", "대체로 타당하나 일부 분기가 불명확하다", "분기가 명확하고 타당하다"],
  ["B4", "평가 생략·면제의 적절성", "평가를 생략하거나 면제하는 판단에 충분한 과학적 근거가 있고, 불확실성이 남을 때 추가 자료를 요구하는가", "근거 없는 면제나 불확실한 상태의 종료가 있다", "대체로 적절하나 근거가 약한 생략이 있다", "모든 생략·면제에 근거가 있다"],
  ["B5", "초안으로서의 활용 가능성", "규제 과학 전문가가 평가체계 초안이나 검토 출발점으로 쓸 수 있는 수준인가", "활용하기 어렵다", "상당한 수정 후 활용할 수 있다", "약간의 수정으로 활용할 수 있다"],
];
const BW = [700, 2600, 1800, 1800, 1800, 1938];
const partB = [h1("Part B. 구조화 평가 (1–5점)"),
  p("각 측면에 대해 1–5점 중 하나를 골라 주십시오. 1점, 3점, 5점의 기준을 참고하시고, 2점과 4점은 그 사이로 판단해 주십시오. 점수의 근거를 한두 문장으로 적어 주십시오.")];
for (const [id, name, q, a1, a3, a5] of DIMS) {
  partB.push(
    p([t(`${id}. ${name}`, { bold: true, size: 21 })], { before: 160, after: 40, keepNext: true }),
    p([t(q, { size: 19 })], { after: 60, keepNext: true }),
    table(BW, [
      ["", "기준", "1점", "3점", "5점", "선택"],
      [id, name, a1, a3, a5, cell(p([t(`${BOX}1  ${BOX}2  ${BOX}3  ${BOX}4  ${BOX}5`, { size: 17 })]), 1938)],
    ], { header: true }),
    p([t("점수 근거:", { size: 18, bold: true })], { before: 60, after: 20 }),
    blankLines(2, PORTRAIT_W),
  );
}

// ---------------------------------------------------------------- part C
const partC = [
  h1("Part C. 서술 의견"),
  h2("C1. 중대한 오류·누락"),
  p("식품 안전성 판단을 잘못 이끌 수 있는 오류, 필요한 평가의 누락, 부적절한 면제를 적어 주십시오. 가장 중요한 것부터 적어 주시면 됩니다."),
  table([1800, 3600, 1600, 2638], [
    ["보고서 위치", "내용", "심각도", "근거 · 수정 제안"],
    ...Array.from({ length: 5 }, () => [" ", " ", cell(["중대", "보통", "경미"].map(s => p([t(`${BOX} ${s}`, { size: 17 })], { after: 10 })), 1600), " "]),
  ], { header: true }),
  h2("C2. 이 보고서의 강점"), blankLines(4, PORTRAIT_W),
  h2("C3. 보완할 점"), blankLines(4, PORTRAIT_W),
  h2("C4. 평가 방법에 대한 의견"),
  p("기준 항목이나 평가 방식 자체에 대한 의견이 있으면 적어 주십시오 (예: 빠진 기준, 판정하기 어려웠던 항목)."),
  blankLines(3, PORTRAIT_W),
  p(" ", { after: 120 }),
  p([t("평가해 주셔서 감사합니다.", { bold: true })], { align: AlignmentType.CENTER }),
];

const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
  new TextRun({ text: `외부 전문가 평가서 · 보고서 ${REPORT_ID} · 기준표 ${cb.version} · `, font: FONT, size: 16, color: "6B7672" }),
  new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: "6B7672" }),
] })] });

const portrait = { page: { size: { width: A4.width, height: A4.height }, margin: { top: M, right: M, bottom: M, left: M } } };
const landscape = { page: { size: { width: A4.width, height: A4.height, orientation: PageOrientation.LANDSCAPE }, margin: { top: M, right: M, bottom: M, left: M } } };

const doc = new Document({
  creator: "Virtual Lab revision", title: "External expert evaluation form",
  styles: {
    default: { document: { run: { font: FONT, size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: FONT, color: "1F4E49" }, paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 0, keepNext: true } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: FONT }, paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 1, keepNext: true } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 560, hanging: 280 } } } }] },
    { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 560, hanging: 280 } } } }] },
  ] },
  sections: [
    { properties: portrait, footers: { default: footer }, children: [...intro, ...part0] },
    { properties: landscape, footers: { default: footer }, children: partA },
    { properties: portrait, footers: { default: footer }, children: [...partB, ...partC] },
  ],
});

Packer.toBuffer(doc).then(buf => { fs.writeFileSync(OUT, buf); console.log("wrote", OUT, buf.length); });
