import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def make_event(
    *,
    type: str,
    source: str,
    data: Dict[str, Any],
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Normalized event envelope for durable structured persistence.

    run_id groups all events produced during a single /ask execution.
    """
    return {
        "id": str(uuid.uuid4()),
        "run_id": run_id,
        "type": type,
        "source": source,
        "ts": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }


def event_to_content(event: Dict[str, Any]) -> str:
    """
    Human-readable content column representation.
    """
    import json

    return "EVENT:" + json.dumps(
        event,
        separators=(",", ":"),
        sort_keys=True,
        default=str,
    )


def event_to_tool_result(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    JSONB-safe tool_result representation.
    """
    return {
        "id": event.get("id"),
        "run_id": event.get("run_id"),
        "type": event.get("type"),
        "source": event.get("source"),
        "ts": event.get("ts"),
        "data": event.get("data"),
    }