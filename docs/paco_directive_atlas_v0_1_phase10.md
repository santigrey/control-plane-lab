# paco_directive_atlas_v0_1_phase10

**To:** PD (Cowork) | **From:** Paco | **Date:** 2026-05-03 Day 79 mid-day
**Authority:** CEO ratified Day 79 mid-day (Atlas Phase 10 GO; A1=PD-executable / B1=Phase 9 review structure as skeleton / C3=both 1-hour spec parity + full-elapsed snapshot / D=apply P6 #36 mitigation / E3-result=Domains 2-4 verified working correctly under no-alert conditions, NOT a bug).
**Status:** ACTIVE
**Tracks:** `tasks/atlas_v0_1_agent_loop.md` Phase 10 (lines 525-560 spec inclusive of Acceptance Gates + Standing Gates blocks).
**Predecessor:** Phase 9 close-confirm (control-plane HEAD `aa0853d` -> `8268fa8`; atlas commit `c28310b` UNCHANGED).
**Target host:** CK for ship report file authoring; Beast for data queries; CK for commit + push.
**SR #7 application:** Second proper application. Paco probed Phase 10 spec text, scheduler.py wall-clock logic, journalctl Domain-2-4 fire evidence, 1-hour window data, spec SG inventory, and live spec-SG verification BEFORE writing this directive. SR #7 verified-live block at section 1.

---

## 0. Directive supersedes spec for these 5 corrections

Paco-side preflight (Day 79 mid-day) caught spec divergences:

| # | Spec assumption (line ref) | Live finding | Directive correction |
|---|---|---|---|
| 1 | Spec AG3 line 532: "Each Domain (1-4) writes >=1 atlas.events row in first hour" | Domains 1-4 write to **atlas.tasks** (carryover correction from Phase 9 directive section 0 #1). atlas.events agent-side writes are zero by design. | **AG3 revised:** "Domain 1 writes >=4 of 5 expected kinds to atlas.tasks within first hour (vitals + service_uptime + substrate_check); Domains 2-4 fire on wall-clock cadences and emit atlas.tasks rows ONLY under alert conditions; ship report verifies firing via journalctl when no atlas.tasks rows present." |
| 2 | Spec AG4 line 533: "Mercury liveness check + fail-closed raises Tier 3 on synthetic paper_trade=false (mercury.py test output)" | Phase 8 unit tests already cover fail-closed logic in unit-mock; live invocation deferred to v0.1.1 (carryover from Phase 9 directive section 0 #4) | **AG4 verification path:** point ship report to `tests/agent/test_mercury.py::test_fail_closed_on_db_error_raises_tier3` (already passing as part of 68/68 suite). |
| 3 | (NEW spec interpretation) Domain 2-4 "first hour" coverage | Domains 2-4 are wall-clock cadenced (vendor 06:00 UTC, talent_log 08:00 UTC, mercury_trade 08:00 UTC, talent_digest weekly Sunday local). Day 79 journalctl confirms ALL fired correctly on schedule and ran clean (no-alert path = zero atlas.tasks rows). NOT a bug. | **Document expected behavior in ship report:** "Domain 2-4 coverage at v0.1 = no-alert path. Quiet day = quiet table. Visibility currently via journalctl only." Bank "no-alert health-check pulse" rows as v0.1.1 P5 candidate (one summary row per domain per day for visibility-without-grep). |
| 4 | (NEW finding) Spec Standing Gates inventory (lines 547-558) DIFFERS from canon Standing Gates verified phase-by-phase | Spec SGs: SG1=6 standing rules applied, SG2=B2b pg_publication untouched, SG3=Garage StartedAt anchor, SG4=mcp_server.py on CK untouched, SG5=atlas-mcp loopback :8001 bind, SG6=nginx vhosts unchanged. Canon SGs (close-confirm artifacts): SG1=discipline (SR #6 + P6 #34 + one-step gate), SG2=postgres anchor, SG3=garage anchor, SG4=atlas-mcp.service active MainPID, SG5=atlas-agent.service active+enabled (post-Phase-9), SG6=mercury-scanner.service @ CK active. The two inventories overlap (both have garage anchor) but mostly describe different layers. | **Ship report has TWO Standing Gates sections: §Spec SGs verification (formal v0.1 acceptance) + §Canon SGs evolution (as operationalized through phases 4-9). Document the divergence + bank as v0.1.1 documentation cleanup candidate.** |
| 5 | Spec implies single-window observation | CEO ratified C3: dual-window reporting (strict 1-hour spec-parity 03:57:17->04:57:17 UTC + full-elapsed snapshot at ship-report-author-time) | Ship report has TWO production-data sections: §First-hour spec-parity sample + §Production behavior over time (full elapsed window). |

---

## 1. Verified live (Paco SR #7 preflight, Day 79 mid-day)

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | atlas-agent runtime stable | `systemctl show atlas-agent.service` on beast | MainPID=2872599 NRestarts=0 active enabled ActiveEnterTimestamp=`Sun 2026-05-03 03:57:17 UTC` (12h+ uptime; no restart since enable) |
| 2 | atlas commit POST-Phase-9 | `git log --oneline -1` on beast atlas | `c28310b` UNCHANGED (state-transition phase only) |
| 3 | Phase 10 spec text | `sed -n '525,560p' tasks/atlas_v0_1_agent_loop.md` on CK | Lines 525-528 (deliverable bullets); lines 530-539 (6 Acceptance Gates); lines 547-558 (6 Standing Gates); lines 562+ (Risk register). Spec lines 525-528 deliverable bullets dictate ship-report sections. |
| 4 | First-hour atlas.tasks data (1-hour spec parity 03:57:17->04:57:17) | psql query on beast | service_uptime=72, monitoring_disk=60, monitoring_cpu=60, monitoring_ram=60, substrate_check=1; total=253 |
| 5 | Full elapsed atlas.tasks data | psql query on beast | total=3015 across 12h+; 5/5 Domain 1 kinds present at sustained ~250 rows/hour |
| 6 | atlas.events agent-side | psql query on beast | 0 rows from atlas.* sources since Phase 9 enable (correct per design; agent.* writes to atlas.tasks; atlas.events from agent only on Phase 7 mercury_control paths which haven't been invoked) |
| 7 | Domain 2-4 wall-clock fire evidence | `journalctl -u atlas-agent --since 03:57 --until 09:00` filtered for vendor/talent/mercury_trade | All 5 wall-clock cadences fired on schedule; all ran clean under no-alert paths (vendor_renewal scanned=0, tailscale_authkey days_until=177, github_pat no notes, talent_log seen=0, mercury_trade_activity recent_7d=22 above threshold) |
| 8 | scheduler.py `_daily_utc_due` correctness | code read | Logic: `if now.hour < target: False; if last_fire is None: True; else: last_fire.date() != now.date()`. For atlas-agent enabled at 03:57, first 06:00 tick fires vendor (last_fire=None), first 08:00 tick fires talent+mercury_trade. Correct. |
| 9 | Standing Gate canon (canon SG2/postgres) | `docker inspect control-postgres-beast` on beast | StartedAt `2026-04-27T00:13:57.800746541Z` restart=0 (bit-identical at ~158h+) |
| 10 | Standing Gate canon (canon SG3/garage) | `docker inspect control-garage-beast` on beast | StartedAt `2026-04-27T05:39:58.168067641Z` restart=0 (bit-identical at ~158h+) |
| 11 | Standing Gate canon (canon SG4/atlas-mcp) | `systemctl show atlas-mcp.service` on beast | MainPID=2173807 active (UNCHANGED through Phase 9) |
| 12 | Standing Gate canon (canon SG5/atlas-agent post-flip) | per claim 1 | active enabled MainPID stable (Phase 9 deliverable; SG5 invariant updated) |
| 13 | Standing Gate canon (canon SG6/mercury) | `systemctl show mercury-scanner.service` on CK | MainPID=643409 active (UNCHANGED) |
| 14 | Standing Gate spec (spec SG2/B2b pg_publication) | psql `SELECT * FROM pg_publication` on beast | 0 rows; no logical replication configured at v0.1; spec SG2 trivially holds |
| 15 | Standing Gate spec (spec SG4/mcp_server.py on CK untouched) | `git log --oneline -1 mcp_server.py` on CK | Last touched commit `0d5b99d` (Day 78 reachability Step 5 Mac mini IP); UNTOUCHED through all v0.1 atlas Phases 6-9 (reachability cycle is outside Atlas cycle scope) |
| 16 | Standing Gate spec (spec SG5/atlas-mcp loopback :8001) | `ss -tlnp` on beast | LISTEN 127.0.0.1:8001 by python pid 2173807 (bind preserved) |
| 17 | Standing Gate spec (spec SG6/nginx vhosts) | `ls -la /etc/nginx/sites-enabled/` on CK | alexandra (Apr 5), mcp (Apr 3); UNTOUCHED through all v0.1 atlas cycle (Atlas cycle started Day 60-something, well after these dates) |

17 verified-live rows. **0 mismatches** beyond the 5 spec corrections in section 0. SR #7 second-application complete; Phase 10 ship report can author from this verified canonical state.

---

## 2. Phase 10 implementation

### 2.1 Discipline reminders

- **Phase 10 is documentation-only.** Zero source code changes. Zero test changes. Zero service-state changes. Output is a single ship-report markdown file.
- **Standing gates 6/6 (canon) AND 6/6 (spec) preserved.** Phase 10 verifies and documents; does not mutate.
- **atlas-agent.service stays running throughout.** Do NOT stop, restart, or otherwise interrupt service. Production observation continues during ship-report authoring.
- **No homelab MCP changes; no DB schema changes; no env var changes.**
- **P6 #36 mitigation applied:** when capturing journalctl excerpts, use `journalctl --since '<TS>' --until '<TS>' --no-pager` (no `-n` cap) OR add `sleep 5` between observation-window-end and journalctl invocation.

### 2.2 Ship report structure (Phase 9 review skeleton)

File: `docs/paco_review_atlas_v0_1_agent_loop_ship.md` on CK control-plane repo. Estimate: ~600 lines / ~30KB. Structure (per CEO ratification B1):

```
# paco_review_atlas_v0_1_agent_loop_ship

## 0. Verified live (~17 rows from this directive's section 1 + ship-author-time additions)
## 1. TL;DR (one paragraph: what shipped, what works, what's deferred to v0.1.1)
## 2. Per-phase summary (one paragraph per Phase 0-9; cite close-confirm + commit hashes)
## 3. Acceptance Gates verification (spec lines 530-539, 6 gates)
   - AG1 systemctl up + restart-clean: Phase 9 verified
   - AG2 3 coroutines + crash recovery: Phase 8 test_loop.py + Phase 9 journalctl evidence
   - AG3 Domain coverage in first hour: Domain 1 verified (4 of 5 kinds, substrate_check at hourly cadence); Domains 2-4 verified via journalctl no-alert paths (per directive section 0 correction #3)
   - AG4 Mercury liveness + fail-closed: Phase 8 test_mercury.py covers fail-closed (per directive section 0 correction #2)
   - AG5 Substrate anchors bit-identical: 158h+ verified
   - AG6 secret-grep + dependency audit: at ship-author-time
## 4. Standing Gates verification (TWO sections per directive correction #4)
   - 4a. Canon Standing Gates (as operationalized through close-confirms 4-9): 6/6 verified
   - 4b. Spec Standing Gates (formal v0.1 acceptance): 6/6 verified
   - 4c. Divergence note: spec SG inventory != canon SG inventory; bank documentation cleanup as v0.1.1 candidate
## 5. Production data (TWO sections per directive correction #5 + CEO ratification C3)
   - 5a. First-hour spec-parity sample (03:57:17 -> 04:57:17 UTC; 253 atlas.tasks rows; 5/5 Domain 1 kinds)
   - 5b. Production behavior over time (full elapsed window; 3015 rows in 12h+; sustained ~250 rows/hour cadence; zero crashes; zero restarts)
## 6. Domain 2-4 verification via journalctl (no-alert paths)
   - vendor_renewal_check 06:00 UTC: scanned=0 written=0
   - tailscale_authkey_check 06:00 UTC: days_until=177 (above threshold)
   - github_pat_check 06:00 UTC: no notes (v0.1.1 wires API)
   - talent.job_search_log_check 08:00 UTC: seen=0 new=0 written=0
   - mercury_trade_activity_check 08:00 UTC: recent_7d=22 (above threshold)
   - talent_digest: weekly local cadence; pending Denver Sunday window
## 7. Risk register (spec lines 562-565+; verify or supersede each line)
## 8. Known issues + P5 candidates banked (the v0.1.1 candidate list from Phase 9 close-confirm + new items from this directive)
## 9. Notable
   - 6 consecutive first-try acceptance passes (Phases 4-9)
   - SR #7 banked Phase 8 close; first-applied Phase 9 directive (zero Path B); second-applied Phase 10 directive
   - P6 lessons banked: 36 cumulative; SRs: 7 cumulative
   - Cross-machine PD continuity (Cortez->JesAir mid-Phase-9) worked clean
   - First atlas Twilio integration shipped (mock-default; real-Twilio decoupled CEO action)
   - First production deployment of Atlas (atlas-agent.service active+enabled since 03:57:17 UTC Day 79)
## 10. One-line objective check (per spec Rule 5)
   - "This cycle advances Atlas-as-Operations-agent macro-objective." PASS.
## 11. v0.1.1 candidate list (banked carry-forward)
## 12. Cycle state at ship
   - Atlas v0.1: 11 of 11 phases COMPLETE
   - atlas commit: c28310b (Phase 7 +Phase 8; Phase 9 state-transition; Phase 10 documentation)
   - control-plane HEAD: <ship-report-commit-hash>
## 13. Asks for Paco (close-confirm + Linux patch cycle GO + Phase 10.5 "no-alert pulse" v0.1.1 scope)
```

Use Phase 9 review structure for section ordering + heading style. PD does NOT need to deviate from established review template.

### 2.3 Procedure

**Step 0 -- Pre-flight:**
```bash
cd /home/jes/control-plane && git log --oneline -1 && \
  ssh beast 'cd /home/jes/atlas && git log --oneline -1 && systemctl is-active atlas-agent.service'
```
Expected: control-plane HEAD `8268fa8` (or later); atlas HEAD `c28310b`; atlas-agent active.

**Step 1 -- Capture additional verified-live data** (beyond directive section 1):
```bash
ssh beast 'systemctl show atlas-agent.service -p MainPID -p NRestarts -p ActiveEnterTimestamp' && \
  ssh beast 'docker exec control-postgres-beast psql -U admin -d controlplane -t -c "SELECT count(*) FROM atlas.tasks WHERE created_at > '\''2026-05-03 03:57:17'\'';"' && \
  ssh beast 'cd /home/jes/atlas && source .venv/bin/activate && pytest --tb=no -q 2>&1 | tail -3'
```
Capture: current MainPID + NRestarts + uptime; current production atlas.tasks total; current full-suite pass-rate (expect 68 passed).

**Step 2 -- Capture journalctl Domain 2-4 evidence with P6 #36 mitigation:**
```bash
ssh beast "journalctl -u atlas-agent.service --since '2026-05-03 05:55:00 UTC' --until '2026-05-03 09:00:00 UTC' --no-pager 2>&1 | grep -iE 'vendor|talent|tailscale|github_pat|mercury_trade|digest' | head -40"
```
No `-n` cap; `--no-pager`; explicit window. P6 #36 satisfied.

**Step 3 -- Author ship report file via homelab_file_write:**
Write `/home/jes/control-plane/docs/paco_review_atlas_v0_1_agent_loop_ship.md` per section 2.2 structure. Use `mode=create` to fail-fast if file already exists (it should not). File size estimate ~30KB.

**Step 4 -- Pre-commit secrets-scan (BOTH layers + literal sweep):**
```bash
cd /home/jes/control-plane && \
  grep -niE 'adminpass|api[_-]?key|secret[_-]?key|access[_-]?token|bearer\s+|password.{0,3}=' docs/paco_review_atlas_v0_1_agent_loop_ship.md | head -10 && \
  grep -niE 'AC[0-9a-f]{32}|sk-[a-zA-Z0-9_-]{20,}|ghp_[a-zA-Z0-9]{36,}' docs/paco_review_atlas_v0_1_agent_loop_ship.md | head -5
```
If either flags actual values (vs policy text references) -> redact + re-scan -> proceed only when both clean.

**Step 5 -- Standing Gates POST-check** (canon 6/6; should be unchanged from Phase 9 close):
```bash
ssh beast 'docker inspect control-postgres-beast --format "{{.State.StartedAt}} restart={{.RestartCount}}"' && \
  ssh beast 'docker inspect control-garage-beast --format "{{.State.StartedAt}} restart={{.RestartCount}}"' && \
  ssh beast 'systemctl show -p MainPID -p ActiveState atlas-mcp.service' && \
  ssh beast 'systemctl show -p MainPID -p ActiveState -p UnitFileState atlas-agent.service' && \
  ssh ciscokid 'systemctl show -p MainPID -p ActiveState mercury-scanner.service'
```
All canon SGs match Phase 9 close-confirm values.

**Step 6 -- Spec Standing Gates POST-check** (spec 6/6):
```bash
ssh beast 'docker exec control-postgres-beast psql -U admin -d controlplane -c "SELECT count(*) FROM pg_publication;"' && \
  cd /home/jes/control-plane && git log --oneline -1 mcp_server.py && \
  ssh beast 'ss -tlnp 2>/dev/null | grep ":8001"' && \
  ls /etc/nginx/sites-enabled/
```

**Step 7 -- Commit + push:**
```bash
cd /home/jes/control-plane && \
  git add docs/paco_review_atlas_v0_1_agent_loop_ship.md && \
  git commit -m 'feat: Atlas v0.1 SHIP REPORT -- Phase 10 close (11 of 11 phases COMPLETE; 6 consecutive first-try acceptance passes Phases 4-9; SR #7 banked + 2x applied; canon P6=36 SR=7; atlas-agent.service production-stable since Day 79 03:57:17 UTC; no-alert Domain 2-4 verified via journalctl per directive section 0 correction #3; spec SGs vs canon SGs divergence documented for v0.1.1 cleanup)' && \
  git push && git log --oneline -3
```

**Step 8 -- Notification line in `docs/handoff_pd_to_paco.md`:**
> Paco, PD finished Atlas v0.1 Phase 10. Ship report `docs/paco_review_atlas_v0_1_agent_loop_ship.md` written; canon SGs 6/6 + spec SGs 6/6 verified; full-suite still 68/68 pass; atlas-agent.service still production-stable; control-plane HEAD `<hash>`. Atlas v0.1 cycle COMPLETE. Review: same file. Check handoff.

## 3. Acceptance criteria (Phase 10)

1. Ship report file exists at `docs/paco_review_atlas_v0_1_agent_loop_ship.md` with sections 0-13 per directive section 2.2.
2. All 6 spec Acceptance Gates documented PASS or referenced (AG3/AG4 reference Phase 9 directive corrections + Phase 8 unit tests).
3. Both Canon SG block (6/6) AND Spec SG block (6/6) verified PASS.
4. Production data sections (first-hour spec-parity 253 rows + full-elapsed snapshot 3015+ rows) populated with live query results.
5. Domain 2-4 journalctl evidence captured for no-alert path verification.
6. Pre-commit secrets-scan BOTH layers + literal sweep CLEAN.
7. Standing gates 6/6 (canon) preserved through Phase 10 (Phase 10 is read-only; gates auto-preserved).
8. atlas-agent.service still active+enabled MainPID UNCHANGED post-Phase-10 (no service mutation by ship report authoring).
9. atlas commit UNCHANGED (Phase 10 is documentation-only; no atlas package modification).

## 4. Trigger from CEO to PD (Cowork prompt)

```
You are PD (Cowork) for Santigrey Enterprises. Paco (COO) has dispatched Atlas v0.1 Phase 10 (final cycle phase: ship report).

Repos:
- santigrey/atlas at /home/jes/atlas on Beast (HEAD c28310b). NO source code changes this phase.
- santigrey/control-plane at /home/jes/control-plane on CK (HEAD 8268fa8 or later). Read directive + write ship report here.

Read in order:
1. /home/jes/control-plane/docs/paco_directive_atlas_v0_1_phase10.md (your authority)
2. /home/jes/control-plane/docs/feedback_paco_pre_directive_verification.md (P6 standing rules through #36; SRs through #7)
3. /home/jes/control-plane/docs/paco_review_atlas_v0_1_phase9.md (predecessor; ship-report skeleton structure source)

Directive supersedes spec for the 5 corrections in section 0.

Execute Steps 0 -> 8 per directive section 2.3. One step at a time; verify before next.

Phase 10 is DOCUMENTATION-ONLY. Do NOT modify any file in src/atlas/. Do NOT stop, restart, or interrupt atlas-agent.service. Standing gates auto-preserved.

If any step fails acceptance: STOP, write paco_request_atlas_v0_1_phase10_<topic>.md, do not proceed.

Begin with Step 0 pre-flight.
```

-- Paco
