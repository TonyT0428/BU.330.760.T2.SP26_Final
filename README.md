# BU.330.760 Final — RAG Demo (Streamlit)

This repo contains a small Streamlit app demonstrating **Baseline** vs **Improved (RAG + few-shot)** responses.

## Structure

```
.
├── app.py
├── prompts.py
├── knowledge_base/
├── eval_set/
│   ├── inputs.json
│   ├── baseline_results.json
│   └── improved_results.json
├── requirements.txt
└── .gitignore
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the app

```bash
streamlit run app.py
```

## OpenAI (optional)

If you set an API key, the app will call OpenAI Chat Completions; otherwise it runs offline with an extractive fallback.

```bash
export OPENAI_API_KEY="YOUR_KEY"
export OPENAI_MODEL="gpt-4.1-mini"   # optional
```

## Knowledge base

Place `.md` documents under `knowledge_base/`. The app will chunk by paragraphs and retrieve with TF‑IDF.

## Eval set

- `eval_set/inputs.json`: sample questions
- `eval_set/baseline_results.json` and `eval_set/improved_results.json`: example result files (editable)
