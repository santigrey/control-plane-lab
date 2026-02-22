from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ai_operator.tools.registry import default_registry
from ai_operator.memory.tasks import (
    claim_task,
    complete_task_success,
    complete_task_failure,
)
from ai_operator.memory.events import write_event

# New: handlers for non-tool task types
from ai_operator.worker.artifacts import run_repo_change_task, run_doc_build_task
from ai_operator.repo.patch_apply import run_patch_apply_task

LOG = logging.getLogger("aiop.worker")
TOOLS = default_registry()


def _setup_logging() -> None:
    # journald-friendly
    lvl = os.getenv("AIOP_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, lvl, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def env_int(name: str, default: str) -> int:
    v = os.getenv(name, default)
    return int(str(v).strip())


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def now_ms() -> int:
    return int(time.time() * 1000)


def compute_backoff_s(attempts: int) -> int:
    # 1s, 2s, 4s ... capped at 30s
    base = 2 ** max(0, attempts - 1)
    return int(min(30, base))


@dataclass
class WorkerConfig:
    poll_s: int = 1
    lock_s: int = 60


def _run_tool_call(task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    tool = payload.get("tool")
    args = payload.get("args") or {}

    if not isinstance(tool, str) or not tool.strip():
        raise ValueError("payload.tool must be a non-empty string")
    if not isinstance(args, dict):
        raise ValueError("payload.args must be an object")

    tool_name = tool.strip()
    result = TOOLS.run(tool_name, args)
    return {"ok": True, "tool": tool_name, "result": result}


def _dispatch_task(task_type: str, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    # NOTE: these names match what you're enqueueing into tasks.type
    if task_type == "tool.call":
        return _run_tool_call(task_id, payload)

    if task_type == "repo.change":
        return run_repo_change_task(task_id=task_id, payload=payload)

    if task_type == "doc.build":
        return run_doc_build_task(task_id=task_id, payload=payload)

    if task_type == "patch.apply":
        return run_patch_apply_task(task_id=task_id, payload=payload)

    raise ValueError(f"unknown task type: {task_type}")


def run_once(worker_id: str, cfg: WorkerConfig) -> bool:
    task = claim_task(worker_id=worker_id, lock_s=cfg.lock_s)
    if not task:
        return False

    task_id = str(task["id"])
    task_type = str(task["type"])
    attempts = int(task.get("attempts") or 0)
    max_attempts = int(task.get("max_attempts") or 3)
    payload = task.get("payload") or {}
    run_id = task.get("run_id")

    t0 = now_ms()
    LOG.info("claimed id=%s type=%s attempts=%s/%s", task_id, task_type, attempts, max_attempts)

    # EVENT: task claimed
    write_event(
        source="worker",
        envelope={
            "type": "task.claimed",
            "ts": utc_iso(),
            "task_id": task_id,
            "task_type": task_type,
            "worker_id": worker_id,
            "attempts": attempts,
            "max_attempts": max_attempts,
            "run_id": str(run_id) if run_id else None,
            "payload": payload,
        },
    )

    try:
        # EVENT: task begin (generic)
        write_event(
            source="worker",
            envelope={
                "type": task_type,
                "ts": utc_iso(),
                "task_id": task_id,
                "run_id": str(run_id) if run_id else None,
                "data": payload,
            },
        )

        result = _dispatch_task(task_type=task_type, task_id=task_id, payload=payload)
        took_ms = now_ms() - t0

        complete_task_success(
            task_id=task_id,
            result={"ok": True, "kind": task_type, "took_ms": took_ms, **(result or {})},
        )

        # EVENT: success
        write_event(
            source="worker",
            envelope={
                "type": f"{task_type}.result",
                "ts": utc_iso(),
                "task_id": task_id,
                "run_id": str(run_id) if run_id else None,
                "data": {"ok": True, "took_ms": took_ms, "result": result},
            },
        )

        LOG.info("succeeded id=%s kind=%s took_ms=%s", task_id, task_type, took_ms)
        return True

    except Exception as e:
        took_ms = now_ms() - t0
        err = f"{type(e).__name__}: {e}"

        retry_backoff_s = compute_backoff_s(max(1, attempts))
        terminal = (attempts >= max_attempts)

        complete_task_failure(task_id=task_id, error=err, retry_backoff_s=retry_backoff_s)

        # EVENT: failure
        write_event(
            source="worker",
            envelope={
                "type": "task.failed" if not terminal else "task.permanently_failed",
                "ts": utc_iso(),
                "task_id": task_id,
                "run_id": str(run_id) if run_id else None,
                "error": err,
                "took_ms": took_ms,
                "attempts": attempts,
                "max_attempts": max_attempts,
                "retry_backoff_s": retry_backoff_s,
            },
        )

        LOG.error("failed id=%s err=%s terminal=%s", task_id, err, terminal)
        return True


def run_forever() -> None:
    _setup_logging()
    worker_id = f"{os.uname().nodename}:{os.getpid()}"
    cfg = WorkerConfig(
        poll_s=env_int("AIOP_WORKER_POLL_S", "1"),
        lock_s=env_int("AIOP_WORKER_LOCK_S", "60"),
    )
    LOG.info("starting wid=%s poll_s=%s lock_s=%s", worker_id, cfg.poll_s, cfg.lock_s)

    while True:
        did = run_once(worker_id, cfg)
        if not did:
            time.sleep(cfg.poll_s)


if __name__ == "__main__":
    run_forever()
