# D2 -- Add `homelab_file_write` MCP Tool

**Owner:** Paco Duece (Cowork) -- Head of Engineering
**Architect:** Paco (COO)
**CEO approval:** [pending]
**Phase:** D2 of the data-plane sequence (D1 closed Day 71)
**Risk:** Low-medium. New tool, atomic operations, deferred-restart pattern. Existing tools keep working until restart.

## Context

D1 lifted the input-validation limits in `mcp_server.py`. D2 adds a new MCP tool, `homelab_file_write`, that lets clients write files to any allowed host in a single tool call. Today, file writes route through `homelab_ssh_run` with chunked `cat <<EOF` heredocs and base64 round-trips -- error-prone, slow, and hard to make atomic. After D2, file writes are one call with proper atomicity, parent-directory creation, and mode control.

Reference: SESSION.md Day 71/72. CHECKLIST.md P2 D2 item. CHARTERS_v0.1.md Charter 3 (Engineering scope). CAPACITY_v1.1.md.

## Methodology lessons baked in (from D1 retrospective)

**Restart safety.** Synchronous `sudo systemctl restart` kills the response channel because the MCP service IS the channel. Use deferred-restart pattern: background subshell with sleep, so the in-flight tool call returns before the bounce. Same pattern PD used in D1.

**Health check semantics.** Plain curl probes against the streamable-HTTP MCP endpoint hang -- they are not reliable success signals. Do NOT block on a curl probe. Verification is Paco's responsibility, post-restart, via an actual MCP tool call from claude.ai. PD's job is to confirm the service is `active` per systemd and the file parses cleanly; Paco runs the live tool-call gate.

**Working-tree handling.** mcp_server.py may have residual uncommitted changes from prior work. Check `git status` before starting. Bring the working tree clean, or roll changes into the D2 commit at Engineering discretion. Document the choice in the report (same as D1).

## Cowork prompt -- paste into P2 verbatim

```
Task: D2 -- Add `homelab_file_write` MCP tool to /home/jes/control-plane/mcp_server.py

Context: D1 (input-limit lift) is shipped and closed. D2 adds a new MCP tool that
lets clients write files to any ALLOWED_HOSTS host atomically. This eliminates the
chunked-cat heredoc workaround Paco currently uses. New tool only -- do not
modify existing tools or change subprocess.run behavior beyond what is needed for
the new tool itself. D3 will add file_transfer in a separate task.

Restart pattern: deferred-restart only (synchronous restart kills the response
channel). Same pattern you used in D1.

Health check pattern: do NOT use curl probes against the streamable-HTTP endpoint
as a success signal -- they hang. Confirm the service is `active` per systemd and
the file parses cleanly; Paco will run the live tool-call gate from claude.ai.

Working-tree note: check git status first. mcp_server.py may have uncommitted
changes. Bring the tree clean or roll into the D2 commit at your discretion.
Document the choice in your report.

Execute in order. Do not skip steps.

1. SSH into CiscoKid as jes. Check `cd /home/jes/control-plane && git status --short`
   and report what's in the working tree.

2. Make a timestamped backup:
   cp /home/jes/control-plane/mcp_server.py \
      /home/jes/control-plane/mcp_server.py.bak.$(date +%Y%m%d_%H%M%S)
   Capture the backup filename for the report.

3. Add the new Pydantic input model immediately after FileReadInput. Field
   definitions (use exactly these field names, types, and constraints):

   class FileWriteInput(BaseModel):
       host: str = Field(..., description="Target host name", min_length=1, max_length=20)
       path: str = Field(..., description="Absolute file path on remote host", min_length=1, max_length=4096)
       content: str = Field(..., description="File content (text). For binary, base64-encode and pass with binary=True.", max_length=5242880)
       mode: Optional[str] = Field(default="write", description="write (overwrite, atomic), append, or create (fail-if-exists)", pattern="^(write|append|create)$")
       binary: Optional[bool] = Field(default=False, description="If True, content is already base64-encoded and will be decoded on the remote side")
       file_mode: Optional[str] = Field(default=None, description="Optional chmod after write (e.g. '0644'). None = system default", pattern="^[0-7]{3,4}$")
       mkdir_parents: Optional[bool] = Field(default=True, description="Create parent directories if missing")

4. Add the tool implementation. Required behavior:

   a. Validate host is in ALLOWED_HOSTS. Return {"ok": False, "error": "..."} if not.
   b. Always base64-encode content on the wire. If binary=False, encode the input
      string. If binary=True, content is already base64 -- use as-is. This
      eliminates shell-escape failures for content with quotes, newlines, unicode,
      special characters, etc.
   c. mkdir_parents=True (default): prepend `mkdir -p $(dirname <path>)` to the
      remote command chain.
   d. mode="write" (default): atomic. Write base64-decoded content to a temp path
      `<path>.tmp.$$` first, then `mv` to final path. This ensures readers never
      see a partially-written file.
   e. mode="append": just append (no atomicity needed). Decode base64 to >> path.
   f. mode="create": fail if file exists. Use `set -o noclobber` or equivalent.
   g. file_mode set: run `chmod <file_mode> <path>` after the write succeeds.
   h. Use shlex.quote on path arguments to defend against any unusual characters.
   i. Return a dict: {"ok": bool, "host": str, "path": str, "bytes_written": int,
      "mode_used": str, "error": Optional[str]}.

   Required imports if not already present: `import base64, shlex`.

   Use the existing ssh_run helper for the actual SSH execution. Do not
   reimplement SSH transport. Pass a generous timeout (60s default is fine for
   files up to a few MB).

   Illustrative shape (adapt to existing code style; do not paste verbatim):

       @mcp.tool()
       def homelab_file_write(input: FileWriteInput) -> dict:
           if input.host not in ALLOWED_HOSTS:
               return {"ok": False, "host": input.host, "path": input.path,
                       "bytes_written": 0, "mode_used": input.mode,
                       "error": f"host '{input.host}' not in ALLOWED_HOSTS"}

           if input.binary:
               b64 = input.content
               raw_bytes = len(base64.b64decode(input.content))
           else:
               raw = input.content.encode("utf-8")
               b64 = base64.b64encode(raw).decode("ascii")
               raw_bytes = len(raw)

           qpath = shlex.quote(input.path)
           parts = []
           if input.mkdir_parents:
               parts.append(f"mkdir -p $(dirname {qpath})")

           if input.mode == "write":
               qtmp = shlex.quote(f"{input.path}.tmp.$$")
               # Note: $$ must NOT be quoted -- it expands on the remote shell
               # Adjust quoting accordingly when building the command string
               parts.append(f"echo {shlex.quote(b64)} | base64 -d > {input.path}.tmp.$$ && mv {input.path}.tmp.$$ {qpath}")
           elif input.mode == "append":
               parts.append(f"echo {shlex.quote(b64)} | base64 -d >> {qpath}")
           elif input.mode == "create":
               parts.append(f"set -o noclobber; echo {shlex.quote(b64)} | base64 -d > {qpath}")

           if input.file_mode:
               parts.append(f"chmod {input.file_mode} {qpath}")

           remote_cmd = " && ".join(parts)
           result = ssh_run(input.host, remote_cmd, timeout=60)
           ok = (result.get("exit_code") == 0)
           return {"ok": ok, "host": input.host, "path": input.path,
                   "bytes_written": raw_bytes if ok else 0,
                   "mode_used": input.mode,
                   "error": None if ok else result.get("stderr", "unknown error")}

   The above is illustrative -- adapt naming, return shape, and quoting to match
   the existing module's conventions. Pay attention to $$ vs shell-escaped
   variables in the temp-path construction -- $$ must reach the remote shell
   intact to expand to the remote PID.

5. Verify the file still parses as valid Python:
   python3 -c "import ast; ast.parse(open('/home/jes/control-plane/mcp_server.py').read())"
   Expected: no output, exit 0.

6. Restart homelab-mcp.service via the deferred pattern (NOT synchronous):
   nohup bash -c 'sleep 3 && sudo systemctl restart homelab-mcp.service' > /dev/null 2>&1 &

7. After ~6 seconds, verify the service came back up:
   sleep 6 && systemctl is-active homelab-mcp.service
   Expected: active

8. (Optional, informational only) Check service logs for tool registration:
   journalctl -u homelab-mcp.service --since '1 minute ago' --no-pager | head -30
   Look for any startup errors. This is NOT a hard pass/fail signal.

9. Commit and push:
   cd /home/jes/control-plane
   git add mcp_server.py
   git commit -m "feat(mcp): add homelab_file_write tool (D2)"
   git push origin main

   If the working tree had pre-existing changes that you rolled into this commit,
   note them in the commit body and the report.

10. Report back with:
    - git status output before starting (working tree state)
    - Backup filename
    - Diff or excerpt showing the new FileWriteInput class and homelab_file_write function
    - AST parse outcome
    - Service restart confirmation (`systemctl is-active` output)
    - Working-tree handling decision (clean before / rolled into D2 / kept separate)
    - Code commit SHA on origin/main
    - Any unexpected stderr or warnings

Rollback procedure if anything fails:
    cp <backup-filename> /home/jes/control-plane/mcp_server.py
    nohup bash -c 'sleep 3 && sudo systemctl restart homelab-mcp.service' > /dev/null 2>&1 &
    sleep 6 && systemctl is-active homelab-mcp.service
    Report rollback outcome.

Hard rules:
- Do NOT modify existing tools.
- Do NOT change subprocess.run behavior outside the new tool.
- Do NOT add path-based access controls (we already trust SSH user 'jes' to write
  anywhere; adding restrictions in this tool would be security theater).
- Do NOT use synchronous systemctl restart (kills response channel).
- Do NOT use curl probes against the streamable-HTTP endpoint as success signal.
- Do NOT add chown support (sudo concern; out of scope for D2).
- Do NOT attempt to verify the new tool from your own session via MCP -- you can't
  call your own MCP server from inside Cowork. Paco runs the live verification
  gate from claude.ai after you report done.
```

## Verification gate (Paco runs this after PD reports done)

From claude.ai, Paco will:
1. Confirm the new tool is callable: invoke `homelab_file_write` with a small test payload.
2. Test write mode (atomic overwrite): write a distinctive file to /tmp/, then read it back via `homelab_file_read` and compare.
3. Test mkdir_parents: write to a non-existent parent directory.
4. Test create mode: write once successfully, then attempt again -- second call should fail.
5. Test file_mode: write with mode '0600' and verify via `homelab_ssh_run` `stat` output.
6. Test binary=True: send a small base64-encoded binary payload, decode, verify hash.

If all six pass, D2 is closed and audit-trail entry lands in CHECKLIST.md + SESSION.md.

## Why this matters

D2 is the highest-leverage single item on the data-plane sequence. After D2:
- Every spec PD writes for B1, B2, Atlas, etc. ships in a single tool call instead of chunked appends
- Paco's iCloud + CiscoKid mirror flow becomes 2 calls instead of 8+
- Multi-page configs (Postgres, MinIO, nginx, systemd units) are first-class citizens
- The MCP fabric stops being a pure control plane and starts being a real (light) data plane

Follow-on: D3 (`homelab_file_transfer`, host-to-host) builds on this foundation.
