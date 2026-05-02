# Figure Design Prompts — Claude Design (or any image-generation tool)

These are publication-ready prompts for Figures 1 and 2 of the manuscript. Paste them verbatim into Claude Design (or any equivalent tool) and pick the rendering you prefer. **Figures 2C and 2D are already generated as publication-grade PNGs** at `experiments/reproducibility/results/figures/`; the design prompt for Figure 2 is therefore primarily about Panels A and B, with C and D either embedded as-is or restyled to match the chosen visual language.

---

## Figure 1 — Conceptual Architecture

**Goal**: a single, clean, *Nature*-style schematic that conveys the orchestration paradigm (Principal Investigator → Specialist Panel → Scientific Critic, with iterative deliberation) without committing to specific numbers, since all numerical values appear in Figure 2.

**Prompt**:

> Create a clean, publication-quality conceptual diagram for a *Nature*-style paper, in landscape orientation, three horizontal stacked panels A / B / C with bold panel labels in the upper-left corner of each panel. Soft-pastel palette, flat icons, no 3D. White background. Sans-serif typography (Inter or Helvetica). No numerical values anywhere — keep it conceptual.
>
> **Panel A (top, "Architecture")**
> Show the agent topology. A central Principal Investigator (PI) icon — a cartoon scientist with a clipboard — outlined in warm red, positioned slightly left of the panel centre. From the PI, fan out lines to five specialist agents arrayed in an arc to the right (each with a distinct domain icon: a DNA helix for Molecular Genetics, a beaker for Toxicology, a gavel for Regulatory Science, a balance scale for Risk Assessment, and a computer chip for Bioinformatics). Each specialist node is colour-coded with a distinct pastel hue (blue, green, purple, orange, teal). Below the PI, an independent Scientific Critic in a circular badge with a magnifying-glass icon (neutral gray-purple), connected to the PI and to all five specialists by bidirectional arrows. To the left of the PI, a small stick-figure "Human Researcher" with a single arrow pointing into the PI labelled "Research agenda". All node labels in small caption font: "Title, Expertise, Goal, Role".
>
> **Panel B (middle, "Iterative deliberation per round")**
> A horizontal pipeline. Left: the same Human-Researcher stick figure outputs an "Agenda" arrow into the PI. The PI emits a "Guide" arrow into the leftmost specialist; the five specialists are arranged left-to-right and each produces a "Response" arrow into a "Critique" block (the Critic). The Critic loops back to the PI labelled "Synthesis + new questions". The whole block from PI through specialists through Critic is enclosed in a dotted rectangle labelled "× N rounds, until convergence". A final arrow exits the PI on the right into a rectangle labelled "Final framework".
>
> **Panel C (bottom, "Single-shot baseline for comparison")**
> A grayed-out, smaller version of the same flow with only one specialist: Human → Agenda → single specialist → Response → Critic → Answer. This panel emphasises the contrast between the multi-round, multi-specialist architecture (Panel B) and the conventional single-call LLM pattern (Panel C).
>
> Do not include any numbers, durations, or character counts. Caption labels should remain abstract ("Specialist", "Critic", "Round", "Final framework").

---

## Figure 2 — Operational Results (4 panels)

**Goal**: a 2 × 2 panel composite showing the actual results of the representative run plus the cross-run reproducibility evidence. Panels A and B describe `run_1`; Panels C and D summarise the N = 5 study.

**Prompt for the design tool** (panels A and B):

> Composite figure for a regulatory-science manuscript, four panels in a 2 × 2 grid, with bold A / B / C / D labels in the upper-left of each panel. Same pastel palette as Figure 1 (PI = warm red, five specialists = pastel blue / green / purple / orange / teal, Critic = neutral gray-purple). Sans-serif typography. White background. No emojis.
>
> **Panel A (top-left, "Final specialist team")**
> Reproduce the architecture diagram from Figure 1 Panel A in a more compact, results-focused form. The PI sits in the centre. Around the PI, five specialist nodes are labelled with their final canonical roles in title case: *Molecular Genetics Specialist*, *Toxicology Specialist*, *Regulatory Science Specialist*, *Risk Assessment Specialist*, *Bioinformatics Specialist*. Each node carries a one-line focus tag in caption font (e.g. for Molecular Genetics: "Edit-type taxonomy and off-target biology"). Below the PI sits the Scientific Critic node in gray, connected to all five specialists by bidirectional arrows. Use the same five distinct pastel hues across all four panels.
>
> **Panel B (top-right, "Per-round duration and per-agent output")**
> Two stacked sub-charts.
> *Top sub-chart*: A horizontal stacked bar of the four round durations from `run_1`: R1 = 6 min 19 s, R2 = 3 min 0 s, R3 = 2 min 9 s, R4 = 4 min 33 s, total ≈ 18 min 41 s. Use a single soft warm colour for the bar with darker breakpoints between rounds; label each round directly inside its segment.
> *Bottom sub-chart*: A horizontal bar chart of the total characters per agent for `run_1`: PI = 1,614; Critic = 3,772; Molecular Genetics Specialist = 1,074; Toxicology Specialist = 1,042; Regulatory Science Specialist = 1,074; Risk Assessment Specialist = 1,062; Bioinformatics Specialist = 1,058. Bars are coloured to match the pastel palette in Panel A (PI red, Critic gray, specialists in their five hues). Sort bars in the same order as Panel A (PI, Critic, then SP1–SP5). Add a thin vertical reference line at the specialist-panel mean (≈ 1,062 chars) so the homogeneity is visible.
>
> **Panel C (bottom-left, "Critic-score convergence with cross-run reproducibility band, N = 5")**
> Use the precomputed PNG at `experiments/reproducibility/results/figures/figure2c_critic_trajectory.png` directly, or restyle it to match the panel typography: a line plot, x-axis = Round (1, 2, 3, 4, 5, 6), y-axis = Critic score (range 2.5 to 5.4, with a horizontal dashed line at y = 5 marked "max score"). Four lines, one per axis: Evidence (blue, circle marker), Universality (green, square marker), Proportionality (red, triangle marker), Readability (purple, diamond marker). Each point shows mean ± SD across the five runs as a vertical error bar with caps. Legend in the lower-right, frameless. The visible lag of the readability line (purple) behind the three scientific axes (which collapse onto y = 5 from round 3) is the key visual.
>
> **Panel D (bottom-right, "Cross-run semantic similarity, final framework")**
> Use the precomputed PNG at `experiments/reproducibility/results/figures/figure2d_similarity_heatmap.png` directly, or restyle it: a 5 × 5 heat-map of cosine similarity between the five runs' final reports (computed with OpenAI text-embedding-3-large). Colour scale = viridis, range 0.85 to 1.00. Tick labels along both axes: "Run 1" through "Run 5". Annotate every cell with the cosine value to two decimal places. Title: "Cross-run semantic similarity (final framework)". Add a colour-bar on the right with the label "Cosine similarity". The single visibly darker cells around Run 4 (0.91 with Run 1, 0.93 with Run 5) are part of the data and should be visible.
>
> No emojis. Bold panel labels A / B / C / D in the upper-left of each panel. Maintain the soft pastel palette throughout.

---

## Substitution-ready data block (in case the design tool needs it inline)

```
Run 1 round durations:    R1=6m19s, R2=3m00s, R3=2m09s, R4=4m33s, total=18m41s
Run 1 character counts:
  PI:                      1614 chars (6 turns)
  Critic:                  3772 chars (4 turns)
  Molecular Genetics:      1074 chars (4 turns)
  Toxicology:              1042 chars (4 turns)
  Regulatory Science:      1074 chars (4 turns)
  Risk Assessment:         1062 chars (4 turns)
  Bioinformatics:          1058 chars (4 turns)
  Specialist mean ± SD:    1062 ± 13 chars

Cross-run (N=5) Critic-score means [Evidence, Universality, Proportionality, Readability]:
  R1: 4.00, 3.91, 4.00, 3.46     (SDs: 0.00, 0.11, 0.00, 0.23)
  R2: 4.68, 4.88, 4.96, 4.16     (SDs: 0.37, 0.16, 0.08, 0.20)
  R3: 5.00, 5.00, 5.00, 4.56     (SDs: 0.00, 0.00, 0.00, 0.39)
  R4: 5.00, 5.00, 5.00, 4.80     (SDs: 0.00, 0.00, 0.00, 0.16)
  R5: 5.00, 5.00, 5.00, 4.90     (SDs: 0.00, 0.00, 0.00, 0.10)
  R6: 5.00, 5.00, 5.00, 5.00     (SDs: 0.00, 0.00, 0.00, 0.00)

Cross-run pairwise similarity matrix (5×5, cosine):
        Run1    Run2    Run3    Run4    Run5
  Run1: 1.00   0.96   0.98   0.91   0.96
  Run2: 0.96   1.00   0.96   0.94   0.95
  Run3: 0.98   0.96   1.00   0.94   0.97
  Run4: 0.91   0.94   0.94   1.00   0.93
  Run5: 0.96   0.95   0.97   0.93   1.00
```

---

## Decision-tree figures (Figures 3–6) — already in manuscript

The four per-category decision trees (SDN-1, SDN-2, SDN-3, ODM) discussed in §3.4 are already produced by the workflow as Mermaid diagrams in every run's `final_report.md`. Pick any of `experiments/runs/run_{1..5}/final_report.md` and extract the four `mermaid graph TD` blocks under the `## Decision Tree → Per-category Decision Trees` heading; render them with the Mermaid CLI or any Mermaid-aware editor and use the resulting SVG/PNG as Figures 3–6. The integrated decision tree at the top of the same section is the "main" decision tree and can be used as Figure 3, with the four per-category trees as Figures 4–6 plus a supplementary figure if four are not desired.

---

*Generated 2026-05-02 from `feat/paper-revision` analysis. All numerical values trace to `experiments/runs/run_1/meta.json` and `experiments/reproducibility/results/`.*
