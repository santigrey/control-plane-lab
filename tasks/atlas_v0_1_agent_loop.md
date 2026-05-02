# Atlas v0.1 -- Operations Agent Loop Build Spec

**Spec version:** 1.0
**Spec date:** 2026-05-01 (Day 77 evening)
**Author:** Paco (COO)
**Executor:** PD (Cowork)
**Cycle name:** Atlas v0.1 Agent Loop
**Branch:** `santigrey/atlas` (existing)
**Repo:** atlas package on Beast `/home/jes/atlas/`
**This cycle advances:** Atlas-as-Operations-agent macro-objective (per CHARTERS Charter 5; per workflow tightening Rule 5 single-line objective check).

**Canonical references (read before executing):**
- `CHARTERS_v0.1.md` Charter 5 (Operations -- Atlas) + Sub-agent Definitions (Mercury) + v0.2 amendment Day 77
- `docs/atlas_sop_v1_0.md` (operating procedures Atlas implements)
- `docs/paco_request_atlas_v0_1_agent_loop_picks.md` (8 ratified architectural picks; immutable)
- `docs/inter_department_sops_v1_0.md` (handoff patterns between depts)
- `docs/feedback_paco_pre_directive_verification.md` (5 standing rules + 30 P6 lessons + SR #6)
- Existing atlas package code: `/home/jes/atlas/src/atlas/`

---

## Overview

Atlas v0.1 substrate (Cycles 1A-1I, ratified Day 76) shipped 10 atlas-mcp tools + atlas.tasks/atlas.events/atlas.memory schemas. What this cycle adds: the **always-on agent loop** that consumes atlas.tasks, runs scheduled domain work, and writes atlas.events. After this cycle, Atlas transitions from "substrate available" to "working employee."

---

## v0.1 SUBSTRATE GAP NOTE (added Day 78 morning post-Phase 3, per docs/paco_response_atlas_v0_1_phase3_confirm_phase4_go.md Ruling 6)

**Constraint:** atlas.events MCP write helper is deferred to v0.2 / Mr Robot build per v0.2 P5 #42. No canonical `create_event` reference impl exists in atlas.* source at v0.1 build time. The only canonical-reference write path is `atlas.mcp_server.tasks.create_task` (Cycle 1I commit `d383fe0`), which writes to `atlas.tasks`.

**v0.1 resolution:** All Domain 1-4 telemetry/event writes go to `atlas.tasks` (with `status='done'` so the poller does not re-claim them) using the canonical `_create_monitoring_task` helper pattern adapted from Phase 3 (`src/atlas/agent/domains/infrastructure.py`). The 5 canonical payload.kind values from Phase 3 set the precedent: Domains 2-4 follow the same `payload.kind = <domain>_<event>` convention.

**Aspirational architecture:** All references to `atlas.events` in this spec (Phases 3-9) describe the **v0.1.1 target architecture** -- not v0.1 implementation. v0.1.1 will introduce the canonical `create_event` helper (likely in same cycle as Mr Robot build) and migrate Domain 1-4 writes from `atlas.tasks` to `atlas.events`, preserving the tier-stratified severity model.

**Impact on this spec:** Phase 3 acceptance gate amended below to reflect atlas.tasks. Phase 4-7 spec sections continue to reference atlas.events as the architectural target; PD applies the atlas.tasks-as-proxy pattern from Phase 3 precedent at implementation time (no spec re-amendment needed for each phase since the pattern is named here). Phase 9 acceptance gates 503/471/479 amend by reference: "atlas.events" reads as "atlas.tasks for v0.1; atlas.events for v0.1.1."

**Why this matters:** Silently overriding spec-canonical text via handoff/directive is canon hygiene failure. The v0.1 substrate gap should have been surfaced in this spec at original authoring time; it was not. P6 #33 (Day 78 morning) banks the lesson + mitigation pattern.


**Scope (per CEO Day 77 ratification: Option A + Mercury):**
- All three Charter 5 domains at minimum-viable depth:
  - Domain 1: Infrastructure monitoring (host vitals, service uptime, substrate anchors)
  - Domain 2: Talent operations (job_search_log reader; recruiter watcher DEFERRED v0.1.1)
  - Domain 3: Vendor & admin (vendor metadata + Tailscale auth key + GitHub PAT manual tracking)
- Domain 4: Mercury supervision (liveness + start/stop; trade subscription DEFERRED v2)
- Communication: atlas.events writes (tier-stratified) + Telegram dispatch helper (Tier 3)

**Out of scope (explicit deferrals):**
- Mercury trade-event subscription (Mercury v2 cycle)
- Real-money flag flip enforcement beyond fail-closed Tier 3 raise (full pre-flight checklist gate is Mercury v2)
- Recruiter watcher / Gmail integration (Atlas v0.1.1)
- Real GitHub PAT API expiration check (Atlas v0.1.1)
- Mac mini monitoring (DNS intermittency v0.2 P5 #35)
- Alexandra-side dashboard banner subscriber (Alexandra v0.3+)
- atlas.events archival rotation (Atlas v0.1.1)

---

## Architecture target

```
        Beast (192.168.1.152)
        ----
        atlas-agent.service (systemd)
            |
            +-- python -m atlas.agent
                    |
                    +-- asyncio.gather() of 3 coroutines:
                        |
                        +-- task_poller       (5s cadence; atlas.tasks SKIP LOCKED)
                        +-- scheduler         (cron-like; domain work)
                        +-- event_subscriber  (skeleton; v0.2 Mr Robot integration)
                        |
                        +-- domains/
                            +-- infrastructure.py  (Domain 1)
                            +-- talent.py          (Domain 2)
                            +-- vendor.py          (Domain 3)
                            +-- mercury.py         (Domain 4)
                        |
                        +-- communication.py       (atlas.events + Telegram)
```

**Substrate untouched:** atlas-mcp.service stays running. control-postgres-beast + control-garage-beast anchors must be bit-identical pre/post (Standing Gate 5).

---

## Phase 0 -- Pre-flight verification (PD reads & verifies)

Before writing any code, PD verifies live state:

0.1 `git log --oneline -3` on `/home/jes/atlas/` confirms HEAD on santigrey/atlas branch with Cycle 1I close at `d4f1a81` (or later).

0.2 `systemctl is-active atlas-mcp.service` returns `active`.

0.3 `systemctl is-active mercury-scanner.service` returns `active` (queried via SSH to CK).

0.4 `curl -s http://192.168.1.40:9090/api/v1/query?query=up` returns 200 from Beast (Prometheus on SlimJim reachable for Domain 1 query).

0.5 SSH from Beast to ck/goliath/slimjim/kalipi succeeds with key-based auth (no password prompt).

0.6 `docker inspect control-postgres-beast --format '{{.State.StartedAt}}'` and `docker inspect control-garage-beast --format '{{.State.StartedAt}}'` return canonical anchors:
  - postgres: `2026-04-27T00:13:57.800746541Z`
  - garage: `2026-04-27T05:39:58.168067641Z`

0.7 atlas package venv exists at `/home/jes/atlas/.venv` and has the existing dependencies (psycopg[binary,pool], httpx, mcp, structlog, pydantic). [Day 78 amended per paco_response_atlas_v0_1_phase0_unblock.md; verified live: pyproject uses psycopg, NOT asyncpg.]

**Pre-flight failure:** if any 0.x check fails, PD writes `paco_request_atlas_v0_1_phase0_blocker.md` and stops. Do NOT proceed to Phase 1.

**Pre-flight pass:** PD writes `paco_review_atlas_v0_1_phase0_preflight.md` with all 7 verifications recorded; proceed to Phase 1.

---

## Phase 1 -- atlas-agent.service systemd unit

Mirror `atlas-mcp.service` Cycle 1G pattern.

**1.1** Create `/etc/systemd/system/atlas-agent.service`:

```ini
[Unit]
Description=Atlas Operations Agent Loop -- Santigrey Enterprises
Documentation=https://github.com/santigrey/control-plane-lab/blob/main/docs/atlas_sop_v1_0.md
After=network-online.target docker.service atlas-mcp.service
Wants=network-online.target
Requires=atlas-mcp.service

[Service]
Type=simple
User=jes
Group=jes
WorkingDirectory=/home/jes/atlas
Environment=PYTHONUNBUFFERED=1
Environment=ATLAS_AGENT_LOG_LEVEL=INFO
EnvironmentFile=/home/jes/atlas/.env
ExecStart=/home/jes/atlas/.venv/bin/python -m atlas.agent
Restart=on-failure
RestartSec=10s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**1.2** `sudo systemctl daemon-reload`

**1.3** Verify with `systemctl status atlas-agent.service` returns `loaded inactive (not enabled)` -- this is correct; we don't enable until Phase 9 after code exists.

**Acceptance Phase 1:** unit file exists; daemon-reload clean; `systemctl status` shows loaded inactive.

---

## Phase 2 -- Agent loop skeleton

**2.1** New package: `src/atlas/agent/__init__.py` (empty marker file).

**2.2** `src/atlas/agent/__main__.py`:

```python
"""Atlas Operations Agent entry point. Run via `python -m atlas.agent` or atlas-agent.service."""
import asyncio
import logging
import sys
from atlas.agent.loop import run

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    stream=sys.stderr,
)

if __name__ == '__main__':
    asyncio.run(run())
```

**2.3** `src/atlas/agent/loop.py`:

Three coroutines wrapped in crash-isolation try/except/sleep:

```python
"""Atlas agent main loop -- 3 concurrent coroutines under one event loop."""
import asyncio
import logging
from atlas.agent.poller import task_poller
from atlas.agent.scheduler import scheduler
from atlas.agent.event_subscriber import event_subscriber

log = logging.getLogger(__name__)

async def isolate(name, coro_factory):
    """Run coro forever with crash isolation. One crash does not cascade."""
    while True:
        try:
            await coro_factory()
        except Exception as e:
            log.exception(f'{name} crashed: {e}; restarting in 30s')
            await asyncio.sleep(30)

async def run():
    log.info('Atlas agent loop starting')
    await asyncio.gather(
        isolate('task_poller', task_poller),
        isolate('scheduler', scheduler),
        isolate('event_subscriber', event_subscriber),
    )
```

**2.4** `src/atlas/agent/poller.py` skeleton:

```python
"""Polls atlas.tasks for pending rows; claims via SKIP LOCKED; executes; writes results.

Per P6 #29 + Cycle 1I canonical pattern (atlas.mcp_server.tasks.claim_task).
Spec amended Day 78 morning per docs/paco_response_atlas_v0_1_phase2_db_api_amendment.md
to correct 5 directive-author errors: (1) get_pool->Database, (2) asyncpg->psycopg API,
(3) started_at->updated_at, (4) completed_at->updated_at, (5) RETURNING column set
+ payload.kind extraction (kind lives inside payload jsonb, no top-level column).
"""
import asyncio
import logging
from atlas.db import Database

log = logging.getLogger(__name__)


async def task_poller():
    db = Database()
    while True:
        # Claim one pending task via FOR UPDATE SKIP LOCKED (Cycle 1I state machine)
        async with db.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE atlas.tasks SET status='running', updated_at=now() "
                    "WHERE id = ("
                    "  SELECT id FROM atlas.tasks "
                    "  WHERE status='pending' "
                    "  ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED"
                    ") "
                    "RETURNING id, payload"
                )
                row = await cur.fetchone()
                await conn.commit()
        if row is None:
            await asyncio.sleep(5)  # 5-second cadence per Pick 2
            continue
        task_id, payload = row[0], row[1]
        log.info(f'Claimed task {task_id} payload_kind={payload.get("kind") if isinstance(payload, dict) else None}')
        # Dispatch to handler (TODO Phase 3+: domain-specific handlers)
        # For now, mark as done with no-op handler
        async with db.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE atlas.tasks SET status='done', updated_at=now() WHERE id=%s",
                    (task_id,)
                )
                await conn.commit()
```

**2.5** `src/atlas/agent/scheduler.py` skeleton:

```python
"""Cron-like scheduler. Runs domain work at defined cadences."""
import asyncio
import logging
from datetime import datetime, timezone

log = logging.getLogger(__name__)

async def scheduler():
    """Tick once per minute; dispatch domain work based on cadence rules."""
    last_run = {}  # domain_name -> last UTC datetime
    while True:
        now = datetime.now(tz=timezone.utc)
        # Domain dispatchers added Phase 3+
        await asyncio.sleep(60)
```

**2.6** `src/atlas/agent/event_subscriber.py` skeleton:

```python
"""Event subscriber -- placeholder for v0.2 Mr Robot security_signal integration."""
import asyncio
import logging

log = logging.getLogger(__name__)

async def event_subscriber():
    """v0.1: idle. v0.2: subscribes to atlas.events for kind=security_signal."""
    while True:
        await asyncio.sleep(300)  # 5-min idle heartbeat
        log.debug('event_subscriber heartbeat (v0.1 placeholder)')
```

**Acceptance Phase 2:** `cd /home/jes/atlas && .venv/bin/python -m atlas.agent` runs for 30 seconds without crashing; logs show all 3 coroutines started; ctrl-C exits clean.

---

## Phase 3 -- Domain 1: Infrastructure monitoring

**3.1** `src/atlas/agent/domains/__init__.py` (empty marker).

**3.2** `src/atlas/agent/domains/infrastructure.py`:

Responsibilities:
- `system_vitals_check()`: every 5min; per-node CPU/RAM/disk via Prometheus first, SSH fallback
- `service_uptime_check()`: every 1min; per-node service health
- `substrate_anchor_check()`: hourly; verify control-postgres-beast + control-garage-beast StartedAt unchanged

Nodes monitored: ck, beast, goliath, slimjim, kalipi (NOT macmini -- DNS intermittency).

**Per-node thresholds (Tier 2 alert):**
- CPU sustained >85% for 5min
- RAM >90%
- Disk >85%

**Service registry (Tier 2 alert if down; Tier 3 if substrate-critical):**
- ck: control-postgres (Tier 3), orchestrator.service (Tier 3), homelab-mcp.service (Tier 2), nginx (Tier 3)
- beast: control-postgres-beast (Tier 3), control-garage-beast (Tier 3), atlas-mcp.service (Tier 2)
- goliath: ollama (Tier 2)
- slimjim: mosquitto (Tier 2), prometheus container (Tier 2; also self-degraded for Domain 1 query), grafana (Tier 1), netdata (Tier 1)

**Anchor check (Tier 3 if drift):**
- `docker inspect control-postgres-beast --format '{{.State.StartedAt}}'` matches `2026-04-27T00:13:57.800746541Z`
- `docker inspect control-garage-beast --format '{{.State.StartedAt}}'` matches `2026-04-27T05:39:58.168067641Z`

Write monitoring rows to `atlas.tasks` per v0.1 SUBSTRATE GAP NOTE (above) using canonical `_create_monitoring_task` helper. Five payload.kind values: `monitoring_cpu` / `monitoring_ram` / `monitoring_disk` / `service_uptime` / `substrate_check`. Rows status=`done` so poller does not re-claim. v0.1.1 migrates to atlas.events with kind={system_vitals/service_uptime/substrate_anchor_drift} when canonical create_event helper exists.

**Acceptance Phase 3:** Prometheus query returns 200; SSH fallback works on at least one node; substrate anchor check matches canonical values; 22 atlas.tasks rows per cycle (5 cpu + 5 ram + 5 disk + 6 service_uptime + 1 substrate_check) with all 5 directive-specified payload.kind values present and correctly keyed (no dict-spread shadowing per Phase 3 bug-fix discipline).

---

## Phase 4 -- Domain 2: Talent operations

**4.1** `src/atlas/agent/domains/talent.py`:

Responsibilities:
- `job_search_log_check()`: on-cadence (daily 08:00 UTC) + ad-hoc trigger
- `weekly_digest_compile()`: Mondays 07:00 local

**Job search log path:** `/home/jes/control-plane/job_search_log.json` (currently `{"seen_urls": []}`).

**Detection logic:**
- Read file; compare entries against atlas-tracked-state
- New entries -> write atlas.events row with `kind='applicant_logged'`, payload includes URL + parsed metadata

**Weekly digest:** aggregate atlas.events `kind='applicant_logged'` from past 7 days; write summary atlas.events row with `kind='weekly_digest_talent'`.

**Recruiter watcher: SKIP at v0.1.** Stub with TODO comment referencing v0.1.1.

**Acceptance Phase 4:** Domain 2 reads job_search_log.json without error; new-entry detection writes correct atlas.events; weekly digest job is scheduled (verified via scheduler logs).

---

## Phase 5 -- Domain 3: Vendor & admin

**5.1** Migration `src/atlas/db/migrations/0006_atlas_vendors.sql` (path corrected Day 78 morning post-Phase 4; existing migrations 0001-0005 live in `src/atlas/db/migrations/` per Beast atlas repo verified live):

```sql
-- Atlas v0.1 Phase 5: vendor & admin tracking
CREATE TABLE IF NOT EXISTS atlas.vendors (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    plan_tier TEXT,
    billing_cycle TEXT CHECK (billing_cycle IN ('monthly', 'annual', 'one-time', 'unknown')),
    renewal_date DATE,
    monthly_cost_usd NUMERIC(10,2),
    primary_contact_url TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'cancelled', 'free')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_atlas_vendors_renewal ON atlas.vendors (renewal_date) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_atlas_vendors_status ON atlas.vendors (status);

-- Initial seed (renewal dates left NULL; Sloan fills via dashboard or direct UPDATE)
INSERT INTO atlas.vendors (name, plan_tier, billing_cycle, primary_contact_url, status) VALUES
    ('Anthropic',   'unknown', 'monthly', 'https://console.anthropic.com',      'active'),
    ('GitHub',      'unknown', 'monthly', 'https://github.com/settings/billing','active'),
    ('Twilio',      'unknown', 'monthly', 'https://console.twilio.com',         'active'),
    ('ElevenLabs',  'unknown', 'monthly', 'https://elevenlabs.io/app',          'active'),
    ('Per Scholas', 'program', 'one-time','https://perscholas.org',             'active'),
    ('Google',      'unknown', 'monthly', 'https://myaccount.google.com',       'active'),
    ('Tailscale',   'unknown', 'monthly', 'https://login.tailscale.com',        'active')
ON CONFLICT (name) DO NOTHING;
```

**5.2** `src/atlas/agent/domains/vendor.py`:

Responsibilities:
- `vendor_renewal_check()`: daily 06:00 UTC; query atlas.vendors WHERE status='active' AND renewal_date IS NOT NULL; flag 14-day + 3-day warnings
- `tailscale_authkey_check()`: daily 06:00 UTC; `tailscale status --json` parse; alert if expiry within 30 days
- `github_pat_check()`: daily 06:00 UTC; read expiration from atlas.vendors.notes (manual tracking; v0.1.1 wires real API)

**Tier mapping:**
- 14-day warning: Tier 2 (notify Paco)
- 3-day warning: Tier 3 (Telegram)

**Acceptance Phase 5:** migration runs clean (no errors; 7 rows inserted); vendor.py executes without crashing; synthetic 5-day-out renewal_date triggers correct Tier 2 alert.

---

## Phase 6 -- Domain 4: Mercury supervision

**6.1** `src/atlas/agent/domains/mercury.py`:

Responsibilities:
- `mercury_liveness_check()`: every 5min; `ssh ck systemctl is-active mercury-scanner.service`; alert if not `active`
- `mercury_trade_activity_check()`: daily 08:00 UTC; query mercury.trades for new rows since last check; if mercury-scanner active but zero new trades >7 days, raise Tier 2
- `mercury_real_money_failclosed()`: continuous (every 5min); query `mercury.trades WHERE paper_trade=false`; raise Tier 3 IMMEDIATELY unless `/home/jes/control-plane/docs/mercury_real_money_ratification.md` exists
- `mercury_start()` / `mercury_stop()`: via `ssh ck sudo systemctl start|stop mercury-scanner.service`; only invoked from atlas.tasks claim with kind=`mercury_control`; Tier 2 cancel-window required before execution

**Live state at spec time:**
- mercury-scanner.service: active running on CK
- mercury.trades: 142 rows; latest 2026-04-26
- paper_trade default true
- Mercury repo location: `/home/jes/polymarket-ai-trader/` on CK

**Mercury data store:** `mercury.*` schema in controlplane DB on CK (NOT replicated to Beast per B2b Q4=C). Atlas queries mercury data via cross-host PG read on CK. Use existing connection pool pattern but route reads to CK conn-string from .env.

**Acceptance Phase 6:** Domain 6 detects mercury-scanner.service is active (returns `True` for liveness); trade activity check correctly identifies the >7-day-no-trades gap currently open; fail-closed test (mock paper_trade=false row) raises Tier 3 with payload referencing the ratification-doc requirement.

---

## Phase 7 -- Communication helper

**7.1** `src/atlas/agent/communication.py`:

Responsibilities:
- `emit_event(source, kind, severity, payload)`: writes atlas.events row with auto-tier mapping
- `dispatch_telegram(message)`: sends via existing Twilio bot endpoint (Tier 3 only)

**Tier mapping:**
- severity='info' -> Tier 1: atlas.events only
- severity='warn' -> Tier 2: atlas.events + dashboard banner (Alexandra reads kind allowlist)
- severity='critical' -> Tier 3: atlas.events + Telegram + dashboard banner

**Telegram dispatch:** Use the Twilio Programmable Messaging API (denver number +1 720 902 7314 per memory). Endpoint + auth from `.env`:
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_FROM_NUMBER`
  - `SLOAN_PHONE_NUMBER`

If .env doesn't have these, log warning + skip Telegram; do not crash. (Wiring Twilio bot into atlas package is a first-time integration; mock initially with `if TWILIO_ENABLED:` guard.)

**Acceptance Phase 7:** emit_event writes correctly for all 3 tiers; dispatch_telegram works in mock mode (logs intended message); when .env has Twilio creds, real test message arrives at Sloan's phone.

---

## Phase 8 -- Tests

**8.1** Unit tests per domain (`src/atlas/agent/test_*.py`):
- `test_loop.py`: loop crash-isolation works (one coroutine raising does not stop others)
- `test_poller.py`: claim semantics correct; SKIP LOCKED prevents double-claim
- `test_infrastructure.py`: Prometheus query parsing; SSH fallback path; threshold detection
- `test_talent.py`: job_search_log parsing; new-entry detection; digest aggregation
- `test_vendor.py`: renewal warning thresholds (14d / 3d); Tailscale parsing; GitHub PAT note reading
- `test_mercury.py`: liveness check; trade activity check; fail-closed raises Tier 3
- `test_communication.py`: tier mapping; Telegram mock dispatch

**8.2** Integration test (`test_integration.py`):
- Spin up agent loop for 30s with mocked atlas.tasks rows
- Verify all coroutines run
- Verify atlas.events rows written

**8.3** Smoke test (manual; documented in ship report):
- enable + start atlas-agent.service
- tail journalctl -u atlas-agent.service for 5 minutes
- verify atlas.events table receives writes from all 4 domains
- verify mercury-scanner.service still healthy (we did not break it)

**Acceptance Phase 8:** all unit tests pass; integration test passes; smoke test documented in ship report.

---

## Phase 9 -- Production deployment

**9.1** `sudo systemctl enable atlas-agent.service`

**9.2** `sudo systemctl start atlas-agent.service`

**9.3** First-hour observation: `journalctl -u atlas-agent.service -f` for 1 hour; capture log excerpt for ship report.

**9.4** Verify atlas.events table receives writes from all 4 domains within first hour.

**9.5** Verify substrate anchors UNCHANGED post-deploy:
- postgres: `2026-04-27T00:13:57.800746541Z`
- garage: `2026-04-27T05:39:58.168067641Z`

**9.6** Verify mercury-scanner.service still active and unaffected.

**Acceptance Phase 9:** atlas-agent.service active running for >=1 hour; atlas.events shows >=10 rows from each domain; substrate anchors bit-identical; mercury-scanner.service unaffected.

---

## Phase 10 -- Ship report

`paco_review_atlas_v0_1_agent_loop_ship.md` includes:

- What works (per Phase acceptance)
- 6 Acceptance Gates pass/fail
- 6 Standing Gates pass/fail
- Substrate anchor verification (must be bit-identical)
- atlas.events row counts per domain (first-hour sample)
- Known issues + P5 candidates banked
- One-line objective check (per Rule 5): "This cycle advances Atlas-as-Operations-agent macro-objective."

---

## Acceptance Gates (6)

| Gate | Description | Evidence |
|---|---|---|
| 1 | atlas-agent.service Up; MainPID rotates clean on restart | `systemctl status` + restart test |
| 2 | 3 asyncio coroutines all running concurrently | journalctl shows 3 coro startups; one synthetic crash recovers |
| 3 | Each Domain (1-4) writes >=1 atlas.events row in first hour | SQL count by source/kind |
| 4 | Mercury liveness check correctly detects active state; fail-closed raises Tier 3 on synthetic paper_trade=false | mercury.py test output |
| 5 | Substrate anchors bit-identical pre/post | docker inspect StartedAt before + after |
| 6 | secret-grep clean on commit; dependency tree audit clean | git diff scan + pip audit |

## Standing Gates (6)

| Gate | Description |
|---|---|
| SG1 | All 6 standing rules applied (verified-live discipline; one-step-at-a-time; closure pattern; handoff format; pre-directive verification; self-state probe) |
| SG2 | B2b subscription untouched (`SELECT * FROM pg_publication` unchanged) |
| SG3 | Garage cluster untouched (StartedAt anchor) |
| SG4 | mcp_server.py on CK untouched (control plane separation) |
| SG5 | atlas-mcp loopback :8001 bind preserved |
| SG6 | nginx vhosts unchanged on CK |

---

## Risk register

- **Cross-host SSH from Beast** -- relies on existing key-based auth. If any node loses key, Domain 1 degrades to "node_unreachable" alert (NOT failure cascade). Mitigation: per-node try/except; one node failure does not stop others.
- **Telegram dispatch first-time wiring** -- Twilio creds in .env may not be populated. Mitigation: guard with `if TWILIO_ENABLED:`; mock-mode logs intended message; ship report flags whether real Telegram tested.
- **Mercury liveness via SSH to CK** -- if CK SSH down, Atlas reports `mercury_unknown` not `mercury_down`. Critical to distinguish.
- **3 asyncio coroutines crash isolation** -- one crash should NOT cascade. Mitigation: `isolate()` wrapper in loop.py.
- **Prometheus query failure** -- fallback to SSH-direct. If SSH also fails, Tier 2 alert `monitoring_degraded`.
- **mercury.* schema cross-host read** -- Atlas on Beast must connect to CK Postgres for Mercury queries. New conn string. Test connection at Phase 0.5.

---

## P5 candidates flagged at spec time

- Mac mini integration (DNS intermittency v0.2 P5 #35)
- Recruiter watcher (Gmail integration; v0.1.1)
- Real GitHub PAT API expiration check (v0.1.1)
- Mercury repo rename `polymarket-ai-trader` -> `mercury` (cosmetic; CEO discretion)
- atlas.events archival policy (Atlas SOP says 90 days general; Mr Robot SOP says 365 days for security; reconcile in Atlas v0.1.1)
- Telegram dispatch failover (no failsafe channel currently; consider email backup)
- atlas.vendors renewal_date population (Sloan workflow: dashboard form vs direct SQL)
- Mercury cross-host PG conn string (live test at Phase 0.5; may surface .env addition)

---

## File-level changes expected

**NEW (in atlas package):**
- `src/atlas/agent/__init__.py`
- `src/atlas/agent/__main__.py`
- `src/atlas/agent/loop.py`
- `src/atlas/agent/poller.py`
- `src/atlas/agent/scheduler.py`
- `src/atlas/agent/event_subscriber.py`
- `src/atlas/agent/communication.py`
- `src/atlas/agent/domains/__init__.py`
- `src/atlas/agent/domains/infrastructure.py`
- `src/atlas/agent/domains/talent.py`
- `src/atlas/agent/domains/vendor.py`
- `src/atlas/agent/domains/mercury.py`
- `src/atlas/agent/test_loop.py`
- `src/atlas/agent/test_poller.py`
- `src/atlas/agent/domains/test_infrastructure.py`
- `src/atlas/agent/domains/test_talent.py`
- `src/atlas/agent/domains/test_vendor.py`
- `src/atlas/agent/domains/test_mercury.py`
- `src/atlas/agent/test_communication.py`
- `src/atlas/agent/test_integration.py`
- `migrations/0006_atlas_vendors.sql`

**NEW (system):**
- `/etc/systemd/system/atlas-agent.service`

**MODIFIED:**
- `pyproject.toml` -- new deps if needed (asyncssh OR paramiko for SSH; httpx already exists for Prometheus)
- `.env` -- may need TWILIO_* and MERCURY_DB_DSN (cross-host PG read) additions

**NOT MODIFIED (Standing Gate enforcement):**
- `src/atlas/db.py` (existing async pool)
- `src/atlas/mcp_client.py`
- `src/atlas/embeddings.py`
- `src/atlas/inference.py`
- `src/atlas/mcp_server.py`
- `/etc/systemd/system/atlas-mcp.service`
- nginx vhosts on CK
- B2b publication / subscription
- Garage configuration

---

## CEO touch points during build

- Phase 0 pre-flight: PD writes paco_review; CEO routes to Paco
- Phase 5 vendor seed: PD inserts placeholder rows; CEO action ITEM (post-ship): fill renewal_date values via dashboard or SQL
- Phase 7 Telegram wiring: CEO confirms +1 720 902 7314 is correct destination; provides Twilio creds for .env if not already
- Phase 9 deployment: PD enables service; CEO acknowledgment of go-live; observes first Tier 3 alert if/when it fires
- Phase 10 ship report: PD writes; CEO routes to Paco for close-confirm

---

## Cycle exit criteria

Cycle CLOSED when:
- All 6 Acceptance Gates PASS
- All 6 Standing Gates PASS
- Ship report committed at `docs/paco_review_atlas_v0_1_agent_loop_ship.md`
- Paco close-confirms with `docs/paco_response_atlas_v0_1_agent_loop_close_confirm.md`
- CHECKLIST.md audit-trail entry appended (per workflow tightening Rule 3)
- atlas-agent.service running for >=24 hours without intervention

---

*End of Atlas v0.1 Agent Loop Build Spec.*
