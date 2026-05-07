## Evaluation metrics (auto-computed)

- Baseline cases: 12, total items: 35, avg items/case: 2.92, avg confidence: 0.76
- Improved cases: 12, total items: 33, avg items/case: 2.75, avg confidence: 0.61

## Data quality flags

- Baseline % Unassigned: 66%; % deadline None: 83%; % non-ISO deadlines (excluding None): 17%
- Improved % Unassigned: 67%; % deadline None: 100%; % non-ISO deadlines (excluding None): 0%

## Where human review is needed

- Low confidence items (below the UI threshold) should be reviewed/edited before use.
- Any deadline that is not an ISO date (YYYY-MM-DD) should be normalized or set to None.
- Unassigned items should be assigned to a person before exporting to a task tracker.
