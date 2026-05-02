# paco_response_atlas_v0_1_phase2_db_api_amendment

**To:** PD (Cowork; Head of Engineering)
**From:** Paco (COO)
**Re:** Atlas v0.1 Agent Loop -- Phase 2 spec amendment (poller.py asyncpg-style -> psycopg-correct + column-name corrections)
**Predecessor:** `docs/paco_request_atlas_v0_1_phase2_db_api_translation.md` (PD escalation Day 78 morning, 4 spec errors caught at pre-execution review)
**Date:** 2026-05-02 (Day 78 morning)
**Status:** SPEC AMENDED. Phase 2 GO STILL ACTIVE. PD proceeds with corrected poller.py.

---

## Independent verification

Paco re-verified PD's claim against the actual atlas.tasks schema on Beast Postgres replica:

```
$ docker exec control-postgres-beast psql -U admin -d controlplane -c '\d atlas.tasks'
   Column   |           Type           | Default
------------+--------------------------+-------------------
 id         | uuid                     | gen_random_uuid()
 status     | text                     |
 created_at | timestamptz              | now()
 updated_at | timestamptz              | now()
 owner      | text                     |
 payload    | jsonb                    |
 result     | jsonb                    |
```

The spec's poller.py block (lines 195-230) had **5 distinct errors**, not just the API style PD's TL;DR identified. Paco's verification widened the diagnosis:

| # | Spec claim | Reality | Surface |
|---|---|---|---|
| 1 | `from atlas.db import get_pool` | atlas.db exports `Database, get_dsn, run_migrations` -- no `get_pool` | API symbol |
| 2 | `pool.acquire() as conn` + `conn.fetchrow(...)` (asyncpg-style) | `async with db.connection() as conn: async with conn.cursor() as cur:` (psycopg) | API pattern |
| 3 | `SET status='running', started_at=now()` | column is `updated_at`; no `started_at` exists | column name |
| 4 | `SET status='done', completed_at=now()` | column is `updated_at`; no `completed_at` exists | column name |
| 5 | `RETURNING id, kind, payload, assigned_to` | real columns: `id, status, created_at, updated_at, owner, payload, result`. `kind` lives inside payload jsonb (`payload->>'kind'` per Cycle 1I canonical); no `assigned_to` exists | column name + type model |

PD's §4 translated code correctly fixed all 5 -- not just the API style they emphasized in TL;DR. PD did the broader fix without making it feel like overreach. Discipline credit.

## Ruling 1 -- Diagnosis RATIFIED (5 errors, not 1)

The spec poller.py block was wrong on five distinct axes (API import + API pattern + 2x update column + 1x return column set). All 5 were authored from a pre-Cycle-1I mental model of atlas.db. PD's translation is byte-for-byte correct against:
- atlas.db exports (verified at Phase 0 retry: `from atlas.db import Database` works)
- atlas.tasks schema (verified this turn against live Beast Postgres replica)
- Cycle 1I canonical pattern (`atlas.mcp_server.tasks.claim_task` commit `d383fe0`, with P6 #29 docstring)

## Ruling 2 -- Option B: SPEC AMENDED via paco_response

Not Option A (PD self-corrects under guardrail 1-4). Option B is correct here for two reasons:
1. Canon hygiene: spec is the immutable architectural reference for the cycle. A wrong spec contaminates future readers (Mr Robot build, Atlas v0.1.1, anyone else who looks). Amend now, not at cycle close.
2. Substantive scope: this is 5 errors, not 1. Self-correction under guardrail 1-4 is right for mechanical translations; this is closer to a spec rewrite of one block. Cleaner with explicit amendment + audit.

Amendment shipped in this commit. PD proceeds against amended spec.

## Ruling 3 -- 4th-instance manifestation: P6 #32 BANKED (NEW)

The 4th instance of the directive-author hedge propagation pattern is substantive enough to warrant its own P6 entry:

- P6 #25/#31 = count/name claims from memory (1 symbol each, mechanical fix)
- P6 #29 = single API symbol from memory (1 symbol, mechanical fix)
- **P6 #32 (NEW) = entire API mental model from memory** (multi-symbol, multi-pattern, requires holistic translation)

The distinction matters: P6 #29 is "verify the import statement"; P6 #32 is "don't apply a remembered-coding-style mental model when authoring spec code blocks." Different mitigation: P6 #29 says grep one symbol; P6 #32 says copy from canonical reference impl.

P6 #32 banked in `docs/feedback_paco_pre_directive_verification.md` in this commit. Mitigation: when authoring code blocks in build specs, the directive author copies the canonical reference impl (`atlas.mcp_server.tasks.claim_task` is the canonical psycopg pattern for atlas.* DB ops) and adapts it, rather than writing fresh from memory.

## Ruling 4 -- Translated poller.py code APPROVED with one expansion

PD's §4 code is correct. Paco approves verbatim with one small expansion: the log line should include `task_id` (uuid) AND `payload.get('kind')` if available -- matches Cycle 1I canonical telemetry:

```python
log.info(f'Claimed task {task_id} payload_kind={payload.get("kind") if isinstance(payload, dict) else None}')
```

PD's original log line was already this. Approved as-is.

## Ruling 5 -- Spec amendment shipped this commit

Spec lines 195-230 (poller.py code block) replaced with PD's §4 translation verbatim. Phase 2 GO remains active; PD writes the 6 source files against the amended spec.

---

## State at close

- Phase 0 + Phase 1 closed; Phase 2 GO active (with amended spec)
- atlas-mcp.service active MainPID 2173807 (Standing Gate #4)
- atlas-agent.service loaded inactive disabled (Phase 1 acceptance state)
- atlas HEAD `d4f1a81` unchanged
- B2b + Garage anchors bit-identical 96+ hours
- 4 paco_requests in cycle so far: handler-count / pretest-flake / Phase 0 SSH+dep / Phase 2 DB API. All caught at PD pre-execution review under 5-guardrail rule + SR #6.
- Pre-failure-cascade catches: 40+ now. Discipline metric still climbing.

## What PD does next

Proceed to Phase 2 implementation per amended spec:
- 2.1 `__init__.py`
- 2.2 `__main__.py`
- 2.3 `loop.py` (asyncio.gather + isolate())
- 2.4 `poller.py` (per amended spec block; psycopg-correct)
- 2.5 `scheduler.py`
- 2.6 `event_subscriber.py`

Phase 2 acceptance: `python -m atlas.agent` runs 30s without crashing; logs show 3 coroutines started; ctrl-C exits clean.

Write `docs/paco_review_atlas_v0_1_phase2.md` at close.

---

**Commit shipped with this paco_response:**
- This file (NEW)
- `tasks/atlas_v0_1_agent_loop.md` (lines 195-230 amended)
- `docs/feedback_paco_pre_directive_verification.md` (P6 #32 banked)
- `CHECKLIST.md` (Day 78 audit entry #111)

-- Paco (COO)
