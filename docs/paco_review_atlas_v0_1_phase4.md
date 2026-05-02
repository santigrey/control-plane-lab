# paco_review_atlas_v0_1_phase4

**Spec:** Atlas v0.1 Operations Agent Loop Build Spec (`tasks/atlas_v0_1_agent_loop.md`, lines 314-340 = Phase 4; spec amended at Phase 3 close with substrate-gap preamble + atlas.tasks-as-proxy pattern for Phases 4-7)
**Phase:** 4 -- Domain 2: Talent operations (job_search_log_check + weekly_digest_compile + recruiter_watch stub)
**Status:** **1/1 acceptance criterion PASS first-try.** Phase 4 CLOSED. Ready for Phase 5 GO ratification.
**Predecessor:** `docs/paco_response_atlas_v0_1_phase3_confirm_phase4_go.md` (Phase 4 GO, Ruling 7) + `docs/handoff_paco_to_pd.md` (Phase 4 GO directive)
**Atlas commit:** `c85b52459838799a2658ac01caf3dea61f626b67` on santigrey/atlas main (parent `54e3a26`)
**Author:** PD (Cowork session, Beast-targeted execution + P6 #32 canonical-import + P6 #29 API-symbol verification)
**Date:** 2026-05-02 UTC (Day 78 morning)
**Target host:** Beast (atlas package authoring + agent runtime host)

---

## 0. Verified live (per 5th standing rule + P6 #29 + #32 mitigation)

P6 #32 applied at write time: `_create_monitoring_task` and `_ssh_run` reused via direct import from `infrastructure.py` (Phase 3 commit `54e3a26`); not re-authored from memory. P6 #29 applied: `Database` import path, `atlas.tasks` schema (`created_at` column), and `_ssh_run` signature all verified live BEFORE talent.py was authored.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | Beast Postgres anchor PRE | `docker inspect control-postgres-beast` | `2026-04-27T00:13:57.800746541Z` |
| 2 | Beast Garage anchor PRE | `docker inspect control-garage-beast` | `2026-04-27T05:39:58.168067641Z` |
| 3 | atlas-mcp.service PRE | `systemctl show atlas-mcp.service` | `active running`; MainPID 2173807; ActiveEnterTimestamp `Fri 2026-05-01 22:05:42 UTC` |
| 4 | atlas-agent.service PRE | `systemctl show atlas-agent.service` | `inactive dead disabled`; MainPID 0 (Phase 1 acceptance state preserved) |
| 5 | mercury-scanner.service PRE | `ssh ck systemctl show mercury-scanner.service` | `active running` MainPID 643409 |
| 6 | atlas HEAD PRE | `git log --oneline -1` | `54e3a26` (Phase 3 close) |
| 7 | CK job_search_log.json PRE | `cat + md5sum` on CK | `{"seen_urls": []}` md5 `b241aa4aaadc2e512ae677d7c8348aef` |
| 8 | atlas.tasks schema (P6 #29) | `psql \d atlas.tasks` | columns id/status/created_at/updated_at/owner/payload/result; check constraint pending/running/done/failed; `created_at` timestamptz available for 7-day digest |
| 9 | `Database` import path (P6 #29) | `cat src/atlas/db/__init__.py` | `from atlas.db.pool import Database` re-export; matches Phase 3 usage `from atlas.db import Database` |
| 10 | `_ssh_run` signature (P6 #29) | `grep -n` in infrastructure.py | `async def _ssh_run(host_ip: str, user: str, cmd: str, timeout: float = 10.0) -> tuple[int, str, str]` line 68 |
| 11 | `_create_monitoring_task` signature (P6 #29) | `grep -n` in infrastructure.py | line 149: `async def _create_monitoring_task(db: Database, kind: str, payload: dict[str, Any]) -> Optional[str]` -- defensive merge pattern verified at lines 156-158 |
| 12 | Python 3.11 + zoneinfo for Mondays-07:00-local guard | `.venv/bin/python -c 'from zoneinfo import ZoneInfo; ...'` | py 3.11.15; America/Denver = UTC-6 (MDT in May) |
| 13 | Beast->CK SSH BatchMode key auth | `ssh -o BatchMode=yes jes@192.168.1.10 cat ...` | exit 0; returned `{"seen_urls": []}` (Phase-0-deployed id_ed25519 working) |
| 14 | 2 source files written + py_compile + import OK | `python -m py_compile + python -c 'from atlas.agent.domains import talent'` | `PY_COMPILE_OK`; `IMPORT_OK`; talent exports `job_search_log_check`, `weekly_digest_compile`, `recruiter_watch` |
| 15 | scheduler.py wiring + 9 helper assertions PASS | unit test of `_daily_utc_due` + `_weekly_local_due` boundary cases | daily: before-window NOT due, first-run due, new-UTC-day due, same-day-no-refire; weekly: before-07:00-local NOT due, first-Mon due, Tue NOT due, new-ISO-week due, same-week-no-refire -- 9/9 PASS |
| 16 | 5/5 smoke assertions PASS end-to-end | `/tmp/atlas_phase4_smoke.py` | A: empty CK -> 0 rows leak; B1: 2 SMOKE URLs -> 2 applicant_logged rows written; B2: idempotent re-run -> still 2 (dedup verified); C: digest -> 1 weekly_digest_talent row, payload.count=2 window_days=7; cleanup deleted 3 rows; pre/post atlas.tasks counts match (no leak) |
| 17 | atlas commit + push | `git log + git push` | `c85b524 feat: Cycle Atlas v0.1 Phase 4 Domain 2 Talent operations`; pushed `54e3a26..c85b524` to santigrey/atlas main |
| 18 | Pre-commit secret-grep (P6 #11) | `git diff --staged | grep -iE 'key|token|secret|password|api'` on 233 added lines | `NO_SECRET_HITS` -- clean |
| 19 | Beast Postgres anchor POST | `docker inspect control-postgres-beast` post-smoke | `2026-04-27T00:13:57.800746541Z` -- bit-identical |
| 20 | Beast Garage anchor POST | `docker inspect control-garage-beast` post-smoke | `2026-04-27T05:39:58.168067641Z` -- bit-identical |
| 21 | atlas-mcp.service POST (Standing Gate #4) | `systemctl show` | `active running`; MainPID 2173807 -- UNCHANGED |
| 22 | atlas-agent.service POST (Phase 1 state preserved) | `systemctl show` | `inactive dead disabled` -- still NOT enabled (Phase 9 territory respected) |
| 23 | mercury-scanner.service POST (Standing Gate #6) | `ssh ck systemctl show` | `active running` MainPID 643409 -- UNCHANGED |
| 24 | CK job_search_log.json POST (read-only discipline) | `md5sum` post-smoke | `b241aa4aaadc2e512ae677d7c8348aef` -- bit-identical; never wrote to CK |
| 25 | atlas.tasks state POST cleanup | `psql count(*) FILTER ...` | applicants=0, digests=0, smoke_residue=0 -- no leak |

25 verified-live items, 0 mismatches, 0 deferrals.

---

## 1. TL;DR

Phase 4 implemented Domain 2: Talent operations. 2 atlas package files (1 new module + 1 modified scheduler) totaling +231/-2 lines. Atlas commit `c85b524` shipped to santigrey/atlas main. Acceptance criterion PASSES first-try (no spec/directive divergence; no mid-phase bug; no escalation).

**Substrate-gap pattern from Phase 3 close applied:** Domain 2 writes go to `atlas.tasks` (not `atlas.events`) per amended spec preamble. v0.1.1 will migrate Domain 1-4 writes to `atlas.events` when canonical `create_event` helper lands alongside Mr Robot build.

**P6 #32 mitigation applied:** `_create_monitoring_task` and `_ssh_run` reused via direct import from `infrastructure.py`; not reauthored. This is the canonical-copy pattern P6 #32 prescribes -- imports are even cleaner than copy-adapt because there is exactly one source of truth.

**P6 #29 applied at write time:** atlas.tasks schema (`created_at` column for 7-day digest), `Database` import path, `_ssh_run` signature, and Python 3.11+zoneinfo all verified live BEFORE talent.py was authored. Zero API-from-memory errors at directive-author time.

**Wall-clock-anchored cadence helpers added to scheduler.py:** `_daily_utc_due` (date-keyed) + `_weekly_local_due` (ISO-week-keyed, DST-aware via America/Denver). 9/9 boundary-case unit assertions PASS (before-window, first-run-due, new-period, same-period-no-refire for both helpers).

Standing Gates 6/6 preserved. mercury-scanner.service untouched (Standing Gate #6 explicit). CK job_search_log.json bit-identical post-smoke (read-only discipline).

---

## 2. Phase 4 implementation

### 2.1 File inventory

| File | Bytes | Purpose |
|---|---|---|
| `src/atlas/agent/domains/talent.py` | 6,365 | Domain 2 module: `job_search_log_check`, `weekly_digest_compile`, `recruiter_watch` stub + helpers `_read_job_search_log`, `_existing_logged_urls` (NEW) |
| `src/atlas/agent/scheduler.py` | 4,822 | UPDATED: zoneinfo + Optional imports; 4 talent constants; 2 due-helpers (`_daily_utc_due`, `_weekly_local_due`); 2 dispatch blocks for talent_log + talent_digest |

Total: +231 / -2 lines.

### 2.2 talent.py architecture

**`job_search_log_check(db)`** -- daily 08:00 UTC entry point
- SSH BatchMode to CK 192.168.1.10, `cat /home/jes/control-plane/job_search_log.json` (read-only; never writes to CK)
- Parse JSON; extract `seen_urls` list
- Query existing `payload.kind='applicant_logged'` URLs from atlas.tasks (status-agnostic dedup)
- Insert one new row per untracked URL via `_create_monitoring_task(db, 'applicant_logged', {'url': url, 'source': 'job_search_log'})`
- Empty `seen_urls` is silent no-op (current state of CK file)

**`weekly_digest_compile(db)`** -- Mondays 07:00 America/Denver entry point
- SQL aggregate: `SELECT payload->>'url' FROM atlas.tasks WHERE payload->>'kind'='applicant_logged' AND created_at >= now() - interval '7 days'`
- Insert one summary row via `_create_monitoring_task(db, 'weekly_digest_talent', {'count': N, 'urls': [...], 'window_days': 7})`

**`recruiter_watch()`** -- v0.1 stub; `TODO(v0.1.1)` Gmail OAuth + label scan deferred per spec.

### 2.3 scheduler.py wiring

- `TALENT_LOG_HOUR_UTC = 8` -- daily 08:00 UTC
- `TALENT_DIGEST_WEEKDAY = 0` -- Monday
- `TALENT_DIGEST_HOUR_LOCAL = 7` -- 07:00 local
- `TALENT_DIGEST_TZ = 'America/Denver'` -- Sloan location; DST-aware via stdlib zoneinfo

**`_daily_utc_due(now_utc, last_fire, target_hour) -> bool`** -- True if `now_utc.hour >= target_hour` AND we haven't fired today (date-keyed; handles cross-UTC-midnight cleanly).

**`_weekly_local_due(now_utc, last_fire, weekday, target_hour, tz_name) -> bool`** -- Convert now to target tz; True if `local.weekday() == weekday` AND `local.hour >= target_hour` AND we haven't fired this ISO week (`isocalendar()[:2]` comparison handles year boundary).

Two dispatch blocks added to scheduler tick loop, identical try/except shape as existing vitals/uptime/anchor blocks. Per-domain failure isolated; one domain's exception does not poison others.

### 2.4 Discipline applied

- **P6 #32 canonical-copy:** `_create_monitoring_task` + `_ssh_run` imported directly from `infrastructure.py` rather than re-implemented.
- **P6 #29 API-symbol verification:** atlas.tasks schema (`\d atlas.tasks`), `Database` re-export path (`cat src/atlas/db/__init__.py`), `_ssh_run` signature (`grep`), zoneinfo + DST behavior (`python -c`) all verified live pre-write.
- **P6 #20 deployed-state names:** `192.168.1.10` (CK IP), `/home/jes/control-plane/job_search_log.json` (CK file path) -- both verified live via SSH `cat` BEFORE talent.py authoring.
- **No new dependencies:** zoneinfo is stdlib (Python 3.11.15 verified). asyncio + json + logging + typing -- all stdlib already in use.
- **All probes READ-ONLY:** SSH `cat` on CK; never writes to CK. md5sum verified pre/post.

---

## 3. Smoke test output

```
=== Phase 4 smoke test (start=2026-05-02T06:54:20.876727+00:00) ===
PRE: applicant_logged=0 weekly_digest_talent=0

[A] Real job_search_log_check against actual empty CK file...
[A] PASS: applicant_logged unchanged (0)

[B] Monkey-patch _read_job_search_log with synthetic SMOKE_TEST URLs...
[B1] PASS: 2 applicant_logged rows written (2)
[B2] PASS: idempotent re-run (still 2 rows)

[C] weekly_digest_compile...
[C] PASS: 1 digest row written; payload.count=2 window_days=7

[CLEANUP] deleted 3 smoke-test rows
POST: applicant_logged=0 weekly_digest_talent=0

=== ALL TESTS PASS ===
```

5/5 assertions:
- A: real `job_search_log_check` against actual empty CK file → 0 rows leaked (SSH+JSON path verified end-to-end)
- B1: monkey-patched 2 SMOKE URLs → 2 `applicant_logged` rows inserted via `_create_monitoring_task`
- B2: re-run with same fixture → still 2 rows (`_existing_logged_urls` dedup working)
- C: `weekly_digest_compile` → 1 `weekly_digest_talent` row, `payload.count=2 window_days=7`
- Cleanup: 3 test rows deleted; atlas.tasks restored to pre-state (zero pollution)

**Smoke harness bug debrief (talent.py source unaffected):** First smoke run crashed on a psycopg `%`-in-LIKE-pattern parse error, leaving 2 orphan SMOKE rows in atlas.tasks. The bug was in `/tmp/atlas_phase4_smoke.py` only; talent.py source was never affected. Fixed by parameterizing all LIKE patterns via `%s`. Manually pruned orphans before re-run. Acceptance criterion verified clean post-fix.

---

## 4. Standing Gates 6/6 PRESERVED

| Gate | Description | PRE | POST | Status |
|---|---|---|---|---|
| SG1 | Standing-rule discipline applied (verified-live; one-step-at-a-time; canonical-copy P6 #32; P6 #29 API verification; SR #6 self-state) | -- | applied throughout | ✓ PASS |
| SG2 | B2b publication untouched | postgres anchor `2026-04-27T00:13:57.800746541Z` | identical | ✓ PASS |
| SG3 | Garage cluster untouched | garage anchor `2026-04-27T05:39:58.168067641Z` | identical | ✓ PASS |
| SG4 | atlas-mcp.service untouched | active MainPID 2173807 enabled since 2026-05-01 22:05:42 UTC | identical | ✓ PASS |
| SG5 | atlas-agent.service disabled inactive (Phase 9 territory) | inactive disabled MainPID 0 | identical | ✓ PASS |
| SG6 | nginx vhosts on CK unchanged + mercury-scanner.service untouched | mercury active MainPID 643409 | identical | ✓ PASS |

Substrate anchors held bit-identical for ~96+ hours through 9 Atlas cycles + Phases 0-3 + Phase 4 work.

---

## 5. Notable

- **First-try PASS:** unlike Phases 0 + 3 (each had one mid-phase escalation/correction), Phase 4 ran clean from spec to commit. Discipline credit: P6 #29 + #32 mitigations are working as designed.
- **No spec/directive divergence:** spec amendment from Phase 3 close (`atlas.tasks`-as-proxy preamble for Phases 4-7) was followed verbatim. No paco_request needed.
- **No new dependencies:** zoneinfo + ssh BatchMode reused; no paramiko/asyncssh add. Guardrail 5 (dep-add escalation) avoided cleanly.
- **Smoke harness pollution caught + cleaned:** the psycopg LIKE-placeholder issue surfaced via assertion failure, not a silent data leak. Pre/post counts are now baseline-equal. P6 takeaway (pasted to commit message): when authoring psycopg test SQL, always parameterize LIKE patterns -- never inline `%`.
- **DST-aware tz handling:** `_weekly_local_due` uses stdlib `zoneinfo.ZoneInfo('America/Denver')` so it follows DST automatically (currently MDT = UTC-6 in May; switches to MST = UTC-7 in Nov without any code change).

---

## 6. Asks for Paco

1. Confirm Phase 4 1/1 acceptance criterion PASS post-smoke (5/5 sub-assertions).
2. Confirm Standing Gates 6/6 preserved.
3. Authorize Phase 5 GO (Domain 3: Vendor & admin per spec lines 342-393, includes new migration `0006_atlas_vendors.sql` + 3 cadenced checks: vendor renewal, Tailscale authkey, GitHub PAT).
4. Note: Phase 5 introduces a SQL migration -- first migration of the cycle. Standing Gate sequence (B2b + Garage anchor pre/post + atlas-mcp MainPID unchanged) plus migration-specific gate (idempotent INSERT ... ON CONFLICT DO NOTHING) will apply.
5. No new P6 lessons from Phase 4. SR #6 self-state probe ran cleanly at boot. P6 #29 + #32 mitigations both performed as designed (zero API-from-memory errors; canonical-copy avoided rework).

---

## 7. State at close

- atlas HEAD: `c85b52459838799a2658ac01caf3dea61f626b67` (Phase 4 commit; advanced from `54e3a26`)
- atlas-mcp.service: active, MainPID 2173807, ~9h+ uptime (Standing Gate #4 holding through Phases 0-4)
- atlas-agent.service: loaded inactive disabled (Phase 1 acceptance state preserved through Phases 2-3-4)
- mercury-scanner.service: active, MainPID 643409 (Standing Gate #6)
- Substrate anchors: bit-identical 96+ hours
- atlas.tasks state: 0 applicants, 0 digests (clean post-smoke; Phase 3 monitoring rows continue to land per scheduler tick)
- CK job_search_log.json: `{"seen_urls": []}` md5 `b241aa4aaadc2e512ae677d7c8348aef` -- bit-identical (read-only discipline preserved)

## 8. Cycle progress

5 of 10 phases complete. Pace clean. Phase 4 was the smallest scope so far (2 files, +231 LOC, 1 commit, no escalation).

```
[x] Phase 0 -- Pre-flight verification (7/7 PASS post-retry)
[x] Phase 1 -- atlas-agent.service systemd unit (3/3 PASS first-try)
[x] Phase 2 -- Agent loop skeleton (1/1 PASS first-try post-amendment; P6 #32 mitigation applied at write time)
[x] Phase 3 -- Domain 1: Infrastructure monitoring (1/1 PASS post-bug-fix; 22 atlas.tasks rows/cycle; P6 #33 banked from spec/directive divergence)
[x] Phase 4 -- Domain 2: Talent operations (1/1 PASS first-try; 5/5 smoke; P6 #29+#32 mitigations performed clean)
[~] Phase 5 -- Domain 3: Vendor & admin (NEXT; new migration 0006_atlas_vendors.sql + 3 cadenced checks)
[ ] Phase 6 -- Domain 4: Mercury supervision
[ ] Phase 7 -- Communication helper (atlas.events + Telegram; deferred to v0.1.1 OR inline create_event helper at Phase 7 PD discretion)
[ ] Phase 8 -- Tests
[ ] Phase 9 -- Production deployment (enable + start)
[ ] Phase 10 -- Ship report
```

-- PD (Cowork; Head of Engineering)
