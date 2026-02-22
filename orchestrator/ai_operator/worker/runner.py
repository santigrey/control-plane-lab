from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict

from ai_operator.tools.registry import default_registry
from ai_operator.memory.tasks import claim_task, complete_task_failure, complete_task_success
from ai_operator.memory.events import write_event
from ai_operator.repo.patch_apply import apply_patch, write_apply_report

TOOLS = default_registry()

LOG = logging.getLogger("aiop.worker")


def setup_logging() -> None:
    if LOG.handlers:
        return
    LOG.setLevel(logging.INFO)
    h = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    h.setFormatter(fmt)
    LOG.addHandler(h)


def env_int(name: str, default: str) -> int:
    v = os.getenv(name, default)
    return int(str(v).strip())


def env_str(name: str, default: str = "") -> str:
    v = os.getenv(name, default)
    return str(v).strip()


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def now_ms() -> int:
    return int(time.time() * 1000)


def compute_backoff_s(attempts: int) -> int:
    base = 2 ** max(0, attempts - 1)
    return int(min(30, base))


@dataclass
class WorkerConfig:
    poll_s: int = 1
    lock_s: int = 60
    default_repo_path: str = "/home/jes/control-plane/orchestrator"


def _event(source: str, envelope: Dict[str, Any], tool: str | None = None, tool_result: Dict[str, Any] | None = None) -> None:
    # Persist to memory table (event-sourcing trail)
    write_event(source=source, envelope=envelope, tool=tool, tool_result=tool_result)


def handle_tool_call(task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    tool = payload.get("tool")
    args = payload.get("args") or {}
    if not isinstance(tool, str) or not tool.strip():
        raise ValueError("payload.tool must be a non-empty string")
    if not isinstance(args, dict):
        raise ValueError("payload.args must be an object")

    tool_name = tool.strip()
    result = TOOLS.run(tool_name, args)
    return {"ok": True, "tool": tool_name, "result": result}


def handle_patch_apply(cfg: WorkerConfig, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    payload fields:
      - repo_path: optional (defaults to cfg.default_repo_path)
      - patch_path: required (path to .patch file)
      - name: optional (used for report file name)
      - purpose: optional (portfolio metadata)
      - require_clean: optional bool (default True)
      - check_only: optional bool (default False)
    """
    repo_path = str(payload.get("repo_path") or cfg.default_repo_path)
    patch_path = payload.get("patch_path")
    if not isinstance(patch_path, str) or not patch_path.strip():
        raise ValueError("payload.patch_path must be a non-empty string")

    name = str(payload.get("name") or "patch_apply")
    purpose = str(payload.get("purpose") or "apply_patch")
    require_clean = bool(payload.get("require_clean", True))
    check_only = bool(payload.get("check_only", False))

    ar = apply_patch(
        repo_path=repo_path,
        patch_path=patch_path,
        require_clean=require_clean,
        check_only=check_only,
    )

    if not ar.ok:
        # Return a structured failure detail; runner will wrap into task failure
        raise RuntimeError(
            "patch apply failed\n"
            f"check_stderr={ar.check_stderr}\n"
            f"apply_stderr={ar.apply_stderr}"
        )

    report_meta = write_apply_report(
        repo_path=repo_path,
        name=name,
        purpose=purpose,
        patch_path=patch_path,
        apply_result=ar,
    )
    ar.report_path = report_meta["meta"]["path"]

    return {
        "ok": True,
        "kind": "patch.apply",
        "repo_path": repo_path,
        "patch_path": patch_path,
        "checked": ar.checked,
        "applied": ar.applied,
        "diff_stat": ar.diff_stat,
        "artifact": report_meta,
    }


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

    LOG.info("claimed id=%s type=%s attempts=%s/%s", task_id, task_type, attempts, max_attempts)

    t0 = now_ms()

    _event(
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
        if task_type == "tool.call":
            _event(
                source="worker",
                envelope={
                    "type": "tool_call",
                    "ts": utc_iso(),
                    "task_id": task_id,
                    "run_id": str(run_id) if run_id else None,
                    "data": {"tool": payload.get("tool"), "args": payload.get("args") or {}},
                },
                tool=str(payload.get("tool") or ""),
            )
            out = handle_tool_call(task_id, payload)
            took_ms = now_ms() - t0
            result = {"ok": True, "tool": out["tool"], "result": out["result"], "took_ms": took_ms}

            complete_task_success(task_id=task_id, result=result)

            _event(
                source="worker",
                envelope={
                    "type": "tool_result",
                    "ts": utc_iso(),
                    "task_id": task_id,
                    "run_id": str(run_id) if run_id else None,
                    "data": {"tool": out["tool"], "result": out["result"], "took_ms": took_ms},
                },
                tool=out["tool"],
                tool_result={"tool": out["tool"], "result": out["result"], "took_ms": took_ms},
            )

            LOG.info("succeeded id=%s tool=%s took_ms=%s", task_id, out["tool"], took_ms)
            return True

        if task_type == "patch.apply":
            _event(
                source="worker",
                envelope={
                    "type": "patch.apply",
                    "ts": utc_iso(),
                    "task_id": task_id,
                    "run_id": str(run_id) if run_id else None,
                    "data": payload,
                },
            )

            out = handle_patch_apply(cfg, payload)
            took_ms = now_ms() - t0
            result = {"ok": True, "kind": "patch.apply", "took_ms": took_ms, **out}

            complete_task_success(task_id=task_id, result=result)

            _event(
                source="worker",
                envelope={
                    "type": "patch.apply.result",
                    "ts": utc_iso(),
                    "task_id": task_id,
                    "run_id": str(run_id) if run_id else None,
                    "data": {"ok": True, "took_ms": took_ms, "artifact": out.get("artifact")},
                },
            )

            LOG.info("succeeded id=%s kind=patch.apply took_ms=%s", task_id, took_ms)
            return True

        raise ValueError(f"unknown task type: {task_type}")

    except Exception as e:
        took_ms = now_ms() - t0
        err = f"{type(e).__name__}: {e}"

        retry_backoff_s = compute_backoff_s(max(1, attempts))
        complete_task_failure(task_id=task_id, error=err, retry_backoff_s=retry_backoff_s)

        terminal = attempts >= max_attempts  # best-effort; DB function is source of truth
        LOG.error("failed id=%s err=%s terminal=%s", task_id, err, terminal)

        _event(
            source="worker",
            envelope={
                "type": "task.failed",
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

        return True


def run_forever() -> None:
    setup_logging()
    worker_id = f"{os.uname().nodename}:{os.getpid()}"
    cfg = WorkerConfig(
        poll_s=env_int("AIOP_WORKER_POLL_S", "1"),
        lock_s=env_int("AIOP_WORKER_LOCK_S", "60"),
        default_repo_path=env_str("AIOP_REPO_PATH", "/home/jes/control-plane/orchestrator"),
    )
    LOG.info("starting wid=%s poll_s=%s lock_s=%s", worker_id, cfg.poll_s, cfg.lock_s)

    while True:
        did = run_once(worker_id, cfg)
        if not did:
            time.sleep(cfg.poll_s)


if __name__ == "__main__":
    run_forever()