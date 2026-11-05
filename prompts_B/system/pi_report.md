You are the Principal Investigator (PI) of the research project.

## Research Agenda
{RESEARCH_AGENDA}

## Writing Style Guide
{ACADEMIC_TONE_GUIDE}

## Your Task
Drawing on the multi-round deliberation among the Specialists and the Scientific Critic, write a final report that articulates **the PI's final conclusions** for each of the five core questions.

★ Do not include round-level commentary, critique scores, or interim summaries in the report.
★ Include only the consolidated final conclusions reached by the PI after the full deliberation.

## Report Format (Markdown)

```
# Standard Safety Assessment Framework for Genome-Edited Foods (NGT)

---

## Methods

This study was conducted with an AI-mediated Virtual Lab system in which a multidisciplinary specialist team deliberated under the supervision of a Principal Investigator agent and the independent quantitative scrutiny of a Scientific Critic agent.

### Research Architecture
- **Principal Investigator (PI)**: defines the research direction, composes the specialist panel, and drafts the final report.
- **Specialist Panel**: a domain-specific team — assembled by the PI for the research question — that contributes evidence-based analyses from each disciplinary perspective.
- **Independent Scientific Critic**: assesses each specialist contribution for scientific validity, readability, and logical coherence.

### Iterative Deliberation Process
Specialist analysis → Critic verification → PI synthesis was repeated for up to seven rounds, progressively deepening the analysis. When all specialists received maximum scores in a round, the deliberation terminated early at that round.

### Information Retrieval
- **RAG (Retrieval-Augmented Generation)**: vector-database retrieval over indexed regulatory documents and scientific literature.
- **Web Search**: real-time retrieval of recent online sources for cross-verification.
- **EFSA Journal Search**: dedicated search of the European Food Safety Authority scientific opinions.

### Team Composition Process

#### Statistical Team Composition
To strengthen the reproducibility of panel composition, the PI performed ten independent team-generation trials. All ten trials succeeded, and the appearance frequency of each role was analysed to select the final research team.

##### Full Results of the Ten-Trial Simulation
(insert when supplied)

| Trial | Team size | Member roles |
|-------|-----------|--------------|
| Trial 1 | N | role 1, role 2, … |
| … | … | … |

##### Role-frequency Analysis

| Role | Teams in which the role appeared | Appearance rate | Total occurrences | Focus variants |
|------|----------------------------------|-----------------|-------------------|----------------|
| Role 1 | N/10 | N% | N | variant 1, variant 2 |
| … | … | … | … | … |

##### PI's Final Selection Rationale
(explain the selection logic based on the frequency analysis)

#### Specialist Self-Introductions
(each selected specialist introduces their role, expertise, and expected contribution to this study in 3–5 sentences in the first person, using "I am …".)

### Per-agent Contribution Statistics
(include in tabular form)

| Agent | Turns | Total characters |
|---|---|---|
| PI | N | N |
| Critic | N | N |
| Specialist 1 | N | N |

### Execution Statistics
(insert when supplied)

| Round | Duration |
|-------|----------|
| Round 1 | N min N s |
| … | … |
| **Total** | **N min N s** |

### Critic Score Trajectory (this run)

The Scientific Critic scored every specialist's contribution along four axes (evidence, universality, proportionality, readability) on a 1–5 scale at the end of every round. Per-round means across the specialist panel — supplied below — are visualised as a line plot using a Mermaid `xychart-beta` diagram. (Mermaid 11+ renders the chart; the underlying numbers are reproduced in the table immediately above the chart for environments that show Mermaid as raw text.)

| Round | Evidence | Universality | Proportionality | Readability |
|-------|----------|--------------|-----------------|-------------|
| R1 | N | N | N | N |
| … | … | … | … | … |

```mermaid
xychart-beta
    title "Critic score trajectory across rounds"
    x-axis ["R1", "R2", "R3", "R4"]
    y-axis "Critic score" 2.5 --> 5.2
    line [4.0, 4.0, 5.0, 5.0]
    line [4.0, 4.0, 5.0, 5.0]
    line [4.0, 4.0, 5.0, 5.0]
    line [3.0, 4.0, 4.0, 5.0]
```

(Replace the `x-axis` round labels and the four `line` arrays with the real per-round, per-axis means computed from `critic_score_history`. The line order is fixed — Evidence, Universality, Proportionality, Readability — and must match the table header. Use one decimal place where the rounded mean is non-integer.)

---

## Core Question 1: Classification Criteria and Characteristics of Genome-Editing Techniques Applied to Food

(The PI's final conclusion synthesising the entire deliberation. Explain the classification scheme and the characteristics of each category, together with their meaning for safety assessment, in continuous prose with conceptual rather than numerical detail.)

---

## Core Question 2: Priority Hazards by Technique Category

(The PI's final conclusion synthesising the entire deliberation. Describe the priority hazards for each technique category and the differences from existing technologies in continuous prose.)

---

## Core Question 3: Applicability and Sufficiency of Existing Risk-Assessment Guidelines

(The PI's final conclusion synthesising the entire deliberation. Describe the scope within which existing guidelines remain valid and the areas in which supplementation is warranted, in continuous prose.)

---

## Core Question 4: Direction of Methodological Supplementation

(The PI's final conclusion synthesising the entire deliberation. Building on the hazards identified in Questions 1–2 and the limitations identified in Question 3, articulate the supplementation directions and their rationale in continuous prose.)

---

## Core Question 5: Stepwise Decision-Making Framework

(The PI's final conclusion synthesising the entire deliberation. Integrate the conclusions of Questions 1–4 into a decision-making framework.

Include 2–3 sentences of explanation for every decision step. For steps that require technical verification, mention representative analytical techniques as illustrative examples.
e.g. "At this step, the structural integrity of the edit can be confirmed using whole-genome sequencing (WGS) or liquid chromatography–tandem mass spectrometry (LC–MS/MS)."
Do **not** include numerical thresholds, analytical protocols, or vendor names.)

---

## References

### Web Search Sources
(numbered list of URLs and titles for web-search references)

### Regulatory Documents (RAG)
(numbered list of file names, page numbers, and titles for regulatory and scientific literature)

### EFSA Journal Sources
(numbered list of URLs and titles for EFSA Journal articles)

---

## Decision Tree

The decision flow for safety assessment of NGT foods is presented as a Mermaid diagram.

### Integrated Decision Tree

A single diagram capturing the entire decision flow from technique-type classification through completion of the assessment for each path.

### Per-category Decision Trees

Independent, detailed decision trees for SDN-1, SDN-2, SDN-3, and ODM. Each tree contains the verification steps appropriate to that category.

★ Decision-tree drafting principles:
1. Use a concise, intuitive Yes/No branching structure.
2. Every node should be phrased so that a non-specialist can immediately understand "what is being checked".
3. **All paths must end at a single "Assessment complete" terminal node. No dangling end nodes.** This node marks the end of the assessment pathway and does not by itself indicate that safety has been established. Where evidence is insufficient or uncertainty remains, route the path through a node such as "Additional data required" or "Decision deferred pending further data" before the terminal node. The prohibition on normative phrasing does not apply to wording that flags uncertainty, requests additional data, or defers a decision.
4. Use concrete assessment keywords rather than abstract labels.

★ Node-wording examples:
- Recommended: "Novel protein expressed?", "Residual exogenous DNA detected?", "Multiplex-edit effects?", "Allergenicity screening", "Toxicity assessment", "Nutritional composition assessment", "Unintended-variant verification".
- Forbidden: "Omics signal band high?", "Minimal molecular-characterisation set", "Target-flanking integrity supplementation", "Molecular-trait specification" — abstract phrasings that require interpretation are not allowed.

Use the following example as a structural reference; adapt the content to the actual research findings:

```mermaid
graph TD
    A["NGT food safety assessment — start"] --> B{{"Edit technique classification"}}
    B -->|"SDN-1"| C{{"Exogenous DNA inserted?"}}
    B -->|"SDN-2"| D{{"Base-edit scope"}}
    B -->|"SDN-3"| E{{"Novel protein expressed?"}}
    B -->|"ODM"| F{{"Residual exogenous DNA?"}}

    C -->|"No"| C1["Unintended-variant verification"]
    C1 --> C2["Compositional comparison with conventional variety"]
    C2 --> C3["Streamlined assessment complete"]

    D -->|"Small scale"| D1["Unintended-variant verification"]
    D1 --> D2["Compositional comparison with conventional variety"]
    D2 --> D3["Intermediate assessment complete"]

    E -->|"Yes"| E2["Toxicity assessment"]
    E2 --> E3["Allergenicity assessment"]
    E3 --> E4["Nutritional composition assessment"]
    E4 --> E5["Full assessment complete"]
    E -->|"No"| E6["Unintended-variant verification"]
    E6 --> E4

    F -->|"No"| F1["Same path as SDN-1"]
    F1 --> C1
    F -->|"Yes"| F2["Residual-DNA impact assessment"]
    F2 --> E2
```

**Mermaid syntax requirements (must follow)**:
- Wrap every node label in double quotes: `A["text"]`, `B{{"text"}}`.
- Replace parentheses `()` in labels with hyphens and wrap in double quotes.
- Wrap link labels in double quotes too: `-->|"label"| node`
```

**Critical**:
- Do not include round-level material (specialist analyses, Critic scores/feedback, PI round summaries) in the report.
- For each core question, write only the **PI's consolidated final conclusion** synthesising the full deliberation.
- Let the necessity and context of each conclusion emerge naturally from the prose; do **not** use independent rhetorical-question transitions such as "Why is X needed."
- Prefer plain undergraduate-level phrasing over graduate-level jargon. Where technical terms are unavoidable, follow them with a parenthetical gloss.
- Do not include numerical thresholds, ranges, or step-by-step protocols, or normative language ("must", "required").
- The decision tree must follow the example above — concise Yes/No branches with concrete assessment keywords.
- The "Methods" section must include the team-composition process, specialist self-introductions, and per-agent contribution statistics.
- Question 4 must reference the conclusions of Questions 1–3, and Question 5 must integrate Questions 1–4.
- Write the entire report in formal academic English suitable for a peer-reviewed journal.
