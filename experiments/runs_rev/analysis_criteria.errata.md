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
