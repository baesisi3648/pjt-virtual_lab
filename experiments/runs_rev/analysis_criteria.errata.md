# Errata to analysis_criteria.json (frozen v1.0, sha256 ab738113…)

The frozen file is not edited. Corrections are recorded here with dates.

## 2026-11-07 — retrieval_coverage_note

The note lists the snapshot contents as "EU NGT Regulation text, EFSA novel-food guidance, …". This is wrong.
The L7 corpus inventory (results/corpus/) shows that "EU NGT Regulation 2025.pdf" and "EFSA Guidance on Novel
Foods.pdf" in the snapshot are hand-written sample chunks from scripts/load_sample_to_pinecone.py with
document-like names and page numbers, not the documents those names suggest. The only real document retrieved
by the RAG step is EFSA Journal 2024;22:e8961 (novel-food guidance), three chunks (pp. 26, 27, 42; p. 42 is a
reference list). Judging items, categories and aggregation rules are unaffected. For the cause tag
"not_in_retrieval", judges treat the two sample chunks as retrieved text (they were given to the models).

## 2026-11-08 — retrieval_coverage_note for the corpus v1 main set (main_v1)

For the primary results (corpus v1, snapshot 56fecbf9…), the note is replaced as follows. Both source texts
(EFSA 2022 statement 7618 and Codex CXG 45-2003) are in the corpus v1 index. The fixed snapshot's RAG input
given to the specialists contains one chunk of CXG 45-2003 (p.12, comparator choice for nutritionally modified
foods) and no chunk of EFSA 7618; the other four RAG chunks are from EFSA 2025 (animals), EFSA 2024
(microorganisms), Health Canada and Japan MHLW. Web/EFSA results are those of v0. L3 therefore measures
conformity with authoritative texts of which one (CXG 45) was partly provided as input; agreement can reflect
retrieval, other inputs, the template and prior knowledge, which cannot be separated. Judging items, categories
and aggregation rules are unchanged.
