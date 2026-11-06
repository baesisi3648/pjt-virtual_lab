"""Per-call provenance log for revision experiments (revision_plan C5).

When a run is configured (by run_experiment.py), every LLM call made through
utils.llm appends one JSON line to `<run_dir>/calls.jsonl` immediately after it
completes or fails, so that an interrupted run still keeps its record.

Each record holds: call ID, UTC time, condition / run / attempt, the caller tag
(agent, round, ...), provider, the exact system and user messages sent, the
request parameters actually sent and those deliberately omitted, every HTTP
attempt, the raw response text, the response model identifier, fingerprint,
usage, finish / stop reason, request ID, latency, and the final status.
API keys are never recorded.

If no run is configured (for example the web server), logging is a no-op.
"""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from utils.redact import redact

_lock = threading.Lock()
_log_path: Path | None = None
_run_meta: dict[str, Any] = {}
_models_seen: dict[str, set[str]] = {}
_call_count = 0


def configure(log_path: Path, run_meta: dict[str, Any]) -> None:
    """Start logging to `log_path` (must not already exist)."""
    global _log_path, _run_meta, _models_seen, _call_count
    log_path = Path(log_path)
    if log_path.exists():
        raise FileExistsError(f"call log already exists: {log_path}")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.touch()
    with _lock:
        _log_path = log_path
        _run_meta = dict(run_meta)
        _models_seen = {}
        _call_count = 0


def reset() -> None:
    """Stop logging (used by tests)."""
    global _log_path, _run_meta, _models_seen, _call_count
    with _lock:
        _log_path = None
        _run_meta = {}
        _models_seen = {}
        _call_count = 0


def is_configured() -> bool:
    return _log_path is not None


def new_call_id() -> str:
    return uuid.uuid4().hex


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def record(entry: dict[str, Any]) -> None:
    """Append one call record. No-op when logging is not configured."""
    global _call_count
    if _log_path is None:
        return
    row = {**_run_meta, **entry}
    # Redact secrets from the serialised line (error bodies may echo keys).
    line = redact(json.dumps(row, ensure_ascii=False, default=str))
    with _lock:
        with _log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
        _call_count += 1
        provider = entry.get("provider", "unknown")
        # Every model the provider reported, including attempts that were rejected.
        models = {entry.get("response_model")} | {a.get("response_model") for a in entry.get("attempts", [])}
        for model in models - {None}:
            _models_seen.setdefault(provider, set()).add(model)


def summary() -> dict[str, Any]:
    """Models actually reported by the providers, and the number of calls logged."""
    with _lock:
        return {
            "calls_logged": _call_count,
            "response_models": {p: sorted(m) for p, m in _models_seen.items()},
        }
