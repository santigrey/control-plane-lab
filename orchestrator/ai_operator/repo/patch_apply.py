from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional


def utc_ts_compact() -> str:
    # 20260221T225059Z
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str], cwd: str, timeout_s: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_s,
        check=False,
    )


@dataclass
class ApplyResult:
    ok: bool
    checked: bool
    applied: bool
    repo_path: str
    patch_path: str
    git_status_porcelain: str
    diff_stat: str
    check_stdout: str
    check_stderr: str
    apply_stdout: str
    apply_stderr: str
    report_path: Optional[str] = None


def ensure_repo_clean(repo_path: str) -> str:
    cp = run(["git", "status", "--porcelain"], cwd=repo_path, timeout_s=30)
    out = (cp.stdout or "").strip()
    # If git itself failed (not a repo), surface stderr
    if cp.returncode != 0:
        raise RuntimeError(f"git status failed: {cp.stderr.strip()}")
    return out


def apply_patch(
    repo_path: str,
    patch_path: str,
    *,
    require_clean: bool = True,
    check_only: bool = False,
    timeout_s: int = 120,
) -> ApplyResult:
    repo_path = os.path.abspath(repo_path)
    patch_path = os.path.abspath(patch_path)

    if not os.path.isdir(repo_path):
        raise ValueError(f"repo_path does not exist or is not a directory: {repo_path}")
    if not os.path.isfile(patch_path):
        raise ValueError(f"patch_path does not exist or is not a file: {patch_path}")

    porcelain = ensure_repo_clean(repo_path)
    if require_clean and porcelain:
        raise RuntimeError(
            "working tree not clean; refusing to apply patch. "
            "Commit/stash/clean and retry.\n"
            f"git status --porcelain:\n{porcelain}"
        )

    # 1) Check
    chk = run(["git", "apply", "--check", patch_path], cwd=repo_path, timeout_s=timeout_s)
    check_stdout = (chk.stdout or "").strip()
    check_stderr = (chk.stderr or "").strip()
    if chk.returncode != 0:
        return ApplyResult(
            ok=False,
            checked=True,
            applied=False,
            repo_path=repo_path,
            patch_path=patch_path,
            git_status_porcelain=porcelain,
            diff_stat="",
            check_stdout=check_stdout,
            check_stderr=check_stderr,
            apply_stdout="",
            apply_stderr="",
        )

    if check_only:
        return ApplyResult(
            ok=True,
            checked=True,
            applied=False,
            repo_path=repo_path,
            patch_path=patch_path,
            git_status_porcelain=porcelain,
            diff_stat="",
            check_stdout=check_stdout,
            check_stderr=check_stderr,
            apply_stdout="",
            apply_stderr="",
        )

    # 2) Apply
    app = run(["git", "apply", patch_path], cwd=repo_path, timeout_s=timeout_s)
    apply_stdout = (app.stdout or "").strip()
    apply_stderr = (app.stderr or "").strip()
    if app.returncode != 0:
        return ApplyResult(
            ok=False,
            checked=True,
            applied=False,
            repo_path=repo_path,
            patch_path=patch_path,
            git_status_porcelain=porcelain,
            diff_stat="",
            check_stdout=check_stdout,
            check_stderr=check_stderr,
            apply_stdout=apply_stdout,
            apply_stderr=apply_stderr,
        )

    # 3) Capture diff stat vs HEAD (safe for uncommitted changes post-apply)
    ds = run(["git", "diff", "--stat"], cwd=repo_path, timeout_s=30)
    diff_stat = (ds.stdout or "").strip()

    return ApplyResult(
        ok=True,
        checked=True,
        applied=True,
        repo_path=repo_path,
        patch_path=patch_path,
        git_status_porcelain=porcelain,
        diff_stat=diff_stat,
        check_stdout=check_stdout,
        check_stderr=check_stderr,
        apply_stdout=apply_stdout,
        apply_stderr=apply_stderr,
    )


def write_apply_report(
    *,
    repo_path: str,
    name: str,
    purpose: str,
    patch_path: str,
    apply_result: ApplyResult,
) -> Dict[str, Any]:
    ts = utc_ts_compact()
    out_dir = Path(repo_path) / "artifacts" / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)

    report_file = out_dir / f"{ts}_{name}_apply_report.md"

    patch_p = Path(patch_path)
    patch_bytes = patch_p.stat().st_size
    patch_sha = sha256_file(patch_p)

    lines = []
    lines.append(f"# Patch Apply Report — {name}")
    lines.append("")
    lines.append(f"- **ts (UTC):** `{ts}`")
    lines.append(f"- **purpose:** `{purpose}`")
    lines.append(f"- **repo_path:** `{repo_path}`")
    lines.append(f"- **patch_path:** `{patch_path}`")
    lines.append(f"- **patch_sha256:** `{patch_sha}`")
    lines.append(f"- **patch_bytes:** `{patch_bytes}`")
    lines.append("")
    lines.append("## Outcome")
    lines.append(f"- **ok:** `{apply_result.ok}`")
    lines.append(f"- **checked:** `{apply_result.checked}`")
    lines.append(f"- **applied:** `{apply_result.applied}`")
    lines.append("")
    if apply_result.git_status_porcelain:
        lines.append("## Pre-check git status (porcelain)")
        lines.append("```")
        lines.append(apply_result.git_status_porcelain)
        lines.append("```")
        lines.append("")

    lines.append("## git apply --check (stdout/stderr)")
    lines.append("```")
    if apply_result.check_stdout:
        lines.append(apply_result.check_stdout)
    if apply_result.check_stderr:
        lines.append(apply_result.check_stderr)
    lines.append("```")
    lines.append("")

    lines.append("## git apply (stdout/stderr)")
    lines.append("```")
    if apply_result.apply_stdout:
        lines.append(apply_result.apply_stdout)
    if apply_result.apply_stderr:
        lines.append(apply_result.apply_stderr)
    lines.append("```")
    lines.append("")

    if apply_result.diff_stat:
        lines.append("## git diff --stat")
        lines.append("```")
        lines.append(apply_result.diff_stat)
        lines.append("```")
        lines.append("")

    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    report_meta = {
        "kind": "doc",
        "meta": {
            "ts": ts,
            "name": f"{name}_apply_report",
            "purpose": purpose,
            "path": str(report_file),
            "bytes": report_file.stat().st_size,
        },
    }
    return report_meta