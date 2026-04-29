# feedback_phase_closure_literal_vs_spirit

**Banked:** 2026-04-29 / Day 74
**Originated:** H1 Phase H ESC #1 (dashboard 3662 renders N/A)
**Companion to:** feedback_directive_command_syntax_correction_pd_authority.md (5-guardrail rule), feedback_paco_review_doc_per_step.md (per-step review), feedback_paco_pd_handoff_protocol.md (handoff protocol)

## Purpose

Define the closure pattern for phases where **literal acceptance gates all PASS** but **spirit-of-test is partial**. Sets the default decision boundary so PD doesn't have to escalate every literal-PASS-but-imperfect case, and Paco doesn't have to re-rule the same architectural question per phase.

## The pattern

A phase has acceptance gates authored at spec-write time (e.g., "4-gate scorecard for Phase H"). The gates use specific wording (e.g., "at least one node_exporter target renders live data"). At test time, the gates literally PASS, but a reasonable reading of the test's underlying intent is partial.

Classic case (this banking origin): "Both provisioned dashboards visible AND at least one renders live data." Both visible (Gate 3) + Node Exporter Full renders (Gate 4 literal) = 4/4 PASS. But spec spirit was "both dashboards work end-to-end." Dashboard 3662 N/A is a partial.

## Standing rule

When a phase's literal acceptance gates all PASS but the test's spirit-of-completion is partial, default to **close at literal scorecard + bank residue as P5 carryover**, NOT escalate, when ALL of the following conditions hold:

1. **Literal gates met as authored** -- no creative re-reading of gate wording. The gate said "at least one," one passed, that's literal-PASS.
2. **Failure is contained + visible** -- the broken state is observable to operators (not silently hidden), and the breakage is bounded to a known artifact (one dashboard, one optional service, one nice-to-have feature).
3. **No substrate impact** -- anchors bit-identical, no service degradation, no security regression, no data-integrity risk.
4. **Inline-fix carries non-trivial risk** -- the in-phase fix would require research / external validation / multi-step changes that could trigger downstream ESCs.
5. **P5 scope is appropriate** -- the fix belongs in a hardening pass, not the build phase.

If ANY condition fails, escalate via paco_request for path ruling instead.

## When this rule does NOT apply

- Gate wording was ambiguous + the test result is genuinely both-readings (escalate, ratify the literal reading explicitly, then close)
- The "partial" failure compromises the phase's substantive deliverable (escalate; partial completion is not closure)
- The failure is silent (not observable to operators) -- silent failures are never P5; they're always ESC
- The failure threatens substrate / anchors / security -- always ESC
- The inline-fix is genuinely cheap + low-risk (e.g., a one-line config edit with no downstream consequences) -- prefer Path B inline-fix over Path A close + P5

## Required documentation when closing under this pattern

The paco_review must explicitly include:

1. **"Known limitations at ship"** section acknowledging the spirit-partial nature of closure
2. **P5 carryover citation by reference** with specific scope + candidate paths-forward
3. **Inline-fix rejection rationale** -- which of conditions 1-5 applied to this case, and which made inline-fix the wrong call
4. **Spec amendment** -- if applicable, a one-line note in the spec cross-referencing the P5 (so future readers know the broken-state is known + tracked, not unintentional)

## Why this rule exists (what problem it solves)

Without this rule, every literal-PASS-but-imperfect case becomes an ESC requiring Paco architectural ruling. That's:

- Velocity drag on PD (each ESC is a paco_request + paco_response roundtrip)
- Paco context overhead (re-rule the same architectural question per phase)
- Premature optimization risk (inline-fix attempts that introduce more churn than they prevent)

With this rule, PD has a clean default for the common case (close + P5) and a clear trigger for escalation (any condition fails -> ESC).

## Why this rule does NOT erode discipline

The 5 conditions are concrete and verifiable. Condition 1 (literal-as-authored) prevents creative re-reading. Condition 4 (inline-fix risk must be real) prevents handwaving. Condition 3 (no substrate impact) preserves the hard invariant. Conditions 2 + 5 keep scope honest.

PD applying this rule still writes a paco_review with the closure-pattern documentation per requirements above; Paco still independently verifies. The rule shifts the *default* without removing the *gate*.

## Banked context (origin)

H1 Phase H ESC #1, 2026-04-29 Day 74:

- Dashboard 3662 (Prometheus 2.0 Overview) renders all panels N/A under Grafana 11.3.0
- Root cause: deprecated singlestat panel + old variable query syntax; Grafana 11 auto-migration insufficient
- Datasource + provisioning + container stack healthy (Node Exporter Full 1860 renders cleanly with same datasource)
- Literal Gate 4 ("at least one node_exporter target renders live data") satisfied by 1860
- Inline-fix (Path B) would require dashboard candidate research + validation (no obvious Grafana-11-tested replacement available off-the-shelf)
- P5 carryover banked with 3 candidate replacements (15489 "Prometheus 2.0 Stats" / 3681 "Prometheus2.0 by FUSAKLA" / hand-rolled minimal) for v0.2 evaluation
- All 5 conditions for this rule satisfied
- Phase H closed under this pattern

First case to set the precedent. Future literal-PASS-spirit-partial cases follow this pattern unless a condition fails.
