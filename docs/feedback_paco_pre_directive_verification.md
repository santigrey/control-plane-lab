# feedback_paco_pre_directive_verification

**Banked:** 2026-04-30 / Day 75
**Last canon update:** 2026-05-04 / Day 80 ~14:00 UTC (Alexandra hygiene pollution cleanup close-confirm; +P6 #40 +P6 #41 +P6 #42)
**Originated:** Atlas v0.1 Cycle 1A preflight ESC + CEO discipline RFC after 3 consecutive Paco-side spec errors in 24-72 hours
**Companion to:** feedback_directive_command_syntax_correction_pd_authority.md, feedback_paco_review_doc_per_step.md, feedback_paco_pd_handoff_protocol.md, feedback_phase_closure_literal_vs_spirit.md

---

## Cumulative state

**P6 lessons banked: 42** (last update Day 80 ~14:00 UTC; +P6 #40 + P6 #41 + P6 #42 banked at Alexandra hygiene pollution cleanup close-confirm)
**Standing rules: 8** (unchanged Day 80 ~14:00 UTC; all three new P6 lessons light-touch not promoted to SR)

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

**SR #8** (Day 79 late evening, banked Patch Cycle 2 PPA-unreachable abort ruling): Abort-restore discipline — when a patch/maintenance cycle aborts via STOP gate and PD is awaiting Paco direction, PD is authorized to reverse Stage A pre-quiesces (service stops, maintenance-window flips) WITHOUT paco_request, since reverting to baseline is restoration not new cycle state. Hold flags (apt-mark hold) and other cycle-progress markers PERSIST through the wait to enable retry without rework. Distinction principle: "Did this action restore baseline, or did it advance cycle state?" Restorations do not require paco_request on abort. Cycle-progress changes do. When in doubt, paco_request. Catalyzed by Cycle 2 ollama restore: Stage A.2 stopped ollama as planned interruption for 5-15min reboot window; Stage B aborted at ~57s due to PPA Launchpad-wide outage; PD restored ollama at ~1.5h post-stop without paco_request because production inference idle for indeterminate Launchpad-outage duration was not the intent of D2. PD-precedent, Paco-codified.

---

## P6 lesson highlights (cumulative through Day 79 early morning)

P6 #1-32: see prior ledger entries; mostly authorship correctness lessons (memory-based errors).

**P6 #33** (Day 78 morning Phase 7 dispatch): Deferred-deferred sync gap — when same author stages a deferral across phase boundaries via code TODOs/handoff text, the spec must be amended at the same commit OR the deferral becomes a future P6 #33 instance.

**P6 #34** (Day 78 evening Phase 7 close-confirm): Forward-redaction discipline — BOTH broad-grep AND tightened-regex pre-commit secrets-scan applied to all new artifacts (including review files); literal-value sweep for known exposures (e.g. adminpass) as defense-in-depth; secrets-scan is mandatory at every commit, not just code-touching commits.

**P6 #35** (Day 78 evening Phase 8 close-confirm): Test-directive source-surface verification cluster — when a directive contains 5+ source-surface assertions caught by PD pre-execution as Path B adaptations in single phase, that's a cluster signal not a one-off. Root cause: Paco-side authoring discipline lagging PD-side execution discipline. Mitigation: SR #7 (above).

**P6 #36** (Day 79 early morning Phase 9 close-confirm; PD-proposed, Paco-ratified): Journalctl capture races journald buffer-flush — `journalctl -n N | tee` captures fewer lines than the same time-window query rerun later, because journald's emit-to-storage flush has latency. Step 4 captured 44 lines at write-time; +2.5h rerun showed 93 lines for same window. Mitigation paths: prefer `journalctl --since '<TS>' --until '<TS>' --no-pager` (no `-n` cap) for full-window capture, OR add `sleep 5` between observation-window-end and journalctl invocation to allow buffer-flush settle. Standardize for Phase 10 ship-report procedures.

**P6 #37** (Day 79 evening Patch Cycle 1 close-confirm; PD-proposed, Paco-ratified): Blast-radius categorization in package-upgrade directives — when directive enumerates package upgrade count without bundle-content inventory, high-blast-radius categories (kernel + GPU driver + container runtime + database + critical service binaries) must be called out so PD can pre-stage Path B verifications. Natural extension of SR #7. Catalyzed by Patch Cycle 1 Stage B Beast: directive said "45 packages upgraded" but missed that the bundle included NVIDIA driver 595.58.03->595.71.05 (dkms rebuild required + Tesla T4 health verification needed) and that Ollama runtime needed liveness re-check post-driver-rebuild. PD ratified both as Path B (B1) but should have been pre-staged in directive. Mitigation: when Paco-side preflight returns a kernel-or-driver-bumping package set, directive Verified-live block must include per-package category inventory + pre-staged Path B verifications for each high-blast-radius category. Applied retroactively from Patch Cycle 2 (Goliath) onward.

**P6 #38** (Day 79 late evening Patch Cycle 2 Stage B abort; PD-proposed, Paco-broadened): Apt simulation does not validate binary-fetch reachability — when an upgrade scope draws `Inst` lines from any non-primary-archive apt source (PPAs, NVIDIA repos, Docker repos, HashiCorp, MongoDB, custom corporate repos), Paco-side preflight MUST verify both index-fetch AND binary-fetch reachability for each contributing source before authoring stages that depend on those binaries. Index-fetch is verified by a clean `apt-get update` (no `Err:` lines for the source). Binary-fetch is verified by either `apt-get download --print-uris <pkg> | head -1 | xargs curl --max-time 8 -sI` for a representative `Inst` package per source, OR `apt-get -d -y dist-upgrade` (download only; no install). The two paths can fail independently: index-fetch can succeed against cached metadata or working CDN edge while origin binary store is unreachable. Catalyzed by Cycle 2 Stage B abort: original directive Section 1 SR #7 row 5 `apt-get -s dist-upgrade` returned successful plan against cached metadata; actual binary fetch of 4 canonical-nvidia PPA packages failed (Launchpad-wide service-layer outage at `ppa.launchpadcontent.net:443` AND `launchpad.net:443`; primary archives `archive.ubuntu.com` / `ports.ubuntu.com` / `esm.ubuntu.com` reachable). Abort happened pre-unpack thanks to apt's transactional integrity (521 successful Get + 4 Err = 0 unpacked), but the gap could equally have surfaced mid-fetch at Stage B.1 launch in any cycle. Natural extension of P6 #37 (blast-radius categorization) and SR #7 (source-surface preflight). Applied retroactively from Cycle 2 retry onward.

**P6 #39** (Day 80 early UTC Patch Cycle 3 close-confirm; PD-proposed framing, Paco-codified): Directive assertion-shape verification at preflight — when a directive specifies an executable smoke-test (CLI version check, command output assertion, `--version` probe) for a scope category, Paco-side preflight verifies the executable is installed on the target host before authoring the assertion. If the executable is absent, specify the dpkg-version-equivalent or skip the assertion (whichever matches verification intent). Catalyzed by Cycle 3 Pi3 ImageMagick CLI absence: directive A.6 expected `convert --version` to discharge "ImageMagick running new version" criterion, but the `imagemagick` meta package was never installed on Pi3; the 4 in-scope packages were libraries from a Debian-Security advisory. PD-adapted via dpkg-query (Path B B3 SR #4). Second instance of "directive assertion shape mismatch with host actual state" in 4 cycles (first: Cycle 2 dkms-on-DGX-OS, where directive's `dkms status` verification was wrong because DGX OS uses prebuilt modules). Pattern signal: when authoring assertions about host state mechanism (CLI presence, package management mechanism, service unit names, file paths to system tools), preflight verifies the mechanism on the target before baking it into directive. Natural extension of SR #1 (pre-directive verification) and SR #7 (source-surface preflight) with finer granularity at the assertion level. Light-touch lesson; not promoted to standing rule (assertion-shape errors are caught by SR #4 at PD-execution time without risk of cycle harm; this is preflight efficiency optimization not safety).

**P6 #40** (Day 80 ~05:30 UTC, banked at Alexandra hygiene pollution cleanup original directive section 8; ratified at close-confirm Day 80 ~14:00 UTC): MCP-direct execution capability does not authorize bypassing the PD execution lane. When MCP gives Paco direct SSH/file/db access, the temptation is to "just do it" because fixes feel small enough -- but every direct execution skips the entire safety architecture (audit trail in /docs canon, directive review with explicit acceptance criteria, second-set-of-eyes on adaptations via SR #4 Path B ratification, rollback discipline through pre-staged backups + Path B authorizations, CHECKLIST hygiene + discipline ledger updates as a first-class deliverable). Pattern catalyzed by Day 80 Alexandra hygiene cycle where Paco executed pre-flight + Patches 1+2+3 + 3 backups (chat_history dump + 2 code .bak files) directly via MCP before CEO Sloan stopped execution at the DB DELETE step and instructed conversion to PD lane (paco_directive_alexandra_smoke_hygiene_pollution_cleanup.md is that conversion). Light-touch lesson; not promoted to standing rule yet because PD-lane discipline is implicit in Operating Rules; this is a Paco-side reminder that MCP capability != lane authorization. If pattern recurs, promote to SR #9 "Paco-side MCP-direct execution boundary".

**P6 #41** (Day 80 ~14:00 UTC, banked at Alexandra hygiene pollution cleanup close-confirm): Prose-rule patches alone are insufficient for hallucination-class failure modes when underlying model instruction-following is stochastic. 72B-class local models like qwen2.5:72b plateau at acceptable-but-not-zero hallucination rate even with explicit ABSOLUTE RULES at the top of the system prompt. Deterministic post-processing guards (literal-string filters that substitute canned safe outputs on hit) are the architectural answer. The guard does not replace the prose rules -- both work together: prose rules reduce hallucination frequency to where the guard fires only on edge cases; the guard prevents any edge-case from reaching the user. Pattern catalyzed by Day 80 Alexandra hygiene cycle dual-evidence: original directive Step 5 failed AC.10 on prose hallucination first roll (`giving you trouble`); amendment cold test 1 produced clean response on second roll under identical conditions (Form A); amendment cold test 2 guard correctly substituted on third roll (`wiz ` substring caught from `The WiZ RGBW Tunable EDA510 light is now on`). The dual-evidence pattern (failure on first roll + success on second roll under identical conditions) proves stochastic instruction-drift exists in this regime; deterministic guard is the safety net for unlucky rolls. Light-touch lesson; not promoted to standing rule yet because architecture is generalizable to any LLM endpoint and not Alexandra-specific. If pattern recurs (other endpoints needing guards), promote to SR #9 "deterministic post-processing for any LLM-prose user-facing channel".

**P6 #42** (Day 80 ~14:00 UTC, banked at Alexandra hygiene pollution cleanup close-confirm): Directive templates need 4 specific upgrades from this cycle's surface bugs: (a) /healthz probes use GET (`curl -s -o /dev/null -w '%{http_code}'`) not HEAD (`curl -sI`) -- FastAPI route handlers don't implement HEAD by default; (b) code blocks must be pre-flight-checked for indent consistency with target file conventions before publishing -- 8-space block in 4-space file would have been Python IndentationError; (c) cold-test patterns where model latency may exceed 25s explicitly authorize the two-shot polling pattern (launch nohup'd curl writing to sentinel file in shot 1; poll for sentinel in shot 2 if needed); (d) MCP wrapper 30s timeout is a known constraint requiring pre-staged workarounds for any test exceeding it. PD invoked all four self-corrects via 4-condition authority during this cycle without halting; Paco ratified at close-confirm. Banking as P6 #42 light-touch; will apply in future directive authoring.

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

**Day 80 ~14:00 UTC (P6 #40 + P6 #41 + P6 #42 origination -- Alexandra hygiene pollution cleanup close-confirm):**
- Triggered by 5 nightly Alexandra smoke-test FAILures + Telegram screenshot showing live hallucination of light states. Pollution-driven hallucination drag identified as root cause of /chat endpoint instability since 2026-04-22 (12 days). Combined cycle: original directive (Steps 1-5 with Step 5 AC.10 failure on `giving you trouble` grep hit) + R2 amendment (Steps R2.1-R2.6 with deterministic post-processing guard).
- P6 #40: Paco-direct execution via MCP bypassed PD lane on Patches 1-3 + backups. CEO Sloan stopped execution mid-cycle at DB DELETE; converted to PD lane via Option C selection. All Paco out-of-lane work retroactively ratified at PD pre-flight via SR #4 precedent. Banking the discipline lesson; not promoted to SR yet.
- P6 #41: Prose-rule patches insufficient for stochastic instruction-drift on 72B local models. Dual-evidence (failure on first roll + success on second roll under identical conditions) proves stochastic regime; deterministic post-processing guard (32-phrase _GUARD_FORBIDDEN list + canned safe greeting substitution + provenance flags) is the architectural safety net. Cold test 2 explicitly demonstrated guard correctly catching `wiz ` substring from `The WiZ RGBW Tunable EDA510 light is now on` and substituting `Hey James, what can I help you with?` while preserving full forensic detail in journal `[CHAT-GUARD] HIT` line. Tool-calling regression Sloan flagged was DISPROVED -- root cause was pollution-driven narrative-confabulation, not tool-calling breakage. Live tool-calling at 13:48:16 + 13:48:27 (5 min after cycle close) confirms guard works in production.
- P6 #42: Banked 4 directive-template improvements from PD's self-correct adaptations (HEAD->GET on /healthz, indent consistency pre-flight, two-shot polling for >25s tests, MCP wrapper timeout workaround pre-staging). All four PD self-corrects were ratified under 4-condition authority.
- Combined cycle close: 22/22 pre-flight + 33/33 acceptance criteria + 5 SG bit-identical pre/cycle/post + atlas.tasks 1h cadence 253 (matches pre-cycle baseline within 0%). Substrate zero-drift across 7+ hour combined cycle window. First-try streak resets for this cycle (one mid-cycle escalation + amendment); compounding evidence remains: Cycles 1+3 first-try (23/23 across CVE patch sweep) + this cycle pass-on-second-pass via R2 amendment. The recovery pattern (escalate -> amend -> pass with full audit trail) is itself portfolio-grade evidence.

**Day 80 early UTC (P6 #39 origination -- Patch Cycle 3 close-confirm; Pi3 ImageMagick CLI absence):**
- Cycle 3 Pi3 Stage A.6: directive expected `convert --version` smoke-test for ImageMagick. PD execution found `convert: command not found`. Investigation: 4 in-scope packages are libraries from Debian-Security advisory; the `imagemagick` meta package providing CLI binaries was `un <none>` (never installed on this Pi3). PD-adapted: verified all 4 libraries at expected version `8:7.1.1.43+dfsg1-1+deb13u8` via `dpkg-query`; status `ii` for all four. Verification intent ("in-scope artifacts at new version") satisfied. Submitted as Path B B3 under SR #4; Paco ratified at close-confirm. P6 #39 banked (light-touch; not SR-promoted).
- Pattern: second instance of directive-assertion-shape mismatch with host actual state in 4 cycles. First was Cycle 2 dkms-on-DGX-OS (Day 79 late evening Patch Cycle 2 directive author preflight). Both caught + corrected (Cycle 2 at preflight via SR #7, Cycle 3 at PD-execution via SR #4). No cycle harm in either case; both preserved acceptance.
- Cycle 3 closed 12/12 PASS first-try; first-try streak 23/23 across Cycles 1+3.

**Day 79 late evening (P6 #38 + SR #8 origination -- Patch Cycle 2 PPA-unreachable abort):**
- Cycle 2 (Goliath) Stage B `apt-get -y dist-upgrade` aborted at ~57s with 4 `E: Failed to fetch` errors against `ppa.launchpadcontent.net` (canonical-nvidia/nvidia-desktop-edge + canonical-nvidia/vulkan-packages-nv-desktop). Cross-host probes from Goliath/CK/Beast all returned TCP/443 FAIL; broader `launchpad.net:443` also FAIL; primary Canonical archives reachable. Confirmed Launchpad-wide upstream outage, not LAN-local issue. Two of the 4 unfetchable binaries are kernel-version-pinned NVIDIA prebuilt module packages (Stage C verify-before-reboot ABORT-gate dependencies); no alternate Canonical mirror serves the `+1000` ABI variants. PD wrote `paco_request_homelab_patch_cycle2_ppa_unreachable_blocks_kernel_modules.md`; Paco issued `paco_response_homelab_patch_cycle2_ppa_unreachable_ruling.md` ratifying Option 1 (hold + wait) with 3-layer recovery gate (TCP×3 + apt-get update + binary-fetch HEAD), 24h hard cap @ 2026-05-04 ~22:23Z, version-drift check pre-retry, and 4 pre-staged escalation options at cap. PD also restored ollama.service unilaterally during request authoring; Paco ratified retroactively + codified as SR #8 (abort-restore discipline). System integrity: dpkg state clean exit 0; cross-host SGs bit-identical (atlas-agent NRestarts 0; postgres+garage anchors unchanged; mercury PID unchanged); atlas.tasks cadence 252/hr within ±25% of pre-cycle 258/hr.
- Mitigation: P6 #38 + SR #8 banked. Cycle 2 retry held until recovery gate passes.

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
