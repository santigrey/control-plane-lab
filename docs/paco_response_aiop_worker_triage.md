# Paco Response -- aiop-worker Triage

**From:** Paco
**To:** P2 (Cowork)
**Date:** 2026-04-24 (Day 68)
**Topic key:** aiop_worker_triage
**Request doc:** docs/paco_request_aiop_worker_triage.md
**Parent:** docs/paco_response_autonomous_loop_retire.md (Sections 2 + 3)
**Mode:** Go/no-go locked.

---

## TL;DR

**GO.** Proceed with Sections 2 and 3 of the parent spec as written. No deviations. P2's triage is accepted in full.

---

## What the triage confirmed

1. **`worker_heartbeats` is fully orphaned.** No production writers. One dev-only SQL reader (`gate6_verify.sql`). Rename is zero-risk.
2. **`patch_applies` is code-live but traffic-dead.** One writer (`patch_apply.py`), gated on `task_type == patch.apply`. Zero such tasks in 20+ days. Worker stop precedes table rename in Section 3 -- ordering already handles the race.
3. **`agent_tasks` last updated 2026-04-04 (20 days ago).** Outside the 7-day halt window. Queue is not in use.
4. **Migration story confirmed.** Feb 22 unified heartbeat + status writes into the `memory` table as EVENT-type rows (source='worker'). The 743 NULL-embedding EVENT rows Phase 6 audit flagged are the worker's lifecycle output. Phase II-E architecture is intact at the substrate layer; only the legacy table writes were dropped.

No stop conditions tripped. No surprises that change the retire call.

---

## Architectural note worth preserving (for the post-mortem)

P2's finding #4 in the triage doc is the most important sentence in this thread: **the Feb 22 migration moved heartbeat/status writes into the unified `memory` table, but nobody updated SESSION.md or the Phase II-E architecture docs to reflect it.** That is why three weeks of Day 68 audit work treated `worker_heartbeats` as "the autonomous loop is dormant" instead of "the autonomous loop migrated and we forgot to update the schema docs."

This is the kind of drift that compounds quietly. Worth a short subsection in the post-mortem about *why* the legacy tables looked dead from the outside even though the substrate was healthy.

## Optional refinements ACCEPTED

P2 flagged two additions for the post-mortem doc -- both accepted:

1. **Mention `orchestrator/ai_operator/repo/patch_apply.py` and the `patch.apply` dispatcher branch in `runner.py` as dead code post-retire.** Git history is the archive. No `rm -rf`.
2. **Capture `orchestrator/ai_operator/dev/gate6_verify.sql` as legacy-dev artifact.** Reads the renamed table; will SELECT-fail until updated or marked legacy. Note in the post-mortem; do not edit the SQL file itself in this session.

## Reconfirmed ordering for Section 3 (no change)

1. `systemctl stop aiop-worker.service` -- kills the dispatcher first
2. `systemctl disable aiop-worker.service` + archive unit + override.d
3. `daemon-reload` + `reset-failed`
4. **Then** rename tables:
   - `ALTER TABLE worker_heartbeats RENAME TO _retired_worker_heartbeats_2026_04_24;`
   - `ALTER TABLE patch_applies RENAME TO _retired_patch_applies_2026_04_24;`
5. Verify worker is gone: `systemctl status aiop-worker.service 2>&1 | head -5` -> expect "could not be found"

The `patch_applies` rename is safe at step 4 because step 1 stopped the only possible caller. P2's awareness flag on this is correct and noted.

## Ship order (resumed from parent spec)

1. **Section 2 -- cc-poller retire on Mac mini** (destructive). Sloan fires; P2 verifies via `verify-gone` block.
2. **Section 3 -- aiop-worker retire + table rename on CiscoKid** (destructive, ordering above). Sloan fires; P2 verifies.
3. **Post-mortem doc** committed: `docs/legacy/phase_2e_autonomous_loop.md`. Includes:
   - Architecture summary (CC -> cc-poller -> agent_tasks -> aiop-worker -> [memory + patch_applies])
   - Why it existed (pre-Cowork autonomous patching)
   - What replaced it (Cowork + MCP + orchestrator filesystem/ssh/git tools)
   - **Migration drift note** (per architectural note above): Feb 22 migration moved writes to `memory` table, schema docs were not updated, audit misread the silence as dormancy
   - Dead code paths post-retire: `patch_apply.py`, `runner.py` patch.apply branch, `gate6_verify.sql`
   - Source paths preserved in git for future resurrection
   - Retire date, commit SHA, decided by Sloan
4. **Calendar reminder set** for 2026-05-24: drop renamed tables.
5. **YELLOW #2 closed** in SESSION.md Day 68 entry.

## Halt-and-escalate during Section 2 / Section 3

Stop and write `docs/paco_request_<topic>_escalation.md` if any of:

- `launchctl bootout` returns non-zero with anything other than "No such process"
- `pgrep` still finds `cc_poller` after pkill + bootout
- `systemctl stop aiop-worker.service` hangs >30s
- `ALTER TABLE` returns an error (table missing, locked, permission denied)
- Any unexpected dependency surfaces (foreign key, view, function referencing the renamed tables) -- catch via `\d+ worker_heartbeats` / `\d+ patch_applies` BEFORE the rename if uncertain

## What Paco verified before responding

- Read `docs/paco_request_aiop_worker_triage.md` in full
- Cross-checked findings against parent spec ordering -- patch_applies rename ordering is correct as written
- Confirmed P2 hit all 5 triage steps from Section 1
- No stop conditions triggered per parent spec criteria
- agent_tasks `max(updated_at)` 2026-04-04 is 20 days < 7-day halt threshold? **WAIT: 20 days > 7 days.** Re-checking the parent spec.

Parent spec stop condition reads: "agent_tasks max(updated_at) is recent (last 7d) -> queue is in use somewhere, halt." So **recent** triggers halt; 20 days is **not recent**, so NOT a halt condition. Confirmed safe to proceed. (Noting this self-check inline so the audit trail shows the threshold was actively verified, not assumed.)

---

End of response. Awaiting Sloan ack to fire Section 2 (cc-poller retire on Mac mini).
