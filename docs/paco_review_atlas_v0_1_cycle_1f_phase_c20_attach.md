# Paco Review -- Atlas v0.1 Cycle 1F Phase C.2.0 Attach Diagnostic

**Filed by:** PD
**Date:** 2026-04-30 (Day 76)
**Phase:** Cycle 1F Phase C.2.0 (non-restart attach diagnostics)
**Status:** PASS, root cause located server-side, recommendation: **STOP and file paco_request for mcp_server.py edit** (server-side fix, requires Paco direction + Sloan single-confirm)

---

## Section 0 -- Verified live block (5th standing rule)

12 verifications run live; all evidence below from this session.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | B2b anchor StartedAt PRE | `docker inspect` on Beast | `2026-04-27T00:13:57.800746541Z` healthy r=0 |
| 2 | Garage anchor StartedAt PRE | `docker inspect` on Beast | `2026-04-27T05:39:58.168067641Z` healthy r=0 |
| 3 | atlas.events count PRE | psql on Beast | embeddings=2, inference=4 |
| 4 | uvicorn PID identity | `pgrep -af mcp_http.py` | 3631249 `python3 /home/jes/control-plane/mcp_http.py` |
| 5 | uvicorn ELAPSED at Step Z | `ps -p 3631249 -o etime` | `3-04:00:55` (no restart through Phase C.2.0) |
| 6 | py-spy ephemeral installed | venv `/tmp/pyspy-diag/bin/py-spy --version` | 0.4.2 |
| 7 | strace tool present | `which strace; --version` | 5.16 (`/usr/bin/strace`) |
| 8 | lsof tool present | `which lsof; -v` | 4.93.2 (`/usr/bin/lsof`) |
| 9 | mcp_server.py path + size | `wc -l` | 357 lines `/home/jes/control-plane/mcp_server.py` |
| 10 | py-spy stack dump (3 dumps) | `sudo -n py-spy dump --pid 3631249` | All 3 sampled the same blocking frame: `subprocess.run` -> `ssh_run` -> `homelab_ssh_run` |
| 11 | Anchors POST bit-identical | diff PRE/POST | ANCHORS-BIT-IDENTICAL |
| 12 | atlas.events POST unchanged | psql on Beast | embeddings=2, inference=4 |
| 13 | Cleanup verified empty | `ls /tmp/ \| grep ...` | NONE remaining |

---

## Section 1 -- TL;DR

FastMCP server's `@mcp.tool` async handlers (notably `homelab_ssh_run`) call synchronous helpers (`ssh_run` -> `subprocess.run`) directly without `asyncio.to_thread()` or `loop.run_in_executor()`. This blocks the entire uvicorn asyncio event loop for the duration of every SSH command (up to 1800s per `SSHRunInput.timeout` max). While blocked, no other client request can be serviced -- `initialize` from any new client queues until the SSH child returns. Same anti-pattern in `homelab_memory_search` (sync `requests.post` for embeddings + sync `psycopg2`).

**Mechanism is event-loop blocking, not init-handler malfunction. Hypothesis 5.E PROVEN; 5.B revised (header was a red herring -- it was a separate gap from PD's Phase C.1).**

Fix scope: edit `mcp_server.py` to wrap sync I/O in `asyncio.to_thread()` (or migrate to async libs). Per directive, server-side mcp_server.py edits require paco_request + Sloan single-confirm. STOPping here.

---

## Section 2 -- py-spy stack dump excerpts

3 dumps captured; identical stack each time.

```
Process 3631249: /usr/bin/python3 /home/jes/control-plane/mcp_http.py
Thread 3631249 (idle): "MainThread"
    select                          (selectors.py:416)
    _communicate                    (subprocess.py:2021)
    communicate                     (subprocess.py:1154)
    run                             (subprocess.py:505)
    ssh_run                         (mcp_server.py:58)
    homelab_ssh_run                 (mcp_server.py:102)
    call_fn_with_arg_validation     (mcp/server/fastmcp/utilities/func_metadata.py:93)
    run                             (mcp/server/fastmcp/tools/base.py:101)
    call_tool                       (mcp/server/fastmcp/tools/tool_manager.py:93)
    call_tool                       (mcp/server/fastmcp/server.py:346)
    handler                         (mcp/server/lowlevel/server.py:540)
    _handle_request                 (mcp/server/lowlevel/server.py:763)
    _handle_message                 (mcp/server/lowlevel/server.py:696)
    _run                            (asyncio/events.py:80)
    _run_once                       (asyncio/base_events.py:1909)
    run_forever                     (asyncio/base_events.py:603)
    run_until_complete              (asyncio/base_events.py:636)
    asyncio_run                     (uvicorn/_compat.py:60)
    run                             (uvicorn/server.py:75)
    run                             (uvicorn/main.py:606)
```

**Read of the stack:** uvicorn's asyncio event loop is parked inside `subprocess.run()` -> `_communicate()` -> `select()` waiting for the SSH child process's stdout/stderr to drain. From the event loop's perspective this is a blocking call, not an awaitable. While in this state, no other coroutine on the loop can run.

The handler at `mcp_server.py:102` is `async def homelab_ssh_run` (decorated `@mcp.tool`) which calls the synchronous `ssh_run(...)` at line 58 directly. The async-ness is cosmetic.

Every dump caught the same state because the dump itself was triggered via this very session's `homelab_ssh_run` MCP tool calls -- so the server was processing my own SSH command at sample time. This is a circular but self-evident proof: any active homelab_ssh_run call blocks the loop for its full duration.

---

## Section 3 -- strace highlights

Not run. Per directive, strace is conditional on "py-spy unavailable or stacks unclear." py-spy stacks were unambiguous (Section 2). Skipped to preserve diagnostic minimality.

---

## Section 4 -- Connection state during hang (Step C.2.0.d)

Captured ~5s into a Beast python-SDK probe with magic header (replicating Paco's CP1).

**ss `:8001` (uvicorn loopback side):**
```
ESTAB  450  0  127.0.0.1:8001  127.0.0.1:53862    <- 450 BYTES PENDING RECEIVE
ESTAB    0  0  127.0.0.1:8001  127.0.0.1:49640    <- drained (Mac mini node-MCP persistent)
TIME-WAIT entries on 51520, 51506, 49628          <- prior conns clean
```

**ss `:8443` (nginx side):**
```
ESTAB  0  0  192.168.1.10:8443     192.168.1.152:50532    <- BEAST CONNECTION ACTIVE during hang
ESTAB  0  0  100.115.56.89:8443    100.102.87.70:59226    <- Mac mini Tailscale persistent
```

**lsof TCP:8001:**
```
nginx    849692 www-data   38u  TCP localhost:49640->localhost:8001 (ESTABLISHED)
nginx    849692 www-data   40u  TCP localhost:53862->localhost:8001 (ESTABLISHED)
python3 3631249      jes    6u  TCP *:8001 (LISTEN)
python3 3631249      jes    7u  TCP localhost:8001->localhost:49640 (ESTABLISHED)
```

**Smoking gun:** `Recv-Q=450` on uvicorn's side of the connection from nginx port 53862. The Beast probe's POST body successfully traversed Beast LAN -> nginx :8443 -> nginx loopback -> uvicorn socket buffer. uvicorn never read the bytes (still queued in kernel) because the asyncio event loop was blocked elsewhere in `subprocess.run`. TCP is fine. TLS is fine. nginx is fine. The block is at the asyncio event loop boundary, not the network stack.

---

## Section 5 -- mcp_server.py audit (Step C.2.0.e)

Searched for source-IP gating, header checks, auth middleware: **NONE FOUND.** grep returned empty for `remote_addr|x.real.ip|x.forwarded|origin|source.ip|MCP-Protocol|protocolVersion`.

Found the anti-pattern instead. Lines 55-63:

```python
def ssh_run(host: str, command: str, timeout: int = 30) -> dict:
    ip = ALLOWED_HOSTS[host]
    user = HOST_USERS.get(host, SSH_USER)
    result = subprocess.run(
        ["ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=10", f"{user}@{ip}", command],
        capture_output=True, text=True, timeout=timeout,
    )
    return {"host": host, "command": command,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "exit_code": result.returncode}
```

Lines 96-105:

```python
@mcp.tool(name="homelab_ssh_run", annotations={...})
async def homelab_ssh_run(params: SSHRunInput) -> str:
    """Execute a shell command on a homelab node via SSH."""
    if params.host not in ALLOWED_HOSTS:
        return json.dumps({"error": f"Unknown host '{params.host}'."})
    try:
        return json.dumps(ssh_run(params.host, params.command, params.timeout), indent=2)
        #                  ^^^^^^^^^ BLOCKING CALL inside async handler
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Timed out after {params.timeout}s"})
    ...
```

No `asyncio.to_thread`, no `loop.run_in_executor`, no thread pool. Same anti-pattern in:
- `homelab_memory_search` calls sync `get_embedding` (`requests.post`) + sync `psycopg2`
- `homelab_memory_store` -- sync DB writes
- `homelab_file_read/write` -- routed via `ssh_run` (sync subprocess)
- `homelab_file_*` and other tools using ssh under the hood

Effectively every tool except those that return immediately blocks the event loop.

---

## Section 6 -- Hypothesis verdict update

| Hypothesis | Phase C.1 verdict | Phase C.2.0 verdict | Evidence |
|---|---|---|---|
| 5.A Tailscale-bound listener | DISPROVEN | DISPROVEN | unchanged (Paco confirmed `host='0.0.0.0'`) |
| 5.B header diff python-SDK vs node-MCP | PROVEN (PD's incorrect verdict) | **REVISED -- header is necessary but not sufficient; deeper cause is event-loop blocking** | Paco's CP1 showed magic header alone still hangs from Beast |
| 5.C nginx Connection upgrade rewrite | DISPROVEN | DISPROVEN | unchanged |
| 5.D source-IP-aware uvicorn | DISPROVEN | DISPROVEN | unchanged; mcp_server.py audit found no source-IP code |
| 5.E (NEW) server initialize hangs for fresh inits | CANDIDATE | **PROVEN** | py-spy stack shows event loop blocked in subprocess.run; ss shows POST body queued unread; mechanism is event-loop blocking, not init-handler malfunction |
| 5.F (NEW) nginx + non-Tailscale source asymmetry | CANDIDATE | DISPROVEN | mcp_server.py audit: no source-IP gating; nginx + uvicorn behave the same regardless of source -- the apparent asymmetry was due to Mac mini's cached session-id requests slipping through gaps between subprocess.run calls while Beast's fresh init unluckily collided with one |

**Reconciliation with Phase C.1:** PD's P1.d.3 curl probe (with magic header) DID return 200 because at that moment the event loop happened to be free. PD over-interpreted this as "header is the fix" without validating against python SDK end-to-end. Paco's counter-probes CP1/CP4 caught the gap (header alone still hangs the SDK). Phase C.2.0 closes the loop: the root cause is server-side blocking, not client-side header omission.

---

## Section 7 -- Recommendation

**STOP and file paco_request.** Server-side mcp_server.py edit needed; per directive, this requires Paco direction + Sloan single-confirm.

### Proposed fix (for paco_request -> Paco directive)

Wrap sync helpers in `asyncio.to_thread` at the async handler boundary. Minimal-diff version:

```python
import asyncio

@mcp.tool(name="homelab_ssh_run", annotations={...})
async def homelab_ssh_run(params: SSHRunInput) -> str:
    if params.host not in ALLOWED_HOSTS:
        return json.dumps({"error": f"Unknown host '{params.host}'."})
    try:
        result = await asyncio.to_thread(
            ssh_run, params.host, params.command, params.timeout
        )
        return json.dumps(result, indent=2)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Timed out after {params.timeout}s"})
    except Exception as e:
        return json.dumps({"error": str(e)})
```

Apply same pattern to:
- `homelab_memory_search` (wrap `get_embedding` + DB calls)
- `homelab_memory_store`
- `homelab_file_read/write`
- All other tools that call sync helpers

### Why this fix is sufficient

- Each tool call moves to a thread; the asyncio loop stays free to handle other connections (init, list_tools, other tool calls)
- `subprocess.run` already supports `timeout=`; thread isolation keeps that contract intact
- No protocol changes; existing clients (node-MCP, python-SDK with magic header) continue to work
- After this fix, atlas.mcp_client with `MCP-Protocol-Version: 2025-03-26` header should validate end-to-end (PD's Phase C.1 fix becomes correct in addition to this server fix)

### Why server restart is needed after fix

- Editing mcp_server.py only changes the source. The running uvicorn (PID 3631249) holds an in-memory copy of the old code
- uvicorn does not auto-reload (mcp_http.py launches with no reload=True)
- Restart sequence: SIGTERM PID 3631249 -> wait for graceful shutdown -> relaunch via `nohup python3 mcp_http.py &`. This is a Sloan single-confirm gate (Phase C.2.1 territory)

### Phase C.2.1 (uvicorn restart) -- still needed?

Debug-restart was originally framed as Phase C.2.1 IF non-restart probes were inconclusive. Probes were conclusive. **But a restart is still required** to pick up the mcp_server.py fix. Reframe Phase C.2.1 as "deploy-restart" rather than "debug-restart." Same Sloan single-confirm gate applies.

---

## Section 8 -- Anchor preservation evidence

```
--- PRE (Step 0) ---
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0

--- POST (Step Z) ---
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0

--- diff ---
ANCHORS-BIT-IDENTICAL
```

uvicorn PID 3631249 unchanged through all probes; ELAPSED `3-04:00:55` confirms no restart.

atlas.events delta:
```
--- PRE ---  embeddings=2, inference=4
--- POST --- embeddings=2, inference=4
--- delta --- 0
```

B2b nanosecond anchor and Garage S3 anchor held bit-identical for ~76+ hours since Day 71.

---

## Section 9 -- Cleanup confirmation

On CiscoKid:
- `/tmp/pyspy-diag` -- removed (rm -rf)
- `/tmp/pyspy_dump1.txt` + `_dump2.txt` + `_dump_idle.txt` -- removed (sudo rm)
- `/tmp/pyspy_install.log` -- removed
- `/tmp/c20b_status.log` + `c20de_status.log` + `c20d_lsof.txt` + `c20d_ss.txt` -- removed
- `/tmp/atlas_1f_c20b_orchestrate.sh` + `c20de.sh` -- removed
- Verification: `ls /tmp/ | grep -iE 'pyspy|c20|atlas_1f|mcp_capture|mcp-diagnostic'` -> NONE

On Beast:
- `/etc/hosts` `192.168.1.10 sloan3.tail1216a3.ts.net` -- INTACT (per directive)
- uvicorn PID 3631249 -- alive, no restart
- `/tmp/atlas_1f_p1_hangtrigger.py` + Phase C.2 anchor pre/post txt -- left for next-session reference
- Substrate containers untouched

No system packages installed on either node. No persistent state changes.

---

## Section 10 -- Cross-references

- **Original paco_request:** `docs/paco_request_atlas_v0_1_cycle_1f_transport_hang.md` (commit `1550eb2`)
- **Path C verdict:** `docs/paco_response_atlas_v0_1_cycle_1f_transport_resolved.md` (commit `560fb77`)
- **Phase C.1 directive:** `docs/handoff_paco_to_pd.md` at commit `560fb77` (cleared post-read)
- **Phase C.1 review (PD's incorrect verdict):** `docs/paco_review_atlas_v0_1_cycle_1f_phase_c1_diagnostic.md` (commit `1f6896c`)
- **Phase C.1 verdict revision:** `docs/paco_response_atlas_v0_1_cycle_1f_phase_c1_review.md` (commit `61b663b`)
- **Phase C.2 directive:** `docs/handoff_paco_to_pd.md` at commit `61b663b` (cleared post-read)
- **This paco_review:** `docs/paco_review_atlas_v0_1_cycle_1f_phase_c20_attach.md`
- **Canonical spec:** `tasks/atlas_v0_1.md` v3 section 8.1F (commit `93b97e6`)
- **Atlas package state:** unchanged from Cycle 1E close (santigrey/atlas commit `6c0b8d6`); no Atlas code written this phase
- **mcp_server.py:** read-only this phase; 357 lines; located at `/home/jes/control-plane/mcp_server.py`

---

## Section 11 -- Phase next-step readiness

Ready for Paco to issue:

1. **paco_request acknowledgment** -- file `paco_request_atlas_v0_1_cycle_1f_mcp_server_blocking.md` (PD can draft if helpful)
2. **Phase 3 fix directive** -- combined Atlas + server-side fix:
   - Server fix: edit mcp_server.py to wrap sync helpers in `asyncio.to_thread`. Sloan single-confirm gate.
   - uvicorn redeploy (kill PID 3631249, relaunch). Sloan single-confirm gate.
   - Atlas fix (PD's Phase C.1 client-side fix carries forward): atlas.mcp_client with `MCP-Protocol-Version: 2025-03-26` header. PD authority.
   - Smoke validation: Beast python-SDK probe -> tools_count > 0 AFTER both fixes
3. **All other Cycle 1F gates** carry forward from original handoff (4 tests, atlas.events token logging, Beast anchor diff, secret-grep audit)

PD recommends combining all fixes in one Phase 3 commit on Atlas side + one mcp_server.py commit on control-plane side. Substrate containers remain untouched (uvicorn is not a substrate anchor).

No close-out fold this turn; open block stays open until Phase 3 fix lands and Cycle 1F build resumes from Step 4 onward.
