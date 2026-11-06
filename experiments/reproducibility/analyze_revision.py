"""Analysis of the revision A/B runs (revision_plan section 11 / 0.4: L1, L2, L8;
C10, C17; representative-run rule of 7.3).

The submitted-version script `analyze.py` is left unchanged so that the original
figures can still be regenerated.

Usage:
    python -B -m experiments.reproducibility.analyze_revision \
        --runs-dir experiments/runs_rev/main --out-dir experiments/runs_rev/results
    (add --skip-embeddings to compute everything except semantic similarity)

Inputs: <runs-dir>/<COND>_<RUN>/attempt_NN/ with meta.json, final_report.md,
critic_scores.json, calls.jsonl. Exactly one attempt per run must have status "ok";
failed attempts are counted and reported, never analysed as results.

Outputs (out-dir):
    runs.json                    included runs, attempts, failed attempts, issues
    extracted/<COND>_<RUN>.md    safety-content text used for the primary similarity
    similarity_content.csv / similarity_full.csv   cosine matrices (A runs first)
    similarity_summary.json      within-A, within-B, A-B pairs: mean, SD, min, max (descriptive)
    representative.json          condition-A medoid run (7.3)
    critic_by_round.csv          per condition, round, axis: mean, SD (NA if n<2), n runs
    critic_per_run.csv           per run, round, axis: specialist-mean score
    critic_run_summary.csv       per run: rounds, all-5 reached, score decreases
    leakage_audit.json           condition-A Critic inputs scanned for residual score mentions
    figures/critic_trajectory.png, figures/similarity_content.png
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from statistics import mean, pstdev

import numpy as np

AXES = ("evidence", "universality", "proportionality", "readability")
CONDITIONS = ("A", "B")
RUN_DIR = re.compile(r"^(?P<cond>[A-Z])_(?P<run>[^/\\]+)$")

# Report sections that carry the safety-assessment content (C17). Methods,
# execution statistics, score charts and reference lists are template-driven and
# excluded from the primary similarity input.
CONTENT_SECTIONS = re.compile(r"^(core question\s*\d|decision tree)", re.IGNORECASE)
# Template subsections that can end up inside a kept section (e.g. the execution
# statistics table appended at the end of the submitted reports).
TEMPLATE_SUBSECTIONS = re.compile(
    r"^(execution statistics|critic score trajectory|per-agent contribution|team composition|"
    r"specialist self-introductions|statistical team composition)", re.IGNORECASE)


# --------------------------------------------------------------------------- loading

def load_runs(runs_dir: Path, conditions=CONDITIONS, excluded: list | None = None) -> tuple[list[dict], list[str]]:
    """`excluded`, if given, receives runs without exactly one successful attempt and their reasons."""
    runs, issues = [], []
    for d in sorted(runs_dir.iterdir()) if runs_dir.exists() else []:
        m = RUN_DIR.match(d.name)
        if not d.is_dir() or not m or m["cond"] not in conditions:
            continue
        attempts = sorted(a for a in d.glob("attempt_*") if a.is_dir())
        metas = {a: json.loads((a / "meta.json").read_text(encoding="utf-8"))
                 for a in attempts if (a / "meta.json").exists()}
        ok = [a for a, meta in metas.items() if meta.get("status") == "ok"]
        failed = [{"attempt": a.name, "status": meta.get("status"),
                   "error_type": (meta.get("error") or {}).get("type"),
                   "error": ((meta.get("error") or {}).get("message") or "")[:300]}
                  for a, meta in metas.items() if meta.get("status") != "ok"]
        no_meta = [a.name for a in attempts if a not in metas]
        if no_meta:
            issues.append(f"{d.name}: attempts without meta.json: {no_meta}")
        if len(ok) != 1:
            issues.append(f"{d.name}: expected exactly one successful attempt, found {len(ok)}")
            if excluded is not None:
                excluded.append({"name": d.name, "successful_attempts": [a.name for a in ok],
                                 "failed_attempts": failed, "attempts_without_meta": no_meta})
            continue
        a = ok[0]
        scores = json.loads((a / "critic_scores.json").read_text(encoding="utf-8"))
        rounds = sorted(int(sn["round"]) for sn in scores)
        if rounds != list(range(1, len(rounds) + 1)) or metas[a].get("rounds_completed") != len(rounds):
            issues.append(f"{d.name}: score rounds {rounds} inconsistent with meta rounds_completed "
                          f"{metas[a].get('rounds_completed')}")
        runs.append({
            "name": d.name, "condition": m["cond"], "run_id": m["run"], "attempt": a.name,
            "dir": a, "meta": metas[a], "failed_attempts": failed,
            "report": (a / "final_report.md").read_text(encoding="utf-8"),
            "scores": scores,
        })
    runs.sort(key=lambda r: (r["condition"], _natural(r["run_id"])))
    return runs, issues


def _natural(s: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


# --------------------------------------------------------------------------- C17 content extraction

def extract_content(report: str) -> str:
    """Keep only the '## Core Question ...' and '## Decision Tree' sections."""
    parts = re.split(r"(?m)^(?=## )", report)
    kept = []
    for part in parts:
        heading, _, body = part.partition("\n")
        heading = heading.lstrip("#").strip()
        if not (part.startswith("## ") and CONTENT_SECTIONS.match(heading)):
            continue
        # Remove template subsections ("### Execution Statistics", ...) inside the section.
        subs = re.split(r"(?m)^(?=#{3,} )", body)
        body = "".join(x for x in subs
                       if not (x.startswith("###") and TEMPLATE_SUBSECTIONS.match(x.split("\n", 1)[0].lstrip("#").strip())))
        # Skip placeholder stubs such as "[Conclusions presented above in Core Question 1.]"
        # that the PI sometimes repeats after the decision trees.
        stub = re.sub(r"[-\s]+", " ", body).strip()
        if not stub or re.fullmatch(r"\[[^\]]*\]", stub):
            continue
        kept.append(("## " + heading + "\n" + body).strip())
    text = "\n\n".join(kept)
    # Drop any score chart that may have been placed inside a kept section.
    return re.sub(r"```mermaid\s*\nxychart-beta.*?```", "", text, flags=re.DOTALL).strip()


# --------------------------------------------------------------------------- L1 similarity

def cosine_matrix(emb: np.ndarray) -> np.ndarray:
    normed = emb / np.clip(np.linalg.norm(emb, axis=1, keepdims=True), 1e-12, None)
    return normed @ normed.T


def summarize_pairs(matrix: np.ndarray, names: list[str], conds: list[str]) -> dict:
    """Descriptive statistics of pairwise similarities (pairs share runs; no tests)."""
    groups = {"within_A": [], "within_B": [], "A_vs_B": []}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            key = "A_vs_B" if conds[i] != conds[j] else f"within_{conds[i]}"
            if key in groups:
                groups[key].append(float(matrix[i, j]))
    out = {}
    for k, v in groups.items():
        out[k] = ({"pairs": len(v), "mean": mean(v), "sd_population": pstdev(v), "min": min(v), "max": max(v)}
                  if v else {"pairs": 0})
    out["note"] = "Pairs share runs and are not independent observations; values are descriptive only."
    return out


def medoid(matrix: np.ndarray, names: list[str], conds: list[str], condition: str = "A") -> dict:
    """7.3: the run with the highest mean similarity to the other runs of the condition."""
    idx = [i for i, c in enumerate(conds) if c == condition]
    if len(idx) < 2:
        return {"condition": condition, "representative": names[idx[0]] if idx else None,
                "note": "fewer than two runs"}
    scores = {names[i]: float(np.mean([matrix[i, j] for j in idx if j != i])) for i in idx}
    best = max(scores.values())
    tied = [n for n in (names[i] for i in idx) if scores[n] == best]
    tied.sort(key=lambda n: _natural(n.split("_", 1)[1]))  # tie: smaller run number
    return {"condition": condition, "representative": tied[0], "mean_similarity_to_others": scores,
            "rule": "highest mean content similarity to the other runs; ties -> smaller run number"}


# --------------------------------------------------------------------------- L2 critic scores

def per_run_round_axis(scores: list[dict]) -> dict[int, dict[str, float]]:
    out = {}
    for snap in scores:
        rnd = int(snap["round"])
        vals = {a: [int(s[a]) for s in snap["scores"].values()] for a in AXES}
        out[rnd] = {a: mean(v) for a, v in vals.items()}
    return out


def run_summary(run: dict) -> dict:
    snaps = sorted(run["scores"], key=lambda s: int(s["round"]))
    decreases = 0
    for prev, cur in zip(snaps, snaps[1:]):
        for role, axes in cur["scores"].items():
            for a in AXES:
                if role in prev["scores"] and axes[a] < prev["scores"][role][a]:
                    decreases += 1
    last = snaps[-1]["scores"] if snaps else {}
    return {"run": run["name"], "condition": run["condition"], "rounds": len(snaps),
            "all_five_reached": bool(last) and all(v == 5 for ax in last.values() for v in ax.values()),
            "score_decreases": decreases, "failed_attempts": len(run["failed_attempts"])}


def condition_summary(runs: list[dict]) -> dict:
    out = {}
    for cond in CONDITIONS:
        rs_ = [run_summary(r) for r in runs if r["condition"] == cond]
        dist: dict[int, int] = {}
        for r in rs_:
            dist[r["rounds"]] = dist.get(r["rounds"], 0) + 1
        out[cond] = {"runs": len(rs_), "termination_round_distribution": dict(sorted(dist.items())),
                     "all_five_reached_runs": sum(r["all_five_reached"] for r in rs_),
                     "score_decreases_total": sum(r["score_decreases"] for r in rs_)}
    return out


def aggregate_by_round(runs: list[dict]) -> list[dict]:
    rows = []
    for cond in CONDITIONS:
        per_run = [per_run_round_axis(r["scores"]) for r in runs if r["condition"] == cond]
        for rnd in sorted({k for pr in per_run for k in pr}):
            for a in AXES:
                vals = [pr[rnd][a] for pr in per_run if rnd in pr]
                rows.append({"condition": cond, "round": rnd, "axis": a, "n_runs": len(vals),
                             "mean": mean(vals),
                             "sd_population": pstdev(vals) if len(vals) >= 2 else None})
    return rows


# --------------------------------------------------------------------------- leakage audit (0.4 L2 note)

DETECTORS = [
    re.compile(r"\b[1-5](?:\.\d)?\s*/\s*5\b"),
    re.compile(r"\b(?:evidence|universality|proportionality|readability|score[sd]?|rated|rating)\b"
               r"[^\n]{0,30}?(?<![\w.])[1-5](?:\.\d)?(?![\w%])", re.IGNORECASE),
]


# Fixed instruction text in the Critic message (a target, not a prior score).
FIXED_PHRASES = ('"concrete actions to reach 5/5"',)


def leakage_audit(runs: list[dict], max_examples_per_run: int | None = None) -> dict:
    """Scan condition-A Critic inputs for score-like text left after masking.

    The detector is deliberately broad (it also flags phrases such as
    "Evidence from 3 studies"), so every hit must be reviewed by hand; the
    examples carry the call ID and an empty "manual_judgement" field for that.
    Hit counts are candidate mentions, not confirmed leaks. A run whose call log
    is missing, or whose logged Critic rounds do not cover every scored round,
    is reported as not auditable rather than as zero hits.
    """
    report = {"runs": {}, "examples": [], "note": leakage_audit.__doc__.strip().split("\n\n")[1]}
    for run in runs:
        if run["condition"] != "A":
            continue
        calls = run["dir"] / "calls.jsonl"
        scored_rounds = {int(sn["round"]) for sn in run["scores"]}
        if not calls.exists():
            report["runs"][run["name"]] = {"auditable": False, "reason": "calls.jsonl missing"}
            continue
        hits = masked = n_calls = examples = 0
        audited_rounds = set()
        for line in calls.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            tag = row.get("tag") or {}
            if tag.get("agent") != "Critic":
                continue
            n_calls += 1
            if tag.get("round") is not None:
                audited_rounds.add(int(tag["round"]))
            text = row.get("user_message", "")
            for phrase in FIXED_PHRASES:
                text = text.replace(phrase, "")
            masked += text.count("[score]")
            spans = sorted({(mt.start(), mt.end()) for det in DETECTORS for mt in det.finditer(text)})
            merged: list[list[int]] = []
            for a, b in spans:  # overlapping detector matches count once
                if merged and a <= merged[-1][1]:
                    merged[-1][1] = max(merged[-1][1], b)
                else:
                    merged.append([a, b])
            hits += len(merged)
            for a, b in merged:
                if max_examples_per_run is None or examples < max_examples_per_run:
                    examples += 1
                    report["examples"].append({
                        "run": run["name"], "round": tag.get("round"), "call_id": row.get("call_id"),
                        "context": text[max(0, a - 60):b + 60].replace("\n", " "), "manual_judgement": None})
        missing = sorted(scored_rounds - audited_rounds)
        report["runs"][run["name"]] = {
            "auditable": not missing and n_calls > 0, "missing_rounds": missing, "critic_calls": n_calls,
            "masked_tokens": masked, "candidate_mentions": hits}
    return report


# --------------------------------------------------------------------------- outputs

def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def _write_matrix(path: Path, matrix: np.ndarray, names: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([""] + names)
        for n, row in zip(names, matrix):
            w.writerow([n] + [f"{v:.4f}" for v in row])


def plot_trajectories(runs: list[dict], out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    colors = {"evidence": "#1f77b4", "universality": "#2ca02c", "proportionality": "#d62728",
              "readability": "#9467bd"}
    for ax, cond in zip(axes, CONDITIONS):
        cruns = [r for r in runs if r["condition"] == cond]
        for r in cruns:
            pr = per_run_round_axis(r["scores"])
            for a in AXES:
                xs = sorted(pr)
                ax.plot(xs, [pr[x][a] for x in xs], color=colors[a], alpha=0.25, linewidth=0.8)
        agg = [row for row in aggregate_by_round(runs) if row["condition"] == cond]
        for a in AXES:
            rows = [row for row in agg if row["axis"] == a]
            ax.plot([row["round"] for row in rows], [row["mean"] for row in rows], marker="o",
                    color=colors[a], label=a.capitalize(), linewidth=2)
        for row in [row for row in agg if row["axis"] == AXES[0]]:
            ax.annotate(f"n={row['n_runs']}", (row["round"], 1.15), ha="center", fontsize=8)
        ax.set_title(f"Condition {cond} ({len(cruns)} runs)")
        ax.set_xlabel("Round")
        ax.set_ylim(1, 5.3)
    axes[0].set_ylabel("Critic score (specialist mean)")
    axes[1].legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)


def plot_matrix(matrix: np.ndarray, names: list[str], out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(matrix, vmin=min(0.8, float(matrix.min())), vmax=1.0, cmap="viridis")
    ax.set_xticks(range(len(names)), names, rotation=90, fontsize=7)
    ax.set_yticks(range(len(names)), names, fontsize=7)
    fig.colorbar(im, ax=ax, label="cosine similarity")
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)


def analyse(runs_dir: Path, out_dir: Path, embed=None, expected_per_condition: int | None = 5) -> dict:
    """Run all analyses. `embed(texts) -> (n, d) array` may be injected (tests).

    The output directory must be new or empty, so results of an earlier analysis
    can never be mistaken for the current one.
    """
    if not runs_dir.is_dir():
        raise SystemExit(f"runs directory not found: {runs_dir}")
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit(f"output directory is not empty: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "figures").mkdir(exist_ok=True)
    (out_dir / "extracted").mkdir(exist_ok=True)
    excluded: list[dict] = []
    runs, issues = load_runs(runs_dir, excluded=excluded)
    counts = {c: sum(r["condition"] == c for r in runs) for c in CONDITIONS}
    # expected_per_condition=None disables the completeness check (tests, partial previews).
    complete = expected_per_condition is None or all(n == expected_per_condition for n in counts.values())
    if not complete:
        issues.append(f"incomplete main set: {counts} (expected {expected_per_condition} per condition)")

    extracted = {}
    for r in runs:
        text = extract_content(r["report"])
        if not text:
            issues.append(f"{r['name']}: no content sections found in final_report.md")
        (out_dir / "extracted" / f"{r['name']}.md").write_text(text, encoding="utf-8")
        extracted[r["name"]] = {"chars": len(text), "sha256": hashlib.sha256(text.encode()).hexdigest(),
                                "report_sha256": hashlib.sha256(r["report"].encode()).hexdigest()}
        r["content"] = text
    sim_runs = [r for r in runs if r["content"]]  # empty extractions never enter similarity
    if len(sim_runs) != len(runs):
        complete = False
        issues.append(f"{len(runs) - len(sim_runs)} run(s) have no extractable content; similarity and the "
                      f"representative run are provisional")
    names = [r["name"] for r in sim_runs]
    conds = [r["condition"] for r in sim_runs]

    summary = {"complete_main_set": complete, "runs_per_condition": counts, "excluded_runs": excluded,
               "runs": [{"name": r["name"], "attempt": r["attempt"], "failed_attempts": r["failed_attempts"],
                         "rounds": r["meta"].get("rounds_completed")} for r in runs],
               "issues": issues, "extracted": extracted}
    _write_json(out_dir / "runs.json", summary)

    _write_csv(out_dir / "critic_by_round.csv", aggregate_by_round(runs))
    _write_csv(out_dir / "critic_per_run.csv", [
        {"run": r["name"], "condition": r["condition"], "round": rnd, **{a: f"{v[a]:.3f}" for a in AXES}}
        for r in runs for rnd, v in sorted(per_run_round_axis(r["scores"]).items())])
    _write_csv(out_dir / "critic_run_summary.csv",
               [{**run_summary(r), "failed_attempts": len(r["failed_attempts"])} for r in runs])
    _write_json(out_dir / "condition_summary.json", condition_summary(runs))
    # L8: full-output statistics recorded by the runner (definition included).
    stats_rows = []
    for r in runs:
        st = r["meta"].get("output_stats") or {}
        for agent, v in (st.get("agents") or {}).items():
            stats_rows.append({"run": r["name"], "condition": r["condition"], "agent": agent,
                               "turns": v.get("turns"), "chars": v.get("chars")})
    _write_csv(out_dir / "output_stats.csv", stats_rows)
    if runs:
        _write_json(out_dir / "output_stats_definition.json",
                    {"definition": (runs[0]["meta"].get("output_stats") or {}).get("definition")})
    _write_json(out_dir / "leakage_audit.json", leakage_audit(runs))
    if runs:
        plot_trajectories(runs, out_dir / "figures" / "critic_trajectory.png")

    if embed is not None and len(sim_runs) >= 2:
        sims = {}
        for label, texts in (("content", [r["content"] for r in sim_runs]),
                             ("full", [r["report"] for r in sim_runs])):
            m = cosine_matrix(embed(texts))
            _write_matrix(out_dir / f"similarity_{label}.csv", m, names)
            sims[label] = summarize_pairs(m, names, conds)
            if label == "content":
                rep = medoid(m, names, conds, "A")
                rep["complete_main_set"] = complete
                if not complete:
                    rep["note_incomplete"] = "Provisional: the main set is incomplete; do not use as the final representative."
                _write_json(out_dir / "representative.json", rep)
                plot_matrix(m, names, out_dir / "figures" / "similarity_content.png")
        _write_json(out_dir / "similarity_summary.json",
                    {**sims, "primary": "content", "embedding_model": getattr(embed, "model", "injected")})
    return summary


def _write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _openai_embedder():
    from experiments.reproducibility import analyze as base

    def embed(texts):
        return base._embed_reports(texts)
    embed.model = base.EMBEDDING_MODEL
    return embed


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--runs-dir", default="experiments/runs_rev/main", type=Path)
    p.add_argument("--out-dir", default="experiments/runs_rev/results", type=Path)
    p.add_argument("--skip-embeddings", action="store_true")
    p.add_argument("--expected-per-condition", type=int, default=5)
    args = p.parse_args()
    summary = analyse(args.runs_dir, args.out_dir, None if args.skip_embeddings else _openai_embedder(),
                      expected_per_condition=args.expected_per_condition)
    print(json.dumps({"runs": len(summary["runs"]), "issues": summary["issues"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
