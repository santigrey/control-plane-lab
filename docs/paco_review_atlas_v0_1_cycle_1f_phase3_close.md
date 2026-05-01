# paco_review_atlas_v0_1_cycle_1f_phase3_close

**Spec:** Atlas v0.1 Cycle 1F Phase 3 (combined fix + deploy-restart + close-out)
**Step:** Phase 3 CLOSE (Steps 1-17 + Z complete)
**Status:** AWAITING PACO FIDELITY CONFIRMATION + CYCLE 1F CLOSE RATIFICATION
**Predecessor:** `docs/handoff_paco_to_pd.md` (cleared after read per P6 #26 protocol)
**Predecessor responses (Phase 3 saga):** `paco_response_atlas_v0_1_cycle_1f_phase3_pretest_flake.md` (commit `eadc2e7`) / `paco_response_handoff_protocol_p6_26.md` (commit `7910b3b`) / `paco_response_atlas_v0_1_cycle_1f_phase3_handler_count_reconciliation.md` (commit `77759f8`) / `paco_response_atlas_v0_1_cycle_1f_phase3_args_wrapping.md` (commit `6eaab4e`)
**Author:** PD (JesAir-side after Cortez handoff)
**Date:** 2026-05-01 UTC (Day 76 night)
**Target hosts:** CiscoKid (server-side patch + uvicorn restart) + Beast (atlas client + tests + commits)

---

## 0. Verified live (per 5th standing rule)

### Anchors PRE/POST Phase 3

```
# PRE (per handoff Section 1, captured by Paco at directive author):
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z healthy 0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z healthy 0

# POST (this turn, after Steps 11-13):
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z healthy 0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z healthy 0
```

BIT-IDENTICAL nanosecond match. **96+ hours of operational time, both anchors held.** No Beast Docker stack disturbed during Phase 3 client-side work.

### atlas.events PRE/POST

```
# PRE (per handoff Section 1): atlas.embeddings=2, atlas.inference=4 (rows have grown during testing; absolute count uninformative now)
# POST (this turn, after Step 11 retry + Step 12 pytest):
  atlas.embeddings=12, atlas.inference=14, atlas.mcp_client=4 (NEW source)
```

Delta: atlas.mcp_client source appeared (+4 rows from this turn's smoke + pytest). 2 tools_list + 2 tool_call kinds.

### uvicorn old/new PIDs

```
OLD: 3631249 (pre-Step-9 deploy-restart)
NEW: 3333714 (post-Step-9 deploy-restart since Fri 2026-05-01 03:11:03 UTC; PID confirmed by handoff verification)
```

### systemd status

```
homelab-mcp.service: active (running) since Fri 2026-05-01 03:11:03 UTC
MainPID: 3333714 (NEW patched code with asyncio.to_thread wraps)
```

### mcp_server.py post-patch line counts

```
mcp_server.py:                NEW patched, 388 lines, md5 fae7ccf759c94fc632751898865ca3d2
mcp_server.py.bak.phase3:     OLD pre-patch, 357 lines
Delta: +31 lines (1 import asyncio + 13 handlers wrapped + comment lines)
```

### atlas package post-build state

Commit `5a9e458` on `santigrey/atlas` `main`:
- `src/atlas/mcp_client/__init__.py` (1156 bytes)
- `src/atlas/mcp_client/client.py` (post-Option-B; ~233 lines)
- `src/atlas/mcp_client/acl.py` (post-Refinement-2; ~69 lines)
- `src/atlas/mcp_client/client.py.bak.phase3` (rollback artifact, 213 lines OLD pre-Option-B)
- `src/atlas/mcp_client/acl.py.bak.phase3` (rollback artifact, 65 lines OLD pre-Refinement-2)
- `tests/mcp_client/{__init__,test_mcp_acl,test_mcp_connect,test_mcp_token_logging,test_mcp_tool_call}.py`

**Process observation:** atlas .bak.phase3 files swept into commit per handoff's literal `git add src/atlas/mcp_client/` (no exclusion clause). Asking Paco discretion in section 11 for whether to clean via follow-up commit or treat as canonical rollback-trail (matches mcp_server.py.bak.phase3 pattern in control-plane-lab Step 15.b).

### Mac mini reconnect evidence

Per handoff Section 1: 200s in nginx log from `100.102.87.70` post-restart timestamp. Cortez + Mac mini clients reconnected post-Step-9 cleanly (verified at handoff author time, not re-verified this turn since out of scope).

### Beast end-to-end smoke result (Step 11 retry)

```
SMOKE INITIALIZE_OK
SMOKE tools_count: 13
SMOKE has_homelab_ssh_run: True
SMOKE has_homelab_file_write: True
SMOKE tool_call result_str_contains_jes: True
SMOKE tool_call result snippet: ... "stdout": "jes", "stderr": "", "exit_code": 0 ...
```

**Step 11 retry: ALL GATES PASS** post-Option B.

Plus telemetry logs confirmed Refinement 3 working: `arg_keys=['command', 'host']` (caller-provided), NOT `['params']` post-wrap.

---

## 1. TL;DR -- Cycle 1F CLOSED 5/5 PASS

Atlas Cycle 1F (MCP client gateway from Atlas to homelab MCP server) is shipped end-to-end. Server-side asyncio.to_thread fix landed at Step 2 (commit at Phase 3 close-out fold this turn). Client-side schema-aware auto-wrap (Option B) implemented per Paco ratification commit `6eaab4e`. End-to-end smoke from Beast through nginx HTTPS to CK MCP returns valid `{"stdout": "jes"}` from `homelab_ssh_run({host: ciscokid, command: whoami})`. 20/20 pytest pass (16 prior + 4 new mcp_client; Step 7's amended count of 15 was off by +1 -- minor count drift documented in section 11). 0 secrets-discipline hits in atlas.events. Both Beast nanosecond anchors bit-identical post Phase 3.

6 P6 lessons banked from the saga (#21-#26). Standing rule (5 guardrails + carve-out) applied through 7 escalations + 1 correction this saga. Cycle 1F CLOSED ratification awaiting Paco confirm.

---

## 2. Cycle 1F 5-gate scorecard

| Gate | Wording | Result |
|---|---|---|
| 1 | mcp_server.py imports asyncio + 13 `@mcp.tool` handlers wrap sync helpers in `asyncio.to_thread` | **PASS** -- verified by inspect.getsource on homelab_ssh_run + spot-check 2 others (homelab_memory_search + homelab_get_profile + homelab_agent_status all show `to_thread=True, _sync_impl=True` per handoff Section 2) |
| 2 | Atlas client imports cleanly with `MCP_PROTOCOL_VERSION="2025-03-26"` AND `_tool_schemas` populated post-`__aenter__` | **PASS** -- live import + smoke confirms tools_count=13 returned from cached `_tool_schemas` lookup |
| 3 | Deploy-restart succeeded: new uvicorn PID 3333714 != old 3631249; systemd active running; Mac mini 200s in nginx log post-restart | **PASS** -- per handoff Section 1 verification |
| 4 | End-to-end Beast smoke retry: `INITIALIZE_OK` + `tools_count >= 13` + `has_homelab_ssh_run/file_write: True` + `tool_call result_str_contains_jes: True` | **PASS** -- this turn's Step 11 retry verified |
| 5 | ACL deny test: `homelab_file_write` to `/home/jes/control-plane/...` raises `AtlasAclDenied` BEFORE network call; `tool_call_denied` row in atlas.events | **PASS** -- via pytest test_acl_denies_control_plane_write (1 of 4 mcp_client tests; passing in 20/20 suite) |

**Standing gate (B2b + Garage anchors bit-identical):** PASS (96+ hours preserved through entire Phase 3 saga).

Plus:
- 20 pytest passing (16 prior + 4 new mcp_client) -- amended count, see section 7
- secret-grep on staged diff (atlas commit `5a9e458`): CLEAN
- atlas.events arg-value secrets discipline: 0 hits on `whoami` (count=0) + 0 hits on `ciscokid` (count=0)
- atlas.events `arg_keys` field shows `["command", "host"]` (caller-provided), NOT `["params"]` -- Refinement 3 verified working
- B2b subscription `controlplane_sub` untouched (anchors held)
- Garage cluster status unchanged

**Cycle 1F internal scorecard: 5/5 PASS + standing PASS.**

---

## 3. Server-side patch summary (Steps 2 + 3)

Applied to `/home/jes/control-plane/mcp_server.py` (Cortez session, before this PD instance picked up):

- 1 import added: `import asyncio`
- 13 `@mcp.tool` handlers wrapped sync helpers in `asyncio.to_thread(...)`:
  - 10 handlers use `_sync_impl()` inner-function pattern
  - 3 handlers use direct ssh_run wrap pattern
- Ratified count: **13** handlers (handler count reconciliation commit `77759f8`; amended from directive's original 14)
- Backup preserved at `/home/jes/control-plane/mcp_server.py.bak.phase3` (357 lines, OLD pre-patch code; gitignored per `*.bak` pattern but explicitly tracked in this commit per handoff Step 15.b)

Deployed at Step 9 via `sudo systemctl restart homelab-mcp.service`. New uvicorn PID 3333714 alive since Fri 2026-05-01 03:11:03 UTC.

---

## 4. Atlas-side patch + module + 4 tests

Landed in commit `5a9e458` on `santigrey/atlas` `main`:

### 4.1 atlas.mcp_client module (3 source files)

- `__init__.py` -- public API exports for ACL_DENY_PATTERNS, AclDenyPattern, AtlasAclDenied, DEFAULT_HEADERS, DEFAULT_MCP_URL, MCP_PROTOCOL_VERSION, McpClient, check_acl, get_mcp_client
- `acl.py` -- ACL_DENY_PATTERNS list with 1 pattern (homelab_file_write under /home/jes/control-plane/), `AtlasAclDenied` exception, `check_acl(tool_name, arguments)` function
- `client.py` -- `McpClient` async context manager: __init__/__aenter__/__aexit__/list_tools/call_tool/_log_event

### 4.2 Schema-aware args auto-wrap (Option B per ratification commit `6eaab4e`)

Applied this turn per handoff Section 4 + Refinements 1+2+3:

**client.py changes (+20 lines, 213 -> 233):**
1. `__init__`: added `self._tool_schemas: dict[str, dict] = {}`
2. `__aenter__`: after `await self._session.initialize()`, populate `self._tool_schemas` via `await self._session.list_tools()` (Refinement 1 -- cache schemas at __aenter__)
3. `call_tool`: capture `caller_arg_keys = sorted(args.keys())` BEFORE auto-wrap (Refinement 3); apply auto-wrap if schema requires `params` and caller hasn't pre-wrapped; ACL check on (possibly wrapped) args
4. 3 telemetry payloads (tool_call_denied, tool_call success, tool_call error): replaced `sorted(args.keys())` with `caller_arg_keys` (Refinement 3 enforcement)

**acl.py changes (+4 lines, 65 -> 69):**
5. `check_acl`: looks in top-level args AND nested `params` (Refinement 2 -- handles auto-wrapped form)

### 4.3 4 tests at `tests/mcp_client/`

- `test_mcp_connect.py` -- async smoke: connect + list_tools returns nonempty
- `test_mcp_tool_call.py` -- async smoke: `homelab_ssh_run({host:ciscokid, command:whoami})` returns `"jes"` via auto-wrap
- `test_mcp_acl.py` -- ACL denies write to /home/jes/control-plane/ BEFORE network
- `test_mcp_token_logging.py` -- audits no arg values in atlas.events payload

All 4 tests PASS via 20/20 pytest run (Step 12).

---

## 5. Deploy-restart evidence (Step 9)

Per handoff Section 1 + 2.6: `sudo systemctl restart homelab-mcp.service` SUCCESS at Fri 2026-05-01 03:11:03 UTC. Pre-PID 3631249 -> Post-PID 3333714 (NEW). Mac mini + Cortez clients reconnected with 200s post-restart from nginx log. New code (asyncio.to_thread wraps) live confirmed by this conversation's MCP tooling responsive again post-restart (the 4-min hangs that prompted the saga were the symptom of the unwrapped sync calls; gone after restart).

---

## 6. End-to-end smoke saga (Step 11 initial fail + post-Option-B retry pass)

### 6.1 Step 11 initial (Cortez session)

```
SMOKE INITIALIZE_OK                      # PASS
SMOKE tools_count: 13                    # PASS
SMOKE has_homelab_ssh_run: True          # PASS
SMOKE has_homelab_file_write: True       # PASS
SMOKE tool_call result: # FAIL
  Error executing tool homelab_ssh_run: 1 validation error
  params: Field required [type=missing, ...]
```

Diagnosis: FastMCP advertises `inputSchema` with `required: ["params"]` for Pydantic-wrapped handlers. atlas.mcp_client was passing `arguments` verbatim through `mcp.ClientSession.call_tool(name, arguments)` without wrap. Diagnostic call with `{"params": {"host": ..., "command": ...}}` returned proper `{"stdout": "jes", ...}`.

PD escalated via `paco_request_atlas_v0_1_cycle_1f_phase3_args_wrapping.md` with 3 options (A=test+ACL update / B=schema-aware auto-wrap / C=server refactor). Paco ratified Option B at commit `6eaab4e` with 3 refinements.

### 6.2 Step 11 retry (post-Option B implementation, this turn)

```
SMOKE INITIALIZE_OK
SMOKE tools_count: 13
SMOKE has_homelab_ssh_run: True
SMOKE has_homelab_file_write: True
SMOKE tool_call result_str_contains_jes: True   <-- now PASS
SMOKE tool_call result snippet: ... "stdout": "jes", "stderr": "", "exit_code": 0 ...
```

**Step 11 retry: ALL GATES PASS.**

Telemetry confirms Refinement 3 working: `arg_keys=['command', 'host']` in atlas.events row (caller-provided keys, NOT `['params']` post-wrap).

---

## 7. pytest output (Step 12)

```
....................                                                     [100%]
=============================== warnings summary ===============================
tests/mcp_client/test_mcp_acl.py::test_acl_denies_control_plane_write
tests/mcp_client/test_mcp_connect.py::test_connect_and_list_tools
tests/mcp_client/test_mcp_token_logging.py::test_token_logging_no_arg_values
tests/mcp_client/test_mcp_tool_call.py::test_homelab_ssh_run_whoami
  /usr/lib/python3.11/contextlib.py:105: DeprecationWarning: Use `streamable_http_client` instead.
    self.gen = func(*args, **kwds)

20 passed, 4 warnings in 8.68s
```

**20 passed in 8.68s.**

Count discrepancy with handoff: handoff Step 12 expected 19 (Step 7 amended count of 15 + 4 new). Actual: 20 (16 prior + 4 new). +1 prior test discrepancy. Possible causes: (a) Step 7 ground-truth recount happened to land at 15 due to a discovery flake; (b) a test was added between Step 7 and now; (c) some other minor accounting. Not a halt-condition; flagging for Paco awareness. Suggested resolution: ground-truth recount at next pytest run; if 16 stays, document as the accurate Step-7-snapshot retroactive correction.

4 DeprecationWarnings about `streamable_http_client` (note the underscore vs hyphen spelling in the warning -- mcp library version drift). Not blocking; bank as v0.2 P5 candidate.

All 4 mcp_client tests PASSED individually (warnings list confirms each test name with its module path).

---

## 8. atlas.events sample by source + secrets discipline audit (Step 13)

### 8.1 Source counts

```
      source      | count 
------------------+-------
 atlas.embeddings |    12
 atlas.inference  |    14
 atlas.mcp_client |     4
```

Delta from handoff PRE: atlas.mcp_client +4 (NEW source); atlas.embeddings +10; atlas.inference +10. Embeddings + inference deltas are from prior Cycle 1E activity, not this turn.

### 8.2 atlas.mcp_client recent rows (last 4)

```
    kind    |      tool       |      arg_keys       | status  | dur_ms 
------------+-----------------+---------------------+---------+---------
 tool_call  | homelab_ssh_run | ["command", "host"] | success | 647.088
 tools_list |                 | []                  | success | 22.561
 tool_call  | homelab_ssh_run | ["command", "host"] | success | 250.956
 tools_list |                 | []                  | success | 23.057
```

**arg_keys field shows `["command", "host"]`** -- Refinement 3 verified. If Refinement 3 had not been applied, arg_keys would be `["params"]` (the post-wrap form). The pre-wrap caller-provided keys preserved through telemetry as designed.

### 8.3 Secrets discipline audit

```
=== whoami in any atlas.mcp_client payload (must be 0) ===
 count: 0
=== ciscokid in any atlas.mcp_client payload (must be 0) ===
 count: 0
```

Both audits PASS. Tool argument VALUES (whoami, ciscokid) never persisted to atlas.events. Only keys + structural metadata.

---

## 9. Anchor preservation (bit-identical diff)

```
PRE-Phase-3:
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z healthy 0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z healthy 0

POST-Phase-3 (this turn, captured immediately before Step 15.a Atlas commit):
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z healthy 0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z healthy 0
```

BIT-IDENTICAL nanosecond match. **96+ hours of operational time, both anchors held through the entire Phase 3 saga (transport hang + Path C verdict + Phase C.1 + Phase C.2.0 + Phase 3 GO + handler count reconciliation + P6 #26 banking + pretest flake + args wrapping + Cortez handoff + JesAir resume).**

---

## 10. P6 lessons appended to feedback file (Step 17)

Per handoff Step 17, the canonical block of P6 #21-#26 has been appended to `/home/jes/control-plane/docs/feedback_paco_pre_directive_verification.md`. Cumulative count: P6 lessons banked = 26 (was 20 at start of Phase 3).

New lessons:
- **#21** -- tcpdump-on-lo for client-server impedance (Phase C.1 P1.c)
- **#22** -- PD diagnostic verdicts must validate end-to-end against runtime path (Phase C.1 verdict gap)
- **#23** -- Verify launch mechanism before authoring restart commands (Phase C.2.0 nohup-vs-systemd)
- **#24** -- Recursive observer effect during long-running diagnostics (Phase C.1 + Step 7 flake)
- **#25** -- Hedge propagation discipline (handler count + prior-test count both off-by-one)
- **#26** -- All Paco<->PD events write notification line in handoff_pd_to_paco.md (this turn applies it)

All six are direct applications of 5th standing rule's principles.

---

## 11. Cross-references + observations + asks of Paco

### Cross-references

- **Cycle 1F GO**: `paco_response_atlas_v0_1_cycle_1f_phase_c20_confirm_phase3_go.md`
- **Phase C.1 + C.2.0 lineage**: `paco_request_atlas_v0_1_cycle_1f_transport_hang.md` + `paco_response_atlas_v0_1_cycle_1f_phase_c1_review_revision.md`
- **Handler count reconciliation**: `paco_response_atlas_v0_1_cycle_1f_phase3_handler_count_reconciliation.md` (commit `77759f8`)
- **P6 #26 protocol banking**: `paco_response_handoff_protocol_p6_26.md` (commit `7910b3b`)
- **Step 7 pretest flake ruling**: `paco_response_atlas_v0_1_cycle_1f_phase3_pretest_flake.md` (commit `eadc2e7`)
- **Step 11 args wrapping ruling**: `paco_response_atlas_v0_1_cycle_1f_phase3_args_wrapping.md` (commit `6eaab4e`)
- **Pre-deploy checkpoint** (untracked, audit trail): `paco_request_atlas_v0_1_cycle_1f_phase3_pre_deploy.md`
- **JesAir resume handoff** (cleared post-read per P6 #26): `handoff_paco_to_pd.md`
- **Atlas commit**: `5a9e458` on `santigrey/atlas` main

### Observations for Paco discretion

1. **.bak.phase3 inclusion in atlas commit `5a9e458`**: PD's literal interpretation of handoff's `git add src/atlas/mcp_client/` swept in the rollback artifacts (client.py.bak.phase3 + acl.py.bak.phase3). They're now in canon. This matches mcp_server.py.bak.phase3 inclusion in the control-plane-lab close-out fold (Step 15.b). Asking Paco discretion: keep as canonical rollback-trail (current state) OR follow-up commit removes via `git rm` + .gitignore `*.bak.*` pattern? PD bias: keep, matches mcp_server.py.bak.phase3 pattern for symmetry.
2. **pytest count drift**: 20 actual vs 19 expected (Step 7's amended count of 15 was off by +1; actual prior is 16). Suggested resolution: document as retroactive Step-7-recount; ratify 20 as the new baseline.
3. **DeprecationWarning on streamable_http_client**: 4 warnings about `streamable_http_client` (vs `streamablehttp_client` we're using). Bank as v0.2 P5 candidate (mcp library version drift).

### Asks of Paco

1. **Confirm Cycle 1F 5/5 PASS** against captured evidence (sections 0 + 2 + 6 + 7 + 8 + 9).
2. **Rule on observation 1** (.bak.phase3 in atlas commit): keep as-is OR follow-up cleanup commit.
3. **Rule on observation 2** (pytest count drift): document-and-move-on OR investigate the +1 source.
4. **Acknowledge P6 #21-#26 banking** in `feedback_paco_pre_directive_verification.md`.
5. **Authorize Cycle 1F CLOSED**: trigger transition out of Cycle 1F into next Atlas cycle (Cycle 1G or whatever Paco's plan calls for next).

---

## Status

**AWAITING PACO FIDELITY CONFIRMATION + CYCLE 1F CLOSE RATIFICATION.**

PD paused. Atlas commit `5a9e458` shipped. control-plane-lab close-out commit pending (this paco_review + feedback file P6 banking + SESSION + anchor + CHECKLIST in Step 15.b fold). Substrate anchors preserved through entire Phase 3 saga (96+ hours bit-identical).

-- PD
