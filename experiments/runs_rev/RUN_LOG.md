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

## 2026-11-06 — Manifest frozen (step 9)

- Code: commit `98de637` (manifest module, run-time check), `b18e0ef` (balanced order). 45 tracked code files hashed by content.
- First build (sha256 `e675dcae…`) drew B first in all five blocks (seed 20261106, unrestricted shuffle). Because that aligns condition with time, the rule was changed before any main run to draw, with the same seed, from the 20 sequences where each condition goes first in 2 or 3 blocks. The first file is kept as `experiment_manifest.superseded_unbalanced_order.json`; it was never used.
- Active manifest: `experiment_manifest.json`, sha256 `ae922a5db1a34e8c3eaa95b218d7a4d79989a56fe93fee0228cec20c5d1bb66c`.
  - Order: A_1, B_1, A_2, B_2, B_3, A_3, A_4, B_4, B_5, A_5 (out-dir `runs_rev/main`).
  - Models: generation `gpt-5` (requested), Critic `claude-opus-5`, effort high. MAX_ROUNDS 7. Up to 3 attempts per run, retried immediately.
  - Retrieval snapshot sha256 `f36ac68c7df9267291d14ad50d7c1ed37a82ef05c07cf3ee453fbd8ea87d5104`, replay mode.
  - Environment: Python 3.12.10, 84 installed distributions (all enforced).
  - Second-judge sample (seed 20261107): A_4, B_1, B_2. Blinding seed 20261108.
- Analysis criteria: two-stage freeze (revision_plan 7.3). `analysis_criteria.json` (L3 codebook etc.) is frozen before any main-run report or deliberation text is opened; until then only run status and call-log completeness are checked.
- Decision before freezing: MAX_ROUNDS kept at 7, as in the submitted system (pilot 3 A gained about one 5-score cell per round; 10 rounds would not change the non-convergence outcome).

## 2026-11-06 — Main runs interrupted: OpenAI credit balance exhausted

- Completed (status ok, call logs complete, Critic stop_reason end_turn in every call, manifest ae922a5d): A_1 (18:42–19:17), B_1 (19:17–19:41), A_2 (19:41–20:19).
- B_2 attempt_01 failed at round 4–5 (20:44) with repeated OpenAI HTTP 429. Every later attempt (B_2 #2–3, B_3, A_3, A_4, B_4, B_5, A_5, three each) failed in about 4 minutes during team composition: 30 OpenAI calls, all HTTP 429, no successful response. The driver marked these runs "exhausted".
- Cause, confirmed with one test call at about 22:30 KST: HTTP 429, error type `insufficient_quota`, code `credit_balance_exhausted` ("You have no credits remaining"). This is an account billing state, not request-rate limiting; the pipeline logged it as "rate limit exceeded" because the 429 body is not recorded.
- No report or deliberation text of any run was opened. All failed attempt folders are kept.
- Pending decision: how to resume after credits are added (protocol amendment needed, because the manifest allows at most 3 attempts per run and all 24 attempts were consumed by the billing failure).

## 2026-11-07 — Manifest amendment 1

- After the outage, the original 3-attempt limit was changed once, before any report was opened: the 21 failed attempts of the outage (2026-11-06 20:19–22:09 KST) are excluded from attempt counting and kept on disk. Attempts in total so far: 24 (3 successful, 21 excluded). Their outputs and scores are not used.
- The 429 response bodies of those attempts were not recorded; the cause (credit balance exhausted) is inferred from the timing, the identical failure pattern and the diagnostic calls (2026-11-06 22:30 KST; 2026-11-07, still `credit_balance_exhausted` after the reported top-up).
- Only code change: `utils/manifest.py` (amendment-aware counting). Prompts, snapshot, models, limits, order and environment unchanged (checked by `scripts/revision/amend_manifest.py`).
- v1 kept as `experiment_manifest.v1.json` (sha256 ae922a5d…). Amended manifest `experiment_manifest.json`, sha256 `b24eefac8a45b30a1b15d6323f005403f12ba78e636fcf9625d93f055659b780`.
- A_1, B_1, A_2 remain valid (run under v1; v1 and the amendment differ only in attempt counting). Resumption starts at B_2 attempt_04.
- Driver: OpenAI preflight before each attempt (logged to `main_logs/preflight.jsonl`), stop on any non-200.

## 2026-11-07 — Main runs complete

- Resumed 14:25 KST after the credit top-up; every preflight ok. B_2, B_3, A_3, A_4, B_4, B_5, A_5 each succeeded at attempt_04 (amended manifest b24eefac). Finished 16:48 KST.
- All ten runs: status ok, call logs complete, 0 failed calls, Critic stop_reason end_turn throughout, response models `gpt-5-2025-08-07` and `claude-opus-5` in every run (same as before the outage).
- Termination (L2 input; no report text opened): condition A ran to the 7-round cap in all five runs; condition B stopped early at all-5 after 4, 6, 4, 4 and 3 rounds (B_1–B_5).
- Next: freeze the L3 codebook (analysis_criteria.json) before any report or deliberation text is opened.

## 2026-11-07 — L3 codebook frozen

- `analysis_criteria.json` v1.0, sha256 `ab7381138d61647983205e7c83e2e46ed91215bfb1179c45cc93c71a14412df9`, frozen from draft v0.3 (30 items, 13 critical, 17 decision points) before any main-run report or deliberation text was opened.
- Frozen at the corresponding author's request without the primary judge's prior review; the primary judge's comments are recorded at judging time as notes.
- Next: automated analyses (L1 similarity, L2 scores, L8 statistics, representative run).

## 2026-11-07 — Automated analyses (L1, L2, L8, representative run)

`analyze_revision.py --runs-dir runs_rev/main --out-dir runs_rev/results`; 10 runs, no issues; embeddings text-embedding-3-large.
- L2 termination: A 0/5 reached all-5 (all stopped at the 7-round cap); B 5/5 reached all-5 (rounds 3, 4, 4, 4, 6). Fisher exact two-sided p = 0.008 (0/5 vs 5/5). Score decreases: A 51, B 4 (per specialist-axis, between consecutive rounds).
- L1 content similarity (primary; pairs not independent, descriptive): within A 0.904 (range 0.823–0.968), within B 0.892 (0.771–0.971), A vs B 0.903 (0.791–0.976). Full-text similarity: within A 0.924, within B 0.954, A vs B 0.942.
- Representative run (condition-A medoid, pre-specified rule): A_5 (mean 0.930). A_3 has the lowest mean similarity (0.839).
- Leakage audit (condition A Critic inputs): 12 candidates, all in specialist outputs; draft judgement: all 12 are SDN category numbers (SDN-1/2/3), not score mentions (`results/leakage_judgement.draft.json`, author confirmation pending). Prior-feedback channel 0; masking fired 0 times, so no scientific text was altered.

## 2026-11-07 — Blinding and judging kit (L3, L4, L9)

- `scripts/revision/build_judging_kit.py` (system Python; the experiment venv untouched). Output in `reference/revision/judging/` (not committed).
- Anonymous IDs R01–R10 drawn with the manifest blinding seed 20261108. Key file `blinding_key.json`, sha256 `4a4d9a3b33c3f56f32f4e55211d7be281213deacb69824e4d9e6409ca0ea001c`; judges do not open it until judging is complete. Second-judge sample (manifest: A_4, B_1, B_2) maps to three IDs listed in the second-judge sheet. External judges receive the representative run A_5 under its ID.
- Blinded reports: the generated report minus the Methods section (it shows rounds and statistics, hence the condition); nothing else edited. A scan found no condition, run, round or score cues in the remaining text; length, reference format and duplicated bodies remain possible indirect cues (Codex review).
- Output defect found while preparing the blinded reports (after the codebook was frozen, before judging): in 3 of 10 runs the final-synthesis output of the model contains the report body twice, the second time shorter (raw `response_text` of the PI final-synthesis call; not a pipeline bug). Rule set 11/7 before judging: the whole report is one judging unit, judged as generated; repetition is not counted twice; contradictory statements follow the conflict-first rule; L4 keeps differing branches. Reported in Methods/Results as an output defect.
- One Korean translation (one B run) is partly untranslated; Korean versions are reference only and judging uses the English original.
- Primary sheet: L3 (status, multi-tag causes, location, item notes), critical cases, AI additions, L4 per branch (location, applicability, presence, condition and target in original and normalised form, outcome type) and a normalisation table. Second sheet: L3 status only with the same frozen item notes (neutral wording). External form (R05) regenerated from the frozen codebook with the same item notes.
- (later on 11/7, before any judging) At the corresponding author's request, the blinded reports again include the team-composition subsection of Methods as an "Expert Panel" section (ten composition trials, role frequencies, PI selection rationale, specialist self-introductions). Team composition precedes Critic scoring and uses identical prompts in A and B, so it carries no condition information; rounds, per-agent statistics, timings and score charts stay withheld. Applied identically to all judges' copies; the anonymous IDs and the key are unchanged.
