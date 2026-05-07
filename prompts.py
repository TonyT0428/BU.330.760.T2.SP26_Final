from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer

from config import get_default_groq_model, get_groq_api_key, get_groq_client


class ActionItem(BaseModel):
    task: str = Field(..., description="Clear, specific task phrased as an imperative.")
    assignee: str = Field(
        ...,
        description='Person responsible. Use a name if present; otherwise use "Unassigned".',
    )
    deadline: str = Field(
        ...,
        description='Due date. Use ISO-8601 date (YYYY-MM-DD) if explicit; otherwise "None".',
    )
    priority: Literal["High", "Medium", "Low"] = Field(
        ...,
        description="Relative priority inferred from urgency/impact cues in notes.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="0.0–1.0 confidence that this is a real action item and fields are correct.",
    )


class ActionItemsResponse(BaseModel):
    action_items: list[ActionItem]


SYSTEM_PROMPT = """\
You are an expert assistant that converts messy meeting notes into actionable tasks.

Goal:
- Extract ONLY real, concrete action items that someone needs to do.
- Return structured output matching the required schema.

Rules:
- Be faithful to the notes; do NOT invent tasks, people, or deadlines.
- If assignee is unclear, set assignee="Unassigned".
- If deadline is unclear or relative (e.g., "next week") and cannot be converted confidently,
  set deadline="None".
- Prefer concise, atomic tasks (split large tasks into 2–4 items if clearly separable).
- Priority:
  - High: urgent/blocking, explicit ASAP, customer-impacting, or hard deadline.
  - Medium: important but not urgent.
  - Low: nice-to-have, optional, or vague follow-ups.
- Confidence:
  - 0.85–1.0 when task/assignee/deadline are explicit.
  - 0.60–0.84 when one field is inferred (e.g., priority) but task is clear.
  - 0.30–0.59 when action item is implied or assignee/deadline are missing.

RAG:
- You may be provided "Retrieved context" containing organization conventions.
- Use it to standardize formatting and reduce hallucinations.

Reasoning:
- Think step-by-step privately, but DO NOT include your reasoning in the output.

Output:
- Return JSON ONLY, no markdown, no backticks, no extra keys.
"""

BASELINE_SYSTEM_PROMPT = """\
You convert messy meeting notes into action items.

Return JSON ONLY in this schema:
{"action_items":[{"task":str,"assignee":str,"deadline":str,"priority":"High"|"Medium"|"Low","confidence":0..1}]}

Rules:
- Do not invent tasks, names, or deadlines.
- If assignee is unclear, use "Unassigned".
- If deadline is unclear, use "None".
"""


@dataclass(frozen=True)
class FewShot:
    notes: str
    response_json: str


FEW_SHOTS: list[FewShot] = [
    FewShot(
        notes=(
            "Weekly sync:\n"
            "- Alex to send the revised deck to the client by Friday.\n"
            "- Priya will follow up with Legal about the contract language.\n"
            "- Decision: ship v1 without SSO.\n"
        ),
        response_json=json.dumps(
            {
                "action_items": [
                    {
                        "task": "Send the revised deck to the client",
                        "assignee": "Alex",
                        "deadline": "None",
                        "priority": "High",
                        "confidence": 0.8,
                    },
                    {
                        "task": "Follow up with Legal about the contract language",
                        "assignee": "Priya",
                        "deadline": "None",
                        "priority": "Medium",
                        "confidence": 0.75,
                    },
                ]
            },
            ensure_ascii=False,
        ),
    ),
    FewShot(
        notes=(
            "Sprint planning notes:\n"
            "• We need the onboarding email copy updated.\n"
            "• Jordan: I'll take the database migration.\n"
            "• Target date for beta: 2026-05-20.\n"
            "• Someone should ping Design about missing icons.\n"
        ),
        response_json=json.dumps(
            {
                "action_items": [
                    {
                        "task": "Update the onboarding email copy",
                        "assignee": "Unassigned",
                        "deadline": "None",
                        "priority": "Medium",
                        "confidence": 0.55,
                    },
                    {
                        "task": "Complete the database migration",
                        "assignee": "Jordan",
                        "deadline": "None",
                        "priority": "High",
                        "confidence": 0.7,
                    },
                    {
                        "task": "Ping Design about missing icons",
                        "assignee": "Unassigned",
                        "deadline": "None",
                        "priority": "Low",
                        "confidence": 0.45,
                    },
                ]
            },
            ensure_ascii=False,
        ),
    ),
    FewShot(
        notes=(
            "Customer call recap:\n"
            "- They reported crashes on iOS 17.2 when uploading.\n"
            "- Mia will open a bug and assign to the mobile team.\n"
            "- Ken: can you draft a status update to send today?\n"
        ),
        response_json=json.dumps(
            {
                "action_items": [
                    {
                        "task": "Open a bug for iOS 17.2 upload crashes and assign it to the mobile team",
                        "assignee": "Mia",
                        "deadline": "None",
                        "priority": "High",
                        "confidence": 0.8,
                    },
                    {
                        "task": "Draft a customer status update and send it today",
                        "assignee": "Ken",
                        "deadline": "None",
                        "priority": "High",
                        "confidence": 0.7,
                    },
                ]
            },
            ensure_ascii=False,
        ),
    ),
    FewShot(
        notes=(
            "Project meeting:\n"
            "Tom will update the risk register.\n"
            "Let's aim to finalize requirements by end of month.\n"
            "Reminder: budget review next Tuesday.\n"
        ),
        response_json=json.dumps(
            {
                "action_items": [
                    {
                        "task": "Update the risk register",
                        "assignee": "Tom",
                        "deadline": "None",
                        "priority": "Medium",
                        "confidence": 0.8,
                    },
                    {
                        "task": "Finalize requirements",
                        "assignee": "Unassigned",
                        "deadline": "None",
                        "priority": "Medium",
                        "confidence": 0.4,
                    },
                ]
            },
            ensure_ascii=False,
        ),
    ),
    FewShot(
        notes=(
            "Retro:\n"
            "- Good: velocity improved.\n"
            "- Bad: too many meetings.\n"
            "- Action: reduce recurring meetings.\n"
        ),
        response_json=json.dumps(
            {
                "action_items": [
                    {
                        "task": "Reduce recurring meetings",
                        "assignee": "Unassigned",
                        "deadline": "None",
                        "priority": "Low",
                        "confidence": 0.5,
                    }
                ]
            },
            ensure_ascii=False,
        ),
    ),
]


ROOT = Path(__file__).resolve().parent
KB_DIR = ROOT / "knowledge_base"


@dataclass(frozen=True)
class KBChunk:
    source: str
    text: str


def _read_kb_chunks(kb_dir: Path) -> list[KBChunk]:
    chunks: list[KBChunk] = []
    if not kb_dir.exists():
        return chunks
    for p in sorted(kb_dir.glob("*.md")):
        raw = p.read_text(encoding="utf-8")
        parts = [s.strip() for s in re.split(r"\n\s*\n+", raw) if s.strip()]
        for part in parts:
            chunks.append(KBChunk(source=p.name, text=part))
    return chunks


@lru_cache(maxsize=1)
def _build_kb_index() -> tuple[list[KBChunk], TfidfVectorizer, np.ndarray]:
    """
    Cache the KB vector index in-process for fast repeat queries.
    """
    chunks = _read_kb_chunks(KB_DIR)
    if not chunks:
        return [], TfidfVectorizer(), np.zeros((0, 0), dtype=np.float32)

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform([c.text for c in chunks]).toarray().astype(np.float32)
    return chunks, vectorizer, matrix


def retrieve_context(query: str, top_k: int = 4, min_score: float = 0.05) -> str:
    """
    Simple TF-IDF retrieval over knowledge_base/*.md paragraph chunks.
    Returns a compact text block to inject into the prompt.
    """
    chunks, vectorizer, matrix = _build_kb_index()
    if not chunks:
        return ""

    q = vectorizer.transform([query]).toarray().astype(np.float32)[0]
    denom = (np.linalg.norm(matrix, axis=1) * (np.linalg.norm(q) + 1e-8)) + 1e-8
    sims = (matrix @ q) / denom
    order = np.argsort(-sims)
    picked: list[int] = []
    for i in order:
        score = float(sims[int(i)])
        if score < min_score:
            break
        picked.append(int(i))
        if len(picked) >= max(1, min(top_k, len(chunks))):
            break

    if not picked:
        return ""

    blocks: list[str] = []
    for i in picked:
        c = chunks[i]
        blocks.append(f"[{c.source}]\n{c.text}")
    return "\n\n---\n\n".join(blocks).strip()


def _build_user_prompt(notes: str, retrieved_context: str) -> str:
    examples = "\n\n".join(
        [
            f"EXAMPLE {i+1} NOTES:\n{ex.notes}\n\nEXAMPLE {i+1} OUTPUT JSON:\n{ex.response_json}"
            for i, ex in enumerate(FEW_SHOTS)
        ]
    )
    ctx = retrieved_context.strip() if retrieved_context.strip() else "(None)"
    context_block = f"RETRIEVED CONTEXT:\n{ctx}\n\n"

    return f"{examples}\n\n{context_block}NOW PROCESS THESE MEETING NOTES:\n{notes.strip()}"


def generate_action_items(notes: str) -> dict:
    """
    Returns a dict matching ActionItemsResponse:
      {"action_items": [ {task, assignee, deadline, priority, confidence}, ... ]}
    """
    if not get_groq_api_key():
        raise RuntimeError("Missing GROQ_API_KEY. Copy .env.example to .env and set the key.")
    client = get_groq_client()
    model = get_default_groq_model()

    retrieved = retrieve_context(
        notes,
        top_k=int(os.getenv("RAG_TOP_K", "4")),
        min_score=float(os.getenv("RAG_MIN_SCORE", "0.05")),
    )
    user_prompt = _build_user_prompt(notes, retrieved_context=retrieved)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Groq call failed: {e}") from e

    content = (resp.choices[0].message.content or "").strip()
    if not content:
        raise RuntimeError("Groq returned an empty response.")

    data = json.loads(content)

    ActionItemsResponse.model_validate(data)
    return data


def generate_action_items_baseline(notes: str) -> dict:
    """
    Baseline = zero-shot only (no few-shots, no RAG).
    Still returns schema-valid JSON.
    """
    if not get_groq_api_key():
        raise RuntimeError("Missing GROQ_API_KEY. Copy .env.example to .env and set the key.")
    client = get_groq_client()
    model = get_default_groq_model()

    messages = [
        {"role": "system", "content": BASELINE_SYSTEM_PROMPT},
        {"role": "user", "content": notes.strip()},
    ]

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Groq call failed: {e}") from e

    content = (resp.choices[0].message.content or "").strip()
    if not content:
        raise RuntimeError("Groq returned an empty response.")

    data = json.loads(content)
    ActionItemsResponse.model_validate(data)
    return data
