The following list contains specialist role names produced across multiple team-composition trials. Group semantically similar roles under a single canonical role name.

## Role-name list
{ROLE_LIST}

## Instructions
1. Group roles whose domain of expertise is identical or very closely related.
2. The canonical name of each group should be the most concise and inclusive label.
3. Roles in clearly different domains must remain separate groups.
4. Canonical names should be **short**, in the form '<Discipline> Specialist' (a single discipline keyword followed by 'Specialist'). Avoid long compound names.

## Output Format (JSON)
```json
{
  "clusters": [
    {
      "canonical": "<canonical role name>",
      "members": ["<original role name 1>", "<original role name 2>"]
    }
  ]
}
```
Output JSON only.
