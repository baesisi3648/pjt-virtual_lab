"""L7 corpus composition (revision_plan 11): what the RAG index holds and what the runs actually retrieved.

    python -B scripts/revision/corpus_inventory.py      (experiment venv; read-only queries)

Writes experiments/runs_rev/results/corpus/:
- index_chunks.csv           every vector in the Pinecone index: id, source, page, text length
- index_documents.csv        per source document: chunks, pages, characters
- retrieval_sources.csv      sources in the fixed retrieval snapshot, per retrieval key
- corpus_summary.json        counts, extraction time and the index stats reported by Pinecone
Document attributes (agency, jurisdiction, year, type, scope) are added by hand in a separate sheet.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "experiments" / "runs_rev" / "results" / "corpus"
SNAPSHOT = ROOT / "experiments" / "runs_rev" / "retrieval_snapshot.json"


def index_vectors():
    from rag.pinecone_client import PineconeRAGClient
    client = PineconeRAGClient()
    index = client.index
    stats = index.describe_index_stats()
    stats = stats.to_dict() if hasattr(stats, "to_dict") else dict(stats)
    ids = []
    for ns in (stats.get("namespaces") or {"": {}}):
        token = None
        while True:  # paginated listing of vector ids (gRPC client returns ListResponse pages)
            page = index.list_paginated(namespace=ns, limit=100, pagination_token=token)
            ids.extend((ns, v.id) for v in page.vectors)
            token = getattr(page.pagination, "next", None) if page.pagination else None
            if not token:
                break
    rows = []
    by_ns = defaultdict(list)
    for ns, vid in ids:
        by_ns[ns].append(vid)
    batches = [(ns, vids[k:k + 100]) for ns, vids in by_ns.items() for k in range(0, len(vids), 100)]
    for ns, batch_ids in batches:  # fetch per namespace (a mixed batch would silently drop vectors)
        res = index.fetch(ids=batch_ids, namespace=ns)
        vecs = res.vectors if hasattr(res, "vectors") else res["vectors"]
        for vid, v in vecs.items():
            md = (v.metadata if hasattr(v, "metadata") else v["metadata"]) or {}
            rows.append({"namespace": ns, "id": vid, "source": md.get("source", ""), "page": md.get("page", ""),
                         "text_chars": len(md.get("text", "") or "")})
    fetched = {(r['namespace'], r['id']) for r in rows}
    if fetched != set(ids) or len(rows) != stats.get('total_vector_count', len(rows)):
        raise SystemExit(f"listed {len(ids)}, fetched {len(rows)}, stats {stats.get('total_vector_count')}: mismatch")
    return stats, rows


def snapshot_sources():
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    rows = []
    for key, entry in snap["entries"].items():
        text = entry.get("result", "") if isinstance(entry, dict) else str(entry)
        for m in re.finditer(r"\*\*출처\*\*: ([^\n]+?) \(p\.([\d.]+)\)", text):
            rows.append({"retrieval_key": key, "kind": "rag", "source": m.group(1), "page": m.group(2)})
        for url in dict.fromkeys(re.findall(r"https?://[^\s)\]>\"']+", text)):
            rows.append({"retrieval_key": key, "kind": "web/efsa", "source": url.rstrip(".,"), "page": ""})
    return rows


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    extracted = datetime.now(timezone.utc).isoformat()
    stats, chunks = index_vectors()
    chunks.sort(key=lambda r: (r["source"], float(r["page"] or 0), r["id"]))
    write_csv(OUT / "index_chunks.csv", chunks, ["namespace", "id", "source", "page", "text_chars"])

    docs = defaultdict(lambda: {"chunks": 0, "pages": set(), "chars": 0})
    for r in chunks:
        d = docs[r["source"]]
        d["chunks"] += 1
        d["pages"].add(r["page"])
        d["chars"] += r["text_chars"]
    doc_rows = [{"source": s, "chunks": d["chunks"], "distinct_pages": len(d["pages"]), "text_chars": d["chars"]}
                for s, d in sorted(docs.items(), key=lambda kv: -kv[1]["chunks"])]
    write_csv(OUT / "index_documents.csv", doc_rows, ["source", "chunks", "distinct_pages", "text_chars"])

    snap_rows = snapshot_sources()
    write_csv(OUT / "retrieval_sources.csv", snap_rows, ["retrieval_key", "kind", "source", "page"])

    summary = {
        "extracted_utc": extracted,
        "note": "Current index state at extraction time; not asserted to equal the index at the time of the "
                "submitted runs (revision_plan L7).",
        "pinecone_stats": json.loads(json.dumps(stats, default=str)),
        "index": {"vectors": len(chunks), "distinct_source_files": len(doc_rows)},
        "retrieval_snapshot": {
            "sha256_prefix": "f36ac68c",
            "keys": sorted({r["retrieval_key"] for r in snap_rows}),
            "rag_source_files": sorted({r["source"] for r in snap_rows if r["kind"] == "rag"}),
            "rag_chunks_retrieved": sum(1 for r in snap_rows if r["kind"] == "rag"),
            "distinct_urls": len({r["source"] for r in snap_rows if r["kind"] != "rag"}),
        },
    }
    (OUT / "corpus_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("index", "retrieval_snapshot")}, ensure_ascii=False, indent=2))
    for r in doc_rows:
        print(f'{r["chunks"]:>4}  {r["distinct_pages"]:>4}p  {r["source"]}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
