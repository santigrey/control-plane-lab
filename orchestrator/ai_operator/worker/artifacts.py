from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def utc_iso_compact() -> str:
    # e.g. 20260221T220047Z
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_text(s: str) -> str:
    h = hashlib.sha256()
    h.update(s.encode("utf-8"))
    return h.hexdigest()


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


@dataclass
class Artifact:
    kind: str  # "patch" | "doc"
    path: str  # relative or absolute
    sha256: str
    bytes: int
    meta: Dict[str, Any]


def write_patch_artifact(
    *,
    repo_path: str,
    patch_text: str,
    artifacts_root: str = "artifacts",
    name: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Artifact:
    """
    Writes a unified diff patch to artifacts/patches/.
    Does NOT apply it. (Safe, auditable.)
    """
    if not isinstance(repo_path, str) or not repo_path.strip():
        raise ValueError("repo_path must be a non-empty string")
    if not isinstance(patch_text, str) or not patch_text.strip():
        raise ValueError("patch_text must be a non-empty string")

    ts = utc_iso_compact()
    safe_name = (name or "change").strip().replace(" ", "_")
    fname = f"{ts}_{safe_name}.patch"

    root = Path(repo_path).resolve()
    out_dir = root / artifacts_root / "patches"
    ensure_dir(out_dir)

    out_path = out_dir / fname
    out_path.write_text(patch_text, encoding="utf-8")

    content_bytes = out_path.read_bytes()
    artifact = Artifact(
        kind="patch",
        path=str(out_path),
        sha256=hashlib.sha256(content_bytes).hexdigest(),
        bytes=len(content_bytes),
        meta={
            "name": safe_name,
            "ts": ts,
            **(meta or {}),
        },
    )
    return artifact


def write_doc_artifact(
    *,
    repo_path: str,
    markdown: str,
    artifacts_root: str = "artifacts",
    name: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Artifact:
    """
    Writes markdown to artifacts/docs/.
    """
    if not isinstance(repo_path, str) or not repo_path.strip():
        raise ValueError("repo_path must be a non-empty string")
    if not isinstance(markdown, str) or not markdown.strip():
        raise ValueError("markdown must be a non-empty string")

    ts = utc_iso_compact()
    safe_name = (name or "report").strip().replace(" ", "_")
    fname = f"{ts}_{safe_name}.md"

    root = Path(repo_path).resolve()
    out_dir = root / artifacts_root / "docs"
    ensure_dir(out_dir)

    out_path = out_dir / fname
    out_path.write_text(markdown, encoding="utf-8")

    content_bytes = out_path.read_bytes()
    artifact = Artifact(
        kind="doc",
        path=str(out_path),
        sha256=hashlib.sha256(content_bytes).hexdigest(),
        bytes=len(content_bytes),
        meta={
            "name": safe_name,
            "ts": ts,
            **(meta or {}),
        },
    )
    return artifact


def artifact_to_result(a: Artifact) -> Dict[str, Any]:
    return {
        "artifact": {
            "kind": a.kind,
            "path": a.path,
            "sha256": a.sha256,
            "bytes": a.bytes,
            "meta": a.meta,
        }
    }