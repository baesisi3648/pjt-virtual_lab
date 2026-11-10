"""L4 candidate extraction from the blinded reports. Deterministic: no LLM.

Copies Mermaid nodes and branches verbatim and locates, by fixed keyword rules,
candidates for each of the 17 decision points in the trees and in the Core
Question 4-5 text. Nothing here is a judgement; the primary judge confirms
every report.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reference" / "revision" / "judging_v1" / "reports"

KEYWORDS = {  # candidate location only
    "CB01": r"\bclassification\b",
    "CB03": r"foreign|exogenous|residual (dna|editor|exogenous|process|template|vector|guide)|\bdelivery\b|repair template|template (used|or)|diet.relevant sequence|transgene|\bvector",
    "CB04": r"gene.?pool|transgenic|\bgmo\b",
    "CB05": r"safe.?harbou?r|targeted (insertion|integration)|random (insertion|integration)|integration (site|type)",
    "CB06": r"disrupt|interrupt",
    "CB11": r"off.?target|unintended|genome.wide|integrity trigger|structural concern",
    "CB13": r"history.of.safe|\bhosu\b|familiar|safe use",
    "CB14": r"\ballele|protein variant|altered protein|protein change|endogenous protein|protein in edible part altered|sequence altered|amino.acid|alters a protein|orf/splice|functional concern",
    "CB16": r"toxi",
    "CB19": r"allergen|novel protein|new protein|new or altered protein|novel or materially|novel.or.altered|novelty in edible|junction dna|hybrid orf|junction orf",
    "CB20": r"\bige\b|\bser(a|um)\b",
    "CB22": r"comparator|compositi|constituent|analyte",
    "CB24": r"\b(no|without|lack|absent|alternative|multiple)\b.{0,20}comparator|comparator.{0,20}\b(unavailable|absent|alternative)\b|stand.?alone",
    "CB27": r"multiplex|stack|multiple (edit|modif|site)",
    "CB28": r"whole.?food|90.?day|animal (stud|test|feed)|\bfeeding",
    "CB29": r"antibiotic|\bmarker gene|selectable marker",
    "CB30": r"\bre.?evaluat|\bre.?assess|new (information|data|evidence)|post.?market|\bmonitoring",
}
SHAPE = r'(?:\[\[|\{\{|\[|\{|\(\(|\()"?(.*?)"?(?:\]\]|\}\}|\]|\}|\)\)|\))'
NODE = re.compile(r"([A-Za-z_]\w*)\s*" + SHAPE + r'(?=\s*(?:-|$|;))')
ARROW = re.compile(r'\s*(?:-->\s*\|"?(.*?)"?\||--\s*"?([^->|]+?)"?\s*-->|-->)\s*')
CONDITIONAL = r"\b(if|when|where|unless|only|whether|absent|until)\b"


def norm(s):
    return re.sub(r"\s+", " ", s.replace("—", "-").replace("‑", "-")).strip()


def trees(text):
    """Return (tree name, occurrence number, Mermaid body) for every diagram."""
    head, seen, out = "Tree", {}, []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("#"):
            head = norm(s.lstrip("# "))
        if s.startswith("```mermaid"):
            j = i + 1
            while not lines[j].strip().startswith("```"):
                j += 1
            seen[head] = seen.get(head, 0) + 1
            out.append((head, seen[head], "\n".join(lines[i + 1:j])))
            i = j
        i += 1
    return out


def parse(body):
    """Return node labels and edges, including chained arrows on one line."""
    nodes, edges = {}, []
    for line in body.split("\n"):
        line = line.strip()
        if not line or line.startswith(("graph", "flowchart", "%%", "style", "classDef", "class ", "subgraph", "end")):
            continue
        for m in NODE.finditer(line):
            nodes[m.group(1)] = norm(m.group(2))
        bare = NODE.sub(lambda m: m.group(1), line)
        parts = ARROW.split(bare)  # id, label1, label2, id, ...
        for k in range(0, len(parts) - 3, 3):
            src, label = parts[k].strip(), parts[k + 1] or parts[k + 2] or ""
            edges.append((src, norm(label), parts[k + 3].strip()))
    return nodes, edges


def outcome(label, terminal):
    low = label.lower()
    if re.search(r"additional data|further data|more data|request.{0,20}data|defer", low):
        return "추가 자료 요구·판단 보류"
    if terminal and re.search(r"complete|\bend\b|conclu", low):
        return "종료"
    return "추가 평가"


def target_class(label):
    low = re.sub(r"\(.*?\)", "", label).lower()  # parenthetical examples do not define the target
    for pat, name in [
        (r"additional data|further data|more data", "추가 자료"),
        (r"assessment complete|^end\b|conclu", "평가 완료"),
        (r"allergen|\bige\b|serum", "알레르기성"),
        (r"toxi", "독성"),
        (r"protein|orf", "단백질 평가"),
        (r"compositi|comparator|nutrition|metabolite|analyte|constituent", "성분·영양"),
        (r"off.?target|unintended|variant|genome.wide|integrity", "비의도 변이"),
        (r"foreign|exogenous|residual|vector|insert|junction|template|locus|sequence|stability|inherit", "분자 특성"),
        (r"exposure|dietary", "노출"),
    ]:
        if re.search(pat, low):
            return name
    return "기타"


def report_trees(rid):
    """Unique diagrams of a report by content: repeats count once, different ones are kept."""
    text = (REPORTS / f"{rid}_en.md").read_text(encoding="utf-8")
    seen, out = set(), []
    for head, k, body in trees(text):
        nodes, edges = parse(body)
        sig = (tuple(sorted(nodes.items())), tuple(sorted(edges)))
        if sig in seen:
            continue
        seen.add(sig)
        out.append((head + (f" (2판 {k})" if k > 1 else ""), nodes, edges))
    return text, out


def tree_hits(all_trees, pat):
    """Candidates in the trees; the same label with different branches is kept apart."""
    hits, seen = [], set()
    for head, nodes, edges in all_trees:
        sources = {s for s, _, _ in edges}
        for nid, label in nodes.items():
            if not re.search(pat, label, re.I):
                continue
            branches = [(l, nodes.get(t, t), outcome(nodes.get(t, t), t not in sources)) for s, l, t in edges if s == nid]
            key = (label.lower(), tuple(sorted((a.lower(), b.lower(), c) for a, b, c in branches)))
            if key in seen:
                continue
            seen.add(key)
            hits.append({"tree": head, "node": nid, "label": label, "branches": branches})
    hits.sort(key=lambda h: (len(h["branches"]) < 2, not h["tree"].startswith("Integrated")))
    return hits


def text_hits(text, pat, limit=3):
    """Conditional sentences in every Core Question 4-5 body, with the nearest heading or step."""
    place, seen, out = "", set(), []
    for m in re.finditer(r"## Core Question 4.*?(?=\n## (?:References|Decision Tree)|\Z)", text, re.S):
        for line in m.group(0).split("\n"):
            s = line.strip()
            h = re.match(r"#+\s*(?:Core Question )?(.*)", s)
            if h:
                place = "CQ" + norm(h.group(1))[:1]
                continue
            step = re.match(r"[*\-\s]*(Step\s*\d)", s)
            if step:
                place = "CQ5 " + step.group(1)
            for sent in re.split(r"(?<=\.)\s+", s):
                t = norm(sent)
                if t in seen or len(t) < 30 or not re.search(pat, t, re.I) or not re.search(CONDITIONAL, t, re.I):
                    continue
                seen.add(t)
                out.append({"place": place, "text": t})
    return out[:limit]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for rid in sorted(p.name[:3] for p in REPORTS.glob("R*_en.md")):
        text, ts = report_trees(rid)
        raw = sum(len(re.findall(r"-->", b)) for _, _, b in trees(text))
        parsed = sum(len(parse(b)[1]) for _, _, b in trees(text))
        print(rid, "diagrams", len(ts), "arrows", raw, "parsed", parsed)
