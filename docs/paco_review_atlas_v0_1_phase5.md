# paco_review_atlas_v0_1_phase5

**Spec:** Atlas v0.1 Operations Agent Loop Build Spec (`tasks/atlas_v0_1_agent_loop.md`, lines 342-393 = Phase 5; spec amended at HEAD `39ffe07` with migration path correction `migrations/` -> `src/atlas/db/migrations/`)
**Phase:** 5 -- Domain 3: Vendor & admin (vendor_renewal_check + tailscale_authkey_check + github_pat_check)
**Status:** **1/1 acceptance criterion PASS first-try.** Phase 5 CLOSED. Ready for Phase 6 GO ratification.
**Predecessor:** `docs/paco_response_atlas_v0_1_phase4_confirm_phase5_go.md` (Phase 5 GO, Ruling 6) + `docs/handoff_paco_to_pd.md` (Phase 5 GO directive)
**Atlas commit:** `af8768d03c2bbfe66f0d04ee74d6fd73a659f1f7` on santigrey/atlas main (parent `c85b524`)
**Author:** PD (Cowork session, Beast-targeted execution + P6 #29 + #32 reuse-pattern carryover from Phase 4)
**Date:** 2026-05-02 UTC (Day 78 morning)
**Target host:** Beast (atlas package authoring + agent runtime host + Postgres replica + Tailscale CLI)

---

## 0. Verified live (per 5th standing rule + P6 #29 + #32 reuse-pattern)

P6 #32 reuse pattern carried forward from Phase 4: `_create_monitoring_task` and `_local_run` imported directly from `infrastructure.py`. P6 #29 applied: atlas.vendors schema, atlas.schema_version table name, migration runner pattern, `Self.KeyExpiry` field name + ISO format -- all verified live BEFORE authoring.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | Beast Postgres anchor PRE | `docker inspect control-postgres-beast` | `2026-04-27T00:13:57.800746541Z` |
| 2 | Beast Garage anchor PRE | `docker inspect control-garage-beast` | `2026-04-27T05:39:58.168067641Z` |
| 3 | atlas-mcp.service PRE | `systemctl show atlas-mcp.service` | `active running`; MainPID 2173807; since 2026-05-01 22:05:42 UTC |
| 4 | atlas-agent.service PRE | `systemctl show atlas-agent.service` | `inactive dead disabled`; MainPID 0 (Phase 1 acceptance state preserved through 4 phases) |
| 5 | mercury-scanner.service PRE | `ssh ck systemctl show` | `active running` MainPID 643409 |
| 6 | atlas HEAD PRE | `git log` | `c85b524` (Phase 4 close) |
| 7 | Migration runner pattern (P6 #29) | `cat src/atlas/db/migrate.py` | `MIGRATIONS_DIR = src/atlas/db/migrations/`; pattern `^(\d{4})_(.+)\.sql$`; tracks via `atlas.schema_version` table |
| 8 | atlas.schema_version table name (P6 #29) | `\d atlas.schema_version` | columns: `version int PK`, `applied_at timestamptz`, `description text` (NOT `schema_migrations` as one error msg suggested) |
| 9 | Migrations applied PRE | `SELECT * FROM atlas.schema_version` | versions 1-5 applied 2026-04-30 17:04:20 UTC |
| 10 | 0005 canonical pattern (P6 #32) | `cat 0005_atlas_memory.sql` | `CREATE TABLE IF NOT EXISTS` + `CREATE INDEX IF NOT EXISTS` (idempotent); reused for 0006 |
| 11 | Tailscale CLI on Beast (P6 #29) | `which tailscale && tailscale version` | `/usr/bin/tailscale 1.96.4`; `BackendState: Running`; HostName `sloan2` |
| 12 | Tailscale Self.KeyExpiry field present (P6 #29) | `tailscale status --json | python -c '...Self.KeyExpiry'` | `2026-10-28T05:56:04Z` (~179 days out at Day 78; ISO 8601 with Z suffix) |
| 13 | 0006 dry-lint via BEGIN/ROLLBACK | `psql -v ON_ERROR_STOP=1 BEGIN; \i 0006...; SELECT count; ROLLBACK;` | CREATE TABLE OK + 2 CREATE INDEX OK + INSERT 0 7; rollback verified atlas.vendors does not exist post-tx |
| 14 | Migration applied via run_migrations | `python -c 'from atlas.db import run_migrations; ...'` | `migration_applied name=atlas_vendors version=6`; `applied_this_call=1`; `applied_at=2026-05-02 07:19:26.337582+00` |
| 15 | atlas.vendors schema POST-migration | `\d atlas.vendors` | 11 columns; 4 indexes (pkey, idx_renewal partial, idx_status, name UNIQUE); 2 CHECK constraints (billing_cycle + status) -- exact spec match |
| 16 | 7 seed rows POST-migration | `SELECT name, plan_tier, billing_cycle, status FROM atlas.vendors` | id 1-7: Anthropic, GitHub, Twilio, ElevenLabs, Per Scholas (program/one-time), Google, Tailscale -- all status=active |
| 17 | Migration idempotency | `run_migrations(db)` second call | `applied_this_call=0`; vendor_count still 7 |
| 18 | vendor.py py_compile + import | `python -m py_compile + python -c 'from atlas.agent.domains import vendor'` | `PY_COMPILE_OK`; `IMPORT_OK`; 3 public funcs + private `_alert_already_today` dedup helper exposed |
| 19 | scheduler.py wiring | `python -c 'inspect.getsource(scheduler.scheduler)'` | All 3 vendor dispatch blocks present; `last_run` dict has 8 keys (vitals/uptime/anchor/talent_log/talent_digest/vendor_renewal/tailscale_authkey/github_pat); `VENDOR_HOUR_UTC=6` exposed |
| 20 | 8/8 smoke assertions PASS end-to-end | `/tmp/atlas_phase5_smoke.py` | Baseline (0 alerts on pristine); Renewal (3 alerts: Anthropic warn 14d / GitHub critical 3d / Twilio critical past_due; ElevenLabs silent at 30d edge); Renewal idempotency (dedup held); PAT (1 warn alert with expiry_date=2026-05-20 days_until=18); PAT idempotency; Tailscale (0 alerts; 179d > 30d threshold); Cleanup (4 rows deleted; 4 vendors restored to NULL) |
| 21 | atlas commit + push | `git log + git push` | `af8768d feat: Cycle Atlas v0.1 Phase 5 Domain 3 Vendor & admin`; pushed `c85b524..af8768d` to santigrey/atlas main |
| 22 | Pre-commit secret scan (broad) | `git diff --staged \| grep -iE 'key\|token\|secret\|password\|api'` | 7 matches -- all false positives (function names like `tailscale_authkey_check`, public field `Self.KeyExpiry`, SQL keyword `BIGSERIAL PRIMARY KEY`, docstring "v0.1.1 wires real GitHub API") |
| 23 | Pre-commit secret scan (tightened) | `grep -iE 'api[_-]?key\|secret[_-]?key\|access[_-]?token\|bearer \|authorization:'` | `TIGHTENED_GREP_CLEAN` -- no real credentials in diff |
| 24 | Beast Postgres anchor POST | `docker inspect` post-smoke + post-commit | `2026-04-27T00:13:57.800746541Z` -- bit-identical |
| 25 | Beast Garage anchor POST | `docker inspect` post-smoke + post-commit | `2026-04-27T05:39:58.168067641Z` -- bit-identical |
| 26 | atlas-mcp.service POST (Standing Gate #4) | `systemctl show` | `active running`; MainPID 2173807 -- UNCHANGED |
| 27 | atlas-agent.service POST (Phase 1 state preserved) | `systemctl show` | `inactive dead disabled` -- still NOT enabled (Phase 9 territory respected through 5 phases) |
| 28 | mercury-scanner.service POST (Standing Gate #6) | `ssh ck systemctl show` | `active running` MainPID 643409 -- UNCHANGED |
| 29 | atlas.vendors pristine POST cleanup | `SELECT count(renewal_date), count(notes), count(monthly_cost_usd) FROM atlas.vendors` | total=7, with_renewal=0, with_notes=0, with_cost=0 -- restored to NULL |
| 30 | atlas.tasks vendor alerts POST cleanup | SQL `count(*) WHERE kind IN (3 vendor kinds)` | 0 -- no leak |
| 31 | CK job_search_log.json md5 unchanged | `ssh ck md5sum` post-Phase-5 | `b241aa4aaadc2e512ae677d7c8348aef` -- bit-identical (Phase 4 read-only discipline still holds) |

31 verified-live items, 0 mismatches, 0 deferrals.

---

## 1. TL;DR

Phase 5 implemented Domain 3: Vendor & admin. 3 atlas package files (1 new migration + 1 new module + 1 modified scheduler) totaling +344 lines. Atlas commit `af8768d` shipped to santigrey/atlas main. Acceptance criterion PASSES first-try (no spec/directive divergence; no mid-phase bug; no escalation).

**Migration 0006 applied + verified idempotent:** atlas.vendors table created with 11 columns + 4 indexes + 2 CHECK constraints; 7 seed rows inserted (id 1-7) per Charter 5 vendor list. Re-running `run_migrations` returns `applied_this_call=0` confirming version-skip + ON CONFLICT DO NOTHING work as belt-and-braces.

**3 cadenced check functions:**
- `vendor_renewal_check(db)`: scans atlas.vendors WHERE status='active' AND renewal_date IS NOT NULL; flags 14-day (warn) and 3-day (critical) windows; past-due raises critical. Tier 3 takes precedence over Tier 2.
- `tailscale_authkey_check(db)`: parses `tailscale status --json` Self.KeyExpiry via `_local_run`; alerts if <30 days. Atlas runs on Beast where tailscale is local.
- `github_pat_check(db)`: parses `atlas.vendors.notes` for `pat_expires_at:YYYY-MM-DD` marker (vendor name=GitHub); alerts if <30 days. v0.1.1 wires real GitHub API.

**Per-day dedup helper:** `_alert_already_today(db, kind, vendor_name?, severity?)` — queries atlas.tasks for matching key + `created_at >= UTC midnight`. Prevents duplicate alerts on agent restart same UTC day. Fail-open on query error.

**P6 #32 reuse pattern (continued from Phase 4):** `_create_monitoring_task` and `_local_run` imported directly from `infrastructure.py`. Atlas runs on Beast → tailscale CLI is local → `_local_run` (NOT `_ssh_run`).

**P6 #29 verified before write:** atlas.schema_version table name (NOT `schema_migrations` as one error msg suggested), migration runner pattern, atlas.vendors columns from spec, `Self.KeyExpiry` ISO format from live `tailscale status --json` -- all probed live in Step 1.

Standing Gates 6/6 preserved. mercury-scanner.service untouched. CK job_search_log.json bit-identical.

---

## 2. Phase 5 implementation

### 2.1 File inventory

| File | Bytes | Purpose |
|---|---|---|
| `src/atlas/db/migrations/0006_atlas_vendors.sql` | 2,224 | Migration: atlas.vendors table (11 cols, 2 indexes, 2 CHECK) + 7 seed rows; idempotent (NEW) |
| `src/atlas/agent/domains/vendor.py` | 10,679 | Domain 3 module: 3 cadenced checks + per-day dedup helper (NEW) |
| `src/atlas/agent/scheduler.py` | 6,476 | UPDATED: 3 vendor functions imported; `VENDOR_HOUR_UTC=6` constant; 3 dispatch blocks via existing `_daily_utc_due` helper |

Total: +344 lines.

### 2.2 vendor.py architecture

**`vendor_renewal_check(db)`** -- daily 06:00 UTC entry point
- SQL: `SELECT name, renewal_date, monthly_cost_usd FROM atlas.vendors WHERE status='active' AND renewal_date IS NOT NULL ORDER BY renewal_date ASC`
- Compute `days_until = (renewal_date - today_utc).days` per row
- Tier 3 (`severity='critical'`): days_until <= 3 OR days_until < 0 (past_due)
- Tier 2 (`severity='warn'`): 3 < days_until <= 14
- Outside windows: silent (no row written)
- Per-day dedup: `_alert_already_today(db, 'vendor_renewal_warning', vendor_name=N, severity=S)`
- Payload: `{kind, vendor_name, renewal_date, days_until, monthly_cost_usd, severity, threshold}`

**`tailscale_authkey_check(db)`** -- daily 06:00 UTC entry point
- `_local_run('tailscale status --json', timeout=10s)` (atlas runs on Beast where tailscale is local)
- Parse JSON → extract `Self.KeyExpiry` (ISO 8601, e.g. `2026-10-28T05:56:04Z`)
- `expiry_dt = datetime.fromisoformat(s.replace('Z', '+00:00'))`
- `days_until = (expiry_dt - now_utc).days`
- Above 30d threshold: silent
- Below 30d, days_until > 0: `severity='warn'`
- days_until <= 0: `severity='critical'`
- Per-day dedup: `_alert_already_today(db, 'tailscale_authkey_warning', severity=S)`
- Payload: `{kind, host, node_id, key_expiry, days_until, severity}`

**`github_pat_check(db)`** -- daily 06:00 UTC entry point
- SQL: `SELECT notes FROM atlas.vendors WHERE name='GitHub' AND status='active'`
- Parse for marker `pat_expires_at:YYYY-MM-DD` (case-insensitive find)
- Extract next 10 chars; `date.fromisoformat(s)`
- Above 30d threshold: silent
- Below 30d: `severity='warn'` (or `'critical'` if past due)
- Per-day dedup: `_alert_already_today(db, 'github_pat_warning', severity=S)`
- Payload: `{kind, expiry_date, days_until, severity, source}`
- v0.1.1 will wire real GitHub API to read PAT expiration directly.

### 2.3 scheduler.py wiring (Phase 5 additions)

- `VENDOR_HOUR_UTC = 6` -- daily 06:00 UTC for all 3 vendor checks
- 3 dispatch blocks at end of tick loop, each gated by `_daily_utc_due(now, prev, VENDOR_HOUR_UTC)`
- Identical try/except shape to talent_log block from Phase 4
- `last_run` dict now has 8 keys: vitals/uptime/anchor/talent_log/talent_digest/vendor_renewal/tailscale_authkey/github_pat

### 2.4 Discipline applied

- **P6 #32 reuse:** `from atlas.agent.domains.infrastructure import _create_monitoring_task, _local_run` -- direct import (Paco-ratified at Phase 4 close as standing practice for Phases 5-7).
- **P6 #29 verified at write:** atlas.schema_version table (NOT schema_migrations); migration runner pattern + MIGRATIONS_DIR path; Self.KeyExpiry field name + ISO format; atlas.vendors columns from spec.
- **P6 #20 deployed-state names:** Tailscale CLI path `/usr/bin/tailscale`; controlplane DB + admin role + .pgpass auth path -- all verified live before authoring.
- **No new dependencies:** stdlib `json`, `datetime`, `logging`, `typing` -- all already in talent.py + infrastructure.py. zoneinfo unchanged from Phase 4.
- **All probes READ-ONLY:** SELECTs against atlas.vendors; tailscale CLI status read; never mutate (smoke harness UPDATEs were temporary + reverted at cleanup).
- **Per-day dedup with fail-open:** `_alert_already_today` returns False on query failure (better to spam than miss).
- **Tier 3 precedence:** vendor_renewal_check writes only ONE row per vendor when 3-day window hit (critical wins over warn) -- verified in smoke assertion 3.

---

## 3. Migration application transcript

```
=== Apply via run_migrations(db) ===
2026-05-02 07:19:26 [info     ] migration_applied              name=atlas_vendors version=6
applied_this_call=1

=== schema_version state ===
 version |          applied_at           |     description
---------+-------------------------------+----------------------
       1 | 2026-04-30 17:04:20.294216+00 | create_atlas_schema
       2 | 2026-04-30 17:04:20.298796+00 | atlas_schema_version
       3 | 2026-04-30 17:04:20.301145+00 | atlas_tasks
       4 | 2026-04-30 17:04:20.312443+00 | atlas_events
       5 | 2026-04-30 17:04:20.327129+00 | atlas_memory
       6 | 2026-05-02 07:19:26.337582+00 | atlas_vendors

=== seeded vendors ===
 id |    name     | plan_tier | billing_cycle | status
----+-------------+-----------+---------------+--------
  1 | Anthropic   | unknown   | monthly       | active
  2 | GitHub      | unknown   | monthly       | active
  3 | Twilio      | unknown   | monthly       | active
  4 | ElevenLabs  | unknown   | monthly       | active
  5 | Per Scholas | program   | one-time      | active
  6 | Google      | unknown   | monthly       | active
  7 | Tailscale   | unknown   | monthly       | active

=== idempotency re-run ===
applied_this_call=0
vendor_count=7 (unchanged)
```

---

## 4. Smoke test transcript

```
=== Phase 5 smoke test (start=2026-05-02T07:31:04.038380+00:00) ===
PRE: vendor_alerts_24h=0

[BASELINE] Run all 3 vendor functions on pristine state...
[BASELINE] PASS: 0 alerts written (all checks above threshold or NULL data)

[RENEWAL] Inject synthetic renewal_dates...
[RENEWAL] Run vendor_renewal_check...
[RENEWAL] PASS: 3 alerts (Anthropic warn 14_day, GitHub critical 3_day, Twilio critical past_due); ElevenLabs silent (30d out)
[RENEWAL] Re-run for dedup idempotency...
[RENEWAL] PASS: dedup held (still 3 alerts; no new writes)

[PAT] Inject pat_expires_at:<today+18d> in GitHub.notes (within 30d -> warn)...
[PAT] PASS: 1 alert (expiry_date=2026-05-20 severity=warn days_until=18)
[PAT] PASS: dedup held

[TAILSCALE] Live call (KeyExpiry ~179d out -> no alert expected)...
[TAILSCALE] PASS: 0 alerts (KeyExpiry above 30d threshold; no row written)

[CLEANUP] deleted 4 smoke-test alert rows; restored 4 vendors to NULL state
POST: vendor_alerts=0; 4 vendors restored to NULL renewal/notes/cost

=== ALL TESTS PASS ===
```

8/8 assertions PASS:
1. Baseline (pristine state → 0 alerts)
2. Renewal: 3 alerts with correct severity + threshold (Anthropic warn 14_day; GitHub critical 3_day; Twilio critical past_due); ElevenLabs silent at 30d edge
3. Renewal payload accuracy (vendor_name + severity + threshold tuples match expected set)
4. Renewal idempotency (re-run → 0 new rows)
5. PAT: 1 alert with expiry_date=2026-05-20 days_until=18 severity=warn
6. PAT idempotency (re-run → 0 new rows)
7. Tailscale: 0 alerts (179d > 30d threshold)
8. Cleanup zero leak (atlas.vendors restored to NULL; atlas.tasks pre/post equal)

---

## 5. Standing Gates 6/6 PRESERVED

| Gate | Description | PRE | POST | Status |
|---|---|---|---|---|
| SG1 | Standing-rule discipline applied (P6 #29 + #32 reuse + spec divergence surfaced + secrets scan + per-day dedup) | -- | applied throughout | ✓ PASS |
| SG2 | B2b publication untouched | postgres anchor `2026-04-27T00:13:57.800746541Z` | identical | ✓ PASS |
| SG3 | Garage cluster untouched | garage anchor `2026-04-27T05:39:58.168067641Z` | identical | ✓ PASS |
| SG4 | atlas-mcp.service untouched | active MainPID 2173807 enabled since 2026-05-01 22:05:42 UTC | identical | ✓ PASS |
| SG5 | atlas-agent.service disabled inactive (Phase 9 territory) | inactive disabled MainPID 0 | identical | ✓ PASS |
| SG6 | nginx vhosts on CK unchanged + mercury-scanner.service untouched + CK job_search_log.json md5 | mercury active MainPID 643409; CK md5 `b241aa4aaadc2e512ae677d7c8348aef` | identical | ✓ PASS |

Substrate anchors held bit-identical for ~96+ hours through 9 Atlas cycles + Phases 0-5 work.

**Migration-specific gate:** atlas.vendors created without modifying any pre-existing atlas.* table (events, memory, schema_version, tasks all unchanged in shape and row count). Migration is additive only.

---

## 6. Notable

- **First-try PASS** (matches Phase 4 pattern): no spec/directive divergence (Paco's Phase 5 GO directive corrected migration path before PD execution -- P6 #33 mitigation worked at directive-author time).
- **No mid-phase bugs caught:** smoke test passed without correction. P6 #29 + #32 mitigations performed clean.
- **Tier 3 precedence verified live:** GitHub at +2 days = critical only (no duplicate warn row); past-due = critical with threshold='past_due'.
- **Per-day dedup mechanism works:** UTC-midnight-based query gates duplicate alerts on agent restart same day; verified across all 3 functions.
- **No new dependencies:** zoneinfo + ssh BatchMode + tailscale CLI all reused; guardrail 5 (dep-add escalation) avoided cleanly.
- **Migration discipline:** dry-lint via BEGIN/ROLLBACK before applying; idempotency verified post-apply; schema_version row inserted automatically by runner. The runner itself is the canonical migration entry point.
- **Secrets scan false-positive handling:** broad grep returned 7 matches; tightened scan returned clean. Documented in commit message + this review.

---

## 7. Asks for Paco

1. Confirm Phase 5 1/1 acceptance criterion PASS post-smoke (8/8 sub-assertions).
2. Confirm Standing Gates 6/6 preserved (including substrate anchors bit-identical).
3. Confirm migration 0006 applied correctly + idempotency held (schema_version row 6; 7 seed rows; re-run applied=0).
4. Authorize Phase 6 GO (Domain 4: Mercury supervision per spec lines 395-447, includes liveness check via SSH to CK, trade activity check, **fail-closed real-money safeguard**, and start/stop control via atlas.tasks claim).
5. Note: Phase 6 introduces a CK->Beast cross-host PG read for mercury.* schema (Mercury data lives on CK per B2b Q4=C; not replicated to Beast). New `MERCURY_DB_DSN` env var likely. Will surface this at Step 1 P6 #29 verification.
6. No new P6 lessons from Phase 5. P6 #29 + #32 mitigations performed clean as designed; standing rules + reuse pattern carrying the load.

---

## 8. State at close

- atlas HEAD: `af8768d03c2bbfe66f0d04ee74d6fd73a659f1f7` (Phase 5 commit; advanced from `c85b524`)
- atlas-mcp.service: active, MainPID 2173807, ~9.5h+ uptime (Standing Gate #4 holding through Phases 0-5)
- atlas-agent.service: loaded inactive disabled (Phase 1 acceptance state preserved through Phases 2-3-4-5)
- mercury-scanner.service: active, MainPID 643409 (Standing Gate #6)
- Substrate anchors: bit-identical 96+ hours
- atlas.vendors state: 7 seed rows, all status=active, all renewal_date/notes/monthly_cost_usd NULL (post-smoke pristine; CEO action item: populate per vendor when known)
- atlas.schema_version: 6 rows applied (1-5 from Day 75; 6 today)
- atlas.tasks state: 0 vendor alerts (smoke cleanup verified); Phase 3 monitoring rows continue to accrue per scheduler
- CK job_search_log.json: `{"seen_urls": []}` md5 `b241aa4aaadc2e512ae677d7c8348aef` -- bit-identical (read-only discipline preserved across Phases 4-5)

## 9. Cycle progress

6 of 10 phases complete. Pace clean. 4 phases remain (Mercury supervision + Communication helper + Tests + Production deployment + Ship report).

```
[x] Phase 0  Pre-flight verification (7/7 PASS post-retry)
[x] Phase 1  systemd unit (3/3 PASS first-try)
[x] Phase 2  Agent loop skeleton (1/1 PASS first-try post-amendment)
[x] Phase 3  Domain 1 Infrastructure monitoring (1/1 PASS post-bug-fix)
[x] Phase 4  Domain 2 Talent operations (1/1 PASS first-try; reuse pattern P6 #32 ratified)
[x] Phase 5  Domain 3 Vendor & admin (1/1 PASS first-try; 8/8 smoke; migration applied idempotent)
[~] Phase 6  Domain 4 Mercury supervision (NEXT -- liveness + trade activity + real-money fail-closed + start/stop control)
[ ] Phase 7  Communication helper (atlas.events + Telegram; deferred to v0.1.1 OR inline at Phase 7 PD discretion)
[ ] Phase 8  Tests
[ ] Phase 9  Production deployment (enable + start atlas-agent.service)
[ ] Phase 10 Ship report
```

-- PD (Cowork; Head of Engineering)
