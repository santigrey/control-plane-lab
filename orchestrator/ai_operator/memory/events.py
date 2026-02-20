from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class MemoryEvent:
    """
    Canonical event envelope for anything we persist.

    type: event category (prompt, retrieval, tool_call, tool_result, response, etc.)
    source: component name (orchestrator, tool:<name>, etc.)
    ts: ISO-8601 UTC timestamp
    data: structured payload (JSON-serializable)
    """
    type: str
    source: str
    data: Dict[str, Any]
    ts: str


def make_event(
    *,
    type: str,
    source: str,
    data: Dict[str, Any],
    ts: Optional[str] = None,
) -> MemoryEvent:
    if not type or not isinstance(type, str):
        raise ValueError("type must be a non-empty string")
    if not source or not isinstance(source, str):
        raise ValueError("source must be a non-empty string")
    if data is None or not isinstance(data, dict):
        raise ValueError("data must be a dict")
    return MemoryEvent(type=type, source=source, data=data, ts=ts or utc_now_iso())


def event_to_content(e: MemoryEvent) -> str:
    """
    Human-readable content string (still useful for quick grep/debug).
    Keep this short and stable.
    """
    # Compact JSON for readability
    payload = json.dumps(
        {"type": e.type, "source": e.source, "ts": e.ts, "data": e.data},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"EVENT:{payload}"


def event_to_tool_result(e: MemoryEvent) -> Dict[str, Any]:
    """
    Structured payload to store in tool_result JSONB.
    This becomes our durable contract.
    """
    return {"type": e.type, "source": e.source, "ts": e.ts, "data": e.data}
