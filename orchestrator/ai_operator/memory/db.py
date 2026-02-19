import os
import uuid
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


def get_db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


def _jsonb(value: Optional[Dict[str, Any]]) -> Optional[Jsonb]:
    if value is None:
        return None
    return Jsonb(json.dumps(value, default=str))


def _vector_literal(vec: List[float]) -> str:
    return "[" + ",".join(f"{float(x):.8f}" for x in vec) + "]"


def insert_memory(
    source: str,
    content: str,
    embedding: Optional[List[float]] = None,
    embedding_model: Optional[str] = None,
    tool: Optional[str] = None,
    tool_result: Optional[Dict[str, Any]] = None,
) -> str:
    mem_id = str(uuid.uuid4())
    db_url = get_db_url()

    embedding_param = _vector_literal(embedding) if embedding is not None else None

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            if embedding_param is None:
                cur.execute(
                    """
                    INSERT INTO memory
                    (id, source, content, embedding, embedding_model, tool, tool_result, created_at)
                    VALUES (%s, %s, %s, NULL, %s, %s, %s, %s)
                    """,
                    (
                        mem_id,
                        source,
                        content,
                        embedding_model,
                        tool,
                        _jsonb(tool_result),
                        datetime.now(timezone.utc),
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO memory
                    (id, source, content, embedding, embedding_model, tool, tool_result, created_at)
                    VALUES (%s, %s, %s, %s::vector, %s, %s, %s, %s)
                    """,
                    (
                        mem_id,
                        source,
                        content,
                        embedding_param,
                        embedding_model,
                        tool,
                        _jsonb(tool_result),
                        datetime.now(timezone.utc),
                    ),
                )
        conn.commit()

    return mem_id


def search_memories(
    query_embedding: List[float],
    *,
    top_k: int = 5,
    min_similarity: float = 0.2,
    include_tools: bool = False,
) -> List[Dict[str, Any]]:
    db_url = get_db_url()
    tool_clause = "" if include_tools else "AND (tool IS NULL OR tool = '')"
    qvec = _vector_literal(query_embedding)

    sql = f"""
    SELECT
        id,
        source,
        content,
        created_at,
        embedding_model,
        tool,
        tool_result,
        1 - (embedding <=> %s::vector) AS cosine_sim
    FROM memory
    WHERE embedding IS NOT NULL
      {tool_clause}
      AND (1 - (embedding <=> %s::vector)) >= %s
    ORDER BY embedding <=> %s::vector
    LIMIT %s;
    """

    with psycopg.connect(db_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (qvec, qvec, float(min_similarity), qvec, int(top_k)))
            return cur.fetchall()


def get_latest_phrase(*, include_tools: bool = False) -> Optional[str]:
    """
    Deterministic recall: grab the most recent stored PHRASE: ... row.
    """
    db_url = get_db_url()
    tool_clause = "" if include_tools else "AND (tool IS NULL OR tool = '')"

    sql = f"""
    SELECT content
    FROM memory
    WHERE content ILIKE 'PHRASE:%'
      {tool_clause}
    ORDER BY created_at DESC
    LIMIT 1;
    """

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()
            if not row:
                return None
            content = (row[0] or "").strip()
            return content.split(":", 1)[1].strip() if ":" in content else None

def db_ping() -> None:
    """
    Minimal connectivity check for readiness probes.
    """
    db_url = get_db_url()
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
