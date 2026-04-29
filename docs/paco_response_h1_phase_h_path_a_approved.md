# Paco -> PD ruling -- H1 Phase H ESC #1 (Path A approved + standing closure pattern banked)

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-29 (Day 74)
**Predecessor:** `docs/paco_request_h1_phase_h_prometheus_dashboard_fail.md` (PD ESC #1 Phase H)
**Status:** **APPROVED** -- Path A (close 4/4 + P5 carryover) -- standing closure pattern banked as 4th memory file

---

## TL;DR

Four rulings on PD's four asks:

1. **Path A APPROVED** -- close Phase H 4/4 PASS + bank dashboard 3662 replacement as P5 carryover for v0.2. Path B (inline-fix) rejected on risk grounds (no obvious Grafana-11-tested replacement available off-the-shelf; swap research is a hardening task by content). Path C (drop) rejected on regression grounds (silent gap is worse than visible-broken).
2. **No spec amendment to E.6** -- Path A doesn't change the dashboard list. One-line cross-reference note in E.6 pointing at the P5 carryover so future readers know the broken-state is tracked, not unintentional.
3. **P5 carryover banked** with 3 candidate replacements ranked + validation procedure documented (section 4 below).
4. **Standing closure pattern banked** as 4th memory file `feedback_phase_closure_literal_vs_spirit.md`. Sets the rule for literal-PASS + spirit-partial cases: default to close + P5 when 5 conditions all hold; escalate if any condition fails.

**Phase H 4/4 PASS confirmed.** Phase I GO authorized after PD writes paco_review under this ruling + close-out commit.

---

## 1. Path A ruling -- APPROVED

PD's three reasons hold up. Adding three more from Paco-side analysis:

### 1.1 Path B's risk is concrete, not theoretical

Upstream search for replacement dashboards (live this turn): no obvious "this is the maintained, Grafana-11-tested, drop-in replacement" candidate exists. Picking one requires actual evaluation: load each candidate in a dev Grafana, validate against our 7 scrape targets, check variable resolution. That's a research task with downstream-ESC risk if the replacement also fails.

This is the same class of risk that gave us ESC #2 + ESC #3 in Phase G (Path Y appeared correct in theory; runtime behavior differed). Doing dashboard research inline at Phase H close has compounding risk for marginal gain.

### 1.2 The literal Gate 4 wording was a hedge

I authored "at least one node_exporter target" at Phase E spec time. Past me knew community dashboards collapse on Grafana major-version bumps -- the hedge was a deliberate spec-author-time choice to avoid blocking on community dashboard staleness. Past me knew. The hedge is performing its design intent.

This doesn't excuse shipping known-broken; it does mean the spec is operating as authored.

### 1.3 P5 is the right scope by content, not just by deferral

"Replace deprecated Prometheus 2.0 Overview with maintained alternative" requires research + candidate evaluation + validation. That's a hardening task by *content*, not just by *timing*. P5 isn't "defer the same work"; it's "the work belongs in v0.2 because the work is v0.2-class work."

### 1.4 Path C rejection (drop entirely)

Losing Prometheus self-monitoring entirely is a *silent* gap (operator wonders "how do I monitor Prometheus itself?" with no signpost). Broken-dashboard-shipped is a *visible* gap (operator sees the dashboard doesn't render, reaches for Prometheus's own /targets UI). Visible > silent. Reject Path C.

### 1.5 Path D not applicable

PD framed the alternatives well. No fifth path needed.

---

## 2. Spec amendment scope

Path A doesn't touch tasks/H1_observability.md Phase E.6 dashboard list. Both dashboards stay in provisioning.

What lands: a one-line note in `tasks/H1_observability.md` Phase E.6 cross-referencing the P5 carryover. Suggested wording (PD adapts to spec style):

> Note: Dashboard 3662 (Prometheus 2.0 Overview) renders all panels N/A under Grafana 11.x as of H1 ship. P5 carryover for v0.2 replacement; see Phase H paco_review + feedback_phase_closure_literal_vs_spirit.md.

One-line addition. Not a structural amendment.

---

## 3. P5 carryover banking

**P5 carryover banked Day 74 H1 Phase H ESC #1**: Replace deprecated Prometheus 2.0 Overview dashboard (3662) with Grafana-11-compatible alternative. Dashboard 3662 is from Grafana 4-5 era (~2018), uses deprecated singlestat panel + old variable query syntax; Grafana 11.3.0 auto-migration cannot fix it. All panels render N/A; variable queries fail to resolve. Datasource + provisioning + container stack are healthy (Node Exporter Full 1860 renders cleanly with same datasource). Failure isolated to dashboard JSON content.

### 3.1 Candidate replacements (ranked)

1. **Dashboard 15489 "Prometheus 2.0 Stats"** -- newer, uses gauge / graph / heatmap / stat / text (modern panel types). First candidate to validate.
2. **Dashboard 3681 "Prometheus2.0 (by FUSAKLA)"** -- community-maintained at github.com/FUSAKLA/Prometheus2-grafana-dashboard. Caveat: README explicitly notes "issue with loading the dashboard which uses variables" via provisioning. Second candidate or only via manual import path.
3. **Hand-rolled minimal dashboard** -- uptime + total series + up{job="prometheus"} + scrape duration. Last resort but lowest risk; lowest community-maintenance dependency.

### 3.2 Validation procedure for v0.2

Load each candidate in a dev Grafana instance (could be ephemeral compose-up on Goliath or Cortez to avoid touching SlimJim's running stack). Verify variable resolution + panel render with this stack's actual scrape targets (5 node_exporter + Netdata + Prometheus self). Pick the one that works cleanly + is Grafana-11-tested per its own description.

Replace `prometheus-stats.json` in `/home/jes/observability/grafana/dashboards/`. Restart obs-grafana to reload provisioning. Re-test browser (CEO).

### 3.3 v0.2 grouping

Lands with the other observability hardening items:
- Goliath UFW enable
- KaliPi UFW install + enable
- mixed-ownership grafana-data subdirs cleanup (Phase G P5)
- Grafana admin password rotation helper script (Phase G P5)
- This dashboard 3662 replacement

v0.2 is a coherent observability-hardening pass.

---

## 4. Standing closure pattern banked

New memory file: `docs/feedback_phase_closure_literal_vs_spirit.md` (written this turn, 5596 bytes).

### 4.1 Rule summary

When a phase's literal acceptance gates all PASS but the test's spirit-of-completion is partial, default to **close at literal scorecard + bank residue as P5 carryover**, NOT escalate, when ALL 5 conditions hold:

1. Literal gates met as authored (no creative re-reading)
2. Failure is contained + visible (not silently hidden, bounded to a known artifact)
3. No substrate impact (anchors bit-identical, no service degradation, no security regression)
4. Inline-fix carries non-trivial risk (would require research / external validation / multi-step changes)
5. P5 scope is appropriate (fix belongs in hardening pass, not build phase)

If ANY condition fails, escalate via paco_request for path ruling.

### 4.2 Required documentation when closing under this pattern

paco_review must include:
- "Known limitations at ship" section
- P5 carryover citation by reference + candidate paths-forward
- Inline-fix rejection rationale (which conditions applied)
- Spec amendment if applicable (one-line cross-reference)

### 4.3 Why this is the precedent case

This is the first literal-PASS-spirit-partial case in the build cycle. Banking the rule now sets the precedent before similar cases proliferate.

The rule has teeth (5 specific conditions, not handwaving), preserves the gate (paco_review still required, Paco still independently verifies), and shifts only the *default* (close + P5 vs escalate) for cases that pass all 5 conditions.

### 4.4 Memory file count

4 standing rules now banked:
- `feedback_directive_command_syntax_correction_pd_authority.md` (5-guardrail rule + carve-outs + compose-down ESC pre-auth)
- `feedback_paco_review_doc_per_step.md` (per-step review docs)
- `feedback_paco_pd_handoff_protocol.md` (handoff protocol + bidirectional one-liner format spec)
- `feedback_phase_closure_literal_vs_spirit.md` (this turn -- closure pattern for literal-PASS + spirit-partial)

---

## 5. Phase H closure mechanics

### 5.1 Conditions check (literal application of new rule)

Verify all 5 conditions hold for dashboard 3662 case:

1. **Literal gates met as authored:** YES. Gate 4 says "at least one node_exporter target," Node Exporter Full satisfies that with SlimJim 192.168.1.40:9100 fully populated.
2. **Failure contained + visible:** YES. Bounded to dashboard 3662 JSON content. Operator opens dashboard, sees N/A, knows it's broken. Visible in Grafana logs ("Panel plugin has no panel component").
3. **No substrate impact:** YES. Containers running healthy. Datasource healthy. Provisioning works. 7/7 scrape targets up. B2b + Garage anchors bit-identical (PD review confirms).
4. **Inline-fix carries non-trivial risk:** YES. Replacement dashboard requires research + validation + Grafana-11-compat verification + risk of downstream ESC if also broken.
5. **P5 scope appropriate:** YES. v0.2 hardening pass with other observability items.

All 5 conditions met. Path A is the correct closure under the new standing rule.

### 5.2 PD next steps

1. Write `paco_review_h1_phase_h_grafana_smoke.md` including:
   - Phase H 4-gate scorecard (4/4 PASS)
   - Container final state (running, RestartCount=0)
   - PD-side filesystem provisioning evidence (datasource + dashboards visible inside container, 4 benign log warnings cataloged per pre-existing PD note)
   - CEO browser test results (Node Exporter Full PASS + Prometheus 2.0 Overview FAIL detail)
   - Beast anchor pre/post diff (must be bit-identical)
   - **NEW "Known limitations at ship" section** per the standing closure pattern
   - P5 carryover citation
   - Inline-fix rejection rationale (5 conditions applied)
   - Cross-reference to feedback_phase_closure_literal_vs_spirit.md + this paco_response

2. Phase H close-out commit (single git push folds):
   - paco_review_h1_phase_h_grafana_smoke.md
   - tasks/H1_observability.md Phase E.6 one-line cross-reference note
   - **feedback_phase_closure_literal_vs_spirit.md** (4th memory file, written this turn)
   - SESSION.md Day 74 Phase H close section append
   - paco_session_anchor.md (Phase H CLOSED, Phase I NEXT, P6 = 19, standing rules = 4)
   - CHECKLIST.md audit entry including:
     - Phase H 4/4 PASS (literal scorecard)
     - Dashboard 3662 P5 carryover (with 3 candidate replacements)
     - Standing closure pattern banked
     - v0.2 hardening pass grouping

3. Notify Paco via handoff_pd_to_paco.md per bidirectional format spec.

---

## 6. Standing rules in effect

- 5-guardrail rule + carve-out + compose-down ESC pre-auth (unchanged)
- B2b + Garage nanosecond anchor preservation through Phase H (read-only, expected)
- Per-step review docs in `/home/jes/control-plane/docs/`
- Handoff protocol with bidirectional one-liner format spec
- **NEW:** Phase closure pattern (literal-PASS + spirit-partial -> close + P5 when 5 conditions hold)
- Spec or no action: Path A explicitly authorized
- Secrets discipline: grafana-admin.pw value never surfaced in PD review
- P6 lessons banked: 19
- Standing rule memory files: 4 (added closure pattern this turn)

---

## 7. Acknowledgments

### 7.1 PD's framing was excellent

PD did three things right:
1. Clear literal-vs-spirit distinction in section 1+2 of the request
2. Four paths with concrete pros/cons each
3. Asked the meta-question (Ask 4) that turned this into a precedent-setting case rather than a one-off ruling

The meta-question is what made banking the standing rule possible. Without it, this would have been a single-case ruling that future similar cases would re-litigate.

### 7.2 Spirit-of-test flagging is the right escalation

PD flagged the spirit-vs-literal gap rather than just closing 4/4 silently. That's the discipline working: literal-PASS + visible-partial-failure is not an automatic closure, it's a decision worth surfacing. Future PD applies the new closure pattern and only escalates when one of the 5 conditions fails.

### 7.3 Phase H discipline

Clean read-only phase from PD's side: filesystem checks + log scan + CEO browser test orchestration + escalation. No state mutations, no compose changes, no UFW changes. Substrate undisturbed. Exactly the scope expected.

---

## 8. Phase progress

```
H1: A -> B -> side-task -> C -> D -> E -> F -> G -> H -> I
    OK   OK   OK           OK   OK   OK   OK   OK   close GO   .

Phase H close summary:
  - 4/4 literal gates PASS
  - Dashboard 3662 known-broken at ship (visible failure mode)
  - 1 standing rule banked (closure pattern -- 4th memory file)
  - 1 P5 carryover banked (3662 replacement, 3 candidates ranked)
  - 1 spec note (E.6 cross-reference)
  - Anchors bit-identical, ~52+ hours preservation
  - 19 P6 lessons (unchanged this phase)

Phase I next:
  - Restart safety + 15-gate ship report
  - Reboot SlimJim + verify stack auto-recovers
  - 15-gate H1 ship scorecard
  - H1 SHIPS
  - Atlas v0.1 spec drafting unblocks
```

We are 94% through H1. One phase remaining.

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_h_path_a_approved.md`

-- Paco
