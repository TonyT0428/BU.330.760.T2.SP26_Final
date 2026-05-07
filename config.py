from __future__ import annotations

import os

from dotenv import load_dotenv


def get_groq_api_key() -> str | None:
    load_dotenv()
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None
    return key.strip() or None


def get_groq_client():
    """
    Loads GROQ_API_KEY from `.env` (via dotenv) and returns a Groq client.
    """
    key = get_groq_api_key()
    if not key:
        raise RuntimeError("Missing GROQ_API_KEY. Copy .env.example to .env and set the key.")
    try:
        from groq import Groq  # type: ignore
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Missing dependency groq. ({e})") from e
    return Groq(api_key=key)


def get_default_groq_model() -> str:
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

