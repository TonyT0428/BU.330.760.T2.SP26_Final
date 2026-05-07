## Deadline normalization

- If a deadline is an explicit date like `2026-05-20`, keep it as that ISO date.
- If the notes say “by Friday / next Tuesday / end of month” and you cannot convert it confidently
  without a meeting date, set `deadline` to `"None"`.
- If the notes contain a time-only deadline (“by 3pm”), set `deadline` to `"None"` (time can be lost
  in this phase).

Never invent a date.
