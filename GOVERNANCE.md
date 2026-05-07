## Governance: when to require human review

This assistant is designed to **speed up** converting notes into action items, not replace judgment.

### Always review before using the output

- **Low-confidence items**: Anything below the UI threshold must be reviewed and edited.
- **Assignee is `Unassigned`**: Assign to a real owner before exporting to a task tracker.
- **Deadlines**:
  - Only trust explicit ISO dates like `YYYY-MM-DD`.
  - If a deadline is relative (“next week”, “EOM”) the system should use `None` and you should set the real date.

### Common failure modes

- **Hallucinated tasks**: A task that sounds plausible but is not in the notes.
- **Over-splitting / under-splitting**: One bullet becomes too many tasks or multiple tasks get merged.
- **Wrong priority**: Urgency cues may be missed or over-weighted.

### UI enforcement

The app requires manual review confirmation before finalizing the generated list.

