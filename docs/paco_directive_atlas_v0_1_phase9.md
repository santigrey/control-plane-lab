# paco_directive_atlas_v0_1_phase9

**To:** PD (Cowork) | **From:** Paco | **Date:** 2026-05-02 Day 78 evening
**Authority:** CEO ratified Day 78 evening (Atlas Phase 9 GO; corrections #1-4 + decisions A-include / B-mock-mode-ship / C2-5min-PD-1hr-paco-async / D-PD-executable / E-flag-bank-not-block).
**Status:** ACTIVE
**Tracks:** `tasks/atlas_v0_1_agent_loop.md` Phase 9 (lines 498-525).
**Predecessor:** Phase 8 close-confirm (atlas commit `c28310b`; control-plane HEAD `c3ebcc7`).
**Target host:** Beast (atlas-agent.service host; sudo systemctl + journalctl).
**SR #7 application:** First proper application of Standing Rule #7 (test-directive source-surface preflight, Paco-side). Paco probed atlas-agent.service unit file, agent loop entrypoint, scheduler cadence, atlas.tasks vs atlas.events ground truth, and existing baseline state BEFORE writing this directive's acceptance criteria. SR #7 verified-live block at section 1.

---

## 0. Directive supersedes spec for these 4 corrections

Live verification (Paco-side, 12 probes Day 78 evening, SR #7 first application) caught spec divergences:

| # | Spec assumption (line ref) | Live finding | Directive correction |
|---|---|---|---|
| 1 | AG3 + spec line 504: "Each Domain (1-4) writes ≥1 atlas.events row in first hour" | Domains 1-4 (`infrastructure`, `talent`, `vendor`, `mercury` Phase 6 surface) write to **atlas.tasks** via `_create_monitoring_task`; atlas.events writes from agent.* are ZERO at baseline (Phase 8 verified live). atlas.events from agent only fires on Phase 7 `mercury_control_initiated/executed` paths (rare; not normal observation cadence). | **AG3 revised:** "Each Domain (1-4) writes ≥1 row to **atlas.tasks** within first 5 min via scheduler first-tick + 1 cadence cycle." Specifically: vitals/uptime/substrate/mercury_liveness/mercury_real_money_failclosed (5min cadence) hit during the 5-min observation; talent/vendor/mercury_trade_activity (daily 08:00 UTC wall-clock) verified separately at next-day tick or in Phase 10 ship report. |
| 2 | Spec 9.4: "atlas.events shows ≥10 rows from each domain" | Same as #1; impossible by design | **9.4 revised:** "atlas.tasks shows ≥1 row from each scheduled-cadence kind within first 30 min: monitoring_cpu, monitoring_ram, monitoring_disk, service_uptime, substrate_check, mercury_liveness_warning (only if mercury inactive; usually zero), mercury_real_money_check (kind TBD). Wall-clock-anchored kinds verified in Phase 10 ship report." |
| 3 | Spec 9.3 + acceptance: 1-hour observation INSIDE Phase 9 cycle | 1-hour PD block defeats cycle iteration; ship report is the right artifact for hour-scale data | **Phase 9 directive acceptance: 5-min foreground smoke + systemd start + 5-min stable observation = 10 minutes total.** Paco runs 1-hour ship-report observation post-cycle (asynchronous; non-blocking). Phase 10 ship report includes 1-hour data sample. |
| 4 | AG4: "fail-closed raises Tier 3 on synthetic paper_trade=false" via mercury.py test output | Live invocation requires CK-side mercury DB write; potentially invasive; Phase 8 test_mercury.py covers fail-closed logic in unit-mock | **AG4 verification path:** point to Phase 8 `tests/agent/test_mercury.py::test_fail_closed_on_db_error_raises_tier3` (already passing). Live invocation deferred to v0.1.1 if/when synthetic paper-mode-flip becomes a non-invasive operation. |

---

## 1. Verified live (Paco SR #7 preflight, Day 78 evening)

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | atlas-agent.service unit file content | `systemctl cat atlas-agent.service` on beast | Unit at `/etc/systemd/system/atlas-agent.service`; User=jes Group=jes; Type=simple; ExecStart=`/home/jes/atlas/.venv/bin/python -m atlas.agent`; EnvironmentFile=`/home/jes/atlas/.env`; Requires=atlas-mcp.service; Restart=on-failure RestartSec=10s; WantedBy=multi-user.target |
| 2 | atlas.agent entrypoint module | `cat src/atlas/agent/__main__.py` | imports `atlas.agent.loop.run`; `asyncio.run(run())` |
| 3 | atlas.agent.loop architecture | `cat src/atlas/agent/loop.py` | 3 coroutines under `asyncio.gather`: task_poller + scheduler + event_subscriber; each wrapped in `isolate(name, coro_factory)` for crash-restart |
| 4 | Scheduler cadence | `grep TICK_INTERVAL\|cadence src/atlas/agent/scheduler.py` | TICK_INTERVAL_S=60s; first tick fires immediately on startup; 5min cadences for vitals/uptime/mercury_liveness/mercury_real_money; hourly substrate; daily wall-clock for talent/vendor/mercury_trade_activity |
| 5 | Domain write target ground truth | Phase 8 close-confirm + grep `_create_monitoring_task` across domains/ | All 4 domains write to **atlas.tasks** via `_create_monitoring_task`; atlas.events write paths are mercury_control_initiated/executed (Phase 7 only) |
| 6 | atlas.tasks baseline (pre-Phase-9) | `SELECT kind, count(*) FROM atlas.tasks GROUP BY kind` | 11 kinds visible; 151 rows total; 145 in last 24h. Kinds present: monitoring_cpu/ram/disk (30 each), service_uptime (25), systemd (16), substrate_check (6), container (8), race_test/wo_test/rt_success/rt_fail (test residue from Phase 8). NO talent/vendor/mercury_trade rows (daily 08:00 cadences haven't fired since last test run intra-day). |
| 7 | atlas.events baseline (pre-Phase-9) | `SELECT source, kind, count(*) FROM atlas.events GROUP BY source, kind` | 80 rows total; ALL from non-agent subpackages (atlas.mcp_server tool_call/error, atlas.inference generate, atlas.embeddings embed_single, atlas.mcp_client tools_list/tool_call). **ZERO from atlas.agent.*** — confirms domains write to atlas.tasks not atlas.events |
| 8 | atlas-mcp.service Required dependency | `systemctl is-active atlas-mcp.service` on beast | active; MainPID 2173807; ActiveEnterTimestamp `Fri 2026-05-01 22:05:42 UTC` (~28h uptime) |
| 9 | Beast jes sudo capability | `sudo -n true` on beast | NOPASSWD; PD-executable `sudo systemctl enable\|start\|status\|stop` |
| 10 | atlas/.env state | `ls + wc -l + grep` /home/jes/atlas/.env | 0 bytes; mock-mode default for Twilio per Phase 7 (TWILIO_ENABLED unset; dispatch_telegram logs `telegram_mock` and returns) |
| 11 | Standing gates 6/6 PRE | per Phase 8 close-confirm + this preflight | SG1 discipline; SG2 postgres anchor `2026-04-27T00:13:57.800746541Z`; SG3 garage `2026-04-27T05:39:58.168067641Z`; SG4 atlas-mcp.service active MainPID 2173807; SG5 atlas-agent.service inactive disabled (THIS PHASE FLIPS SG5); SG6 mercury-scanner.service @ CK active MainPID 643409 |
| 12 | atlas HEAD PRE | `git log --oneline -1` on beast atlas | `c28310b` (Phase 8) |

All 12 SR #7 preflight rows confirm intent. **0 mismatches**. SR #7's first application caught the 4 corrections in section 0 BEFORE directive author time, not at PD pre-execution time. This is the rule's payoff.

---

## 2. Phase 9 implementation

### 2.1 Discipline reminders

- **Phase 9 is a state-transition phase, not a code-authoring phase.** Zero source code changes. Zero new files. The only mutation is `systemctl enable` + `systemctl start` flipping `atlas-agent.service` from inactive-disabled to active-enabled.
- **Standing Gate 5 INTENTIONALLY FLIPS this phase.** SG5 was "atlas-agent.service inactive disabled" through Phases 0-8 to preserve the not-yet-deployed invariant. Phase 9's deliberate purpose is to flip SG5 to "active enabled." From Phase 9 onward, SG5 is "atlas-agent.service active enabled MainPID stable."
- **Other 5 standing gates remain bit-identical.** SG2/SG3 substrate anchors UNCHANGED. SG4 atlas-mcp.service unchanged. SG6 mercury-scanner.service @ CK unchanged. Phase 9 does NOT restart any service other than atlas-agent.
- **No homelab MCP changes; no DB schema changes; no env var changes.** Mock-mode Twilio default carries through.
- **Domain-side row growth is expected and welcomed.** atlas.tasks will accumulate rows immediately on first scheduler tick. Do NOT clean these up; they are production observation data from Phase 9 forward.

### 2.2 Procedure

**Step 0 — Pre-flight:**
```bash
cd /home/jes/atlas && git log --oneline -1 && \
  systemctl is-active atlas-mcp.service && \
  systemctl is-enabled atlas-agent.service && \
  systemctl is-active atlas-agent.service && \
  ssh ciscokid 'systemctl is-active mercury-scanner.service' && \
  docker inspect control-postgres-beast --format '{{.State.StartedAt}}' && \
  docker inspect control-garage-beast --format '{{.State.StartedAt}}'
```
Expected: HEAD `c28310b`; atlas-mcp active; atlas-agent disabled + inactive; mercury-scanner active; postgres anchor `2026-04-27T00:13:57.800746541Z`; garage `2026-04-27T05:39:58.168067641Z`.

If any check diverges → STOP + paco_request.

**Step 1 — Manual smoke (foreground, ~120s):**
```bash
cd /home/jes/atlas && timeout 120 .venv/bin/python -m atlas.agent 2>&1 | tee /tmp/atlas_phase9_foreground.log; echo "exit=$?"
```
Duration cap 120s. Captures startup behavior into `/tmp/atlas_phase9_foreground.log` for review section 4. Exit code expected: 124 (timeout-killed; means agent was running when timeout fired).

**Acceptance Step 1:** log shows `Atlas agent loop starting`; 3 isolate-wrapped coroutines start (task_poller, scheduler, event_subscriber); scheduler first tick fires within ~5s and at least one `_create_monitoring_task` log line appears; NO Python tracebacks; exit code 124 (clean timeout, not crash).

If any traceback or non-124 exit → STOP + paco_request with /tmp/atlas_phase9_foreground.log content.

**Step 2 — Pre-deploy atlas.tasks count baseline:**
```bash
docker exec control-postgres-beast psql -U admin -d controlplane -t -c "SELECT count(*) FROM atlas.tasks;" | xargs echo 'baseline_count='
```
Capture this number; it's the reference for Step 4 row growth verification.

**Step 3 — Enable + start atlas-agent.service:**
```bash
sudo systemctl enable atlas-agent.service && \
  sudo systemctl start atlas-agent.service && \
  sleep 5 && \
  systemctl is-active atlas-agent.service && \
  systemctl show atlas-agent.service -p MainPID -p ActiveEnterTimestamp -p UnitFileState
```

**Acceptance Step 3:** is-active returns `active`; MainPID > 0; ActiveEnterTimestamp is current; UnitFileState is `enabled`.

**Step 4 — 5-minute stable observation:**
```bash
sleep 300 && \
  systemctl is-active atlas-agent.service && \
  systemctl show atlas-agent.service -p MainPID -p ActiveState && \
  journalctl -u atlas-agent.service --since '6 min ago' -n 100 --no-pager | tee /tmp/atlas_phase9_first5min.log && \
  docker exec control-postgres-beast psql -U admin -d controlplane -t -c "SELECT count(*) FROM atlas.tasks;" | xargs echo 'post_5min_count='
```

**Acceptance Step 4:**
- is-active returns `active` (no crash + restart loop)
- MainPID UNCHANGED from Step 3 value (no restart occurred)
- journalctl shows `Atlas agent loop starting`, 3 coroutine isolate spawns, multiple scheduler tick log lines, NO `crashed` lines, NO Python tracebacks
- post_5min_count > baseline_count by at least 5 rows (vitals 5min cadence: 1 monitoring_cpu + 1 monitoring_ram + 1 monitoring_disk + 1 service_uptime + 1 substrate_check + first-tick row growth = at minimum +5 rows in 5 min, typically +10-15)

**Step 5 — Per-domain row verification (replaces spec 9.4):**
```bash
docker exec control-postgres-beast psql -U admin -d controlplane -c "SELECT payload->>'kind' AS kind, count(*) AS new_count FROM atlas.tasks WHERE created_at > now() - interval '6 minutes' GROUP BY payload->>'kind' ORDER BY new_count DESC;"
```

**Acceptance Step 5:** at minimum these 5 kinds appear with count >= 1 each:
- `monitoring_cpu`
- `monitoring_ram`
- `monitoring_disk`
- `service_uptime`
- `substrate_check` (only if hourly cadence happened to land in window; otherwise this single kind may be absent—acceptable, document)

Note: `mercury_liveness_warning` only appears if mercury-scanner.service is INACTIVE; since SG6 is active, this kind should be ABSENT (which is correct behavior). Document absence in review.

`monitoring_cpu/ram/disk + service_uptime + substrate_check` = 4 of 4 required Domain 1 (Infrastructure) sub-checks. **Domains 2-4 (talent/vendor/mercury) are wall-clock cadenced; verified at +24h tick or in Phase 10 ship report.**

**Step 6 — Standing gates POST (5 must be unchanged; SG5 INTENTIONALLY FLIPPED):**
```bash
docker inspect control-postgres-beast --format '{{.State.StartedAt}} {{.State.Status}} restart={{.RestartCount}}' && \
  docker inspect control-garage-beast --format '{{.State.StartedAt}} {{.State.Status}} restart={{.RestartCount}}' && \
  systemctl show -p MainPID -p ActiveState atlas-mcp.service && \
  systemctl show -p MainPID -p ActiveState -p UnitFileState atlas-agent.service && \
  ssh ciscokid 'systemctl show -p MainPID -p ActiveState mercury-scanner.service'
```

**Acceptance Step 6:**
- SG2 postgres StartedAt = `2026-04-27T00:13:57.800746541Z` restart=0 (UNCHANGED; bit-identical to PRE)
- SG3 garage StartedAt = `2026-04-27T05:39:58.168067641Z` restart=0 (UNCHANGED)
- SG4 atlas-mcp MainPID = 2173807 (UNCHANGED; no restart)
- **SG5 atlas-agent MainPID > 0; ActiveState=active; UnitFileState=enabled** (FLIPPED INTENTIONALLY)
- SG6 mercury-scanner @ CK MainPID = 643409 (UNCHANGED)

**Step 7 — Domain-row leak check (cleanup verification, parallel to Phase 8 discipline):**
```bash
docker exec control-postgres-beast psql -U admin -d controlplane -c "SELECT count(*) FROM atlas.tasks WHERE payload->>'kind' IN ('test_integration_marker','noop','race_test','wo_test','rt_success','rt_fail');"
```
Expected: low single-digit (Phase 8 residue from before integration-test cleanup; not Phase 9 issue). Document for ship-report cleanup.

**Step 8 — Pre-commit secrets-scan (broad + tightened) on this directive's review file ONLY:**
Phase 9 has zero source code changes; secrets-scan applies only to the `paco_review_atlas_v0_1_phase9.md` written at Step 9. Apply BOTH layers.

**Step 9 — Write `docs/paco_review_atlas_v0_1_phase9.md`** in control-plane following Phase 8 review template. Sections:
- 0: Verified-live (~12 rows from Steps 0, 4, 5, 6, 7)
- 1: TL;DR
- 2: Procedure walk-through with foreground-log + journalctl excerpts
- 3: Acceptance per Step (1-7)
- 4: Standing Gates 6/6 (SG5 flipped intentionally; 5 others bit-identical)
- 5: Notable / 5 consecutive first-try acceptance passes (if applicable)
- 6: Asks for Paco (close-confirm + Phase 10 GO + 1-hour observation handoff)
- 7: P6 lessons banked
- 8: State at close (atlas commit chain; atlas-agent MainPID + ActiveEnterTimestamp; substrate anchors at +X hours)
- 9: Cycle progress (10 of 11 phases done; Phase 10 next)

Commit + push to control-plane.

**Step 10 — Notification line in `docs/handoff_pd_to_paco.md`:**
> Paco, PD finished Atlas v0.1 Phase 9. atlas-agent.service ENABLED + STARTED; MainPID `<pid>`; first-5min stable; <N> atlas.tasks rows added in 5min from Domain 1 sub-checks; SG5 flipped active+enabled (intentional); other 5 SGs bit-identical; atlas commit unchanged (`c28310b`; no source code modification this phase). Review: `docs/paco_review_atlas_v0_1_phase9.md`. Check handoff.

## 3. Acceptance criteria (Phase 9)

1. atlas-agent.service is `active` running for >=5 minutes (not >=1 hour as spec; per directive correction #3).
2. MainPID stable (no restart loops) across 5-min observation.
3. journalctl shows clean startup: 3 coroutine isolates spawned; scheduler first tick within 5s; no Python tracebacks; no `crashed` lines.
4. atlas.tasks accumulates >=4 of 5 Domain 1 kinds within 5-min window: monitoring_cpu, monitoring_ram, monitoring_disk, service_uptime (substrate_check optional in 5-min window per hourly cadence).
5. atlas.events writes from agent.* remain at zero (expected; agent.* domains write to atlas.tasks not atlas.events; mercury_control paths only fire under explicit invocation).
6. SG2/SG3/SG4/SG6 bit-identical to PRE; SG5 INTENTIONALLY FLIPPED to active+enabled.
7. Pre-commit secrets-scan BOTH layers clean on review file.

**1-hour observation NOT a Phase 9 acceptance criterion** — captured asynchronously by Paco for Phase 10 ship report.

## 4. Discipline reminders

- One step at a time per Phase 7-8 cadence; 10 steps total.
- DO NOT touch source code. Phase 9 is service-state-flip only.
- `sudo systemctl daemon-reload` ONLY if unit file is modified (which it is NOT this phase). Do not run.
- If atlas-agent crashes during 5-min observation: capture journalctl output; STOP; paco_request. Do NOT `systemctl restart` to mask it.
- Do NOT clean up atlas.tasks rows generated during Phase 9 — those are production observation data from this point forward. Phase 8 cleanup discipline (test-marker-only) does NOT apply.
- atlas/.env stays empty (mock-mode Twilio); CEO can populate it post-Phase-10 at their discretion (per Phase 7 close-confirm Step 1.5 deferral).
- Paco runs 1-hour ship-report observation post-cycle; PD does not block on it.

## 5. Trigger from CEO to PD (Cowork prompt)

```
You are PD (Cowork) for Santigrey Enterprises. Paco (COO) has dispatched Atlas v0.1 Phase 9.

Repos:
- santigrey/atlas at /home/jes/atlas on Beast (HEAD c28310b). NO source code changes this phase.
- santigrey/control-plane at /home/jes/control-plane on CK. Read directive + write paco_review here.

Read in order:
1. /home/jes/control-plane/docs/paco_directive_atlas_v0_1_phase9.md (your authority)
2. /home/jes/control-plane/docs/feedback_paco_pre_directive_verification.md (P6 standing rules through #35)
3. /home/jes/control-plane/docs/paco_review_atlas_v0_1_phase8.md (predecessor; Path B adaptation pattern)

Directive supersedes spec for the 4 corrections in section 0.

Execute Steps 0 -> 10 per directive section 2.2. One step at a time; verify before next.

Phase 9 is a STATE-TRANSITION phase: zero source code changes; only `systemctl enable + start` flips atlas-agent.service from disabled-inactive to active-enabled. Do NOT modify any file in src/atlas/.

If any step fails acceptance: STOP, write paco_request_atlas_v0_1_phase9_<topic>.md, do not proceed.

Begin with Step 0 pre-flight.
```

-- Paco
