import json
import os
import uuid
from typing import Any, Dict, List

from ai_operator.inference.ollama import ollama_chat, ollama_embed
from ai_operator.memory.db import search_memories, get_db_url
import psycopg as _psycopg
from ai_operator.memory.events import make_event
from ai_operator.memory.writer import write_event
from ai_operator.tools.registry import default_registry
from pydantic import BaseModel

TOOLS = default_registry()
MAX_STEPS = int(os.getenv("AGENT_MAX_STEPS", "5"))

AGENT_SYSTEM_PROMPT = os.getenv("AGENT_SYSTEM_PROMPT", """
You are Alexandra, James Sloan's personal AI companion. You know James well — he is a senior infrastructure engineer in Denver, CO transitioning into AI engineering, building Project Ascension (a Jarvis-level AI platform and homelab), and targeting an AI Platform Engineer role by May 2026. You speak directly to James, not about him. You are direct, intelligent, and personal — never robotic or generic. When James asks if you remember him, you respond warmly and specifically about who he is and what you are building together.

To use a tool, output ONLY a single line of valid JSON. Nothing else. No explanation before or after:
{"tool": "job_search_jsearch", "args": {"what": "AI Engineer", "where": "Denver"}}
OR to research a company: {"tool": "research_topic", "args": {"topic": "True Anomaly company"}}

Available tools: job_search_jsearch, job_search, web_search, web_fetch, research_topic, draft_message, ping, get_emails, get_calendar

When searching for jobs ALWAYS use job_search_jsearch first — it searches LinkedIn, Indeed, and Glassdoor.
- "what" = job title only (e.g. "AI Engineer", "MLOps Engineer")
- "where" = location only (e.g. "Denver")
- "remote_only" = true for remote jobs, false for local
- NEVER put location in "what"

If job_search_jsearch returns results, produce your final answer immediately.
Do NOT call any other job search tool after job_search_jsearch succeeds.

You have direct tools to access James's Gmail (get_emails) and Google Calendar (get_calendar). Always use these tools when asked about emails or schedule — never use web_fetch on mail.google.com or calendar.google.com.

Rules:
- For any job or career task, always use job_search_jsearch first, then job_search as fallback — never web_search.
- For company research, background checks, or tech stack analysis, always use research_topic.
- To read a specific URL, use web_fetch.
- After receiving a tool result, either call another tool OR write your final answer in plain text.
- Your final answer must be plain text only — never JSON.
- Be direct. Be useful. Execute.
""".strip())


class AgentRequest(BaseModel):
    prompt: str
    session_id: str = ""


class AgentResponse(BaseModel):
    status: str
    answer: str
    steps: List[Dict[str, Any]]
    run_id: str
    session_id: str


def _parse_tool_call(text: str):
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
    return {"tool": tool.strip(), "args": args or {}}



def _load_user_profile() -> str:
    try:
        with _psycopg.connect(get_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT category, key, value FROM user_profile ORDER BY category, key")
                rows = cur.fetchall()
        if not rows:
            return ""
        parts = [f"{key}: {value}" for _, key, value in rows]
        return "User profile — " + " | ".join(parts)
    except Exception:
        return ""

def _get_api_key() -> str:
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if key:
        return key
    env_path = "/home/jes/control-plane/.env"
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("ANTHROPIC_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""


def claude_chat(
    system_prompt: str,
    user_prompt: str,
    injected_memories: str = "",
    history: list = None,
    model: str = "claude-haiku-4-5",
) -> str:
    api_key = _get_api_key()
    if not api_key:
        return ollama_chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            injected_memories=injected_memories,
            history=history,
        )

    user_text = user_prompt
    if injected_memories.strip():
        user_text = (
            f"{user_prompt}\n\n"
            "----\n"
            "RELEVANT MEMORY (use only if helpful and consistent):\n"
            f"{injected_memories}\n"
            "----"
        )

    messages = []
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )
        return (response.content[0].text or "").strip()
    except Exception:
        return ollama_chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            injected_memories=injected_memories,
            history=history,
        )



def store_conversation(prompt, answer):
    try:
        ms = f"User asked: {prompt}\nAlexandra answered: {answer}"
        emb = ollama_embed(ms[:1500])
        es = "[" + ",".join(str(x) for x in emb) + "]"
        with _psycopg.connect(get_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO memories (content, embedding) VALUES (%s, %s::vector)",
                    (ms, es),
                )
            conn.commit()
    except Exception:
        pass


def retrieve_relevant_memories(prompt, limit=5):
    try:
        emb = ollama_embed(prompt[:1500])
        es = "[" + ",".join(str(x) for x in emb) + "]"
        with _psycopg.connect(get_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT content FROM memories ORDER BY embedding <-> %s::vector LIMIT %s",
                    (es, limit),
                )
                rows = cur.fetchall()
        return [r[0] for r in rows if r[0]]
    except Exception:
        return []



def _load_user_profile() -> str:
    try:
        with _psycopg.connect(get_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT category, key, value FROM user_profile ORDER BY category, key")
                rows = cur.fetchall()
        if not rows:
            return ""
        parts = [f"{key}: {value}" for _, key, value in rows]
        return "User profile — " + " | ".join(parts)
    except Exception:
        return ""

def run_agent(prompt: str, run_id: str, session_id: str = "", conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    past_memories = retrieve_relevant_memories(prompt)
    profile_str = _load_user_profile()
    system_prompt = (profile_str + "\n\n" + AGENT_SYSTEM_PROMPT) if profile_str else AGENT_SYSTEM_PROMPT
    if past_memories:
        mp = "RELEVANT PAST CONVERSATIONS:\n"+"\n".join(past_memories)+"\n\n"
        system_prompt = mp+system_prompt
    _embed_query = prompt[:1500]  # mxbai-embed-large has 512-token context limit
    query_emb = ollama_embed(_embed_query)
    retrieved = search_memories(query_embedding=query_emb, top_k=5, min_similarity=0.6)
    memory_context = "\n\n".join(
        (m.get("content") or "").strip() for m in retrieved if m.get("content")
    )

    history: List[Dict[str, str]] = list(conversation_history) if conversation_history else []
    steps: List[Dict[str, Any]] = []
    final_answer = ""

    seen_calls = set()
    for step_n in range(MAX_STEPS):
        model_out = claude_chat(
            system_prompt=system_prompt,
            user_prompt=prompt,
            injected_memories=memory_context,
            history=history,
        )

        tool_call = _parse_tool_call(model_out)

        if not tool_call:
            final_answer = model_out
            write_event(event=make_event(
                type="agent_answer",
                source="agent",
                data={"prompt": prompt, "answer": final_answer, "total_steps": step_n},
                run_id=run_id,
            ))
            break

        tool_name = tool_call["tool"]
        tool_args = tool_call["args"]

        # Deduplication guard
        import hashlib as _hashlib
        _args_hash = _hashlib.md5(
            json.dumps(tool_args, sort_keys=True).encode()
        ).hexdigest()
        _call_key = f"{tool_name}:{_args_hash}"

        if _call_key in seen_calls:
            history.append({"role": "assistant", "content": model_out})
            history.append({"role": "user", "content": f"You already called {tool_name} with those exact arguments. Use the results you already have and produce your final answer now."})
            continue

        seen_calls.add(_call_key)

        try:
            result = TOOLS.run(tool_name, tool_args)
        except Exception as e:
            result = {"ok": False, "error": str(e), "tool": tool_name}

        step_record = {"step": step_n, "tool": tool_name, "args": tool_args, "result": result}
        steps.append(step_record)

        write_event(event=make_event(
            type="agent_step",
            source="agent",
            data=step_record,
            run_id=run_id,
        ))

        history.append({"role": "assistant", "content": model_out})
        history.append({
            "role": "user",
            "content": f"TOOL_RESULT for {tool_name}:\n{json.dumps(result, default=str)}"
        })

    import re as _re
    _has_tool_json = bool(_re.search(r'\{\s*"tool"\s*:', final_answer or ""))
    if not final_answer or _parse_tool_call(final_answer) is not None or _has_tool_json:
        step_summary = ", ".join(
            f"{s['tool']}({list(s['args'].values())[0] if s['args'] else ''})"
            for s in steps
        )
        final_answer = (
            f"Completed {len(steps)} research step(s): {step_summary}. "
            f"Step limit reached before a final answer was produced. "
            f"Try a more specific prompt."
        )

    store_conversation(prompt, final_answer)

    return {
        "status": "ok",
        "answer": final_answer,
        "steps": steps,
        "run_id": run_id,
        "session_id": session_id,
    }
