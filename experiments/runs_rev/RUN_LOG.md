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

## 2026-11-07 — Judging packages sent

- The corresponding author sent the four packages (primary judge, second judge, external judges 1 and 2) on 2026-11-07. Package sha256 (first 16 hex):
  - 1_주판정자_함준혁.zip c61d6eb88ae0a41a
  - 2_2차판정자.zip c7409e6a8e8bcc9c
  - 3_외부판정자_1.zip dc93ebb55a935ab9
  - 4_외부판정자_2.zip 5a5bd8ff2690e25b
- Second judge and external judges' names, and reply deadlines, to be recorded when confirmed.

## 2026-11-07 — L7 corpus inventory: placeholder documents in the RAG index

`scripts/revision/corpus_inventory.py` (read-only Pinecone listing; outputs in `results/corpus/`).
- The index holds 316 vectors (chunks), not documents: 271 chunks of EFSA Journal 2024;22:e8961 (novel-food guidance), 40 chunks of Codex CXS 1-1985 (General Standard for the Labelling of Pre-packaged Foods) stored as "Codex Guideline Section 4.2.pdf", and 5 hand-written sample chunks from `scripts/load_sample_to_pinecone.py` with document-like names and page numbers (EU NGT Regulation 2025.pdf p.15, EFSA Guidance on Novel Foods.pdf p.24, FDA Guidance for Industry.pdf p.45, Codex Guideline Section 3.1.pdf p.8, Codex Guideline Section 4.2.pdf p.12).
- No Codex GL 44/45, EU NGT regulation or EFSA GMO/NGT guidance text is in the index.
- The fixed snapshot's specialist RAG result (5 chunks) contains two sample chunks, ranked 1st ("EU NGT Regulation 2025.pdf" p.15: "SDN-1: No foreign DNA introduced, may not require extensive safety assessment … may support a streamlined regulatory approach") and 4th ("EFSA Guidance on Novel Foods.pdf" p.24). All ten main-run reports and all five submitted runs list both names as sources.
- Both conditions received the same input, so the A/B comparison is unaffected; the content conclusions and the manuscript's corpus description are affected. The index state at the time of the submitted runs is not established.
- Codex review (11/7): findings confirmed; recommended keeping the main runs and disclosing precisely, treating the two citations as sources without real counterparts in L5, and correcting the corpus description; a rebuilt corpus with ten new runs is needed only to claim a framework grounded in the intended documents. Decision pending (corresponding author).
- Frozen codebook note corrected in `analysis_criteria.errata.md` (the frozen file is unchanged).

## 2026-11-07 — Rerun preparation (corpus v1), part 1

Decision (corresponding author): rebuild the corpus and rerun all ten runs after a final check of the input path. Rule: fix input errors and clear code bugs; keep design choices and model-output defects and disclose them. Judges were asked by the corresponding author to pause.
- Corpus v1 (`scripts/revision/build_corpus_v1.py`, manifest `corpus_v1/corpus_manifest.json`): 19 documents, 2,830 chunks, new index `virtual-lab-corpus-v1` (v0 index `virtual-lab` untouched). Codex CXG 44/45/46/68; EFSA 2011 (2150, 2193), 2012 (2501, 2561, 2943), 2020 (6299), 2022 (7618, 7621), 2024 (8895), 2025 (9566); COM(2023) 411 and Regulation (EU) 2026/1388; FSANZ P1055 (2025), Health Canada novel-food guidelines (2006, 2022 appendices), Japan MHLW procedures (2019, rev. 2020, English). Cutoff: rerun date (2026-11-07). Five EFSA documents from Europe PMC XML carry section labels instead of page numbers. Same chunking rule and embedding model as v0; pypdf instead of PyPDF2 (not in the venv).
- Code fixes: RAG query without web negation operators (`utils/search_query.rag_query`); final team 1-5 distinct roles; report statistics from full outputs; run root and snapshot from the manifest; corpus inventory hash and labels; RAG formatting shared by tool and snapshot builder (raw matches = injected text).
- P5 (both prompt sets): factual corrections of the template Methods text (no live web retrieval, failed team trials repeated, separate Critic model).
- Snapshot v1, first build (sha256 `5601eb544d1192a15fb209924fab88bcb6a67b71134c9b34a4f1839b72232f63`): web/EFSA entries copied unchanged from v0; RAG top-5 all from one document (EFSA 2025 animals opinion). Kept as a record. Pending decision on a per-document cap (Codex recommends one chunk per document, decided after seeing this snapshot and disclosed as such). No run has been made with corpus v1.

## 2026-11-07 — Rerun preparation, part 2: RAG selection rule (cap 1 per document)

- After the first v1 snapshot returned five chunks of one document (EFSA 2025 animals opinion), the corresponding author chose, on Codex's recommendation, a per-document cap of 1: the top-1 chunk of each of the 19 documents by a filtered Pinecone query (approximate nearest neighbour), then the 5 documents with the highest scores (ties by doc_id). Query, embedding, chunking, TOP_K = 5 and the injection point are unchanged. The rule was set after seeing that snapshot and before any run with corpus v1; it will not be changed again.
- Snapshots kept: `retrieval_snapshot_v1_first_top5_unused.json` (sha256 5601eb54…, plain top-5), `retrieval_snapshot_v1_float_pages_unused.json` (cap 1, pages printed "p.12.0"), and the final `retrieval_snapshot_v1.json` (sha256 `56fecbf9a240357738d2da4b7001b1a3d03f13dc592c81d7990ed69f76091f15`, same selection, integer page numbers). Web/EFSA results and queries are those of v0 (retrieval timestamps re-recorded).
- Selected for the agents: EFSA 2025 animals (section 4), Japan MHLW procedures (p.1), EFSA 2024 microorganisms (section 4), Codex CXG 45 (p.12), Health Canada guidelines (p.61). All 19 candidates and scores are in the snapshot build record.
- The live `rag_search_tool` path (not used in replay runs) still uses plain top-k.
- Next: pilot A_1/B_1 into `pilot_v1`, then manifest v2 (out_dir `main_v1`), then ten runs.

## 2026-11-07 — Pilot v1 (corpus v1, snapshot 56fecbf9)

- A_1: ok, 7 rounds (cap), 25 min, 68 calls, 0 failed calls, Critic stop_reason end_turn throughout. B_1: ok, early stop at round 4, 16 min, 47 calls, 0 failed.
- Both: team of 5 (Genomics, Toxicology, Regulatory, Risk, Bioinformatics), response models gpt-5-2025-08-07 and claude-opus-5, snapshot hash 56fecbf9 at start, report statistics from full outputs, corpus v1 documents cited, no v0 placeholder names.
- Leakage audit (A): 6 candidates, all in the prior-feedback channel and all the same sentence repeated from round 2 ("... 'cisgenic background'. (4) 'A central premise ..."), where "(4)" is a list number. Draft judgement: 0 confirmed leaks; masking fired 0 times.
- Pass criteria met. Pilot runs are not part of the main set.

## 2026-11-07 — Manifest v2 frozen; main runs v1 start

- `experiment_manifest_v2.json`, sha256 `ae7f54408fb391042fdc9103495b1d96a7339a301097e1b6f5291a4aa0c96d28`: out_dir `experiments/runs_rev/main_v1`; snapshot `retrieval_snapshot_v1.json` (56fecbf9…); corpus v1 (19 documents, 2,830 chunks, index `virtual-lab-corpus-v1`, corpus manifest hash); preparation-script hashes; code, prompt and environment hashes; same order and seeds as v1 (A_1, B_1, A_2, B_2, B_3, A_3, A_4, B_4, B_5, A_5; second-judge sample A_4, B_1, B_2; blinding seed 20261108); retry policy unchanged; the v1 amendment's exclusions do not carry over.
- The ten new runs replace the earlier main set (`main/`, corpus v0) as the primary results; the earlier set is kept as a record and as a corpus-v0 comparison. The authors had seen the v0 results (status, scores, similarity, and some report text after the codebook was frozen) before deciding the rerun. The frozen L3 codebook (`analysis_criteria.json`, with `analysis_criteria.errata.md`) and the analysis rules are kept unchanged; the coverage note is updated for corpus v1 in the errata at analysis time.
- Pilot v1 notes (Codex review): the RAG text (5,656 characters) reached all five specialists in round 1; B_1 shows a duplicated body/tree and an EFSA title–URL mismatch (model-output defects, kept and reported). The six A_1 leakage candidates are list numbers; author confirmation is pending (recorded as a draft judgement).
- Report statistics exclude the final report (stated in the table header); `meta.json` statistics include it.
- Environment check before start: venv Python 3.12.10 and all 84 installed distributions match the manifest (Codex's sandbox could not start the venv interpreter; not an issue in the run environment).

## 2026-11-07 — Leakage judgements confirmed

- The corresponding author (Bae Seongu) confirmed the draft judgements: v0 main set, 12 candidates, all SDN category numbers (`results/leakage_judgement.json`); pilot v1 A_1, 6 candidates, all the list number "(4)". Confirmed prior-score leaks: 0.
- The corresponding author has drafted the deadline-extension request to the editorial office.

## 2026-11-08 — Main runs v1 complete; analysis; judging kit v1

- Ten runs in `main_v1` (manifest v2 ae7f5440…), KST 2026-11-07 21:44:57 – 2026-11-08 01:06:45, all ok at attempt 1, 568 calls (54 Critic calls), 0 failed calls, Critic stop_reason end_turn throughout, snapshot 56fecbf9 at start in every run, response models gpt-5-2025-08-07 and claude-opus-5.
- L2: A 0/5 reached all-5 (all stopped at the 7-round cap); B 5/5 (rounds 3, 4, 4, 4, 4). Score decreases: A 64, B 0.
- L1 content similarity (descriptive; pairs not independent): within A 0.907 (0.839–0.964), within B 0.926 (0.895–0.970), A vs B 0.920 (0.858–0.969). Full text: 0.940, 0.959, 0.945. Representative run (condition-A medoid): A_5 (0.9286; next 0.9261).
- v0 for comparison (inputs and code differ; descriptive only): content 0.904 / 0.892 / 0.903; decreases A 51, B 4.
- Leakage audit (A): 2 candidates, both in A_2 round-1 specialist outputs, both SDN category numbers (draft judgement; author confirmation pending). Masking fired 0 times.
- Duplicated report bodies (model output): 4 of 10 reports, including all three reports of the fixed second-judge sample. Kept as generated; the whole report is the judging unit with the conflict-first rule.
- Judging kit v1 (`reference/revision/judging_v1`, blinding key sha256 94d71073…; same seed and therefore the same ID mapping rule as v0) and packages v1 (`reference/revision/packages_v1`, zip names end with `_재실험v1`). Codex review found and I fixed: (1) the codebook page listed the second-judge sample by original run IDs (a condition cue; also present in the paused v0 package) — replaced by neutral wording; (2) the primary-judge guide pointed to the v0 snapshot — the package now includes `검색입력_공통.md` (the common retrieval input, identical for all runs) and the guide refers to it. Rechecked: no run IDs and no key file in any package. Errata 2026-11-08 applied (coverage for corpus v1).
- Package sha256 (first 16 hex):
  - 1_주판정자_함준혁박사_재실험v1.zip 147c1f186179e16d
  - 2_2차판정자_재실험v1.zip 67704ef642eb1d3c
  - 3_외부판정자_1_재실험v1.zip f4bfcd0c31c51f72
  - 4_외부판정자_2_재실험v1.zip 5b9f93b8bbe808f1
- To record when sent: date, recipients, reply deadlines; the v0 packages are superseded.

## 2026-11-08 — v1 leakage judgements confirmed; sending plan

- The corresponding author confirmed both v1 candidates (A_2, SDN category numbers): confirmed prior-score leaks 0 (`results_v1/leakage_judgement.json`).
- Packages v1 to be sent on 2026-11-09 to the primary judge, the second judge and the two external judges; replies due within three days (by 2026-11-12). The v0 packages are superseded and must not be used.

## 2026-11-08 — L5 part 1 (reference existence) and L7 (corpus v1)

- L5 part 1 (`scripts/revision/l5_reference_audit.py` → `results_v1/l5_reference_audit.csv`, `l5_reference_summary.json`; drafts by Claude, author confirmation pending): 89 reference entries in the five condition-A reports = 22 unique documents (per report 14, 19, 14, 13, 18; 11 duplicate entries within reports). All 22 exist. Input route by unique document: 10 retrieved web/EFSA results, 5 RAG chunks, 2 named inside retrieved texts (Codex CXG 44, EFSA 2020 SDN-1/2/ODM opinion), 5 not in the retrieved inputs (EFSA 2011 GM-plant guidance, 2012 cisgenesis, 2017 allergenicity, 2019 TTC; COM(2023) 411) — real documents; not attributable to prior knowledge with certainty. Titles by entry: 66 accurate, 15 descriptive labels, 8 different titles. All five reports list the FDA human gene-therapy draft guidance (retrieved press announcement) and a USDA report on Thailand. Listing is not evidence of use (the pipeline adds retrieved sources to the References). Codex review applied (route categories, unique documents, title rules, EFSA 2021 issue 19(4)).
- L7 (`results/corpus_v1/`): 19 documents / 2,830 chunks / 5 chunks given to the agents. EU 12 documents (63%), 1,862 chunks (66%), 2 of 5 chunks given; Codex 4 (21%), 228 (8%), 1; Australia/New Zealand 1, 382 (13.5%), 0; Canada 1, 341 (12%), 1; Japan 1, 17 (0.6%), 1. Web results: 14 URLs = 13 documents. `pi_final_efsa` unused. EFSA 7618 was not given to the agents; CXG 45 only through one chunk (p.12).
- Next: L5 part 2 (claim support, representative run A_5, frozen selection rule; uncited claims kept as such).

## 2026-11-08 — L5 part 2 (claim support, representative run A_5)

- `scripts/revision/l5_claims_a5.py` → `results_v1/l5_claims_a5.csv`, `l5_claims_summary.json`. Frozen selection rule applied; 37 candidate sentences logged (30 included, 4 duplicates linked to their first occurrence, 3 excluded with reasons). 30 claims (a 7, b 4, c 12, d 7); no sampling (threshold: more than 30). Revised once after Codex review (truncated claims, Step 2 duplicates, strata); Codex re-review: can be finalised pending author confirmation.
- None of the 30 claims carries an explicit citation in the report; support is "not judged: uncited" and the support rate is not computable (not 0%). Across the ten main_v1 reports, Core Questions 1–5 contain 9 explicit parenthetical/bracketed citations (A_1 3, A_3 5, B_5 1; definition in the summary file), almost all naming Codex guidelines.
- Interpretation for R2-M4: claim-level source traceability is absent in the generated reports; this is not an error or hallucination rate. Optional exploratory analysis (not done): locate the same 30 claims in the delivered snapshot text only, without changing the uncited judgement.

## 2026-11-09 — Release preparation and SI tables (local commit only, not pushed)

- `scripts/revision/build_release.py` builds the public data package locally (`release/data_v1`, gitignored; 446 files, 145 MB). Third-party retrieval excerpts are removed where injected (snapshots; `system_prompt`/`user_message` in calls.jsonl; logs) and replaced by markers with length and SHA-256; bibliographic lines are kept in the snapshots; model outputs unchanged; local path replaced. Checks passed (10-word excerpt n-grams, keys, local paths); 20 of 3,441 excerpt n-grams also occur in model outputs (agent quotations) and are reported. Codex review applied.
- Blinding note (Codex): the judging-kit code and the anonymization seed are in the public branch, so the R01–R10 mapping can be recomputed without the key. No further judging-related pushes until all judgements are final; judges to be asked to confirm they did not consult the repository.
- `scripts/revision/build_si_tables.py` generates the new SI items (Note S1, Tables S7–S12) from the result files.
