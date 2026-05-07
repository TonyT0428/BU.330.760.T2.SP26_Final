from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _load(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_action_items(entry: dict) -> list[dict]:
    out = entry.get("output", {})
    if isinstance(out, dict) and "action_items" in out and isinstance(out["action_items"], list):
        return [x for x in out["action_items"] if isinstance(x, dict)]
    return []


def _is_iso_date(s: str) -> bool:
    # Minimal ISO date check: YYYY-MM-DD
    if not isinstance(s, str) or len(s) != 10:
        return False
    return s[4] == "-" and s[7] == "-" and s[:4].isdigit() and s[5:7].isdigit() and s[8:10].isdigit()


def compute_metrics(results: list[dict]) -> dict:
    num_cases = len(results)
    case_item_counts: list[int] = []
    confidences: list[float] = []
    unassigned = 0
    deadline_none = 0
    non_iso_deadline = 0
    priorities = {"High": 0, "Medium": 0, "Low": 0}

    for r in results:
        items = _extract_action_items(r)
        case_item_counts.append(len(items))
        for it in items:
            assignee = str(it.get("assignee", "")).strip()
            deadline = str(it.get("deadline", "")).strip()
            pr = str(it.get("priority", "")).strip()
            conf = it.get("confidence")

            if assignee == "Unassigned":
                unassigned += 1
            if deadline == "None":
                deadline_none += 1
            elif deadline and not _is_iso_date(deadline):
                non_iso_deadline += 1

            if pr in priorities:
                priorities[pr] += 1

            try:
                confidences.append(float(conf))
            except Exception:
                pass

    total_items = sum(case_item_counts)
    avg_items = (total_items / num_cases) if num_cases else 0.0
    avg_conf = (sum(confidences) / len(confidences)) if confidences else 0.0

    return {
        "num_cases": num_cases,
        "total_action_items": total_items,
        "avg_action_items_per_case": avg_items,
        "avg_confidence": avg_conf,
        "pct_unassigned": (unassigned / total_items) if total_items else 0.0,
        "pct_deadline_none": (deadline_none / total_items) if total_items else 0.0,
        "pct_deadline_non_iso_non_none": (non_iso_deadline / total_items) if total_items else 0.0,
        "priority_counts": priorities,
    }


def main() -> None:
    baseline = _load(ROOT / "baseline_results.json")
    improved = _load(ROOT / "improved_results.json")

    metrics = {
        "baseline": compute_metrics(baseline),
        "improved": compute_metrics(improved),
    }

    (ROOT / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # Short human-readable summary (no tables)
    summary_lines = [
        "## Evaluation metrics (auto-computed)",
        "",
        f"- Baseline cases: {metrics['baseline']['num_cases']}, total items: {metrics['baseline']['total_action_items']}, avg items/case: {metrics['baseline']['avg_action_items_per_case']:.2f}, avg confidence: {metrics['baseline']['avg_confidence']:.2f}",
        f"- Improved cases: {metrics['improved']['num_cases']}, total items: {metrics['improved']['total_action_items']}, avg items/case: {metrics['improved']['avg_action_items_per_case']:.2f}, avg confidence: {metrics['improved']['avg_confidence']:.2f}",
        "",
        "## Data quality flags",
        "",
        f"- Baseline % Unassigned: {metrics['baseline']['pct_unassigned']:.0%}; % deadline None: {metrics['baseline']['pct_deadline_none']:.0%}; % non-ISO deadlines (excluding None): {metrics['baseline']['pct_deadline_non_iso_non_none']:.0%}",
        f"- Improved % Unassigned: {metrics['improved']['pct_unassigned']:.0%}; % deadline None: {metrics['improved']['pct_deadline_none']:.0%}; % non-ISO deadlines (excluding None): {metrics['improved']['pct_deadline_non_iso_non_none']:.0%}",
        "",
        "## Where human review is needed",
        "",
        "- Low confidence items (below the UI threshold) should be reviewed/edited before use.",
        "- Any deadline that is not an ISO date (YYYY-MM-DD) should be normalized or set to None.",
        "- Unassigned items should be assigned to a person before exporting to a task tracker.",
        "",
    ]
    (ROOT / "analysis.md").write_text("\n".join(summary_lines), encoding="utf-8")

    print("Wrote eval_set/metrics.json and eval_set/analysis.md")


if __name__ == "__main__":
    main()

