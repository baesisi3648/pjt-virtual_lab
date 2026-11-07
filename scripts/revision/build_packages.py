"""Build one folder and one zip per recipient from the judging kit (system Python).

    python scripts/revision/build_packages.py <mermaid.min.js>

Reads reference/revision/judging/ (built by build_judging_kit.py) and writes
reference/revision/packages/<recipient>/ plus <recipient>.zip. Each package opens with index.html,
works offline (mermaid bundled), and never contains blinding_key.json.
"""
from __future__ import annotations

import html
import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
J = ROOT / "reference" / "revision" / "judging"
OUT = ROOT / "reference" / "revision" / "packages"
CODEBOOK_PAGE = ROOT / "reference" / "revision" / "codebook_review" / "codebook-review.html"
CODEX_PDF = ROOT / "reference" / "revision" / "sources" / "Codex_CXG_45-2003.pdf"
MANIFEST = ROOT / "experiments" / "runs_rev" / "experiment_manifest.json"
CDN_TAG = '<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>'
EFSA_LINKS = [("EFSA Journal (Wiley)", "https://efsa.onlinelibrary.wiley.com/doi/10.2903/j.efsa.2022.7618"),
              ("Europe PMC 전문", "https://europepmc.org/article/PMC/PMC9583736")]

CSS = """
:root{--bg:#f5f7f6;--surface:#fff;--ink:#1c2422;--muted:#5a6662;--line:#d5dcd9;--accent:#24605a;--soft:#e0eeeb;--warn:#8a5a00;--warn-soft:#f8ecd2}
@media (prefers-color-scheme:dark){:root{--bg:#131917;--surface:#1a2220;--ink:#e4ebe8;--muted:#9aa7a2;--line:#2e3a37;--accent:#7cc4b6;--soft:#1d3330;--warn:#e8bf6a;--warn-soft:#3a2f17}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.7 "Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif}
main{max-width:860px;margin:0 auto;padding:32px 18px 64px;display:grid;gap:22px}
h1{font-size:1.7rem;line-height:1.3;margin:0}h2{font-size:1.15rem;margin:0 0 8px}p{margin:0}
.eyebrow{font-size:13px;letter-spacing:.06em;color:var(--muted);margin-bottom:6px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:18px 20px}
.steps{counter-reset:s;list-style:none;padding:0;margin:0;display:grid;gap:12px}
.steps li{counter-increment:s;display:grid;grid-template-columns:2.2em 1fr;gap:10px}
.steps li::before{content:counter(s);width:2em;height:2em;border-radius:50%;background:var(--accent);color:var(--surface);display:grid;place-items:center;font-weight:700}
ul.plain{margin:6px 0 0;padding-left:1.2em;display:grid;gap:4px}
.files{display:grid;gap:8px}.file{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;border-top:1px solid var(--line);padding-top:8px}
.file:first-child{border-top:0;padding-top:0}.file a{color:var(--accent);font-weight:700}.file span{color:var(--muted);font-size:14px}
a{color:var(--accent)}.steps li>.reports{grid-column:2}
.reports{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}.reports a{border:1px solid var(--accent);color:var(--accent);border-radius:8px;padding:6px 14px;text-decoration:none;font-weight:700}
.reports a:hover,.reports a:focus-visible{background:var(--soft)}
.warn{background:var(--warn-soft);border-color:var(--warn)}.warn h2{color:var(--warn)}
.foot{color:var(--muted);font-size:14px}
"""


def page(title: str, body: str) -> str:
    return (f'<!doctype html><html lang="ko"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>'
            f"<style>{CSS}</style></head><body><main>{body}</main></body></html>")


def file_row(href: str, label: str, desc: str) -> str:
    return f'<div class="file"><a href="{href}">{html.escape(label)}</a><span>{html.escape(desc)}</span></div>'


def sources_card() -> str:
    links = "".join(f'<li><a href="{u}">{html.escape(n)}</a></li>' for n, u in EFSA_LINKS)
    return ('<section class="card"><h2>기준 문헌</h2>'
            '<ul class="plain"><li><a href="sources/Codex_CAC-GL-45-2003.pdf">Codex CAC/GL 45-2003</a> '
            '(재조합 DNA 식물 유래 식품의 안전성 평가 지침, Annex II·III 2008 채택)</li>'
            '<li>EFSA Journal 2022;20(10):7618 (targeted mutagenesis, cisgenesis, intragenesis 식물의 위해성 평가 기준) '
            '— 저작권 때문에 파일 대신 공개 링크로 안내합니다:<ul class="plain">' + links + "</ul></li></ul></section>")


def copy_report(rid: str, dst: Path):
    (dst / "reports").mkdir(parents=True, exist_ok=True)
    text = (J / "reports" / f"{rid}.html").read_text(encoding="utf-8")
    if CDN_TAG not in text:
        raise SystemExit(f"{rid}.html: mermaid tag not found")
    (dst / "reports" / f"{rid}.html").write_text(text.replace(CDN_TAG, '<script src="../assets/mermaid.min.js"></script>'),
                                               encoding="utf-8")
    for suf in ("_en.md", "_ko.md"):
        shutil.copy2(J / "reports" / f"{rid}{suf}", dst / "reports" / f"{rid}{suf}")


def common(dst: Path, mermaid: Path):
    (dst / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy2(mermaid, dst / "assets" / "mermaid.min.js")
    (dst / "sources").mkdir(exist_ok=True)
    shutil.copy2(CODEX_PDF, dst / "sources" / "Codex_CAC-GL-45-2003.pdf")


def report_links(ids) -> str:
    return '<div class="reports">' + "".join(f'<a href="reports/{r}.html">{r}</a>' for r in ids) + "</div>"


def primary(dst: Path, ids, mermaid: Path):
    common(dst, mermaid)
    for r in ids:
        copy_report(r, dst)
    shutil.copy2(J / "primary_judge_sheet.xlsx", dst / "주판정_시트.xlsx")
    body = CODEBOOK_PAGE.read_text(encoding="utf-8")
    (dst / "기준표_codebook.html").write_text(
        '<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        + body + "</html>", encoding="utf-8")
    html_body = f"""
<header><p class="eyebrow">npj 리비전 · 주 판정자용</p><h1>지침 대조 판정 (L3·L4) 안내</h1>
<p style="margin-top:8px;color:var(--muted)">AI가 생성한 유전자편집식품 안전성 평가체계 보고서 10개를 EFSA 2022와 Codex CXG 45 기준으로 판정해 주세요.</p></header>
<section class="card"><h2>진행 순서</h2><ol class="steps">
<li><p><b>기준표 읽기.</b> <a href="기준표_codebook.html">기준표_codebook.html</a>에서 판정 방법과 30개 항목을 먼저 봐 주세요. 맨 위 "판정하시는 분께"와 "판정 시 유의할 점"이 요점입니다.</p></li>
<li><p><b>보고서 열기.</b> 아래 보고서를 브라우저로 엽니다. 영문 원문이 판정 기준이고 한국어는 참고용 자동 번역입니다. Methods 절은 전문가 패널(팀 구성)만 남기고 뺐습니다.</p>{report_links(ids)}</li>
<li><p><b>L3 판정.</b> <a href="주판정_시트.xlsx">주판정_시트.xlsx</a>의 "L3 판정" 시트에서 보고서마다 30개 항목의 반영 상태(드롭다운), 원인(해당 칸에 O), 근거 위치를 적습니다. "항목 비고"의 규칙을 우선 적용합니다.</p></li>
<li><p><b>중대 사례와 AI 추가 제안.</b> 필수 평가 생략, 근거 없는 면제, 불확실한 상태의 종료는 "중대 사례" 시트에, 기준표에 없는 제안은 "AI 추가 제안" 시트에 적습니다.</p></li>
<li><p><b>L4 구조.</b> "L4 구조" 시트에 판단 지점 17개의 분기를 한 행에 하나씩 기록하고, 같은 뜻의 표현은 "정규화 변환표"에 등록합니다.</p></li>
<li><p><b>회신.</b> 작성한 시트를 그대로 보내 주세요.</p></li>
</ol></section>
<section class="card"><h2>파일</h2><div class="files">
{file_row("기준표_codebook.html", "기준표_codebook.html", "판정 기준 (확정본 v1.0)")}
{file_row("주판정_시트.xlsx", "주판정_시트.xlsx", "L3 300행, 중대 사례, AI 추가 제안, L4, 정규화 변환표")}
{file_row("reports/", "reports/", "보고서 R01–R10 (HTML, 영문·한국어 md)")}
</div></section>
{sources_card()}
<section class="card warn"><h2>지켜 주실 것</h2><ul class="plain">
<li>판정은 직접 해 주세요. GPT·Claude 등 실험에 쓴 모델로 판정하지 않습니다. LLM으로 위치만 찾았다면 원문과 대조해 확정하고 비고에 적어 주세요.</li>
<li>보고서가 어느 조건에서 나왔는지는 판정이 끝날 때까지 알려 드리지 않습니다. 짐작되더라도 기준표대로만 판정해 주세요.</li>
<li>일부 보고서는 본문이 두 번 쓰여 있습니다. 보고서 전체를 한 단위로 판정하고, 반대되는 서술이면 상충입니다.</li>
<li>보고서는 출판 전까지 외부에 공유하지 말아 주세요.</li>
</ul></section>
<p class="foot">트리 그림은 인터넷 없이도 표시됩니다 (assets/mermaid.min.js 포함). 문의: 교신저자.</p>"""
    (dst / "index.html").write_text(page("주 판정자 안내", html_body), encoding="utf-8")


def second(dst: Path, ids, mermaid: Path):
    common(dst, mermaid)
    for r in ids:
        copy_report(r, dst)
    shutil.copy2(J / "second_judge_sheet.xlsx", dst / "2차판정_시트.xlsx")
    html_body = f"""
<header><p class="eyebrow">npj 리비전 · 2차 판정자용</p><h1>지침 대조 판정 (L3) 안내</h1>
<p style="margin-top:8px;color:var(--muted)">AI가 생성한 유전자편집식품 안전성 평가체계 보고서 3개를 EFSA 2022와 Codex CXG 45 기준으로 독립 판정해 주세요. 판정자 간 일치도 계산에 쓰입니다.</p></header>
<section class="card"><h2>진행 순서</h2><ol class="steps">
<li><p><b>판정 방법 읽기.</b> <a href="2차판정_시트.xlsx">2차판정_시트.xlsx</a>의 "안내" 시트에 반영 상태 5가지의 정의와 규칙이 있습니다.</p></li>
<li><p><b>보고서 열기.</b> 영문 원문이 판정 기준이고 한국어는 참고용입니다. Methods 절은 전문가 패널(팀 구성)만 남기고 뺐습니다.</p>{report_links(ids)}</li>
<li><p><b>판정.</b> "L3 판정" 시트에서 보고서마다 30개 항목의 반영 상태 하나를 드롭다운으로 고르고, 근거 위치를 적습니다. "항목 비고"의 규칙을 우선 적용합니다.</p></li>
<li><p><b>회신.</b> 작성한 시트를 그대로 보내 주세요.</p></li>
</ol></section>
<section class="card"><h2>파일</h2><div class="files">
{file_row("2차판정_시트.xlsx", "2차판정_시트.xlsx", "L3 90행 (보고서 3개 × 30항목)")}
{file_row("reports/", "reports/", "보고서 " + ", ".join(ids))}
</div></section>
{sources_card()}
<section class="card warn"><h2>독립성을 위해 지켜 주실 것</h2><ul class="plain">
<li>주 판정자의 판정 결과나 다른 분석 자료를 보지 않고, 다른 판정자와 상의하지 않습니다.</li>
<li>생성형 AI 도구로 판정하지 않습니다.</li>
<li>일부 보고서는 본문이 두 번 쓰여 있습니다. 보고서 전체를 한 단위로 판정하고, 반대되는 서술이면 상충입니다.</li>
<li>보고서는 출판 전까지 외부에 공유하지 말아 주세요.</li>
</ul></section>
<p class="foot">트리 그림은 인터넷 없이도 표시됩니다. 문의: 교신저자.</p>"""
    (dst / "index.html").write_text(page("2차 판정자 안내", html_body), encoding="utf-8")


def external(dst: Path, rid: str, mermaid: Path):
    common(dst, mermaid)
    copy_report(rid, dst)
    form = J / "external" / rid / f"외부전문가_평가서_{rid}.docx"
    shutil.copy2(form, dst / form.name)
    html_body = f"""
<header><p class="eyebrow">외부 전문가 평가</p><h1>AI 생성 안전성 평가체계 보고서 평가 안내</h1>
<p style="margin-top:8px;color:var(--muted)">생성형 AI 다중 에이전트 시스템이 작성한 유전자편집식품(NGT) 식품 안전성 평가체계 보고서 한 건을 전문가의 관점에서 독립적으로 평가해 주세요. 결과는 연구 논문의 외부 전문가 평가 절에 집계해 보고합니다.</p></header>
<section class="card"><h2>진행 순서 (약 3–4시간)</h2><ol class="steps">
<li><p><b>평가서 열기.</b> <a href="{form.name}">{html.escape(form.name)}</a>의 안내와 Part 0(이해상충·동의)을 먼저 작성해 주세요.</p></li>
<li><p><b>보고서 읽기.</b> 영문 원문이 평가 기준이고 한국어는 참고용 자동 번역입니다.</p>{report_links([rid])}</li>
<li><p><b>Part A.</b> 기준 항목 30개마다 보고서의 반영 상태를 고릅니다 (2–3시간).</p></li>
<li><p><b>Part B·C.</b> 다섯 측면의 1–5점 평가와 서술 의견을 적습니다 (약 50분).</p></li>
<li><p><b>회신.</b> 작성한 평가서(Word 파일)를 그대로 보내 주세요.</p></li>
</ol></section>
<section class="card"><h2>파일</h2><div class="files">
{file_row(form.name, form.name, "평가서 (Part 0, A, B, C)")}
{file_row(f"reports/{rid}.html", f"reports/{rid}.html", "평가 대상 보고서 (영문·한국어 전환)")}
</div></section>
{sources_card()}
<section class="card warn"><h2>독립성을 위해 지켜 주실 것</h2><ul class="plain">
<li>다른 평가자와 상의하지 말아 주세요.</li>
<li>판정과 점수는 직접 해 주세요. 생성형 AI 도구로 판정하거나 의견을 작성하지 말아 주세요.</li>
<li>평가가 끝날 때까지 연구진은 시스템 내부 점수, 저자 판정, 생성 조건을 알려 드리지 않습니다.</li>
<li>보고서와 평가서는 출판 전까지 외부에 공유하지 말아 주세요.</li>
</ul></section>
<p class="foot">트리 그림은 인터넷 없이도 표시됩니다. 문의: 교신저자.</p>"""
    (dst / "index.html").write_text(page("외부 전문가 평가 안내", html_body), encoding="utf-8")


def zip_dir(src: Path):
    zpath = src.with_suffix(".zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(src.rglob("*")):
            if f.is_file():
                z.write(f, Path(src.name) / f.relative_to(src))
    return zpath


def main() -> int:
    mermaid = Path(sys.argv[1])
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    ids = sorted(p.stem for p in (J / "reports").glob("R*.html"))
    second_ids = sorted({c.value for c in __import__("openpyxl").load_workbook(J / "second_judge_sheet.xlsx")["L3 판정"]["A"][1:]})
    ext_id = sorted(p.name for p in (J / "external").iterdir() if p.is_dir())[0]
    builds = {
        "1_주판정자_함준혁박사": lambda d: primary(d, ids, mermaid),
        "2_2차판정자": lambda d: second(d, second_ids, mermaid),
        "3_외부판정자_1": lambda d: external(d, ext_id, mermaid),
        "4_외부판정자_2": lambda d: external(d, ext_id, mermaid),
    }
    for name, fn in builds.items():
        d = OUT / name
        fn(d)
        bad = [f for f in d.rglob("*") if "blinding" in f.name.lower()]
        if bad:
            raise SystemExit(f"blinding file leaked into {name}: {bad}")
        z = zip_dir(d)
        n = sum(1 for f in d.rglob("*") if f.is_file())
        print(f"{name}: {n} files, {z.name} {z.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
