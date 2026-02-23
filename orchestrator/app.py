import os
import re
import time
import json
import uuid
from typing import Any, Dict, List, Optional

import requests
import psycopg
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
from ai_operator.memory.db import search_memories, get_latest_phrase, db_ping, get_db_url
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


class ToolCallResponse(BaseModel):
    tool: str
    args: Dict[str, Any] = {}
    result: Optional[Dict[str, Any]] = None


class AskResponse(BaseModel):
    status: str
    answer: str
    tool_calls: List[ToolCallResponse]
    memory_ids: List[str]
    retrieved_ids: List[str]
    retrieved_topk: int
    run_id: str


class HealthResponse(BaseModel):
    status: str
    details: Optional[Dict[str, Any]] = None


FALLBACK_ANSWER = "Sorry, I could not generate a valid response."


def _safe_answer(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text:
            return text
    return FALLBACK_ANSWER


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
_TOKEN_RX = re.compile(r"\b[A-Z]+[A-Z0-9-]{3,}\b")


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


def is_token_recall_prompt(prompt: str) -> bool:
    p = (prompt or "").strip().lower()
    return p.startswith("recall:") or "reply with only the token" in p


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
    # Liveness + dependency snapshot (non-fatal for probe callers)
    details: Dict[str, Any] = {"api": "ok"}
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

    # Worker/service status (best effort, only if tasks table exists)
    try:
        with psycopg.connect(get_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT to_regclass('public.tasks')")
                has_tasks_table = cur.fetchone()[0] is not None
                if not has_tasks_table:
                    details["worker"] = {"status": "unavailable", "reason": "tasks_table_missing"}
                else:
                    cur.execute(
                        """
                        SELECT
                          COUNT(*) FILTER (WHERE status='queued') AS queued,
                          COUNT(*) FILTER (WHERE status='running') AS running,
                          COUNT(DISTINCT locked_by) FILTER (
                            WHERE status='running'
                              AND locked_by IS NOT NULL
                              AND lock_expires_at IS NOT NULL
                              AND lock_expires_at > now()
                          ) AS active_workers
                        FROM tasks;
                        """
                    )
                    queued, running, active_workers = cur.fetchone()
                    queued_n = int(queued or 0)
                    running_n = int(running or 0)
                    active_workers_n = int(active_workers or 0)
                    if active_workers_n > 0:
                        worker_status = "ok"
                    elif queued_n == 0 and running_n == 0:
                        worker_status = "idle"
                    else:
                        worker_status = "unknown"
                    details["worker"] = {
                        "status": worker_status,
                        "active_workers": active_workers_n,
                        "running_tasks": running_n,
                        "queued_tasks": queued_n,
                        "signal_source": "tasks.locked_by+lock_expires_at",
                    }
    except Exception as e:
        details["worker"] = {"status": "unavailable", "reason": f"error: {e}"}

    return {"status": "ok" if ok else "degraded", "details": details}


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

@app.post("/ask", response_model=AskResponse)
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

        return {
            "status": "ok",
            "answer": _safe_answer(phrase),
            "tool_calls": [],
            "memory_ids": [mem_id],
            "retrieved_ids": [],
            "retrieved_topk": 0,
            "run_id": run_id,
        }

    if mode == "recall":
        phrase = get_latest_phrase(include_tools=INCLUDE_TOOLS)
        if not phrase:
            raise HTTPException(status_code=404, detail="No remembered phrase found")

        return {
            "status": "ok",
            "answer": _safe_answer(phrase),
            "tool_calls": [],
            "memory_ids": [],
            "retrieved_ids": [],
            "retrieved_topk": 0,
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

    retrieved_ids = [str(m.get("id")) for m in retrieved if m.get("id")]

    if is_token_recall_prompt(user_prompt) and len(retrieved) > 0:
        token_candidates = set()
        for m in retrieved:
            content = str(m.get("content") or "")
            token_candidates.update(_TOKEN_RX.findall(content))

        if len(token_candidates) == 1:
            token_answer = next(iter(token_candidates))
            response_event = make_event(
                type="response",
                source="orchestrator",
                data={
                    "prompt": user_prompt,
                    "response": token_answer,
                    "retrieved_topk": len(retrieved),
                    "retrieved_ids": retrieved_ids,
                    "tool_used": None,
                },
                run_id=run_id,
            )
            mem_id = write_event(event=response_event)
            return {
                "status": "ok",
                "answer": token_answer,
                "tool_calls": [],
                "memory_ids": [mem_id],
                "retrieved_ids": retrieved_ids,
                "retrieved_topk": len(retrieved),
                "run_id": run_id,
            }

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
    tool_calls: List[Dict[str, Any]] = []
    memory_ids: List[str] = []
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
        tool_call_mem_id = write_event(event=tool_call_event)
        memory_ids.append(tool_call_mem_id)

        try:
            tool_result = TOOLS.run(tool_used, args)
        except Exception as e:
            tool_result = {"ok": False, "error": str(e), "tool": tool_used}
        tool_calls.append({"tool": tool_used, "args": args, "result": tool_result})

        tool_result_event = make_event(
            type="tool_result",
            source=f"tool:{tool_used}",
            data={"tool": tool_used, "result": tool_result},
            run_id=run_id,
        )
        tool_result_mem_id = write_event(event=tool_result_event)
        memory_ids.append(tool_result_mem_id)

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
            "response": _safe_answer(final_text),
            "retrieved_topk": len(retrieved),
            "retrieved_ids": retrieved_ids,
            "tool_used": tool_used,
        },
        run_id=run_id,
    )
    mem_id = write_event(event=response_event)
    memory_ids.append(mem_id)

    timings["db_s"] = round(time.time() - t0, 4)
    timings["total_s"] = round(time.time() - t0, 4)

    return {
        "status": "ok",
        "answer": _safe_answer(final_text),
        "tool_calls": tool_calls,
        "memory_ids": memory_ids,
        "retrieved_ids": retrieved_ids,
        "retrieved_topk": len(retrieved),
        "run_id": run_id,
    }
