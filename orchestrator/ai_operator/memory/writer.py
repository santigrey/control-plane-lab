from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from ai_operator.memory.db import insert_memory
from ai_operator.memory.events import event_to_content, event_to_tool_result


def write_event(
    *,
    event: Dict[str, Any],
    tool: Optional[str] = None,
    embedding: Optional[List[float]] = None,
    embedding_model: Optional[str] = None,
) -> str:
    """
    Single canonical path for persisting a normalized event into the memory table.

    - Stores human-readable JSON envelope in `content` as: EVENT:{...}
    - Stores structured JSONB envelope in `tool_result`
    - Optional: stores embedding + embedding_model (for retrieval)
    """
    return insert_memory(
        source=event.get("source", "orchestrator"),
        content=event_to_content(event),
        embedding=embedding,
        embedding_model=embedding_model,
        tool=tool or event.get("type"),
        tool_result=event_to_tool_result(event),
    )


def write_memory_event(
    _conn: Any,
    *,
    source: str,
    tool: Optional[str],
    content: str,
) -> str:
    """
    Backward-compatible wrapper used by worker runner.
    Accepts JSON string content and stores it through the canonical writer path.
    """
    try:
        event = json.loads(content)
        if not isinstance(event, dict):
            event = {"type": "raw.event", "content": content}
    except Exception:
        event = {"type": "raw.event", "content": content}

    event.setdefault("source", source)
    return write_event(event=event, tool=tool)
