# Experiments

Two sets of runs live here.

| Folder | What it is |
|---|---|
| `runs/` | The five runs of the originally submitted manuscript (preserved, not regenerated). |
| `runs_rev/` | The revision experiment: conditions A and B, five runs each, plus preparation records. |

The manuscript reports condition A of the revision experiment (records `runs_rev/main_v1/`,
results `runs_rev/results_v1/`). The run log is `runs_rev/RUN_LOG.md`.

## Revision experiment (`runs_rev/`)

### Conditions

| | A (revised scoring) | B (submitted scoring rules) |
|---|---|---|
| Prompt set | `prompts_A/` | `prompts_B/` |
| Critic mode | `independent`: no prior numeric scores, no raise / do-not-lower rules, no Round-1 cap; score mentions masked in the Critic input | `cumulative`: prior scores and the submitted rules |
| Common to both | neutral constraint and rubric (P1–P4), same generation model (`GPT_MODEL`), same Critic model (Claude, `CRITIC_MODEL`, default `claude-opus-5`, effort high), same fixed retrieval snapshot, up to 7 rounds | |

`prompts_A/` and `prompts_B/` are built from `prompts/` by `scripts/revision/build_prompt_sets.py`;
their only difference is `system/critic.md`.

Notes on condition A:
- In both conditions the specialists still receive their own scores and the Critic's prior
  feedback (common design element). Condition A changes only what the Critic receives.
- Masking of score mentions in the Critic input is rule-based and narrow (scientific numbers are
  never masked), so some phrasings may remain. The analysis reports every remaining candidate
  mention for manual review (`leakage_audit.json`).

### Steps

```powershell
# 1. Build the fixed retrieval snapshot once (never overwritten)
python -B scripts/revision/build_retrieval_snapshot.py

# 2. One run = one process. Condition, run number and attempt are explicit.
#    Without --manifest, give a new output folder (runs in runs_rev/main need a manifest).
python -B run_experiment.py --condition A --run-id 1 --attempt 1 --out-dir experiments/runs_rev/new_runs
python -B run_experiment.py --condition B --run-id 1 --attempt 1 --out-dir experiments/runs_rev/new_runs
#    output: <out-dir>/<COND>_<RUN>/attempt_<NN>/ (existing folders are never overwritten)
#    pilot runs: add --out-dir experiments/runs_rev/pilot

#    main runs: freeze the inputs once, then run in manifest order (one process per run)
#    (the reported runs used experiment_manifest_v2.json: --out-dir experiments/runs_rev/main_v1
#     --retrieval-snapshot experiments/runs_rev/retrieval_snapshot_v1.json)
python -B scripts/revision/build_manifest.py          # writes runs_rev/experiment_manifest.json
python -B run_experiment.py --condition B --run-id 1 --attempt 1 `
    --manifest experiments/runs_rev/experiment_manifest.json
#    run_experiment.py refuses a main run whose code, prompts, snapshot, topic/constraints,
#    models, Python/package versions, order or attempt number differ from the manifest

# 3. Analysis (add --skip-embeddings to skip the embedding calls)
python -B -m experiments.reproducibility.analyze_revision `
    --runs-dir experiments/runs_rev/main --out-dir experiments/runs_rev/results
```

### Analysis outputs (`analyze_revision.py`)

The output folder must be new or empty. The main set is flagged incomplete unless each condition
has `--expected-per-condition` (default 5) runs with exactly one successful attempt; a
representative run chosen from an incomplete set is marked provisional.

- `runs.json`: runs, attempts, failed attempts with reasons, issues, extraction hashes
- `extracted/`: safety-content text (Core Questions 1–5 and decision trees; Methods, statistics,
  score charts, references and placeholder stubs removed) used for the primary similarity
- `similarity_content.csv`, `similarity_full.csv`, `similarity_summary.json`: cosine similarity
  (descriptive; pairs share runs and are not independent)
- `representative.json`: condition-A medoid (highest mean content similarity; ties: smaller run number)
- `critic_by_round.csv` (mean, population SD only when n ≥ 2, n runs), `critic_per_run.csv`,
  `critic_run_summary.csv`, `condition_summary.json` (termination-round distribution, runs that
  reached all 5, score decreases)
- `leakage_audit.json`: candidate score mentions in condition-A Critic inputs with call IDs and an
  empty `manual_judgement` field; a run without a complete call log is marked not auditable
- `output_stats.csv`: turns and characters from full outputs, with the definition

### What each run records

`calls.jsonl` (every LLM call: inputs, parameters sent and omitted, all attempts, raw response,
model identifier reported by the provider, usage, stop reason, request id),
`conversations.json`, `critic_scores.json`, `team_selection.json`, `final_report.md`,
`meta.json` (status, condition, models, prompt hashes, retrieval snapshot hash, code version,
package versions, UTC/KST times, output statistics, errors). API keys are redacted.

A failed run keeps its `meta.json` (status `failed`) and partial records and is retried as a
new attempt; low scores or non-convergence are results, not failures.

### Sampling parameters

GPT-5 requests send no `temperature` (the API does not accept a custom value for this model
family) and no `reasoning_effort`; provider defaults apply and the omission is recorded per call.
The Claude Critic is called with `output_config.effort = "high"` and no sampling parameters.
Claude Opus 5.5 was tried first and refused Critic calls on this content (safety classifier
category `bio`, a false positive for food-safety assessment); the Critic therefore uses Claude
Opus 5, with no server-side fallback to any other model.
The earlier note that runs used temperature 0.2 did not apply to GPT-5 requests.

## Original runs (`runs/`)

Produced by the submitted version of `run_experiment.py` and analysed with
`reproducibility/analyze.py`. Their `messages.json` holds only 200-character previews of the
specialist outputs; full per-round outputs were not saved for these runs. The model snapshot
used was not recorded.
