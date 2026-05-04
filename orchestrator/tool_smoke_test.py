#!/usr/bin/env python3
"""
Alexandra tool registry smoke test.

Runs every registered tool handler with safe, non-destructive inputs, classifies
the result as PASS / FAIL / EXCEPTION / SCHEMA_ISSUE / SKIP, writes a JSON summary,
records a pgvector memory row, and fires a Telegram alert on any failure.

Origin: Day 64 — post-mortem action item after memory_save + memory_recall
drift (wrong embed model, wrong table) went undetected for unknown duration.

Day 80 amendments:
  - SKIP status added for tools intentionally disabled by env-var gate
    (handler returns {ok: False, disabled: True}); not a FAIL.
  - read_file test target swapped from SESSION.md (now >50KB, exceeds cap)
    to paco_session_anchor.md (canonical, ~15KB, stable).
"""
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

# --- Step 1: load .env BEFORE importing anything env-dependent ---
ORCH_DIR = Path("/home/jes/control-plane/orchestrator")
ENV_PATH = ORCH_DIR / ".env"

try:
    from dotenv import dotenv_values
except ImportError:
    sys.stderr.write("python-dotenv not installed in venv\n")
    sys.exit(2)

_env = dotenv_values(str(ENV_PATH))
for k, v in _env.items():
    if v is not None and k not in os.environ:
        os.environ[k] = v

# --- Step 2: import registry AFTER env is in place ---
sys.path.insert(0, str(ORCH_DIR))
from ai_operator.tools.registry import default_registry  # noqa: E402

TIMESTAMP = int(time.time())
ISO_NOW = datetime.now(timezone.utc).isoformat()

RESULTS_PATH = Path("/home/jes/control-plane/tool_smoke_test_results.json")

# Non-destructive test matrix. Any tool NOT listed here is skipped.
# Destructive tools (send_email, send_telegram, home_control,
# create_calendar_event, write_file) are intentionally excluded.
SAFE_TESTS = {
    "ping": {},
    "memory_save": {"content": "smoke test", "source": f"smoke_test_{TIMESTAMP}"},
    "memory_recall": {"query": "smoke test"},
    "read_file": {"path": "paco_session_anchor.md"},
    "list_files": {},
    "web_search": {"query": "test"},
    "web_fetch": {"url": "https://httpbin.org/html"},
    "get_emails": {"limit": 1},
    "get_calendar": {},
    "get_upcoming_calendar": {"days": 1},
    "summarize": {"text": "Smoke test content."},
    "home_status": {"domain": "light"},
    "get_system_status": {},
    "get_live_context": {},
    "get_linkedin_profile": {"section": "experience"},
    "research_topic": {"topic": "test"},
}


def classify(result):
    """Return (status, detail) from a handler result."""
    if isinstance(result, dict):
        if result.get("ok") is True:
            return "PASS", None
        # Tool intentionally disabled by env-var gate (e.g. memory_save
        # defense-in-depth). Not a FAIL: the gate IS the feature. Banked
        # Day 80 after nightly false-FAIL noise on memory_save.
        if result.get("disabled") is True:
            return "SKIP", str(result.get("error", "tool disabled by config"))
        if result.get("ok") is False:
            return "FAIL", str(result.get("error", "ok:False without error message"))
        # dict with no explicit ok field
        if result:
            return "PASS", None
        return "FAIL", "empty dict"
    if isinstance(result, list):
        return ("PASS", None) if len(result) > 0 else ("FAIL", "empty list")
    if isinstance(result, str):
        return ("PASS", None) if result.strip() else ("FAIL", "empty string")
    if result is None:
        return "SCHEMA_ISSUE", "handler returned None (no standardized envelope)"
    return "PASS", None


def run_one(registry, name, args):
    entry = {"tool": name, "args": args, "status": None, "detail": None,
             "duration_ms": None, "raw_result_preview": None}
    t0 = time.time()
    try:
        result = registry.run(name, args)
        status, detail = classify(result)
        entry["status"] = status
        entry["detail"] = detail
        # keep a short preview so the JSON stays readable
        preview = repr(result)
        entry["raw_result_preview"] = preview[:300]
    except Exception as e:
        entry["status"] = "EXCEPTION"
        entry["detail"] = f"{type(e).__name__}: {e}"
        entry["raw_result_preview"] = traceback.format_exc()[-500:]
    entry["duration_ms"] = int((time.time() - t0) * 1000)
    return entry


def write_memory_row(summary_text):
    """Write summary to pgvector memory table (matches _store_memory_async pattern)."""
    import requests
    import psycopg
    try:
        db_pass = os.getenv("CONTROLPLANE_DB_PASS", "adminpass")
        db_url = f"postgresql://admin:{db_pass}@192.168.1.10:5432/controlplane"
        embed_model = "mxbai-embed-large"
        r = requests.post(
            "http://192.168.1.152:11434/api/embeddings",
            json={"model": embed_model, "prompt": summary_text[:500]},
            timeout=30,
        )
        r.raise_for_status()
        embedding = r.json().get("embedding")
        if not embedding:
            return {"ok": False, "error": "no embedding returned"}
        vec_str = "[" + ",".join(f"{float(v):.8f}" for v in embedding) + "]"
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO memory (id, source, content, embedding, embedding_model, created_at)
                       VALUES (gen_random_uuid(), %s, %s, %s::vector, %s, NOW())""",
                    ("tool_smoke_test", summary_text[:500], vec_str, f"{embed_model}:latest"),
                )
            conn.commit()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def alert_telegram(registry, failures):
    """Fire Telegram alert with failing tool list. Uses send_telegram handler."""
    lines = ["Alexandra tool smoke test: FAILURES"]
    for e in failures:
        tool = e["tool"]
        status = e["status"]
        detail = (e.get("detail") or "").replace("\n", " ")[:200]
        lines.append(f"  [{status}] {tool}: {detail}")
    msg = "\n".join(lines)[:3800]
    try:
        return registry.run("send_telegram", {"message": msg})
    except Exception as e:
        return {"ok": False, "error": f"telegram alert failed: {e}"}


def main():
    registry = default_registry()
    entries = []
    for name, args in SAFE_TESTS.items():
        print(f"[smoke] running {name} ...", flush=True)
        entry = run_one(registry, name, args)
        print(f"[smoke] {name}: {entry['status']} ({entry['duration_ms']} ms)", flush=True)
        entries.append(entry)

    counts = {"PASS": 0, "FAIL": 0, "EXCEPTION": 0, "SCHEMA_ISSUE": 0, "SKIP": 0}
    for e in entries:
        counts[e["status"]] = counts.get(e["status"], 0) + 1

    failures = [e for e in entries if e["status"] in ("FAIL", "EXCEPTION")]

    summary = {
        "timestamp_utc": ISO_NOW,
        "timestamp_unix": TIMESTAMP,
        "total": len(entries),
        "counts": counts,
        "failures": [e["tool"] for e in failures],
        "schema_issues": [e["tool"] for e in entries if e["status"] == "SCHEMA_ISSUE"],
        "skipped": [e["tool"] for e in entries if e["status"] == "SKIP"],
        "entries": entries,
    }

    RESULTS_PATH.write_text(json.dumps(summary, indent=2, default=str))
    print(f"[smoke] results written to {RESULTS_PATH}", flush=True)

    summary_text = (
        f"tool_smoke_test {ISO_NOW}: "
        f"{counts['PASS']} PASS / {counts['FAIL']} FAIL / "
        f"{counts['EXCEPTION']} EXCEPTION / {counts['SCHEMA_ISSUE']} SCHEMA_ISSUE / "
        f"{counts['SKIP']} SKIP"
    )
    if failures:
        summary_text += " | broken: " + ",".join(e["tool"] for e in failures)

    mem = write_memory_row(summary_text)
    print(f"[smoke] memory row: {mem}", flush=True)

    if failures:
        alert = alert_telegram(registry, failures)
        print(f"[smoke] telegram alert: {alert}", flush=True)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
