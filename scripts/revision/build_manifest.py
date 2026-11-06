"""Freeze the main-experiment inputs in experiments/runs_rev/experiment_manifest.json.

revision_plan 7.3 / step 9. Run once, after the code and prompt sets are committed and
before the first main run. The file is never overwritten.

    python -B scripts/revision/build_manifest.py

Preconditions (the script stops otherwise):
- no uncommitted changes in the tracked code files and prompt sets;
- the retrieval snapshot exists;
- GPT_MODEL is set (in the environment or .env) and CRITIC_MODEL / CRITIC_EFFORT, if set,
  equal the code defaults.
"""
from __future__ import annotations

import json
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

from utils import manifest as mf  # noqa: E402

OUT = ROOT / "experiments" / "runs_rev" / "experiment_manifest.json"
SNAPSHOT = ROOT / "experiments" / "runs_rev" / "retrieval_snapshot.json"
SEED_ORDER = 20261106          # A/B order within each block
SEED_SECOND_JUDGE = 20261107   # L3 second-judge sample
SEED_BLINDING = 20261108       # anonymous report IDs for judging (applied after the runs)
RUNS_PER_CONDITION = 5
MAX_ATTEMPTS_PER_RUN = 3


def run_order() -> list[dict]:
    """Seeded A/B order within each block, balanced: each condition goes first in 2 or 3 of the 5 blocks.

    The unrestricted draw used first gave B first in all five blocks, which would align the
    condition with time (revision_plan 7.3, RUN_LOG 2026-11-06); the restriction was added
    before any main run.
    """
    import itertools
    rng = random.Random(SEED_ORDER)
    balanced = [seq for seq in itertools.product("AB", repeat=RUNS_PER_CONDITION)
                if 2 <= seq.count("A") <= 3]       # which condition goes first in each block
    firsts = rng.choice(balanced)
    order, seq = [], 0
    for block, first in enumerate(firsts, start=1):
        for cond in (first, "B" if first == "A" else "A"):
            seq += 1
            order.append({"seq": seq, "block": block, "condition": cond, "run_id": str(block)})
    return order


def second_judge_sample() -> dict:
    rng = random.Random(SEED_SECOND_JUDGE)
    n_a = rng.choice([2, 1])
    runs = [str(i) for i in range(1, RUNS_PER_CONDITION + 1)]
    picks = [f"A_{r}" for r in sorted(rng.sample(runs, n_a), key=int)] + \
            [f"B_{r}" for r in sorted(rng.sample(runs, 3 - n_a), key=int)]
    return {"seed": SEED_SECOND_JUDGE, "rule": "stratified: 3 reports, both conditions present; "
            "the A/B split (2+1 or 1+2) and the runs are drawn with the seed", "reports": picks}


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"{OUT} already exists; the manifest is never overwritten")
    load_dotenv(ROOT / ".env")

    paths = list(mf.CODE_PATHS) + list(mf.PROMPT_DIRS.values())
    dirty = mf.uncommitted(paths)
    if dirty:
        raise SystemExit("commit these files first:\n  " + "\n  ".join(dirty))
    extra = mf.untracked_code(paths)
    if extra:
        raise SystemExit("untracked Python files in code paths (commit or remove):\n  " + "\n  ".join(extra))
    env_problems = mf.environment_problems()
    if env_problems:
        raise SystemExit("environment not fixable: " + "; ".join(env_problems))
    for env in mf.FORBIDDEN_ENV:
        if os.environ.get(env) is not None:
            raise SystemExit(f"{env} is set; unset it")
    if not SNAPSHOT.is_file():
        raise SystemExit(f"retrieval snapshot not found: {SNAPSHOT}")

    consts = mf.read_constants()
    gen = os.environ.get("GPT_MODEL")
    if not gen:
        raise SystemExit("GPT_MODEL is not set")
    for env, key in (("CRITIC_MODEL", "DEFAULT_CRITIC_MODEL"), ("CRITIC_EFFORT", "DEFAULT_CRITIC_EFFORT")):
        if os.environ.get(env) not in (None, consts[key]):
            raise SystemExit(f"{env}={os.environ[env]!r} differs from the code default {consts[key]!r}; unset it")

    now = datetime.now(timezone.utc)
    import run_experiment as rex  # default topic and constraints (P1)

    manifest = {
        "manifest_version": mf.MANIFEST_VERSION,
        "created": {"utc": now.isoformat(), "kst": now.astimezone(timezone(timedelta(hours=9))).isoformat()},
        "purpose": "Inputs fixed before the main runs of the revision experiment (revision_plan 7.3). "
                   "Not a formal preregistration.",
        "code": {
            "commit_at_freeze": mf._git("rev-parse", "HEAD"),
            "branch": mf._git("rev-parse", "--abbrev-ref", "HEAD"),
            "paths": list(mf.CODE_PATHS),
            "file_hashes": mf.file_hashes(mf.CODE_PATHS),
            "comparison": "by file content; run_experiment.py refuses to start if any tracked file differs",
        },
        "prompts": {c: {"dir": d, "file_hashes": mf.prompt_hashes(c)} for c, d in mf.PROMPT_DIRS.items()},
        "inputs": {"topic": rex.DEFAULT_TOPIC, "constraints": rex.DEFAULT_CONSTRAINTS},
        "conditions": {
            "A": {"prompts_dir": "prompts_A", "critic_mode": "independent"},
            "B": {"prompts_dir": "prompts_B", "critic_mode": "cumulative"},
        },
        "retrieval": {"mode": "replay", "snapshot_path": "experiments/runs_rev/retrieval_snapshot.json",
                      "snapshot_sha256": mf.sha256_file(SNAPSHOT)},
        "models": {
            "generation_model_requested": gen,
            "critic_provider": "anthropic",
            "critic_model_requested": consts["DEFAULT_CRITIC_MODEL"],
            "critic_effort": consts["DEFAULT_CRITIC_EFFORT"],
            "sampling": "GPT-5: no temperature and no reasoning_effort sent (provider defaults); "
                        "Critic: output_config.effort only, no sampling parameters, no fallback model",
        },
        "limits": {k: consts[k] for k in ("MAX_ROUNDS", "CRITIC_MAX_TOKENS", "INTRO_MAX_TOKENS")},
        "termination": "early stop when every axis of every specialist scores 5; otherwise stop after MAX_ROUNDS",
        "retry_policy": {
            "max_attempts_per_run": MAX_ATTEMPTS_PER_RUN,
            "in_call": {k: consts[k] for k in ("MAX_HTTP_RETRIES", "MAX_INCOMPLETE_RETRIES",
                                               "CRITIC_VALIDATION_RETRIES")},
            "technical_failure": "infrastructure or API error, logging failure, response-format failure "
                                 "after the in-call retries, or a Critic refusal; the run exits non-zero "
                                 "and is retried as a new attempt immediately, before the next run",
            "refusals": "Critic refusals (stop_reason refusal) are counted and reported separately, "
                        "because they depend on content",
            "scientific_result": "low scores, non-convergence, wrong or weak content; included as is, "
                                 "never replaced by another run",
            "valid_run": "exactly one attempt with status ok; all attempts are kept and reported",
            "if_exhausted": f"after {MAX_ATTEMPTS_PER_RUN} failed attempts the run is reported as missing "
                            "and the condition is analysed with fewer runs (flagged incomplete)",
        },
        "runs_per_condition": RUNS_PER_CONDITION,
        "order_seed": SEED_ORDER,
        "order_rule": "per block, which condition goes first is drawn with the seed from the 20 sequences in "
                      "which each condition goes first in 2 or 3 of the 5 blocks",
        "order": run_order(),
        "execution": "one new Python process per run, sequential, in manifest order, "
                     "out-dir experiments/runs_rev/main",
        "analysis": {
            "script": "experiments/reproducibility/analyze_revision.py (hash in code.file_hashes)",
            "missing_sampled_report": "if a report drawn for the second judge is missing, the replacement is "
                                      "drawn with the same seed from the remaining runs of that condition",
            "representative_run": "condition-A medoid: highest mean cosine similarity of the safety-content "
                                  "embedding to the other four A runs; ties go to the smaller run number",
            "primary_similarity_input": "safety-content extraction (Core Questions 1-5 and decision trees; "
                                        "Methods, statistics, score charts, references and stubs removed)",
            "second_judge_sample": second_judge_sample(),
            "blinding_seed": SEED_BLINDING,
            "criteria_freeze": "Two stages (revision_plan 7.3). This manifest fixes the execution inputs "
                               "and the analysis rules above before the first main run. The L3 codebook, "
                               "judgement and cause categories, aggregation formulas and the L5 "
                               "claim-selection rule are frozen in experiments/runs_rev/analysis_criteria.json "
                               "before any main-run report or deliberation text is opened (only run status "
                               "and call-log completeness are checked before that); its hash is logged in "
                               "RUN_LOG.md. The authors have seen the submitted runs and the pilot outputs.",
        },
        "environment": {"python": mf.python_version(), "packages": mf.installed_packages(),
                        "enforced": "run_experiment.py refuses to start if the Python version or any installed package version differs"},
    }
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  sha256={mf.sha256_file(OUT)}")
    for e in manifest["order"]:
        print(f"  {e['seq']:>2}  block {e['block']}  {e['condition']}_{e['run_id']}")
    print("second judge:", manifest["analysis"]["second_judge_sample"]["reports"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
