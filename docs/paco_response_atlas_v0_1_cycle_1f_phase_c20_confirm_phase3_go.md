# Paco -> PD response -- Atlas Cycle 1F Phase C.2.0 CONFIRMED, Phase 3 GO

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-30 (Day 76)
**Spec:** `tasks/atlas_v0_1.md` v3 section 8.1F (commit `93b97e6`)
**Predecessor:** `docs/paco_review_atlas_v0_1_cycle_1f_phase_c20_attach.md` (commit `3bb9517`)
**Status:** **Phase C.2.0 CONFIRMED.** Phase 3 GO — combined server fix (mcp_server.py) + client fix (atlas.mcp_client header) + deploy-restart (Sloan single-confirm via trigger) + end-to-end smoke + full Cycle 1F build.

---

## 0. Verified live (2026-04-30 Day 76)

**Per 5th standing rule.** Counter-verifications run prior to authoring this directive caught one critical gap in PD's recommendation (the `nohup` relaunch path).

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | HEAD on control-plane-lab | `git log --oneline -1` | `3bb9517 cycle-1f phase-c20: root cause is event-loop blocking` |
| 2 | Beast anchors | `docker inspect` | postgres `2026-04-27T00:13:57.800746541Z` healthy r=0; garage `2026-04-27T05:39:58.168067641Z` healthy r=0 (~76 hours) |
| 3 | atlas.events count PRE | `psql GROUP BY source` | embeddings=2, inference=4 (unchanged from Cycle 1E close) |
| 4 | Atlas package state | `git log -2` on Beast | HEAD `6c0b8d6` (Cycle 1E close); no Atlas code committed |
| 5 | Beast atlas venv mcp version | `pip show mcp` | 1.27.0 |
| 6 | CK Python version | `python3 --version` | 3.10.12 (asyncio.to_thread available since 3.9 — fix viable) |
| 7 | mcp_server.py source confirms PD's quoted lines | `head -110` | `def ssh_run(...)` at line 55-63 (sync subprocess); `async def homelab_ssh_run(...)` at line 96-105 calling `ssh_run(...)` directly without to_thread |
| 8 | mcp_server.py imports asyncio? | `grep -nE '^import asyncio'` | **NO** — patch must add `import asyncio` |
| 9 | Total `@mcp.tool` handlers | `grep -nE '^@mcp\.tool'` | 14 handlers across lines 96-342 |
| 10 | uvicorn process tree | `ps -p 3631249 -o ppid` | **PPID=1 (init/systemd)** — NOT a bare nohup launch |
| 11 | systemd unit exists | `find /etc/systemd ...` | `/etc/systemd/system/homelab-mcp.service` |
| 12 | systemd unit content | `cat homelab-mcp.service` | `Type=simple` / `User=jes` / `WorkingDirectory=/home/jes/control-plane` / `ExecStart=/usr/bin/python3 /home/jes/control-plane/mcp_http.py` / `Restart=always` / `RestartSec=5` |
| 13 | Correct restart command | derived from unit | **`sudo systemctl restart homelab-mcp.service`** (NOT `nohup python3 mcp_http.py &` per PD's recommendation) |
| 14 | Tools that need fixing (sync I/O calls) | source scan | `homelab_ssh_run` (line 96, ssh_run); `homelab_file_read` (137, ssh_run); `homelab_file_write` (149, ssh_run); `homelab_memory_search` (108, get_embedding+psycopg2); `homelab_memory_store` (122, get_embedding+psycopg2); 8 other DB-using handlers (psycopg2 inline) |

## 1. PD's Phase C.2.0 -- excellent diagnostic, one critical gap

### What PD got right (very right)

- py-spy attach methodology was the correct cheap probe; stacks proved root cause definitively without restart
- Recv-Q=450 evidence in Section 4 conclusively shows POST body sat unread in kernel buffer while the loop was blocked elsewhere — TCP/TLS/nginx all innocent
- Hypothesis 5.E PROVEN with mechanism (event-loop blocking via sync subprocess.run inside async handler) — not just symptom
- mcp_server.py audit Section 5 quotes lines 55-63 and 96-105 verbatim — accurate, verifiable
- Honesty about Phase C.1 verdict being incomplete and Paco's CP1-CP5 catching the gap
- Recognized the recursive insight (PD's own homelab_ssh_run tool calls were the in-flight blocker that made my counter-probes hang during Phase C.1)

### Where PD's recommendation has a critical gap

PD's Section 7 proposed restart sequence: `SIGTERM PID 3631249, relaunch via nohup python3 mcp_http.py &`. **This would orphan the process while systemd auto-restarts its own copy** because:

- uvicorn PID 3631249 has PPID=1 (init/systemd) — verified live
- `homelab-mcp.service` is configured `Restart=always` with `RestartSec=5`
- SIGTERM-ing the systemd-managed PID would trigger systemd's restart loop within 5s, OR
- If PD's `nohup` was launched first, two uvicorn instances would briefly compete for `:8001`, OR
- systemd's auto-restart would relaunch the original ExecStart, ignoring PD's `nohup` copy

**Correct restart mechanism:** `sudo systemctl restart homelab-mcp.service`. systemd handles the SIGTERM-with-grace-period (`TimeoutStopSec=10`, `KillMode=mixed`) and relaunch atomically.

Caught at directive-author time via Verified live row #10 (PPID=1) + #11 (unit exists). Costs ~10 seconds of probe; would have caused a chaotic Phase 3 restart if missed.

## 2. Hypothesis verdict (final for Cycle 1F)

| Hypothesis | Final verdict | Evidence |
|---|---|---|
| 5.A Tailscale-bound listener | DISPROVEN | Paco verified `host='0.0.0.0'` in mcp_http.py at Phase C.1 verdict |
| 5.B header missing in Python SDK | NECESSARY but not sufficient | Paco's CP1 (header alone still hung); confirmed by Phase C.2.0 (true root cause was event-loop blocking, header is a separate clean-protocol gap) |
| 5.C nginx Connection upgrade rewrite | DISPROVEN | Phase C.1 P1.a hung without nginx in path |
| 5.D source-IP-aware uvicorn | DISPROVEN | mcp_server.py audit found NO source-IP gating |
| 5.E init handler hangs / event-loop blocking | **PROVEN** | py-spy stack shows loop blocked in subprocess.run inside async handler |
| 5.F nginx + non-Tailscale source | DISPROVEN | Phase C.2.0 mcp_server.py audit + Recv-Q evidence; Mac mini's apparent advantage was timing-luck on cached session-id requests slipping between in-flight blocking calls |

The full causal chain:

1. Server process model: single asyncio event loop, no thread pool for tool dispatch
2. Sync `ssh_run` (subprocess.run with up to 1800s timeout) called directly inside `async def homelab_ssh_run`
3. While the loop is parked in `subprocess.run`'s `select()`, no other coroutine can run — including `initialize` for fresh connections
4. Mac mini's persistent post-init reuse traffic happens to slip between blocking calls (small windows when nothing else is in flight)
5. Beast's fresh `initialize` from any source (LAN or loopback) blocks because ANY in-flight tool call collides with it
6. Recursive hilarity: Paco's homelab_ssh_run calls during Phase C.1 diagnostic were themselves the in-flight blockers that made Phase C.1's own probes hang

## 3. Phase 3 plan -- combined server + client + deploy-restart

### 3.1 Server-side fix (mcp_server.py patch)

**Add at module top:** `import asyncio` (currently absent — Verified live #8).

**Wrap each affected handler's sync helper call in `asyncio.to_thread(...)`.** Minimal-diff: keep `ssh_run` / `get_embedding` / `db_connect` helpers sync; add the wrapper at the call site inside each async handler.

Fix scope: ALL 14 `@mcp.tool` handlers. Mechanical pattern, consistent. Risk per-handler is low; comprehensive fix prevents "oops we fixed only 3 of them and the 4th still blocks" debt.

If any specific handler proves syntactically tricky during edit, **PD is authorized to defer that handler to a v0.2 P5 followup commit and continue Phase 3 with the rest fixed.** The unblock priority is `homelab_ssh_run` (used by Atlas Cycle 1F test).

### 3.2 Atlas client-side fix (atlas.mcp_client patch)

Add `MCP-Protocol-Version: 2025-03-26` header to the `streamablehttp_client(...)` call in `atlas.mcp_client.client.McpClient`. PD's Phase C.1 client-side patch sketch is correct as a one-line change; integrates cleanly with the original Cycle 1F handoff's module sketch.

### 3.3 Deploy-restart (Sloan single-confirm via trigger)

The act of Sloan triggering PD with `Read docs/handoff_paco_to_pd.md and execute.` constitutes the single-confirm. The trigger explicitly enables the restart step.

Restart command: `sudo systemctl restart homelab-mcp.service`

Brief unavailability window (~30s):
- Mac mini Claude Desktop drops; auto-reconnects via mcp-remote
- This conversation's homelab-mcp tooling drops; auto-reconnects
- Any other tail1216a3 mcp clients drop; auto-reconnect

### 3.4 End-to-end smoke validation

After deploy-restart: Beast python-SDK probe to `https://sloan3.tail1216a3.ts.net:8443/mcp` with `MCP-Protocol-Version` header → must return `tools_count >= 14` (matching the 14 `@mcp.tool` handlers in mcp_server.py).

### 3.5 Original Cycle 1F build resumes

Full module + 4 tests + 5-gate acceptance + token logging + ACL + secrets discipline audit, exactly as the original Cycle 1F handoff specified. Commit Atlas changes to santigrey/atlas; close-out fold to control-plane-lab.

## 4. P6 lessons banking decisions

Four candidate lessons surfaced in this cycle. Banking decisions:

**P6 #21 (PD-side discipline):** When client-server impedance hangs initialize, capture both sides' headers via tcpdump on `lo`. Five-minute root-cause vs hours of speculation. **Banked as P6 #21.** Concrete pattern; demonstrated value in Phase C.1.

**P6 #22 (PD-side discipline):** Diagnostic verdicts on transport/protocol issues MUST be validated end-to-end against the actual runtime path before issuing a build directive. Curl-loopback probes are not sufficient evidence for SDK+HTTPS+nginx claims. **Banked as P6 #22.** Direct application of 5th rule's Layer 3 (adversarial pre-mortem). Caught Phase C.1's incomplete fix.

**P6 #23 (NEW from this turn — Paco-side discipline):** Verify launch mechanism (systemd vs nohup vs screen vs supervisord) BEFORE authoring restart commands. PPID=1 + systemd unit existence is a 10-second probe. PD's `nohup` recommendation would have orphaned the process while systemd auto-restarted its own copy. **Banked as P6 #23.**

**P6 #24 (NEW from this turn — Paco-side discipline):** When attaching diagnostic tools to a long-running production server, account for the recursive observer effect. Paco's homelab_ssh_run calls during Phase C.1 diagnostic were themselves the in-flight blockers that made Phase C.1's probes hang. py-spy's catching the same handler in 3 sequential dumps was partially because Paco was actively driving probe traffic. The diagnostic methodology should isolate active observer load. **Banked as P6 #24.**

P5 #10 (v0.2 backlog): file upstream issue/PR with `mcp` python SDK 1.27.0 to default `MCP-Protocol-Version` header on initialize. Defer.

**Counts:** Standing rules unchanged at 5. P6 lessons banked: was 22 (P6 #21/#22 from prior turn; held in commit message but not yet written to canonical 5th rule memory file). With this turn's #23 + #24, count is **24**. PD's paco_review canonically lists P6=20 unchanged; the deltas (#21-24) need to land in the next paco_review or as a fold update to `feedback_paco_pre_directive_verification.md`. Adding to Phase 3 directive's deliverables.

## 5. Sloan-confirm gate scope

- **Server patch (mcp_server.py edit):** PD authority. File edit, no service touched yet. Reversible (git checkout if needed).
- **Atlas client patch + module + tests:** PD authority. Standard build directive scope.
- **Deploy-restart of homelab-mcp.service:** **Sloan single-confirm via trigger.** Sloan's act of pasting `Read docs/handoff_paco_to_pd.md and execute.` to PD constitutes confirmation that the restart is in scope.
- **Anchor preservation invariant:** B2b + Garage must remain bit-identical through restart. uvicorn restart does NOT touch Postgres or Garage containers; verify in Step Z.

No Sloan double-confirm needed (no nginx changes, no hardware changes, no Tailscale install).

## 6. Anchor preservation invariant

B2b + Garage anchors held bit-identical for ~76+ hours through Cycles 1A-1E + 1F Steps 1-2 + Phase C.1 + my Phase C.1 review counter-probes + Phase C.2.0. Phase 3 must preserve this. The uvicorn restart is non-substrate (mcp_http.py is a Python process; substrate anchors are `control-postgres-beast` and `control-garage-beast` containers).

## 7. Cycle 1F status

```
1F -- MCP client gateway (outbound to CK)
   Step 1-2 (anchors, /etc/hosts):              COMPLETED
   Step 3 (connectivity smoke):                 was BLOCKED -- transport hang
   Phase C.1 (read-only probes):                COMPLETED, partial cause + incomplete fix
   Phase C.1 review (Paco counter-probes):      COMPLETED, gap caught
   Phase C.2.0 (non-restart attach):            COMPLETED, root cause PROVEN (event-loop blocking)
   Phase 3 (combined fix + deploy-restart):     GO (this directive)
     - server patch (mcp_server.py asyncio.to_thread)
     - atlas client patch (MCP-Protocol-Version header)
     - deploy-restart via systemctl (Sloan trigger == confirm)
     - end-to-end smoke from Beast
     - original Cycle 1F build resumes (4 tests, 5 gates, token logging, ACL, secrets audit)
     - close-out fold
   Phase C.2.1 (debug-restart):                 NOT NEEDED -- root cause already proven without restart
```

## 8. Discipline metrics Day 75-76

10 directive verifications + 6 PD reviews + 1 paco_request + 1 verdict + 1 verdict revision + 1 confirm-and-Phase-3-go.

| Cumulative findings caught at directive-authorship | 30 |
| **This turn (Phase C.2.0 confirm + Phase 3 directive author)** | **2** (mcp_server.py asyncio NOT imported; PD's nohup recommendation would have orphaned the systemd-managed process) |

The `nohup vs systemctl` catch is the pattern this rule is designed for: PD's recommendation looked correct in isolation but failed against verified deployed state. Costs 10 seconds; missing it would have caused a chaotic Phase 3 restart with two competing processes or a phantom restart loop.

Also worth noting: across Cycle 1F's transport saga, the rule earned its keep at every stage:
- Phase C.1 verdict: Paco caught `host='0.0.0.0'` disproving 5.A
- Phase C.1 review: Paco's CP1-CP5 caught header-alone-fix gap
- Phase C.2.0 review: PD's diagnostic was strong, Paco's verification confirmed it cleanly
- Phase 3 directive (this turn): Paco caught nohup vs systemctl + asyncio import gap

Cumulative ROI on Cycle 1F transport hang: prevented at least 2 BLOCKs (incomplete fix shipping) and 1 outage event (chaotic restart).

---

**File location:** `/home/jes/control-plane/docs/paco_response_atlas_v0_1_cycle_1f_phase_c20_confirm_phase3_go.md`

-- Paco
