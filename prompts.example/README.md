# Prompt Assets — Public Placeholders

This directory contains short placeholder prompts that let the codebase start without the
study prompts. They are not the prompts used in the study.

The prompts used in the study are public in this repository.

- `../prompts_A/` is the prompt set of the final protocol reported in the manuscript, including
  the Critic rubric (`data/critique_rubric.md`).
- `../prompts_B/` is the comparison prompt set and differs from `prompts_A/` only in
  `system/critic.md`.

To run with a study prompt set, set the environment variable
`VIRTUAL_LAB_PROMPTS_DIR=prompts_A` (or `prompts_B`). Without it the loader uses `../prompts/`
when present and otherwise this directory.
