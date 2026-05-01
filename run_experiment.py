"""CLI entry point for a reproducibility-tracked workflow execution.

Usage:
    python run_experiment.py --run-id 1
    python run_experiment.py --run-id 2 --topic "..." --constraints "..."

For each run, this script:
1. Executes the full LangGraph workflow.
2. Writes the artefacts to `experiments/runs/run_<ID>/`:
     - final_report.md           — the English final report
     - final_report.ko.md        — the Korean translation (sidecar)
     - critic_scores.json        — per-round 4-axis scores for every specialist
     - meta.json                 — round durations, agent turn statistics, team composition
     - messages.json             — full message log
3. Prints a one-line summary on stdout.

The five runs produced by this script feed into
`experiments/reproducibility/analyze.py`, which computes the semantic
similarity matrix (Figure 2D) and the Critic-score CV (Figure 2C with error
bars).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Same anti-cache behaviour as server.py.
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECACHE"] = "1"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_TRACING"] = "false"

from workflow.graph import create_workflow  # noqa: E402
from workflow.state import AgentState  # noqa: E402

DEFAULT_TOPIC = (
    "Derivation of a standard safety assessment framework for "
    "genome-edited foods (NGT)."
)
DEFAULT_CONSTRAINTS = (
    "Avoid the GMO-style blanket strictness; require additional data only "
    "when there is a clear scientific basis. Be proportionate and rational."
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one reproducibility-tracked workflow execution.")
    parser.add_argument("--run-id", default=None,
                        help="Run identifier; defaults to a UTC timestamp.")
    parser.add_argument("--topic", default=DEFAULT_TOPIC,
                        help="Research topic (English).")
    parser.add_argument("--constraints", default=DEFAULT_CONSTRAINTS,
                        help="Additional constraints (English).")
    parser.add_argument("--out-dir", default="experiments/runs",
                        help="Output base directory.")
    return parser.parse_args()


def _agent_turn_stats(messages: list[dict]) -> dict:
    """Same logic as agents.pi._compute_word_counts but kept local for portability."""
    stats: dict[str, dict[str, int]] = {}
    for msg in messages:
        role = msg.get("role", "unknown")
        name = msg.get("name", role)
        content = msg.get("content", "")
        if role == "specialist":
            agent_key = name
        elif role == "pi":
            agent_key = "PI"
        elif role == "critic":
            agent_key = "Critic"
        elif role == "translator":
            agent_key = "Translator"
        else:
            agent_key = role
        if agent_key not in stats:
            stats[agent_key] = {"count": 0, "chars": 0}
        stats[agent_key]["count"] += 1
        stats[agent_key]["chars"] += len(content)
    return stats


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    args = _parse_args()

    run_id = args.run_id or datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out_dir) / f"run_{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*80}")
    print(f"[EXPERIMENT] Run ID: {run_id}")
    print(f"[EXPERIMENT] Output: {out_dir.resolve()}")
    print(f"[EXPERIMENT] Topic:  {args.topic}")
    print(f"{'='*80}\n")

    workflow = create_workflow()
    initial_state: AgentState = {
        "topic": args.topic,
        "constraints": args.constraints,
        "team": [],
        "specialist_outputs": [],
        "draft": "",
        "critique": None,
        "current_round": 1,
        "meeting_history": [],
        "final_report": "",
        "final_report_ko": "",
        "messages": [],
        "parallel_views": [],
        "sources": [],
        "cached_efsa_context": "",
        "team_selection_data": None,
        "specialist_introductions": [],
        "word_counts": {},
        "critic_score_history": [],
        "run_id": run_id,
    }

    started_wall = time.time()
    started_iso = datetime.utcnow().isoformat() + "Z"

    # Track round durations by snapshotting node-event timestamps.
    round_durations: dict[int, float] = {}
    round_start: dict[int, float] = {1: started_wall}
    current_round_seen = 1

    final_state: dict = {}

    for event in workflow.stream(initial_state):
        for node_name, node_state in event.items():
            if node_name == "increment_round":
                # Close out the round that just ended.
                round_durations[current_round_seen] = time.time() - round_start.get(
                    current_round_seen, time.time()
                )
                new_round = node_state.get("current_round", current_round_seen + 1)
                current_round_seen = new_round
                round_start[current_round_seen] = time.time()
            elif node_name == "final_synthesis":
                if current_round_seen not in round_durations:
                    round_durations[current_round_seen] = (
                        time.time() - round_start.get(current_round_seen, time.time())
                    )
            # Track the latest snapshot of each state field.
            for key, value in node_state.items():
                final_state[key] = value

    total_duration = time.time() - started_wall

    final_report = final_state.get("final_report", "") or ""
    final_report_ko = final_state.get("final_report_ko", "") or ""

    # Backfill the Methods → Execution Statistics table with real durations.
    if final_report and round_durations:
        import re as _re

        def _hms(s: float) -> str:
            return f"{int(s // 60)} min {int(s % 60)} s"

        rows = [f"| Round {r} | {_hms(round_durations[r])} |" for r in sorted(round_durations)]
        rows.append(f"| **Total** | **{_hms(total_duration)}** |")
        new_table = "| Round | Duration |\n|-------|----------|\n" + "\n".join(rows) + "\n"
        placeholder_re = _re.compile(
            r"\| Round \| Duration \|\n\|-+\|-+\|\n(?:\|[^\n]*\|\n)+",
            _re.MULTILINE,
        )
        if placeholder_re.search(final_report):
            final_report = placeholder_re.sub(new_table, final_report, count=1)
        else:
            final_report += "\n\n### Execution Statistics\n\n" + new_table
    score_history = final_state.get("critic_score_history", []) or []
    messages = final_state.get("messages", []) or []
    team = final_state.get("team", []) or []
    team_selection_data = final_state.get("team_selection_data") or {}
    introductions = final_state.get("specialist_introductions", []) or []
    sources = final_state.get("sources", []) or []

    # ─ Persist artefacts ───────────────────────────────────────────
    (out_dir / "final_report.md").write_text(final_report, encoding="utf-8")
    if final_report_ko:
        (out_dir / "final_report.ko.md").write_text(final_report_ko, encoding="utf-8")

    (out_dir / "critic_scores.json").write_text(
        json.dumps(score_history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (out_dir / "messages.json").write_text(
        json.dumps(messages, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    meta = {
        "run_id": run_id,
        "started_at": started_iso,
        "topic": args.topic,
        "constraints": args.constraints,
        "total_duration_seconds": round(total_duration, 2),
        "rounds_completed": current_round_seen,
        "round_durations_seconds": {str(r): round(d, 2) for r, d in sorted(round_durations.items())},
        "agent_turn_stats": _agent_turn_stats(messages),
        "team": team,
        "team_selection_rationale": team_selection_data.get("rationale", ""),
        "team_size": len(team),
        "specialist_introductions": introductions,
        "sources": sources,
        "report_chars_en": len(final_report),
        "report_chars_ko": len(final_report_ko),
        "score_axes": ["evidence", "universality", "proportionality", "readability"],
    }
    (out_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # ─ Console summary ─────────────────────────────────────────────
    minutes = int(total_duration // 60)
    seconds = int(total_duration % 60)
    print(f"\n{'='*80}")
    print(f"[EXPERIMENT] Run {run_id} complete")
    print(f"  Total: {minutes}m {seconds}s, rounds: {current_round_seen}")
    print(f"  Final report (EN): {len(final_report):,} chars")
    print(f"  Final report (KO): {len(final_report_ko):,} chars")
    print(f"  Score history snapshots: {len(score_history)}")
    print(f"  Output: {out_dir.resolve()}")
    print(f"{'='*80}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
