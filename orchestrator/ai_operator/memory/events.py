from __future__ import annotations

import json
from typing import Any, Dict, Optional

import psycopg

from ai_operator.memory.db import get_db_url


def event_to_content(event: Dict[str, Any]) -> str:
    """
    Human-readable storage format for memory.content.
    Convention: prefix with 'EVENT:' then JSON.
    """
    return "EVENT:" + json.dumps(event, ensure_ascii=False)


def event_to_tool_result(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Structured storage format for memory.tool_result (JSONB).
    Keep it as the event envelope.
    """
    return event


def write_event(
    *,
    source: str,
    envelope: Dict[str, Any],
    tool: Optional[str] = None,
    tool_result: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Append a canonical event envelope into public.memory.

    We store:
      - source: e.g. "worker"
      - content: JSON string of envelope
      - tool: optional tool name
      - tool_result: optional JSONB payload (stored safely via json.dumps + ::jsonb)
    """
    db_url = get_db_url()

    content_json = json.dumps(envelope, ensure_ascii=False)

    tool_result_json: Optional[str] = None
    if tool_result is not None:
        tool_result_json = json.dumps(tool_result, ensure_ascii=False)

    sql = """
    INSERT INTO memory (id, source, content, tool, tool_result)
    VALUES (gen_random_uuid(), %(source)s, %(content)s, %(tool)s, %(tool_result)s::jsonb);
    """

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                {
                    "source": source,
                    "content": content_json,
                    "tool": tool,
                    "tool_result": tool_result_json,
                },
            )
            conn.commit()
