import os
from typing import List, Optional

import requests


def env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name, default)
    if v is None or v == "":
        raise RuntimeError(f"{name} is not set")
    return v


def env_int(name: str, default: str) -> int:
    return int(env(name, default).strip())


def get_ollama_url() -> str:
    return env("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")


def get_embed_model() -> str:
    return env("EMBED_MODEL", "mxbai-embed-large:latest")


def get_chat_model() -> str:
    return env("CHAT_MODEL", "llama3.1:8b")


def get_expected_dim() -> int:
    return env_int("EXPECTED_EMBED_DIM", "1024")


def ollama_embed(text: str) -> List[float]:
    url = f"{get_ollama_url()}/api/embeddings"
    model = get_embed_model()
    r = requests.post(url, json={"model": model, "prompt": text}, timeout=60)
    r.raise_for_status()
    data = r.json()
    emb = data.get("embedding") or []
    expected = get_expected_dim()
    if len(emb) != expected:
        raise RuntimeError(f"Expected {expected}-dim embedding, got {len(emb)}")
    return emb


def ollama_chat(system_prompt: str, user_prompt: str, injected_memories: str = "") -> str:
    url = f"{get_ollama_url()}/api/chat"
    model = get_chat_model()

    user_text = user_prompt
    if injected_memories.strip():
        user_text = (
            f"{user_prompt}\n\n"
            "----\n"
            "RELEVANT MEMORY (use only if helpful and consistent):\n"
            f"{injected_memories}\n"
            "----"
        )

    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
    }

    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    msg = data.get("message") or {}
    return (msg.get("content") or "").strip()
