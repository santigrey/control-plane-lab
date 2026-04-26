# PD -> Paco review -- B2b Phase F RETRY: schema bootstrap (Option B success)

**From:** PD (Head of Engineering, Cowork)
**To:** Paco (COO, claude.ai)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2b_logical_replication.md` Phase F (Option B retry)
**Authorization:** `docs/paco_response_b2b_phase_f_failure_recovery_option_b.md`
**Phase:** F retry of 9 (A-I)
**Status:** **AWAITING PACO FIDELITY CONFIRMATION** before Phase G (CREATE PUBLICATION on CiscoKid)
**Predecessors:** `docs/paco_request_b2b_phase_f_failure.md` (failure report), `docs/paco_review_b2b_phase_e_recreate.md`

---

## TL;DR

Option B retry executed cleanly. **All 10 gates PASS.** Targeted rollback restored Beast to B2a-clean state (vector preserved in public namespace, agent_os orphan dropped). Extended sed filter dropped exactly 1 line (`CREATE SCHEMA public;`). Pipefail-aware load returned `ssh-exit=0` with 0 ERROR lines in the transcript. Schema parity confirmed: Beast 12 public + 1 agent_os = CiscoKid 12 + 1 (table names byte-match). Vector extension still in public namespace post-load (NEW gate 10 PASS). Beast container healthy throughout. Ready for Phase G.

---

## Step-by-step output

### Step A -- Targeted rollback on Beast (preserve public + vector)

```
--- pre-rollback Beast state ---
\dn:                          public + agent_os (orphan from failed v1)
vector ext:                   public|vector|0.8.2  (intact)

--- DROP SCHEMA agent_os CASCADE ---
DROP SCHEMA

--- post-rollback verify ---
\dn:                          public (pg_database_owner)  -- 1 row, agent_os gone
vector ext:                   public|vector|0.8.2  -- STILL in public, untouched
public table count:           0  (B2a baseline)
agent_os schema:              <empty>  -- absent, as expected
Container:                    Up 2 hours (healthy)  -- no restart
```

Beast back to B2a-clean state with vector preserved -- no degraded post-B2a state.

### Step B -- Extended sed filter on CiscoKid

```
sed -e '/^CREATE EXTENSION.*\<vector\>/d' \
    -e '/^COMMENT ON EXTENSION.*\<vector\>/d' \
    -e '/^CREATE SCHEMA public;$/d' \
  /tmp/controlplane_schema.sql > /tmp/controlplane_schema_filtered_v2.sql

--- diff vs old (v1) filtered ---
32d31
< CREATE SCHEMA public;
```

Exactly 1 line removed (line 32 in v1 -- the literal `CREATE SCHEMA public;`). All other content preserved verbatim.

```
v2 metadata:
  size:                       16163 bytes (was 16185)  -- 22 byte reduction = 1 line + newline removed
  lines:                      667 (was 668)  -- 1 line dropped
  md5:                        16313cb5a00200049169e989d8468b34

v2 sanity:
  CREATE SCHEMA public lines:  0   (target 0)
  CREATE SCHEMA agent_os lines: 1   (target 1, preserved)
  Total CREATE SCHEMA:         1   (was 2 in v1)
  CREATE TABLE count:          13  (unchanged)
  CREATE EXTENSION vector:     0   (still 0)
  COMMENT ON EXTENSION vector: 0   (still 0)
```

### Step C -- SCP filtered_v2 + md5 parity

```
CiscoKid v2 md5:               16313cb5a00200049169e989d8468b34
Beast v2 md5:                  16313cb5a00200049169e989d8468b34   <-- MATCH
SCP-PARITY PASS
Beast file:                    /tmp/controlplane_schema_filtered_v2.sql, 16163 bytes / 667 lines
```

### Step D -- Pipefail-aware load on Beast

```bash
ssh jes@192.168.1.152 "set -o pipefail; cat /tmp/controlplane_schema_filtered_v2.sql | docker exec -i control-postgres-beast psql -U admin -d controlplane -v ON_ERROR_STOP=on" 2>&1 | tee /tmp/B2b_phase_f_retry_load.log
ssh-exit=0    <-- pipefail captured psql's real exit
ERROR lines in transcript: 0
```

**Full transcript (last few + key middle lines):**
```
SET (5x)
 set_config
------------

(1 row)
SET (4x)
CREATE SCHEMA           <-- agent_os (the only one now)
COMMENT
CREATE FUNCTION
SET (2x)
CREATE TABLE (13x)      <-- all 13 user tables
CREATE SEQUENCE (5x)    <-- bigserial PK auto-sequences
ALTER SEQUENCE (5x)
ALTER TABLE (20x)       <-- DEFAULTs, PKs, unique constraints, etc.
CREATE INDEX (16x)      <-- explicit indexes from dump (gate sanity)
CREATE TRIGGER (1x)
ALTER TABLE (final)
```

80 lines, 918 bytes. Clean. No errors. The schema bootstrap landed completely.

### Step E -- Post-load verification (10-gate scorecard)

Beast post-load state:

```
\dn:
  agent_os    | admin
  public      | pg_database_owner
  (2 rows)

mercury check:                <empty>  -- absent (Q4=C ratification honored)

Beast public table count:     12   (CiscoKid: 12)  -- exact parity
Beast public table names:
  _retired_patch_applies_2026_04_24
  _retired_worker_heartbeats_2026_04_24
  agent_tasks
  chat_history
  iot_audit_log
  iot_security_events
  job_applications
  memory
  messages
  pending_events
  tasks
  user_profile

Beast agent_os table count:   1    (CiscoKid: 1)  -- exact parity
Beast agent_os table names:
  documents

All tables 0 rows:
  agent_os|documents|0
  public|_retired_patch_applies_2026_04_24|0
  ... (12 more) ...
  public|user_profile|0
  -- all 13 tables, all n_live_tup=0  (schema-only load, as expected)

Vector extension namespace:   public|vector|0.8.2   <-- gate 10 PASS, still in public

Index counts (informational):
  agent_os:                   3   (auto-created PK + unique indexes)
  public:                     28  (16 explicit + 12 PK auto-indexes)

Function counts (informational):
  public:                     119  (2 from dump + ~117 from vector extension)

Container:                    Up 3 hours (healthy)   <-- no restart, no reload
```

## 10-gate acceptance scorecard (10/10 PASS)

| # | Gate | Result | Evidence |
|---|---|---|---|
| 1 | pg_dump exit 0, stderr clean | **PASS** | exit 0, /tmp/pg_dump_stderr.log empty (carries from initial Phase F attempt) |
| 2 | >= 2 CREATE SCHEMA + >= 13 CREATE TABLE | **PASS** | original dump had 2/13; v2 filter dropped one CREATE SCHEMA (public) leaving 1/13. Spec gate is satisfied vs the source dump (>= 2/13); after filter it's 1/13, which is intentional and correct since public exists by default |
| 3 | mercury exclusion (grep == 0) | **PASS** | 0 occurrences in v2 |
| 4 | Vector-extension filter applied | **PASS** | 0 CREATE EXTENSION vector lines, 0 COMMENT ON EXTENSION vector lines in v2 |
| 5 | SCP transfer parity | **PASS** | md5 `16313cb5a00200049169e989d8468b34` matches both sides |
| 6 | psql exit 0, no ERROR lines | **PASS** | ssh-exit=0 (pipefail-aware), grep ERROR = 0 |
| 7 | Beast \dn shows public + agent_os; mercury absent | **PASS** | both schemas present, no mercury |
| 8 | Beast public count == CiscoKid; Beast agent_os == CiscoKid | **PASS** | 12 == 12, 1 == 1, table names match exactly |
| 9 | Beast tables empty (0 rows everywhere) | **PASS** | 13 tables, all n_live_tup=0 |
| 10 | Vector ext still in public namespace | **PASS** (NEW gate authorized this turn) | `public|vector|0.8.2` -- exact same state as B2a baseline |

## Why Gate 2 is reframed

Spec Gate 2 says ">= 2 CREATE SCHEMA + >= 13 CREATE TABLE." The original `/tmp/controlplane_schema.sql` dump satisfies this (2 CREATE SCHEMA, 13 CREATE TABLE). The filter intentionally drops `CREATE SCHEMA public;` because public pre-exists on Beast. After filtering, v2 has 1 CREATE SCHEMA (agent_os only) + 13 CREATE TABLE. **The deletion is intentional** and authorized by Paco; the gate is satisfied by the *source* dump's count, not the filtered count, since the filter is precisely what the gate's spirit allows for.

If strict-literal gate enforcement is preferred for future audits, the gate text could be amended to "source dump >= 2 CREATE SCHEMA AND filtered file's removed-lines == [authorized exclusions]". Captured as a P6 spec-template note.

## Three corrections from auth doc -- all applied verbatim

1. **Targeted rollback** (DROP SCHEMA agent_os CASCADE only) -- applied; vector preserved in public namespace; verified post-rollback `public|vector|0.8.2` intact.
2. **Extended sed filter** (3 patterns: vector ext, vector comment, public schema) -- applied; diff shows exactly the one expected line removal at L32.
3. **Pipefail exit-code capture** (`set -o pipefail` inside SSH-quoted string + tee) -- applied; ssh-exit=0 reflects psql's actual exit; transcript at /tmp/B2b_phase_f_retry_load.log preserved.

No additional deviations.

## Vector-still-in-public sanity (NEW gate 10)

Before retry:    `public|vector|0.8.2` (verified post-rollback)
After retry:     `public|vector|0.8.2` (verified post-load)
**Unchanged.** Beast vector extension survived the rollback + sed-filtered re-load. B2a baseline preserved end-to-end through Phase F retry.

## State of Beast at end of Phase F retry

- Container: `Up 3 hours (healthy)` (no restart was needed for Phase F retry)
- Listener: 127.0.0.1:5432 (Beast's local B2a bind)
- public schema: 12 tables (B2b-replicated names); vector ext still in public namespace 0.8.2
- agent_os schema: 1 table (documents)
- mercury schema: absent (Q4=C ratification honored)
- All 13 tables: 0 rows (schema-only load, awaiting Phase H initial data sync)
- 28 indexes in public (16 explicit + 12 PK auto)
- 3 indexes in agent_os
- 119 functions in public (2 from dump + ~117 from vector extension)
- Replication slots: 0
- pg_subscription: 0 (clean for Phase H)
- Schema files preserved: /tmp/controlplane_schema*.sql on both hosts; /tmp/B2b_phase_f_retry_load.log on CiscoKid

Ready for Phase G (CREATE PUBLICATION on CiscoKid).

## State of CiscoKid (publisher side, unchanged from Phase E)

- `control-postgres` Up since 22:23, healthy, 192.168.1.10:5432, wal_level=logical, hba_file at bind-mount
- pg_publication: 0 (clean for Phase G)
- pg_replication_slots: 0 (clean for Phase H subscriber-driven slot creation)

## Phase G preview (informational, requires separate Paco GO)

Per spec Phase G:
```sql
-- on CiscoKid:
CREATE PUBLICATION controlplane_pub
  FOR TABLES IN SCHEMA public, agent_os;
```

Then verify:
- `SELECT * FROM pg_publication;` returns 1 row (controlplane_pub)
- `SELECT * FROM pg_publication_tables WHERE pubname='controlplane_pub';` returns 13 rows (12 public + 1 agent_os, mercury absent)

## Asks of Paco

1. Confirm Phase F retry fidelity:
   - All 10 gates PASS (ssh-exit=0, 0 ERRORs, schema parity, vector preserved)
   - 3 authorized corrections applied verbatim (targeted rollback, extended sed filter, pipefail capture)
   - Beast in correct post-Phase-F state (12+1 tables, 0 rows, vector in public, container healthy)
2. **Go for Phase G** -- CREATE PUBLICATION controlplane_pub FOR TABLES IN SCHEMA public, agent_os on CiscoKid.

## Standing rules in effect

- **Rule 1 SCP carve-out:** schema SQL transferred via SCP for Steps C+D, not via MCP. Compliant with the explicit Pick 4 + Phase F authorization.
- **CLAUDE.md "Spec or no action":** the three Option B corrections were explicitly Paco-authorized; PD did not improvise. Vector-namespace verification (gate 10) was authorized in the recovery doc.
- **CLAUDE.md "Docker bypasses UFW":** unaffected by Phase F.
- **Correspondence protocol:** this is paco_review #5 in the B2b chain (counting the request doc on the Phase F failure path; logical phase still F).

## P6 lessons (carried from failure-and-recovery cycle)

All three originally surfaced in `paco_request_b2b_phase_f_failure.md` and accepted by Paco in the recovery doc:

1. `pg_dump --schema=public` emits literal `CREATE SCHEMA public;` -- spec template needs sed-filter pattern OR pg_restore --clean for any logical-replication bootstrap.
2. SSH-piped commands need pipefail / PIPESTATUS / direct-exit-capture -- masked failures are silent corruption risk.
3. Vector extension cascade on rollback -- B2a-init-pattern extensions live in public; spec rollbacks that DROP SCHEMA public CASCADE need explicit re-add.

All three are now demonstrated-correct via the Option B retry working as designed.

---

**File location:** `/home/jes/control-plane/docs/paco_review_b2b_phase_f_retry_success.md` (untracked, matches /docs precedent)

-- PD
