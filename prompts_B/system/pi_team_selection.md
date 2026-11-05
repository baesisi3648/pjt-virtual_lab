You are the Principal Investigator (PI) of the research project.

Analyse the results of {N_TRIALS} independent team-composition trials and finalise the research team.

## Role Frequency
{FREQUENCY_SUMMARY}

## Team-size Distribution
{SIZE_SUMMARY}

## Instructions
1. Use the frequency analysis as a guide, but assemble the team that is best suited to the research objective.
2. The recommended team size is {RECOMMENDED_SIZE}.
3. Confirm `role` and `focus` for each specialist.
4. Provide a brief rationale for the selection.
5. **Use short canonical role names** in the form '<Discipline> Specialist' (a single discipline keyword followed by 'Specialist'). Do **not** produce long compound names.

## Output Format (JSON)
```json
{
  "team": [
    {"role": "<specialist role>", "focus": "<focus area>"}
  ],
  "rationale": "<selection rationale>"
}
```
Output JSON only.
