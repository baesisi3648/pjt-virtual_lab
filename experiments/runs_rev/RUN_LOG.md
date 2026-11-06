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

## 2026-11-06 — Pilot 1 (Critic claude-opus-5-5) — superseded

Code: commit `1db581c` (clean apart from untracked files). Output: `runs_rev/pilot/`. Not part of the main set.

- A_1 attempt_01: **failed** in round 2. Both Critic attempts ended with `stop_reason: refusal`, `stop_details.category: bio` (false positive on food-safety content). Round 1 completed (scores 3-4, readability 2-3). Team: Genetics, Bioinformatics, Toxicology, Risk, Regulatory Specialist. Duration 594 s, 30 calls.
- B_1 attempt_01: completed, 6 rounds, 1606 s, 61 calls, 0 errors. One `bio` refusal in round 1, passed on the retry. Score decreases occurred in round 5 despite the submitted do-not-lower rules. Team: Bioinformatics, Toxicology, Regulatory, Immunology, Risk Specialist. Tokens: OpenAI 476,879 in / 227,671 out; Claude 288,692 in / 89,157 out.
- Diagnostic: the refused round-2 Critic input of A_1 was sent once to `claude-opus-5` and returned valid JSON (not logged as a run).
- Decision (user, 2026-11-06): Critic changed to `claude-opus-5`, no server-side fallback (revision_plan 7.6). Pilot repeated as attempt_02 of A_1 and B_1.

## 2026-11-06 — Pilot 2 (Critic claude-opus-5)

Code: commit `1db581c` plus uncommitted Critic-model change (utils/llm.py default `claude-opus-5`). Output: `runs_rev/pilot/A_1/attempt_02`, `runs_rev/pilot/B_1/attempt_02`. Not part of the main set.

- A_1 attempt_02: ok. Ran to the 7-round cap without all-5 (one readability 4 at R7). 1432 s, 68 calls, 0 errors, no Critic refusals. Team: Genomics, Toxicology, Regulatory, Risk, Immunology Specialist. Tokens: OpenAI 511,346 in / 232,913 out; Claude 322,671 in / 54,619 out. Masked score mentions per Critic call: 0, 5, 11, 18, 23, 28, 33.
- B_1 attempt_02: ok. Converged at R4. 1021 s, 47 calls, 0 errors, no refusals. Team: Genetics, Bioinformatics, Toxicology, Risk, Regulatory Specialist. Tokens: OpenAI 280,492 in / 164,033 out; Claude 150,055 in / 31,920 out.
- Both: response models `gpt-5-2025-08-07` and `claude-opus-5`; retrieval snapshot sha256 unchanged at start and end; P4 effective (A: 7 "Additional data required", 3 "Decision deferred" nodes; B: 8 and 10); 5 decision trees each.
- Leakage audit (A): 252 candidate score mentions in Critic inputs, mostly the Critic's own prior feedback restating score levels ("carry universality to 5", "readability below 4"). Protocol development followed (masking and extraction changes); see revision_plan 7.6 and the pending decision on the prior-feedback channel.
- Extraction: C17 switched from a heading whitelist to exclusion after pilot A produced an extra safety-content section ("Explanatory Notes for the Decision Framework").

## 2026-11-06 — Pilot 3 (Critic claude-opus-5, score-free feedback in A)

Code: commit `1db581c` plus uncommitted protocol-development changes (Critic `claude-opus-5`; condition-A score-free feedback instruction in prompts_A and agents/critic.py; aggressive masking removed; extraction by exclusion; audit by channel). Output: `runs_rev/pilot/*/attempt_03`; analysis `runs_rev/pilot_analysis_attempt03/`. Not part of the main set.

- A_1 attempt_03: ok. Ran to the 7-round cap; scores stayed mostly at 4 (R1 mean ≈3.9 → R7 ≈4.3; no all-5). 1587 s, 68 calls, 0 errors, no refusals. Team: Genetics, Toxicology, Regulatory, Risk, Bioinformatics Specialist. Tokens: OpenAI 504,889 in / 245,337 out; Claude 298,870 in / 54,129 out.
- B_1 attempt_03: ok. All-5 at R5 (early stop). 1101 s, 54 calls, 0 errors, no refusals. Team: Genetics, Regulatory, Toxicology, Risk, Biostatistics Specialist.
- Pilot pass criteria (revision_plan 7.4), condition A:
  - Leakage audit: auditable, 7 Critic calls covering R1-R7. Candidates: prior_feedback 0, instructions 0, retrieval 0, specialist_outputs 2. Both candidates are the same sentence in R6 and R7 ("...transparency and proportionality. SDN‑3 follows..."), where the detector read the "3" of "SDN‑3" (Unicode hyphen). Draft judgement: not a score mention (false positive); to be confirmed by an author. Confirmed leaks 0; unjudged 0 after confirmation.
  - Masking: 0 tokens masked in all seven rounds, so no scientific content was altered.
  - Feedback: 0 score words across all A feedback; feedback still records "What improved" against earlier critique.
  - Termination: A stopped at the 7-round cap, B stopped early at all-5. Both as specified.
- Observation (n = 1 per condition, not a result): with score-free feedback, A's scores plateaued near 4, whereas pilot 2 A (feedback that restated score levels) approached 5.
