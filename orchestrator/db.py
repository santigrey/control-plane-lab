import os
import uuid
from datetime import datetime, timezone

import psycopg


def get_db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


def insert_memory(source: str, content: str) -> str:
    """
    Inserts a memory row without an embedding (we'll add embeddings next).
    Returns the UUID (as a string).
    """
    mem_id = str(uuid.uuid4())
    db_url = get_db_url()

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO memory (id, source, content, embedding, created_at)
                VALUES (%s, %s, %s, NULL, %s)
                """,
                (mem_id, source, content, datetime.now(timezone.utc)),
            )
        conn.commit()

    return mem_id
