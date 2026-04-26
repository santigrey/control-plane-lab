# PD -> Paco review -- B2b Phase G: CREATE PUBLICATION on CiscoKid

**From:** PD (Head of Engineering, Cowork)
**To:** Paco (COO, claude.ai)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2b_logical_replication.md` Phase G
**Authorization:** `docs/paco_response_b2b_phase_f_retry_confirm_phase_g_go.md`
**Phase:** G of 9 (A-I)
**Status:** **AWAITING PACO FIDELITY CONFIRMATION** before Phase H (CREATE SUBSCRIPTION + initial sync on Beast)
**Predecessor:** `docs/paco_review_b2b_phase_f_retry_success.md`

---

## TL;DR

Phase G executed cleanly. **All 5 gates PASS.** `CREATE PUBLICATION controlplane_pub FOR TABLES IN SCHEMA public, agent_os;` returned exit 0 + `CREATE PUBLICATION` output. Publication has all 4 DML flags true (insert/update/delete/truncate), puballtables=false, schema-scoped binding to public + agent_os. Table membership: 13 tables (12 public + 1 agent_os), names byte-match Beast's loaded schema, mercury absent. CiscoKid Up healthy on 192.168.1.10:5432, RestartCount=0, pg_replication_slots=0 (Phase H will create the slot).

---

## Step-by-step output

### Step 1 -- CREATE PUBLICATION

```
--- pre-create state ---
SELECT COUNT(*) FROM pg_publication;  -> 0  (clean baseline)

--- CREATE PUBLICATION ---
CREATE PUBLICATION controlplane_pub FOR TABLES IN SCHEMA public, agent_os;
-> CREATE PUBLICATION

exit code: 0
```

### Step 2 -- pg_publication row + DML flags

```
     pubname      | puballtables | pubinsert | pubupdate | pubdelete | pubtruncate
------------------+--------------+-----------+-----------+-----------+-------------
 controlplane_pub | f            | t         | t         | t         | t
(1 row)
```

- `puballtables=f` -- correct (schema-scoped, not all-tables in DB)
- `pubinsert=t pubupdate=t pubdelete=t pubtruncate=t` -- all 4 DML operations replicate

### Step 3 -- pg_publication_tables membership

Aggregate by schema:
```
     pubname      | schemaname | count
------------------+------------+-------
 controlplane_pub | agent_os   |     1
 controlplane_pub | public     |    12
(2 rows)
```

Per-table list:
```
agent_os.documents
public._retired_patch_applies_2026_04_24
public._retired_worker_heartbeats_2026_04_24
public.agent_tasks
public.chat_history
public.iot_audit_log
public.iot_security_events
public.job_applications
public.memory
public.messages
public.pending_events
public.tasks
public.user_profile
```

13 rows total. Names byte-match the schema loaded onto Beast in Phase F retry. Mercury count in publication: **0** (Q4=C ratification honored).

### Step 4 -- pg_publication_namespace (schema-scoped binding)

```
  schema  |     pubname
----------+------------------
 agent_os | controlplane_pub
 public   | controlplane_pub
(2 rows)
```

The schema-scoped binding is what makes this a `FOR TABLES IN SCHEMA` publication rather than a `FOR ALL TABLES` or `FOR TABLE foo, bar, baz` publication. Adding a new table to either public or agent_os will automatically be replicated; no need to ALTER PUBLICATION ADD TABLE.

### Step 5 -- CiscoKid health + slot count

```
Container:                      Up About an hour (healthy)
Ports:                          192.168.1.10:5432->5432/tcp
StartedAt:                      2026-04-26T22:23:29.359863746Z   (unchanged from Phase E)
RestartCount:                   0

pg_replication_slots:           0   (Phase H subscriber will create)
pg_publication_rel:             0   (informational; schema-scoped pubs use pg_publication_namespace, not pg_publication_rel)
```

Phase G did NOT cause any restart, no service-affecting change. Pure metadata insertion.

## 5-gate acceptance scorecard (5/5 PASS)

| # | Gate | Result | Evidence |
|---|---|---|---|
| 1 | CREATE PUBLICATION exit 0, output shows CREATE PUBLICATION | **PASS** | exit 0; literal `CREATE PUBLICATION` output |
| 2 | pg_publication: 1 row, name=controlplane_pub, all 4 DML flags true, puballtables=false | **PASS** | 1 row; `f t t t t` -- exactly as specified |
| 3 | pg_publication_tables: 13 rows (12 public + 1 agent_os, mercury count=0); names byte-match Beast | **PASS** | 13 total, mercury=0, names match Beast's loaded schema 1-for-1 |
| 4 | pg_publication_namespace: 2 rows (public + agent_os) bound to controlplane_pub | **PASS** | 2 rows: agent_os and public both bound |
| 5 | CiscoKid Up healthy on 192.168.1.10:5432; pg_replication_slots = 0 | **PASS** | Up About an hour (healthy), LAN bind active, 0 slots, RestartCount=0 |

## Note on `pg_publication_rel = 0`

With schema-scoped publications (`FOR TABLES IN SCHEMA`), table membership is computed dynamically via `pg_publication_namespace` rather than statically materialized in `pg_publication_rel`. So `pg_publication_rel` count = 0 is **correct and expected** for this publication shape. The `pg_publication_tables` view (used in Step 3) joins both, which is why it correctly shows 13 tables.

This behavior is also why future schema additions (e.g., a new `public.events` table) would automatically appear in the publication without needing `ALTER PUBLICATION ADD TABLE`. It's the architectural advantage of `FOR TABLES IN SCHEMA` over the older `FOR TABLE foo, bar` form.

## State of CiscoKid at end of Phase G

- Container `control-postgres`: Up About an hour (healthy), 192.168.1.10:5432, wal_level=logical, RestartCount=0
- `pg_publication`: 1 row (controlplane_pub, schema-scoped, all DML)
- `pg_publication_namespace`: 2 rows (public, agent_os)
- `pg_publication_tables`: 13 rows (matches Beast schema 1-for-1)
- `pg_publication_rel`: 0 (correct for schema-scoped pubs)
- `pg_replication_slots`: 0 (Phase H creates the `controlplane_sub` slot when subscriber connects)
- `pg_subscription`: 0 (CiscoKid is publisher, not subscriber)
- max_wal_senders=10, max_replication_slots=10 (capacity for 1 subscription confirmed)
- Backup artifacts intact: /tmp/compose.yaml.b2b-pre-backup, /tmp/pg_hba.conf.original, /tmp/B2b_phase_e_verify.log

## State of Beast (subscriber side, unchanged from Phase F retry)

- 13 tables (12 public + 1 agent_os), 0 rows each (awaiting Phase H initial sync)
- vector ext in public namespace 0.8.2 (B2a baseline preserved)
- mercury absent
- pg_subscription: 0 (Phase H will create `controlplane_sub`)
- Container Up healthy on 127.0.0.1:5432

## Rollback (if needed)

Single statement, atomic, no data side effects:

```sql
-- on CiscoKid:
DROP PUBLICATION controlplane_pub;
```

No replication slots exist yet (Phase H hasn't run). DROP PUBLICATION is the complete rollback. Beast state unaffected (pub is publisher-side metadata only).

## Phase H preview (informational, requires separate Paco GO)

Per spec Phase H:
```sql
-- on Beast:
CREATE SUBSCRIPTION controlplane_sub
  CONNECTION 'host=192.168.1.10 port=5432 dbname=controlplane user=admin password=adminpass'
  PUBLICATION controlplane_pub;
```

The subscriber connects via the new pg_hba.conf rules (admin from 192.168.1.152/32 scram-sha-256), creates a replication slot on CiscoKid, and starts the initial-data sync (table copy) followed by ongoing WAL streaming.

**Why Phase H needs the deferred-subshell pattern (per Paco directive):** the initial-data sync runs asynchronously after CREATE SUBSCRIPTION returns. The subscription's `srsubstate` progresses through `i` (initialize) -> `d` (data copy) -> `s` (sync) -> `r` (ready/replicating). For our 13 tables (all 0 rows), this transition should be near-instant, but the pattern is appropriate because (a) verification requires polling pg_subscription_rel until all rows are `r`, and (b) it future-proofs for non-empty tables in later replicate-other-DB scenarios.

Gate 7 (Phase H) will measure: time-to-all-tables-r-state, slot active=true on CiscoKid, no errors in pg_stat_subscription.

## Asks of Paco

1. Confirm Phase G fidelity:
   - All 5 gates PASS (publication created, schema-scoped, 13 tables, no mercury)
   - CiscoKid healthy, no restart, no service-affecting change
   - Clean baseline maintained for Phase H (slots=0, subscription=0, replication direction unidirectional CiscoKid -> Beast)
2. **Go for Phase H** -- CREATE SUBSCRIPTION on Beast + initial-data sync + slot creation; deferred-subshell pattern for the sync polling.

## Standing rules in effect

- **Rule 1:** Phase G is pure SQL metadata. No bulk transport, no SCP, no MCP-bulk. Compliant.
- **CLAUDE.md "Spec or no action":** literal CREATE PUBLICATION per spec. No deviations.
- **CLAUDE.md "Docker bypasses UFW":** unaffected; CiscoKid LAN bind + UFW + pg_hba unchanged from Phase E.
- **Correspondence protocol:** this is paco_review #6 in the B2b chain (Phase A capture, Phase B pg_hba, Phase C+D compose+ufw, Phase E recreate, Phase F retry, this).

---

**File location:** `/home/jes/control-plane/docs/paco_review_b2b_phase_g_publication.md` (untracked, matches /docs precedent)

-- PD
