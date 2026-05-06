from __future__ import annotations

from dataclasses import dataclass


BASELINE_SYSTEM = """\
You are a helpful assistant. Answer the user's question clearly and concisely.
If you are unsure, say so.
"""


IMPROVED_SYSTEM = """\
You are a helpful assistant that answers using the provided context.

Rules:
- Prefer the provided context over general knowledge.
- If the context is insufficient, say what is missing and give a best-effort answer.
- Cite the most relevant context snippets by quoting short phrases (no fake sources).
"""


@dataclass(frozen=True)
class FewShot:
    user: str
    assistant: str


FEW_SHOTS: list[FewShot] = [
    FewShot(
        user="What is RAG in one sentence?",
        assistant=(
            "RAG (Retrieval-Augmented Generation) is a method that retrieves relevant documents "
            "to ground an LLM's response in specific context."
        ),
    ),
    FewShot(
        user="How should I respond if the context doesn't mention the answer?",
        assistant=(
            "I should say the context is insufficient, explain what evidence is missing, "
            "and then provide a cautious best-effort answer."
        ),
    ),
]


def build_messages_baseline(question: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": BASELINE_SYSTEM},
        {"role": "user", "content": question.strip()},
    ]


def build_messages_improved(question: str, context: str) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": IMPROVED_SYSTEM}]
    for ex in FEW_SHOTS:
        messages.append({"role": "user", "content": ex.user})
        messages.append({"role": "assistant", "content": ex.assistant})

    messages.append(
        {
            "role": "user",
            "content": (
                "Context:\n"
                f"{context.strip()}\n\n"
                "Question:\n"
                f"{question.strip()}"
            ),
        }
    )
    return messages
