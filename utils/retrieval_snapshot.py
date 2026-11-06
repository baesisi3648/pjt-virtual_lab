"""Fixed retrieval inputs for the revision experiment (revision_plan C4, 9.1).

Every retrieval in the experiment path goes through `retrieve(key, tool, query)`:

- live    (default; web server): call the tool, as in the submitted version.
- record  (snapshot preparation only): call the tool once per key and store the
          exact text returned, then reuse it. Written by
          scripts/revision/build_retrieval_snapshot.py before any experiment run.
- replay  (pilot and main runs): read only. A missing key, or a query that differs
          from the recorded one, raises SearchError. No live search, no file update.

Keys and call sites:
    specialist_rag / specialist_web / specialist_efsa   Round-1 specialist context
    critic_web      Critic verification context (same query every round, so one
                    fixed context is used for all rounds R1-R7)
    pi_final_web / pi_final_efsa   PI final synthesis (EFSA only if the specialist
                    EFSA context is empty)

Environment: VIRTUAL_LAB_RETRIEVAL_MODE, VIRTUAL_LAB_RETRIEVAL_SNAPSHOT.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from utils.errors import SearchError

MODES = ("live", "record", "replay")
FORMAT_VERSION = 1
KEYS = ("specialist_rag", "specialist_web", "specialist_efsa", "critic_web", "pi_final_web", "pi_final_efsa")

_lock = threading.Lock()
_cache: dict[str, Any] | None = None
_cache_path: Path | None = None
_cache_sha256: str | None = None
_used: set[str] = set()
_key_locks: dict[str, threading.Lock] = {k: threading.Lock() for k in KEYS}


def mode() -> str:
    m = os.environ.get("VIRTUAL_LAB_RETRIEVAL_MODE", "live")
    if m not in MODES:
        raise ValueError(f"Unknown VIRTUAL_LAB_RETRIEVAL_MODE: {m}")
    return m


def snapshot_path() -> Path:
    p = os.environ.get("VIRTUAL_LAB_RETRIEVAL_SNAPSHOT")
    if not p:
        raise SearchError("VIRTUAL_LAB_RETRIEVAL_SNAPSHOT is not set")
    return Path(p).resolve()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reset() -> None:
    """Forget the cached snapshot (tests, or a new run in the same process)."""
    global _cache, _cache_path, _cache_sha256
    with _lock:
        _cache, _cache_path, _cache_sha256 = None, None, None
        _used.clear()


def _load(path: Path, create: bool) -> dict[str, Any]:
    global _cache, _cache_path, _cache_sha256
    if _cache is not None and _cache_path == path:
        return _cache
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        _validate(data, path)
        _cache_sha256 = file_sha256(path)
    elif create:
        data = {"format_version": FORMAT_VERSION, "created_utc": datetime.now(timezone.utc).isoformat(),
                "settings": _settings(), "entries": {}}
    else:
        raise SearchError(f"Retrieval snapshot not found: {path}")
    _cache, _cache_path = data, path
    return data


def _validate(data: Any, path: Path) -> None:
    """Schema check: every entry must hold a string query and a string result."""
    if not isinstance(data, dict) or data.get("format_version") != FORMAT_VERSION:
        raise SearchError(f"Unsupported snapshot format in {path}")
    entries = data.get("entries")
    if not isinstance(entries, dict):
        raise SearchError(f"Snapshot {path} has no 'entries' object")
    for key, entry in entries.items():
        if key not in KEYS or not isinstance(entry, dict) \
                or not isinstance(entry.get("query"), str) or not isinstance(entry.get("result"), str):
            raise SearchError(f"Malformed snapshot entry {key!r} in {path}")


def _save(path: Path, data: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _settings() -> dict[str, Any]:
    """Retrieval settings in force when the snapshot was recorded."""
    try:
        from config import settings
        rag = {"vector_db": settings.VECTOR_DB_TYPE, "index": settings.PINECONE_INDEX_NAME,
               "embedding_model": settings.EMBEDDING_MODEL, "top_k": settings.TOP_K}
    except Exception as e:  # settings are descriptive only
        rag = {"error": str(e)[:200]}
    return {"rag": rag,
            "web": {"provider": "tavily", "max_results": 5, "search_depth": "advanced",
                    "include_domains": [".gov", "nature.com", "sciencedirect.com", "efsa.onlinelibrary.wiley.com"]},
            "efsa": {"provider": "tavily", "include_domains": ["efsa.onlinelibrary.wiley.com"]}}


def retrieve(key: str, tool, query: str) -> str:
    """Return the retrieval text for `key` according to the current mode."""
    if key not in KEYS:
        raise SearchError(f"Unknown retrieval key: {key}")
    m = mode()
    if m == "live":
        return tool.invoke({"query": query})

    path = snapshot_path()
    if m == "replay" and not path.is_file():
        # Checked on every call: a snapshot removed after loading is not silently reused.
        raise SearchError(f"Retrieval snapshot not found: {path}")
    # Per-key lock: in record mode each key is queried live at most once, even if
    # called concurrently (the global lock is released during the live call).
    with _key_locks[key]:
        with _lock:
            data = _load(path, create=(m == "record"))
            entry = data["entries"].get(key)
            if entry is not None:
                if entry["query"] != query:
                    raise SearchError(
                        f"Snapshot query mismatch for {key}: recorded {entry['query']!r}, requested {query!r}")
                _used.add(key)
                return entry["result"]
            if m == "replay":
                raise SearchError(f"Retrieval key {key!r} is missing from the snapshot {path}")

        result = tool.invoke({"query": query})  # record mode only; SearchError propagates
        if not isinstance(result, str):
            raise SearchError(f"Tool for {key} returned {type(result).__name__}, expected str")
        with _lock:
            data = _load(path, create=True)
            data["entries"][key] = {
                "key": key, "tool": getattr(tool, "name", type(tool).__name__), "query": query,
                "result": result, "result_chars": len(result), "empty": not result.strip(),
                "retrieved_utc": datetime.now(timezone.utc).isoformat(),
            }
            _save(path, data)
            _used.add(key)
        return result


def info() -> dict[str, Any]:
    """Snapshot provenance for meta.json."""
    m = mode()
    out: dict[str, Any] = {"mode": m, "keys_used": sorted(_used)}
    if m != "live":
        path = snapshot_path()
        out["path"] = str(path)
        out["sha256"] = file_sha256(path) if path.exists() else None
        out["sha256_at_load"] = _cache_sha256
    return out
