"""Figure 7 (revision): Critic-score trajectory and cross-run similarity of the five final reports.

    python -B scripts/revision/make_fig7.py [--out reference/revision/figures_v2/Fig7_v2.png]

Same visual design as the original Figure 5 (two panels of equal size). Data: results_v1/critic_by_round.csv
(condition A, the five main runs) and results_v1/similarity_full.csv (full final reports, as in the original analysis).
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "experiments" / "runs_rev" / "results_v1"
AXES = [("evidence", "Evidence", "tab:blue", "o"), ("universality", "Universality", "tab:green", "s"),
        ("proportionality", "Proportionality", "tab:red", "^"), ("readability", "Readability", "tab:purple", "D")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reference/revision/figures_v2/Fig7_v2.png")
    a = ap.parse_args()
    d = defaultdict(dict)
    with (RES / "critic_by_round.csv").open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["condition"] == "A":
                d[int(r["round"])][r["axis"]] = (float(r["mean"]), float(r["sd_population"]))
    with (RES / "similarity_full.csv").open(encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    names = rows[0][1:]
    idx = [names.index(f"A_{i}") for i in range(1, 6)]
    mat = np.array([[float(rows[i + 1][j + 1]) for j in idx] for i in idx])
    labels = [f"Run {i}" for i in range(1, 6)]

    fig = plt.figure(figsize=(12.4, 5.0), dpi=300)
    axA = fig.add_axes([0.065, 0.15, 0.38, 0.70])
    axB = fig.add_axes([0.535, 0.15, 0.38, 0.70])
    cax = fig.add_axes([0.925, 0.15, 0.015, 0.70])
    rounds = sorted(d)
    off = {"evidence": -0.09, "universality": -0.03, "proportionality": 0.03, "readability": 0.09}
    for key, label, color, marker in AXES:
        axA.errorbar([r + off[key] for r in rounds], [d[r][key][0] for r in rounds], yerr=[d[r][key][1] for r in rounds],
                     color=color, marker=marker, label=label, linewidth=1.8, markersize=6, capsize=3)
    axA.axhline(5.0, color="gray", linestyle="--", linewidth=0.8)
    axA.set_xticks(rounds); axA.set_xlim(0.6, 7.4); axA.set_ylim(2.5, 5.2)
    axA.set_xlabel("Round"); axA.set_ylabel("Critic score")
    axA.set_title("Critic-score trajectory with cross-run\nreproducibility band (N = 5)", fontsize=11)
    axA.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.7)
    axA.legend(loc="lower right", fontsize=8.5, framealpha=0.95)
    im = axB.imshow(mat, cmap="viridis", vmin=0.70, vmax=1.00, aspect="auto")
    axB.set_xticks(range(5)); axB.set_xticklabels(labels, rotation=45, ha="right")
    axB.set_yticks(range(5)); axB.set_yticklabels(labels)
    for i in range(5):
        for j in range(5):
            axB.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center", fontsize=9, color="black" if mat[i, j] >= 0.93 else "white")
    axB.set_title("Cross-run semantic similarity\n(final framework)", fontsize=11)
    cb = fig.colorbar(im, cax=cax); cb.set_label("Cosine similarity")
    for ax, lab in ((axA, "(A)"), (axB, "(B)")):
        ax.text(-0.08, 1.12, lab, transform=ax.transAxes, fontsize=14, fontweight="bold", ha="right", va="bottom")
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300, facecolor="white")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
