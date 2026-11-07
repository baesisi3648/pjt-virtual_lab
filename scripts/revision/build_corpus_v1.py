"""Build RAG corpus v1 into a new Pinecone index (revision, 2026-11-07).

    python -B scripts/revision/build_corpus_v1.py            (experiment venv)

Replaces the v0 index ("virtual-lab": EFSA novel-food guidance, a misnamed Codex labelling standard and five
hand-written sample chunks; RUN_LOG 2026-11-07). v0 is left untouched for reproducibility.

- Only the documents in REGISTRY are loaded, from reference/revision/corpus_v1/raw/ (not committed: licences).
- Chunking is the v0 loader's rule: per page (PDF) or per section (XML), 1,000-character slices, no overlap,
  slices with 50 or fewer non-space characters dropped. Embedding model and index settings as in v0.
- Fail-closed: a missing file, an empty extraction, a non-empty target index, an incomplete upload or a
  mismatch between expected and indexed vectors stops the build.
- Writes experiments/runs_rev/corpus_v1/corpus_manifest.json (hashes and counts, committed) and
  reference/revision/corpus_v1/chunks.jsonl (chunk text, local only).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

RAW = ROOT / "reference" / "revision" / "corpus_v1" / "raw"
LOCAL_OUT = ROOT / "reference" / "revision" / "corpus_v1"
MANIFEST_OUT = ROOT / "experiments" / "runs_rev" / "corpus_v1" / "corpus_manifest.json"
INDEX_NAME = "virtual-lab-corpus-v1"
CHUNK = 1000
MIN_CHARS = 50
CUTOFF = "2026-11-07"

# id, file, source name shown to the agents, citation, agency, jurisdiction, year, status, scope, licence note
REGISTRY = [
    ("codex_cxg44", "Codex_CXG44-2003.pdf", "Codex CXG 44-2003 Principles for the risk analysis of foods derived from modern biotechnology",
     "Codex Alimentarius Commission. CAC/GL 44-2003 (amended 2008, 2011)", "Codex", "international", "2003/2011", "adopted guideline", "all", "FAO terms of use"),
    ("codex_cxg45", "Codex_CXG45-2003.pdf", "Codex CXG 45-2003 Guideline for food safety assessment of foods derived from recombinant-DNA plants",
     "Codex Alimentarius Commission. CAC/GL 45-2003 (Annexes II-III 2008)", "Codex", "international", "2003/2008", "adopted guideline", "plants", "FAO terms of use"),
    ("codex_cxg46", "Codex_CXG46-2003.pdf", "Codex CXG 46-2003 Guideline for food safety assessment of foods produced using recombinant-DNA microorganisms",
     "Codex Alimentarius Commission. CAC/GL 46-2003", "Codex", "international", "2003", "adopted guideline", "microorganisms", "FAO terms of use"),
    ("codex_cxg68", "Codex_CXG68-2008.pdf", "Codex CXG 68-2008 Guideline for food safety assessment of foods derived from recombinant-DNA animals",
     "Codex Alimentarius Commission. CAC/GL 68-2008", "Codex", "international", "2008", "adopted guideline", "animals", "FAO terms of use"),
    ("efsa_2011_2150", "EFSA_2011_2150.pdf", "EFSA 2011 Guidance for risk assessment of food and feed from genetically modified plants",
     "EFSA GMO Panel. EFSA Journal 2011;9(5):2150", "EFSA", "EU", "2011", "guidance", "plants", "EFSA Journal terms"),
    ("efsa_2011_2193", "EFSA_2011_2193.pdf", "EFSA 2011 Guidance on the risk assessment of genetically modified microorganisms and their products",
     "EFSA GMO Panel. EFSA Journal 2011;9(6):2193", "EFSA", "EU", "2011", "guidance", "microorganisms", "EFSA Journal terms"),
    ("efsa_2012_2501", "EFSA_2012_2501.pdf", "EFSA 2012 Guidance on the risk assessment of food and feed from genetically modified animals",
     "EFSA GMO and AHAW Panels. EFSA Journal 2012;10(1):2501", "EFSA", "EU", "2012", "guidance", "animals", "EFSA Journal terms"),
    ("efsa_2012_2561", "EFSA_2012_2561.pdf", "EFSA 2012 Scientific opinion on plants developed through cisgenesis and intragenesis",
     "EFSA GMO Panel. EFSA Journal 2012;10(2):2561", "EFSA", "EU", "2012", "scientific opinion", "plants", "EFSA Journal terms"),
    ("efsa_2012_2943", "EFSA_2012_2943.pdf", "EFSA 2012 Scientific opinion on plants developed using the site-directed nuclease 3 technique",
     "EFSA GMO Panel. EFSA Journal 2012;10(10):2943", "EFSA", "EU", "2012", "scientific opinion", "plants", "EFSA Journal terms"),
    ("efsa_2020_6299", "EFSA_2020_6299.xml", "EFSA 2020 Applicability of the SDN-3 opinion to plants developed by SDN-1, SDN-2 and ODM",
     "EFSA GMO Panel. EFSA Journal 2020;18(11):6299", "EFSA", "EU", "2020", "scientific opinion", "plants", "CC BY-ND 4.0"),
    ("efsa_2022_7618", "EFSA_2022_7618.xml", "EFSA 2022 Criteria for risk assessment of plants produced by targeted mutagenesis, cisgenesis and intragenesis",
     "EFSA. EFSA Journal 2022;20(10):7618", "EFSA", "EU", "2022", "statement", "plants", "CC BY-ND 4.0"),
    ("efsa_2022_7621", "EFSA_2022_7621.xml", "EFSA 2022 Updated scientific opinion on plants developed through cisgenesis and intragenesis",
     "EFSA GMO Panel. EFSA Journal 2022;20(10):7621", "EFSA", "EU", "2022", "scientific opinion", "plants", "CC BY-ND 4.0"),
    ("efsa_2024_8895", "EFSA_2024_8895.xml", "EFSA 2024 New developments in biotechnology applied to microorganisms",
     "EFSA GMO Panel. EFSA Journal 2024;22(7):e8895", "EFSA", "EU", "2024", "scientific opinion", "microorganisms", "CC BY-ND 4.0"),
    ("efsa_2025_9566", "EFSA_2025_9566.xml", "EFSA 2025 New developments in biotechnology applied to animals",
     "EFSA GMO Panel. EFSA Journal 2025;23(8):e9566", "EFSA", "EU", "2025", "scientific opinion", "animals", "CC BY-ND 4.0"),
    ("eu_com_2023_411", "EU_COM_2023_411_proposal.pdf", "European Commission 2023 Proposal for a regulation on plants obtained by new genomic techniques COM(2023) 411",
     "European Commission. COM(2023) 411 final, 5.7.2023", "European Commission", "EU", "2023", "legislative proposal", "plants", "EUR-Lex reuse policy"),
    ("eu_reg_2026_1388", "EU_NGT_Regulation_2026_adopted.pdf", "Regulation (EU) 2026/1388 on plants obtained by certain new genomic techniques",
     "Regulation (EU) 2026/1388 of 17 June 2026", "European Parliament and Council", "EU", "2026", "adopted regulation", "plants", "EUR-Lex reuse policy"),
    ("fsanz_p1055", "FSANZ_P1055_ApprovalReport_2025.pdf", "FSANZ 2025 Approval Report P1055 Definitions for gene technology and new breeding techniques",
     "Food Standards Australia New Zealand. Approval Report P1055, 18 June 2025", "FSANZ", "Australia/New Zealand", "2025", "approval report", "all", "FSANZ copyright terms"),
    ("health_canada_nf", "HealthCanada_NovelFoods_Guidelines.pdf", "Health Canada Guidelines for the Safety Assessment of Novel Foods (2006, 2022 plant breeding appendices)",
     "Health Canada. Guidelines for the Safety Assessment of Novel Foods (2006; appendices 2022)", "Health Canada", "Canada", "2006/2022", "guidance", "all", "Government of Canada terms"),
    ("japan_mhlw", "Japan_MHLW_GenomeEditing_Procedures_2019rev2020_EN.pdf", "Japan MHLW Food hygiene handling procedures for food and additives derived from genome editing technology",
     "Ministry of Health, Labour and Welfare (Japan), 2019, amended 2020 (English)", "MHLW", "Japan", "2019/2020", "administrative procedure", "all", "MHLW terms"),
]
FIELDS = ("id", "file", "source", "citation", "agency", "jurisdiction", "year", "status", "scope", "licence")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def units_pdf(path: Path):
    """(unit number, location label shown to the agents, text): one unit per PDF page, labelled by page."""
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    return [(i, i, page.extract_text() or "") for i, page in enumerate(reader.pages, start=1)]


def units_xml(path: Path):
    """Each top-level body section is one unit (the PDF loader's 'page'); title and abstract form unit 1.
    XML full texts have no page numbers, so the location label is "abstract" or "section <label>"."""
    root = ET.parse(path).getroot()
    text = lambda el: " ".join("".join(el.itertext()).split()) if el is not None else ""
    head = [text(root.find(".//article-title")), text(root.find(".//abstract"))]
    units = [(1, "abstract", "\n".join(h for h in head if h))]
    body = root.find(".//body")
    for i, sec in enumerate(body.findall("sec") if body is not None else [], start=2):
        lab, title = sec.find("label"), sec.find("title")
        num = (lab.text or "").strip().rstrip(".") if lab is not None else ""
        if num:
            label = f"section {num}"
        else:  # unnumbered (Summary, Glossary, References, ...): use the heading itself
            label = (" ".join("".join(title.itertext()).split()) if title is not None else "") or f"unnumbered part {i - 1}"
        units.append((i, label, text(sec)))
    return units


def chunk_units(doc_id: str, source: str, units):
    out, n = [], 0
    for unit, label, text in units:
        for k in range(0, len(text), CHUNK):
            piece = text[k:k + CHUNK]
            if len(piece.strip()) > MIN_CHARS:
                out.append({"id": f"{doc_id}_{unit}_{n}", "doc_id": doc_id, "source": source, "page": label, "text": piece})
                n += 1
    return out


def embed(client, texts, model):
    vecs = []
    for k in range(0, len(texts), 100):
        for attempt in range(5):
            try:
                resp = client.embeddings.create(model=model, input=texts[k:k + 100])
                vecs.extend(d.embedding for d in resp.data)
                break
            except Exception:
                if attempt == 4:
                    raise
                time.sleep(2 ** attempt)
    return vecs


def main() -> int:
    from config import settings
    from openai import OpenAI
    from pinecone import Pinecone, ServerlessSpec

    docs = [dict(zip(FIELDS, row)) for row in REGISTRY]
    missing = [d["file"] for d in docs if not (RAW / d["file"]).is_file()]
    if missing:
        raise SystemExit(f"missing raw files: {missing}")
    extra = sorted(p.name for p in RAW.iterdir() if p.is_file() and p.name not in {d["file"] for d in docs})
    if extra:
        raise SystemExit(f"files in raw/ that are not in the registry (remove or register): {extra}")

    chunks = []
    for d in docs:
        path = RAW / d["file"]
        raw = path.read_bytes()
        units = units_pdf(path) if path.suffix == ".pdf" else units_xml(path)
        full = "\n".join(t for _, _, t in units)
        if len(full.strip()) < 1000:
            raise SystemExit(f"{d['file']}: extraction too short ({len(full.strip())} chars)")
        c = chunk_units(d["id"], d["source"], units)
        if not c:
            raise SystemExit(f"{d['file']}: no chunks")
        d.update(raw_sha256=sha256(raw), units=len(units), extracted_chars=len(full),
                 extracted_sha256=sha256(full.encode("utf-8")), chunks=len(c),
                 chunk_ids_sha256=sha256("\n".join(x["id"] for x in c).encode()))
        chunks.extend(c)
    ids = [c["id"] for c in chunks]
    if len(set(ids)) != len(ids):
        raise SystemExit("duplicate chunk ids")

    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    if INDEX_NAME not in [i.name for i in pc.list_indexes()]:
        pc.create_index(name=INDEX_NAME, dimension=1536, metric="cosine",
                        spec=ServerlessSpec(cloud="aws", region="us-east-1"))
        while not pc.describe_index(INDEX_NAME).status["ready"]:
            time.sleep(2)
    index = pc.Index(INDEX_NAME)
    if index.describe_index_stats().total_vector_count:
        if "--replace" not in sys.argv:
            raise SystemExit(f"index {INDEX_NAME} is not empty; refusing to load into it (--replace rebuilds v1)")
        index.delete(delete_all=True)
        for _ in range(60):
            if not index.describe_index_stats().total_vector_count:
                break
            time.sleep(5)

    oa = OpenAI(api_key=settings.OPENAI_API_KEY)
    vectors = embed(oa, [c["text"] for c in chunks], settings.EMBEDDING_MODEL)
    for k in range(0, len(chunks), 100):
        batch = [{"id": c["id"], "values": v,
                  "metadata": {"text": c["text"], "source": c["source"], "page": c["page"], "doc_id": c["doc_id"]}}
                 for c, v in zip(chunks[k:k + 100], vectors[k:k + 100])]
        index.upsert(vectors=batch)

    for _ in range(60):  # serverless indexes report counts with a delay
        if index.describe_index_stats().total_vector_count == len(chunks):
            break
        time.sleep(5)
    total = index.describe_index_stats().total_vector_count
    if total != len(chunks):
        raise SystemExit(f"index holds {total} vectors, expected {len(chunks)}")
    for k in range(0, len(ids), 100):  # every chunk retrievable with its exact text
        got = index.fetch(ids=ids[k:k + 100]).vectors
        for c in chunks[k:k + 100]:
            v = got.get(c["id"])
            if v is None or v.metadata.get("text") != c["text"]:
                raise SystemExit(f"chunk {c['id']} missing or altered in the index")

    LOCAL_OUT.mkdir(parents=True, exist_ok=True)
    with (LOCAL_OUT / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "corpus_version": "v1", "built_utc": datetime.now(timezone.utc).isoformat(), "cutoff": CUTOFF,
        "index": {"name": INDEX_NAME, "namespace": "", "dimension": 1536, "metric": "cosine",
                  "cloud": "aws", "region": "us-east-1", "vectors": total},
        "embedding_model": settings.EMBEDDING_MODEL,
        "chunking": {"unit": "PDF page (label: page number) or XML top-level section (label: 'abstract' or 'section N')", "size": CHUNK,
                     "overlap": 0, "drop_if_nonspace_chars_le": MIN_CHARS,
                     "pdf_library": f"pypdf {metadata.version('pypdf')}"},
        "replaces": "v0 index 'virtual-lab' (kept unchanged; see RUN_LOG 2026-11-07)",
        "documents": docs,
        "chunks_sha256": sha256("\n".join(json.dumps(c, ensure_ascii=False, sort_keys=True) for c in chunks).encode("utf-8")),
    }
    MANIFEST_OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"index {INDEX_NAME}: {total} vectors from {len(docs)} documents")
    for d in docs:
        print(f"  {d['chunks']:>5}  {d['id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
