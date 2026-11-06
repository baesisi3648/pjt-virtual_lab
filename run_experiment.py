"""CLI entry point for one reproducibility-tracked workflow execution (revision).

Usage:
    python -B run_experiment.py --condition A --run-id 1 --attempt 1
    python -B run_experiment.py --condition B --run-id 1 --attempt 1 --out-dir experiments/runs_rev/pilot

Conditions (reference/revision/revision_plan.md, section 7.2):
    A  prompts_A/, Critic mode "independent" (current content only)
    B  prompts_B/, Critic mode "cumulative"  (submitted scoring rules)
Both use the same neutralised prompts (P1-P4), the same generation model
(env GPT_MODEL) and the same Critic model (Claude, env CRITIC_MODEL).

Each run writes to <out-dir>/<condition>_<run-id>/attempt_<NN>/ and refuses to
overwrite an existing directory:
    calls.jsonl          every LLM call: inputs, parameters sent/omitted, attempts,
                         raw response, response model id, usage, stop reason
    conversations.json   per-round specialist outputs, Critic results, PI summaries
    critic_scores.json   per-round, per-specialist, per-axis scores and feedback
    team_selection.json  all team-composition trials, frequency table, failed attempts
    final_report.md / final_report.ko.md
    messages.json        short message log (as in the submitted version)
    meta.json            run status, condition, models, prompt hashes, code version,
                         environment, durations, output statistics, errors

A failed run still writes meta.json (status "failed") and the partial records,
then exits with code 1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import platform
import subprocess
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from importlib import metadata
from pathlib import Path

# Same anti-cache behaviour as server.py.
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECACHE"] = "1"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_TRACING"] = "false"

ROOT = Path(__file__).resolve().parent

DEFAULT_TOPIC = (
    "Derivation of a standard safety assessment framework for "
    "genome-edited foods (NGT)."
)
# P1 (revision): neutral constraint. The submitted version used
# "Avoid the GMO-style blanket strictness; require additional data only when there
# is a clear scientific basis. Be proportionate and rational."
DEFAULT_CONSTRAINTS = (
    "Be proportionate and science-based. Require additional data only when there "
    "is a scientific basis, and justify any decision to omit an assessment. "
    "Avoid both disproportionate data requirements and unsupported waivers."
)

CONDITIONS = {
    "A": {"prompts_dir": "prompts_A", "critic_mode": "independent"},
    "B": {"prompts_dir": "prompts_B", "critic_mode": "cumulative"},
}
CRITIC_PROVIDER = "anthropic"
KST = timezone(timedelta(hours=9))
PACKAGES = ("anthropic", "openai", "httpx", "langgraph", "langchain-core", "pinecone",
            "tavily-python", "numpy", "pydantic")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run one revision experiment execution.")
    p.add_argument("--condition", required=True, choices=sorted(CONDITIONS))
    p.add_argument("--run-id", required=True, help="Run number within the condition, e.g. 1")
    p.add_argument("--attempt", type=int, default=1, help="Attempt number (technical retries)")
    p.add_argument("--topic", default=DEFAULT_TOPIC)
    p.add_argument("--constraints", default=DEFAULT_CONSTRAINTS)
    p.add_argument("--out-dir", default="experiments/runs_rev/main")
    return p.parse_args()


def _configure_condition(condition: str) -> dict:
    """Set the condition's environment before any prompt is imported (C1, C7)."""
    cfg = CONDITIONS[condition]
    expected = {
        "VIRTUAL_LAB_PROMPTS_DIR": str((ROOT / cfg["prompts_dir"]).resolve()),
        "VIRTUAL_LAB_CRITIC_MODE": cfg["critic_mode"],
        "VIRTUAL_LAB_CRITIC_PROVIDER": CRITIC_PROVIDER,
    }
    for key, value in expected.items():
        current = os.environ.get(key)
        if current is not None:
            same = (Path(current).resolve() == Path(value)) if key == "VIRTUAL_LAB_PROMPTS_DIR" else current == value
            if not same:
                raise SystemExit(f"{key}={current!r} conflicts with condition {condition} ({value!r})")
        os.environ[key] = value
    if not Path(expected["VIRTUAL_LAB_PROMPTS_DIR"]).is_dir():
        raise SystemExit(f"prompt set not found: {expected['VIRTUAL_LAB_PROMPTS_DIR']}")
    return {**cfg, **expected}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_info() -> dict:
    def run(*args):
        try:
            return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            return None
    porcelain = run("status", "--porcelain") or ""
    return {"commit": run("rev-parse", "HEAD"), "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(porcelain), "status_porcelain": porcelain.splitlines()}


def _package_versions() -> dict:
    out = {}
    for name in PACKAGES:
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = None
    return out


def _times(ts: float) -> dict:
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return {"utc": dt.isoformat(), "kst": dt.astimezone(KST).isoformat()}


def _write_json(path: Path, obj) -> None:
    from utils.redact import redact  # secrets may appear in error texts (e.g. translation_error)
    path.write_text(redact(json.dumps(obj, ensure_ascii=False, indent=2, default=str)), encoding="utf-8")


def _critique_to_dict(c) -> dict:
    if c is None:
        return {}
    return {"decision": c.decision, "feedback": c.feedback, "scores": c.scores,
            "specialist_feedback": c.specialist_feedback}


def _conversations(final_state: dict, current_round: int, produced: set[str]) -> list[dict]:
    """meeting_history holds rounds 1..N-1; add the last round from the live state.

    Only parts actually produced in the current round are added (`produced` holds the
    node names seen since the last increment_round), so a failure early in a round
    never re-labels the previous round's outputs as the current round.
    """
    history = list(final_state.get("meeting_history", []) or [])
    if history and history[-1].get("round") == current_round:
        return history
    last: dict = {"round": current_round, "complete": "pi_summary" in produced}
    if produced & {"researching", "round_revision"}:
        last["specialist_outputs"] = final_state.get("specialist_outputs", []) or []
    if "critique" in produced:
        last["critique"] = _critique_to_dict(final_state.get("critique"))
    if "pi_summary" in produced:
        last["pi_summary"] = final_state.get("draft", "") or ""
    if len(last) > 2:
        history.append(last)
    return history


def _output_stats(conversations: list[dict], final_report: str) -> dict:
    """Turn and character counts from full outputs (L8; replaces preview-based Table 1).

    Definition: characters of the full text returned by the model, whitespace included.
    Specialist turns = one analysis or revision per round. Critic text = overall plus
    per-specialist feedback. PI text = round summaries plus the final report.
    """
    stats: dict[str, dict] = {}

    def add(key, text):
        s = stats.setdefault(key, {"turns": 0, "chars": 0})
        s["turns"] += 1
        s["chars"] += len(text or "")

    for rnd in conversations:
        for so in rnd.get("specialist_outputs", []):
            add(so.get("role", "Specialist"), so.get("output", ""))
        crit = rnd.get("critique") or {
            "feedback": rnd.get("critique_feedback", ""),
            "specialist_feedback": rnd.get("specialist_feedback", {}),
        }
        add("Critic", (crit.get("feedback") or "") + "".join((crit.get("specialist_feedback") or {}).values()))
        add("PI", rnd.get("pi_summary", ""))
    if final_report:
        add("PI", final_report)
    return {"definition": _output_stats.__doc__.split("\n\n", 1)[1].strip(), "agents": stats}


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    args = _parse_args()
    cond = _configure_condition(args.condition)

    out_dir = ROOT / args.out_dir / f"{args.condition}_{args.run_id}" / f"attempt_{args.attempt:02d}"
    if out_dir.exists():
        raise SystemExit(f"output directory already exists, refusing to overwrite: {out_dir}")
    out_dir.mkdir(parents=True)

    from utils.redact import redact

    def _error(e: BaseException) -> dict:
        return {"type": type(e).__name__, "message": redact(str(e))[:4000],
                "traceback": redact(traceback.format_exc())[-8000:]}

    # Initialisation (imports after the condition environment is fixed, because
    # prompts load at import time). A failure here still leaves a meta.json.
    try:
        from utils import call_log
        from utils.llm import DEFAULT_CRITIC_EFFORT, DEFAULT_CRITIC_MODEL
        from utils.prompt_loader import active_prompts_dir
        from workflow.graph import MAX_ROUNDS, create_workflow

        if Path(active_prompts_dir()).resolve() != Path(cond["VIRTUAL_LAB_PROMPTS_DIR"]):
            raise RuntimeError(f"active prompt set {active_prompts_dir()} does not match condition {args.condition}")

        prompts_dir = Path(cond["VIRTUAL_LAB_PROMPTS_DIR"])
        prompt_hashes = {p.relative_to(prompts_dir).as_posix(): _sha256(p)
                         for p in sorted(prompts_dir.rglob("*.md"))}
        run_meta = {"condition": args.condition, "run_id": str(args.run_id), "attempt": args.attempt}
        call_log.configure(out_dir / "calls.jsonl", run_meta)
    except BaseException as e:
        _write_json(out_dir / "meta.json", {
            "status": "failed_init", "error": _error(e), "condition": args.condition,
            "run_id": str(args.run_id), "attempt": args.attempt, "started": _times(time.time()),
            "prompts_dir": cond["prompts_dir"], "code": _git_info(),
        })
        print(f"\n[EXPERIMENT] INITIALISATION FAILED: {type(e).__name__}: {redact(str(e))}\n")
        return 1

    print(f"\n{'='*80}\n[EXPERIMENT] condition={args.condition} run={args.run_id} attempt={args.attempt}"
          f"\n[EXPERIMENT] output: {out_dir}\n{'='*80}\n")

    initial_state = {
        "topic": args.topic, "constraints": args.constraints, "team": [], "specialist_outputs": [],
        "draft": "", "critique": None, "current_round": 1, "meeting_history": [],
        "final_report": "", "final_report_ko": "", "messages": [], "parallel_views": [],
        "sources": [], "cached_efsa_context": "", "team_selection_data": None,
        "specialist_introductions": [], "word_counts": {}, "critic_score_history": [],
        "run_id": f"{args.condition}_{args.run_id}", "translation_error": "",
    }

    started = time.time()
    round_durations: dict[int, float] = {}
    round_start = {1: started}
    current_round = 1
    produced: set[str] = set()  # node names seen since the last increment_round
    final_state: dict = {}
    status, error = "ok", None

    try:
        workflow = create_workflow()
        for event in workflow.stream(initial_state, {"recursion_limit": 200}):
            for node_name, node_state in event.items():
                if node_name == "increment_round":
                    round_durations[current_round] = time.time() - round_start[current_round]
                    current_round = node_state.get("current_round", current_round + 1)
                    round_start[current_round] = time.time()
                    produced = set()
                else:
                    produced.add(node_name)
                if node_name == "final_synthesis" and current_round not in round_durations:
                    round_durations[current_round] = time.time() - round_start[current_round]
                for key, value in (node_state or {}).items():
                    final_state[key] = value
    except BaseException as e:  # record the failure, then exit non-zero
        status = "failed"
        error = _error(e)
        # Records produced before the failure (e.g. team-selection trials).
        for key, value in (getattr(e, "partial", None) or {}).items():
            final_state.setdefault(key, value)
        print(f"\n[EXPERIMENT] FAILED: {type(e).__name__}: {redact(str(e))}\n")

    finished = time.time()
    final_report = final_state.get("final_report", "") or ""
    final_report_ko = final_state.get("final_report_ko", "") or ""
    conversations = _conversations(final_state, current_round, produced)
    rounds_completed = sum(1 for r in conversations if r.get("complete", True) and r.get("pi_summary") is not None)
    tsd = final_state.get("team_selection_data") or {}

    _write_json(out_dir / "conversations.json", conversations)
    _write_json(out_dir / "critic_scores.json", final_state.get("critic_score_history", []) or [])
    _write_json(out_dir / "messages.json", final_state.get("messages", []) or [])
    _write_json(out_dir / "team_selection.json", tsd)
    if final_report:
        (out_dir / "final_report.md").write_text(redact(final_report), encoding="utf-8")
    if final_report_ko:
        (out_dir / "final_report.ko.md").write_text(redact(final_report_ko), encoding="utf-8")

    meta = {
        "status": status,
        "error": error,
        "condition": args.condition,
        "run_id": str(args.run_id),
        "attempt": args.attempt,
        "started": _times(started),
        "finished": _times(finished),
        "total_duration_seconds": round(finished - started, 2),
        "rounds_completed": rounds_completed,
        "round_at_end": current_round,
        "max_rounds": MAX_ROUNDS,
        "round_durations_seconds": {str(r): round(d, 2) for r, d in sorted(round_durations.items())},
        "topic": args.topic,
        "constraints": args.constraints,
        "prompts_dir": cond["prompts_dir"],
        "prompt_hashes": prompt_hashes,
        "generation_model_requested": os.environ.get("GPT_MODEL", "gpt-4o"),
        "critic": {
            "provider": CRITIC_PROVIDER,
            "mode": cond["critic_mode"],
            "model_requested": os.environ.get("CRITIC_MODEL", DEFAULT_CRITIC_MODEL),
            "effort": os.environ.get("CRITIC_EFFORT", DEFAULT_CRITIC_EFFORT),
        },
        "call_log": call_log.summary(),
        "code": _git_info(),
        "environment": {"python": sys.version, "platform": platform.platform(), "packages": _package_versions()},
        "team": final_state.get("team", []),
        "team_selection_rationale": tsd.get("rationale", ""),
        "failed_team_trial_attempts": len(tsd.get("failed_trial_attempts", []) or []),
        "specialist_introductions": final_state.get("specialist_introductions", []),
        "sources": final_state.get("sources", []),
        "output_stats": _output_stats(conversations, final_report),
        "translation_error": final_state.get("translation_error", ""),
        "report_chars_en": len(final_report),
        "report_chars_ko": len(final_report_ko),
        "score_axes": ["evidence", "universality", "proportionality", "readability"],
    }
    _write_json(out_dir / "meta.json", meta)
    call_log.reset()

    print(f"[EXPERIMENT] {status}: {args.condition}_{args.run_id} attempt {args.attempt}, rounds={current_round}, "
          f"{int(meta['total_duration_seconds'] // 60)}m {int(meta['total_duration_seconds'] % 60)}s, "
          f"calls={meta['call_log']['calls_logged']}, models={meta['call_log']['response_models']}")
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
