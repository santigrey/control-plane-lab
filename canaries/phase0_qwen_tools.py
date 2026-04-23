#!/usr/bin/env python3
"""
Phase 0 canary — Qwen2.5:72B tool-call emission via Ollama /api/chat.
Standalone. Does not touch production /chat handler or TOOLS registry.
Tests whether Qwen can reliably emit Ollama-native tool_calls for 5 representative prompts.

Ref: unified_alexandra_spec_v1.md §8 Phase 2 + Paco amendment 2026-04-22.
"""
import json
import time
import requests
from pathlib import Path
from datetime import datetime

OLLAMA_URL = "http://192.168.1.20:11434/api/chat"
MODEL = "qwen2.5:72b"
TIMEOUT = 120
OUT_DIR = Path("/home/jes/control-plane/canaries")
OUT_DIR.mkdir(exist_ok=True)

# --- Tool schema (representative subset of prod) ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_emails",
            "description": "Retrieve recent emails from the user's inbox.",
            "parameters": {
                "type": "object",
                "properties": {
                    "unread": {"type": "boolean", "description": "If true, only unread emails."},
                    "limit": {"type": "integer", "description": "Max number of emails to return."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "research_topic",
            "description": "Search the web for information on a given topic and return a summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch the contents of a specific URL and return them as text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to fetch."}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_job_pipeline",
            "description": "Return the user's tracked job application pipeline.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a given location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City, state, or coordinates."}
                },
                "required": ["location"]
            }
        }
    }
]

# --- Canary prompts ---
PROMPTS = [
    {
        "id": 1,
        "kind": "single_tool_clear",
        "prompt": "What are my three most recent unread emails?",
        "expected_tool": "get_emails",
    },
    {
        "id": 2,
        "kind": "single_tool_free_text",
        "prompt": "Search the web for recent news on ASUS Ascent GX10 availability.",
        "expected_tool": "research_topic",
    },
    {
        "id": 3,
        "kind": "single_tool_structured_arg",
        "prompt": "Fetch https://docs.anthropic.com/en/home and summarize.",
        "expected_tool": "web_fetch",
    },
    {
        "id": 4,
        "kind": "single_tool_no_args",
        "prompt": "Show me my current job application pipeline.",
        "expected_tool": "get_job_pipeline",
    },
    {
        "id": 5,
        "kind": "multi_step_loop",
        "prompt": "Check my recent emails for job alerts, then research the top company mentioned.",
        "expected_first_tool": "get_emails",
        "expected_second_tool": "research_topic",
    }
]

# --- Mocked tool response for multi-step test ---
MOCKED_EMAILS_RESPONSE = json.dumps({
    "emails": [
        {"from": "alerts@jobright.ai", "subject": "5 new ML Engineer roles at Anthropic", "unread": True},
        {"from": "noreply@linkedin.com", "subject": "Job alert: Applied AI Engineer at OpenAI", "unread": True},
        {"from": "recruiting@scale.com", "subject": "Follow up on Scale AI application", "unread": False},
    ]
})


def call_ollama(messages, tools=None):
    """Single call to Ollama /api/chat; returns (response_dict, elapsed_seconds)."""
    payload = {"model": MODEL, "messages": messages, "stream": False}
    if tools:
        payload["tools"] = tools
    t0 = time.time()
    r = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
    elapsed = time.time() - t0
    r.raise_for_status()
    return r.json(), elapsed


def extract_tool_calls(response):
    msg = response.get("message", {}) or {}
    return msg.get("tool_calls", []) or []


def assess_single(prompt_spec, tool_calls, content, elapsed):
    result = {
        "id": prompt_spec["id"],
        "kind": prompt_spec["kind"],
        "prompt": prompt_spec["prompt"],
        "latency_s": round(elapsed, 2),
        "tool_calls_emitted": len(tool_calls),
        "tool_calls_raw": tool_calls,
        "content_when_no_tool": content if not tool_calls else None,
    }
    expected = prompt_spec["expected_tool"]
    if tool_calls and tool_calls[0].get("function", {}).get("name") == expected:
        result["pass"] = True
        result["failure_reason"] = None
    elif tool_calls:
        result["pass"] = False
        result["failure_reason"] = f"wrong tool: got {tool_calls[0].get('function', {}).get('name')}, expected {expected}"
    else:
        result["pass"] = False
        result["failure_reason"] = "no tool_calls emitted"
    return result


def run_multi_step(prompt_spec):
    messages = [{"role": "user", "content": prompt_spec["prompt"]}]
    r1, e1 = call_ollama(messages, tools=TOOLS)
    tc1 = extract_tool_calls(r1)
    step1_ok = bool(tc1 and tc1[0].get("function", {}).get("name") == prompt_spec["expected_first_tool"])

    step2_ok = False
    tc2 = []
    e2 = 0
    content2 = None
    if step1_ok:
        messages.append(r1.get("message", {}))
        messages.append({"role": "tool", "content": MOCKED_EMAILS_RESPONSE, "name": "get_emails"})
        r2, e2 = call_ollama(messages, tools=TOOLS)
        tc2 = extract_tool_calls(r2)
        content2 = (r2.get("message") or {}).get("content")
        step2_ok = bool(tc2 and tc2[0].get("function", {}).get("name") == prompt_spec["expected_second_tool"])

    return {
        "id": prompt_spec["id"],
        "kind": prompt_spec["kind"],
        "prompt": prompt_spec["prompt"],
        "step1_tool_calls": tc1,
        "step1_latency_s": round(e1, 2),
        "step1_ok": step1_ok,
        "step2_tool_calls": tc2,
        "step2_latency_s": round(e2, 2),
        "step2_ok": step2_ok,
        "step2_content": content2,
        "pass": step1_ok and step2_ok,
        "failure_reason": None if (step1_ok and step2_ok) else f"step1_ok={step1_ok} step2_ok={step2_ok}",
    }


def main():
    print(f"[phase0] Canary start {datetime.now().isoformat()}")
    print(f"[phase0] Model: {MODEL}  Endpoint: {OLLAMA_URL}")

    results = []
    latencies = []

    for p in PROMPTS:
        print(f"\n[phase0] Prompt #{p['id']} ({p['kind']}): {p['prompt'][:70]}...")
        try:
            if p["kind"] == "multi_step_loop":
                res = run_multi_step(p)
                latencies.append(res["step1_latency_s"])
                if res["step2_latency_s"]:
                    latencies.append(res["step2_latency_s"])
            else:
                r, elapsed = call_ollama([{"role": "user", "content": p["prompt"]}], tools=TOOLS)
                tc = extract_tool_calls(r)
                content = (r.get("message") or {}).get("content")
                res = assess_single(p, tc, content, elapsed)
                latencies.append(elapsed)
        except Exception as e:
            res = {"id": p["id"], "kind": p["kind"], "prompt": p["prompt"], "pass": False, "failure_reason": f"exception: {e}"}

        results.append(res)
        lat = res.get("latency_s") or res.get("step1_latency_s") or "N/A"
        print(f"  -> pass={res.get('pass')}  latency={lat}s  reason={res.get('failure_reason')}")

    passed = sum(1 for r in results if r.get("pass"))
    total = len(results)
    lat_sorted = sorted(latencies)
    p50 = lat_sorted[len(lat_sorted)//2] if lat_sorted else 0
    p90_idx = max(0, int(len(lat_sorted) * 0.9) - 1) if lat_sorted else 0
    p90 = lat_sorted[p90_idx] if lat_sorted else 0

    summary = {
        "timestamp": datetime.now().isoformat(),
        "model": MODEL,
        "endpoint": OLLAMA_URL,
        "passed": passed,
        "total": total,
        "pass_rate": f"{passed}/{total}",
        "p50_latency_s": round(p50, 2),
        "p90_latency_s": round(p90, 2),
        "results": results,
    }

    if passed == 5:
        summary["verdict"] = "PROCEED: Option A viable"
    elif passed == 4:
        summary["verdict"] = "PROCEED WITH CAUTION: one failure documented"
    elif passed == 3:
        summary["verdict"] = "FLAG TO PACO: recommend pivot to Option B or C"
    else:
        summary["verdict"] = "FAIL: Option A off the table"

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUT_DIR / f"phase0_results_{ts}.json"
    json_path.write_text(json.dumps(summary, indent=2, default=str))

    md_path = OUT_DIR / f"phase0_summary_{ts}.md"
    md = [
        "# Phase 0 Canary — Qwen2.5:72B Tool-Call Emission",
        "",
        f"- Timestamp: {summary['timestamp']}",
        f"- Model: `{MODEL}`",
        f"- Endpoint: `{OLLAMA_URL}`",
        f"- Pass rate: **{summary['pass_rate']}**",
        f"- p50 latency: {summary['p50_latency_s']}s",
        f"- p90 latency: {summary['p90_latency_s']}s",
        f"- **Verdict: {summary['verdict']}**",
        "",
        "## Per-prompt results",
        "",
    ]
    for r in results:
        md.append(f"### #{r['id']} ({r.get('kind')})")
        md.append(f"- Prompt: {r['prompt']}")
        md.append(f"- Pass: **{r.get('pass')}**")
        md.append(f"- Failure reason: {r.get('failure_reason')}")
        if r.get("tool_calls_raw") is not None:
            md.append(f"- Tool calls: `{json.dumps(r.get('tool_calls_raw'))}`")
        if r.get("content_when_no_tool"):
            md.append(f"- Content (no tool): `{r['content_when_no_tool'][:200]}...`")
        if r.get("step1_tool_calls") is not None:
            md.append(f"- Step 1 tool_calls: `{json.dumps(r.get('step1_tool_calls'))}`")
            md.append(f"- Step 2 tool_calls: `{json.dumps(r.get('step2_tool_calls'))}`")
            if r.get("step2_content"):
                md.append(f"- Step 2 content: `{r['step2_content'][:200]}...`")
        md.append("")
    md_path.write_text("\n".join(md))

    print(f"\n[phase0] DONE  verdict={summary['verdict']}")
    print(f"[phase0] JSON: {json_path}")
    print(f"[phase0] MD:   {md_path}")
    return summary


if __name__ == "__main__":
    main()
