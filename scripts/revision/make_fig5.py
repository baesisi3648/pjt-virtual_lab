"""Figure 5 (revision): Critic-score trajectories under the two scoring protocols and content similarity of the ten reports.

    python -B scripts/revision/make_fig5.py [--out reference/revision/figures_v1/Fig5_v1.png]

Same visual design as the original Figure 5 (matplotlib defaults, tab colours and markers per dimension, error bars =
population SD across runs, viridis heatmap 0.70-1.00 with values). Data: results_v1/critic_by_round.csv and
results_v1/similarity_content.csv.
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


def load_rounds():
    d = defaultdict(dict)
    with (RES / "critic_by_round.csv").open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            d[r["condition"]].setdefault(int(r["round"]), {})[r["axis"]] = (float(r["mean"]), float(r["sd_population"]), int(r["n_runs"]))
    return d


def load_similarity():
    with (RES / "similarity_content.csv").open(encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    names = rows[0][1:]
    mat = np.array([[float(x) for x in r[1:]] for r in rows[1:]])
    order = sorted(range(len(names)), key=lambda i: (names[i][0], int(names[i].split("_")[1])))
    return [names[i].replace("_", "") for i in order], mat[np.ix_(order, order)]


def trajectory(ax, data, title, xmax):
    rounds = sorted(data)
    off = {"evidence": -0.09, "universality": -0.03, "proportionality": 0.03, "readability": 0.09}
    for key, label, color, marker in AXES:
        m = [data[r][key][0] for r in rounds]
        sd = [data[r][key][1] for r in rounds]
        ax.errorbar([r + off[key] for r in rounds], m, yerr=sd, color=color, marker=marker, label=label,
                    linewidth=1.8, markersize=6, capsize=3)
    ax.axhline(5.0, color="gray", linestyle="--", linewidth=0.8)
    for r in rounds:
        ax.text(r, 2.58, f"n={data[r]['evidence'][2]}", ha="center", fontsize=8, color="#4A4A4A")
    ax.set_xticks(range(1, xmax + 1))
    ax.set_xlim(0.6, xmax + 0.4)
    ax.set_ylim(2.5, 5.2)
    ax.set_xlabel("Round")
    ax.set_title(title, fontsize=11)
    ax.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.7)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reference/revision/figures_v1/Fig5_v1.png")
    a = ap.parse_args()
    d = load_rounds()
    names, mat = load_similarity()
    fig = plt.figure(figsize=(15.6, 4.9), dpi=300)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 0.85, 1.15], wspace=0.28, left=0.05, right=0.94, bottom=0.14, top=0.86)
    axA = fig.add_subplot(gs[0])
    axB = fig.add_subplot(gs[1], sharey=axA)
    axC = fig.add_subplot(gs[2])
    trajectory(axA, d["A"], "Revised protocol (5 runs)", 7)
    trajectory(axB, d["B"], "Comparison protocol (5 runs)", 4)
    axA.set_ylabel("Critic score (mean of specialists)")
    plt.setp(axB.get_yticklabels(), visible=False)
    axA.legend(loc="lower right", bbox_to_anchor=(1.0, 0.07), fontsize=8.5, framealpha=0.95, ncol=2)
    axB.text(0.5, 0.075, "stopped when every score was 5\n(round 3 in one run, round 4 in four)", transform=axB.transAxes,
             ha="center", fontsize=7.6, color="#4A4A4A")

    im = axC.imshow(mat, cmap="viridis", vmin=0.70, vmax=1.00)
    axC.set_xticks(range(len(names))); axC.set_xticklabels(names, rotation=45, ha="right")
    axC.set_yticks(range(len(names))); axC.set_yticklabels(names)
    for i in range(len(names)):
        for j in range(len(names)):
            v = mat[i, j]
            axC.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.6, color="black" if v >= 0.93 else "white")
    axC.axhline(4.5, color="white", linewidth=2.2); axC.axvline(4.5, color="white", linewidth=2.2)
    axC.set_title("Content similarity of the final reports\n(A = revised, B = comparison protocol)", fontsize=11)
    cb = fig.colorbar(im, ax=axC, fraction=0.046, pad=0.03)
    cb.set_label("Cosine similarity")
    for ax, lab in ((axA, "(A)"), (axB, "(B)"), (axC, "(C)")):
        ax.text(-0.02, 1.13, lab, transform=ax.transAxes, fontsize=14, fontweight="bold", ha="right", va="bottom")
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300, facecolor="white")
    fig.savefig(out.with_suffix(".pdf"), facecolor="white")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
