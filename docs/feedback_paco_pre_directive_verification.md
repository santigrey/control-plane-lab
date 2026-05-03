# feedback_paco_pre_directive_verification

**Banked:** 2026-04-30 / Day 75
**Last canon update:** 2026-05-03 / Day 79 evening (Patch Cycle 1 close-confirm propagation; +P6 #37)
**Originated:** Atlas v0.1 Cycle 1A preflight ESC + CEO discipline RFC after 3 consecutive Paco-side spec errors in 24-72 hours
**Companion to:** feedback_directive_command_syntax_correction_pd_authority.md, feedback_paco_review_doc_per_step.md, feedback_paco_pd_handoff_protocol.md, feedback_phase_closure_literal_vs_spirit.md

---

## Cumulative state

**P6 lessons banked: 37** (last update Day 79 evening; +P6 #37 banked at Patch Cycle 1 close)
**Standing rules: 7** (last update Day 79 early morning; +SR #7 since prior ledger refresh)

**Critical for new Cowork sessions:** This ledger is the source of truth for cumulative count. PD-side must reconcile against THIS file's cumulative section, not against memory-of-prior-cycles. PD's Phase 9 review correctly flagged a propagation gap (ledger said 34/6; close-confirm canon said 35/7); the gap is closed in this Day 79 early morning update.

---

## Standing rules (cumulative through Day 79 early morning)

**SR #1** (Day 75): Pre-directive verification — every directive must contain a Verified-live block proving the directive's claims about source surface, schema, runtime state are true at directive-author time, not assumed from memory.

**SR #2** (Day 75): Spec sync gates close-confirm — when directive supersedes spec, the close-confirm must amend spec to match new canon OR document the divergence as intentional permanent override.

**SR #3** (Day 75): One-step-at-a-time during execution — PD does not chain steps; CEO gates each transition.

**SR #4** (Day 75): Path B authorization — PD may adapt directive to ground truth at pre-execution time only when directive's stated assumption is empirically false; documents adaptation in review for Paco ratification at close-confirm.

**SR #5** (Day 75): Cross-check directive against spec at every author point — includes prior-phase deferrals (TODOs, commit messages, prior handoffs) that should have been amended into spec.

**SR #6** (Day 76): Self-state probe before drawing conclusions — at session resume or before any conclusion-drawing turn, re-verify external runtime state vs in-context memory of prior turn's state. Trust running infrastructure over prior-turn assumption.

**SR #7** (Day 78 evening, banked Phase 8 close-confirm): Test-directive source-surface preflight — when authoring a directive that specifies test cases or asserts source-surface shape (file paths, function signatures, schema columns, kind enum values, table names), Paco runs the same probes PD would run at pre-execution time BEFORE writing the directive. Probe outputs land in directive's Verified-live block. Mitigates the cluster-of-corrections pattern PD-side that costs ~15min per round-trip.

---

## P6 lesson highlights (cumulative through Day 79 early morning)

P6 #1-32: see prior ledger entries; mostly authorship correctness lessons (memory-based errors).

**P6 #33** (Day 78 morning Phase 7 dispatch): Deferred-deferred sync gap — when same author stages a deferral across phase boundaries via code TODOs/handoff text, the spec must be amended at the same commit OR the deferral becomes a future P6 #33 instance.

**P6 #34** (Day 78 evening Phase 7 close-confirm): Forward-redaction discipline — BOTH broad-grep AND tightened-regex pre-commit secrets-scan applied to all new artifacts (including review files); literal-value sweep for known exposures (e.g. adminpass) as defense-in-depth; secrets-scan is mandatory at every commit, not just code-touching commits.

**P6 #35** (Day 78 evening Phase 8 close-confirm): Test-directive source-surface verification cluster — when a directive contains 5+ source-surface assertions caught by PD pre-execution as Path B adaptations in single phase, that's a cluster signal not a one-off. Root cause: Paco-side authoring discipline lagging PD-side execution discipline. Mitigation: SR #7 (above).

**P6 #36** (Day 79 early morning Phase 9 close-confirm; PD-proposed, Paco-ratified): Journalctl capture races journald buffer-flush — `journalctl -n N | tee` captures fewer lines than the same time-window query rerun later, because journald's emit-to-storage flush has latency. Step 4 captured 44 lines at write-time; +2.5h rerun showed 93 lines for same window. Mitigation paths: prefer `journalctl --since '<TS>' --until '<TS>' --no-pager` (no `-n` cap) for full-window capture, OR add `sleep 5` between observation-window-end and journalctl invocation to allow buffer-flush settle. Standardize for Phase 10 ship-report procedures.

**P6 #37** (Day 79 evening Patch Cycle 1 close-confirm; PD-proposed, Paco-ratified): Blast-radius categorization in package-upgrade directives — when directive enumerates package upgrade count without bundle-content inventory, high-blast-radius categories (kernel + GPU driver + container runtime + database + critical service binaries) must be called out so PD can pre-stage Path B verifications. Natural extension of SR #7. Catalyzed by Patch Cycle 1 Stage B Beast: directive said "45 packages upgraded" but missed that the bundle included NVIDIA driver 595.58.03->595.71.05 (dkms rebuild required + Tesla T4 health verification needed) and that Ollama runtime needed liveness re-check post-driver-rebuild. PD ratified both as Path B (B1) but should have been pre-staged in directive. Mitigation: when Paco-side preflight returns a kernel-or-driver-bumping package set, directive Verified-live block must include per-package category inventory + pre-staged Path B verifications for each high-blast-radius category. Applied retroactively from Patch Cycle 2 (Goliath) onward.

---

## Mitigation pattern (becomes standing practice for handoff/directive authors)

1. Before writing any handoff or cowork prompt, open the canonical spec for the relevant phase
2. Cross-check directive against spec sentence-by-sentence on key axes: file paths, table names, schema names, kind names, acceptance criteria, dependency names, cadence values
3. If directive matches spec verbatim: no further action
4. If directive diverges from spec: choose ONE of the resolution paths:
   - (a) Note the divergence + rationale at the top of the directive AND amend spec in same commit (preferred for substantively-correct overrides like substrate gaps)
   - (b) Escalate the divergence to CEO for explicit ratification BEFORE PD executes (preferred for novel decisions where Paco wants CEO judgment)
   - (c) Revise the directive to match the spec (preferred when the directive divergence was unintentional)
5. NEVER silently substitute directive text for spec text

**Cross-reference:** P6 #20-32 cover authorship correctness (memory-based errors). P6 #33 covers authorship consistency (divergence between canon artifacts by same author at different times). P6 #34-36 cover cumulative-count + verification + capture discipline. All are surface-specific applications of the same root principle: canon must be self-consistent and verifiable.

---

## Recurrence log

**Day 78 morning (P6 #33 origination):**
- Instance 1 (Phase 3): atlas.events->atlas.tasks override via silent handoff. PD caught at pre-execution; CEO ratified mid-execution; spec amended at close-confirm.
- Instance 2 (Phase 5): migrations/ -> src/atlas/db/migrations/ path correction. Caught at directive-author time (Paco-side); no PD round-trip needed. Discipline maturation point.
- Instance 3 (Phase 7): 7.2 mercury cancel-window wire-up. Same author (Paco) staged Phase 6 mercury.py TODOs deferring cancel-window to Phase 7, then authored Phase 7 directive including 7.2, but never amended Phase 7 spec section to match. PD caught at pre-execution Step 4 cross-check.

**Day 78 evening (P6 #35 cluster signal):**
- Phase 8 directive contained 5 source-surface assertions authored from memory of canonical Cycle 1I patterns instead of probing live Phase 3-6 source. PD caught all 5 at pre-execution (Path B adaptations Steps 2/5/6/7/8/9). Total Phase 8 PD overhead from Paco-side spec drift: ~75min.
- Mitigation: SR #7 banked + applied retroactively from Phase 9 onward.

**Day 79 early morning (SR #7 first-application validation):**
- Phase 9 directive: 4 spec corrections caught at directive-author time (Paco-side preflight, 12-row Verified-live block). PD pre-execution found ZERO additional divergences (Phase 9 review §2.2: "Path B adaptations: zero structural"). SR #7 paid for itself first application.
- Counter-instance: Phase 9 ledger-staleness: PD's Phase 9 review cited cumulative P6=34/SRs=6 from ledger file; canon (close-confirm artifacts) said 35/7. PD correctly flagged drift in handoff. Lesson: ledger file must be updated at every close-confirm that banks new lesson/rule, not just at periodic refresh. **This file's Day 79 early morning update closes that gap.**

---

## Standing practice strengthening (Paco-side, Day 79 early morning)

When Paco close-confirms a phase that banks a new P6 lesson or new SR:
1. Update this ledger file's `## Cumulative state` block in the same close-confirm commit
2. Update this ledger file's `## Standing rules` and/or `## P6 lesson highlights` block with the new entry
3. Update this ledger file's `## Recurrence log` with the originating instance
4. NEVER let the ledger lag the close-confirm canon

This is the propagation gap PD's Phase 9 review caught. Closed structurally going forward.
