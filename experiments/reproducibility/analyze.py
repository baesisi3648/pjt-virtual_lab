"""Reproducibility analysis — Figure 2C / 2D and the manuscript metrics.

Consumes the dossiers produced by `run_experiment.py` and computes the two
quantitative reproducibility indicators reported in the paper:

  (a) Cross-run semantic textual similarity of the final framework
      (final_report.md). Implemented with OpenAI's text-embedding-3-large.
      → 5×5 cosine matrix → mean ± SD → Figure 2D heatmap.

  (b) Per-round, per-axis Coefficient of Variation (CV) of the Critic
      scores across the N runs.
      → mean ± SD trajectory across rounds → Figure 2C with error bars.

Outputs (under `experiments/reproducibility/results/`):

  - similarity_matrix.csv          # NxN cosine similarities
  - similarity_summary.json        # mean, SD, min, max across off-diagonal
  - critic_cv.csv                  # round × axis × {mean, std, cv}
  - critic_per_run.csv             # raw per-run mean scores per round per axis
  - manuscript_numbers.md          # ready-to-paste numbers for §3.1 / §2.6 / §3.5
  - figures/figure2c_critic_trajectory.png
  - figures/figure2d_similarity_heatmap.png

Usage:
    python -m experiments.reproducibility.analyze \\
        --runs-dir experiments/runs \\
        --out-dir experiments/reproducibility/results
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import os
import sys
from pathlib import Path
from statistics import mean, pstdev
from typing import Iterable

import httpx
import numpy as np
import matplotlib.pyplot as plt
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("repro")

load_dotenv()

# OpenAI embeddings — used for the semantic-similarity metric.
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-large")
OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

AXES = ("evidence", "universality", "proportionality", "readability")
AXIS_LABELS = {
    "evidence": "Evidence",
    "universality": "Universality",
    "proportionality": "Proportionality",
    "readability": "Readability",
}
AXIS_COLORS = {
    "evidence": "#1f77b4",
    "universality": "#2ca02c",
    "proportionality": "#d62728",
    "readability": "#9467bd",
}
AXIS_MARKERS = {
    "evidence": "o",
    "universality": "s",
    "proportionality": "^",
    "readability": "D",
}


# ─ Helpers ────────────────────────────────────────────────────────────


def _load_runs(runs_dir: Path) -> list[dict]:
    """Discover `run_<ID>/` dossiers and load their key artefacts."""
    runs = []
    for run_dir in sorted(runs_dir.glob("run_*")):
        if not run_dir.is_dir():
            continue
        report_path = run_dir / "final_report.md"
        scores_path = run_dir / "critic_scores.json"
        meta_path = run_dir / "meta.json"
        if not report_path.exists() or not scores_path.exists():
            log.warning("Skipping %s — missing final_report.md or critic_scores.json", run_dir.name)
            continue
        runs.append({
            "run_id": run_dir.name.replace("run_", "", 1),
            "dir": run_dir,
            "report": report_path.read_text(encoding="utf-8"),
            "scores": json.loads(scores_path.read_text(encoding="utf-8")),
            "meta": json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {},
        })
    return runs


def _embed_batch(texts: list[str]) -> np.ndarray:
    """Call the OpenAI embeddings API and return an `(n, d)` array."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set; semantic similarity cannot be computed.")
    payload = {"model": EMBEDDING_MODEL, "input": texts}
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(
            OPENAI_EMBEDDINGS_URL,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
    return np.array([row["embedding"] for row in data["data"]], dtype=np.float64)


def _cosine_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Compute pairwise cosine similarity for an `(n, d)` embedding matrix."""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normed = embeddings / np.clip(norms, 1e-12, None)
    return normed @ normed.T


def _per_run_round_axis(scores: list[dict]) -> dict[int, dict[str, float]]:
    """Average each round's per-specialist axis scores into a single value per axis."""
    by_round: dict[int, dict[str, list[int]]] = {}
    for snap in scores:
        rnd = int(snap.get("round", 0))
        by_round.setdefault(rnd, {ax: [] for ax in AXES})
        for _role, axis_scores in (snap.get("scores") or {}).items():
            if not isinstance(axis_scores, dict):
                continue
            for ax in AXES:
                if ax in axis_scores and axis_scores[ax] is not None:
                    by_round[rnd][ax].append(int(axis_scores[ax]))
    out: dict[int, dict[str, float]] = {}
    for rnd, axis_lists in by_round.items():
        out[rnd] = {
            ax: (mean(vals) if vals else float("nan"))
            for ax, vals in axis_lists.items()
        }
    return out


def _aggregate_critic(runs: list[dict]) -> dict:
    """Aggregate per-run round-axis scores into mean/std/CV across runs."""
    per_run = []
    for r in runs:
        per_run.append(_per_run_round_axis(r["scores"]))

    all_rounds = sorted({rnd for d in per_run for rnd in d})
    aggregated = {}
    for rnd in all_rounds:
        aggregated[rnd] = {}
        for ax in AXES:
            values = [d.get(rnd, {}).get(ax, float("nan")) for d in per_run]
            clean = [v for v in values if isinstance(v, (int, float)) and not math.isnan(v)]
            if not clean:
                aggregated[rnd][ax] = {"mean": float("nan"), "std": float("nan"), "cv": float("nan"), "values": values}
                continue
            mu = mean(clean)
            sd = pstdev(clean) if len(clean) >= 2 else 0.0
            cv = (sd / mu) if mu else float("nan")
            aggregated[rnd][ax] = {
                "mean": mu,
                "std": sd,
                "cv": cv,
                "values": values,
            }
    return aggregated


# ─ Outputs ────────────────────────────────────────────────────────────


def _write_similarity_csv(matrix: np.ndarray, run_ids: list[str], out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["run"] + run_ids)
        for i, rid in enumerate(run_ids):
            writer.writerow([rid] + [f"{matrix[i, j]:.6f}" for j in range(len(run_ids))])


def _write_similarity_summary(matrix: np.ndarray, run_ids: list[str], out_path: Path) -> dict:
    n = matrix.shape[0]
    if n < 2:
        summary = {"n": n, "note": "Need ≥2 runs for cross-run similarity."}
    else:
        iu = np.triu_indices(n, k=1)
        offdiag = matrix[iu]
        summary = {
            "n": n,
            "embedding_model": EMBEDDING_MODEL,
            "pairwise_count": int(offdiag.size),
            "mean": float(np.mean(offdiag)),
            "std": float(np.std(offdiag, ddof=0)),
            "min": float(np.min(offdiag)),
            "max": float(np.max(offdiag)),
            "run_ids": run_ids,
        }
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _write_critic_csvs(critic: dict, runs: list[dict], out_dir: Path) -> None:
    cv_path = out_dir / "critic_cv.csv"
    with cv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["round", "axis", "mean", "std", "cv"])
        for rnd in sorted(critic.keys()):
            for ax in AXES:
                v = critic[rnd][ax]
                writer.writerow([
                    rnd, ax,
                    f"{v['mean']:.4f}" if not math.isnan(v["mean"]) else "",
                    f"{v['std']:.4f}" if not math.isnan(v["std"]) else "",
                    f"{v['cv']:.4f}" if not math.isnan(v["cv"]) else "",
                ])

    raw_path = out_dir / "critic_per_run.csv"
    run_ids = [r["run_id"] for r in runs]
    with raw_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["round", "axis"] + [f"run_{rid}" for rid in run_ids])
        for rnd in sorted(critic.keys()):
            for ax in AXES:
                row = [rnd, ax] + [
                    f"{val:.4f}" if isinstance(val, (int, float)) and not math.isnan(val) else ""
                    for val in critic[rnd][ax]["values"]
                ]
                writer.writerow(row)


def _plot_critic_trajectory(critic: dict, out_path: Path, n_runs: int) -> None:
    rounds_sorted = sorted(critic.keys())
    fig, ax = plt.subplots(figsize=(7.5, 5.0), dpi=150)
    for axis in AXES:
        means = [critic[r][axis]["mean"] for r in rounds_sorted]
        stds = [critic[r][axis]["std"] for r in rounds_sorted]
        ax.errorbar(
            rounds_sorted,
            means,
            yerr=stds,
            label=AXIS_LABELS[axis],
            color=AXIS_COLORS[axis],
            marker=AXIS_MARKERS[axis],
            markersize=7,
            linewidth=1.8,
            capsize=4,
            alpha=0.95,
        )
    ax.axhline(5.0, color="grey", linestyle="--", linewidth=0.9, alpha=0.6)
    ax.set_xlabel("Round")
    ax.set_ylabel("Critic score")
    ax.set_title(f"Critic-score convergence with cross-run reproducibility band (N={n_runs})")
    ax.set_xticks(rounds_sorted)
    ax.set_ylim(2.5, 5.4)
    ax.grid(True, axis="y", linestyle=":", alpha=0.4)
    ax.legend(loc="lower right", frameon=False)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def _plot_similarity_heatmap(matrix: np.ndarray, run_ids: list[str], out_path: Path) -> None:
    n = matrix.shape[0]
    fig, ax = plt.subplots(figsize=(5.6, 5.0), dpi=150)
    vmin = min(0.7, float(np.min(matrix)))
    im = ax.imshow(matrix, cmap="viridis", vmin=vmin, vmax=1.0)
    ax.set_xticks(range(n), [f"Run {rid}" for rid in run_ids], rotation=30, ha="right")
    ax.set_yticks(range(n), [f"Run {rid}" for rid in run_ids])
    for i in range(n):
        for j in range(n):
            ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center",
                    color="white" if matrix[i, j] < 0.85 else "black", fontsize=9)
    ax.set_title("Cross-run semantic similarity (final framework)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Cosine similarity")
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def _write_manuscript_numbers(
    runs: list[dict],
    similarity: dict,
    critic: dict,
    out_path: Path,
) -> None:
    n = len(runs)
    durations = [r["meta"].get("total_duration_seconds", 0.0) for r in runs]
    rounds_completed = [r["meta"].get("rounds_completed", 0) for r in runs]
    chars_en = [r["meta"].get("report_chars_en", 0) for r in runs]

    def _hms(s: float) -> str:
        m, sec = divmod(int(s), 60)
        return f"{m} min {sec} s"

    lines = []
    lines.append("# Reproducibility Numbers — paste-ready snippets for the manuscript")
    lines.append("")
    lines.append(f"_N = {n} independent runs, embedding model = `{EMBEDDING_MODEL}`._")
    lines.append("")

    lines.append("## §3.1 — Operational characteristics (mean ± SD across runs)")
    if durations:
        mu = mean(durations)
        sd = pstdev(durations) if len(durations) >= 2 else 0.0
        lines.append(
            f"- Total deliberation time: **{_hms(mu)} ± {sd:.0f} s** "
            f"(min {_hms(min(durations))}, max {_hms(max(durations))})"
        )
    if rounds_completed:
        mu = mean(rounds_completed)
        lines.append(f"- Rounds completed: **{mu:.1f}** on average")
    if chars_en:
        mu = mean(chars_en)
        sd = pstdev(chars_en) if len(chars_en) >= 2 else 0.0
        lines.append(f"- English report length: **{mu:.0f} ± {sd:.0f}** characters")
    lines.append("")

    lines.append("## §2.6 / §3.5 — Reproducibility metrics")
    if similarity.get("n", 0) >= 2 and "mean" in similarity:
        lines.append(
            f"- Pairwise semantic textual similarity (final framework, off-diagonal): "
            f"**{similarity['mean']:.3f} ± {similarity['std']:.3f}** "
            f"(min {similarity['min']:.3f}, max {similarity['max']:.3f}, "
            f"{similarity['pairwise_count']} pairs)."
        )
    else:
        lines.append("- Pairwise semantic textual similarity: _embedding step skipped or unavailable._")
    lines.append("- Critic-score Coefficient of Variation (CV) per round and axis:")
    lines.append("")
    lines.append("  | Round | " + " | ".join(AXIS_LABELS[a] for a in AXES) + " |")
    lines.append("  |-------|" + "|".join(["----"] * len(AXES)) + "|")
    for rnd in sorted(critic.keys()):
        cells = []
        for ax in AXES:
            v = critic[rnd][ax]
            if math.isnan(v["mean"]):
                cells.append("—")
            else:
                cells.append(
                    f"{v['mean']:.2f} ± {v['std']:.2f}  (CV {v['cv']:.3f})"
                )
        lines.append(f"  | R{rnd} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("## Notes")
    lines.append("- Critic scores were aggregated per round by averaging across all specialists.")
    lines.append("- Similarity uses OpenAI `text-embedding-3-large` on the entire English final report.")
    lines.append("- Figures saved to `experiments/reproducibility/results/figures/`.")

    out_path.write_text("\n".join(lines), encoding="utf-8")


# ─ Entrypoint ─────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute reproducibility metrics from N runs.")
    parser.add_argument("--runs-dir", default="experiments/runs", type=Path)
    parser.add_argument("--out-dir", default="experiments/reproducibility/results", type=Path)
    parser.add_argument("--skip-embeddings", action="store_true",
                        help="Skip the OpenAI embedding call (e.g. for quick CV-only re-runs).")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = args.out_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    runs = _load_runs(args.runs_dir)
    if not runs:
        log.error("No runs found in %s", args.runs_dir.resolve())
        return 1
    run_ids = [r["run_id"] for r in runs]
    log.info("Loaded %d run(s): %s", len(runs), run_ids)

    # ─ Critic CV (always available) ──
    critic = _aggregate_critic(runs)
    _write_critic_csvs(critic, runs, args.out_dir)
    _plot_critic_trajectory(critic, figures_dir / "figure2c_critic_trajectory.png", len(runs))
    log.info("Wrote critic_cv.csv + figure2c_critic_trajectory.png")

    # ─ Semantic similarity ──
    similarity_summary: dict = {"n": len(runs), "note": "skipped"}
    if not args.skip_embeddings and len(runs) >= 2:
        log.info("Embedding %d reports with %s …", len(runs), EMBEDDING_MODEL)
        embeddings = _embed_batch([r["report"] for r in runs])
        matrix = _cosine_matrix(embeddings)
        _write_similarity_csv(matrix, run_ids, args.out_dir / "similarity_matrix.csv")
        similarity_summary = _write_similarity_summary(matrix, run_ids, args.out_dir / "similarity_summary.json")
        _plot_similarity_heatmap(matrix, run_ids, figures_dir / "figure2d_similarity_heatmap.png")
        log.info("Wrote similarity_matrix.csv + figure2d_similarity_heatmap.png")
    elif args.skip_embeddings:
        log.warning("Embedding step skipped (--skip-embeddings).")
    elif len(runs) < 2:
        log.warning("Only %d run(s) — need ≥2 for similarity matrix.", len(runs))

    # ─ Manuscript-ready numbers ──
    _write_manuscript_numbers(
        runs,
        similarity_summary,
        critic,
        args.out_dir / "manuscript_numbers.md",
    )
    log.info("Wrote manuscript_numbers.md")
    log.info("Done. Outputs at %s", args.out_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
