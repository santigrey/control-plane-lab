import os
import re
import time
import uuid
import json
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ai_operator.tools.registry import default_registry
from ai_operator.inference.ollama import (
    ollama_embed,
    ollama_chat,
    get_ollama_url,
    get_embed_model,
    get_chat_model,
    get_expected_dim,
)
from ai_operator.memory.db import insert_memory, search_memories, get_latest_phrase, db_ping
from ai_operator.memory.writer import write_event
from ai_operator.memory.events import make_event, event_to_content, event_to_tool_result

app = FastAPI()
TOOLS = default_registry()


def parse_tool_call(text: str) -> Optional[Dict[str, Any]]:
    """
    Accepts a strict JSON object like:
      {"tool":"ping","args":{"message":"hi"}}
    Returns None if not a valid tool call.
    """
    try:
        obj = json.loads((text or "").strip())
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None

    tool = obj.get("tool")
    args = obj.get("args", {})
    if not isinstance(tool, str) or not tool.strip():
        return None
    if args is None:
        args = {}
    if not isinstance(args, dict):
        return None

    return {"tool": tool.strip(), "args": args}


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


_RECALL_RX = re.compile(
    r"^\s*what\s+exact\s+phrase\s+did\s+i\s+ask\s+you\s+to\s+remember\b", re.I
)
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
    return {"status": "ok"}


@app.get("/readyz", response_model=HealthResponse)
def readyz() -> Dict[str, Any]:
    details: Dict[str, Any] = {}
    ok = True

    try:
        db_ping()
        details["postgres"] = "ok"
    except Exception as e:
        ok = False
        details["postgres"] = f"error: {e}"

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

    run_id = str(uuid.uuid4())

    tool_used: Optional[str] = None
    tool_result: Optional[Dict[str, Any]] = None

    if mode == "remember":
        phrase = extract_phrase(user_prompt)
        if not phrase:
            raise HTTPException(status_code=400, detail="No phrase provided")

        t = time.time()
        remember_event = make_event(
            type="remember_phrase",
            source="orchestrator",
            data={"phrase": phrase},
        
            run_id=run_id,
        )

        mem_id = write_event(event=remember_event)
        timings["db_s"] = round(time.time() - t, 4)
        timings["total_s"] = round(time.time() - t0, 4)

        return {
            "model": CHAT_MODEL,
            "response": phrase,
            "memory_id": mem_id,
            "retrieved": [],
            "tool_used": tool_used,
            "tool_result": tool_result,
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
            "memory_id": None,
            "retrieved": [],
            "tool_used": tool_used,
            "tool_result": tool_result,
            "timings": {
                **timings,
                "embed_s": 0.0,
                "retrieve_s": 0.0,
                "generate_s": 0.0,
                "db_s": 0.0,
            },
            "config": {"mode": mode, "expected_dim": EXPECTED_DIM},
        }

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

    if INCLUDE_TOOLS:
        tc = parse_tool_call(response_text)
        if tc:
            tool_used = tc["tool"]
            tool_args = tc["args"]

            try:
                tool_result = TOOLS.run(tool_used, tool_args)
            except Exception as e:
                tool_result = {"ok": False, "tool": tool_used, "error": str(e)}

            tool_call_event = make_event(
                type="tool_call",
                source="orchestrator",
                data={"tool": tool_used, "args": tool_args},
            
            run_id=run_id,
        )

            write_event(event=tool_call_event)

            tool_result_event = make_event(
                type="tool_result",
                source=f"tool:{tool_used}",
                data={"tool": tool_used, "result": tool_result},
            
            run_id=run_id,
        )

            write_event(event=tool_result_event)

            followup_prompt = (
                f"{user_prompt}\n\n"
                f"TOOL_USED: {tool_used}\n"
                f"TOOL_RESULT: {tool_result}\n\n"
                "Now respond to the user with the final answer."
            )
            try:
                t = time.time()
                response_text = ollama_chat(SYSTEM_PROMPT, followup_prompt, injected_text)
                timings["generate_s_2"] = round(time.time() - t, 4)
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Generation (post-tool) failed: {e}"
                )

    response_event = make_event(
        type="response",
        source="orchestrator",
        data={
            "prompt": user_prompt,
            "retrieved_topk": len(retrieved),
            "retrieved_ids": [m.get("id") for m in retrieved if m.get("id")],
            "tool_used": tool_used,
            "response": response_text,
        },
    
            run_id=run_id,
        )

    mem_id = write_event(event=response_event)

    timings["db_s"] = round(time.time() - t0, 4)
    timings["total_s"] = round(time.time() - t0, 4)

    return {
        "model": CHAT_MODEL,
        "response": response_text,
        "memory_id": mem_id,
        "retrieved": retrieved,
        "tool_used": tool_used,
        "tool_result": tool_result,
        "timings": timings,
        "config": {"mode": "chat", "expected_dim": EXPECTED_DIM},
    }
