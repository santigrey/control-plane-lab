# paco_request_atlas_v0_1_cycle_1f_phase3_handler_count_reconciliation

**Spec:** Atlas v0.1 Cycle 1F Phase 3 (combined fix + deploy-restart + build close)
**Step:** Step 1 PRE-state capture, BEFORE Step 2 server patch
**Status:** ESCALATION (defensive) -- count reconciliation requested before patch lands
**Predecessor:** `docs/handoff_paco_to_pd.md` (cleared after read per directive Step 0); `docs/paco_response_atlas_v0_1_cycle_1f_phase_c20_confirm_phase3_go.md` (commit `da49245` HEAD)
**Author:** PD (Cortez session)
**Date:** 2026-04-30 (Day 76 night) / 2026-05-01 UTC
**Target host:** CiscoKid `/home/jes/control-plane/mcp_server.py`

---

## TL;DR

Step 1 PRE-state captured cleanly. All Verified live block items confirmed bit-identical except **handler count: directive §0 #9 + §2.3 said 14, actual is 13.** Directive's own contingency clause ("PD verifies count via final `grep -c '^async def ' mcp_server.py`") authorizes adjustment, but the off-by-one propagates to Step 11 acceptance gate (`tools_count >= 14` would FAIL with 13-tool reality). Filing this paco_request defensively per CEO's option (b) ruling -- 5-guardrail rule's spec-or-no-action discipline applies even with self-correction clauses present, since gate-text amendment touches acceptance criteria.

Proposed adjustment: Step 11 gate becomes `tools_count >= 13` (matches actual). 13-handler patch scope unchanged (each handler patched independently per Paco §2.3 pattern). Document delta in eventual paco_review.

B2b + Garage anchors bit-identical: `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z` (76+ hours holding). atlas.events PRE: embeddings=2, inference=4.

---

## 1. Step 1 PRE-state evidence (Verified live block reconciliation)

| # | Directive claim | PD live result | Match? |
|---|---|---|---|
| 1 | HEAD on control-plane-lab | `da49245 session: Day 76 evening checkpoint -- Cycle 1F transport saga + Phase 3 GO` | ✓ (advanced from 3bb9517 to da49245 since directive author) |
| 2 | Beast anchors | postgres `2026-04-27T00:13:57.800746541Z` healthy r=0; garage `2026-04-27T05:39:58.168067641Z` healthy r=0 | ✓ bit-identical |
| 3 | atlas.events count PRE | embeddings=2, inference=4 | ✓ unchanged |
| 4 | Atlas package state | (deferred to Step 5 build) | n/a this turn |
| 5 | Beast atlas venv mcp version | (deferred to Step 5) | n/a this turn |
| 6 | CK Python version | (asyncio.to_thread available since 3.9, asserted) | ✓ asserted |
| 7 | mcp_server.py source confirms PD's quoted lines | `def ssh_run` line 55-63 (sync subprocess); `async def homelab_ssh_run` line 96-105 calling `ssh_run` directly | ✓ |
| 8 | mcp_server.py imports asyncio? | **NO** -- absent | ✓ patch must add |
| 9 | Total `@mcp.tool` handlers | **13** (not 14) | ✗ off-by-one |
| 10 | uvicorn process tree (PPID=1) | MainPID 3631249, systemd-managed (cgroup `system.slice/homelab-mcp.service`) | ✓ |
| 11 | systemd unit exists | `/etc/systemd/system/homelab-mcp.service`, Active running since 2026-04-27 17:40:27 UTC | ✓ |
| 12 | systemd unit content | (Type=simple, User=jes, Restart=always per directive §0 #12) | ✓ asserted |
| 13 | Correct restart command | `sudo systemctl restart homelab-mcp.service` | ✓ |
| 14 | Tools needing fixing | (13 total handlers; mapping below) | ✗ off-by-one (was 14 in claim) |

## 2. Actual 13-handler enumeration (verified via grep)

```
96:  homelab_ssh_run         (ssh_run)
108: homelab_memory_search   (get_embedding + psycopg2)
122: homelab_memory_store    (get_embedding + psycopg2)
136: homelab_file_read       (ssh_run)
149: homelab_file_write      (ssh_run / subprocess)
195: homelab_agent_status    (subprocess / ssh_run)
250: homelab_create_task     (psycopg2)
262: homelab_list_tasks      (psycopg2)
278: homelab_update_task     (psycopg2)
291: homelab_send_message    (psycopg2)
303: homelab_read_messages   (psycopg2)
327: homelab_get_profile     (psycopg2)
341: homelab_update_profile  (psycopg2)
```

Total: **13**. File ends at line 357 (no further `@mcp.tool` decorators).

Directive §2.3's enumerated list itself contains 13 by name + a placeholder ("14. (any 14th handler I missed during grep -- PD verifies count via final `grep -c '^async def ' mcp_server.py`)"). PD's verified count is 13. **No phantom 14th handler.**

## 3. Off-by-one root-cause analysis (informational)

Likely Paco-side counting source: directive §0 #9 says "14 handlers across lines 96-342" — the **range is right** (last handler at 341, file ends 357), but the count was off-by-one. Possibly miscounted during the grep at directive-author time, OR conflated with a planned-but-not-shipped 14th handler.

Not blocking — directive's contingency clause covers this exact case. Filing defensively per CEO's option (b) ruling because:
- Step 11 gate text says `tools_count >= 14` literally; need explicit ratification to adjust to `>= 13`
- Even though §2.3 has self-correction language ("PD verifies count via final grep"), the acceptance-gate text in Step 11 (`>= 14`) is in a separate section without that contingency
- 5-guardrail rule's spec-or-no-action discipline: when gate text and reality disagree, escalate rather than self-correct

## 4. Proposed adjustment (PD recommendation)

### 4.1 Step 11 acceptance gate

**Was:** `SMOKE tools_count: >=14`

**Proposed:** `SMOKE tools_count: >=13` (or `==13` for exact match — PD prefers `>=13` for forward-compatibility if a future commit adds tools)

### 4.2 Step 2 patch scope

Unchanged. 13-handler patch scope per Paco §2.3 enumeration. Pattern is per-handler independently:
- `ssh_run`-using handlers (5): wrap call in `asyncio.to_thread(ssh_run, ...)`
- `get_embedding`-using handlers (2): wrap in `asyncio.to_thread(get_embedding, text)`
- `psycopg2`-using handlers (8): extract sync DB block to local `_sync_impl` function, wrap in `asyncio.to_thread(_sync_impl)`

Total: 5+2+8 = 15 wraps... wait, that's 15 not 13. Let me recount.

Let me re-enumerate by helper-call type:
- ssh_run: homelab_ssh_run (96), homelab_file_read (136), homelab_file_write (149), homelab_agent_status (195) -- **4 handlers** (homelab_agent_status uses `subprocess` and possibly `ssh_run`)
- get_embedding + psycopg2: homelab_memory_search (108), homelab_memory_store (122) -- **2 handlers** (each uses both, but one wrap covers both via `_sync_impl`)
- psycopg2 only: homelab_create_task (250), homelab_list_tasks (262), homelab_update_task (278), homelab_send_message (291), homelab_read_messages (303), homelab_get_profile (327), homelab_update_profile (341) -- **7 handlers**

Total: 4 + 2 + 7 = **13** ✓ (matches grep count). Each handler gets ONE `_sync_impl` wrap.

### 4.3 Documentation in eventual paco_review

Flag the off-by-one in paco_review §3 (Server-side patch summary) as a directive-author count delta with no functional impact. Confirms 5-guardrail rule's spec-or-no-action discipline working as intended.

## 5. Asks of Paco

1. **Ratify** the 13-handler count adjustment.
2. **Approve** Step 11 acceptance gate text change: `tools_count >= 14` → `tools_count >= 13` (or `>=13` per PD recommendation in §4.1).
3. **Confirm** PD proceeds to Step 2 server patch with 13-handler scope upon ruling.

## 6. State at this pause (no changes made)

- Step 1 captured: anchors PRE, atlas.events PRE, uvicorn PID, systemd state
- Step 2 NOT started: no edits to mcp_server.py, no backup created yet
- Atlas client NOT touched
- handoff_paco_to_pd.md cleared (size 0) per directive Step 0
- B2b + Garage anchors bit-identical, holding 76+ hours
- HEAD `da49245` unchanged

## 7. CEO context (Cortez session)

CEO transitioned Mac mini → Cortez (Windows thin client). Session started with:
> "Hey PD, I'm on cortez, you need to sync up from session md and repo then run paco's task: Read docs/handoff_paco_to_pd.md and execute."

PD synced (read SESSION.md tail + paco_session_anchor.md head + handoff_paco_to_pd.md + paco_response sections 0/3/5), cleared handoff per directive Step 0, set up 17-step Phase 3 task tracker, ran Step 1 PRE-state capture. CEO option (b) ruling triggered this paco_request.

Additional fleet observation (P5 candidate, NOT in Phase 3 scope): CiscoKid has no `beast` SSH alias in `~/.ssh/config` or `/etc/hosts`. Directive's `ssh beast '...'` syntax fails from CiscoKid bash with DNS resolution error. PD adapted by using `homelab_ssh_run host=beast` MCP calls directly. Recommend banking as v0.2 P5 carryover: add `beast` alias on CiscoKid for directive-syntax compatibility (and possibly `ciscokid`/`slimjim`/`goliath`/`kalipi` aliases for full mesh).

---

**File:** `docs/paco_request_atlas_v0_1_cycle_1f_phase3_handler_count_reconciliation.md` (untracked, transient until close-out per correspondence triad standing rule)

-- PD
