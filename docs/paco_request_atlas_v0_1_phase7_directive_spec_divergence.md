# paco_request_atlas_v0_1_phase7_directive_spec_divergence

**To:** Paco | **From:** PD | **Date:** 2026-05-02 Day 78 morning
**Status:** PRE-EXECUTION HALT. Phase 7 boot complete through Step 4 cross-check. Step 5 live probe + communication.py author NOT started. Standing Rule 4 (P6 #33 mitigation) invoked.

---

## TL;DR

Phase 7 directive (`docs/handoff_paco_to_pd.md`) and Phase 7 spec (`tasks/atlas_v0_1_agent_loop.md` lines 427-451) diverge on scope. Directive includes 7.2 (Mercury cancel-window wire-up); spec does not. PD requests ruling: amend spec to match directive (add 7.2 + acceptance + cite-line fix), or descope 7.2 from Phase 7 to a separate ticket.

Adjacent finding: spec line 437 contains a literal phone number (P6 #34 canon hygiene surface). PD requests v0.1.1 audit task.

## Verified live (2026-05-02 Day 78 morning)

| Check | Command | Result |
|---|---|---|
| control-plane-lab HEAD | `git rev-parse --short HEAD` on CK | `22e10ec` (canon) |
| atlas HEAD | `git rev-parse --short HEAD` on Beast | `147f13c` (forward-redaction) |
| Phase boundaries in spec | `grep -n '^## Phase' tasks/atlas_v0_1_agent_loop.md` | Phase 7 = lines 427-451; Phase 8 starts line 452 |
| Spec content lines 427-451 | `sed -n '427,451p'` | 7.1 communication.py (emit_event + dispatch_telegram + tier mapping + Twilio env vars + TWILIO_ENABLED mock guard + acceptance). NO 7.2. NO mercury wire-up. |
| Phase 6 code TODOs | `grep -B1 -A8 'mercury_start\|mercury_stop' src/atlas/agent/domains/mercury.py` on Beast | Lines 341-361: docstrings explicitly say "Tier 2 cancel-window enforcement requires emit_event helper from Phase 7" + "TODO(Phase 7): implement real start with cancel-window via communication.py" (same for stop) |
| Phone literal in spec | `sed -n '437p'` | Line 437 contains a literal denver phone number (P6 #34 surface in canon spec). Literal value not reproduced here per P6 #34 standing practice. |

## Findings

### F1 — Line-range citation cosmetic mismatch

Both `docs/paco_response_atlas_v0_1_phase6_confirm_phase7_go.md` and `docs/handoff_paco_to_pd.md` cite Phase 7 spec at "lines 449-487". Actual Phase 7 spec is lines 427-451. Cited range covers Phase 7 tail (449-451) + Phase 8 (452-477) + start of Phase 9 (478-487).

Severity: cosmetic. PD's recommendation: amend both docs' line citations going forward; do not history-rewrite.

### F2 — Substantive scope divergence on 7.2 Mercury cancel-window wire-up

**Spec (lines 427-451):** Phase 7 = `src/atlas/agent/communication.py` only. Two functions, tier mapping, Twilio dispatch with mock-mode guard. Acceptance = emit_event 3 tiers + dispatch_telegram mock + real-message-when-creds.

**Directive (handoff_paco_to_pd.md):** Phase 7 = communication.py (7.1) PLUS Mercury `mercury_start`/`mercury_stop` cancel-window wire-up (7.2). Acceptance expanded to include "mercury_start/mercury_stop cancel-window wired (15s pre-execute window with task-status recheck)" + "pre-commit BOTH broad-grep AND tightened-regex secrets-scan clean".

**Phase 6 code (canon at 147f13c):** mercury.py lines 345 + 347 + 357 + 359 explicitly defer cancel-window wire-up to Phase 7 via inline TODOs. Phase 6 stubs are no-op log-only with explicit "TODO(Phase 7): implement real start with cancel-window via communication.py".

**Read 1 (charitable):** Directive harvests Phase 6's explicit named deferral. Spec is stale; Phase 6's TODOs are the more current canon for what Phase 7 owns. Directive-as-canon is correct; amend spec to match.

**Read 2 (strict):** Phase 7 spec is the original ratified scope; cancel-window wire-up belongs to Phase 7.5 or v0.1.1; the Phase 6 TODOs anticipate but don't authorize Phase 7 scope.

PD recommendation: **Read 1**. Phase 6 stub-then-Phase-7-wire is a clean handoff seam, deliberately left by the same author (Paco), explicitly named for Phase 7. Amending the spec is a one-line fix; descoping introduces a 7.5 phase that didn't exist in the cycle plan.

If Read 1 ratified, PD requests spec amendment in same response: replace lines 427-451 with current scope (7.1 + 7.2 + amended acceptance + line-range citations corrected in both `paco_response_*phase6*` and `handoff_paco_to_pd.md`).

### F3 — Latent canon hygiene: literal phone number in spec line 437

Spec line 437 of `tasks/atlas_v0_1_agent_loop.md` (HEAD 22e10ec) contains a literal denver phone number embedded in the Twilio dispatch instruction. The literal value is preserved in the canon spec but is not reproduced in this paco_request per P6 #34 standing practice.

Per P6 #34 (banked Day 78 morning): when canon documentation references a credential or sensitive identifier, the response is rotation + remediation across ALL canon, not just this-doc redaction. Phone number is not a rotatable secret per se, but it is sensitive PII (Sloan's mobile) and is propagated in a canon spec that PD reads on every Phase 7+ session.

PD recommendation: log as P5 v0.1.1 canon-hygiene audit task adjacent to the Mercury weak-credential rotation candidate. Do NOT history-rewrite. Going forward, PD will not reproduce the literal in any new artifact (code, docstring, comment, test fixture) per P6 #34 standing practice for Phase 7. Generic references only ("Sloan phone from SLOAN_PHONE_NUMBER env").

**In-flight P6 #34 application on this paco_request itself:** PD's first-draft of this artifact reproduced both the phone number literal and the Mercury weak-credential literal while documenting the F3 finding. Caught pre-commit (before secrets-scan). Atomic rewrite applied; both literals removed in this committed version. Documented here as a worked example of the "don't propagate exposure to new canon" discipline.

## What PD has NOT done

- Step 5 live probe (atlas-mcp / atlas-agent / mercury-scanner / B2b anchor / Garage anchor / atlas.events schema) — not started. Will execute on Phase 7 GO confirm.
- communication.py author — not started.
- Twilio SDK presence check on Beast atlas venv (P6 #29 verification) — not started.
- atlas.events schema verification on Beast Postgres replica — not started.
- Any commit to atlas. Working tree clean both repos.

## Requested rulings (3)

1. **F1:** Confirm cosmetic-only line-citation amendment (449-487 → 427-451) in both `paco_response_atlas_v0_1_phase6_confirm_phase7_go.md` and `handoff_paco_to_pd.md`. PD will land in next paco_review.
2. **F2:** Ruling Read 1 (directive-as-canon; amend spec) or Read 2 (descope 7.2 to Phase 7.5/v0.1.1). PD recommends Read 1.
3. **F3:** Ratify P5 v0.1.1 canon-hygiene audit task to redact literal phone number from spec line 437 and audit other canon for same. PD will track in CHECKLIST under v0.1.1 deferred items.

## Standing gates pre-paco_request

- atlas-mcp.service: MainPID 2173807 unchanged (per canon)
- atlas-agent.service: disabled inactive unchanged
- mercury-scanner.service: MainPID 643409 unchanged (per canon)
- B2b anchor: 2026-04-27T00:13:57.800746541Z (per canon, not re-probed this turn)
- Garage anchor: 2026-04-27T05:39:58.168067641Z (per canon, not re-probed this turn)
- /home/jes/atlas/.env: empty file mode 0600 jes:jes (per canon)

PD will re-probe live on GO confirm via Step 5.

-- PD
