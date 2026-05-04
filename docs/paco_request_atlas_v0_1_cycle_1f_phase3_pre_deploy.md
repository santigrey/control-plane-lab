# paco_request_atlas_v0_1_cycle_1f_phase3_pre_deploy

**Spec:** Atlas v0.1 Cycle 1F Phase 3 (combined fix + deploy-restart + build close)
**Step:** Step 8 mid-cycle safety-harness checkpoint, BEFORE Step 9 deploy-restart
**Status:** CHECKPOINT (not an escalation; documenting clean PRE-restart state for audit trail). PD authorized by Paco ruling `eadc2e7` to proceed to Step 9.
**Predecessor:** `docs/paco_response_atlas_v0_1_cycle_1f_phase3_pretest_flake.md` (HEAD `eadc2e7`); `docs/paco_response_atlas_v0_1_cycle_1f_phase3_handler_count_reconciliation.md` (commit `77759f8`); `docs/paco_response_handoff_protocol_p6_26.md` (commit `7910b3b`); `docs/paco_response_atlas_v0_1_cycle_1f_phase_c20_confirm_phase3_go.md`
**Author:** PD (Cortez session)
**Date:** 2026-04-30 / 2026-05-01 UTC (Day 76 night)
**Target host:** CiscoKid (uvicorn restart) + Beast (atlas test target)

---

## TL;DR

All Steps 1-7 complete with Paco rulings ratified. Phase 3 PRE-restart state is clean. PD ready to fire `sudo systemctl restart homelab-mcp.service` per Step 9 single-confirm gate.

This file is the safety-harness audit trail. If Step 9 + Step 10 + Step 11 fail, this file proves the pre-restart state was clean and rollback is `mv mcp_server.py.bak.phase3 mcp_server.py + sudo systemctl restart homelab-mcp.service`.

## 1. Server-side patch state (Steps 2 + 3)

- **`/home/jes/control-plane/mcp_server.py`** (NEW patched code on disk, 19,520 bytes / 388 lines, md5 `fae7ccf759c94fc632751898865ca3d2`)
  - 1 import added: `import asyncio`
  - 13 @mcp.tool handlers wrapped with `await asyncio.to_thread(...)` (10 use `_sync_impl` pattern, 3 use direct ssh_run wrap)
  - Ratified count: 13 handlers (Paco ratification commit `77759f8` -- amended from directive's 14)
- **`/home/jes/control-plane/mcp_server.py.bak.phase3`** (OLD code preserved, 18,431 bytes / 357 lines)
- Step 3 syntactic validation PASSED: `import mcp_server; from mcp_server import mcp` -- 30 attrs; `inspect.getsource(homelab_ssh_run)` confirms `asyncio.to_thread` present; spot-check on `homelab_memory_search` + `homelab_get_profile` + `homelab_agent_status` all show `to_thread=True, _sync_impl=True`.
- mcp_server.py.bak.phase3 is gitignored per `.gitignore:21 *.bak`.

## 2. Atlas client-side build state (Steps 4-6)

- **`/home/jes/atlas/src/atlas/mcp_client/`** (3 source files, NEW)
  - `__init__.py` (1156 bytes) -- public API exports
  - `acl.py` (1961 bytes) -- `AtlasAclDenied`, `AclDenyPattern`, `ACL_DENY_PATTERNS`, `check_acl()`
  - `client.py` (7594 bytes) -- `McpClient` async context manager + telemetry + integrated `MCP-Protocol-Version: 2025-03-26` header
- **`/home/jes/atlas/tests/mcp_client/`** (5 files: 1 empty `__init__.py` + 4 test files: connect, tool_call, acl, token_logging; total 5731 bytes)
- Step 6 syntactic validation PASSED: `from atlas.mcp_client import McpClient, MCP_PROTOCOL_VERSION, AtlasAclDenied, ACL_DENY_PATTERNS, check_acl, get_mcp_client, DEFAULT_MCP_URL, DEFAULT_HEADERS` all imported cleanly.
- ACL positive test (path under control-plane): raises `AtlasAclDenied` correctly.
- ACL negative test (path under /tmp/): allow passes correctly.

## 3. Prior-test snapshot state (Step 7, post-Paco-ruling `eadc2e7`)

- Step 7 amended gate: **15** prior tests (was 16 in directive; off-by-one resolved via Paco ratification).
- Run 1 (PD, this Cortez session): 13 passed + 2 failed under contended async event-loop (recursive observer P6 #24).
- Runs 2/3/4 (Paco, controlled reruns): **15/15 PASS** in 7.27s / 7.36s / 7.36s.
- Isolation run (just the 2 failing tests alone): **2/2 PASS** in 1.05s.
- Flake banked as **v0.2 P5 #12**. Root cause: race in `count(*)` snapshots under contended async commits in psycopg pool.

Step 7 amended gate 15/15 PASS satisfied (per Paco rulings 2.1 + 2.2 in commit `eadc2e7`).

## 4. Substrate state

- **B2b nanosecond anchor:** `2026-04-27T00:13:57.800746541Z` -- bit-identical, holding 76+ hours through Cycles 1A-1E + Cycle 1F BLOCK + Phase C.1 + Phase C.2.0 + Phase 3 GO + Phase 3 Steps 1-7
- **Garage anchor:** `2026-04-27T05:39:58.168067641Z` -- bit-identical, holding 76+ hours
- **atlas.events PRE (per Verified live block):** embeddings=2, inference=4 (now grown to embeddings=10, inference=12 per Paco's Verified live row 8 reflecting reruns -- no Phase 3 mutation; rows are append-only audit log entries from test runs)
- **uvicorn MainPID 3631249** alive, 3+ days uptime, OLD code still running (no restart yet)
- **systemd unit:** `/etc/systemd/system/homelab-mcp.service` Type=simple Restart=always User=jes WorkingDirectory=/home/jes/control-plane ExecStart=/usr/bin/python3 mcp_http.py
- **HEAD on control-plane-lab:** `eadc2e7` (Paco ruling Step 7 + Phase 3 advance authorization)
- **HEAD on atlas:** `6c0b8d6` (Cycle 1E close, unchanged from pre-Phase-3)

## 5. Standing rule + protocol compliance

- 5-guardrail rule: 2 PD-side defensive escalations this cycle (handler count + pretest flake), both ratified by Paco. No silent self-corrections on auth/security boundaries.
- 5th standing rule (Verified live blocks): mandatory at Step 16 paco_review §0.
- P6 #26 protocol (banked at `7910b3b`): notification lines in handoff_pd_to_paco.md for ALL Paco<->PD events. This file's existence triggers a notification line.
- Secrets discipline: mosquitto password in Phase C close-out fully redacted (`61ff118`). atlas.mcp_client tests at Step 12 will assert NO arg values in atlas.events payloads ("whoami", "ciscokid" tested literally).

## 6. Step 9 deploy-restart readiness

Ready to fire:
```
OLD_PID=$(pgrep -af mcp_http.py | head -1 | awk '{print $1}')   # capture 3631249
sudo systemctl restart homelab-mcp.service
sleep 5
NEW_PID=$(pgrep -af mcp_http.py | head -1 | awk '{print $1}')
echo "PIDs differ (good): $([[ \"$OLD_PID\" != \"$NEW_PID\" ]] && echo YES || echo NO)"
sudo systemctl status homelab-mcp.service --no-pager | head -10
sudo ss -tlnp | grep ':8001'
```

Expected:
- `Active: active (running)` immediately post-restart
- New MainPID != 3631249
- Port 8001 listening on new PID
- Mac mini Tailscale source `100.102.87.70` will see ~30s MCP unavailability then auto-reconnect (Step 10 verifies)
- This conversation's homelab_ssh_run + homelab_file_write tooling will drop briefly then reconnect

Rollback if Step 9 fails:
```
mv /home/jes/control-plane/mcp_server.py.bak.phase3 /home/jes/control-plane/mcp_server.py
sudo systemctl restart homelab-mcp.service
```
This restores pre-Phase-3 state in <30s.

## 7. CEO single-confirm gate

CEO's original trigger "Read docs/handoff_paco_to_pd.md and execute" stands as the single-confirm for the entire Phase 3 cycle including Step 9 deploy-restart per directive §0:

> *Reads PD authority through Step 11; Step 9 deploy-restart is the Sloan-confirm gate (the trigger itself authorizes it).*

No additional CEO confirm required to fire the restart.

## 8. Substrate impact (none expected)

uvicorn restart is a Python process restart on CiscoKid only. Does NOT touch:
- control-postgres-beast container (Beast 192.168.1.152:5432) -- B2b anchor preserved
- control-garage-beast container (Beast 192.168.1.152:3900) -- Garage anchor preserved
- B2b subscription `controlplane_sub` -- Postgres logical replication preserved
- Any other systemd service on any node

Step 14 anchor POST diff will confirm bit-identity.

---

**File:** `/home/jes/control-plane/docs/paco_request_atlas_v0_1_cycle_1f_phase3_pre_deploy.md` (untracked, transient until close-out per correspondence triad standing rule)

-- PD
