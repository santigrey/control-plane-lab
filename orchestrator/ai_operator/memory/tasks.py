from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import psycopg
from psycopg.rows import dict_row

from ai_operator.memory.db import get_db_url


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def claim_task(worker_id: str, lock_s: int = 60) -> Optional[Dict[str, Any]]:
    """
    Atomically claim one queued task whose available_at <= now, by priority then created_at.
    Sets status=running, locked_by/locked_at/lock_expires_at, increments attempts.
    Returns the claimed row (dict) or None.
    """
    db_url = get_db_url()
    now = utcnow()
    lock_expires = now + timedelta(seconds=int(lock_s))

    sql = """
    WITH candidate AS (
      SELECT id
      FROM tasks
      WHERE status = 'queued'
        AND available_at <= %(now)s
      ORDER BY priority ASC, created_at ASC
      FOR UPDATE SKIP LOCKED
      LIMIT 1
    )
    UPDATE tasks t
    SET status = 'running',
        locked_by = %(worker_id)s,
        locked_at = %(now)s,
        lock_expires_at = %(lock_expires)s,
        attempts = attempts + 1
    FROM candidate c
    WHERE t.id = c.id
    RETURNING t.*;
    """

    with psycopg.connect(db_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                {"now": now, "lock_expires": lock_expires, "worker_id": worker_id},
            )
            row = cur.fetchone()
            conn.commit()
            return row


def complete_task_success(task_id: str, result: Dict[str, Any]) -> None:
    """
    Store result as jsonb. psycopg3 won't always adapt dict->json automatically,
    so we explicitly json.dumps + ::jsonb.
    """
    db_url = get_db_url()
    payload_json = json.dumps(result, ensure_ascii=False)

    sql = """
    UPDATE tasks
    SET status='succeeded',
        result=%(result)s::jsonb,
        last_error=NULL,
        locked_by=NULL,
        locked_at=NULL,
        lock_expires_at=NULL,
        updated_at=now()
    WHERE id=%(id)s::uuid;
    """
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {"id": task_id, "result": payload_json})
            conn.commit()


def complete_task_failure(task_id: str, error: str, retry_backoff_s: int = 1) -> None:
    """
    If attempts >= max_attempts => mark failed.
    Else re-queue with available_at = now + backoff, keep last_error, clear locks, status=queued.
    """
    db_url = get_db_url()
    now = utcnow()
    next_time = now + timedelta(seconds=int(max(0, retry_backoff_s)))

    sql = """
    UPDATE tasks
    SET
      status = CASE
        WHEN attempts >= max_attempts THEN 'failed'
        ELSE 'queued'
      END,
      last_error = %(err)s,
      available_at = CASE
        WHEN attempts >= max_attempts THEN available_at
        ELSE %(next_time)s
      END,
      locked_by=NULL,
      locked_at=NULL,
      lock_expires_at=NULL,
      updated_at=now()
    WHERE id=%(id)s::uuid
    RETURNING id, status, attempts, max_attempts;
    """

    with psycopg.connect(db_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {"id": task_id, "err": error, "next_time": next_time})
            _ = cur.fetchone()
            conn.commit()
