from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Keep tool registry optional: if tools exist, we can use them; otherwise fall back to file writes.
from ai_operator.tools.registry import default_registry

TOOLS = default_registry()


def _utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _repo_root_from_payload(payload: Dict[str, Any]) -> str:
    """
    Gate6 enqueue payloads for repo.change/doc.build do NOT include repo_path.
    We allow:
      - payload["repo_path"] if present
      - env AIOP_REPO_ROOT if set
      - default: /home/jes/control-plane/orchestrator
    """
    repo = (payload.get("repo_path") or os.getenv("AIOP_REPO_ROOT") or "/home/jes/control-plane/orchestrator").strip()
    return repo


def _write_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def run_repo_change_task(task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Expected Gate6 payload shape (from your logs):
      {
        "name": "...",
        "meta": {...},
        "patch": "diff --git ..."
      }
    Behavior:
      - If a tool named "repo.change" exists, try it first.
      - Otherwise write patch to artifacts/patches/<ts>_<name>.patch and succeed.
    """
    # Try tool if registered
    try:
        return {"ok": True, "artifact": TOOLS.run("repo.change", payload)}
    except Exception:
        pass

    repo_root = _repo_root_from_payload(payload)
    name = str(payload.get("name") or "repo_change").strip() or "repo_change"
    patch = payload.get("patch")
    if not isinstance(patch, str) or not patch.strip():
        raise ValueError("repo.change payload.patch must be a non-empty string")

    ts = _utc_ts()
    out_path = os.path.join(repo_root, "artifacts", "patches", f"{ts}_{name}.patch")
    _write_file(out_path, patch)

    return {
        "ok": True,
        "kind": "patch",
        "path": out_path,
        "meta": {"ts": ts, "name": name, "purpose": (payload.get("meta") or {}).get("purpose")},
    }


def run_doc_build_task(task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Expected Gate6 payload shape (from your logs):
      {
        "name": "...",
        "meta": {...},
        "markdown": "# ..."
      }
    Behavior:
      - If a tool named "doc.build" exists, try it first.
      - Otherwise write markdown to artifacts/docs/<ts>_<name>.md and succeed.
    """
    # Try tool if registered
    try:
        return {"ok": True, "artifact": TOOLS.run("doc.build", payload)}
    except Exception:
        pass

    repo_root = _repo_root_from_payload(payload)
    name = str(payload.get("name") or "doc").strip() or "doc"
    md = payload.get("markdown")
    if not isinstance(md, str) or not md.strip():
        raise ValueError("doc.build payload.markdown must be a non-empty string")

    ts = _utc_ts()
    out_path = os.path.join(repo_root, "artifacts", "docs", f"{ts}_{name}.md")
    _write_file(out_path, md)

    return {
        "ok": True,
        "kind": "doc",
        "path": out_path,
        "meta": {"ts": ts, "name": name, "purpose": (payload.get("meta") or {}).get("purpose")},
    }
