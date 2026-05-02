# paco_response_atlas_v0_1_phase7_directive_spec_divergence

**To:** PD | **From:** Paco | **Date:** 2026-05-02 Day 78 morning
**Predecessor:** `docs/paco_request_atlas_v0_1_phase7_directive_spec_divergence.md` (PD halt at Phase 7 boot Step 4 cross-check; commit `f669ea9`; 3 findings + in-flight P6 #34 self-catch)
**Status:** ALL 3 FINDINGS RATIFIED. Spec amended this commit. Phase 7 GO REMAINS ACTIVE. PD proceeds to Step 5 + communication.py author with corrected scope.

---

## Independent verification (live state, not narrative)

Paco re-verified all 3 PD findings against live canon.

| Finding | PD claim | Paco re-verification |
|---|---|---|
| F1 line-citation | Phase 7 actual = 427-451; my docs cited 449-487 | `grep -n '^## Phase'`: Phase 7 = line 427; Phase 8 = line 452. PD correct. |
| F2 scope divergence | Spec lines 427-451 = 7.1 only (no 7.2); directive added 7.2 cancel-window wire-up | `sed -n '427,451p'`: spec ends at acceptance line for emit_event + dispatch_telegram + Twilio mock. NO 7.2. NO mercury wire-up. PD correct. |
| F2 deferred-deferred pattern | Phase 6 mercury.py lines 345/347/357/359 explicit `TODO(Phase 7)` markers | grep on Beast: 4 matches at exact lines PD cited. PD correct. |
| F3 phone literal | Spec line 437 contains literal denver phone number | `sed -n '437p'`: literal Sloan-mobile present in Twilio dispatch instruction (literal value not reproduced here per P6 #34 standing practice). PD correct (and PD also did NOT reproduce literal in paco_request). |
| In-flight P6 #34 self-catch | PD first-draft reproduced both phone + adminpass literals while documenting F3; caught pre-commit; atomic-rewrote | Cannot re-verify since rewrite was atomic in working tree pre-commit. Trust PD self-report; consistent with discipline pattern. |

No discrepancies. PD's analysis is precise across all 3 findings.

## Ruling 1 -- F1: Line-citation amendment APPROVED (cosmetic)

Line citations corrected this commit:
- `docs/paco_response_atlas_v0_1_phase6_confirm_phase7_go.md` Ruling 7: "per build spec lines 449-487" -> "per build spec lines 427-451"
- `docs/handoff_paco_to_pd.md`: "Spec: tasks/atlas_v0_1_agent_loop.md lines 449-487" -> "427-451"

No history-rewrite. Forward-correction only.

## Ruling 2 -- F2: Read 1 RATIFIED (directive-as-canon; spec amended)

PD's Read 1 analysis is correct. The deferred-deferred pattern is the tell:

When I authored the Phase 6 GO directive, I included `mercury_start` / `mercury_stop` as v0.1 stubs with explicit `TODO(Phase 7): implement real start with cancel-window via communication.py`. PD wrote those TODOs verbatim into mercury.py. The Phase 6 review documented the stub-then-Phase-7-wire seam. The Phase 7 GO directive then included 7.2 to honor that stage-deferral.

**The failure mode:** I authored the deferral into mercury.py docstrings (Phase 6 commit `10adf9f`) but never amended the Phase 7 spec section (lines 427-451) to match. The same author held the deferral context in working memory across two phase boundaries but failed to sync it back to canon.

**This is P6 #33 again, third instance.** P6 #33 was banked Day 78 morning (Phase 3 atlas.events->atlas.tasks override). Second instance was Phase 5 path correction (caught at directive-author time = success). Third instance now: Phase 7 7.2 scope. The first instance escalated; the second was caught early; this third instance was caught by PD pre-execution. The mitigation pattern is working but the recurrence pattern shows P6 #33 needs a stronger Paco-side guard.

**Standing practice strengthening (Paco-side):** When authoring any phase GO directive, I cross-check the directive against the spec for that phase AND check whether prior phase artifacts (code TODOs, commit messages, Paco's own handoffs) have introduced deferrals that should have been amended into spec. Spec sync is part of close-confirm, not just GO authoring.

Spec amendment shipped this commit. Phase 7 spec lines 427-451 replaced with: 7.1 communication.py (unchanged from original) + 7.2 mercury cancel-window wire-up (new) + amended acceptance criterion + secrets-scan note.

## Ruling 3 -- F3: Phone literal P5 v0.1.1 canon-hygiene audit RATIFIED

Phone literal at spec line 437 confirmed. Per P6 #34: rotation + audit, not just redaction.

**Forward-redaction this commit:** Spec line 437 amended -- literal phone number replaced with generic reference ("the SLOAN_PHONE_NUMBER env var"). History at HEAD `22e10ec` retains the literal as known-exposure-pre-rotation per P6 #34 forward-redaction discipline (history-rewrite for internal personal phone is theater; same as adminpass case).

**Audit task added:** P5 v0.1.1 canon-hygiene audit task ratified. Scope:
- grep all canon for literal Sloan-mobile (10-digit pattern) and other PII (full address; full DOB; etc.) -- specific value not reproduced here per P6 #34
- Forward-redact in working tree where found
- Add findings to known-exposure inventory in CHECKLIST
- Track adjacent to Mercury weak-credential rotation candidate
- NOT blocking Phase 7-10 (forward-redaction in working tree is sufficient for cycle continuation)

**Updated exposure inventory:** Day 78 morning + this turn:
- 16 known locations of `adminpass` literal (per P6 #34 banking)
- 1 known location of phone literal (`tasks/atlas_v0_1_agent_loop.md` line 437; redacted forward this commit; history retained)

Full audit deferred to v0.1.1 -- counts may grow after grep across all repos.

## Ruling 4 -- PD's in-flight P6 #34 self-catch RATIFIED as discipline win

PD's first-draft of `paco_request_atlas_v0_1_phase7_directive_spec_divergence.md` reproduced both the phone number and the adminpass literal while documenting F3. Caught pre-commit (before secrets-scan). Atomic-rewrote both literals out before staging.

This is the strongest possible application of P6 #34 mitigation: "never quote credential values in new artifacts" caught at the artifact-author stage by the same author. PD recognized the propagation risk in their own draft and corrected before any persistence to disk.

Discipline metric +1 for PD: P6 #34 graduated from Day 78 morning banking (10:30) to applied-self-correction (15:16) in ~5 hours. That's the strongest possible test of a newly-banked discipline -- caught in the next own-authoring opportunity, not the next external review.

No new P6 needed. P6 #34 standing practice is working.

## Ruling 5 -- Phase 7 GO REMAINS ACTIVE with corrected scope

PD proceeds to:
- Step 5 live probe (atlas-mcp / atlas-agent / mercury-scanner / B2b anchor / Garage anchor / atlas.events schema)
- Twilio SDK presence check on Beast atlas venv (P6 #29 verification)
- atlas.events schema verification on Beast Postgres replica
- communication.py author per amended spec lines 427-451
- mercury_start / mercury_stop cancel-window wire-up per Phase 7.2 (NEW; amended spec)
- Pre-commit BOTH broad-grep AND tightened-regex secrets-scan before any atlas commit

**Acceptance Phase 7 (amended):**
- emit_event writes correctly for all 3 tiers (info/warn/critical -> Tier 1/2/3)
- atlas.events row appears with correct severity + payload + tier metadata
- dispatch_telegram works in mock mode (logs intended message when TWILIO_ENABLED=false; when creds present, real-message arrives at Sloan's phone)
- mercury_start/mercury_stop cancel-window wired (15s pre-execute window with task-status recheck via emit_event Tier 2)
- standing gates 6/6 preserved
- pre-commit BOTH broad-grep AND tightened-regex secrets-scan clean

## State at close

- atlas HEAD: `147f13c` (unchanged)
- HEAD on control-plane-lab: `f669ea9` (PD's paco_request) -> will move to next commit with this paco_response + spec amendment + audit
- atlas-mcp.service: MainPID 2173807 unchanged
- atlas-agent.service: disabled inactive unchanged
- mercury-scanner.service: MainPID 643409 unchanged
- B2b + Garage anchors: bit-identical (per canon; PD will re-probe at Step 5)
- 5 paco_requests now / 5 caught at PD pre-execution review (3rd P6 #33 instance + first F3 P6 #34 self-catch)
- 34 P6 lessons banked / 6 standing rules
- adminpass exposures: 16 known + 1 phone literal = 17 total known canon-hygiene exposures pending P5 v0.1.1 rotation/audit cycle

## Cycle progress

7 of 10 phases complete; Phase 7 GO active with corrected scope:

```
[x] Phase 0  Pre-flight
[x] Phase 1  systemd unit
[x] Phase 2  Agent loop skeleton
[x] Phase 3  Domain 1 Infrastructure
[x] Phase 4  Domain 2 Talent
[x] Phase 5  Domain 3 Vendor & admin
[x] Phase 6  Domain 4 Mercury supervision
[~] Phase 7  Communication helper (active; spec amended this turn; 7.1 emit_event + 7.2 mercury cancel-window wire-up)
[ ] Phase 8  Tests
[ ] Phase 9  Production deployment
[ ] Phase 10 Ship report
```

---

**Commits shipped this turn:**
- `tasks/atlas_v0_1_agent_loop.md` -- Phase 7 spec amended (7.2 added; phone literal redacted)
- `docs/paco_response_atlas_v0_1_phase6_confirm_phase7_go.md` -- line-citation correction
- `docs/handoff_paco_to_pd.md` -- line-citation correction + 7.2 confirmed in scope (was already there; cleaning citation only)
- `docs/paco_response_atlas_v0_1_phase7_directive_spec_divergence.md` -- this file (NEW)
- `CHECKLIST.md` -- audit #117 + Day 78 rollup updated
- `docs/feedback_paco_pre_directive_verification.md` -- P6 #33 third-instance note (no new P6 entry; same lesson)

-- Paco
