# Paco Session Anchor (canonical on-disk source of truth)

**Last updated:** 2026-05-02 Day 78 mid-day (post Step 4.1 close)
**Updated by:** Paco at every cycle close or major decision
**Used by:** CEO at session start to boot a fresh Paco context

---

## ONE-LINER REPO SAVE (paste at top of fresh Paco session)

```
You are Paco -- COO + systems architect for Santigrey Enterprises. CEO is Sloan. PD is Cowork. Operating mode: anchor-as-pointer (canon is source of truth, not anchor restatement).

Boot probe via homelab MCP:
- ssh ciscokid 'cd /home/jes/control-plane && git log --oneline -1' -> expect HEAD 1cfced4
- ssh beast 'cd /home/jes/atlas && git log --oneline -1' -> expect 147f13c
- ssh ciscokid 'systemctl show -p MainPID mercury-scanner.service' -> expect 643409
- ssh beast 'systemctl show -p MainPID atlas-mcp.service' -> expect 2173807
- ssh beast 'docker inspect control-postgres-beast --format "{{.State.StartedAt}}"' -> expect 2026-04-27T00:13:57.800746541Z
- ssh beast 'docker inspect control-garage-beast --format "{{.State.StartedAt}}"' -> expect 2026-04-27T05:39:58.168067641Z

Read on boot (in order):
1. paco_session_anchor.md (this file -- queue + open questions)
2. docs/handoff_paco_to_pd.md (PD's current directive)
3. docs/homelab_reachability_v1_0.md (active reachability cycle canon)
4. docs/paco_directive_homelab_patch_cycle_cve_2026_31431.md (queued patch cycle)
5. docs/feedback_paco_pre_directive_verification.md (34 P6 lessons)

Three active queues, executed in order:
1. Reachability cycle Step 3+ (in flight; Step 1+2 done; Step 3 next)
2. CVE-2026-31431 patch cycle (queued)
3. Atlas v0.1 Phase 7 (queued)
```

---

## CURRENT STATE (2026-05-02 Day 78 mid-day)

### HEADs
- control-plane-lab: `1cfced4` (Step 2 close: CEO Option A ratified)
- atlas: `147f13c` (Phase 6 forward-redaction)

### Active queues

**Queue 1 -- Reachability cycle (in flight)**
- [x] Step 1 -- Canon doc + probe script (HEAD 38b0c46)
- [x] Step 2 -- CEO user policy: Option A consolidate to `jes` (HEAD 1cfced4)
- [x] Cortez sub-decision: Y1 ratified (Day 78 mid-day; canon already encodes `sloan@cortez-canonical`)
- [x] Step 3 -- Push canonical /etc/hosts to 4 PD-executable Linux nodes: CK, Beast, SlimJim, Goliath. CLOSE-CONFIRM 4/4 PASS first-try; standing gates 5/5 bit-identical (PD review HEAD `b421e05`; close-confirm `docs/paco_response_reachability_step3_close_confirm.md`)
- [x] Step 3.5 -- KaliPi+Pi3 onboarding CLOSE-CONFIRM 6/6 phases PASS; standing gates 5/5 bit-identical; jes user with NOPASSWD sudo + canonical ssh keys + canonical /etc/hosts on both nodes; MCP HOST_USERS mapped to jes (commit `5517775`); homelab-mcp.service restarted (MainPID 1640430). Patch-cycle Step 1 banked. Close-confirm `docs/paco_response_reachability_step35_close_confirm.md`.
- [~] Step 4 -- IN FLIGHT (sub-cycle structure ratified Day 78 mid-day):
  - [x] Step 4.1 -- Generate canonical id_ed25519 on Goliath, KaliPi, Pi3 (`docs/fleet_outbound_keys_canon.md`)
  - [ ] Step 4.2 -- CEO supplies Cortez + JesAir public keys (paste from each device)
  - [ ] Step 4.3 -- Push canonical authorized_keys (marker block; union of fleet outbound keys) to 6 Class A Linux nodes
  - [ ] Step 4.4 -- Push canonical ~/.ssh/config (Linux nodes via PD; Cortez + JesAir via CEO)
  - [ ] Step 4.5 -- Run reachability_probe.sh; capture N×N matrix; canon baseline; close-confirm
- [ ] Step 5 -- Mac mini sshd persistence + watchdog
- [ ] Step 6 -- Probe full N×N PASS; commit canon baseline
- [ ] Step 7 -- Atlas Domain 1 integration (deferred; not blocking)

**Queue 2 -- CVE-2026-31431 patch cycle (queued)**
- See `docs/paco_directive_homelab_patch_cycle_cve_2026_31431.md` (6 steps)
- Resumes after reachability Step 6
- Mr Robot backlog Job #1

**Queue 3 -- Atlas v0.1 Phase 7 (queued)**
- Spec: `tasks/atlas_v0_1_agent_loop.md` lines 427-451 (amended Day 78 mid-day)
- 7.1 emit_event + dispatch_telegram + 7.2 mercury cancel-window wire-up
- Resumes after patch cycle close
- 3 of 10 phases remain

### Standing Gates 6/6 holding
- atlas-mcp.service: MainPID 2173807 (~13h+)
- atlas-agent.service: disabled inactive (Phase 1 acceptance preserved through 6 phases)
- mercury-scanner.service: MainPID 643409 (Day 78 morning .env fix preserved)
- B2b anchor: 2026-04-27T00:13:57.800746541Z (bit-identical 96+h; resets at patch Step 5)
- Garage anchor: 2026-04-27T05:39:58.168067641Z (bit-identical 96+h; resets at patch Step 5)
- atlas .env on Beast: empty mode 0600 jes:jes (Phase 9 latent blocker neutralized)

### Discipline metrics
- 34 P6 lessons banked (last: #34 Day 78 morning)
- 6 standing rules
- 18 known canon-hygiene exposures pending P5 v0.1.1 (17 P5-class weak-credential + 1 phone literal; +1 mcp_server.py line 25 found Day 78 mid-day, P6 #34 forward-redaction applied to new artifacts this cycle)
- 5 paco_requests / 5 caught at PD pre-execution
- Paco-side error rate this session: high; correlated with conversation depth; fresh session expected to reduce

### Open CEO questions
(none currently — Cortez sub-decision Y1 ratified Day 78 mid-day)

---

## UPDATE PROTOCOL

Paco updates this anchor when ANY of:
- A queue progresses (cycle step closes)
- A new queue spawns
- HEAD moves on either repo
- Standing gate values reset (post-patch / post-anchor-reset)
- A CEO decision lands

Updates are SURGICAL (no sweeping rewrites). Anchor is a pointer to canon, not a restatement. Canon files (CHECKLIST, paco_response, handoffs, feedback ledger, directive docs) are authoritative.

If this anchor and a canon file disagree, canon wins; anchor is stale and gets fixed at the next update.
