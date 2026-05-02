# paco_request_atlas_v0_1_phase2_db_api_translation

**Spec:** Atlas v0.1 Operations Agent Loop Build Spec (`tasks/atlas_v0_1_agent_loop.md`, lines 139-271 = Phase 2; commit `8195987`)
**Step:** Phase 2 PRE-execution review BEFORE writing any agent loop skeleton code
**Status:** ESCALATION -- Phase 2 spec poller.py (line 199-237 region) uses **asyncpg-style API** but atlas package uses **psycopg-style API** per banked P6 #29 + Cycle 1I canonical reference impl. Filing per directive standing rules + defensive escalation discipline before code lands. **4th instance** of P6 #25/#31 directive-author hedge propagation; this instance directly contradicts already-banked P6 #29.
**Predecessor:** `docs/paco_response_atlas_v0_1_phase1_confirm_phase2_go.md` (Phase 2 GO authorization, HEAD `a256f05`); Cycle 1I close commit `d383fe0` (canonical psycopg reference impl in `atlas.mcp_server.tasks.claim_task`)
**Author:** PD (Cortez session, host-targeted verification per Day 78 self-correction note)
**Date:** 2026-05-02 UTC (Day 78 morning)
**Target host:** Beast (atlas package authoring host)

---

## TL;DR

Phase 2 spec section 2.4 (`poller.py` skeleton, build spec lines 199-237) uses asyncpg-style API:
```python
from atlas.db import get_pool
pool = await get_pool()
async with pool.acquire() as conn:
    row = await conn.fetchrow(""" UPDATE atlas.tasks ... RETURNING ... """)
    await conn.execute("UPDATE atlas.tasks ... WHERE id=$1", row['id'])
```

**Reality:** atlas.db has no `get_pool` symbol; canonical API is `Database()` + `db.connection()` async context manager + cursor-based `cur.execute(%s)` + explicit `await conn.commit()`. Verified by grep: zero occurrences of `get_pool` or `pool.acquire` anywhere in `/home/jes/atlas/src/`.

**P6 #29 already banked this discipline** (per docstring of `atlas.mcp_server.tasks` at /home/jes/atlas/src/atlas/mcp_server/tasks.py): *"DB API: uses atlas.db.Database psycopg-style API verified live per P6 #29: async with db.connection() as conn: async with conn.cursor() as cur: await cur.execute(sql, args) with %s placeholders, await cur.fetchall() / await cur.fetchone() returns tuples"*. The Phase 2 spec author wrote against the PRE-P6-#29 mental model.

**Pattern recurrence:** This is the 4th instance this cycle-family of directive-author hedge propagation:
1. Cycle 1F Phase 3: handler count 14→13 (commit `77759f8`)
2. Cycle 1F Phase 3 Step 7: prior-test count 16→15 (commit `eadc2e7`)
3. Atlas v0.1 Phase 0: dep name asyncpg→psycopg (commit `8195987`, P6 #31 banked)
4. **Atlas v0.1 Phase 2 (this paco_request): DB API entire pattern asyncpg→psycopg**

This 4th instance is more substantive than the prior 3 (count/name) -- it's a complete API translation with multiple distinct method/symbol/syntax differences. PD halts before writing code per defensive escalation.

4 of 6 Phase 2 files are clean as-spec'd (`__init__.py`, `__main__.py`, `loop.py`, `scheduler.py`, `event_subscriber.py`). Only `poller.py` needs translation.

B2b + Garage anchors bit-identical: `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z` (96+ hours holding through Phase 0 + Phase 1).

---

## 1. Spec vs reality table (poller.py only)

| Aspect | Spec (asyncpg-style) | Reality (psycopg per P6 #29) | Source of truth |
|---|---|---|---|
| Pool import | `from atlas.db import get_pool` | `from atlas.db import Database` | `/home/jes/atlas/src/atlas/db/__init__.py` exports only `Database, get_dsn, run_migrations` |
| Pool acquisition | `pool = await get_pool()` | `db = Database()` (async-open lazy via `db.connection()`) | `atlas.db.pool.Database` per Phase 0 verified-live |
| Conn acquisition | `async with pool.acquire() as conn:` | `async with db.connection() as conn:` | `atlas.db.pool.Database.connection()` `@asynccontextmanager` |
| Query execute | `row = await conn.fetchrow(sql)` | `async with conn.cursor() as cur: await cur.execute(sql, args); row = await cur.fetchone()` | `atlas.mcp_server.tasks.claim_task` Cycle 1I canonical (lines 152-156) |
| Param placeholders | `$1`, `$2`, ... (asyncpg) | `%s` (psycopg) | psycopg native |
| Write commit | implicit (asyncpg autocommits per call) | `await conn.commit()` explicit | `atlas.mcp_server.tasks.claim_task` line 157 |
| Row format | dict (asyncpg Record acts dict-like) | tuple (psycopg default; would need `dict_row` factory or `_row_to_dict()` helper) | atlas.mcp_server.tasks `_row_to_dict()` pattern |

## 2. Canonical psycopg pattern from Cycle 1I (verbatim quote)

From `/home/jes/atlas/src/atlas/mcp_server/tasks.py` lines 122-159 (Cycle 1I close, commit `d383fe0`):

```python
async def claim_task(
    params: TasksClaimInput, db: Database, caller_endpoint: str
) -> Optional[dict[str, Any]]:
    """Atomic pending->running with FOR UPDATE SKIP LOCKED race-safety.

    Returns claimed row OR None (queue empty matching filter).
    Owner is set to caller_endpoint (X-Real-IP from nginx).
    """
    if params.payload_kind is not None:
        sql = (
            "UPDATE atlas.tasks SET status='running', owner=%s, updated_at=now() "
            "WHERE id = ("
            "  SELECT id FROM atlas.tasks "
            "  WHERE status='pending' AND payload->>'kind' = %s "
            "  ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED"
            ") "
            f"RETURNING {_COLS}"
        )
        sql_args: tuple = (caller_endpoint, params.payload_kind)
    else:
        sql = (...)
        sql_args = (caller_endpoint,)
    async with db.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, sql_args)
            row = await cur.fetchone()
            await conn.commit()
    return _row_to_dict(row) if row is not None else None
```

This is exactly the pattern Phase 2 poller.py should follow (with adjusted SQL for the standalone agent context where there is no caller_endpoint).

## 3. P6 #29 docstring (verbatim from atlas.mcp_server.tasks)

From `atlas.mcp_server.tasks` module docstring (lines 21-25 of /home/jes/atlas/src/atlas/mcp_server/tasks.py):

> DB API: uses atlas.db.Database psycopg-style API verified live per P6 #29:
> - async with db.connection() as conn: async with conn.cursor() as cur:
> - await cur.execute(sql, args) with %s placeholders
> - await cur.fetchall() / await cur.fetchone() returns tuples (no row_factory set)

The Phase 2 spec poller.py contradicts this banked discipline directly.

## 4. Proposed translation (PD's psycopg-correct poller.py)

Minimal-diff equivalent of spec section 2.4:

```python
"""Polls atlas.tasks for pending rows; claims via SKIP LOCKED; executes; writes results.

Per P6 #29 + Cycle 1I canonical pattern (atlas.mcp_server.tasks.claim_task).
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

Key changes from spec:
- `from atlas.db import Database` (was `get_pool`)
- `db = Database()` instance (was `pool = await get_pool()`)
- `async with db.connection() as conn: async with conn.cursor() as cur:` cursor pattern (was `async with pool.acquire() as conn:`)
- `await cur.execute(sql)` + `await cur.fetchone()` (was `await conn.fetchrow(sql)`)
- `%s` placeholders (was `$1`)
- Explicit `await conn.commit()` after writes
- Tuple unpacking `task_id, payload = row[0], row[1]` (was dict subscript `row['id']`)

Functional equivalence: same SKIP LOCKED claim semantics; same 5-second sleep on empty; same no-op completion. Spec PURPOSE preserved verbatim; only the API layer translated.

## 5. Other Phase 2 files (clean as-spec'd, no changes needed)

- 2.1 `__init__.py` -- empty marker, no imports ✓
- 2.2 `__main__.py` -- imports `from atlas.agent.loop import run`; uses `asyncio.run(run())`; standard logging setup. No atlas.db direct usage ✓
- 2.3 `loop.py` -- imports `from atlas.agent.poller import task_poller` (etc.); `asyncio.gather` with `isolate()` wrapper. No atlas.db direct usage ✓
- 2.5 `scheduler.py` -- only `datetime` + `asyncio.sleep(60)`. No atlas.db direct usage ✓
- 2.6 `event_subscriber.py` -- only `asyncio.sleep(300)` + `log.debug`. No atlas.db direct usage ✓

Only 2.4 `poller.py` needs translation.

## 6. Resolution options

### Option A -- PD self-corrects under guardrail 1-4 (RECOMMENDED)

Per 5-guardrail rule § 1-4 (intent unambiguous; functional equivalence; no scope expansion; documentation):
- Intent: spec clearly intends `"claim a pending task atomically via FOR UPDATE SKIP LOCKED, log, mark done"` -- unambiguous
- Functional equivalence: same SQL (modulo placeholder syntax), same SKIP LOCKED semantics, same control flow
- No scope expansion: poller.py only; no other files affected; no new dependencies; no auth/security boundary touched
- Documentation: this paco_request + paco_review §3 (Server-side patch summary equivalent)

Guardrail 5 (auth/security) NOT triggered: no auth scoping, password file, ACL, UFW, sudoers, container privilege, or secret operation involved. SKIP LOCKED is a query-correctness concern, not a security boundary.

PD self-corrects + documents in paco_review.

### Option B -- Paco amends spec via paco_response with translated code

Paco issues `paco_response_atlas_v0_1_phase2_db_api_amendment.md` with the corrected poller.py code. Slower but cleanest audit trail. PD then implements verbatim.

### Option C -- PD files paco_request EVERY occurrence + amends spec at end of cycle

Defensive but slow. Not recommended for this case since translation is mechanical and pattern is already named (P6 #29 + #31).

## 7. PD recommendation

**Option A** -- PD self-corrects under guardrail 1-4. Documents translation in paco_review §3 (NEW section: `"Spec amendment: poller.py asyncpg→psycopg per P6 #29"`). Bank as 4th-instance datapoint for P6 #31 (no new P6 entry needed; pattern already named).

Fallback: Option B if Paco prefers spec-amendment-via-response audit trail.

## 8. Asks of Paco

1. **Ratify** spec→reality discrepancy diagnosis (poller.py asyncpg-style vs atlas psycopg-style API).
2. **Approve** Option A (PD self-corrects under guardrail 1-4 with paco_review §3 documentation) OR Option B (Paco amends spec via paco_response).
3. **Acknowledge** 4th-instance manifestation of P6 #25/#31 family. Decision on whether to bank as new P6 #32 (recurring at substantive level beyond count/name) OR cover via existing P6 #31 + this paco_request as audit datapoint.
4. **Ratify** Option A's psycopg-correct poller.py code from §4 (or amend before PD writes).
5. **Spec amendment line 199-237 plan** (whether amendment ships in this paco_response or in cycle close-out fold).

## 9. State at this pause

- Phases 0 + 1 closed (verified-live confirmed)
- Phase 2 NOT started (zero code written)
- atlas-mcp.service: active, MainPID 2173807, ~6.5h uptime (Standing Gate #4 preserved)
- atlas-agent.service: loaded inactive disabled (Phase 1 acceptance state preserved)
- atlas HEAD: `d4f1a81` unchanged
- HEAD on control-plane-lab: `a256f05` (Phase 1 close-confirm + Phase 2 GO)
- B2b + Garage anchors: bit-identical, holding 96+ hours
- handoff_pd_to_paco.md notification line for THIS paco_request to follow per P6 #26

---

**File:** `docs/paco_request_atlas_v0_1_phase2_db_api_translation.md` (untracked, transient until close-out per correspondence triad standing rule)

-- PD
