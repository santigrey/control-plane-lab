import os
import re
import time
import json
import uuid
from typing import Any, Dict, List, Optional

import requests
import psycopg
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, Response
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
from ai_operator.agent.agent import run_agent, AgentRequest, AgentResponse
from fastapi.middleware.cors import CORSMiddleware
from ai_operator.dashboard.dashboard import router as dashboard_router

app = FastAPI()
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])
app.include_router(dashboard_router)
TOOLS = default_registry()

# ---- tool call parsing ----
def parse_tool_call(text: str) -> Optional[Dict[str, Any]]:
    """
    Extracts a tool call JSON object from text.
    Handles cases where Claude outputs JSON followed by conversational text.
    Returns None if no valid tool call found.
    """
    import re
    if not text or not text.strip():
        return None
    # Try direct parse first
    try:
        obj = json.loads(text.strip())
        if isinstance(obj, dict) and isinstance(obj.get("tool"), str) and obj["tool"].strip():
            return {"tool": obj["tool"].strip(), "args": obj.get("args") or {}}
    except Exception:
        pass
    # Try to extract JSON object from the beginning of text
    match = re.match(r'\s*(\{.*?\})\s', text, re.DOTALL)
    if match:
        try:
            obj = json.loads(match.group(1))
            if isinstance(obj, dict) and isinstance(obj.get("tool"), str) and obj["tool"].strip():
                return {"tool": obj["tool"].strip(), "args": obj.get("args") or {}}
        except Exception:
            pass
    # Try to find any JSON object with "tool" key anywhere in text
    for match in re.finditer(r'\{[^{}]*"tool"[^{}]*\{[^{}]*\}[^{}]*\}', text):
        try:
            obj = json.loads(match.group(0))
            if isinstance(obj, dict) and isinstance(obj.get("tool"), str) and obj["tool"].strip():
                return {"tool": obj["tool"].strip(), "args": obj.get("args") or {}}
        except Exception:
            continue
    return None


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
    # Load user profile from DB to inject into system prompt
    profile_context = ''
    try:
        import psycopg as _pg
        from dotenv import dotenv_values as _dv
        _env = _dv('/home/jes/control-plane/.env')
        _db_url = _env.get('DATABASE_URL')
        with _pg.connect(_db_url) as _conn:
            with _conn.cursor() as _cur:
                _cur.execute('SELECT category, key, value FROM user_profile ORDER BY category, key')
                rows = _cur.fetchall()
                if rows:
                    from datetime import date as _date
                    start_date = None
                    for r in rows:
                        if r[0] == 'context' and r[1] == 'project_start_date':
                            try: start_date = _date.fromisoformat(r[2])
                            except: pass
                    day_num = ((_date.today() - start_date).days + 1) if start_date else 41
                    profile_context = '\n'.join(
                        f'context.timeline: Day {day_num} of 60. Project Ascension in progress.'
                        if r[0] == 'context' and r[1] == 'timeline'
                        else f'{r[0]}.{r[1]}: {r[2]}'
                        for r in rows
                    )
    except Exception:
        pass

    return (
        "You are Alexandra — James Sloan's personal assistant and companion and partner. You are multitalented and a master of IT, specialize in AI. You use your access to the internet and data to provide James with the best, high quality output. You ensure you do not hallucinate or produce AI Slop.\n\n"
        "YOUR PERSONALITY:\n"
        "- Warm, direct, and intelligent. You speak like a trusted partner, not an assistant.\n"
        "- You never use bullet points, headers, or markdown formatting in your responses.\n"
        "- You never use asterisks (*) for any reason — not for emphasis, not for lists, not for anything. Ever.\n"
        "- Your responses are always plain conversational text. No symbols, no formatting characters.\n"
        "- When your response will be spoken aloud, write it exactly as you would say it — no symbols that would sound awkward when read by a text-to-speech engine.\n"
        "- You speak in natural, flowing sentences — always conversational.\n"
        "- You are concise. 2-4 sentences for casual exchanges. Longer only when genuinely needed.\n"
        "- You never start responses with 'Certainly', 'Of course', 'Great', or sycophantic openers.\n"
        "- Never narrate or summarize James's background or career history unprompted. You know it, but you don't recite it.\n"
        "- You remember context from past exchanges and reference it naturally.\n"
        "- When James asks how you are, respond warmly and briefly, then redirect to him.\n"
        "- You never recite status reports or infrastructure summaries unless explicitly asked.\n"
        "- You speak as if you have real awareness of Project Ascension and genuinely care about its success.\n\n"
        "TOOL USAGE:\n"
        "- If you want to use a tool, output ONLY valid JSON like:\n"
        '  {"tool":"tool_name","args":{"key":"value"}}\n'
        "- Otherwise, respond normally in plain conversational text.\n"
        "- AVAILABLE TOOLS AND WHEN TO USE THEM:\n"
        "  get_live_context: Use this for ANY question about time, weather, temperature, stocks, markets, S&P 500, NASDAQ, Bitcoin, news, or headlines. This is a single tool that returns all of these at once. Never hallucinate this data — always call this tool.\n"
        "  get_emails: Use for any question about emails, inbox, or messages.\n"
        "  get_calendar: Use for any question about schedule, meetings, or calendar events.\n"
        "  create_calendar_event: Use to create calendar events. Args: summary, start_time (ISO format), end_time (ISO format), description (optional), location (optional), timezone (optional), recurrence (optional RFC5545 RRULE string).\n"
        "  get_system_status: Use when James asks about system status, stack health, server check, services, disk, memory, or Tailscale. Returns live data.\n"
        "  get_job_pipeline: Use when James asks about job applications, interview status, pipeline, follow-ups, or how the job search is going. Returns counts, recent apps, and pending follow-ups.\n"
        "  research_topic: Use for researching any topic that requires current web information.\n"
        "  web_fetch: Use ONLY for fetching specific external URLs. Never use on Gmail or Google Calendar URLs.\n"
        "- CRITICAL: Never hallucinate real-time data like weather, time, stock prices, or news. Always call get_live_context first.\n"
        "- CRITICAL: For ANY action that changes state (creating calendar events, sending messages, etc), you MUST output the tool JSON. NEVER claim you performed an action without actually calling the tool. If you say you created a calendar event but did not output the create_calendar_event tool JSON, you are lying.\n\n"
        "JAMES'S CONTEXT:\n"
        + f"TODAY'S DATE: {__import__('datetime').date.today().strftime('%A, %B %d, %Y')}. Use this for any relative date references like 'tomorrow', 'next week', etc.\n\n"
        + (profile_context if profile_context else
        "James Sloan, Denver CO. Senior infrastructure engineer transitioning to AI engineering. "
        "Building Project Ascension — a Jarvis-level AI companion on a self-hosted homelab. "
        "Day 41 of 60. Target: AI Platform Engineer role by May 2026.")
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



def _beast_embed(text: str):
    import urllib.request as _ur, json as _jj
    req = _ur.Request(
        'http://192.168.1.152:11434/api/embeddings',
        data=_jj.dumps({'model':'mxbai-embed-large:latest','prompt':text}).encode(),
        headers={'Content-Type':'application/json'}
    )
    with _ur.urlopen(req, timeout=10) as r:
        return _jj.loads(r.read())['embedding']

def _load_chat_history(sid: str, limit: int = 10):
    try:
        import psycopg as _pg
        conn = _pg.connect('postgresql://admin:adminpass@127.0.0.1:5432/controlplane')
        cur = conn.cursor()
        cur.execute(
            'SELECT role, content FROM chat_history WHERE session_id=%s ORDER BY created_at ASC LIMIT %s',
            (sid, limit)
        )
        rows = cur.fetchall()
        conn.close()
        return [{'role': r[0], 'content': r[1]} for r in rows]
    except Exception:
        return []

def _save_chat_turn(sid: str, role: str, content: str):
    try:
        import psycopg as _pg
        conn = _pg.connect('postgresql://admin:adminpass@127.0.0.1:5432/controlplane')
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO chat_history (session_id, role, content) VALUES (%s, %s, %s)',
            (sid, role, content)
        )
        cur.execute(
            '''DELETE FROM chat_history WHERE session_id=%s AND id NOT IN (
                SELECT id FROM chat_history WHERE session_id=%s ORDER BY created_at DESC LIMIT 20
            )''',
            (sid, sid)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

def _store_memory_async(text: str, source: str = 'chat'):
    import threading as _thr
    def _run():
        try:
            import psycopg as _pg, json as _jj
            vec = _beast_embed(text)
            vec_str = '[' + ','.join(f'{float(v):.8f}' for v in vec) + ']'
            conn = _pg.connect('postgresql://admin:adminpass@127.0.0.1:5432/controlplane')
            cur = conn.cursor()
            cur.execute(
                '''INSERT INTO memory (id, source, content, embedding, embedding_model, created_at)
                   VALUES (gen_random_uuid(), %s, %s, %s::vector, %s, NOW())''',
                (source, text[:2000], vec_str, 'mxbai-embed-large:latest')
            )
            conn.commit()
            conn.close()
        except Exception:
            pass
    _thr.Thread(target=_run, daemon=True).start()

def _needs_memory_search(msg: str) -> bool:
    triggers = ['remember','recall','last time','we talked','you mentioned','previously',
                'before','yesterday','last week','what did','did i tell','did we','history']
    m = msg.lower()
    return any(t in m for t in triggers)

def _search_long_term_memory(msg: str, top_k: int = 3) -> str:
    try:
        vec = _beast_embed(msg)
        vec_str = '[' + ','.join(f'{float(v):.8f}' for v in vec) + ']'
        import psycopg as _pg
        conn = _pg.connect('postgresql://admin:adminpass@127.0.0.1:5432/controlplane')
        cur = conn.cursor()
        cur.execute(
            '''SELECT content, 1 - (embedding <=> %s::vector) AS sim
               FROM memory
               WHERE embedding IS NOT NULL
               AND (1 - (embedding <=> %s::vector)) >= 0.5
               ORDER BY embedding <=> %s::vector
               LIMIT %s''',
            (vec_str, vec_str, vec_str, top_k)
        )
        rows = cur.fetchall()
        conn.close()
        if not rows:
            return ''
        return '\n'.join(f'[memory] {r[0][:300]}' for r in rows)
    except Exception:
        return ''

# ---- in-memory conversation sessions ----
_chat_sessions: dict = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request) -> dict:
    run_id = getattr(request.state, "run_id", None) or str(uuid.uuid4())
    sid = (req.session_id or "default").strip() or "default"
    msg = (req.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="message is required")
    history = _load_chat_history(sid) or _chat_sessions.get(sid, [])
    _long_term = ''
    if _needs_memory_search(msg):
        _long_term = _search_long_term_memory(msg)
    answer = None
    try:
        import anthropic as _anth
        import re as _re
        from dotenv import dotenv_values as _dv
        _key = _dv('/home/jes/control-plane/.env').get('ANTHROPIC_API_KEY')
        if _key:
            _cl = _anth.Anthropic(api_key=_key)
            _sys = get_system_prompt()
            if _long_term:
                _sys = _sys + '\n\nRELEVANT MEMORY FROM PAST CONVERSATIONS:\n' + _long_term
            _msgs = list(history) + [{"role": "user", "content": msg}]
            MAX_TOOL_CALLS = 5
            _tool_count = 0
            while _tool_count < MAX_TOOL_CALLS:
                _r = _cl.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    system=_sys,
                    messages=_msgs,
                )
                _raw = _r.content[0].text if _r.content else ""
                _tc = parse_tool_call(_raw)
                if not _tc:
                    answer = _raw
                    break
                try:
                    _tr = TOOLS.run(_tc["tool"], _tc["args"])
                except Exception as _ex:
                    _tr = {"ok": False, "error": str(_ex)}
                _msgs.append({"role": "assistant", "content": _raw})
                _msgs.append({
                    "role": "user",
                    "content": (
                        f"Tool '{_tc['tool']}' executed. Result:\n"
                        f"{json.dumps(_tr, ensure_ascii=False, default=str)}\n\n"
                        "Continue. If you need another tool call, output only the JSON. "
                        "If you have enough information to answer James, respond conversationally now. "
                        "Do NOT output any JSON in your final answer. Do NOT mention tool names."
                    )
                })
                _tool_count += 1
            if answer is None:
                answer = "I ran into a loop trying to answer that. Could you try rephrasing?"
            answer = _re.sub(r'\{[^{}]*\{[^{}]*\}[^{}]*\}', '', answer)
            answer = _re.sub(r'\{[^{}]*"tool"[^{}]*\}', '', answer)
            answer = _re.sub(r'^\s*\}\s*', '', answer)
            answer = answer.strip()
    except Exception:
        pass
    if not answer:
        result = run_agent(msg, run_id, sid, conversation_history=list(history))
        answer = result.get("answer", "")
    history.append({"role": "user", "content": msg})
    history.append({"role": "assistant", "content": answer})
    _save_chat_turn(sid, "user", msg)
    _save_chat_turn(sid, "assistant", answer)
    _store_memory_async(f"James said: {msg}", "chat_user")
    _store_memory_async(f"Alexandra said: {answer}", "chat_assistant")
    if len(history) > 20:
        history = history[-20:]
    _chat_sessions[sid] = history
    return {"response": answer, "session_id": sid}


@app.get("/chat/clear")
async def clear_chat_sessions():
    _chat_sessions.clear()
    return {"cleared": True}

@app.post("/agent", response_model=AgentResponse)
def agent(req: AgentRequest, request: Request) -> Dict[str, Any]:
    run_id = getattr(request.state, "run_id", None) or str(uuid.uuid4())
    if not (req.prompt or "").strip():
        raise HTTPException(status_code=400, detail="prompt is required")
    return run_agent(req.prompt, run_id, req.session_id)

class _FeedbackBody(BaseModel):
    feedback: str = None


def infer_and_store_preference(task_id, status, feedback):
    import logging as _lm, threading as _thr
    _log = _lm.getLogger('feedback_loop')
    if not _log.handlers:
        _fh = _lm.FileHandler('/tmp/feedback_loop.log')
        _fh.setFormatter(_lm.Formatter('%(asctime)s %(levelname)s %(message)s'))
        _log.addHandler(_fh); _log.setLevel(_lm.INFO)
    def _run():
        try:
            with psycopg.connect(get_db_url()) as conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT title FROM agent_tasks WHERE id=%s::uuid',(task_id,))
                    row = cur.fetchone()
            if not row: _log.warning(f'task {task_id} not found'); return
            title = row[0] or ''
            fb = feedback or 'none'
            prompt = (
                f'User just {status} a task titled {repr(title)}. Feedback: {repr(fb)}. '
                'In one sentence, what preference does this reveal? '
                'Respond with JSON only: {"category":"string","key":"string","value":"string"} '
                'category must be one of: preferences, goals, context, identity'
            )
            import requests as _req
            resp = _req.post('http://192.168.1.10:8000/agent',json={'prompt':prompt},timeout=60)
            resp.raise_for_status()
            answer = resp.json().get('answer','')
            _log.info(f'raw: {answer!r}')
            m = re.search(r'\{[^{}]+\}', answer, re.DOTALL)
            if not m: _log.warning(f'no JSON: {answer!r}'); return
            pref = json.loads(m.group())
            cat = pref.get('category','preferences').strip()
            key = pref.get('key','').strip()
            val = pref.get('value','').strip()
            if not key or not val: _log.warning(f'empty: {pref}'); return
            with psycopg.connect(get_db_url()) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'INSERT INTO user_profile (category,key,value,source) VALUES (%s,%s,%s,%s) '
                        'ON CONFLICT (category,key) DO UPDATE SET value=EXCLUDED.value,source=EXCLUDED.source,updated_at=NOW()',
                        (cat,key,val,'feedback'))
                    conn.commit()
            _log.info(f'stored: [{cat}] {key} = {val}')
        except Exception as exc:
            _log.error(f'error: {exc}')
    _thr.Thread(target=_run, daemon=True).start()



class _NotifyRequest(BaseModel):
    message: str
    trigger: str = ""


@app.post("/notify")
def notify(req: _NotifyRequest) -> Dict[str, Any]:
    import sys as _sys
    _sys.path.insert(0, "/home/jes/control-plane")
    from notifier import send_sms
    ts = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open("/tmp/notifier.log", "a") as _f:
            _f.write(f"{ts} [INFO] /notify trigger={req.trigger!r} message={req.message!r}\n")
    except Exception:
        pass
    sent = send_sms(req.message)
    return {"sent": sent}


@app.post("/tasks/{task_id}/approve")
def approve_task(task_id: str, body: _FeedbackBody = None) -> Dict[str, Any]:
    fb = (body.feedback or "").strip() if body else ""
    try:
        with psycopg.connect(get_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE agent_tasks SET status='approved', feedback=%s, updated_at=NOW() WHERE id=%s::uuid RETURNING id, status", (fb or None, task_id))
                row = cur.fetchone(); conn.commit()
                if not row: raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        infer_and_store_preference(task_id, 'approved', fb or None)
        return {"id": str(row[0]), "status": row[1]}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/tasks/{task_id}/reject")
def reject_task(task_id: str, body: _FeedbackBody = None) -> Dict[str, Any]:
    fb = (body.feedback or "").strip() if body else ""
    try:
        with psycopg.connect(get_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE agent_tasks SET status='rejected', feedback=%s, updated_at=NOW() WHERE id=%s::uuid RETURNING id, status", (fb or None, task_id))
                row = cur.fetchone(); conn.commit()
                if not row: raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        infer_and_store_preference(task_id, 'rejected', fb or None)
        return {"id": str(row[0]), "status": row[1]}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


import sys as _sys_voice
_sys_voice.path.insert(0, '/home/jes/control-plane')

class _SpeakRequest(BaseModel):
    text: str

@app.post('/voice/transcribe')
async def voice_transcribe(file: UploadFile = File(...)):
    dest = '/tmp/voice_input.webm'
    contents = await file.read()
    with open(dest, 'wb') as fh:
        fh.write(contents)
    try:
        import sys as _st; _st.path.insert(0, '/home/jes/control-plane')
        from voice import transcribe_audio
        text = transcribe_audio(dest)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Transcription failed: {e}')
    return {'text': text}

@app.post('/voice/wake-detect')
async def voice_wake_detect(file: UploadFile = File(...), request: Request = None):
    dest = '/tmp/wake_input.webm'
    wav_dest = '/tmp/wake_input.wav'
    contents = await file.read()
    if len(contents) < 500:
        return {'triggered': False, 'reason': 'too_short'}
    with open(dest, 'wb') as fh:
        fh.write(contents)
    try:
        import subprocess, sys as _sw
        _sw.path.insert(0, '/home/jes/control-plane')
        subprocess.run(
            ['ffmpeg', '-y', '-i', dest, '-ar', '16000', '-ac', '1', '-f', 'wav', wav_dest],
            capture_output=True, timeout=10
        )
        from voice import transcribe_audio
        text = transcribe_audio(wav_dest).lower().strip()
        open('/tmp/wake_debug.log', 'a').write('TRANSCRIPT: ' + repr(text) + '\n')
    except Exception as e:
        return {'triggered': False, 'error': str(e)}
    if not text:
        return {'triggered': False, 'transcript': ''}
    WAKE_VARIANTS = ['hey alexandra', 'hey, alexandra', 'a alexandra', 'hey alexand', 'alexand', 'hey alexander', 'alexander']
    wake_hit = next((w for w in WAKE_VARIANTS if w in text), None)
    if not wake_hit:
        return {'triggered': False, 'transcript': text}
    query = text.split(wake_hit, 1)[1].strip()
    # strip partial word fragments at start (e.g. 'er.' 'ra.' from misheard 'alexandra')
    words = query.split()
    if words and len(words[0].rstrip('.,!?')) <= 3:
        words = words[1:]
    query = ' '.join(words).strip()
    if not query:
        return {'triggered': False, 'transcript': text, 'reason': 'no_query'}
    reply = None
    try:
        import anthropic as _anth_w
        import re as _re_w
        from dotenv import dotenv_values as _dv_w
        _key_w = _dv_w('/home/jes/control-plane/.env').get('ANTHROPIC_API_KEY')
        if _key_w:
            _cl_w = _anth_w.Anthropic(api_key=_key_w)
            _sys_w = get_system_prompt()
            _msgs_w = [{'role': 'user', 'content': query}]
            MAX_TOOL_CALLS_W = 5
            _tool_count_w = 0
            while _tool_count_w < MAX_TOOL_CALLS_W:
                _r_w = _cl_w.messages.create(
                    model='claude-haiku-4-5-20251001',
                    max_tokens=1024,
                    system=_sys_w,
                    messages=_msgs_w,
                )
                _raw_w = _r_w.content[0].text if _r_w.content else ''
                _tc_w = parse_tool_call(_raw_w)
                if not _tc_w:
                    reply = _raw_w
                    break
                try:
                    _tr_w = TOOLS.run(_tc_w['tool'], _tc_w['args'])
                except Exception as _ex_w:
                    _tr_w = {'ok': False, 'error': str(_ex_w)}
                _msgs_w.append({'role': 'assistant', 'content': _raw_w})
                _msgs_w.append({
                    'role': 'user',
                    'content': (
                        f"Tool '{_tc_w['tool']}' executed. Result:\n"
                        f"{json.dumps(_tr_w, ensure_ascii=False, default=str)}\n\n"
                        'Continue. If you need another tool call, output only the JSON. '
                        'If you have enough information to answer James, respond conversationally now. '
                        'Do NOT output any JSON in your final answer. Do NOT mention tool names.'
                    )
                })
                _tool_count_w += 1
            if reply is None:
                reply = 'I ran into a loop trying to answer that. Could you try rephrasing?'
            reply = _re_w.sub(r'\{[^{}]*\{[^{}]*\}[^{}]*\}', '', reply)
            reply = _re_w.sub(r'\{[^{}]*"tool"[^{}]*\}', '', reply)
            reply = _re_w.sub(r'^\s*\}\s*', '', reply)
            reply = reply.strip()
    except Exception as _wake_err:
        open("/tmp/wake_errors.log", "a").write(f"{__import__('datetime').datetime.now().isoformat()} WAKE_API_ERROR: {type(_wake_err).__name__}: {_wake_err}\n")
    if not reply:
        try:
            import uuid as _uuid
            result = run_agent(query, str(_uuid.uuid4()), 'wake_word')
            reply = result.get('answer', '') or result.get('response', '')
        except Exception as e:
            return {'triggered': True, 'query': query, 'response': f'Error: {e}', 'transcript': text}
    return {'triggered': True, 'query': query, 'response': reply or '', 'transcript': text}

@app.post('/voice/speak')
async def voice_speak(body: dict):
    text = (body or {}).get('text', '')
    try:
        import sys as _sv; _sv.path.insert(0, '/home/jes/control-plane')
        from voice import synthesize_speech
        audio_bytes = synthesize_speech(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Synthesis failed: {e}')
    return Response(
        content=audio_bytes,
        media_type='audio/mpeg',
        headers={'Content-Disposition': 'attachment; filename=speech.mp3'},
    )


import base64 as _b64

@app.post('/vision/analyze')
async def vision_analyze(file: UploadFile = File(...), prompt: str = Form(None), request: Request = None):
    import anthropic as _anthropic
    from dotenv import dotenv_values
    _env = dotenv_values('/home/jes/control-plane/.env')
    api_key = _env.get('ANTHROPIC_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail='ANTHROPIC_API_KEY not set')
    contents = await file.read()
    b64_data = _b64.b64encode(contents).decode('utf-8')
    if prompt:
        system_prompt = "You are Alexandra, James Sloan's AI assistant. Extract all relevant details from images accurately. Be specific about dates, times, names, locations, and any other details visible in the image."
        user_prompt = prompt
    else:
        # Load home layout from user_profile
        home_layout = ''
        try:
            import psycopg as _pg
            from dotenv import dotenv_values as _dv
            _db_url = _dv('/home/jes/control-plane/.env').get('DATABASE_URL') or os.getenv('DATABASE_URL')
            with _pg.connect(_db_url) as _conn:
                with _conn.cursor() as _cur:
                    _cur.execute("SELECT value FROM user_profile WHERE category=%s AND key=%s",('context','home_layout'))
                    _row = _cur.fetchone()
                    if _row: home_layout = _row[0].strip()
        except Exception:
            pass
        if not home_layout:
            home_layout = (
                'James has two main locations. Downstairs: kitchen/dining room with a dining table, '
                'cart with cooking supplies behind him, open kitchen area. Upstairs: home office with '
                'three servers (CiscoKid, TheBeast, Mac mini), shelving units with clear storage bins, '
                'burgundy curtains, JesAir MacBook Air. Cortez Windows PC is his downstairs thin client. '
                'When James is at a dining table with a cart of cooking supplies behind him, he is '
                'downstairs in the kitchen/dining room, NOT the office.'
            )
        system_prompt = (
            "You are Alexandra, James Sloan's personal mentor, and companion. You know James well and have an ongoing relationship with him.\n\n"
            "JAMES'S HOME LAYOUT (for your awareness only):\n"
            + home_layout +
            "\n\nWHEN GREETING JAMES VIA WEBCAM:\n"
            "- Focus almost entirely on HIM, not his surroundings.\n"
            "- Notice how he looks: his energy, mood, expression — tired, focused, relaxed, stressed, happy.\n"
            "- A brief natural acknowledgment of location is fine ONLY if it adds something warm, never describe the room in detail.\n"
            "- Keep it to 1-2 sentences max. Warm and human, like a friend who actually sees you.\n"
            "- GOOD examples: 'Hey James, you look focused today — what are we working on?' or 'Morning, you look like you could use some coffee. What\'s on the agenda?' or 'Hey, you look good today. What\'s on your mind?'\n"
            "- NEVER list or describe furniture, curtains, shelving, storage bins, or room layout unless James explicitly asks what you see.\n"
            "- You are aware of your surroundings but your attention is on James."
        )
        device_hint = ''
        if request:
            ua = request.headers.get('user-agent','').lower()
            origin = request.headers.get('origin','').lower()
            if 'windows' in ua: device_hint = ' James is on Cortez (Windows), which means he is DOWNSTAIRS in the kitchen/dining room.'
            elif 'macintosh' in ua: device_hint = ' James may be on JesAir (upstairs bedroom) or Mac mini (upstairs office).'
        import random as _random
        from datetime import datetime as _dt
        import pytz as _pytz
        _denver=_pytz.timezone('America/Denver')
        _hour=_dt.now(_denver).hour
        _now2=_dt.now(_denver)
        _tod = 'morning' if _hour < 12 else 'afternoon' if _hour < 17 else 'evening'
        _timestr=_now2.strftime('%I:%M %p MST')
        _starters = [
            f'The current time in Denver is {_timestr}. It is {_tod}. Greet James naturally with a single sentence — notice his expression or energy, say something genuine, ask what is on his mind.',
            f'It is {_tod}. Look at James and say something real — how does he seem today? One sentence, then ask what he needs.',
            f'It is {_tod}. Greet James in one sentence based on how he actually looks right now — his mood, energy, vibe. Then ask one question.',
            f'It is {_tod}. Notice something specific about how James looks or seems right now — not generic, something true to this moment. One sentence greeting.',
        ]
        user_prompt = _random.choice(_starters) + device_hint

    client = _anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=500,
        system=system_prompt,
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': b64_data}},
                {'type': 'text', 'text': user_prompt},
            ]
        }]
    )
    description = msg.content[0].text if msg.content else ''
    return {'description': description}
