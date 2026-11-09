"""Build the public data package of the revision experiment (local only; publishes nothing).

    python -B scripts/revision/build_release.py [--out release/data_v1]

Scope
- Copies the gitignored run records (main_v1 = main results; pilot_v1; the replaced corpus-v0 set `main` and its
  pilots; logs; pilot analyses; extracted report content; retrieval snapshots) into --out, with DATA_README.md.
Third-party text
- Removed only where it was injected. Model outputs (responses, conversations, reports, scores, team selection) are
  never changed apart from the local path. In the snapshot files every `result`/`text` string is replaced by a marker
  (length, SHA-256) followed by the bibliographic lines of that result (titles, source labels, URLs). In calls.jsonl
  the excerpts are replaced inside `system_prompt` and `user_message`; logs are treated like prompts.
Checks (the package is written to a temporary folder and kept only if all pass)
- No 10-word sequence of excerpt prose remains in any non-output file or prompt field, except sequences that also
  occur in model outputs (an agent quoting a title or sentence, which then re-enters later prompts as part of that
  output); their number is reported. Model outputs quoting excerpt prose are listed, not changed. No API-key pattern, local path or "OneDrive" anywhere.
  Every listed source must exist.
RELEASE_MANIFEST.json records the commit SHA, this script's SHA-256 and arguments, the check results, and for every
file the SHA-256 of the published and the original version.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "experiments" / "runs_rev"
SOURCES = ["main_v1", "main_v1_logs", "pilot_v1", "pilot_v1_logs", "main", "main_logs", "pilot", "pilot_logs",
           "pilot_analysis_attempt02", "pilot_analysis_attempt03", "pilot_analysis_compare",
           "results/extracted", "results_v1/extracted",
           "retrieval_snapshot.json", "retrieval_snapshot_v1.json",
           "retrieval_snapshot_v1_first_top5_unused.json", "retrieval_snapshot_v1_float_pages_unused.json"]
SNAPSHOTS = [s for s in SOURCES if s.startswith("retrieval_snapshot")]
TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".log", ".txt", ".csv", ".html"}
OUTPUT_FILES = {"conversations.json", "messages.json", "critic_scores.json", "final_report.md", "final_report.ko.md",
                "team_selection.json"}
KEY = re.compile(r"sk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}|tvly-[A-Za-z0-9]{16,}|pcsk_[A-Za-z0-9_]{20,}")
NGRAM = 10
URL = re.compile(r"https?://\S+")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def is_biblio(line: str) -> bool:
    """Title, heading, source label or URL line of a retrieval result (kept as bibliographic data)."""
    s = line.strip()
    return bool(s) and len(s) < 300 and (s.startswith(("**", "#", "[Document]", "[Web]", "Source", "URL", "출처"))
                                         or bool(URL.search(s)) or s.startswith("### 문서"))


def words(text: str) -> list[str]:
    return re.findall(r"\w+", URL.sub(" ", text).lower())


def load_excerpts() -> list[tuple[str, str, str]]:
    out = []
    for name in SNAPSHOTS:
        for key, e in json.loads((RUNS / name).read_text(encoding="utf-8"))["entries"].items():
            if isinstance(e.get("result"), str) and e["result"].strip():
                out.append((name, key, e["result"]))
    out.sort(key=lambda x: -len(x[2]))
    return out


def marker(where: str, text: str) -> str:
    return f"[THIRD-PARTY EXCERPT REMOVED: {where} chars={len(text)} sha256={sha(text.encode('utf-8'))}]"


class Redactor:
    def __init__(self, excerpts):
        self.ex = excerpts
        self.lines, seen = [], set()
        grams = set()
        for snap, key, text in excerpts:
            for ln in text.split("\n"):
                s = ln.strip()
                if s and not is_biblio(s):
                    if len(s) >= 40 and s not in seen:
                        seen.add(s)
                        self.lines.append((s, marker(f"{snap} entry={key} line", s)))
                    w = words(s)
                    grams |= {tuple(w[i:i + NGRAM]) for i in range(len(w) - NGRAM + 1)}
        biblio = set()
        for _, _, text in excerpts:
            for ln in text.split("\n"):
                if is_biblio(ln):
                    w = words(ln)
                    biblio |= {tuple(w[i:i + NGRAM]) for i in range(len(w) - NGRAM + 1)}
        self.lines.sort(key=lambda x: -len(x[0]))
        self.grams = grams - biblio  # titles and labels kept on purpose are not leftovers
        self.count = {"whole_results": 0, "lines": 0, "snapshot_fields": 0}

    def text(self, s: str) -> str:
        for snap, key, t in self.ex:
            if t in s:
                self.count["whole_results"] += s.count(t)
                s = s.replace(t, marker(f"{snap} entry={key}", t))
        for ln, m in self.lines:
            if ln in s:
                self.count["lines"] += s.count(ln)
                s = s.replace(ln, m)
        return s

    def residual(self, s: str, include_quoted: bool = False) -> str | None:
        grams = self.grams if include_quoted else getattr(self, "grams_checked", self.grams)
        w = words(s)
        for i in range(len(w) - NGRAM + 1):
            if tuple(w[i:i + NGRAM]) in grams:
                return " ".join(w[i:i + NGRAM])
        return None


def walk(obj, fn):
    if isinstance(obj, str):
        return fn(obj)
    if isinstance(obj, list):
        return [walk(v, fn) for v in obj]
    if isinstance(obj, dict):
        return {k: walk(v, fn) for k, v in obj.items()}
    return obj


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from strings(v)


DATA_README = """# Data package: revision experiment (scoring-protocol comparison)

Companion to the code repository https://github.com/baesisi3648/pjt-virtual_lab (same release tag). Unpack at the
repository root so that the files land in `experiments/runs_rev/`.

## Contents
- `main_v1/` — **main results**: ten runs (A_1–A_5 revised protocol, B_1–B_5 comparison protocol), corpus v1,
  experiment manifest `experiment_manifest_v2.json` (in the code repository). One folder per run and attempt with
  `calls.jsonl` (every model call with request parameters, response identifiers, usage and full response text),
  `conversations.json`, `messages.json`, `critic_scores.json` (per round, specialist and dimension), `team_selection.json`,
  `meta.json` and the final reports (`final_report.md`, Korean translation `final_report.ko.md`). `main_v1_logs/`
  holds the console logs and the pre-run API checks.
- `pilot_v1/` — pilot runs with corpus v1, not part of the analysis.
- `main/`, `pilot/` — an earlier set of main runs and pilots with the corpus-v0 index, replaced after an audit found
  placeholder documents in that index. Kept as a record (amendment and exclusions in `RUN_LOG.md`).
- `pilot_analysis_*`, `results/extracted`, `results_v1/extracted` — pilot analyses and the safety-content extractions
  used for the similarity analysis.
- `retrieval_snapshot*.json` — the fixed retrieval inputs (v1 used in the main runs; v0 for the replaced set; two
  unused v1 variants that document the change of the RAG selection rule).

## Removed third-party text
Retrieval results (web pages, EFSA Journal records and RAG chunks of regulatory documents) are third-party text under
different terms. They were removed where they were injected, namely in the snapshot files and in the `system_prompt` and
`user_message` fields of `calls.jsonl`, and replaced by markers giving the length and SHA-256 of the removed text. The
titles, source labels and URLs of each result are kept after the marker in the snapshot files. Model outputs are
unchanged. The local repository path was replaced by `<repo>`. `RELEASE_MANIFEST.json` lists every file with the SHA-256
of the published and of the original version.

Consequences: the prompts cannot be replayed exactly from this package. RAG chunks can be regenerated from the public
source documents with `scripts/revision/build_corpus_v1.py` (document hashes, chunk-ID sets and the hash of all chunks
are in `experiments/runs_rev/corpus_v1/corpus_manifest.json`) and compared with the hashes in the markers. Web and EFSA
Journal results can be consulted at their URLs, but the excerpts returned by the search API cannot be regenerated.

## Levels of reproduction
1. Re-analysis of the saved outputs (no API): scores, rounds, decreases, the tables of the paper
   (`experiments/reproducibility/analyze_revision.py`, results in `experiments/runs_rev/results_v1/`). The similarity
   matrices are published as CSV; recomputing them requires the OpenAI embedding API (text-embedding-3-large).
2. Re-running the pipeline requires API access to the generation and Critic models and the retrieval inputs (see above);
   new runs are not expected to reproduce the outputs exactly.

## Licences
Records and outputs produced by the authors: CC BY 4.0. Code: MIT (code repository). Third-party documents and their
excerpts are not covered by these licences.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="release/data_v1")
    a = ap.parse_args()
    out = (ROOT / a.out).resolve()
    tmp = out.with_name(out.name + ".building")
    missing = [s for s in SOURCES if not (RUNS / s).exists()]
    if missing:
        print("missing inputs:", missing)
        return 1
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    red = Redactor(load_excerpts())
    # Excerpt n-grams that also occur in model outputs may come back into later prompts through those outputs
    # (e.g. a document title quoted by an agent). They are reported, not treated as injection leftovers.
    out_grams = set()
    for src in SOURCES:
        base = RUNS / src
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if p.name in OUTPUT_FILES:
                w = words(p.read_text(encoding="utf-8"))
            elif p.name == "calls.jsonl":
                w = []
                for ln in p.read_text(encoding="utf-8").splitlines():
                    if ln.strip():
                        w += words(json.loads(ln).get("response_text") or "") + ["|"]
            else:
                continue
            out_grams |= {tuple(w[i:i + NGRAM]) for i in range(len(w) - NGRAM + 1)} & red.grams
    red.quoted_grams = out_grams
    red.grams_checked = red.grams - out_grams
    root_variants = sorted({str(ROOT), str(ROOT).replace("\\", "/"), str(ROOT).replace("\\", "\\\\")}, key=len, reverse=True)

    def clean_path(s: str) -> str:
        for v in root_variants:
            s = s.replace(v, "<repo>")
        return s

    def snap_fn(obj, where, key=None):
        if isinstance(obj, dict):
            return {k: snap_fn(v, where, k) for k, v in obj.items()}
        if isinstance(obj, list):
            return [snap_fn(v, where, key) for v in obj]
        if isinstance(obj, str) and key in ("result", "text") and obj.strip():
            red.count["snapshot_fields"] += 1
            biblio = [ln.strip() for ln in obj.split("\n") if is_biblio(ln)]
            return "\n".join([marker(f"{where} field={key}", obj)] + biblio)
        return clean_path(obj) if isinstance(obj, str) else obj

    files, problems, quoted = [], [], []
    for src in SOURCES:
        base = RUNS / src
        items = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file())
        for p in items:
            rel = p.relative_to(RUNS)
            dst = tmp / "experiments" / "runs_rev" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            raw = p.read_bytes()
            pub = raw
            if p.suffix in TEXT_SUFFIXES:
                t = raw.decode("utf-8")
                must_be_clean = []
                if src in SNAPSHOTS:
                    t2 = json.dumps(snap_fn(json.loads(t), rel.name), ensure_ascii=False, indent=2)
                    must_be_clean.append(t2)
                elif p.suffix == ".jsonl":
                    lines = []
                    for ln in t.splitlines():
                        if not ln.strip():
                            lines.append(ln)
                            continue
                        d = json.loads(ln)
                        for f in ("system_prompt", "user_message"):
                            if isinstance(d.get(f), str):
                                d[f] = red.text(d[f])
                        d = walk(d, clean_path)
                        must_be_clean += [v for k, v in d.items() if k != "response_text" for v in strings(v)]
                        lines.append(json.dumps(d, ensure_ascii=False))
                    t2 = "\n".join(lines) + ("\n" if t.endswith("\n") else "")
                elif p.suffix == ".log":
                    t2 = clean_path(red.text(t))
                    must_be_clean.append(t2)
                else:  # bytes kept except the local path
                    t2 = clean_path(t)
                    if p.name not in OUTPUT_FILES:
                        must_be_clean.append(t2)
                for c in must_be_clean:
                    w = red.residual(c)
                    if w:
                        problems.append(f"excerpt prose remains in {rel}: {w[:60]!r}")
                        break
                if p.name in OUTPUT_FILES and red.residual(t2, include_quoted=True):
                    quoted.append(str(rel).replace("\\", "/"))
                if KEY.search(t2):
                    problems.append(f"key-like string in {rel}")
                if any(v in t2 for v in root_variants) or "OneDrive" in t2:
                    problems.append(f"local path in {rel}")
                pub = t2.encode("utf-8")
            dst.write_bytes(pub)
            files.append({"path": str(Path("experiments/runs_rev") / rel).replace("\\", "/"),
                          "sha256": sha(pub), "original_sha256": sha(raw), "modified": pub != raw})
    (tmp / "DATA_README.md").write_text(DATA_README, encoding="utf-8")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "scripts/revision/build_release.py"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    manifest = {"code_commit": commit, "builder": "scripts/revision/build_release.py",
                "builder_sha256": sha(Path(__file__).read_bytes()), "builder_uncommitted": bool(dirty),
                "arguments": vars(a), "checks": {"passed": not problems, "problems": problems,
                                                 "model_outputs_quoting_excerpt_prose": quoted,
                                                 "excerpt_ngrams_total": len(red.grams),
                                                 "excerpt_ngrams_also_in_model_outputs": len(red.quoted_grams),
                                                 "ngram_words": NGRAM},
                "redactions": red.count, "files": files}
    (tmp / "RELEASE_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    size = sum(p.stat().st_size for p in tmp.rglob("*") if p.is_file())
    print(f"files {len(files)}, modified {sum(f['modified'] for f in files)}, size {size / 1e6:.1f} MB, "
          f"redactions {red.count}, outputs quoting excerpt prose {len(quoted)}")
    if problems:
        shutil.rmtree(tmp)
        print("FAILED, nothing kept:", *problems[:30], sep="\n  ")
        return 1
    if out.exists():
        shutil.rmtree(out)
    tmp.rename(out)
    print("checks passed:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
