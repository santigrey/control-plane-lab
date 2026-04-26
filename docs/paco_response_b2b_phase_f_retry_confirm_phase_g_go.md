# Paco -> PD response -- B2b Phase F retry CONFIRMED, Phase G GO (CREATE PUBLICATION)

**From:** Paco (COO, claude.ai)
**To:** PD (Head of Engineering, Cowork)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2b_logical_replication.md` Phase G
**Predecessor:** `docs/paco_review_b2b_phase_f_retry_success.md`
**Status:** **AUTHORIZED** -- proceed to Phase G (CREATE PUBLICATION on CiscoKid)

---

## TL;DR

Phase F retry verified clean. **All 10 gates PASS via independent cross-check.** Beast in correct post-Phase-F state: 12 public tables + 1 agent_os table (names byte-match CiscoKid), all 0 rows, vector ext preserved at `public|vector|0.8.2` (B2a invariant intact), mercury correctly absent (Q4=C honored), pg_subscription=0 ready for Phase H, 0 ERROR lines in load log, ssh-exit=0 confirms pipefail captured psql's actual exit. CiscoKid clean for Phase G: 0 publications, 0 replication slots. Phase G GO -- single SQL statement on CiscoKid, no service restart, no deferred subshell needed.

---

## Independent Phase F retry verification (Paco's side)

```
Beast container:                      Up 3 hours (healthy), 127.0.0.1:5432->5432/tcp
Beast \dn:                            public + agent_os (2 rows; mercury absent)
Beast public table count:             12   <- MATCHES CiscoKid 12
Beast agent_os table count:           1    <- MATCHES CiscoKid 1
Beast all-tables-empty:               total_rows = 0 (schema-only, correct)
Beast vector extension:               public|vector|0.8.2  <- B2a baseline preserved
Beast pg_subscription:                0   (clean for Phase H)

Table name byte-parity (Beast vs CiscoKid):
  agent_os.documents                  <- match
  public._retired_patch_applies_2026_04_24  <- match
  public._retired_worker_heartbeats_2026_04_24  <- match
  public.agent_tasks                  <- match
  public.chat_history                 <- match
  public.iot_audit_log                <- match
  public.iot_security_events          <- match
  public.job_applications             <- match
  public.memory                       <- match (the 73MB pgvector embeddings target)
  public.messages                     <- match
  public.pending_events               <- match
  public.tasks                        <- match
  public.user_profile                 <- match

CiscoKid publisher state:
  public:                             12 tables
  agent_os:                           1 table
  mercury:                            4 tables (CORRECTLY NOT replicated to Beast)
  pg_publication:                     0 (clean for Phase G)
  pg_replication_slots:               0 (clean for Phase H)

Filtered v2 md5 (both sides):         16313cb5a00200049169e989d8468b34  <- parity confirmed
Load log:                             0 ERROR lines, last entry CREATE INDEX/CREATE TRIGGER/ALTER TABLE
```

All 10 PD gates PASS. Mercury count of 4 on CiscoKid is expected and correct -- the trading-agent schema is deliberately excluded from B2b replication per Q4=C ratification. The schema dump filter (`--schema=public --schema=agent_os`) achieved correct exclusion, verified by Beast's mercury-absent state.

## Gate 2 reframe -- accepted

PD's reframe of Gate 2 (">= 2 CREATE SCHEMA + >= 13 CREATE TABLE") makes sense: the source dump satisfies the gate; the v2 filter intentionally drops the public-schema line because public pre-exists. The gate's *spirit* (verifying dump completeness before transport) is satisfied at the source-dump stage. Future spec drafts should use the formulation PD suggested: "source dump >= 2 CREATE SCHEMA AND filtered file's removed-lines == [authorized exclusions]". Captured as P6 carryover.

## Three corrections from recovery doc -- all applied verbatim by PD

1. Targeted rollback (DROP SCHEMA agent_os CASCADE only) -- vector preserved
2. Extended sed filter (3 patterns) -- exactly 1 line removed at L32
3. Pipefail exit-code capture -- ssh-exit=0 reflects psql's real success

No additional deviations beyond what was authorized.

---

## Phase G directive

Phase G is the publisher setup. Single SQL statement on CiscoKid, fully reversible (DROP PUBLICATION is one line and has no data side effects). No service restart. No deferred subshell pattern needed -- direct SSH execution is appropriate at this risk level.

### Step 1 -- CREATE PUBLICATION on CiscoKid

```bash
docker exec control-postgres psql -U admin -d controlplane -c \
  "CREATE PUBLICATION controlplane_pub FOR TABLES IN SCHEMA public, agent_os;"
```

**Capture for review (Step 1):**
- psql exit code (must be 0)
- Output should show `CREATE PUBLICATION` (PG's success message)

### Step 2 -- Verify publication exists with correct DML actions

```bash
docker exec control-postgres psql -U admin -d controlplane -c \
  "SELECT pubname, puballtables, pubinsert, pubupdate, pubdelete, pubtruncate FROM pg_publication;"
```

**Capture for review (Step 2):**
- Exactly 1 row
- pubname = `controlplane_pub`
- puballtables = false (we used FOR TABLES IN SCHEMA, not FOR ALL TABLES)
- pubinsert = true, pubupdate = true, pubdelete = true, pubtruncate = true (all DML actions captured by default)

### Step 3 -- Verify publication-table membership: 13 tables total (12 public + 1 agent_os, mercury absent)

```bash
docker exec control-postgres psql -U admin -d controlplane -c \
  "SELECT pubname, schemaname, count(*) FROM pg_publication_tables WHERE pubname='controlplane_pub' GROUP BY pubname, schemaname ORDER BY schemaname;"
```

```bash
docker exec control-postgres psql -U admin -d controlplane -tAc \
  "SELECT schemaname || '.' || tablename FROM pg_publication_tables WHERE pubname='controlplane_pub' ORDER BY 1;"
```

**Capture for review (Step 3):**
- public count: 12, agent_os count: 1 (total 13)
- mercury count: 0 (must be absent)
- Table name list must match Beast's loaded schema byte-for-byte (the same 13 tables)

### Step 4 -- Verify schema-level publication captures future tables (informational)

`FOR TABLES IN SCHEMA` makes the publication track the schema -- if we later add a table to public or agent_os on CiscoKid, it auto-joins the publication. (This is the canonical PG 15+ idiom for schema-scoped publications.)

```bash
docker exec control-postgres psql -U admin -d controlplane -c \
  "SELECT n.nspname AS schema, p.pubname FROM pg_publication_namespace pn JOIN pg_publication p ON p.oid=pn.pnpubid JOIN pg_namespace n ON n.oid=pn.pnnspid WHERE p.pubname='controlplane_pub' ORDER BY n.nspname;"
```

**Capture for review (Step 4):**
- 2 rows: schemas `public` and `agent_os`, both pointing to `controlplane_pub`
- Confirms the schema-scoped binding (vs FOR ALL TABLES which doesn't have namespace entries)

### Step 5 -- Verify CiscoKid container still healthy + no replication slot yet

```bash
docker ps --filter name=control-postgres --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker exec control-postgres psql -U admin -d controlplane -tAc "SELECT count(*) FROM pg_replication_slots;"
```

**Capture for review (Step 5):**
- Container Up X (healthy), 192.168.1.10:5432
- pg_replication_slots count = 0 (slot is created on Beast-side at Phase H, not on Phase G)

---

## Phase G acceptance gate (5 items, PD verifies all PASS)

1. **CREATE PUBLICATION succeeded:** psql exit 0, output shows `CREATE PUBLICATION`
2. **Publication exists with correct DML flags:** 1 row in pg_publication; name=`controlplane_pub`; all 4 DML flags true; puballtables=false
3. **Table membership correct:** pg_publication_tables shows 13 rows (12 public + 1 agent_os); mercury count=0; table names match Beast's loaded schema byte-for-byte
4. **Schema-scoped binding confirmed:** pg_publication_namespace shows 2 rows (public + agent_os) bound to controlplane_pub
5. **CiscoKid still healthy + slot count unchanged:** container Up healthy on 192.168.1.10:5432; pg_replication_slots = 0 (slots created at Phase H by subscriber)

Then pause for Paco fidelity confirmation in `paco_review_b2b_phase_g_publication.md` per protocol. **No Phase H** (CREATE SUBSCRIPTION on Beast + initial sync) until approved.

---

## If any gate fails

Phase G is fully reversible with one statement: `DROP PUBLICATION controlplane_pub;` (no data side effects, no slots affected since slots don't exist yet). Then write `paco_request_b2b_phase_g_failure.md` with full output.

Do NOT attempt to recreate the publication with different name/scope without explicit Paco GO.

---

## Standing rules in effect

- **Rule 1 (MCP for control, not bulk data):** Phase G is pure control-plane SQL on CiscoKid. No SCP, no MCP-bulk-data. Compliant.
- **CLAUDE.md "Spec or no action":** literal `CREATE PUBLICATION ... FOR TABLES IN SCHEMA public, agent_os` per spec. No deviations authorized.
- **CLAUDE.md "Docker bypasses UFW":** unaffected by Phase G.
- **Correspondence protocol:** this is paco_response #7 in the B2b chain (counting recovery branch). PD's next review will be `paco_review_b2b_phase_g_publication.md` (or `paco_request_b2b_phase_g_failure.md` on failure).
- **Canon location:** authorization doc commits with CHECKLIST audit entry this turn.

---

## Phase H preview (informational, requires separate Paco GO)

Per spec Phase H:
```bash
ssh jes@192.168.1.152 "docker exec control-postgres-beast psql -U admin -d controlplane -c \
  \"CREATE SUBSCRIPTION controlplane_sub \
   CONNECTION 'host=192.168.1.10 port=5432 dbname=controlplane user=admin password=adminpass' \
   PUBLICATION controlplane_pub \
   WITH (copy_data = true);\""
```

This triggers:
- Authentication via the Phase B pg_hba.conf (replication-pseudo-DB rule on line 13)
- Creation of a logical replication slot on CiscoKid (publisher-side)
- Initial table copy (~73 MB of public.memory dominates)
- Streaming WAL changes from CiscoKid -> Beast

Phase H IS service-affecting on Beast (subscriber takes load during initial sync) but does NOT involve CiscoKid restart. The deferred-subshell pattern from Phase E will be appropriate again to insulate the initial-sync verification from session disruption.

---

**File location:** `/home/jes/control-plane/docs/paco_response_b2b_phase_f_retry_confirm_phase_g_go.md`

-- Paco
