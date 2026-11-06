# Revision experiment run log

Times in UTC unless noted. One entry per preparation step and per run attempt.

## 2026-11-06 — Retrieval snapshot built

- File: `experiments/runs_rev/retrieval_snapshot.json` (kept out of git until redistribution of the web excerpts is checked, revision_plan §13)
- SHA-256: `f36ac68c7df9267291d14ad50d7c1ed37a82ef05c07cf3ee453fbd8ea87d5104`
- Built with `scripts/revision/build_retrieval_snapshot.py`, default topic.
- Code state: commit `a4f2e48` plus the uncommitted step-5 routing code (utils/retrieval_snapshot.py and the call-site changes). The retrieval tools themselves (tools/web_search.py, tools/rag_search.py) were unchanged since commit `2145b52`.
- Pinecone index `virtual-lab`: 316 vectors (chunks), dimension 1536, single default namespace. "316 docs" in older project notes refers to chunks, not documents.
- Keys and sizes: specialist_rag 4320, specialist_web 7520, specialist_efsa 4327, critic_web 9137, pi_final_web 10497, pi_final_efsa 4327 characters. No empty results.
- RAG top-5 chunks came from three files: "Guidance on the scientific requirements for an application for authorisation of a novel food in.pdf" (3), "EU NGT Regulation 2025.pdf" (1), "EFSA Guidance on Novel Foods.pdf" (1).
- The snapshot was built before any pilot or main run and was not edited after the build.
