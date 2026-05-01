# Reproducibility Experiments

This directory hosts the artefacts and analysis pipeline for the
reproducibility study described in §2.6 and §3.5 of the manuscript.

## Layout

```
experiments/
├── runs/                                # one folder per independent execution
│   ├── run_1/
│   │   ├── final_report.md              # English final report (primary)
│   │   ├── final_report.ko.md           # Korean translation (sidecar)
│   │   ├── critic_scores.json           # per-round, per-specialist, per-axis
│   │   ├── messages.json                # full agent message log
│   │   └── meta.json                    # durations, team, sources, …
│   ├── run_2/
│   └── …
└── reproducibility/
    ├── analyze.py                       # metrics + figures
    └── results/
        ├── similarity_matrix.csv
        ├── similarity_summary.json
        ├── critic_cv.csv
        ├── critic_per_run.csv
        ├── manuscript_numbers.md        # paste-ready snippets for §3.1/§2.6/§3.5
        └── figures/
            ├── figure2c_critic_trajectory.png
            └── figure2d_similarity_heatmap.png
```

## Step 1 — Generate runs

For each independent run (target: N = 5):

```bash
python run_experiment.py --run-id 1
python run_experiment.py --run-id 2
python run_experiment.py --run-id 3
python run_experiment.py --run-id 4
python run_experiment.py --run-id 5
```

Each invocation executes the full LangGraph workflow once (English
report → Korean translation) and writes the per-run dossier under
`experiments/runs/run_<ID>/`. Expect roughly 16–18 minutes per run.

The temperature is held at 0.2 (configurable via
`VIRTUAL_LAB_TEMPERATURE`) to maximise consistency across runs while
preserving the model's natural variation.

## Step 2 — Compute metrics and figures

```bash
python -m experiments.reproducibility.analyze
```

This computes:
- **(a) Cross-run semantic textual similarity** — pairwise cosine similarity
  of the English `final_report.md` files via OpenAI
  `text-embedding-3-large`. Reported as a 5×5 matrix (Figure 2D) and a
  mean ± SD over the off-diagonal pairs.
- **(b) Critic-score Coefficient of Variation** — for each round and each
  of the four axes (evidence, universality, proportionality, readability),
  the mean and population SD across runs, plus the CV (= SD / mean).
  Plotted as Figure 2C with error bars.

Use `--skip-embeddings` to skip the OpenAI call (CV-only re-runs).

## Step 3 — Paste into the manuscript

`results/manuscript_numbers.md` contains paste-ready snippets formatted to
match the tables expected in §3.1, §2.6, and §3.5 of the manuscript.

## Reproducibility checklist

- Same `VIRTUAL_LAB_PROMPTS_DIR` (i.e. the same `prompts/` directory) is
  loaded for every run.
- Same `GPT_MODEL` and `VIRTUAL_LAB_TEMPERATURE` environment variables.
- Same `topic` and `constraints` strings (defaults baked into
  `run_experiment.py`).
- Same RAG corpus version (Pinecone index unchanged between runs).
