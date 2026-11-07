"""Build the fixed retrieval snapshot used by every pilot and main run (C4, 9.1).

Runs each retrieval of the experiment path exactly once, with the same queries the
agents use, and stores the exact text returned to the agents. The snapshot is built
in a temporary file under an exclusive lock and published only when all six
retrievals succeed; an existing snapshot is never overwritten.

Usage:
    python -B scripts/revision/build_retrieval_snapshot.py
    python -B scripts/revision/build_retrieval_snapshot.py --out experiments/runs_rev/retrieval_snapshot.json

Queries are built exactly as in the agents:
    specialist_rag   rag_query(topic, "safety assessment")          RAG (Pinecone, top-k chunks; no negation operators)
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
DEFAULT_INDEX = "virtual-lab-corpus-v1"  # corpus v1 (2026-11-07); v0 was "virtual-lab"
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


class _Fixed:
    """Tool stand-in returning a precomputed result (base-snapshot entry or a recorded RAG search)."""

    def __init__(self, name: str, result: str):
        self.name, self._result = name, result

    def invoke(self, _payload):
        return self._result


def build(out: Path, topic: str, tools: dict | None = None, index: str | None = None,
          base: str | None = None, per_document: str | None = None) -> str:
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
        if index:  # the RAG tool reads the index name from settings at import time
            os.environ["PINECONE_INDEX_NAME"] = index
        os.environ["VIRTUAL_LAB_RETRIEVAL_MODE"] = "record"
        os.environ["VIRTUAL_LAB_RETRIEVAL_SNAPSHOT"] = str(tmp)
        from utils import retrieval_snapshot as rs
        from utils.search_query import disambiguate, rag_query
        rs.reset()
        if tools is None:
            from tools.rag_search import rag_search_tool
            from tools.web_search import efsa_search, web_search
            tools = {"rag": rag_search_tool, "web": web_search, "efsa": efsa_search}

        rag_index = None
        if index:
            from config import settings
            if settings.PINECONE_INDEX_NAME != index:
                raise SystemExit(f"RAG would use index {settings.PINECONE_INDEX_NAME!r}, expected {index!r}")
            rag_index = index
        raw_rag = {}
        base_entries = {}
        if base:
            base_data = json.loads(Path(base).read_text(encoding="utf-8"))
            base_entries = base_data["entries"]
        started = datetime.now(timezone.utc).isoformat()
        for key, kind, intent in PLAN:
            query = rag_query(topic, intent) if kind == "rag" else disambiguate(topic, intent)
            if base and kind != "rag":
                entry = base_entries[key]  # unchanged web/EFSA retrieval from the base snapshot
                if entry["query"] != query:
                    raise SystemExit(f"base snapshot query differs for {key}")
                tool = _Fixed(entry.get("tool", kind), entry["result"])
            elif kind == "rag" and rag_index:
                # One search: the raw matches are recorded and the same matches are formatted for the agents.
                from config import settings
                from rag.pinecone_client import get_pinecone_client
                from tools.rag_search import format_docs
                if per_document:
                    cm = json.loads((ROOT / per_document).read_text(encoding="utf-8"))
                    doc_ids = [d["id"] for d in cm["documents"]]
                    candidates = get_pinecone_client().search_one_per_document(query, doc_ids, top_k=len(doc_ids))
                    raw_rag[key + "_all_documents"] = [
                        {"rank": i + 1, "doc_id": d["doc_id"], "id": d["id"], "score": d["score"],
                         "page": d["page"]} for i, d in enumerate(candidates)]
                    docs = candidates[:settings.TOP_K]
                else:
                    docs = get_pinecone_client().search(query, top_k=settings.TOP_K)
                if not docs:
                    raise SystemExit("RAG search returned no documents")
                raw_rag[key] = [{"rank": i + 1, "id": d.get("id"), "score": d.get("score"),
                                 "source": d.get("source"), "page": d.get("page")} for i, d in enumerate(docs)]
                tool = _Fixed("rag_search_tool", format_docs(docs))
            else:
                tool = tools[kind]
            text = rs.retrieve(key, tool, query)
            print(f"  {key:16s} {len(text):6d} chars{'  (EMPTY)' if not text.strip() else ''}")

        data = json.loads(tmp.read_text(encoding="utf-8"))
        data["build"] = {"topic": topic, "started_utc": started,
                         "finished_utc": datetime.now(timezone.utc).isoformat(),
                         "git_commit": _git_commit(), "python": sys.version, "packages": _versions(),
                         "script": "scripts/revision/build_retrieval_snapshot.py",
                         "rag_index": rag_index, "rag_raw_matches": raw_rag,
                         "rag_selection": ("top-1 chunk per document by a filtered Pinecone query per doc_id (approximate "
                                           "nearest neighbour), top TOP_K documents by score, ties by doc_id; documents from "
                                           + str(per_document)) if per_document else "top TOP_K chunks",
                         "base_snapshot": ({"path": str(base), "sha256": rs.file_sha256(Path(base)),
                                            "copied_keys": [k for k, kind, _ in PLAN if kind != "rag"]}
                                           if base else None)}
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
    p.add_argument("--index", default=DEFAULT_INDEX, help="Pinecone index of the RAG corpus")
    p.add_argument("--base", default=None,
                   help="earlier snapshot whose web/EFSA entries are copied unchanged (only the RAG entry is new)")
    p.add_argument("--per-document", default=None,
                   help="corpus manifest; RAG takes the best chunk of each listed document, then the top TOP_K")
    args = p.parse_args()
    out = (ROOT / args.out)
    digest = build(out, args.topic, index=args.index, base=(str(ROOT / args.base) if args.base else None),
                   per_document=args.per_document)
    print(f"snapshot: {out.resolve()}\nsha256:   {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
