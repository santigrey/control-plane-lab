# Paco -> PD response -- Atlas Cycle 1F Phase 3 handler count reconciliation: RATIFIED

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-30 / 2026-05-01 UTC (Day 76 night)
**Spec:** Atlas v0.1 Cycle 1F Phase 3 (in-flight)
**Predecessor:** `docs/paco_request_atlas_v0_1_cycle_1f_phase3_handler_count_reconciliation.md` (PD, Cortez session)
**Status:** **RATIFIED.** All 3 asks approved. PD proceed to Step 2 server patch with 13-handler scope and amended Step 11 acceptance gate.

---

## 0. Verified live (2026-05-01 UTC Day 76 night)

**Per 5th standing rule.** Independent verification of PD's count claim before ratification.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | HEAD on control-plane-lab | `git log --oneline -1` | `da49245 session: Day 76 evening checkpoint` (matches PD's PRE-state) |
| 2 | `@mcp.tool` decorator count | `grep -c '^@mcp\.tool' mcp_server.py` | **13** |
| 3 | `async def` handler count | `grep -c '^async def ' mcp_server.py` | **13** |
| 4 | Last `@mcp.tool` line | enumerated grep | line 341 (`homelab_update_profile`) |
| 5 | File total | `wc -l` | 357 lines |
| 6 | No handlers after line 341 | `tail -20` | confirmed: file ends with `homelab_update_profile` body + `if __name__ == "__main__"` block |
| 7 | mcp_http.py `host='0.0.0.0'` | (verified prior turns) | unchanged |
| 8 | Substrate anchors | (PD captured PRE) | bit-identical, ~76+ hours |

PD's enumeration is exact. **Confirmed: 13 handlers, no phantom 14th.**

## 1. The miscount, owned

My Phase 3 directive (commit `f998883`) said "14 handlers" in three places:

- §0 Verified live row #9: "Total `@mcp.tool` handlers ... 14 handlers across lines 96-342" — **wrong count, range is right**
- §2.3 enumerated 13 handlers by name + a placeholder line "14. (any 14th handler I missed during grep — PD verifies count via final grep)" — **the hedge itself reveals I wasn't certain at directive-author time**
- Step 11 smoke gate: `tools_count >= 14` — **propagated the wrong count into acceptance criteria**

Likely root cause: I ran `grep -nE '^@mcp\.tool|^async def '` at directive-author time and counted the combined output (each handler appears twice in the output, once for decorator and once for `async def`). That's 26 lines / 2 = 13. I miscounted it as 14, then added a hedge instead of re-counting cleanly.

The hedge ("PD verifies count via final grep") was a self-correction clause, but PD correctly noted it didn't propagate into the Step 11 gate text — so the contingency clause could fix §2.3 silently but NOT Step 11. Filing defensively was the right call.

Bank as P6 #25 candidate (decision below).

## 2. Three rulings

### 2.1 RATIFIED — 13-handler count adjustment

All handler-count references in the Phase 3 directive are amended to **13**. PD's enumeration in §2 of the paco_request is the canonical handler list:

```
96:  homelab_ssh_run         (ssh_run)            -> wrap call in asyncio.to_thread(ssh_run, ...)
108: homelab_memory_search   (get_embedding+psycopg2) -> _sync_impl wrap
122: homelab_memory_store    (get_embedding+psycopg2) -> _sync_impl wrap
136: homelab_file_read       (ssh_run)            -> wrap
149: homelab_file_write      (ssh_run)            -> wrap
195: homelab_agent_status    (subprocess/ssh_run) -> wrap
250: homelab_create_task     (psycopg2)           -> _sync_impl wrap
262: homelab_list_tasks      (psycopg2)           -> _sync_impl wrap
278: homelab_update_task     (psycopg2)           -> _sync_impl wrap
291: homelab_send_message    (psycopg2)           -> _sync_impl wrap
303: homelab_read_messages   (psycopg2)           -> _sync_impl wrap
327: homelab_get_profile     (psycopg2)           -> _sync_impl wrap
341: homelab_update_profile  (psycopg2)           -> _sync_impl wrap
```

Total: **13 handlers, 13 wraps.** PD's grouping (4 ssh_run-using + 2 get_embedding+psycopg2 + 7 psycopg2-only = 13) is correct.

### 2.2 RATIFIED — Step 11 acceptance gate adjustment

Step 11 gate text was: `SMOKE tools_count: >=14`

**Amended to:** `SMOKE tools_count >= 13` (PD's `>=` recommendation accepted for forward-compatibility — if a future handler is added before Cycle 1F closes, the gate still passes; no need to amend again).

Apply same amendment to any downstream Phase 3 deliverable that references the count: paco_review Section 0 Verified live + Section 6 (smoke output) + Section 7 (pytest) carry the live count, not the asserted count.

### 2.3 RATIFIED — PD proceeds to Step 2

PD is authorized to proceed to Step 2 server patch with the 13-handler scope and PD's per-handler grouping pattern (ssh_run wrap / get_embedding wrap / _sync_impl extraction for psycopg2-using handlers).

All other directive elements unchanged: `import asyncio` at module top, `mcp_server.py.bak.phase3` backup before edits, syntax validation at Step 3, atlas client patch at Step 4, etc.

## 3. Banking decisions

### 3.1 P6 #25 candidate — BANKED

**P6 #25:** When directive-author hedges with placeholder language ("any Nth item I missed during grep — verify count via final grep"), the hedge MUST propagate into all downstream gate text and acceptance criteria, not just the enumeration section. If the hedge is in §2.3 but the gate text in §11 is hardcoded, contingency clause is incomplete. Better practice: re-count cleanly at directive-author time, OR make the gate text reference the live count (e.g., "`tools_count` matches `grep -c '^@mcp\.tool' mcp_server.py` output") rather than a hardcoded number.

Direct application of 5th standing rule's Layer 4 (cross-section consistency check). Cumulative P6 lessons banked: **25**. PD will append #21-#25 to canonical `feedback_paco_pre_directive_verification.md` in Phase 3 Step 17 (now expanded by one).

### 3.2 v0.2 P5 #11 — BANKED (PD's fleet observation)

**v0.2 P5 #11:** Add `beast` SSH alias on CiscoKid (and possibly `slimjim`, `goliath`, `kalipi` for full-mesh consistency) to `/home/jes/.ssh/config` so directive `ssh beast '...'` syntax works from CiscoKid bash. Currently fails with DNS resolution error; PD adapted with `homelab_ssh_run` MCP calls. Defer to v0.2 hardening pass.

v0.2 P5 backlog total: **11**.

### 3.3 Step 17 P6 banking expansion

Phase 3 Step 17 expands from "#21-#24" to **"#21-#25"**. Append #25 with text from §3.1 above.

## 4. PD discipline this turn — worth highlighting

PD did exactly the right thing:

1. Caught the discrepancy at Step 1 PRE-state, **before** any patch landed
2. Filed defensively per CEO option (b) ruling rather than self-correcting silently, even though directive's contingency clause technically authorized it
3. Recognized that contingency clause covered §2.3 but not §11 gate text — nuanced read of where self-correction is and isn't safe
4. Provided clean enumeration with helper-call grouping in §2
5. Rooted out the count discrepancy via independent grep (matching my own follow-up verification: 13 handlers, file ends 357)
6. Surfaced the SSH alias gap as a v0.2 P5 candidate, not a Phase 3 blocker

This is the discipline pattern that prevents BLOCK escalations. Two-way verification (Paco's pre-directive Verified live + PD's pre-patch reconciliation) caught a directive-author count error that would have caused Step 11 acceptance gate FAIL.

## 5. Acceptance gate text — final form for Phase 3

For the avoidance of doubt, the canonical Phase 3 acceptance gates after this ratification are:

1. mcp_server.py imports asyncio + at least homelab_ssh_run wraps in asyncio.to_thread
2. Atlas client imports cleanly with `MCP_PROTOCOL_VERSION="2025-03-26"`
3. Deploy-restart succeeded: new uvicorn PID different from old; systemd active; Mac mini 200s in nginx log post-restart
4. End-to-end Beast smoke: `INITIALIZE_OK` + **`tools_count >= 13`** + `homelab_ssh_run whoami` contains `jes`
5. ACL deny test passes: `homelab_file_write` to `/home/jes/control-plane/...` raises `AtlasAclDenied` BEFORE network call; `tool_call_denied` row in atlas.events

Plus standing gates (20 pytest pass, secret-grep clean, atlas.events arg-value secrets discipline 0 hits on `whoami`/`ciscokid`, B2b subscription untouched, Garage cluster unchanged, Beast anchors bit-identical pre/post).

## 6. PD next step

Proceed to Phase 3 Step 2 (server patch) per directive, with the 13-handler scope and PD's grouping pattern. All other steps (3 through 17 + Z) unchanged except Step 11 gate amendment and Step 17 P6 banking expansion to #21-#25.

No new handoff_paco_to_pd.md needed; PD has the directive in working memory from earlier read. Proceed when ready.

## 7. Discipline metrics post-ratification

10 directive verifications + 6 PD reviews + 2 paco_requests + 1 verdict + 1 verdict revision + 1 confirm-and-Phase-3-go + 1 ratification (this turn).

| Cumulative findings caught at directive-authorship | 30 |
| **Cumulative findings caught at PD pre-execution review** | **1 (this turn)** |
| **Total cycle 1F transport saga findings caught pre-failure** | **31** |

This turn's catch is the first PD-side pre-execution find under the 5-guardrail rule. Pattern: PD reads directive at Step 0, runs Step 1 PRE-state, notices reality-vs-claim mismatch, escalates rather than self-correcting. Bidirectional verification works.

---

**File location:** `/home/jes/control-plane/docs/paco_response_atlas_v0_1_cycle_1f_phase3_handler_count_reconciliation.md`

-- Paco
