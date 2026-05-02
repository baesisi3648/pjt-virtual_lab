# Figure Design Prompts — Claude Design (paste-ready)

Two self-contained blocks below. For each figure, follow the **3-step workflow**:

1. **Attach** the listed reference images to the Claude Design conversation.
2. **Paste** the entire fenced block (everything inside the ` ``` ` markers) as a single message.
3. Iterate on the result with short follow-up instructions if needed.

The colour palette is held constant across both figures so the deliverables read as one coherent figure system.

---

## Shared Visual System (used by both figures)

```
Background:          #FFFFFF (pure white)
Body text / labels:  #1A1A1A (near-black)
Caption / axis:      #4A4A4A (dark gray)

Agent palette:
  PI                       #E63946  (warm red)
  Scientific Critic        #6C757D  (neutral gray)
  Human researcher         #ADB5BD  (light gray)
  Specialist 1 — Molecular Genetics    #A8DADC  (pastel blue)
  Specialist 2 — Toxicology            #B7E4C7  (pastel green)
  Specialist 3 — Regulatory Science    #C7B7E0  (pastel purple)
  Specialist 4 — Risk Assessment       #FFD6A5  (pastel orange)
  Specialist 5 — Bioinformatics        #95D5B2  (pastel teal)

Round/timing accent:  #F1A208 (mustard, used sparingly)
Heatmap scale:        viridis (matplotlib default), range 0.85 → 1.00

Typography:           Inter or Helvetica (sans-serif). Title 14 pt, axis 10 pt, labels 9 pt.
Stroke weight:        1.0 pt for connectors, 0.6 pt for grid.
Iconography:          flat illustration, no 3D, no gradients, no drop shadows.
```

---

## ▶ Figure 1 — Conceptual Architecture

### Step 1. Attach these images to the chat

| # | Path | Purpose |
|---|------|---------|
| 1 | `reference/260428 figure.pdf` page 1 (export as PNG) | Author's hand-drawn sketch of Figure 1 (layout intent) |
| 2 | `reference/260428 figure.pdf` page 1, lower-right Nature panel (crop as PNG) | Visual-style reference (cartoon avatars, level of polish) |

Tip: open the PDF, screenshot each region, and drop the two PNGs into the Claude Design conversation in this order before pasting the message.

### Step 2. Paste this entire block as your message

```
I am preparing Figure 1 of a manuscript on agentic AI orchestration for the
safety assessment of genome-edited foods. Generate the figure as a single
publication-quality image, landscape orientation, three stacked panels A / B / C
with bold panel labels in the upper-left of each panel.

Reference images attached:
  1) Hand-drawn sketch — shows the layout I want.
  2) Nature reference — shows the cartoon-illustration style and the level of
     polish I am aiming for. Match this style, but use the pastel palette
     specified below (not the reference's gray tones).

VISUAL SYSTEM (apply consistently across all three panels):
  Background:           #FFFFFF
  Body text:            #1A1A1A
  Caption / axis text:  #4A4A4A
  PI:                   #E63946  (warm red)
  Scientific Critic:    #6C757D  (neutral gray)
  Human researcher:     #ADB5BD  (light gray)
  Specialist 1 (Molecular Genetics):  #A8DADC  (pastel blue)
  Specialist 2 (Toxicology):          #B7E4C7  (pastel green)
  Specialist 3 (Regulatory Science):  #C7B7E0  (pastel purple)
  Specialist 4 (Risk Assessment):     #FFD6A5  (pastel orange)
  Specialist 5 (Bioinformatics):      #95D5B2  (pastel teal)
  Typography: Inter / Helvetica, sans-serif. Title 16 pt, labels 11 pt,
              captions 9 pt. (Bias toward LARGER text — small text is the
              most common readability complaint.)
  Iconography: AGENTIC AI CHARACTER STYLE — every agent is a friendly
              humanoid cartoon character (Pixar / Studio Ghibli flat
              illustration), NOT an abstract icon inside a circle. Each
              character has a head, body, and a domain-appropriate prop
              (DNA helix, beaker, gavel, balance scale, laptop, magnifying
              glass, clipboard). Faces are minimal — two-dot eyes and a
              small mouth — to stay publication-appropriate. Each
              character sits inside a softly tinted circular badge in
              their assigned palette colour so a reader can track the
              same agent across Panels A, B, and C.
              Style cues: clean line work, no 3D, no gradients, no drop
              shadows. Agent badge diameter should be at least 12% of the
              panel height, with a 1 pt outline (#1A1A1A) for edge
              definition.

  Character roster (use the same characters in all three panels):
    Human researcher    — casual figure with a notepad, light gray
    Principal Investigator (PI) — senior scientist in a white lab coat
                          holding a clipboard, warm-red accent
    Molecular Genetics  — researcher holding a DNA-helix model
    Toxicology          — researcher with safety goggles holding a flask
    Regulatory Science  — researcher in smart-casual attire with a small
                          gavel or policy clipboard
    Risk Assessment     — researcher with a notebook and a balance scale
    Bioinformatics      — hoodie-wearing developer with a laptop showing
                          a small genome plot
    Scientific Critic   — bookish figure with reading glasses, magnifying
                          glass, and red pen — visually distinct from the
                          specialists; reads as "skeptical reviewer"
  Stroke usage: solid lines for primary connectors (1.0 pt). Bidirectional
              audit channels in Panel A use a dashed stroke (1.2 pt,
              #4A4A4A) with arrowheads at BOTH ends — not dotted.
              The Critic→PI synthesis loop in Panel B uses a slightly
              thicker stroke (1.4 pt) so the round-closing feedback is
              visually distinct.
  Color saturation: the pastel specialist hues should read clearly, not
              blend into the white background. If the literal hex codes
              look too washed out, increase saturation by ~15% while
              keeping the same hue family.
  No emojis. No numerical values anywhere on the figure (numbers belong to Figure 2).

PANEL A — "Architecture" (top)
  Show the agent topology as a BALANCED, HORIZONTALLY-CENTERED composition
  (~10-15% horizontal padding on both sides; do not flush content to one
  side).
    - Place the Principal Investigator (PI) character in the horizontal
      centre of the panel. The PI is a cartoon scientist in a white lab
      coat with a clipboard, sitting in a warm-red badge.
    - To the LEFT of the PI, place the Human researcher character (casual
      figure with a notepad). A single solid arrow points from the Human
      researcher to the PI, labelled "Research agenda".
    - To the RIGHT of the PI, the five specialist characters are arranged
      in a vertical column or shallow arc. Each is a humanoid cartoon
      character with a domain prop and the assigned pastel hue:
        SP1 Molecular Genetics  — DNA-helix-holding researcher, pastel blue
        SP2 Toxicology          — flask-holding researcher with goggles, pastel green
        SP3 Regulatory Science  — gavel/policy-clipboard researcher, pastel purple
        SP4 Risk Assessment     — balance-scale researcher, pastel orange
        SP5 Bioinformatics      — laptop-holding hoodie developer, pastel teal
      The PI fans out solid arrows to all five specialists.
    - BELOW the PI, centred horizontally relative to the specialist column,
      place the Scientific Critic character (bookish, reading glasses,
      magnifying glass + red pen) in a neutral-gray badge. The Critic is
      connected to the PI and to every specialist by DASHED bidirectional
      channels (1.2 pt, #4A4A4A, arrowheads at both ends).
    - Each character carries a four-line label in caption font, in this
      order: Title / Expertise / Goal / Role.

PANEL B — "Iterative deliberation per round" (middle)
  CRITICAL: this panel must show PARALLEL fan-out / fan-in, not a sequential
  chain. The five specialists run concurrently and never pass work to each
  other. Layout:
    - Left: Human researcher icon → "Agenda" arrow → PI icon.
    - PI fans out FIVE simultaneous arrows to SP1, SP2, SP3, SP4, SP5
      stacked in a vertical column (or vertical arc) to the right of the PI.
      Every fan-out arrow carries the label "Guide". The specialists are
      NOT connected to each other — each receives its guide directly from
      the PI in parallel.
    - Each specialist emits a single "Response" arrow that fans IN on the
      Scientific Critic node, placed to the right of the specialist column.
      This produces five separate arrows converging on the Critic.
    - From the Critic, a single, slightly thicker curved arrow loops back
      to the PI labelled "Synthesis + new questions" (label above the line).
    - Enclose PI / 5 specialists / Critic / loop in a dotted rectangle
      labelled "× N rounds, until convergence".
    - A final arrow exits the PI on the right into a "Final framework"
      rectangle OUTSIDE the dotted rectangle.
  The visual idea is: one PI broadcasts to many specialists in parallel,
  the Critic gathers their parallel responses, and the loop synthesises
  the round into the next agenda.

PANEL C — "Single-shot baseline for comparison" (bottom)
  Grayed-out, smaller version of the same flow with only one specialist:
    Human → Agenda → single specialist → Response → Critic → Answer
  This panel emphasises the contrast with Panel B.

Caption labels remain abstract throughout: "Specialist", "Critic", "Round",
"Final framework". Do not invent or display any numbers.
```

### Step 3. After receiving the result

Quick refinement messages to send if needed:
- "Make the dotted rectangle in Panel B more clearly dotted, and move the 'x N rounds' label inside the rectangle."
- "Increase the contrast between the gray Critic in Panel A and the pastel specialists."
- "Reduce Panel C to ~60% of the height of Panel B; it should read as the contrast baseline, not a peer panel."

---

## ▶ Figure 2 — Operational Results (4 panels)

### Step 1. Attach these images to the chat

| # | Path | Purpose |
|---|------|---------|
| 1 | `reference/260428 figure.pdf` page 2 (export as PNG) | Author's hand-drawn sketch of Figure 2 (panel layout) |
| 2 | `reference/260428 figure.pdf` page 2, lower-right Nature panel (crop as PNG) | Visual-style reference (panel grid, caption style) |
| 3 | `experiments/reproducibility/results/figures/figure2c_critic_trajectory.png` | Final Panel C — embed as-is or restyle to match A/B |
| 4 | `experiments/reproducibility/results/figures/figure2d_similarity_heatmap.png` | Final Panel D — embed as-is or restyle to match A/B |
| 5 | *(optional)* the finished Figure 1 PNG once you have it | For style continuity between the two figures |

### Step 2. Paste this entire block as your message

```
I am preparing Figure 2 of the same manuscript as the figure I just generated.
Figure 2 is a 2x2 panel composite reporting the operational results of one
representative run plus the cross-run reproducibility evidence. Use the
attached references:

  1) Hand-drawn sketch — shows the 2x2 panel layout.
  2) Nature reference — shows panel grid spacing and caption style.
  3) figure2c_critic_trajectory.png — Panel C is already publication-grade.
     Place it verbatim as Panel C, OR restyle it to match the typography of
     Panels A and B (legend font, axis tick style) without changing the data.
  4) figure2d_similarity_heatmap.png — same instruction for Panel D.

The figure must read as a sibling to Figure 1: identical pastel palette,
identical iconography, identical typography. Bold A / B / C / D labels in
the upper-left of each panel.

VISUAL SYSTEM (identical to Figure 1):
  Background:           #FFFFFF
  Body / axis text:     #1A1A1A / #4A4A4A
  PI:                   #E63946     Critic:     #6C757D
  Specialists:          #A8DADC (Molecular Genetics) / #B7E4C7 (Toxicology) /
                        #C7B7E0 (Regulatory Science) / #FFD6A5 (Risk Assessment) /
                        #95D5B2 (Bioinformatics)
  Round/timing accent:  #F1A208 (mustard)
  Typography: Inter / Helvetica. Title 14 pt, axis 10 pt, labels 9 pt.
  No emojis. No drop shadows.

PANEL A — "Final specialist team" (top-left)
  Compact, results-focused version of the architecture in Figure 1 Panel A.
  PI in centre (warm red). Five specialist nodes around the PI, each
  labelled with the canonical role title and a one-line focus tag in
  caption font:
    Molecular Genetics Specialist  — "Edit-type taxonomy and off-target biology"
    Toxicology Specialist          — "Hazard identification, NAMs, and TTC triggers"
    Regulatory Science Specialist  — "Codex / EFSA / OECD alignment and proportionate oversight"
    Risk Assessment Specialist     — "Problem formulation and exposure-led decision trees"
    Bioinformatics Specialist      — "In silico off-target prediction and omics integration"
  Scientific Critic node (gray) sits below the PI, connected to all five
  specialists by bidirectional arrows. Use the same five pastel hues as
  Figure 1.

PANEL B — "Per-round duration and per-agent output" (top-right)
  Two stacked sub-charts.
  Top sub-chart — Round timeline:
    Horizontal stacked bar of the four round durations of the representative
    run (run_1):
      R1 = 6 min 19 s
      R2 = 3 min 0 s
      R3 = 2 min 9 s
      R4 = 4 min 33 s
      total = 18 min 41 s
    Single mustard accent colour (#F1A208) for the bar with darker breakpoints
    between rounds; label each round directly inside its segment.
  Bottom sub-chart — Per-agent output bar chart:
    Horizontal bar chart of total characters per agent in run_1, ordered:
      PI                              1,614 chars     (red, #E63946)
      Critic                          3,772 chars     (gray, #6C757D)
      Molecular Genetics Specialist   1,074 chars     (pastel blue)
      Toxicology Specialist           1,042 chars     (pastel green)
      Regulatory Science Specialist   1,074 chars     (pastel purple)
      Risk Assessment Specialist      1,062 chars     (pastel orange)
      Bioinformatics Specialist       1,058 chars     (pastel teal)
    Add a thin vertical reference line at the specialist-panel mean
    (~1,062 chars) so the homogeneity of specialist outputs is visible.

PANEL C — "Critic-score convergence with cross-run reproducibility band, N = 5"
  Use the attached figure2c_critic_trajectory.png. Either embed it
  verbatim or restyle it (same data, same series, same legend) so that
  axis labels and legend font match the typography used in Panels A and B.
  Do not change the data values or the y-axis range.
  Series colours (must remain distinct):
    Evidence       — blue, circle markers
    Universality   — green, square markers
    Proportionality — red, triangle markers
    Readability    — purple, diamond markers
  Horizontal dashed line at y = 5 marked "max score". Error bars are
  cross-run mean ± SD over five independent runs.

PANEL D — "Cross-run semantic similarity, final framework"
  Use the attached figure2d_similarity_heatmap.png. Either embed it
  verbatim or restyle it (same data, same colour scale, same cell labels).
  5 x 5 heatmap, colour scale viridis, range 0.85 to 1.00, every cell
  annotated with the cosine value to two decimal places. Tick labels
  "Run 1" through "Run 5" on both axes. Colour-bar on the right labelled
  "Cosine similarity".

DATA BLOCK (in case you need to re-derive any panel):
  Run 1 round durations:    R1=6m19s, R2=3m00s, R3=2m09s, R4=4m33s, total=18m41s
  Run 1 character counts:
    PI                        1614 chars   (6 turns)
    Critic                    3772 chars   (4 turns)
    Molecular Genetics        1074 chars   (4 turns)
    Toxicology                1042 chars   (4 turns)
    Regulatory Science        1074 chars   (4 turns)
    Risk Assessment           1062 chars   (4 turns)
    Bioinformatics            1058 chars   (4 turns)
    Specialist mean +/- SD    1062 +/- 13 chars

  Cross-run (N=5) Critic-score means [Evidence, Universality, Proportionality, Readability]:
    R1: 4.00, 3.91, 4.00, 3.46    (SD: 0.00, 0.11, 0.00, 0.23)
    R2: 4.68, 4.88, 4.96, 4.16    (SD: 0.37, 0.16, 0.08, 0.20)
    R3: 5.00, 5.00, 5.00, 4.56    (SD: 0.00, 0.00, 0.00, 0.39)
    R4: 5.00, 5.00, 5.00, 4.80    (SD: 0.00, 0.00, 0.00, 0.16)
    R5: 5.00, 5.00, 5.00, 4.90    (SD: 0.00, 0.00, 0.00, 0.10)
    R6: 5.00, 5.00, 5.00, 5.00    (SD: 0.00, 0.00, 0.00, 0.00)

  Cross-run pairwise similarity matrix (5x5, cosine):
            Run1   Run2   Run3   Run4   Run5
    Run 1:  1.00   0.96   0.98   0.91   0.96
    Run 2:  0.96   1.00   0.96   0.94   0.95
    Run 3:  0.98   0.96   1.00   0.94   0.97
    Run 4:  0.91   0.94   0.94   1.00   0.93
    Run 5:  0.96   0.95   0.97   0.93   1.00

REQUIREMENTS:
  - The PI, specialists, and Critic icons in Panel A must be the SAME
    characters used in Figure 1 Panel A (same avatars, same colours).
  - All four panels share a consistent typography and grid spacing.
  - No emojis, no drop shadows, no 3D effects, no decorative gradients.
  - Bold panel labels A / B / C / D in the upper-left of each panel.
```

### Step 3. After receiving the result

Quick refinement messages to send if needed:
- "Make the gap between the two sub-charts of Panel B smaller — they should clearly belong to one panel."
- "In Panel B's character-count chart, the PI bar (red) and the Critic bar (gray) should appear above the five specialist bars, not interleaved."
- "Restyle Panels C and D so the axis font sizes match Panels A and B; otherwise keep the data and colour scales untouched."

---

## Figures 3–6 — Decision Trees (no design tool needed)

The four per-category decision trees (SDN-1, SDN-2, SDN-3, ODM) are produced by the workflow as Mermaid diagrams in every run's `final_report.md`. To use them as Figures 3–6:

1. Open `experiments/runs/run_1/final_report.md` (or any run).
2. Extract the four `mermaid graph TD` blocks under the section
   `## Decision Tree → Per-category Decision Trees`.
3. Render each block to PNG/SVG using one of:
   - `https://mermaid.live/` (paste, click "Actions → PNG/SVG download")
   - `npx @mermaid-js/mermaid-cli -i input.mmd -o output.svg`
4. The integrated decision tree at the top of the same section can be Figure 3, with the four per-category trees as Figures 4–6 plus one Supplementary if needed.

No tool prompt is required — the diagrams are already final; rendering is purely cosmetic.

---

*Generated 2026-05-02 from `feat/paper-revision` analysis. Numerical values trace to `experiments/runs/run_1/meta.json` and `experiments/reproducibility/results/`.*
