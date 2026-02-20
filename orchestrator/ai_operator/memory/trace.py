import json
from typing import List, Dict, Any

import psycopg
from psycopg.rows import dict_row

from ai_operator.memory.db import get_db_url


def get_trace(run_id: str) -> List[Dict[str, Any]]:
    """
    Return all EVENT rows for a given run_id ordered chronologically.

    NOTE: psycopg uses % placeholders. We must escape the literal % in LIKE 'EVENT:%'
    as 'EVENT:%%' to avoid placeholder parsing errors.
    """
    db_url = get_db_url()

    sql = """
    SELECT created_at,
           (substring(content from 7)::json->>'type') AS tool,
           substring(content from 7) AS event_json
    FROM memory
    WHERE content LIKE 'EVENT:%%'
      AND (substring(content from 7)::json->>'run_id') = %s
    ORDER BY created_at ASC;
    """

    with psycopg.connect(db_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (run_id,))
            rows = cur.fetchall()

    # Parse JSON payload into a proper dict
    out: List[Dict[str, Any]] = []
    for r in rows:
        raw = r.get("event_json") or "{}"
        try:
            ev = json.loads(raw)
        except Exception:
            ev = {}
        out.append(
            {
                "created_at": r.get("created_at"),
                "tool": r.get("tool"),
                "event": ev,
            }
        )

    return out
