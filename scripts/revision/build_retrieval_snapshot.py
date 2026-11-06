"""Build the fixed retrieval snapshot used by every pilot and main run (C4, 9.1).

Runs each retrieval of the experiment path exactly once, with the same queries the
agents use, and stores the exact text returned to the agents. The snapshot is built
in a temporary file under an exclusive lock and published only when all six
retrievals succeed; an existing snapshot is never overwritten.

Usage:
    python -B scripts/revision/build_retrieval_snapshot.py
    python -B scripts/revision/build_retrieval_snapshot.py --out experiments/runs_rev/retrieval_snapshot.json

Queries are built exactly as in the agents:
    specialist_rag   disambiguate(topic, "safety assessment")       RAG (Pinecone, top-k chunks)
    specialist_web   disambiguate(topic, "regulation 2025")         Tavily
    specialist_efsa  disambiguate(topic, "EFSA opinion")            Tavily, EFSA Journal only
    critic_web       disambiguate(topic, "regulatory verification") Tavily
    pi_final_web     disambiguate(topic, "safety framework 2025")   Tavily
    pi_final_efsa    disambiguate(topic, "EFSA opinion")            Tavily, EFSA Journal only

What is stored is the formatted text each tool returns to the agents (titles,
content, source URLs and relevance for web results; source file, page and
similarity for RAG chunks). This is exactly the retrieval input of every run.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

DEFAULT_OUT = "experiments/runs_rev/retrieval_snapshot.json"
PLAN = [
    ("specialist_rag", "rag", "safety assessment"),
    ("specialist_web", "web", "regulation 2025"),
    ("specialist_efsa", "efsa", "EFSA opinion"),
    ("critic_web", "web", "regulatory verification"),
    ("pi_final_web", "web", "safety framework 2025"),
    ("pi_final_efsa", "efsa", "EFSA opinion"),
]


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return None


def _versions() -> dict:
    out = {}
    for name in ("tavily-python", "pinecone", "openai", "langchain-core"):
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = None
    return out


def build(out: Path, topic: str, tools: dict | None = None) -> str:
    """Build and publish the snapshot; return its sha256. `tools` may be injected for tests."""
    out = out.resolve()
    if out.exists():
        raise SystemExit(f"snapshot already exists, refusing to overwrite: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    lock = out.with_name(out.name + ".lock")
    tmp = out.with_name(out.name + ".building")
    try:
        lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)  # exclusive: one builder at a time
    except FileExistsError:
        raise SystemExit(f"another build holds the lock (remove it only if no build is running): {lock}")
    try:
        if tmp.exists():
            tmp.unlink()
        os.environ["VIRTUAL_LAB_RETRIEVAL_MODE"] = "record"
        os.environ["VIRTUAL_LAB_RETRIEVAL_SNAPSHOT"] = str(tmp)
        from utils import retrieval_snapshot as rs
        from utils.search_query import disambiguate
        rs.reset()
        if tools is None:
            from tools.rag_search import rag_search_tool
            from tools.web_search import efsa_search, web_search
            tools = {"rag": rag_search_tool, "web": web_search, "efsa": efsa_search}

        started = datetime.now(timezone.utc).isoformat()
        for key, kind, intent in PLAN:
            text = rs.retrieve(key, tools[kind], disambiguate(topic, intent))
            print(f"  {key:16s} {len(text):6d} chars{'  (EMPTY)' if not text.strip() else ''}")

        data = json.loads(tmp.read_text(encoding="utf-8"))
        data["build"] = {"topic": topic, "started_utc": started,
                         "finished_utc": datetime.now(timezone.utc).isoformat(),
                         "git_commit": _git_commit(), "python": sys.version, "packages": _versions(),
                         "script": "scripts/revision/build_retrieval_snapshot.py"}
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        if out.exists():
            raise SystemExit(f"snapshot appeared during the build, refusing to overwrite: {out}")
        os.rename(tmp, out)  # publish (rename never overwrites on Windows)
        rs.reset()
        return rs.file_sha256(out)
    finally:
        os.close(lock_fd)
        if tmp.exists():
            tmp.unlink()
        lock.unlink()


def main() -> int:
    from run_experiment import DEFAULT_TOPIC

    p = argparse.ArgumentParser()
    p.add_argument("--out", default=DEFAULT_OUT)
    p.add_argument("--topic", default=DEFAULT_TOPIC)
    args = p.parse_args()
    out = (ROOT / args.out)
    digest = build(out, args.topic)
    print(f"snapshot: {out.resolve()}\nsha256:   {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
