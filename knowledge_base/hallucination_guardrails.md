## Hallucination guardrails

- Extract only tasks that are supported by the notes.
- If the notes contain no clear action items, return an empty list:

```json
{"action_items": []}
```

- Lower `confidence` when a task is implied rather than explicitly stated.
- Never fabricate names, deadlines, or deliverables.
