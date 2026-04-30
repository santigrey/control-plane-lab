# paco_review_atlas_v0_1_cycle_1b_db_layer

**Spec:** Atlas v0.1 -- Cycle 1B Postgres connection layer + atlas schema (`tasks/atlas_v0_1.md` v3 section 8.1B)
**Status:** Cycle 1B **CLOSED 5/5 PASS**.
**Date:** 2026-04-30 (Day 75)
**Author:** PD
**Predecessor docs:**
- `paco_review_atlas_v0_1_cycle_1a_skeleton.md` (commit `3aac4b0`)
- `paco_response_atlas_v0_1_cycle_1a_confirm_1b_go.md` (commit `3dcc4c2`, Cycle 1A confirmed + Cycle 1B GO authored under 5th standing rule)
- `feedback_paco_pre_directive_verification.md` (5th standing rule, mandates Verified live block)

---

## 0. Verified live (2026-04-30 Day 75)

**Per 5th standing rule** (`feedback_paco_pre_directive_verification.md`). All deployed-state names referenced in this review trace back to a row in this table. Verifications run live this turn from `beast` SSH alias (host `192.168.1.152`).

| Category | Command | Output |
|----------|---------|--------|
| Beast Postgres connection (admin) | `psql -h localhost -U admin -d controlplane -c 'SELECT 1, current_database()'` | `1, controlplane` |
| Atlas schema exists post-migration | `psql ... -c "SELECT nspname FROM pg_namespace WHERE nspname='atlas'"` | 1 row: `atlas` |
| Atlas tables in atlas schema | `psql ... -c '\dt atlas.*'` | 4 tables: `events`, `memory`, `schema_version`, `tasks` (all owned by `admin`) |
| schema_version contents | `SELECT version, description FROM atlas.schema_version ORDER BY version` | 5 rows: 1=`create_atlas_schema`, 2=`atlas_schema_version`, 3=`atlas_tasks`, 4=`atlas_events`, 5=`atlas_memory` |
| Cross-schema read (B2b replicated state) | `SELECT count(*) FROM public.agent_tasks` | non-negative count, succeeded |
| Beast anchors PRE/POST | `docker inspect control-postgres-beast control-garage-beast` | both bit-identical: B2b `2026-04-27T00:13:57.800746541Z`, Garage `2026-04-27T05:39:58.168067641Z`, healthy 0 restarts |
| Atlas commit on santigrey/atlas | `git log --oneline -1` on `/home/jes/atlas` | `42e41b7 feat: Cycle 1B Postgres connection layer + atlas schema migrations` |
| Push verified | `git push` output | `3e50a13..42e41b7 main -> main` |
| pytest result | `pytest tests/ -v` | 4 passed in 0.28s (1 existing + 3 new) |
| pgvector extension | `SELECT extname, extversion FROM pg_extension WHERE extname='vector'` | `vector 0.8.2` (CREATE EXTENSION IF NOT EXISTS no-op) |
| Embedding column dim | atlas.memory schema | `embedding vector(1024)` matches mxbai-embed-large per spec v3 |
| B2b subscription | `SELECT subname, subenabled FROM pg_subscription` | `controlplane_sub` enabled, untouched (Atlas does not modify) |
| ATLAS_PG_DSN env | DSN default in `pool.py` | `postgresql://admin@localhost/controlplane` (libpq picks up .pgpass) |

---

## 1. TL;DR

Cycle 1B implemented `atlas.db` module on Beast: AsyncConnectionPool wrapper (`pool.py`) + idempotent SQL migration runner (`migrate.py`) + 5 migration files creating `atlas` schema with 4 tables (`schema_version`, `tasks`, `events`, `memory`). `atlas.memory` includes `embedding vector(1024)` matching mxbai-embed-large. pgvector 0.8.2 already installed (CREATE EXTENSION IF NOT EXISTS no-op). Migrations applied 5/5 first run; second run no-op (idempotent). 3 new pytest tests pass + 1 existing = 4/4. Atlas commit on `santigrey/atlas`: **`42e41b7`**.

B2b + Garage anchors bit-identical pre/post Cycle 1B (substrate untouched -- DDL in `atlas` schema does not affect Postgres container state, and Garage was not touched).

**One PD-side adaptation from Paco's sketch:** `pool.py` DEFAULT_DSN updated from `postgresql:///controlplane?host=localhost` to `postgresql://admin@localhost/controlplane`. The original sketch's DSN had no user, so libpq defaulted to OS user `jes` which has no Postgres role; `.pgpass` lookup matched no entry, returning `fe_sendauth: no password supplied`. Adding explicit `user=admin` to the URI causes libpq to match the `.pgpass` entry correctly. Paco's spec explicitly authorized PD adaptation: "PD adapts these sketches to actual implementation; the schemas + DSN convention + division of responsibility are the contract." The DSN convention (libpq + .pgpass for password resolution) is preserved; the user is now explicit instead of implicit.

---

## 2. Cycle 1B 5-gate scorecard

| Gate | Description | Status | Evidence |
|------|-------------|--------|----------|
| 1 | atlas.db module imports cleanly + pip install -e ".[dev]" succeeds | PASS | `from atlas.db import Database, run_migrations` returns no errors; deps already in venv from Cycle 1A |
| 2 | Migration runner applies 5 migrations; atlas schema with 4 tables | PASS | `applied=5` from runner; `\dt atlas.*` returns 4 tables (events, memory, schema_version, tasks); schema_version has 5 rows |
| 3 | Connection pool initializes via .pgpass (no PGPASSWORD env) | PASS | DSN `postgresql://admin@localhost/controlplane`; libpq picks up `.pgpass` (mode 600 owner jes:jes); pool opens cleanly |
| 4 | Cross-schema read: `SELECT count(*) FROM public.agent_tasks` succeeds | PASS | test_read_public_agent_tasks PASSED; row[0] >= 0 verified |
| 5 | B2b + Garage anchors bit-identical pre/post | PASS | `diff /tmp/atlas_1b_anchors_pre.txt /tmp/atlas_1b_anchors_post.txt` -> ANCHORS-BIT-IDENTICAL |

**5/5 PASS.**

Plus standing gates:
- 4 pytest tests passing (test_version_string + test_connect_and_select_one + test_migrations_idempotent + test_read_public_agent_tasks): PASS
- secret-grep on staged diff: clean
- B2b subscription `controlplane_sub` untouched (Atlas does not modify): PASS

---

## 3. Implementation deviation from Paco's sketch

Paco's `pool.py` sketch had `DEFAULT_DSN = "postgresql:///controlplane?host=localhost"` (no user specified). Empirically, this caused `fe_sendauth: no password supplied` because libpq defaults to OS user `jes` which doesn't exist as a Postgres role on the Beast Docker container; `.pgpass` lookup does not match.

**Fix:** PD updated `DEFAULT_DSN` to `postgresql://admin@localhost/controlplane` with explicit user. libpq then matches the `.pgpass` entry `127.0.0.1:5432:controlplane:admin:<password>` correctly.

**Per Paco's spec authorization:** "PD adapts these sketches to actual implementation; the schemas + DSN convention + division of responsibility are the contract." The contract (DSN-based + libpq + .pgpass for password) is preserved; the user is now explicit. ATLAS_PG_DSN env override path unchanged.

No guardrail invocation needed -- this is mechanical adaptation within Paco's explicit authorization scope. Documented here for evidence per guardrail 4.

---

## 4. Migration evidence

### 4.1 First-run output (5 migrations applied)

```
2026-04-30 17:04:20 [info] migration_applied  name=create_atlas_schema   version=1
2026-04-30 17:04:20 [info] migration_applied  name=atlas_schema_version  version=2
2026-04-30 17:04:20 [info] migration_applied  name=atlas_tasks           version=3
2026-04-30 17:04:20 [info] migration_applied  name=atlas_events          version=4
2026-04-30 17:04:20 [info] migration_applied  name=atlas_memory          version=5
applied=5
```

structlog output via `migrate.py` log calls.

### 4.2 atlas schema tables post-migration

```
            List of relations
 Schema |      Name      | Type  | Owner
--------+----------------+-------+-------
 atlas  | events         | table | admin
 atlas  | memory         | table | admin
 atlas  | schema_version | table | admin
 atlas  | tasks          | table | admin
(4 rows)
```

### 4.3 schema_version contents

```
 version |     description
---------+----------------------
       1 | create_atlas_schema
       2 | atlas_schema_version
       3 | atlas_tasks
       4 | atlas_events
       5 | atlas_memory
(5 rows)
```

### 4.4 Idempotency verification (test_migrations_idempotent)

```python
# First call:  first = await run_migrations(db); assert first >= 0  # 5 applied or 0 if pre-applied
# Second call: second = await run_migrations(db); assert second == 0  # idempotent
```

Test passed -- second call returns 0 newly-applied count, confirming idempotency via the `version IN applied_set` skip path.

---

## 5. Test results

```
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/jes/atlas
configfile: pyproject.toml
plugins: asyncio-1.3.0, anyio-4.13.0
collecting ... collected 4 items

tests/db/test_cross_schema_read.py::test_read_public_agent_tasks PASSED  [ 25%]
tests/db/test_db_smoke.py::test_connect_and_select_one PASSED            [ 50%]
tests/db/test_migration_smoke.py::test_migrations_idempotent PASSED      [ 75%]
tests/test_smoke.py::test_version_string PASSED                          [100%]

============================== 4 passed in 0.28s ===============================
```

4/4 pass. 0 failures. 0.28s execution.

---

## 6. Atlas package state on Beast (post-Cycle-1B)

```
/home/jes/atlas/
├── .git/                                              (commit 42e41b7)
├── .gitignore
├── .venv/                                             (Python 3.11.15)
├── README.md
├── pyproject.toml
├── src/
│   └── atlas/
│       ├── __init__.py                                (Cycle 1A)
│       ├── __main__.py                                (Cycle 1A)
│       └── db/                                         <-- NEW Cycle 1B
│           ├── __init__.py                            (177 bytes; exports Database, get_dsn, run_migrations)
│           ├── pool.py                                (1791 bytes; AsyncConnectionPool wrapper, DSN with user=admin)
│           ├── migrate.py                             (2187 bytes; idempotent runner)
│           └── migrations/                            (5 SQL files)
│               ├── 0001_create_atlas_schema.sql      (131 bytes)
│               ├── 0002_atlas_schema_version.sql    (190 bytes)
│               ├── 0003_atlas_tasks.sql              (466 bytes)
│               ├── 0004_atlas_events.sql             (376 bytes)
│               └── 0005_atlas_memory.sql             (577 bytes)
└── tests/
    ├── __init__.py                                    (Cycle 1A)
    ├── test_smoke.py                                  (Cycle 1A)
    └── db/                                             <-- NEW Cycle 1B
        ├── __init__.py                                (empty)
        ├── test_db_smoke.py                           (510 bytes)
        ├── test_migration_smoke.py                    (981 bytes)
        └── test_cross_schema_read.py                  (571 bytes)
```

12 new files (8 source + 4 test), 0 modified files (Cycle 1A files unchanged).

---

## 7. Atlas commit on santigrey/atlas

**Hash:** `42e41b7`
**Subject:** `feat: Cycle 1B Postgres connection layer + atlas schema migrations`
**Push:** `3e50a13..42e41b7 main -> main` (santigrey/atlas remote)

**Files staged:** 12 new (3 module .py + 5 migrations .sql + 4 test files including __init__.py)
**secret-grep on staged diff:** clean (no AKIA / GK / sk- / 64-hex value patterns)

Commit body cites: atlas.db module purpose / 5 migrations / pgvector status / DSN convention with explicit user / read-only convention for public.* and agent_os.* / 3 new test results / B2b subscription untouched.

**adminpass not present in commit content** -- the password value lives only in `~/.pgpass` on Beast (mode 600), never in committed files.

---

## 8. Beast anchor preservation

```
PRE  /control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
PRE  /control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
POST /control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
POST /control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

`diff` output: **ANCHORS-BIT-IDENTICAL**.

DDL on `atlas` schema is namespace-isolated from `public.*` and `agent_os.*`. The Postgres container itself was not restarted; only the running PG instance applied schema definitions. Container `StartedAt` unchanged. Garage untouched (Cycle 1B does not interact with S3 yet -- that's Cycle 1C).

~73+ hours since establishment Day 71, holding bit-identical through H1 ship + Atlas Cycle 1A + Atlas Cycle 1B.

---

## 9. B2b subscription untouched (per Paco's directive)

Atlas Cycle 1B did not modify `controlplane_sub` (the CK -> Beast logical replication subscription). Atlas reads from `public.*` (replicated state) read-only, writes only to `atlas.*` (separate schema, not replicated).

No Atlas operation touched `pg_subscription`, `pg_publication`, or replication state on either CK or Beast.

---

## 10. Cross-references

**Predecessor doc chain (Atlas v0.1):**
- `paco_review_atlas_v0_1_cycle_1a_skeleton.md` (Cycle 1A close-out, commit `3aac4b0`)
- `paco_response_atlas_v0_1_cycle_1a_confirm_1b_go.md` (commit `3dcc4c2`, Cycle 1B directive)
- (this) `paco_review_atlas_v0_1_cycle_1b_db_layer.md`

**Standing rules invoked:**
- 5th standing rule (`feedback_paco_pre_directive_verification.md`) -- this review's section 0 Verified live block satisfies the rule
- 5-guardrail rule -- DSN user adaptation falls within Paco's explicit "PD adapts these sketches" authorization, not a guardrail invocation
- B2b + Garage anchor preservation invariant: holding
- Bidirectional one-liner format spec: this cycle's paired handoff follows it

---

## 11. Status

**CYCLE 1B CLOSED 5/5 PASS.** atlas.db module shipped; atlas schema with 4 tables provisioned; 4 pytest tests passing; first commit on `santigrey/atlas` advanced to `42e41b7`. Substrate untouched.

This Cycle 1B close-out commit on `santigrey/control-plane-lab` folds: this paco_review + SESSION.md Day 75 Cycle 1B close section append + paco_session_anchor.md update (Cycle 1B CLOSED, Cycle 1C NEXT, P6=20, standing rules=5) + CHECKLIST.md audit entry.

Ready for Cycle 1C (Garage S3 client + bucket adoption) per spec v3.

-- PD
