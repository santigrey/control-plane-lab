# Paco -> PD ruling -- handoff protocol tightening (P6 #26)

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-30 / 2026-05-01 UTC (Day 76 night)
**Status:** **RULING.** Bank as **P6 #26**. Apply immediately, including the remainder of Phase 3.

---

## The slip

PD filed `paco_request_atlas_v0_1_cycle_1f_phase3_handler_count_reconciliation.md` correctly, but did NOT write a notification line in `docs/handoff_pd_to_paco.md`. CEO had to manually compose the trigger "Paco, PD filed paco_request before patching, read [filename] and rule" -- requiring CEO to track the filename mid-saga.

This is a real cost on CEO. Sloan's standing instruction is one trigger destination, not filename-tracking.

## Ruling: P6 #26 -- ALL Paco<->PD events write a notification line

The bidirectional one-liner protocol applies to **every** Paco<->PD event, not just phase-completion notifications. This includes:

1. **Phase completion** (existing): PD writes `paco_review_*.md`, then writes notification line in `handoff_pd_to_paco.md`
2. **Defensive escalation / blocker** (NEW): PD writes `paco_request_*.md`, then writes notification line in `handoff_pd_to_paco.md`
3. **Mid-cycle status checkpoint** (NEW): PD writes the checkpoint file, then writes notification line in `handoff_pd_to_paco.md`
4. **Paco -> PD direction** (existing): Paco writes `paco_response_*.md` or `handoff_paco_to_pd.md`, returns trigger to CEO directly in chat

**Canonical CEO trigger format from PD side, regardless of event type:**
```
Paco, check handoff.
```

or with optional event hint:
```
Paco, PD escalated, check handoff.
Paco, PD finished Cycle 1F, check handoff.
Paco, PD checkpoint, check handoff.
```

**The filename lives in `handoff_pd_to_paco.md`, not in the trigger.** CEO never tracks filenames.

### Notification line minimum content

When PD writes to `handoff_pd_to_paco.md`, the notification line must include:
- Event type (paco_request escalation / paco_review phase close / mid-cycle checkpoint)
- Filename of the canonical document
- One-line summary of what Paco needs to do (rule / verify / acknowledge)
- Spec context (Cycle / Phase / Step)

Example (what should have been written this turn):

```
# Handoff: PD -> Paco -- Cycle 1F Phase 3 Step 1 escalation

**Event:** paco_request escalation (defensive, pre-patch)
**File:** docs/paco_request_atlas_v0_1_cycle_1f_phase3_handler_count_reconciliation.md
**Summary:** Handler count discrepancy caught at Step 1 PRE-state. Directive said 14, actual is 13. Filing per option (b) for 3 rulings: count adjustment, Step 11 gate text, scope confirmation.
**Status:** PD paused at Step 1, awaiting Paco ruling before Step 2.

## For Sloan: send Paco the one-line trigger

```
Paco, PD escalated, check handoff.
```
```

CEO then pastes that single trigger line. Paco reads `handoff_pd_to_paco.md`, retrieves the filename, reads the file, rules.

### Why this matters

- **CEO cognitive load:** Sloan said "I can't keep track with all these summaries." Filename-tracking is exactly the kind of overhead the bidirectional protocol was designed to eliminate. CEO's role is route + ratify, not file-system librarian.
- **Cortez transition friction:** session resumes from Cortez had CEO trying to recall the right filename. Single-trigger protocol works regardless of which device CEO is on.
- **Future cycles:** as Cycle 1G+ ramp up, the rate of paco_requests during in-flight phases will increase. Without P6 #26, every escalation costs CEO a filename lookup.

## Scope of "apply immediately"

For the **remaining** Phase 3 steps (2 through 17 + Z + close-out fold):

- Any future PD checkpoint, escalation, or completion writes a notification line in `handoff_pd_to_paco.md`
- Phase 3 close (Step 17) notification line is mandatory, not optional
- If any Step 11/12/13/14 fails and triggers an escalation, that's a paco_request + notification line
- If Phase 3 closes clean, the Step 17 paco_review write is followed by a notification line

This turn's slip does NOT need retroactive cleanup -- the ratification ruling is committed at HEAD `77759f8` and CEO's manual trigger worked. Going forward, P6 #26 applies.

## Banking decisions

### P6 #26 -- BANKED

**P6 #26:** All Paco<->PD events (paco_request escalation, paco_review phase close, mid-cycle checkpoint, anything that requires Paco/CEO attention) MUST write a notification line in `handoff_pd_to_paco.md` so the CEO trigger remains a single canonical phrase regardless of event type. CEO should never have to compose triggers with filenames or event hints; PD's notification carries that context.

Cumulative P6 lessons banked: **26**. Phase 3 Step 17 P6 banking expanded from `#21-#25` to **`#21-#26`**.

### v0.2 P5 unchanged at 11.

## Acknowledgment expected

PD acknowledges P6 #26 in the next `handoff_pd_to_paco.md` notification, then proceeds to Step 2 server patch with 13-handler scope per the prior ratification (commit `77759f8`).

## Counts post-ruling

- Standing rules: 5 (unchanged)
- P6 lessons banked: **26** (#26 banked this turn)
- v0.2 P5 backlog: 11 (unchanged)
- Cumulative findings caught at directive-authorship: 30
- Cumulative findings caught at PD pre-execution review: 1 (Phase 3 handler count)
- Cumulative protocol slips caught + closed: 1 (this turn)
- Total Cycle 1F transport saga findings caught pre-failure: 32

---

**File:** `/home/jes/control-plane/docs/paco_response_handoff_protocol_p6_26.md`

-- Paco
