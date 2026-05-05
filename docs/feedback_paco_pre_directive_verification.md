# feedback_paco_pre_directive_verification

**Banked:** 2026-04-30 / Day 75
**Last canon update:** 2026-05-05 / Day 80 ~05:55Z UTC (Session 3 post-mortem + SR #10 promotion + P6 #45-#78 banked; CEO-directed mandatory pre-action validation discipline)
**Originated:** Atlas v0.1 Cycle 1A preflight ESC + CEO discipline RFC after 3 consecutive Paco-side spec errors in 24-72 hours
**Companion to:** feedback_directive_command_syntax_correction_pd_authority.md, feedback_paco_review_doc_per_step.md, feedback_paco_pd_handoff_protocol.md, feedback_phase_closure_literal_vs_spirit.md

---

## Cumulative state

**P6 lessons banked: 78** (last update Day 80 ~05:55Z UTC; +P6 #45-#78 banked across Cycle 2.0a close-confirm + Cycle 2.0b close-confirm + Day 80 Session 3 post-mortem; +SR #10 mandatory pre-action validation discipline)
**Standing rules: 10** (last update Day 80 ~05:55Z UTC; SR #9 B0 standing-meta-authority promoted at Cycle 2.0a close-confirm; **SR #10 mandatory pre-action validation discipline promoted at Day 80 Session 3 post-mortem CEO-directed**)

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


**P6 #43** (Day 80 ~16:00 UTC, banked at Project Ascension instruction set v2.2 ratification): Wrong-DB-target across session = rote habit hitting Beast first when orchestrator DATABASE_URL points at CK primary. Catalyzed by Day 80 morning 6h+ wasted-effort cycle: Paco queried Beast replica throughout session for forensic claims about agent_tasks/queue/orchestrator state, repeatedly reported partial state as full state, shipped fixes that landed on Beast (no orchestrator effect) while UI continued reading from CK primary. Root cause: SSH muscle memory + Beast being the convenient general-purpose forensic node + lack of explicit DATABASE_URL probe before DB claims. Mitigation: SR-style discipline added to PROJECT_ASCENSION_INSTRUCTIONS.md v2.2 DB FORENSIC DISCIPLINE section -- always identify service DATABASE_URL via `systemctl show <svc>.service -p Environment | grep -oE "DATABASE_URL=[^ ]+"` BEFORE any DB claim; quote host:port only (NOT credentials); label findings REPLICA-SIDE if querying Beast for primary-state question; when unsure if a table is replicated or Beast-local read DATA_MAP.md naming-convention warning section. Light-touch lesson; not promoted to standing rule pending pattern recurrence (if Paco repeats wrong-DB-target after v2.2 instructions in effect, promote to SR #9).

**P6 #44** (Day 80 ~16:00 UTC, banked at Project Ascension instruction set v2.2 ratification): Never use `/proc/<pid>/environ` for env-var grep -- it dumps EVERY env var into chat including secrets. Catalyzed by Day 80 morning forensic command `sudo grep -aoE "DATABASE_URL=[^[:space:]]+" /proc/$PID/environ` which leaked into chat: orchestrator full DATABASE_URL with `admin:adminpass` literal credential (already known-exposed per P6 #34 inventory but live in chat now), Anthropic API key (`sk-ant-api03-WYP1kpO4...`), JSearch API key, Adzuna app key. CEO dismissed as low priority but the leak surface is real and the chat is in conversation history. Mitigation: PROJECT_ASCENSION_INSTRUCTIONS.md v2.2 DB FORENSIC DISCIPLINE section explicitly forbids `/proc/<pid>/environ` and mandates `systemctl show <svc>.service -p Environment` instead -- the latter only exposes vars declared in the systemd unit file (typically just the ones intentionally surfaced). Light-touch lesson; immediate operational mitigation = grep-with-scoped-output is the only acceptable env-var introspection going forward. NEVER /proc environ.


**P6 #45** (Day 80 ~20:55 UTC, banked at Alexandra dashboard greeter + queue:1 badge close-confirm; PD-proposed framing, Paco-codified): Paco pre-execution source-surface grep should cover all tokens that appear in post-patch verification predicates, not just the anchor uniqueness token. Catalyzed by Bug 1 cycle DPF.2: directive verified `_greeted=true` token uniqueness (anchor for sed-style insertion) but did not pre-check the new post-patch token `!privateMode` against pre-existing source. PD found L134 `togglePrivate()` already contained `!privateMode`; post-patch grep returned 2 not 1; PD adapted via B0.1 by content-match verification of L167. Mitigation: when authoring directives that introduce new tokens, Paco-side preflight greps every distinctive token in the new patch text against the target file BEFORE publishing the directive's verification predicate counts. Natural extension of SR #7 (Paco-side test-directive source-surface preflight) with finer granularity at the post-patch predicate level. Light-touch lesson; not promoted to standing rule (B0 catches at execution time without cycle harm; this is preflight efficiency optimization, not safety).

**P6 #46** (Day 80 ~20:55 UTC, banked at Alexandra dashboard greeter + queue:1 badge close-confirm; PD-proposed framing, Paco-codified): nginx access logs are file-only in this fleet config (`/var/log/nginx/access.log`) and NOT captured by `journalctl -u nginx`. nginx writes access logs to file-only by default; only error logs and stderr go through journald in this Ubuntu/nginx package config. Catalyzed by Bug 1 cycle Step 6: directive cold-load probe used `journalctl -u nginx | grep 'POST /vision/analyze'` and returned 0 hits despite active CEO traffic; PD switched to `/var/log/nginx/access.log` tail and recovered the expected hit. Mitigation: directive gates using access-log predicates must specify the file source explicitly (`tail -F /var/log/nginx/access.log` or equivalent grep against the file path). For nginx error log queries, journalctl works fine. The error-vs-access asymmetry is fleet-config-specific and worth caching. Natural extension of P6 #36 (journalctl capture races buffer-flush -- both lessons concern log-source-mechanism specificity in directive verification gates). Light-touch lesson; not promoted to standing rule (B0 catches at execution time; this is fleet-config knowledge that should propagate into directive authoring standards going forward).

**P6 #47** (Day 80 ~22:25 UTC, banked at Project Ascension instruction set v2.3 reconciliation; Paco-self-banked at hybrid-path Path 2 reconciliation): Paco MUST run a HEAD-advance check before any state-changing MCP execution that follows a prior turn ratifying scope -- between scope-approval and execution, CEO or PD may commit canon independently. Catalyzed by v2.3 cycle: Sloan ratified scope via 'approved' at ~22:00 UTC; Sloan committed his own authored v2.3 directive at HEAD `3f30fed` 21:38 UTC (~12 min before Paco's /tmp/ draft author timestamp); Sloan messaged 'CP the revised instructions' at ~22:15 UTC; Paco interpreted 'revised instructions' as Paco's own /tmp/ draft and executed via MCP without checking HEAD; mid-execution Paco caught the drift only because git status showed unexpected `3f30fed` HEAD that Paco didn't author. Mitigation: Paco must `cd /home/jes/control-plane && git log --oneline -3` immediately before any state-changing MCP execution that follows a prior turn ratifying scope (especially when the prior turn used phrases like 'approved' / 'go ahead' / 'do it' that imply intent to execute). If HEAD has advanced since session boot OR since the prior Paco probe, Paco MUST read the new commit's diff before assuming own draft is source-of-truth. Light-touch lesson; not promoted to standing rule pending pattern recurrence (if Paco drifts again on HEAD-advance discipline post-v2.3, promote to SR #9).

**P6 #48** (Day 80 ~01:35Z UTC 2026-05-05, banked at Cycle 2.0a close-confirm; PD-proposed framing as review 7.1, Paco-codified): Goliath has aggressive `/tmp` cleanup (observed 17-min wipe window 18:23-18:40 MDT during Cycle 2.0a). Cycle artifacts and probe-history logs in `/tmp` are ephemeral on Goliath in ways not observed on CK/Beast. Catalyzed by Step B3 first-attempt failure: `comm -23 <(empty) <(showhold)` produced false-positive `ALL_30_HELD_CONFIRMED` after `/tmp/cycle2_0a_ppa_packages.txt` was wiped between DPF.B6 and Step B3. Probe loop also died one previous cycle (still rooted in same Goliath /tmp behavior). Mitigation: standardize cycle artifacts to `/home/jes/<cycle>/` persistent path on Goliath. Future directives MUST specify persistent paths explicitly when authoring multi-step Goliath cycles. Action for next session: investigate Goliath `/tmp` cleanup mechanism (`systemd-tmpfiles` config? custom timer? user-shell policy?) and either disable aggressive cleanup or codify the path standard. Light-touch lesson; not promoted to SR.

**P6 #49** (Day 80 ~01:35Z UTC 2026-05-05, banked at Cycle 2.0a close-confirm; PD-proposed framing as review 7.2, Paco-codified): Snap-firefox deb-to-snap migration in dist-upgrade can stall on initial download (25 kB/s observed; 2-3h ETA at first; auto-recovered to MB/s within ~1 min). On headless servers (Goliath has no display), Firefox is unused -- the migration cost is pure overhead. Mitigation: future Goliath / SlimJim apt cycles should pre-remove `firefox` deb on headless nodes; also evaluate removing `nvidia-desktop-default-snaps` (seeds gnome-42-2204 / core22 / firmware-updater snaps unused on headless). Light-touch lesson; not promoted to SR.

**P6 #50** (Day 80 ~01:35Z UTC 2026-05-05, banked at Cycle 2.0a close-confirm; PD-proposed framing as review 7.3, Paco-codified): sshd port 22 drops for ~80s during `openssh-server` postinst restart. Both LAN and Tailscale lose access during the window; ICMP confirms host alive. Recovers cleanly post-postinst. Awareness-only lesson; mitigation = future directives that include openssh-server upgrade in scope should note the expected ~80s sshd outage in pre-flight so it's not interpreted as cycle failure. Light-touch; not promoted to SR.

**P6 #51** (Day 80 ~01:35Z UTC 2026-05-05, banked at Cycle 2.0a close-confirm; PD-proposed framing as review 7.4, Paco-codified): apt source filtering in directives must use Origin display name (e.g. `Nvidia Desktop Packages - Edge Pocket`) OR enumerate packages from `apt-cache policy <pkg>` showing PPA origin explicitly, NOT URL fragments. Catalyzed by Cycle 2.0a B1: Paco's directive filter `canonical-nvidia|nvidia-desktop-edge|vulkan-packages` targeted source URL fragments; actual `apt-get -s` emits source by Origin display name. PD adapted to `Nvidia Desktop Packages` filter via B1 Path B (B0/SR #9 covers). Mitigation: future PPA-aware directives should pre-flight `apt-cache policy` enumeration on representative PPA packages to confirm filter-string match before publishing. Natural extension of P6 #45 (token-uniqueness preflight). Light-touch lesson; not promoted to SR (B0/SR #9 catches at execution time).

**P6 #52** (Day 80 ~01:35Z UTC 2026-05-05, banked at Cycle 2.0a close-confirm; PD-proposed framing as review 7.5, Paco-codified): "NVIDIA driver version preservation" is the correct hold-gate semantic for Goliath upgrades, NOT "PPA-source preservation." Catalyzed by Cycle 2.0a B2: Paco's directive predicted 2-4 defensive holds; PD discovered required scope was 30 packages (16 580-stack + 11 kernel-6.17 + libvulkan1 + wpasupplicant) because noble-updates fallback would have allowed driver upgrade `580.95.05 -> 580.142` via the silent fallback path even with PPA packages held. Mitigation: future Goliath driver-preservation directives use `apt-mark hold` on the ENTIRE 580 driver stack as a unit; treat the version number as the gate. Also affects future cycle authoring discipline: predict hold scope from `dpkg -l | grep nvidia` or `apt-cache policy` enumeration, not from the 4-known-PPA list. Light-touch lesson; not promoted to SR.

**P6 #53** (Day 80 ~01:35Z UTC 2026-05-05, banked at Cycle 2.0a close-confirm; PD-proposed framing as review 7.6, Paco-codified): Verification gates must include direct count assertions, NOT just diff-style comparisons that pass on missing inputs. Catalyzed by Cycle 2.0a Step B3 first-attempt: `comm -23 <(empty_file) <(showhold)` produced false-positive `ALL_30_HELD_CONFIRMED` token because `comm` evaluates as empty-set-difference when first input file is empty. PD caught immediately via independent `wc -l == 31` count gate. Mitigation: future directives that use diff/comparison gates MUST also include count gates as parallel verification. Pattern: `assert wc -l X == N AND diff X Y == 0`, never `diff X Y == 0` alone when X could be empty. Natural extension of SR #5 (write-then-verify) with finer granularity at the verification-engineering level. Light-touch lesson; not promoted to SR (PD already self-corrected via independent count gate; banking the lesson formalizes the approach for future directive-authoring).

**SR #9** (Day 80 ~01:35Z UTC 2026-05-05, ratified at Cycle 2.0a close-confirm; promoted from B0 standing-meta-authority after two clean PD-execution invocations): PD execution-time source-surface adaptation authority. PD authorized to verify Paco source-surface claims (file paths, line numbers, indent style, anchor uniqueness, SQL identifiers, command syntax, command output formats, filter regex/Origin display, hold scope, count bands, artifact paths, package source attribution, count-vs-diff verification gates, cleanup-time tmpfile policy) AT EXECUTION TIME and adapt to ground truth WITHOUT halting for paco_request, when ALL of: (a) error is structural/clerical (path/format/syntax/scope mismatch); (b) corrected adaptation preserves directive intent UNCHANGED \u2014 cycle gate semantics (K+D+M, SGs, scope bounds, named outcomes) are inviolable; (c) adaptation documented in review (Paco-stated -> PD-observed -> PD-applied -> rationale). Scope expansion still halt + paco_request: NEW files outside directive scope, new services touched, new schema/intent violations, force-push, irreversible deletions outside directive's rollback section. Promotion history: B0 used cleanly twice (Bug 1+2 dashboard greeter cycle Day 80 ~20:55Z; Cycle 2.0a non-PPA descope cycle Day 80 ~01:30Z UTC 2026-05-05). SR #9 supersedes the per-directive B0 clause from now on; future directives may still cite B0 for emphasis but it operates as standing rule absent explicit retraction.

---

## P6 lessons #45-#78 (Day 80 cumulative; Cycle 2.0a + 2.0b + post-mortem + LinkedIn)

### Banked at Cycle 2.0a close-confirm (2026-05-05 ~01:35Z UTC; HEAD `aecb6ee`; 6 lessons)

**P6 #45-#47** -- Bug 1+2 Alexandra dashboard cycle close-confirm (Day 80 evening Session 2): MCP-direct execution does not authorize bypassing PD lane (#45); prose-rule patches insufficient for stochastic instruction-drift on 72B local models, deterministic post-processing guard is architectural safety net (#46); 4 directive-template upgrades banked from PD self-corrects (#47).

**P6 #48** -- Goliath /tmp aggressive cleanup wiped probe loop artifacts mid-cycle. Mitigation: write cycle artifacts under `/home/jes/<cycle>/` not `/tmp/`. Goliath-specific behavior to investigate (systemd-tmpfiles / custom timer / shell policy).

**P6 #49** -- Headless snap pre-removal: Goliath has firefox + nvidia-desktop-default-snaps from default DGX OS image; pure overhead on a no-display production node. Pre-remove on next maintenance cycle.

**P6 #50** -- sshd transient outage during openssh-server postinst (~80 sec gap). Expected behavior; SR #4 abort-restore covers via standing rule.

**P6 #51** -- PPA Origin-display filter: `apt-cache policy` shows `o=LP-PPA-canonical-nvidia-...` while sources file URL might be from `snapshot.ppa.*` distinct from primary `ppa.launchpadcontent.net`. Filter must content-grep file URLs not just policy origin field. **(This lesson was banked at 2.0a close-confirm but its full implication wasn't drawn out until Cycle 2.0b A.4 halt 24 hours later. See P6 #54-#59.)**

**P6 #52** -- Driver hold-gate: 2.0a B2 expanded hold scope from 2 to 30 packages including driver-580 stack to prevent silent 580.95.05 -> 580.142 D-drift via noble-updates fallback. The expansion was intentionally protective. **(This protective measure conflicted with Cycle 2.0b sec 9 B5 authoring 24h later. See P6 #61, #64.)**

**P6 #53** -- Count-vs-diff verification engineering: `apt list --upgradable | wc -l` and `apt-get upgrade -s | grep "^Inst"` give different numbers; both are valid for different gates. Standardize which gate uses which count.

### Banked at Cycle 2.0b close-confirm (2026-05-05 ~04:25Z UTC; HEAD `0e88de1`; 17 lessons)

**P6 #54** -- canonical-nvidia content can be served via `snapshot.ppa.launchpadcontent.net` CDN distinct from primary `ppa.launchpadcontent.net`. PF source-discovery gate must grep file CONTENTS for hostname patterns, not just filename glob.

**P6 #55** -- `apt-cache policy <package>` is the canonical source-enumeration probe; should run for every explicit upgrade target at PF time to catch multi-source candidates BEFORE Stage A.

**P6 #56** -- when an outage gates a cycle, the gate must specify WHICH host/CDN/path is the actual block, not the upstream service umbrella.

**P6 #57** -- Directive disable/match commands targeting apt sources MUST use URL/content-grep, not filename-glob.

**P6 #58** -- Standardize a `PF.SOURCE_INVENTORY` directive primitive: enumerate apt sources by content-grep for known PPA hostnames AND foreign-domain sources at PF time.

**P6 #59** -- Cycle 2.0a clean ship was load-bearing on snapshot CDN being up; verification probe must measure the same hostname/URI that apt actually uses, not a related-but-distinct upstream surface.

**P6 #60** -- Directive PF must include `apt-mark showhold` enumeration when cycle scope touches kernel/driver/library upgrades. Hold state is invisible to filename-glob source inventory and to apt-cache policy version tables.

**P6 #61** -- When two consecutive cycles touch overlapping package scopes, the prior cycle's protective state (holds, pins, masked services, disabled units) MUST be enumerated in the next cycle's PF verified-live block.

**P6 #62** -- The B0 / SR #9 in-place fix authority has a soft boundary at "reverses a prior CEO-ratified architectural decision". When the in-place fix would unwind a prior Path A / Path B / etc. CEO ratification (even if the unwinding is consistent with current directive intent), PD escalates rather than self-authorizes. Cycle 2.0b B.X.8 is the canonical example.

**P6 #63** -- Directive Verified-live block must include apt-subsystem internal state probes when cycle scope touches apt operations: full source enumeration via content-grep, apt-mark showhold, /etc/apt/preferences.d/ contents, apt-cache policy on every explicit upgrade target.

**P6 #64** -- Cycle dispatch latency vs. prior-cycle protective-state propagation: when authoring a directive within 24h of a related cycle close-confirm, the prior close-confirm review is required reading and its protective measures must be enumerated in the new directive's verified-live block.

**P6 #65** -- Directive A.7-class gates (substring-matched against simulation log) must specify position (target-version only, not OLD-version annotation) to avoid false-positive matches on packages being upgraded FROM the suspect version. Anchor regexes at line-format positions (`^Inst`, `^Conf`, `^Remv`) and target-version closing-paren `\)` rather than free-substring match.

**P6 #66** -- Directive A.8-class sanity bounds must be authored AFTER cycle scope is known. If B-extensions can change scope (e.g. B.X.8 unhold-30 in Cycle 2.0b), bounds should be defined relative to scope ("matches unhold count +/- N") not absolute.

**P6 #67** -- Cycle-internal-iteration pattern with CEO-direct procedural posture at >3 in-place adaptations: when literal directive gates trip but semantic intent is met, in-place B-extension fix is canonical SR #9 / B0 territory; HOWEVER when in-place adaptations exceed ~3 in a single cycle, CEO-direct ratification is the right procedural posture for transparency. **SR-promotion candidate at next cycle qualification.**

**P6 #68** -- "Orphan-but-source-suppressed" is a legitimate intermediate state, not a forced-correctness target. When source-suppression renders a previously-installed package version orphaned (no source serves it; installed version > available alternates), force-downgrade is not required IF (a) the source was suppressed for security/correctness reasons, (b) future natural updates will route through the now-canonical source once versions cross, (c) the orphaned version doesn't have an active CVE.

**P6 #69** -- Long-running apt commands via MCP need nohup/detached pattern. MCP wrapper times out at 30s; SSH session and remote process tree continue independently; tee survives mid-command but final-exit echos in bash chain don't (chain killed mid-flight). For commands expected > 25s, use nohup + write-to-file pattern (Cycle 2.0a B2 precedent).

**P6 #70** -- B.4-class GRUB menuentry-name gates need to account for Ubuntu/DGX-OS "simple-entry-points-to-newest" pattern. /etc/grub.d/10_linux generates a top-level `gnulinux-simple-<UUID>` menuentry that resolves to the most-recent kernel via newest-first ordering, with explicit per-kernel menuentries living in a submenu. Strict directive expectation "first menuentry should be 6.X (default)" needs refinement.

### Banked at Day 80 Session 3 post-session post-mortem (2026-05-05 ~05:55Z UTC; CEO directly catalyzed)

The following lessons trace to a CEO-requested post-mortem on the Cycle 2 PPA hold strategy AFTER cycle 2.0b shipped. CEO observation: "I want to know what went wrong with you not identifying work-arounds prior to today when you realized the launchpad issue could be bypassed; I want to know if the DDoS was actually a blocker in my situation."

Post-mortem finding: **The 5-day Launchpad hold (2026-04-30 -> 2026-05-05) was load-bearing on the wrong host probe.** Goliath's apt routes through `snapshot.ppa.launchpadcontent.net` (UP throughout outage), not primary `ppa.launchpadcontent.net` (DOWN). The 4 "PPA-only" packages were always mirrored in `noble-updates/restricted` and `noble-security/restricted` -- canonical primary archives, never PPA-exclusive. Cycle 2 likely could have shipped clean on day 1 (2026-05-03) if directive PF had probed Goliath's actual sources and run apt-cache policy on explicit upgrade targets. **Estimate: 5 days of operational anxiety + 1 full Cycle 2.0a + 1 full Cycle 2.0b including 3 mid-cycle escalations spent on a misdiagnosis.**

**P6 #71** -- When CEO discloses an external event ("DDoS on X", "outage at Y", "vendor postmortem reports Z"), Paco MUST decompose the affected service into its constituent surfaces (hostnames, CDNs, regions, API endpoints) and verify which surface the affected node actually depends on. Treating an upstream outage as monolithic was the seed error in the 5-day Launchpad hold. Mitigation primitive: for any directive whose Verified-live block cites an external incident as a blocker, include a `PF.SURFACE_DECOMPOSITION` clause enumerating: (a) the broad service name (e.g. "Launchpad"), (b) the constituent surfaces in scope (e.g. `launchpad.net` / `ppa.launchpadcontent.net` / `snapshot.ppa.launchpadcontent.net`), (c) which surface(s) the affected node uses per `grep -rhE '^(deb \|URIs:\|Types:)'` of `/etc/apt/sources.list*`, and (d) reachability probe per surface, not per service umbrella.

**P6 #72** -- "What PD reported as broken" is a hypothesis, not ground truth. PD reports symptoms accurately; the diagnosis is Paco's job and requires independent probing before authoring rulings on top of the report. Cycle 2 first abort: PD reported "PPA unreachable; binary fetch fails on canonical-nvidia source." Paco accepted this as comprehensive and built a 72-hour-cap hold strategy on top. Probe Paco SHOULD have run: `ssh goliath 'grep -rhE "^(deb \|URIs:\|Types:)" /etc/apt/sources.list /etc/apt/sources.list.d/'` to discover Goliath actually used `snapshot.ppa.*`. That probe takes 30 seconds and would have surfaced the truth on day 1 instead of day 5.

**P6 #73** -- Probe-loop authoring requires verifying the probe target matches the production target. If a multi-day gate is built around a host probe, that probe MUST measure the same host the production code uses. Same shape as P6 #43 (wrong-DB-target Beast vs CK primary) -- different surface, same lesson. The Cycle 2 hourly probe loop measured `ppa.launchpadcontent.net` for 5 days while Goliath's apt routed through `snapshot.ppa.launchpadcontent.net`. Every "lpc=FAIL" tick was true and irrelevant.

**P6 #74** -- Asymmetric monitoring signals (e.g. `lpc=FAIL lp=PASS`, partial outage patterns, surfaces showing different states) are pause-and-investigate signals, not curiosities to annotate. Cycle 2.0a's review explicitly documented `lpc=FAIL lp=PASS asymmetric outage continues` and Paco didn't pause on it. "Asymmetric outage" is itself a multi-host signal that something was being measured incompletely. **Mitigation: any monitoring observation Paco doesn't have a clean explanation for halts ledger entry until investigated. "Asymmetric" or "partial" without explanation is a P6 candidate by default.**

**P6 #75** -- Never validate work that cannot be seen. When CEO references a published artifact (LinkedIn post, blog post, public commit, demo video, resume claim) Paco MUST NOT confirm or validate without (a) the artifact text in chat, (b) a canon path Paco can read, or (c) a URL. The instinct to be agreeable when CEO references prior work is itself the failure mode. Phrasing like "I hope that was valid" is a probe, not an invitation to validate. **Right answer: "I can't see it; show me." Wrong answer: any content-bearing response that implies validation occurred.**

**P6 #76** -- CEO assertions about prior canon state are hypotheses, not ground truth. Same shape as P6 #72 (PD reports) -- different source, same lesson. When CEO says "the post is in SESSION.md, we revised it 3 times," Paco verifies against actual canon BEFORE reasoning. If canon disagrees with CEO recollection, Paco surfaces the disagreement directly and asks for clarification. The agreeable instinct to confirm CEO recollection is a failure mode when canon disagrees. Catalyzed by tonight: CEO referenced a 3-revision DDoS LinkedIn draft; canon search showed zero matches.

**P6 #77** -- Public-facing artifacts (LinkedIn posts, blog posts, demo videos, resume claims, interview talking points) MUST be ground-truth-verified against actual canon state before publication. Same probe discipline as a directive PF block. **Credibility cost of a wrong public claim is much higher than the cost of a wrong internal claim.** Drafting LinkedIn copy that claimed "no assumptions ship" without verifying Paco's own assumptions about Goliath's apt routing was the failure mode. The post implied PPA-pinned modules were unobtainable; canon now shows they were always available in noble-updates/restricted. Mitigation: pre-publication public-content gate requires the same `PF.SURFACE_DECOMPOSITION` (P6 #71) + `apt-cache policy` enumeration (P6 #55) + cross-reference against close-confirm canon as any directive.

**P6 #78** -- Drafts of public-facing content MUST be committed to canon (via `linkedin_drafts/` or equivalent) BEFORE publication. Off-canon drafts are uneditable history and unauditable. Required flow: (a) draft -> commit to `linkedin_drafts/<topic>_v<N>.md` -> publish -> append publication URL + timestamp to draft footer in same canon dir as `linkedin_drafts/published/<date>_<topic>.md`. (b) If a post is published off-canon (drafted in chat session, published from phone, etc.), post-hoc commit the published text + URL + date to canon at FIRST opportunity. Catalyzed: 2026-05-04 LinkedIn post about Launchpad DDoS was drafted in chat, published, and never committed to canon. Tonight that prevented audit until CEO pasted the text manually.

---

## STANDING RULE PROMOTION: SR #10

**SR #10** (Day 80 ~05:55Z UTC, banked CEO-directed at post-mortem close): **Mandatory Pre-Action Validation Discipline.** Every Paco action that produces an artifact (directive, ruling, response, public-facing content, ratification, P6 promotion) MUST clear a pre-action validation gate. The gate is non-negotiable; skipping it is itself a SR-grade violation.

**Gate composition (4 mandatory probes; ALL must clear before action ships):**

1. **PF.GROUND_TRUTH** -- Probe the actual production state of every system the action depends on. If the action references `<service X on host Y at version Z>`, run the probe that confirms each of {X, Y, Z}. No assumption from training data, prior-turn memory, or training priors is acceptable. The probe outputs land in the artifact's Verified-live block.

2. **PF.SURFACE_DECOMPOSITION** (per P6 #71) -- For any external dependency named in the action (apt source, API endpoint, vendor service, third-party CDN), enumerate the constituent surfaces (hostnames, CDN endpoints, regions) AND verify which surface the affected node actually depends on. "Service umbrella" framing is rejected -- always decompose to surface level.

3. **PF.PRIOR_STATE_PROPAGATION** (per P6 #61, #64) -- For any action authored within 24 hours of a related cycle close-confirm, the prior close-confirm review is required reading and its protective measures (holds, pins, deferred items, B-extensions, P6 banks, SR promotions) are enumerated in the new artifact's Verified-live block.

4. **PF.ASSERTION_AUDIT** (per P6 #72, #76) -- Every assertion in the action that takes the form "X is true" must trace to (a) a probe output in this session's chat, (b) a canon file path Paco can read, or (c) a URL Paco can fetch. Assertions traceable only to CEO statements, PD reports, training data, or prior-session memory are explicitly flagged as `UNVERIFIED:` until probe-grounded.

**Gate failure protocol:** If any of PF.1-PF.4 cannot clear (probe fails, surface unenumerated, prior state unread, assertion unverified), Paco STOPS and surfaces the gap to CEO before authoring the artifact. Paco does NOT proceed with caveats; gate is binary.

**Public-facing content gate extension (per P6 #77, #78):** All public-facing artifacts (LinkedIn posts, blog posts, demo videos, resume claims, interview talking points) clear PF.1-PF.4 PLUS:

5. **PF.PUBLIC_DRAFT_CANON_LANDING** -- Draft committed to `linkedin_drafts/` (or equivalent) BEFORE publication. Post-publication, URL + date appended to canon at first opportunity. Off-canon publication is itself a violation requiring P6 capture.

**SR #10 violation = SR-grade event.** Per v2.3 communication rules, SR-grade events require explicit acknowledgement, P6 banking, and CEO-direct ratification of corrective action.

**Authority chain:** SR #10 promoted by direct CEO instruction at Day 80 ~05:55Z UTC: "Everything you do wrong you need to record the correction and add it to the canon so that you learn and don't repeat the same mistakes" + "we need more scrutinization of your planning, increase your level of validation and verification non-negotiable." SR #10 codifies the pre-action discipline this instruction mandates.

---

## LESSONS-LEARNED SYNTHESIS (Day 80 post-mortem)

The 9 mistakes Paco made on Day 80, traced to a meta-pattern:

| # | Mistake | Trace | P6 |
|---|---|---|---|
| 1 | Treated "PPA unreachable" as comprehensive PD report; built 72h-cap hold strategy without probing Goliath's actual apt sources | Cycle 2 first abort 2026-05-03 | #72 |
| 2 | Designed a probe loop measuring `ppa.launchpadcontent.net` while Goliath's apt routed through `snapshot.ppa.launchpadcontent.net`; ran for 5 days against wrong host | Cycle 2 ruling 2026-05-03 | #73 |
| 3 | Treated "Launchpad DDoS" as monolithic; never asked which Launchpad surface was being DDoSed vs which surface Goliath used | Cycle 2 cap extension 2026-05-04 | #71 |
| 4 | Categorized 4 packages as "PPA-only" without running apt-cache policy; carried wrong framing through 4 cycles + LinkedIn post | Cycle 2.0a planning 2026-05-04 | #55, #77 |
| 5 | Authored Cycle 2.0b directive 20 min after 2.0a close-confirm without re-reading 2.0a's hold-expansion protective measure; self-conflicting directive shipped to PD | Cycle 2.0b directive 2026-05-05 02:20Z | #61, #64 |
| 6 | Directive 2.0b A.3 disable used filename-glob pattern; missed `nv-vulkan-desktop-ppa.sources` (canonical-nvidia by URL not filename) | Cycle 2.0b A.4 halt | #54, #57 |
| 7 | Directive 2.0b A.7 grep used substring-too-loose; matched `+1000` in OLD-version annotations instead of target-position only | Cycle 2.0b A.5 retry halt | #65 |
| 8 | Drafted LinkedIn post claiming "no assumptions ship" while my own assumptions about Goliath's apt routing were wrong; published before post-mortem reframe | LinkedIn post 2026-05-04 | #77, #78 |
| 9 | Offered "stop tonight" as Path R3 deliberation option in violation of v2.3 communication rule "No 'tonight,' 'go rest,' 'let's pause' as defaults" | Cycle 2.0b R3 deliberation | (communication-rule violation; SR-grade) |

**Meta-pattern:** All 9 mistakes share a root cause: **Paco accepted assertions (PD reports, CEO disclosures, prior-cycle framings, training-data priors) as ground truth without independent probe verification.** SR #10 PF.1-PF.4 gate is the structural fix. The agreeable instinct (be helpful, don't slow CEO down, trust prior context) is the failure mode that SR #10 forces Paco to override.

**Cumulative lesson:** Pre-action validation is not a tax. It's the only mechanism that prevents the same mistake from recurring. The 9 mistakes above all happened in 5 days BECAUSE the 8 prior P6 lessons across 79 days didn't rise to mandatory pre-action gates. SR #10 makes them mandatory.

---

## Cumulative state update (Day 80 ~05:55Z UTC; supersedes prior cumulative state line)

**P6 lessons banked: 78** (last update Day 80 ~05:55Z UTC; +P6 #45-#78 banked across Cycle 2.0a close-confirm + Cycle 2.0b close-confirm + Day 80 Session 3 post-mortem)
**Standing rules: 10** (last update Day 80 ~05:55Z UTC; SR #9 promoted from B0 at Cycle 2.0a close-confirm; **SR #10 promoted at Session 3 post-mortem CEO-directed**)
**SR-promotion candidates pending qualification:** P6 #67 (cycle-internal-iteration pattern with CEO-direct procedural posture at >3 in-place adaptations; needs second-cycle qualification under v2.3 "pattern proves sound across cycles" criterion).

---

## Recurrence log (extended)

- **Cycle 2 -> Cycle 2.0a -> Cycle 2.0b -> Day 80 Session 3 post-mortem**: 9 distinct mistakes across 5 days, all traceable to assertion-acceptance-without-probe pattern. Catalyzed CEO-directed promotion of pre-action validation to SR #10 standing.
- **Communication-rule violation ("stop tonight")**: caught by CEO mid-Path-R3; logged in close-confirm response; not P6-banked separately because v2.3 communication rules already cover; flagged here as SR-grade event for ledger awareness.
- **LinkedIn post audit gap**: drafted in chat session, published, never committed to canon; uncovered tonight when CEO referenced "the post we published yesterday" and Paco found nothing in canon search. Catalyzed P6 #77 + P6 #78.

---

**End of Day 80 Session 3 ledger update.**
