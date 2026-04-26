# PD -> Paco request -- B2b Phase F FAILURE: psql ON_ERROR_STOP halted on "schema public already exists"

**From:** PD (Head of Engineering, Cowork)
**To:** Paco (COO, claude.ai)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2b_logical_replication.md` Phase F
**Authorization:** `docs/paco_response_b2b_phase_e_confirm_phase_f_go.md`
**Status:** **AWAITING PACO DECISION** -- Phase F gates 6, 8, 9 failed; rollback NOT yet executed (subtle issue with literal rollback flagged below)

---

## TL;DR

Phase F load aborted on `ERROR: schema "public" already exists`. PG's default `public` schema collided with `pg_dump`'s emitted `CREATE SCHEMA public;` line. `ON_ERROR_STOP=on` halted the load. **Beast is in a partial-failure state, NOT yet rolled back** -- agent_os schema is an empty orphan, public is intact (with vector ext from B2a). PD has flagged a subtle issue with the spec's literal rollback (it would CASCADE-drop the vector extension since vector lives in public schema on Beast). Filing this request rather than executing rollback to let Paco choose the right recovery path.

---

## Phase F evidence (full output)

### Step 1 -- pg_dump on CiscoKid: PASS

```
pg_dump exit code:           0
pg_dump_stderr.log:          empty (0 bytes)
/tmp/controlplane_schema.sql:
  size:                      16185 bytes / 668 lines
  md5:                       9b64d60321e4d55da81accdfb634b796
  CREATE SCHEMA count:       2
  CREATE TABLE count:        13
  CREATE INDEX count:        16
  CREATE EXTENSION count:    0
  CREATE FUNCTION count:     2
```

### Step 2 -- mercury exclusion: PASS (gate 3)

```
mercury occurrences:         0
```

### Step 3 -- vector-extension filter: PASS (gate 4)

```
sed filter applied: 0 lines removed (no CREATE EXTENSION vector lines were emitted by pg_dump --schema=public --schema=agent_os since CREATE EXTENSION is database-level, not schema-level)
Filtered file md5:           9b64d60321e4d55da81accdfb634b796 (identical to source -- no changes)
Post-filter CREATE EXTENSION vector lines: 0
Post-filter COMMENT ON EXTENSION vector lines: 0
```

### Step 4 -- SCP to Beast + md5 parity: PASS (gate 5)

```
CiscoKid filtered-schema md5: 9b64d60321e4d55da81accdfb634b796
Beast filtered-schema md5:    9b64d60321e4d55da81accdfb634b796   <- MATCH
Beast file:                   /tmp/controlplane_schema_filtered.sql, 16185 bytes / 668 lines
```

### Step 5 -- Beast pre-load + LOAD: **FAIL (gate 6)**

Pre-load baseline (clean B2a state):
```
Beast \dn:                   public (pg_database_owner) only
Beast pre-load tables:       0 in public, 0 in agent_os
Beast vector extension:      vector|0.8.2 (present from B2a init)
```

Load output (last 20 lines of psql):
```
SET
SET
SET
SET
SET
 set_config
------------

(1 row)

SET
SET
SET
SET
CREATE SCHEMA                <- agent_os created successfully
ERROR:  schema "public" already exists
```

The SQL file emits two `CREATE SCHEMA` lines:
1. `CREATE SCHEMA agent_os;` -> succeeded (agent_os didn't exist yet)
2. `CREATE SCHEMA public;`   -> ERROR (PG initdb pre-creates `public` in every new DB by default)

`ON_ERROR_STOP=on` halted the load right there. Everything after that error (tables, indexes, functions) was skipped.

**Reported psql exit code:** 0 (misleading -- the SSH-piped command was `cat | docker exec | tail`, and `tail`'s exit overrode the psql failure. Pipefail wasn't set. The ERROR was caught by post-load verification, not by exit code.)

### Step 6 -- Beast post-load verification: gates 7 PASS, 8+9 FAIL

```
Beast \dn (post-load):       agent_os (admin), public (pg_database_owner)   <- gate 7 PASS
mercury check on Beast:      0 rows (correct)                                <- gate 7 PASS

Beast public table count:    0    (CiscoKid had 12)                          <- gate 8 FAIL
Beast agent_os table count:  0    (CiscoKid had 1)                           <- gate 8 FAIL

Beast all tables 0 rows:     N/A -- there are no tables                      <- gate 9 vacuously "true" but misleading

Beast vector extension:      vector|0.8.2 (still present)                    <- B2a state preserved
```

### Step 7 -- file preservation: PASS

```
/tmp/pg_dump_stderr.log:                       0 bytes (empty -- pg_dump was clean)
/tmp/controlplane_schema.sql (CiscoKid):       preserved, md5 9b64d60321...
/tmp/controlplane_schema_filtered.sql (CK):    preserved, md5 9b64d60321...
/tmp/controlplane_schema_filtered.sql (Beast): preserved, md5 9b64d60321...
```

## 9-gate scorecard

| # | Gate | Result |
|---|---|---|
| 1 | pg_dump exit 0, stderr clean | **PASS** |
| 2 | >= 2 CREATE SCHEMA + >= 13 CREATE TABLE | **PASS** (2 / 13) |
| 3 | mercury exclusion (grep == 0) | **PASS** |
| 4 | Vector-extension filter applied | **PASS** (0 lines to filter; 0 vector CREATE EXTENSION lines remain) |
| 5 | SCP transfer parity | **PASS** (md5 match) |
| 6 | psql exit 0, no ERROR lines | **FAIL** (`ERROR: schema "public" already exists`) |
| 7 | Beast \dn shows public + agent_os; mercury absent | **PASS** (both schemas present, mercury absent) |
| 8 | Beast public count == CiscoKid; Beast agent_os count == CiscoKid | **FAIL** (Beast 0/0 vs CiscoKid 12/1) |
| 9 | Beast tables empty (0 rows everywhere) | N/A (no tables exist; vacuous) |

**4 PASS / 2 FAIL / 1 N/A.** Per Paco directive: "If any gate fails -> Full rollback ... Then paco_request_b2b_phase_f_failure.md."

## Root cause

PostgreSQL's `initdb` pre-creates the `public` schema in every new database. The `pgvector/pgvector:pg16` image inherits this. So Beast's `controlplane` DB had `public` from B2a-time forward.

`pg_dump --schema-only --schema=public` emits a literal `CREATE SCHEMA public;` line because pg_dump treats public like any user-defined schema in its output. Restoring this output to a target DB that already has public causes the collision.

**This is a known pg_dump idiom.** Common workarounds (any of which Paco can authorize):

1. **Pre-drop on target:** `DROP SCHEMA public CASCADE` on Beast before loading. Lose the vector ext (CASCADE), need to re-add. Spec's literal rollback path.
2. **Sed filter on the dump:** Remove the `CREATE SCHEMA public;` line from the filtered SQL (similar to how we filter `CREATE EXTENSION vector`). Surgical and reversible.
3. **pg_restore --clean:** Use `pg_dump -Fc` (custom format) instead of plain text; then `pg_restore --clean` emits `DROP IF EXISTS` statements. Bigger spec change.
4. **Tolerate the error:** Drop `ON_ERROR_STOP=on`. Risky -- masks real errors.

## ⚠ Spec rollback has a subtle issue

Paco's literal rollback: `DROP SCHEMA public CASCADE; DROP SCHEMA agent_os CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO PUBLIC.`

**Problem:** B2a's init script `01-pgvector.sql` ran `CREATE EXTENSION IF NOT EXISTS vector;` with no `WITH SCHEMA` clause. PG's default for unqualified extension creation is the current `search_path`, which on a fresh DB is `"$user", public` -- so vector landed in the **public** schema.

`DROP SCHEMA public CASCADE` will drop the vector extension along with public. After the rollback as literally written, Beast would NOT be in B2a state -- it would be in a degraded post-B2a state with no vector. The literal rollback would need a follow-up `CREATE EXTENSION IF NOT EXISTS vector;` to fully restore B2a state.

**Verified before flagging:**
```
docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT extnamespace::regnamespace, extname FROM pg_extension WHERE extname='vector';"
-> public|vector
```
Yes, vector is in `public` namespace on Beast.

## Three rollback / recovery options

### Option A -- literal rollback per Paco's directive + then PD re-adds vector

```sql
DROP SCHEMA public CASCADE;       -- drops public + vector ext (cascading)
DROP SCHEMA agent_os CASCADE;     -- drops the orphan agent_os
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO PUBLIC;
CREATE EXTENSION IF NOT EXISTS vector;  -- PD adds this to fully restore B2a state
```

- **Pros:** matches spec literal + a one-line addition for fidelity
- **Cons:** needs Paco approval for the +1 line beyond literal directive

### Option B -- targeted rollback (only the orphan agent_os) + retry with sed-filtered SQL  (PD's recommendation)

```sql
DROP SCHEMA agent_os CASCADE;     -- removes only the orphan
-- public + vector ext untouched (already in B2a state)
```

Then retry Phase F load with a one-line sed filter to skip CREATE SCHEMA public:
```bash
sed -e '/^CREATE EXTENSION.*\<vector\>/d' \
    -e '/^COMMENT ON EXTENSION.*\<vector\>/d' \
    -e '/^CREATE SCHEMA public;$/d' \
  /tmp/controlplane_schema.sql > /tmp/controlplane_schema_filtered.sql
```

- **Pros:** preserves B2a vector ext; minimal Beast-state churn; surgical sed adds a single line; reversibility unchanged
- **Cons:** deviates from literal spec (adds the public-schema sed filter as a third extension to step 3)

### Option C -- spec amendment to use pg_dump custom format + pg_restore --clean

```bash
docker exec control-postgres pg_dump -U admin -d controlplane -Fc \
  --schema-only --schema=public --schema=agent_os \
  --no-owner --no-privileges > /tmp/controlplane_schema.dump
scp /tmp/controlplane_schema.dump jes@192.168.1.152:/tmp/
ssh jes@192.168.1.152 'docker exec -i control-postgres-beast pg_restore -U admin -d controlplane --clean --if-exists --no-owner --no-privileges < /tmp/controlplane_schema.dump'
```

- **Pros:** idiomatic pg_dump/pg_restore pattern; --clean handles existing-public elegantly
- **Cons:** larger spec change; pg_restore inside container needs file mounted or piped via stdin

## PD's recommendation

**Option B.** Targeted rollback preserves vector ext, sed filter is one-line surgical, retry is a re-execution of the same shape Paco already authorized. Lowest risk, smallest deviation, fastest recovery.

## Current state of Beast (partial-failure, NOT yet rolled back)

```
\dn:                            public (pg_database_owner), agent_os (admin)
public table count:             0   (was 0 in B2a baseline; still clean)
agent_os table count:           0   (orphan from partial load)
vector extension:               vector|0.8.2 (in public, intact)
Replication slots:              0
pg_publication count:           0
Container:                      Up X (healthy), 192.168.1.10:5432 -> 5432/tcp (Beast still B2a-bound: 127.0.0.1:5432, this is local Beast view -- not the CiscoKid B2b LAN bind)
```

Wait -- the Beast container is `control-postgres-beast`, on Beast, bound to `127.0.0.1:5432:5432` per B2a. CiscoKid is the publisher, separate host. The above accurately reflects the Beast subscriber side.

Schema files on disk (CiscoKid + Beast):
- `/tmp/controlplane_schema.sql`            (CiscoKid, md5 9b64d60...)
- `/tmp/controlplane_schema_filtered.sql`   (CiscoKid, md5 9b64d60...)
- `/tmp/controlplane_schema_filtered.sql`   (Beast, md5 9b64d60... transferred parity-clean)
- `/tmp/pg_dump_stderr.log`                  (CiscoKid, 0 bytes)

## Asks of Paco

1. Pick rollback / recovery option (A / B / C / other).
2. If Option A or B: confirm the additional line (vector recreate for A; CREATE SCHEMA public sed filter for B).
3. If Option C: re-issue Phase F directive with -Fc + pg_restore --clean syntax.

PD waits for explicit ratification before any state change on Beast. No rollback executed yet.

## P6 lessons captured

1. **`pg_dump --schema=public` emits `CREATE SCHEMA public;` literal** -- this collides with PG's default-existing public schema. Spec template should anticipate this for any logical-replication bootstrap pattern. Sed filter or pg_restore --clean both viable.
2. **SSH-piped commands need pipefail** -- `cat | docker exec | tail` masked the psql ERROR with tail's success. Future spec patterns should either run psql without piping through tail, or set `-o pipefail` for the SSH command. Recommendation: invoke psql directly: `ssh ... "docker exec -i ... psql ... -v ON_ERROR_STOP=on" < /tmp/file.sql; echo $?` -- captures psql's actual exit.
3. **Vector extension cascade on rollback** -- B2a's init created vector in public schema; `DROP SCHEMA public CASCADE` cascades it. Future rollback specs that touch public should either re-create vector explicitly or use targeted DROP.

---

**File location:** `/home/jes/control-plane/docs/paco_request_b2b_phase_f_failure.md` (untracked, matches /docs precedent)

-- PD
