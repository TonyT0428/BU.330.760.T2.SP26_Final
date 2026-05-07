# Meeting Notes → Action Items Assistant

**BU.330.760 — Generative AI Applications (Final Project)**  
A Streamlit application that turns pasted meeting notes into structured action items (task, assignee, deadline, priority, confidence), with optional retrieval-augmented prompting, human-in-the-loop review, and an offline evaluation set comparing a zero-shot baseline to the improved system.

## Demo video

**Placeholder — replace with your recording after upload:**

`[Your demo video](https://www.youtube.com/watch?v=REPLACE_WITH_VIDEO_ID)`

---

## 1. Context, user, and problem

**Context.** Teams capture meeting outcomes as messy text: bulleted notes, partial transcripts, or Zoom summaries. Turning that into accountable tasks usually means manual cleanup.

**Target users.** Product managers, student project teams, and small startup groups who need fast, consistent handoffs after meetings.

**Problem.** Raw notes mix implied ownership, vague deadlines, and discussion that is not actionable. Manually extracting tasks is slow and error-prone; purely rule-based tools miss varied phrasing and implicit intent. The project uses a **large language model** to interpret context and produce **structured** outputs, while **governance** (confidence, review gates) limits over-trust when the model is uncertain.

---

## 2. Solution and design

**User experience.** A Streamlit UI lets users paste notes, click **Generate Action Items**, review a per-item editor with confidence and “Reviewed” flags, adjust fields, then **finalize** after explicitly confirming manual review. Optional sidebar controls include a **low-confidence threshold** and (for transparency) **show retrieved RAG context**.

**LLM and API.** Generation uses **Groq** (`groq` Python SDK) with **JSON mode** (`response_format: json_object`) and **Pydantic** validation for `ActionItem` / `ActionItemsResponse`. Configuration lives in `config.py` (`.env`-loaded `GROQ_API_KEY`, optional `GROQ_MODEL`, default `llama-3.3-70b-versatile`).

**Prompting.**

- **Improved system:** Strong system prompt, **few-shot** examples, and **chain-of-thought** instruction (reason privately; output JSON only).
- **Baseline:** **Zero-shot** only—minimal system instructions and the raw notes, no few-shots and no RAG (see `generate_action_items_baseline` in `prompts.py`).

**RAG.** Markdown files under `knowledge_base/` are split into paragraphs and retrieved with **TF–IDF** (scikit-learn). Top chunks are injected under a fixed **`RETRIEVED CONTEXT:`** block in the user prompt to align assignee, deadline, priority, and style with project conventions.

**Governance.** Each item carries a model **confidence** score; items below a user-set threshold are flagged. Finalization requires checking **Reviewed** on every item and acknowledging manual review. See `GOVERNANCE.md` for when human judgment is required (e.g., unassigned owners, non-ISO deadlines, hallucination risk).

**Evaluation tooling.** `run_eval.py` runs baseline and improved generators over `eval_set/inputs.json` and writes `eval_set/baseline_results.json` and `eval_set/improved_results.json`. `eval_set/analyze_results.py` recomputes aggregate metrics into `eval_set/metrics.json` and a short narrative in `eval_set/analysis.md`.

---

## 3. Evaluation and results (with baseline comparison)

**Test set.** Twelve realistic meeting-note scenarios in `eval_set/inputs.json` (product syncs, sprint planning, customer calls, ops, retro, etc.).

**Automated metrics** (from `eval_set/metrics.json`, derived from saved Groq outputs):

| Metric | Baseline (zero-shot) | Improved (few-shot + RAG) |
| --- | --- | --- |
| Cases | 12 | 12 |
| Total action items | 35 | 33 |
| Avg items per case | ~2.92 | ~2.75 |
| Avg confidence | ~0.76 | ~0.61 |
| % assignee `Unassigned` | ~66% | ~67% |
| % deadline `None` | ~83% | 100% |
| % deadlines not ISO and not `None` | ~17% | 0% |

**Interpretation.** The **improved** pipeline favors **deadline hygiene** (no non-ISO deadline strings; ambiguous dates collapse to `None` per KB rules), at the cost of **slightly fewer extracted items** and **lower average confidence**—consistent with stricter extraction and fewer invented dates. **Human evaluation** (completeness, correctness, hallucinations) remains the authoritative read; the numbers above are **proxy signals** for format and conservatism, not ground-truth task quality. Rubric-aligned scoring can extend the same JSON outputs with manual or LLM-as-judge labels.

---

## 4. Artifact snapshot

| Path | Role |
| --- | --- |
| `app.py` | Streamlit UI, governance controls, finalize gate |
| `prompts.py` | Schemas, few-shots, RAG retrieval, baseline vs improved Groq calls |
| `config.py` | Groq client, env-based API key and model |
| `knowledge_base/*.md` | Domain rules for RAG (priority, deadlines, assignees, style, guardrails) |
| `eval_set/inputs.json` | 12 evaluation note sets |
| `eval_set/baseline_results.json` | Zero-shot run outputs |
| `eval_set/improved_results.json` | Few-shot + RAG run outputs |
| `eval_set/metrics.json` | Aggregated comparison metrics |
| `eval_set/analysis.md` | Human-readable summary |
| `eval_set/analyze_results.py` | Metric recomputation |
| `run_eval.py` | Batch eval runner |
| `GOVERNANCE.md` | Human-review policy |
| `requirements.txt` | Python dependencies |
| `.env.example` | Example `GROQ_API_KEY` (do not commit real secrets) |
| `project_plan.md` | Course project plan (author intent, metrics targets) |

---

## Setup and usage

**Prerequisites.** Python 3.10+ recommended.

**Install**

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Configure secrets**

```bash
cp .env.example .env
# Edit .env and set:
# GROQ_API_KEY=your_key_here
# Optional: GROQ_MODEL=llama-3.3-70b-versatile
```

Do **not** commit `.env` (it is listed in `.gitignore`).

**Run the app**

```bash
streamlit run app.py
```

Paste meeting notes → **Generate Action Items** → edit rows → mark **Reviewed** → confirm **I confirm I manually reviewed** → view finalized JSON. Use the sidebar to tune the low-confidence threshold and optionally display retrieved RAG context.

**Re-run evaluation and refresh metrics**

```bash
python run_eval.py
python eval_set/analyze_results.py
```

Regenerated results overwrite `eval_set/baseline_results.json`, `eval_set/improved_results.json`, `eval_set/metrics.json`, and `eval_set/analysis.md`.

---

**Author.** Project plan and implementation align with `project_plan.md` (prompt engineering, RAG, evaluation design, and governance).
