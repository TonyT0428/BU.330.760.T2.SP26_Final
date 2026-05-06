from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer

from prompts import build_messages_baseline, build_messages_improved


ROOT = Path(__file__).resolve().parent
KB_DIR = ROOT / "knowledge_base"
EVAL_DIR = ROOT / "eval_set"


@dataclass(frozen=True)
class Chunk:
    source: str
    text: str


def _read_markdown_files(kb_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for p in sorted(kb_dir.glob("*.md")):
        raw = p.read_text(encoding="utf-8")
        parts = [s.strip() for s in re.split(r"\n\s*\n+", raw) if s.strip()]
        for part in parts:
            chunks.append(Chunk(source=p.name, text=part))
    return chunks


@st.cache_resource(show_spinner=False)
def _build_index() -> tuple[list[Chunk], TfidfVectorizer, np.ndarray]:
    kb_dir = KB_DIR
    if not kb_dir.exists():
        kb_dir.mkdir(parents=True, exist_ok=True)

    chunks = _read_markdown_files(kb_dir)
    if not chunks:
        chunks = [
            Chunk(
                source="(empty)",
                text="No knowledge base documents found. Add .md files under knowledge_base/.",
            )
        ]

    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform([c.text for c in chunks]).toarray().astype(np.float32)
    return chunks, vectorizer, matrix


def retrieve(query: str, top_k: int = 4) -> list[tuple[Chunk, float]]:
    chunks, vectorizer, matrix = _build_index()
    q = vectorizer.transform([query]).toarray().astype(np.float32)[0]
    denom = (np.linalg.norm(matrix, axis=1) * (np.linalg.norm(q) + 1e-8)) + 1e-8
    sims = (matrix @ q) / denom
    idx = np.argsort(-sims)[:top_k]
    return [(chunks[i], float(sims[i])) for i in idx]


def format_context(hits: list[tuple[Chunk, float]]) -> str:
    blocks: list[str] = []
    for c, score in hits:
        blocks.append(f"[{c.source} | score={score:.3f}]\n{c.text}")
    return "\n\n---\n\n".join(blocks)


def try_openai_chat(messages: list[dict[str, str]]) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI  # type: ignore

        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=messages,
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:  # noqa: BLE001
        return f"(OpenAI call failed: {e})"


def heuristic_answer(question: str, context: str) -> str:
    # Simple offline fallback: return a short extractive answer from the retrieved context.
    sents = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", context.strip()))
    sents = [s.strip() for s in sents if len(s.strip()) >= 20]
    if not sents:
        return "I couldn't find relevant context in the knowledge base. Add documents under knowledge_base/."
    return "Based on the retrieved context, here are the most relevant snippets:\n\n- " + "\n- ".join(
        sents[:5]
    )


def load_eval_inputs() -> list[dict]:
    p = EVAL_DIR / "inputs.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> None:
    st.set_page_config(page_title="RAG Demo (Streamlit)", layout="wide")
    st.title("RAG Demo (Streamlit)")
    st.caption("Baseline vs Improved (RAG + few-shot). Uses OpenAI if `OPENAI_API_KEY` is set; otherwise runs offline.")

    with st.sidebar:
        st.header("Settings")
        mode = st.radio("Mode", ["Improved (RAG + few-shot)", "Baseline"], index=0)
        top_k = st.slider("Top-K retrieved chunks", 1, 8, 4)
        show_context = st.checkbox("Show retrieved context", value=True)

        st.divider()
        st.subheader("Eval set")
        eval_items = load_eval_inputs()
        if eval_items:
            picked = st.selectbox(
                "Pick a sample input",
                options=list(range(len(eval_items))),
                format_func=lambda i: f"{eval_items[i].get('id', i)}: {eval_items[i].get('question','')[:60]}",
            )
            sample_q = eval_items[picked].get("question", "")
            if st.button("Use this question"):
                st.session_state["question"] = sample_q
        else:
            st.info("No eval inputs found. See eval_set/inputs.json.")

    question = st.text_area("Question", value=st.session_state.get("question", ""), height=110)
    go = st.button("Run")

    if not go:
        st.stop()

    hits = retrieve(question, top_k=top_k)
    context = format_context(hits)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Answer")
        if mode.startswith("Baseline"):
            messages = build_messages_baseline(question)
            llm = try_openai_chat(messages)
            st.write(llm if llm is not None else heuristic_answer(question, context=""))
        else:
            messages = build_messages_improved(question, context=context)
            llm = try_openai_chat(messages)
            st.write(llm if llm is not None else heuristic_answer(question, context=context))

    with col2:
        st.subheader("Retrieval")
        for c, score in hits:
            st.markdown(f"**{c.source}**  \nscore={score:.3f}")
            st.code(c.text, language="markdown")

        if show_context:
            st.divider()
            st.subheader("Context (as sent to improved prompt)")
            st.code(context, language="markdown")


if __name__ == "__main__":
    main()
