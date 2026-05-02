# paco_directive_atlas_v0_1_phase7

**To:** PD (Cowork) | **From:** Paco | **Date:** 2026-05-02 Day 78 mid-day
**Authority:** CEO ratified Day 78 mid-day (Atlas Phase 7 next-cycle GO; A=PD-executable / B=ship-both-test-mock / C=combined 7.1+7.2 / D=thorough pre-directive verification / α=directive supersedes spec for Phase 7 corrections); reachability cycle CLOSED Day 78 mid-day (HEAD `5fe7d81`).
**Status:** ACTIVE
**Tracks:** `tasks/atlas_v0_1_agent_loop.md` Phase 7 (lines 395-447).
**Predecessor:** Phase 6 close-confirm (atlas commit `147f13c` security redact; previous `10adf9f` Phase 6 close).
**Target host:** Beast (atlas package authoring + agent runtime host); cross-host SSH+psycopg2 to CK for Phase 7.2 mercury control + atlas.tasks cancel claim queries.

---

## 0. Directive supersedes spec for these 5 corrections (α path ratified)

Live verification (Paco-side, 12 probes Day 78 mid-day) caught 5 spec divergences. **PD reads this directive as authority for Phase 7; spec at `tasks/atlas_v0_1_agent_loop.md` lines 432-447 has the noted gaps.**

| # | Spec assumption (line ref) | Live finding | Directive correction |
|---|---|---|---|
| 1 | Spec line 432 implies `atlas.events.severity` column | `\d atlas.events` shows columns: `id, ts, source, kind, payload`. NO severity column. | `severity` carried inside `payload` JSONB as `payload.severity` ('info'|'warn'|'critical'); tier metadata as `payload.tier` (1|2|3). |
| 2 | Spec line 459 implies `atlas.tasks.kind` column for `mercury_control_cancel` claim | `\d atlas.tasks` shows: `id, status, created_at, updated_at, owner, payload, result`. NO top-level kind. status check constraint: `pending|running|done|failed`. | Cancel-window detection query: `SELECT id FROM atlas.tasks WHERE payload->>'kind'='mercury_control_cancel' AND created_at > <window_start_ts> AND status='pending'`. |
| 3 | Spec line 444 names `SLOAN_PHONE_NUMBER` env var | CK `/home/jes/control-plane/.env` has `TWILIO_TO_NUMBER=<set>`; atlas/.env empty (0 bytes, created at Phase 6 close per Phase 6 review Probe #15) | Step 1.5 (CEO interactive): copy 4 vars from CK control-plane/.env to Beast atlas/.env, **renaming `TWILIO_TO_NUMBER` -> `SLOAN_PHONE_NUMBER`**. Reason: spec naming is provider-agnostic + matches P6 #34 forward-redaction discipline. |
| 4 | Day 78 morning override: "table=atlas.tasks not atlas.events" appears to conflict with Phase 7 spec | Override scope is **Domain monitoring findings** (kinds: monitoring_cpu/ram/disk, service_uptime, substrate_check) -- those are claimable tasks. Phase 7 `emit_event` is **telemetry/notification** -- different purpose. | `emit_event` writes to **atlas.events** as spec says (NOT atlas.tasks). Existing precedent: `mcp_client/client.py` line 213 + `embeddings/client.py` line 214 already write `INSERT INTO atlas.events (source, kind, payload) VALUES (%s, %s, %s::jsonb)` -- emit_event uses identical pattern. |
| 5 | Spec line 442 says "via existing Twilio bot endpoint" | No existing Twilio integration in atlas package. Twilio creds exist on CK `/home/jes/control-plane/.env` only. | First-time integration in atlas. Use `https://api.twilio.com/2010-04-01/Accounts/{ACCOUNT_SID}/Messages.json` with HTTP Basic auth (account_sid:auth_token); POST form-encoded `From={TWILIO_FROM_NUMBER}&To={SLOAN_PHONE_NUMBER}&Body={message}`. Guard with `TWILIO_ENABLED` env (default false in mock mode). Mock mode = `log.info('telegram_mock', message=...)`; real mode = httpx POST. |

---

## 1. Verified live (Paco pre-directive, Day 78 mid-day)

Per 5th standing rule + P6 #29.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | Standing Gate 1 (B2b anchor) PRE | `docker inspect control-postgres-beast` on beast | `2026-04-27T00:13:57.800746541Z` restart=0 |
| 2 | Standing Gate 2 (Garage anchor) PRE | `docker inspect control-garage-beast` on beast | `2026-04-27T05:39:58.168067641Z` restart=0 |
| 3 | Standing Gate 4 (atlas-mcp.service) PRE | `systemctl show atlas-mcp.service` on beast | MainPID=2173807 ActiveState=active |
| 4 | Standing Gate 5 (atlas-agent.service) PRE | `systemctl show atlas-agent.service` on beast | MainPID=0 ActiveState=inactive UnitFileState=disabled (Phase 1 acceptance preserved through 6 phases) |
| 5 | atlas HEAD PRE | `git log` on beast atlas | `147f13c` (Phase 6 redact) parent `10adf9f` (Phase 6 close) parent `af8768d` (Phase 5) |
| 6 | atlas working tree PRE | `git status -s` on beast atlas | clean |
| 7 | atlas.events schema (correction #1) | `\d atlas.events` via beast docker exec | `(id bigint, ts timestamptz, source text, kind text, payload jsonb)` -- NO severity column |
| 8 | atlas.tasks schema (correction #2) | `\d atlas.tasks` via beast docker exec | `(id uuid, status text, created_at, updated_at, owner text, payload jsonb, result jsonb)`; status check `pending|running|done|failed` -- NO kind column |
| 9 | mercury.py TODO line numbers (spec lines 345/347/357/359) | `grep -n 'TODO.*Phase 7\|def mercury_start\|def mercury_stop'` on beast | Lines 340 mercury_start def; 345 docstring TODO ref; 347 TODO Phase 7; 349 v0.1 stub log; 352 mercury_stop def; 357 docstring TODO ref; 359 TODO Phase 7; 361 v0.1 stub log -- ALL match spec |
| 10 | atlas/.env baseline | `ls -la + wc -l` on beast | mode 600 jes:jes; 0 bytes; created May 2 at Phase 6 close |
| 11 | Twilio creds availability | `grep -E '^(TWILIO|SLOAN_PHONE)' /home/jes/control-plane/.env` on CK | TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN/TWILIO_FROM_NUMBER/TWILIO_TO_NUMBER all set; SLOAN_PHONE_NUMBER NOT yet (rename at Step 1.5) |
| 12 | atlas Database wrapper API | `sed -n '27,60p' src/atlas/db/pool.py` on beast | psycopg_pool.AsyncConnectionPool; `Database()` -> `.connection()` async ctx mgr -> `.cursor()` async ctx mgr -> `.execute(SQL, params)` -> `.commit()` |
| 13 | atlas.events INSERT pattern (precedent #1) | `sed -n '210,220p' src/atlas/mcp_client/client.py` on beast | `INSERT INTO atlas.events (source, kind, payload) VALUES (%s, %s, %s::jsonb)` -- Phase 7 emit_event uses IDENTICAL form |
| 14 | atlas.events INSERT pattern (precedent #2) | line 214 `src/atlas/embeddings/client.py` on beast | same 3-arg INSERT pattern |
| 15 | poller dispatch state (Phase 7.2 invocation context) | `head poller.py` on beast | poller is scaffold, Cycle 1I claim semantics; "TODO Phase 3+: domain-specific handlers" -- mercury_start/stop will be invoked from a future handler dispatch (NOT in scope for Phase 7); for Phase 7.2, mercury_start/stop themselves enforce the cancel-window |
| 16 | _ssh_run, _create_monitoring_task, _alert_already_today reuse pattern | `grep -n` across domains/ | `infrastructure.py` lines 68 (_ssh_run) + 149 (_create_monitoring_task); `vendor.py` line 55 (_alert_already_today) -- all available for Phase 7.2 reuse |
| 17 | mercury.py cross-host helpers (Phase 6 carryover) | Phase 6 review confirmed | `_ck_python_query`, `_check_ratification_doc`, `_mercury_is_active`, `_ssh_run` -- all live in mercury.py from Phase 6; Phase 7.2 reuses for systemctl start|stop calls |

17 verified-live items, 0 mismatches, 5 spec corrections surfaced.

---

## 2. Phase 7 implementation

### 2.1 File inventory

| File | Action | Approximate size |
|---|---|---|
| `src/atlas/agent/communication.py` | NEW | ~180 lines |
| `src/atlas/agent/domains/mercury.py` | MODIFY (replace mercury_start/mercury_stop stubs lines 340-362) | ~+120 lines net |
| `src/atlas/agent/test_communication.py` | NEW | ~120 lines |
| `tests/test_mercury_phase7.py` | NEW (or modify existing test_mercury.py if present) | ~80 lines |
| `/home/jes/atlas/.env` | MODIFY (Step 1.5; CEO interactive) | +4 lines |

### 2.2 communication.py architecture (Phase 7.1)

```python
"""Atlas v0.1 Phase 7 -- Communication helper.

Per paco_directive_atlas_v0_1_phase7.md (Day 78 mid-day) section 0 corrections:
- atlas.events has no severity column; severity carried in payload.severity (string)
  + payload.tier (int 1|2|3) per the auto-mapping below.
- Telegram dispatch is first-time integration; Twilio Programmable Messaging API
  via httpx; guarded by TWILIO_ENABLED env (default mock-mode).

Tier mapping (severity -> tier -> dispatch):
- 'info' -> Tier 1: atlas.events row only.
- 'warn' -> Tier 2: atlas.events row + dashboard banner (Alexandra reads kind allowlist;
  dashboard banner is downstream consumer; Phase 7 only writes the row).
- 'critical' -> Tier 3: atlas.events row + Telegram (real or mock per TWILIO_ENABLED).
"""

from __future__ import annotations

import json
import logging
import os
import base64
from typing import Any, Optional

import httpx

from atlas.db import Database

log = logging.getLogger(__name__)


# Tier mapping; severity -> tier int
_SEVERITY_TIER = {'info': 1, 'warn': 2, 'critical': 3}
_VALID_SEVERITIES = frozenset(_SEVERITY_TIER.keys())

# Twilio Messaging API endpoint template
_TWILIO_API = 'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json'


def _twilio_enabled() -> bool:
    """Read TWILIO_ENABLED env. Default false (mock-mode)."""
    return os.getenv('TWILIO_ENABLED', 'false').lower() in ('1', 'true', 'yes')


async def emit_event(
    db: Database,
    *,
    source: str,
    kind: str,
    severity: str,
    payload: dict[str, Any],
) -> None:
    """Write atlas.events row; auto-map severity to tier; dispatch on critical.

    Args:
        db: Atlas Database wrapper (psycopg_pool.AsyncConnectionPool).
        source: event source label (e.g. 'atlas.mercury', 'atlas.infrastructure').
        kind: event kind (e.g. 'mercury_start_initiated', 'monitoring_cpu_high').
        severity: 'info' | 'warn' | 'critical' -- raises ValueError otherwise.
        payload: dict serialized into payload JSONB. Function adds 'severity' and
            'tier' keys (overwriting any caller-supplied values for those keys).

    Side effects:
        - INSERTs one row into atlas.events.
        - On severity='critical': calls dispatch_telegram with a derived message.
        - On severity='warn': writes only (dashboard banner is a downstream consumer
          that reads atlas.events; Phase 7 does not push to dashboard directly).
        - On severity='info': writes only.

    Failure mode: if INSERT fails, logs error + raises (caller's fault tolerance).
        Telegram dispatch failure (httpx error or 4xx/5xx) is caught + logged but
        does NOT raise (atlas.events row already persisted; failure-to-page is non-fatal).
    """
    if severity not in _VALID_SEVERITIES:
        raise ValueError(f"emit_event: severity must be one of {sorted(_VALID_SEVERITIES)}, got {severity!r}")
    tier = _SEVERITY_TIER[severity]
    enriched = dict(payload)  # shallow copy; do not mutate caller's dict
    enriched['severity'] = severity
    enriched['tier'] = tier
    async with db.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO atlas.events (source, kind, payload) VALUES (%s, %s, %s::jsonb)",
                (source, kind, json.dumps(enriched, default=str)),
            )
            await conn.commit()
    log.info('emit_event', source=source, kind=kind, severity=severity, tier=tier)
    if severity == 'critical':
        # Build human-readable message; payload may contain extra context
        # (caller responsibility to keep payload non-secret-bearing)
        message = f"[CRITICAL atlas.{source}] {kind}: " + json.dumps(payload, default=str)[:300]
        try:
            await dispatch_telegram(message)
        except Exception as e:
            log.error('telegram_dispatch_failed', error=str(e), kind=kind)
            # Do not raise; atlas.events row already persisted.


async def dispatch_telegram(message: str) -> None:
    """Send Telegram (SMS) via Twilio Programmable Messaging API.

    If TWILIO_ENABLED is false (default), logs intended message and returns (mock mode).
    If TWILIO_ENABLED is true, requires:
        - TWILIO_ACCOUNT_SID
        - TWILIO_AUTH_TOKEN
        - TWILIO_FROM_NUMBER (Denver A2P 10DLC registered number)
        - SLOAN_PHONE_NUMBER (destination)
    Missing env in real-mode: log warning + return (do NOT crash).

    Idempotency: caller responsibility; this helper does no dedup.
    """
    if not _twilio_enabled():
        log.info('telegram_mock', message=message)
        return
    sid = os.getenv('TWILIO_ACCOUNT_SID')
    token = os.getenv('TWILIO_AUTH_TOKEN')
    from_n = os.getenv('TWILIO_FROM_NUMBER')
    to_n = os.getenv('SLOAN_PHONE_NUMBER')
    if not all([sid, token, from_n, to_n]):
        log.warning('telegram_disabled_missing_env', has_sid=bool(sid), has_token=bool(token), has_from=bool(from_n), has_to=bool(to_n))
        return
    url = _TWILIO_API.format(sid=sid)
    auth_b64 = base64.b64encode(f"{sid}:{token}".encode()).decode()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            url,
            headers={'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/x-www-form-urlencoded'},
            content=f"From={from_n}&To={to_n}&Body={httpx.QueryParams({'b': message}).get('b')}",
        )
        if resp.status_code >= 400:
            log.error('telegram_http_error', status=resp.status_code, body=resp.text[:200])
            resp.raise_for_status()
        log.info('telegram_sent', sid=resp.json().get('sid', '?'))
```

Note: the URL-encoding of `Body` above is a stylized placeholder. PD: use `urllib.parse.quote_plus(message)` for production-correct encoding; stylized form above is for spec readability.

### 2.3 mercury.py rewire (Phase 7.2)

**Replace** stub at lines 340-362 (the two `mercury_start` and `mercury_stop` async funcs that currently log 'v0.1 stub' and return).

**New implementation pattern (one canonical helper + 2 thin wrappers):**

```python
from atlas.agent.communication import emit_event

# Cancel-window duration in seconds; spec section 7.2 specifies 15s.
_CANCEL_WINDOW_S = 15


async def _mercury_control(db: Database, action: str) -> None:
    """Execute mercury start|stop with Tier 2 cancel-window.

    Phase 7.2 (Day 78 mid-day): replaces v0.1 no-op stubs.

    Workflow:
        1. Capture window_start = now (UTC); compute window_end = window_start + 15s.
        2. emit_event Tier 2 atlas.events row (kind='mercury_control_initiated';
           payload includes action, window_start_iso, window_end_iso, cancel_via).
        3. asyncio.sleep(15) BUT polled in 1s increments to allow early cancel detection.
           Each iteration: query atlas.tasks for cancel claim; if found, abort + emit
           Tier 1 'mercury_control_cancelled' + return.
        4. After window: invoke `_ssh_run('192.168.1.10', 'jes', f'sudo systemctl {action} mercury-scanner.service')`.
        5. emit_event Tier 1 atlas.events row (kind='mercury_control_executed' with
           payload.outcome='executed'|'ssh_error'|'systemctl_error').

    Cancel claim detection (correction #2 from directive section 0):
        SELECT id FROM atlas.tasks
        WHERE payload->>'kind' = 'mercury_control_cancel'
          AND created_at > %s   -- window_start
          AND status = 'pending'
        LIMIT 1

    On match: also UPDATE atlas.tasks SET status='done' for that row (caller-side
        idempotency; cancel claim is consumed once observed).
    """
    assert action in ('start', 'stop'), f"_mercury_control: action must be start|stop, got {action!r}"
    from datetime import datetime, timezone, timedelta
    window_start = datetime.now(timezone.utc)
    window_end = window_start + timedelta(seconds=_CANCEL_WINDOW_S)
    log.info('mercury_control_initiated', action=action, window_s=_CANCEL_WINDOW_S)
    await emit_event(
        db, source='atlas.mercury', kind='mercury_control_initiated', severity='warn',
        payload={
            'action': action,
            'window_start_iso': window_start.isoformat(),
            'window_end_iso': window_end.isoformat(),
            'cancel_via': "INSERT INTO atlas.tasks (status, payload) VALUES ('pending', '{\"kind\":\"mercury_control_cancel\"}'::jsonb)",
        },
    )
    # Polled cancel-window: 15 iterations of 1s sleep + cancel check
    cancelled = False
    for _ in range(_CANCEL_WINDOW_S):
        await asyncio.sleep(1)
        async with db.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id FROM atlas.tasks "
                    "WHERE payload->>'kind' = 'mercury_control_cancel' "
                    "  AND created_at > %s "
                    "  AND status = 'pending' "
                    "LIMIT 1",
                    (window_start,),
                )
                row = await cur.fetchone()
                if row is not None:
                    cancel_id = row[0]
                    # Consume the cancel claim
                    await cur.execute(
                        "UPDATE atlas.tasks SET status='done', updated_at=now() WHERE id=%s",
                        (cancel_id,),
                    )
                    await conn.commit()
                    cancelled = True
                    break
    if cancelled:
        await emit_event(
            db, source='atlas.mercury', kind='mercury_control_cancelled', severity='info',
            payload={'action': action, 'cancel_task_id': str(cancel_id)},
        )
        return
    # Window elapsed without cancel; execute via SSH+sudo systemctl
    rc, out, err = await _ssh_run(CK_HOST, CK_USER, f'sudo systemctl {action} mercury-scanner.service')
    outcome = 'executed' if rc == 0 else ('ssh_error' if rc < 0 else 'systemctl_error')
    await emit_event(
        db, source='atlas.mercury', kind='mercury_control_executed', severity='info',
        payload={'action': action, 'outcome': outcome, 'rc': rc, 'stderr': err[:500] if err else ''},
    )


async def mercury_start(db: Database) -> None:
    """Phase 7.2 (Day 78 mid-day): real start with 15s cancel-window via _mercury_control."""
    await _mercury_control(db, 'start')


async def mercury_stop(db: Database) -> None:
    """Phase 7.2 (Day 78 mid-day): real stop with 15s cancel-window via _mercury_control."""
    await _mercury_control(db, 'stop')
```

**Module docstring update:** at line 10, replace `mercury_start / mercury_stop: STUB at v0.1 (Paco-preferred option a); TODO Phase 7.` with `mercury_start / mercury_stop: Phase 7 (Day 78 mid-day) -- 15s Tier 2 cancel-window via communication.emit_event; ssh+sudo systemctl exec on CK after window elapses without cancel claim.`

**Sudo capability check:** `sudo systemctl <action> mercury-scanner.service` requires NOPASSWD on CK for jes user. Per reachability cycle Step 3.5: jes has NOPASSWD on CK (sudoers.d/99-jes-nopasswd). Verified live. PD verifies once with `ssh ck sudo -n true && echo OK` at Step 0 (pre-execution).

### 2.4 Step 1.5 -- CEO interactive .env population

After PD finishes Phase 7.1 + 7.2 code authoring + smoke tests but BEFORE Phase 7 close, CEO runs (one-time, manual; NOT in PD scope):

```bash
ssh ciscokid 'grep -E "^(TWILIO_ACCOUNT_SID|TWILIO_AUTH_TOKEN|TWILIO_FROM_NUMBER|TWILIO_TO_NUMBER)=" /home/jes/control-plane/.env' \
  | ssh beast 'cat >> /home/jes/atlas/.env'
ssh beast "sed -i 's/^TWILIO_TO_NUMBER=/SLOAN_PHONE_NUMBER=/' /home/jes/atlas/.env && cat /home/jes/atlas/.env | grep -E '^[A-Z]+=' | sed 's/=.*/=<set>/'"
```

Expected output: 4 lines, vars are TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, SLOAN_PHONE_NUMBER.

PD smoke-tests in mock mode (TWILIO_ENABLED unset). Real-Twilio test deferred to CEO discretion post-cycle (see Step 4 below).

### 2.5 Tests

**`test_communication.py` (Phase 7.1 unit tests):**

- `test_emit_event_severity_validation`: emit_event with severity='bogus' raises ValueError.
- `test_emit_event_inserts_atlas_events`: monkey-patch Database; verify INSERT params (source, kind, payload-with-severity-and-tier).
- `test_emit_event_tier_mapping`: severity='info'->tier=1; 'warn'->tier=2; 'critical'->tier=3 in payload.
- `test_emit_event_critical_calls_dispatch`: monkey-patch dispatch_telegram; verify called once on critical, NOT called on info|warn.
- `test_dispatch_telegram_mock_mode`: TWILIO_ENABLED=false; assert log.info('telegram_mock', ...) call; no httpx.
- `test_dispatch_telegram_missing_env`: TWILIO_ENABLED=true but TWILIO_ACCOUNT_SID unset; assert log.warning + no httpx.
- `test_dispatch_telegram_real_post`: TWILIO_ENABLED=true + all env set; monkey-patch httpx.AsyncClient; assert POST to correct URL with Basic auth header.

**`test_mercury_phase7.py` (Phase 7.2 integration tests):**

- `test_mercury_start_no_cancel_invokes_systemctl`: monkey-patch `_ssh_run` (return rc=0) and `emit_event` (capture calls); call `mercury_start(db)` with no concurrent cancel claim; verify 2 emit_event calls (initiated warn + executed info) and 1 _ssh_run call with cmd containing 'systemctl start'. NOTE: this test MUST monkey-patch `_CANCEL_WINDOW_S=2` (not 15) for test runtime sanity; document override in test fixture.
- `test_mercury_start_with_cancel_aborts`: insert atlas.tasks row with `payload.kind='mercury_control_cancel'` AT t+1s into the cancel-window; verify mercury_start returns WITHOUT calling _ssh_run; verify cancelled emit_event logged; verify cancel task status updated to 'done'.
- `test_mercury_stop_outcome_systemctl_error`: monkey-patch _ssh_run -> rc=1, stderr='Unit not found'; verify executed emit_event has outcome='systemctl_error' in payload.

### 2.6 Smoke test (manual at Phase 7 close)

```bash
cd /home/jes/atlas && python -m pytest tests/test_communication.py tests/test_mercury_phase7.py -v 2>&1 | tail -30
```

Expected: all tests pass; output captured in PD review.

---

## 3. Acceptance criteria (Phase 7)

From spec line 446 + amendments:

1. emit_event writes correctly for all 3 tiers (info/warn/critical -> Tier 1/2/3) -- verified via test_emit_event_tier_mapping.
2. atlas.events row appears with correct payload (severity + tier inside payload per correction #1) -- verified via test_emit_event_inserts_atlas_events + manual `SELECT * FROM atlas.events ORDER BY ts DESC LIMIT 5` in smoke.
3. dispatch_telegram works in mock mode (logs intended message; no real SMS) -- verified via test_dispatch_telegram_mock_mode.
4. dispatch_telegram works in real mode IF env populated (deferred -- mock mode is the in-cycle test; real-Twilio verification is CEO discretion post-cycle).
5. mercury_start/mercury_stop cancel-window wired (15s pre-execute + task-status recheck) -- verified via 3 test_mercury_phase7 tests.
6. Standing gates 6/6 preserved (B2b anchor, Garage anchor, atlas-mcp.service, atlas-agent.service inactive, mercury-scanner.service active, mcp_server.py untouched).
7. Pre-commit BOTH broad-grep AND tightened-regex secrets-scan clean (P6 #34 standing practice). PD: scan diff-only at staging, NOT full file (avoids hitting Phase 6's redacted-already-handled DB_PASS context).

---

## 4. Procedure

**Step 0 -- Pre-flight (PD does this first; one tool call):**

```bash
cd /home/jes/atlas && git log --oneline -1 && git status -s && \
echo '---ck-sudo-check---' && ssh ciscokid 'sudo -n true && echo SUDO_OK' && \
echo '---atlas-events-schema---' && docker exec control-postgres-beast psql -U admin -d controlplane -c '\d atlas.events' | head -10 && \
echo '---atlas-tasks-schema---' && docker exec control-postgres-beast psql -U admin -d controlplane -c '\d atlas.tasks' | head -10
```

Expected: HEAD `147f13c`; clean tree; SUDO_OK; events schema (id/ts/source/kind/payload no severity); tasks schema (status check pending|running|done|failed no kind).

If any check diverges -> STOP + paco_request.

**Step 1 -- Author `src/atlas/agent/communication.py`** per section 2.2; py_compile + import check.

**Step 2 -- Author `tests/test_communication.py`** per section 2.5; run tests; capture output.

**Step 3 -- Modify `src/atlas/agent/domains/mercury.py`** per section 2.3; replace stubs at lines 340-362; py_compile + import check.

**Step 4 -- Author `tests/test_mercury_phase7.py`** per section 2.5; run tests; capture output.

**Step 5 -- Cross-cutting smoke**: full `pytest -v` against the 2 new test files; capture output.

**Step 6 -- Pre-commit secrets scan (BOTH broad + tightened, diff-only):**

```bash
cd /home/jes/atlas && git diff | grep -E '^[+-]' | grep -v '^---' | grep -v '^+++' | grep -niE 'key|token|secret|password|api|auth' | head -30
cd /home/jes/atlas && git diff | grep -E '^[+-]' | grep -v '^---' | grep -v '^+++' | grep -niE 'api[_-]?key|secret[_-]?key|access[_-]?token|bearer\s+|authorization:'
```

If either flags a real value (not policy reference) -> redact + re-scan -> proceed only when both clean.

**Step 7 -- Standing gates POST-check** (4 + mercury liveness):

```bash
docker inspect control-postgres-beast --format '{{.State.StartedAt}}' && \
docker inspect control-garage-beast --format '{{.State.StartedAt}}' && \
systemctl show -p MainPID -p ActiveState atlas-mcp.service && \
systemctl show -p MainPID -p ActiveState atlas-agent.service && \
ssh ciscokid 'systemctl is-active mercury-scanner.service'
```

All must equal pre-flight values + mercury active.

**Step 8 -- Commit + push:**

```bash
git add src/atlas/agent/communication.py tests/test_communication.py src/atlas/agent/domains/mercury.py tests/test_mercury_phase7.py
git commit -m 'feat: Cycle Atlas v0.1 Phase 7 communication helper + mercury cancel-window

Phase 7.1: communication.py emit_event + dispatch_telegram with tier auto-mapping;
severity goes in payload.severity (atlas.events has no severity column per Phase 7
directive correction #1); critical-tier triggers Twilio dispatch (mock-mode default).

Phase 7.2: mercury_start/mercury_stop replaced v0.1 stubs with 15s Tier 2 cancel-window
via _mercury_control helper; cancel detection via payload->>kind=mercury_control_cancel
claim on atlas.tasks (no top-level kind column per directive correction #2); ssh+sudo
systemctl on CK after window elapses without cancel.

5 spec corrections handled per paco_directive_atlas_v0_1_phase7.md section 0.

Tests: test_communication.py (7 cases) + test_mercury_phase7.py (3 cases) all pass.'
git push
```

**Step 9 -- Write `docs/paco_review_atlas_v0_1_phase7.md`** following Phase 6 review template:
- Section 0: 17 verified-live items (PRE) + standing gates POST + tests output
- Section 1: TL;DR
- Section 2: implementation per file
- Section 3: acceptance criteria pass/fail
- Section 4: known issues / P5 candidates
- Section 5: P6 lessons (banked or new)
- Section 6: handoff line for handoff_pd_to_paco.md

**Step 10 -- Notification line in `docs/handoff_pd_to_paco.md`:**

> Paco, PD finished Atlas v0.1 Phase 7. communication.py + mercury cancel-window wired; 5 spec corrections handled per directive section 0; standing gates 6/6 preserved; tests 10/10 pass. Check handoff.

## 5. Discipline reminders

- One step at a time. Do NOT chain Steps 1->8 in a single PD action; stop at each step's natural boundary; verify before next.
- TWILIO creds: NEVER paste literal values into commit messages, test files, or paco_review. Reference env var names only.
- atlas.events INSERT pattern is precedent-matched (mcp_client/client.py + embeddings/client.py); do not invent a new pattern.
- Cancel-window query MUST use `payload->>'kind'` not a top-level kind column (correction #2).
- atlas-agent.service stays disabled+inactive (Phase 1 acceptance preserved; Phase 9 is when it enables).
- mercury-scanner.service stays untouched outside the deliberate Phase 7.2 invocation tests (which use monkey-patched _ssh_run, NOT real systemctl calls).
- If real-Twilio test needed in-cycle: CEO ratifies via chat; PD enables TWILIO_ENABLED=true momentarily, sends one test SMS, captures Twilio API response, disables again. Default path is mock-mode-only.
- Cycle Atlas commits to santigrey/atlas repo (NOT control-plane); paco_review/handoff land in santigrey/control-plane (canon discipline).

## 6. Trigger from CEO to PD (Cowork prompt)

When CEO ready to dispatch, paste this into a fresh Cowork session:

```
You are PD (Cowork) for Santigrey Enterprises. Paco (COO) has dispatched Atlas v0.1 Phase 7.

Repos:
- santigrey/atlas at /home/jes/atlas on Beast (HEAD 147f13c). All Phase 7 code commits here.
- santigrey/control-plane at /home/jes/control-plane on CK (HEAD 5fe7d81). Read directive + write paco_review here.

Read in order:
1. /home/jes/control-plane/docs/paco_directive_atlas_v0_1_phase7.md (your authority)
2. /home/jes/control-plane/docs/feedback_paco_pre_directive_verification.md (P6 standing rules)
3. /home/jes/control-plane/docs/paco_review_atlas_v0_1_phase6.md (predecessor; reuse pattern catalog)

Directive supersedes spec for the 5 corrections in section 0. Do NOT reference
tasks/atlas_v0_1_agent_loop.md for Phase 7 details; reference the directive.

Execute Steps 0 -> 9 per directive section 4. One step at a time; verify before next.

At Step 9 (paco_review), commit + push the review to control-plane and add the
handoff notification line per directive section 4 Step 10.

If any step fails acceptance: STOP, write paco_request_atlas_v0_1_phase7_<topic>.md
in control-plane/docs/, do not proceed.

Begin with Step 0 pre-flight.
```

## 7. Note on Step 1.5 (CEO interactive .env)

Step 1.5 is OUT OF PD SCOPE. PD smoke-tests in mock mode (TWILIO_ENABLED unset; emit_event critical-tier triggers `dispatch_telegram` which logs `telegram_mock` and returns -- this is the in-cycle test). After Phase 7 PD review lands and Paco close-confirms, CEO can optionally:

1. Run the .env population command from section 2.4.
2. `TWILIO_ENABLED=true` momentarily.
3. Trigger one test event via `python -c 'import asyncio; from atlas.agent.communication import dispatch_telegram; asyncio.run(dispatch_telegram("Phase 7 real-Twilio test"))'`.
4. Verify SMS arrival on Sloan phone.
5. Restore TWILIO_ENABLED to default (unset/false).

Real-Twilio verification is independent of Phase 7 acceptance; mock-mode passing is the formal acceptance gate.

-- Paco
