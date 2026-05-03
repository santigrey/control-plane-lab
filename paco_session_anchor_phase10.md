# paco_session_anchor_phase10

**Purpose:** Bootstrap a fresh Paco session for Atlas v0.1 Phase 10 (ship report) + CVE-2026-31431 patch cycle Step 2+. Self-contained — paste this file's URL OR contents at session start; Paco runs the boot probe + reads queued canon + proceeds.

**Anchor authored:** 2026-05-03 Day 79 early morning (post-Phase-9 close-confirm)
**Anchor active until:** Phase 10 + patch cycle Step 2 close-confirm OR replaced by next anchor

---

## Identity reminder

You are Paco — COO + systems architect for Santigrey Enterprises. CEO is Sloan. PD is Cowork. Operating mode: anchor-as-pointer (canon is source of truth). Address Sloan as Sloan. Operations motto: measure twice, cut once.

---

## Boot probe (run via homelab MCP at session start)

```
ssh ciscokid 'cd /home/jes/control-plane && git log --oneline -1' -> expect HEAD ab2c72f (or later if patch cycle landed)
ssh beast 'cd /home/jes/atlas && git log --oneline -1' -> expect 147f13c parent (atlas HEAD c28310b OR later if Phase 10 landed)
ssh ciscokid 'systemctl show -p MainPID mercury-scanner.service' -> expect 643409
ssh beast 'systemctl show -p MainPID atlas-mcp.service' -> expect 2173807
ssh beast 'systemctl show -p MainPID -p ActiveState -p UnitFileState atlas-agent.service' -> expect MainPID 2872599 active enabled (Phase 9 deliverable; SG5 invariant updated)
ssh beast 'docker inspect control-postgres-beast --format "{{.State.StartedAt}}"' -> expect 2026-04-27T00:13:57.800746541Z (substrate anchor; bit-identical at ~145h+ as of Day 79 early morning)
ssh beast 'docker inspect control-garage-beast --format "{{.State.StartedAt}}"' -> expect 2026-04-27T05:39:58.168067641Z
```

**If atlas-agent MainPID has changed** (NRestarts > 0 OR ActiveEnterTimestamp moved): atlas-agent restarted since Phase 9 close. Note the new MainPID + investigate journalctl for restart reason BEFORE proceeding to Phase 10. Production observation discontinuity may affect ship report data.

---

## Read on boot (in order)

1. `paco_session_anchor.md` (current running anchor; Day 79 early morning state)
2. `docs/feedback_paco_pre_directive_verification.md` (REFRESHED Day 79 early morning; cumulative P6=36 SR=7; canonical source-of-truth for cumulative count)
3. `docs/paco_response_atlas_v0_1_phase9_close_confirm.md` (Phase 9 close artifact; PD-asks 1-8 ratification; SR #7 first-application validation)
4. `docs/paco_review_atlas_v0_1_phase9.md` (PD's Phase 9 review; cross-machine continuity pattern; drift catch resolution)
5. `tasks/atlas_v0_1_agent_loop.md` lines 525-539 (Phase 10 spec) AND lines 540-end (Acceptance Gates 6 + Standing Gates 6)
6. `docs/paco_directive_homelab_patch_cycle_cve_2026_31431.md` (queued patch cycle directive; Step 1 banked at Step 3.5; Steps 2+ remain)

---

## Three queues, executed in priority order

### Queue 1: Atlas v0.1 Phase 10 (ship report)

**Status:** AUTHORIZED at Phase 9 close-confirm. Data already over-saturated (atlas-agent enabled 2026-05-03 03:57:17 UTC; spec asks for 1-hour observation; current elapsed >> 1 hour at session resume).

**Spec scope (lines 525-539):** author `paco_review_atlas_v0_1_agent_loop_ship.md` covering:
- What works (per Phase acceptance)
- 6 Acceptance Gates pass/fail
- 6 Standing Gates pass/fail (SG5 invariant updated to active+enabled going forward)
- Substrate anchor verification (must be bit-identical)
- atlas.events row counts per domain (EXPECT zero from agent.* per SR #7 correction; non-agent rows from mcp_server/inference/embeddings/mcp_client) -- **clarify in ship report that atlas.tasks is the agent.* observation table**
- atlas.tasks row counts per domain (first-hour sample; actual elapsed >> 1h so use 1h window starting at 03:57:17 UTC for spec parity)
- Known issues + P5 candidates banked (see v0.1.1 candidate list below)
- One-line objective check per Rule 5

**SR #7 source-surface preflight required before authoring directive.** Probe scope:
- Verify Phase 10 spec line range + acceptance criteria text
- Verify atlas-agent.service runtime state at preflight time (MainPID stable? NRestarts? uptime?)
- Sample atlas.tasks 1-hour window 03:57:17->04:57:17 UTC: row count per kind
- Verify substrate anchors still bit-identical at preflight time (SG2/SG3)
- Verify mercury-scanner @ CK MainPID still 643409 (SG6)
- Verify atlas-mcp.service still MainPID 2173807 (SG4)

**Decisions for CEO ratification before authoring:**
- A: PD-executable vs Paco-executable? Phase 10 is single-file ship report authoring; case for Paco-executable (no code; document-only). Case for PD-executable: continue established pattern + Paco close-confirms.
- B: Reuse PD's Phase 9 review structure as ship-report skeleton, OR author from spec template fresh?
- C: 1-hour observation window: use 03:57:17->04:57:17 UTC strictly for spec parity, OR use full elapsed window (more data, deviates from spec)?
- D: P6 #36 mitigation (journalctl --no-pager / sleep 5 settle) applied to ship-report data capture procedure?

### Queue 2: CVE-2026-31431 patch cycle Step 2+

**Status:** Step 1 banked at reachability cycle Step 3.5 (kernel + sudo inventory captured for KaliPi + Pi3). Steps 2+ remain.

**Banked kernel inventory (from Step 1):**
- KaliPi: `6.12.34+rpt-rpi-2712` / Kali Rolling 2025.4 / NOPASSWD jes
- Pi3: `6.12.75+rpt-rpi-v8` / Debian 13 trixie / NOPASSWD jes

**Other Linux nodes (need probe at directive author time per SR #7):** CK, Beast, SlimJim, Goliath. Mac mini (macOS) has separate update path (softwareupdate; deferred from CVE-2026-31431 unless Apple advisory issued).

**Decisions for CEO ratification:**
- A: Patch order (suggest: SlimJim first — lowest blast radius; then KaliPi/Pi3 — edge nodes; then Goliath — standalone GPU; then Beast — Atlas runtime; CK last — orchestrator)
- B: Reboot policy — reboot-after-patch (forced) vs check-needs-restart (conditional)? Bias to reboot-after-patch on edge/standalone, conditional on Atlas runtime + orchestrator.
- C: Sequencing with respect to Atlas — patch Beast (atlas-agent host) requires atlas-agent.service restart on reboot. SG5 invariant tolerance: bounded-restarts/24h must accept this OR patch Beast at "maintenance window" with explicit SG5-flip ratification.
- D: Standing gates pre/post snapshot per node (mandatory per Phase 9 pattern).
- E: Patch cycle uses Paco PD-executable cycles per node, OR one batched directive covering all 6 Linux nodes serially?

### Queue 3: Atlas v0.1.1 candidate list (banked, no rush)

See `docs/paco_response_atlas_v0_1_phase9_close_confirm.md` §"Atlas v0.1.1 candidate list". 7 items as of Phase 9 close: emit_event PII redaction, Domain 1-4 atlas.tasks vs atlas.events unification, structlog uniformity, _MockDb hoist to conftest.py, INTEGRATION_QUICK env var, atlas.tasks retention policy, journalctl capture standardization (P6 #36 mitigation).

P5 v0.1.1 credential rotation queue: 18 canon-hygiene exposures (17 P5-class + 1 phone literal); independent cycle; slot when convenient.

---

## State at anchor time (Day 79 early morning)

```
Reachability cycle:        7 of 7 steps CLOSED (entire cycle complete)
Atlas v0.1:                10 of 11 phases CLOSED (Phase 10 ship report = NEXT)
Patch cycle:               Step 1 banked (Steps 2+ queued)
P5 v0.1.1 rotation:        18-credential queue (independent)

Fleet topology:            7 nodes 100% canonical SSH (NxN 42/42 PASS post-prune)
Standing gates:            6/6 with SG5 invariant updated to active+enabled (Phase 9 deliverable)
Substrate anchors:         ~145h+ bit-identical
atlas-agent in production: MainPID 2872599 since 2026-05-03 03:57:17 UTC; NRestarts 0
atlas.tasks growth:        ~260 rows/hour Domain 1 monitoring; 781 rows in first 3h
P6 lessons banked:         36 (last bank: P6 #36 journalctl race, Day 79 early morning)
Standing rules:            7 (last bank: SR #7 test-directive source-surface preflight, Day 78 evening)
First-try acceptance streak: 6 consecutive (Phases 4, 5, 6, 7, 8, 9)
paco_request escalations:  0 across all cycles to date
```

---

## What just happened (Phase 9 close-confirm context)

PD's Phase 9 review correctly flagged a Paco-side propagation gap: ledger file `feedback_paco_pre_directive_verification.md` was 2 P6 lessons + 1 SR behind canon (Phase 8 close-confirm banked P6 #34/#35/SR #7 but didn't update the ledger in same commit). PD did not have visibility into close-confirm canon; sourced count from ledger; flagged the discrepancy in review for Paco recalibration.

**Resolution at Phase 9 close-confirm (commit ab2c72f):**
1. Ledger file refreshed with current canon (P6=36 / SR=7 after banking P6 #36).
2. New standing practice: "When Paco close-confirms a phase that banks a new P6 lesson or new SR, update this ledger file in the same close-confirm commit. NEVER let ledger lag close-confirm canon." Baked into ledger §"Standing practice strengthening (Paco-side, Day 79 early morning)".
3. PD's proposed lesson (journalctl buffer-flush race) banked as P6 #36.
4. PD's handoff overwrite request DENIED (drift catch belongs in review + close-confirm, not handoff).

**Going forward:** every Paco close-confirm that banks a new P6 lesson or new SR co-updates the ledger file. Propagation gap closed structurally.

---

## Tool / schema notes for next session

- homelab MCP tool schema: function definitions show `params`-wrapped per current refresh. Server has historically alternated; first call confirms current enforcement — if validation error "params required", use wrap; if "params.params forbidden", use flat. Trust validation error feedback.
- Cross-machine PD continuity (Cortez → JesAir mid-cycle) worked clean at Phase 9 because (a) atlas-agent runs independently of Cowork, (b) SR #6 self-state re-verification at resume, (c) SESSION.md served as bridge. Reusable pattern.

---

## Recommended fresh-session opening prompt

When Sloan returns, paste a system prompt that includes:

```
You are Paco. Read /home/jes/control-plane/paco_session_anchor_phase10.md and execute its boot probe. Then proceed to Queue 1 (Atlas v0.1 Phase 10) per the anchor's structural decisions — surface decisions A/B/C/D for CEO ratification before authoring. Apply SR #7 source-surface preflight before directive authoring. CEO is Sloan; address as Sloan.
```

-- Paco (Day 79 early morning, post-Phase-9 close)
