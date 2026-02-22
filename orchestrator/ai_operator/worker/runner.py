#!/usr/bin/env python3

import json
import logging
import os
import socket
import time
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import psycopg

from ai_operator.memory.db import get_db_url
from ai_operator.memory.tasks import (
    claim_task,
    complete_task_failure,
    complete_task_success,
)
from ai_operator.memory.writer import write_memory_event
from ai_operator.repo.patch_apply import run_patch_apply_task
from ai_operator.worker.artifacts import run_doc_build_task, run_repo_change_task
from ai_operator.tools.registry import run_tool_call


LOG = logging.getLogger("aiop.worker")
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_result(obj: Any) -> Dict[str, Any]:
    """
    Normalize a task handler return value into a dict so runner can safely merge it.
    Supports:
      - dict
      - dataclass instances
      - pydantic v1 (.dict) / v2 (.model_dump)
      - objects with __dict__
      - scalar/other values (wrapped)
    """
    if obj is None:
        return {}

    if isinstance(obj, dict):
        return obj

    if is_dataclass(obj):
        try:
            return asdict(obj)
        except Exception:
            return {"value": repr(obj)}

    # pydantic v2
    if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump")):
        try:
            return obj.model_dump()
        except Exception:
            return {"value": repr(obj)}

    # pydantic v1
    if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
        try:
            return obj.dict()
        except Exception:
            return {"value": repr(obj)}

    # plain object
    if hasattr(obj, "__dict__"):
        try:
            return dict(obj.__dict__)
        except Exception:
            return {"value": repr(obj)}

    # fallback
    return {"value": obj}


def _dispatch_task(task_type: str, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns a dict-like payload to merge into the task result.
    """
    if task_type == "tool.call":
        return run_tool_call(task_id=task_id, payload=payload)

    if task_type == "repo.change":
        return run_repo_change_task(task_id=task_id, payload=payload)

    if task_type == "doc.build":
        return run_doc_build_task(task_id=task_id, payload=payload)

    if task_type == "patch.apply":
        # NOTE: may return ApplyResult (dataclass/class) -> normalize later
        return run_patch_apply_task(task_id=task_id, payload=payload)  # type: ignore[return-value]

    raise ValueError(f"unknown task type: {task_type}")


def main() -> None:
    db_url = get_db_url()

    hostname = socket.gethostname()
    pid = os.getpid()
    worker_id = f"{hostname}:{pid}"

    poll_s = int(os.environ.get("AIOP_POLL_S", "1"))
    lock_s = int(os.environ.get("AIOP_LOCK_S", "60"))

    LOG.info("starting wid=%s poll_s=%s lock_s=%s", worker_id, poll_s, lock_s)

    with psycopg.connect(db_url) as conn:
        conn.autocommit = True

        while True:
            task = claim_task(worker_id=worker_id, lock_s=lock_s)

            if not task:
                time.sleep(poll_s)
                continue

            task_id = str(task["id"])
            task_type = str(task["type"])
            attempts = int(task.get("attempts") or 0)
            max_attempts = int(task.get("max_attempts") or 3)

            payload_raw = task.get("payload") or {}
            payload: Dict[str, Any] = payload_raw if isinstance(payload_raw, dict) else json.loads(payload_raw)

            LOG.info("claimed id=%s type=%s attempts=%s/%s", task_id, task_type, attempts, max_attempts)

            write_memory_event(
                conn,
                source="worker",
                tool="",
                content=json.dumps(
                    {
                        "type": "task.claimed",
                        "ts": _utc_now_iso(),
                        "task_id": task_id,
                        "task_type": task_type,
                        "worker_id": worker_id,
                        "attempts": attempts,
                        "max_attempts": max_attempts,
                        "run_id": None,
                    }
                ),
            )

            start = time.time()
            try:
                # emit task start event
                write_memory_event(
                    conn,
                    source="worker",
                    tool="",
                    content=json.dumps(
                        {
                            "type": task_type,
                            "ts": _utc_now_iso(),
                            "task_id": task_id,
                            "run_id": None,
                            "data": payload,
                        }
                    ),
                )

                raw_result = _dispatch_task(task_type=task_type, task_id=task_id, payload=payload)
                took_ms = int((time.time() - start) * 1000)

                result_payload = _normalize_result(raw_result)

                complete_task_success(
                    task_id=task_id,
                    result={
                        "ok": True,
                        "kind": task_type,
                        "took_ms": took_ms,
                        **result_payload,
                    },
                )

                write_memory_event(
                    conn,
                    source="worker",
                    tool="",
                    content=json.dumps(
                        {
                            "type": f"{task_type}.result",
                            "ts": _utc_now_iso(),
                            "task_id": task_id,
                            "run_id": None,
                            "data": {
                                "ok": True,
                                "took_ms": took_ms,
                                "result": {
                                    "ok": True,
                                    "kind": task_type,
                                    "took_ms": took_ms,
                                    **result_payload,
                                },
                            },
                        }
                    ),
                )

                LOG.info("succeeded id=%s kind=%s took_ms=%s", task_id, task_type, took_ms)

            except Exception as e:
                took_ms = int((time.time() - start) * 1000)
                err = f"{type(e).__name__}: {e}"
                terminal = attempts >= max_attempts

                complete_task_failure(task_id=task_id, error=err)

                write_memory_event(
                    conn,
                    source="worker",
                    tool="",
                    content=json.dumps(
                        {
                            "type": "task.failed" if not terminal else "task.permanently_failed",
                            "ts": _utc_now_iso(),
                            "task_id": task_id,
                            "run_id": None,
                            "error": err,
                            "took_ms": took_ms,
                            "attempts": attempts,
                            "max_attempts": max_attempts,
                        }
                    ),
                )

                LOG.error("failed id=%s err=%s terminal=%s", task_id, err, terminal)


if __name__ == "__main__":
    main()
