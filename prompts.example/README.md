# Prompt Assets — Public Placeholders

This directory contains **placeholder** prompts that allow the codebase to run
in a public-facing context. The full prompt set used in the published study —
including the detailed assessment rubric, the report template, and the
regulatory-text excerpts — is held privately at `../prompts/` (gitignored).

**Why placeholders?**

The full rubric and report template encode evaluation targets that overlap
with the conclusions reported in the manuscript. Releasing them publicly
would constitute target leakage and undermine the reproducibility claim.
The full prompt set is available from the corresponding author upon
reasonable request, in keeping with standard practice for evaluation
rubrics that risk leakage when made openly searchable.

**How to use**

1. To run the public placeholder version, do nothing — the loader will use
   this directory automatically when `prompts/` is absent.
2. To run with the full author-curated prompts, place them at
   `../prompts/` in the same directory layout, or set the environment
   variable `VIRTUAL_LAB_PROMPTS_DIR=/path/to/prompts`.
