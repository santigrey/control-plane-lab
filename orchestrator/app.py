import os
import re
import time
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ai_operator.memory.db import insert_memory, search_memories, get_latest_phrase, db_ping

app = FastAPI()


class AskRequest(BaseModel):
    prompt: str


class HealthResponse(BaseModel):
    status: str
    details: Optional[Dict[str, Any]] = None


def env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name, default)
    if v is None or v == "":
        raise RuntimeError(f"{name} is not set")
    return v


def env_bool(name: str, default: str = "false") -> bool:
    return env(name, default).strip().lower() in ("1", "true", "yes", "y", "on")


def env_int(name: str, default: str) -> int:
    return int(env(name, default).strip())


def env_float(name: str, default: str) -> float:
    return float(env(name, default).strip())


def get_ollama_url() -> str:
    return env("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")


def get_embed_model() -> str:
    return env("EMBED_MODEL", "mxbai-embed-large:latest")


def get_chat_model() -> str:
    return env("CHAT_MODEL", "llama3.1:8b")


def get_expected_dim() -> int:
    return env_int("EXPECTED_EMBED_DIM", "1024")


def get_top_k() -> int:
    return env_int("TOP_K", "5")


def get_min_similarity() -> float:
    return env_float("MIN_SIMILARITY", "0.6")


def get_include_tools() -> bool:
    return env_bool("INCLUDE_TOOLS", "false")


def get_system_prompt() -> str:
    return env(
        "SYSTEM_PROMPT",
        (
            "You are Alexandra 2.0 — a precise, fast assistant.\n"
            "If the user asks for an exact phrase, reply with ONLY that phrase, no extra text.\n"
            "Follow the user's instructions exactly.\n"
        ),
    )


# ---- intent detection ----
_RECALL_RX = re.compile(r"^\s*what\s+exact\s+phrase\s+did\s+i\s+ask\s+you\s+to\s+remember\b", re.I)
_REMEMBER_RX = re.compile(r"^\s*remember\s+this\s+exact\s+phrase\s*:\s*(.+)\s*$", re.I)


def classify_mode(prompt: str) -> str:
    p = (prompt or "").strip()
    if not p:
        return "empty"
    if _REMEMBER_RX.match(p):
        return "remember"
    if _RECALL_RX.match(p):
        return "recall"
    return "chat"


def extract_phrase(prompt: str) -> str:
    m = _REMEMBER_RX.match((prompt or "").strip())
    return (m.group(1) or "").strip() if m else ""


# ---- ollama ----
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


def format_retrieved_for_injection(retrieved: List[Dict[str, Any]]) -> str:
    chunks: List[str] = []
    for m in retrieved:
        content = (m.get("content") or "").strip()
        if not content:
            continue
        mid = m.get("id")
        sim = m.get("cosine_sim")
        header = []
        if mid:
            header.append(f"id={mid}")
        if sim is not None:
            try:
                header.append(f"sim={float(sim):.3f}")
            except Exception:
                pass
        chunks.append(f"[{', '.join(header)}]\n{content}" if header else content)
    return "\n\n".join(chunks)


@app.get("/healthz", response_model=HealthResponse)
def healthz() -> Dict[str, Any]:
    # Liveness: process is up
    return {"status": "ok"}


@app.get("/readyz", response_model=HealthResponse)
def readyz() -> Dict[str, Any]:
    # Readiness: dependencies are reachable
    details: Dict[str, Any] = {}
    ok = True

    # Postgres
    try:
        db_ping()
        details["postgres"] = "ok"
    except Exception as e:
        ok = False
        details["postgres"] = f"error: {e}"

    # Ollama
    try:
        r = requests.get(f"{get_ollama_url()}/api/tags", timeout=10)
        r.raise_for_status()
        details["ollama"] = "ok"
    except Exception as e:
        ok = False
        details["ollama"] = f"error: {e}"

    if not ok:
        raise HTTPException(status_code=503, detail=details)
    return {"status": "ok", "details": details}


@app.post("/ask")
def ask(req: AskRequest) -> Dict[str, Any]:
    user_prompt = (req.prompt or "").strip()
    if not user_prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    TOP_K = get_top_k()
    MIN_SIMILARITY = get_min_similarity()
    INCLUDE_TOOLS = get_include_tools()
    EMBED_MODEL = get_embed_model()
    CHAT_MODEL = get_chat_model()
    EXPECTED_DIM = get_expected_dim()
    SYSTEM_PROMPT = get_system_prompt()

    mode = classify_mode(user_prompt)

    timings: Dict[str, float] = {}
    t0 = time.time()

    # --- remember/recall are deterministic and do NOT touch Ollama ---
    if mode == "remember":
        phrase = extract_phrase(user_prompt)
        if not phrase:
            raise HTTPException(status_code=400, detail="No phrase provided")

        t = time.time()
        mem_id = insert_memory(
            source="orchestrator",
            content=f"PHRASE: {phrase}",
            embedding=None,                 # no embedding needed
            embedding_model=EMBED_MODEL,
            tool=None,
            tool_result={"mode": "remember"},
        )
        timings["db_s"] = round(time.time() - t, 4)
        timings["total_s"] = round(time.time() - t0, 4)

        return {
            "model": CHAT_MODEL,
            "response": phrase,
            "memory_id": mem_id,
            "retrieved": [],
            "timings": {**timings, "embed_s": 0.0, "retrieve_s": 0.0, "generate_s": 0.0},
            "config": {"mode": mode, "expected_dim": EXPECTED_DIM},
        }

    if mode == "recall":
        phrase = get_latest_phrase(include_tools=INCLUDE_TOOLS)
        if not phrase:
            raise HTTPException(status_code=404, detail="No remembered phrase found")

        timings["total_s"] = round(time.time() - t0, 4)
        return {
            "model": CHAT_MODEL,
            "response": phrase,
            "memory_id": None,   # DO NOT persist recall
            "retrieved": [],
            "timings": {**timings, "embed_s": 0.0, "retrieve_s": 0.0, "generate_s": 0.0, "db_s": 0.0},
            "config": {"mode": mode, "expected_dim": EXPECTED_DIM},
        }

    # --- chat mode uses embeddings + retrieval + ollama ---
    try:
        t = time.time()
        query_emb = ollama_embed(user_prompt)
        timings["embed_s"] = round(time.time() - t, 4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}")

    try:
        t = time.time()
        retrieved = search_memories(
            query_embedding=query_emb,
            top_k=TOP_K,
            min_similarity=MIN_SIMILARITY,
            include_tools=INCLUDE_TOOLS,
        )
        timings["retrieve_s"] = round(time.time() - t, 4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory search failed: {e}")

    injected_text = format_retrieved_for_injection(retrieved)

    try:
        t = time.time()
        response_text = ollama_chat(SYSTEM_PROMPT, user_prompt, injected_text)
        timings["generate_s"] = round(time.time() - t, 4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

    # persist chat
    mem_id = insert_memory(
        source="orchestrator",
        content=f"PROMPT: {user_prompt}\nRETRIEVED_TOPK: {len(retrieved)}\nRESPONSE: {response_text}",
        embedding=query_emb,
        embedding_model=EMBED_MODEL,
        tool="retrieval_injection",
        tool_result={
            "mode": "chat",
            "top_k": TOP_K,
            "min_similarity": MIN_SIMILARITY,
            "include_tools": INCLUDE_TOOLS,
            "chat_model": CHAT_MODEL,
            "embed_model": EMBED_MODEL,
            "retrieved_ids": [m.get("id") for m in retrieved if m.get("id")],
        },
    )

    timings["db_s"] = round(time.time() - t0, 4)  # coarse but fine
    timings["total_s"] = round(time.time() - t0, 4)

    return {
        "model": CHAT_MODEL,
        "response": response_text,
        "memory_id": mem_id,
        "retrieved": retrieved,
        "timings": timings,
        "config": {"mode": "chat", "expected_dim": EXPECTED_DIM},
    }