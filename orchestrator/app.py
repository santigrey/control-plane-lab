import os
import re
import time
import json
import uuid
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from ai_operator.inference.ollama import (
    ollama_embed,
    ollama_chat,
    get_ollama_url,
    get_embed_model,
    get_chat_model,
    get_expected_dim,
)
from ai_operator.memory.db import search_memories, get_latest_phrase, db_ping
from ai_operator.memory.events import make_event
from ai_operator.memory.writer import write_event
from ai_operator.memory.trace import get_trace
from ai_operator.tools.registry import default_registry
from ai_operator.api.observability import RequestLoggingMiddleware

app = FastAPI()
app.add_middleware(RequestLoggingMiddleware)
TOOLS = default_registry()

# ---- tool call parsing (strict JSON only) ----
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


# ---- request/response models ----
class AskRequest(BaseModel):
    prompt: str


class HealthResponse(BaseModel):
    status: str
    details: Optional[Dict[str, Any]] = None


# ---- env helpers ----
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
            "\n"
            "Tool usage:\n"
            "- If you want to use a tool, output ONLY valid JSON like:\n"
            '  {"tool":"ping","args":{"message":"hi"}}\n'
            "- Otherwise, respond normally.\n"
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


@app.get("/trace/{run_id}")
def trace(run_id: str) -> Dict[str, Any]:
    """
    Return chronological EVENT envelopes for a given run_id.
    trace.py already parses event JSON into row["event"].
    """
    rows = get_trace(run_id)

    events: List[Dict[str, Any]] = []
    for r in rows:
        events.append({
            "created_at": r.get("created_at").isoformat() if r.get("created_at") else None,
            "tool": r.get("tool"),
            "event": r.get("event") or {},   # <-- key fix: use parsed event dict
        })

    return {"run_id": run_id, "count": len(events), "events": events}

@app.post("/ask")
def ask(req: AskRequest, request: Request) -> Dict[str, Any]:
    run_id = getattr(request.state, 'run_id', None) or str(uuid.uuid4())

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

        remember_event = make_event(
            type="remember_phrase",
            source="orchestrator",
            data={"phrase": phrase},
            run_id=run_id,
        )
        mem_id = write_event(event=remember_event)

        timings["db_s"] = round(time.time() - t0, 4)
        timings["total_s"] = round(time.time() - t0, 4)

        return {
            "model": CHAT_MODEL,
            "response": phrase,
            "memory_id": mem_id,
            "retrieved": [],
            "tool_used": None,
            "tool_result": None,
            "timings": {**timings, "embed_s": 0.0, "retrieve_s": 0.0, "generate_s": 0.0},
            "config": {"mode": mode, "expected_dim": EXPECTED_DIM},
            "run_id": run_id,
        }

    if mode == "recall":
        phrase = get_latest_phrase(include_tools=INCLUDE_TOOLS)
        if not phrase:
            raise HTTPException(status_code=404, detail="No remembered phrase found")

        timings["total_s"] = round(time.time() - t0, 4)
        return {
            "model": CHAT_MODEL,
            "response": phrase,
            "memory_id": None,  # DO NOT persist recall
            "retrieved": [],
            "tool_used": None,
            "tool_result": None,
            "timings": {**timings, "embed_s": 0.0, "retrieve_s": 0.0, "generate_s": 0.0, "db_s": 0.0},
            "config": {"mode": mode, "expected_dim": EXPECTED_DIM},
            "run_id": run_id,
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

    # 1) First model call
    try:
        t = time.time()
        model_out = ollama_chat(SYSTEM_PROMPT, user_prompt, injected_text)
        timings["generate_s"] = round(time.time() - t, 4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

    tool_used = None
    tool_result = None
    final_text = model_out

    # 2) If model output is a strict tool JSON, execute once, then do a second model call
    tool_call = parse_tool_call(model_out)
    if tool_call:
        tool_used = tool_call["tool"]
        args = tool_call["args"]

        tool_call_event = make_event(
            type="tool_call",
            source="orchestrator",
            data={"tool": tool_used, "args": args},
            run_id=run_id,
        )
        write_event(event=tool_call_event)

        try:
            tool_result = TOOLS.run(tool_used, args)
        except Exception as e:
            tool_result = {"ok": False, "error": str(e), "tool": tool_used}

        tool_result_event = make_event(
            type="tool_result",
            source=f"tool:{tool_used}",
            data={"tool": tool_used, "result": tool_result},
            run_id=run_id,
        )
        write_event(event=tool_result_event)

        # second model call with tool result appended
        followup = (
            "You executed a tool. Produce the final answer now.\n\n"
            f"TOOL_CALL: {json.dumps(tool_call, ensure_ascii=False)}\n"
            f"TOOL_RESULT: {json.dumps(tool_result, ensure_ascii=False, default=str)}\n"
        )
        try:
            t = time.time()
            final_text = ollama_chat(SYSTEM_PROMPT, followup, injected_text)
            timings["generate_s_2"] = round(time.time() - t, 4)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Second generation failed: {e}")

    # 3) Persist response event (canonical)
    response_event = make_event(
        type="response",
        source="orchestrator",
        data={
            "prompt": user_prompt,
            "response": final_text,
            "retrieved_topk": len(retrieved),
            "retrieved_ids": [m.get("id") for m in retrieved if m.get("id")],
            "tool_used": tool_used,
        },
        run_id=run_id,
    )
    mem_id = write_event(event=response_event)

    timings["db_s"] = round(time.time() - t0, 4)
    timings["total_s"] = round(time.time() - t0, 4)

    return {
        "model": CHAT_MODEL,
        "response": final_text,
        "memory_id": mem_id,
        "retrieved": retrieved,
        "tool_used": tool_used,
        "tool_result": tool_result,
        "timings": timings,
        "config": {"mode": "chat", "expected_dim": EXPECTED_DIM},
        "run_id": run_id,
    }
