from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from prompts import generate_action_items, generate_action_items_baseline


ROOT = Path(__file__).resolve().parent
EVAL_DIR = ROOT / "eval_set"


def load_inputs() -> list[dict]:
    p = EVAL_DIR / "inputs.json"
    return json.loads(p.read_text(encoding="utf-8"))

def _ensure_groq_key_for_eval() -> None:
    """
    For convenience when running locally: if GROQ_API_KEY isn't set and `.env` is not present,
    fall back to reading `.env.example` (which this project uses in the assignment).
    """
    if os.getenv("GROQ_API_KEY"):
        return
    if (ROOT / ".env").exists():
        return

    example = ROOT / ".env.example"
    if not example.exists():
        return

    for line in example.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("GROQ_API_KEY="):
            os.environ["GROQ_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
            return


def main() -> None:
    _ensure_groq_key_for_eval()
    items = load_inputs()
    now = datetime.now(timezone.utc).isoformat()

    baseline_results: list[dict] = []
    improved_results: list[dict] = []

    for it in items:
        mid = it.get("id")
        notes = it.get("notes", "")

        baseline_out: dict
        improved_out: dict

        try:
            baseline_out = generate_action_items_baseline(notes)
        except Exception as e:  # noqa: BLE001
            baseline_out = {"error": str(e)}

        try:
            improved_out = generate_action_items(notes)
        except Exception as e:  # noqa: BLE001
            improved_out = {"error": str(e)}

        baseline_results.append(
            {"id": mid, "timestamp_utc": now, "notes": notes, "output": baseline_out}
        )
        improved_results.append(
            {"id": mid, "timestamp_utc": now, "notes": notes, "output": improved_out}
        )

    (EVAL_DIR / "baseline_results.json").write_text(
        json.dumps(baseline_results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (EVAL_DIR / "improved_results.json").write_text(
        json.dumps(improved_results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Wrote {len(items)} baseline + improved results to {EVAL_DIR}")


if __name__ == "__main__":
    main()

