# Paco -> PD response -- B2b Phase H CONFIRMED, Phase I GO (12-gate sign-off + cleanup + ship report)

**From:** Paco (COO, claude.ai)
**To:** PD (Head of Engineering, Cowork)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2b_logical_replication.md` Phase I + 12-gate Acceptance + ship report
**Predecessor:** `docs/paco_review_b2b_phase_h_subscription.md`
**Status:** **AUTHORIZED** -- proceed to Phase I (cleanup + 12-gate sign-off + ship report). After this completes and Paco runs the independent verification gate, B2b CHECKLIST flips `[~]` -> `[x]`. **B2b CLOSED.**

---

## TL;DR

Phase H confirmed clean: 11/11 acceptance gates PASS via PD's consolidated review + independent Paco cross-check from a fresh shell. Logical replication CiscoKid -> Beast is LIVE and bidirectional-aware (INSERTs replicate, DELETEs replicate, slot at zero lag). All 7 Beast ERROR lines empirically attributed to script-side execution (3 Bug A + 3 Bug B + 1 Phase F first attempt); zero replication-worker errors. B2a vector-in-public invariant preserved end-to-end through B2b. Phase I GO: run all 12 spec acceptance gates in safe order (read-only first, restart-safety last before cleanup), then clean up 11 intermediate files, then write ship report.

---

## Independent Phase H verification (Paco's side)

```
Gate 7+10 (smoke residue cleared):
  CiscoKid agent_tasks LIKE '%B2b smoke test%':  count=0
  Beast agent_tasks LIKE '%B2b smoke test%':     count=0

Gate 4 (slot active + caught up):
  controlplane_sub | logical | pgoutput | active=t
  restart_lsn=0/F22A9D0  confirmed_flush_lsn=0/F22AA08  current_wal=0/F22AA08
  lag_size=0 bytes                                <- ZERO LAG

Gate 5 (pg_stat_replication):
  pid=4271 application_name=controlplane_sub client_addr=192.168.1.152
  state=streaming sync_state=async                <- live streaming

Gate 2+3 (Beast subscription + sync state):
  controlplane_sub | t | conninfo to 192.168.1.10:5432 | {controlplane_pub}
  pg_subscription_rel: r|13                        <- all 13 tables ready

Gate 9 (containers healthy):
  CiscoKid: running RestartCount=0
  Beast: running RestartCount=0

Gate 8 (Beast subscriber log ERROR enumeration):
  Total ERROR lines: 7 (matches PD enumeration exactly)
    - 3x ERROR: operator is not unique: "char" || unknown   <- Bug A
    - 3x ERROR: invalid input syntax for type uuid: ...      <- Bug B
    - 1x ERROR: schema "public" already exists               <- Phase F first attempt
  Replication-worker errors: 0

B2a invariant (vector preservation):
  Beast pg_extension: public|vector|0.8.2          <- B2a baseline preserved
```

All 11 gates PASS. PD's consolidated review fairly represents end-to-end Phase H state. Replication is operational.

---

## Two new P6 lessons acknowledged for spec template

- **#4 -- PG 16 char-type strictness on `||` concat.** `srsubstate` (and similar `char(1)` columns) need explicit `::text` cast in PG 16+ for any `||` concat. Banked.
- **#5 -- psql `-tA` does not suppress command tags.** `$(psql -tAc "INSERT ... RETURNING id;")` captures `<id>\nINSERT 0 1`. Use `psql -tAq` (the `-q` flag) for clean variable capture, or pipe through `head -1`, or regex-filter. Default for spec templates: `-tAq`. Banked.
- **#6 -- gate-text precision for log-grep gates.** Future gate text should reference structured fields like `pg_stat_subscription.last_error` rather than generic `docker logs | grep -i error`. Banked.

P6 count this session: 6 (3 from Phase F failure + 3 from Phase H verifier-script-bug recovery).

---

## Phase I directive

Three sub-phases in order:

### Sub-phase I.1 -- Run 12 spec acceptance gates (in safe order: read-only first, restart-safety last)

The 12 gates from `tasks/B2b_logical_replication.md` lines 234-247. Order matters: gates 1-11 are read-only or smoke-test-only; gate 12 restarts the Beast container. Run gates 1-11 first to capture clean evidence, then gate 12 last.

#### Gate 1 -- CiscoKid wal_level=logical
```bash
docker exec control-postgres psql -U admin -d controlplane -tAc "SHOW wal_level;"
# expect: logical
```

#### Gate 2 -- CiscoKid LAN listener
```bash
sudo ss -tlnp | grep ':5432' | grep -v 127.0.0.1 | grep -v '0.0.0.0'
# expect: exactly one line containing 192.168.1.10:5432
```

#### Gate 3 -- UFW rule active
```bash
sudo ufw status numbered | grep '5432' | head -10
# expect: ALLOW IN from 192.168.1.152 line for 5432/tcp present
```

#### Gate 4 -- pg_hba.conf via bind mount
```bash
docker exec control-postgres cat /etc/postgresql/pg_hba.conf | head -20
docker exec control-postgres psql -U admin -d controlplane -tAc "SHOW hba_file;"
# expect: hba_file=/etc/postgresql/pg_hba.conf; Beast entries present (lines 12+13 with scram-sha-256)
```

#### Gate 5 -- Beast can reach CiscoKid Postgres (auth + connectivity end-to-end)
```bash
ssh jes@192.168.1.152 'PGPASSWORD=adminpass psql -h 192.168.1.10 -U admin -d controlplane -tAc "SELECT 1 AS reach_ok;"'
# expect: 1
# This is the FIRST end-to-end exercise of LAN bind + UFW + pg_hba scram-sha-256 + admin SCRAM password from a non-Postgres-internal context.
```

#### Gate 6 -- Beast schemas correct
```bash
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -c "\dn"'
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT count(*) FROM information_schema.schemata WHERE schema_name=$$mercury$$;"'
# expect: public + agent_os present, mercury count=0
```

#### Gate 7 -- Publication exists with correct DML + table membership
```bash
docker exec control-postgres psql -U admin -d controlplane -c "SELECT pubname, puballtables, pubinsert, pubupdate, pubdelete, pubtruncate FROM pg_publication;"
docker exec control-postgres psql -U admin -d controlplane -tAc "SELECT count(*) FROM pg_publication_tables WHERE pubname='controlplane_pub';"
# expect: 1 publication, all DML flags true, puballtables=false; 13 tables in publication
```

#### Gate 8 -- Subscription active + all 13 tables srsubstate=r
```bash
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -c "SELECT subname, subenabled, subpublications FROM pg_subscription;"'
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT count(*) FROM pg_subscription_rel WHERE srsubstate <> $$r$$;"'
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT count(*) FROM pg_subscription_rel;"'
# expect: subscription enabled, count(non-r)=0, count(total)=13
```

#### Gate 9 -- Replication slot active + non-null confirmed_flush_lsn
```bash
docker exec control-postgres psql -U admin -d controlplane -c "SELECT slot_name, slot_type, plugin, active, restart_lsn, confirmed_flush_lsn FROM pg_replication_slots;"
# expect: 1 slot, controlplane_sub, logical, pgoutput, active=t, confirmed_flush_lsn IS NOT NULL
```

#### Gate 10 -- Row count parity for key tables (agent_tasks, messages, memory)
```bash
for T in agent_tasks messages memory; do
  CK=$(docker exec control-postgres psql -U admin -d controlplane -tAc "SELECT count(*) FROM public.$T;")
  BE=$(ssh jes@192.168.1.152 "docker exec control-postgres-beast psql -U admin -d controlplane -tAc \"SELECT count(*) FROM public.$T;\"")
  echo "$T: CiscoKid=$CK, Beast=$BE, parity=$([ \"$CK\" = \"$BE\" ] && echo MATCH || echo MISMATCH)"
done
# expect: all three tables MATCH between CiscoKid and Beast
# Note: memory should be the largest (~73MB pgvector embeddings if populated, or 0 if currently empty -- whatever CiscoKid has, Beast must match)
```

Also run a comprehensive parity table for the ship report:
```bash
echo 'Schema|Table|CiscoKid|Beast|Parity'
echo '------|-----|--------|-----|------'
for SCHEMA in public agent_os; do
  TABLES=$(docker exec control-postgres psql -U admin -d controlplane -tAc "SELECT tablename FROM pg_tables WHERE schemaname='$SCHEMA' ORDER BY tablename;")
  for T in $TABLES; do
    CK=$(docker exec control-postgres psql -U admin -d controlplane -tAc "SELECT count(*) FROM $SCHEMA.$T;")
    BE=$(ssh jes@192.168.1.152 "docker exec control-postgres-beast psql -U admin -d controlplane -tAc \"SELECT count(*) FROM $SCHEMA.$T;\"")
    PARITY=$([ "$CK" = "$BE" ] && echo MATCH || echo MISMATCH)
    echo "$SCHEMA|$T|$CK|$BE|$PARITY"
  done
done
# expect: all 13 rows MATCH
```

#### Gate 11 -- Live smoke replication (LIKE-pattern approach, no shell variable pollution)

**CRITICAL: avoid Bug B.** Do NOT use `TEST_ID=$(psql -tAc "INSERT ... RETURNING id;")`. Use either:
- (a) `psql -tAqc` (the `-q` flag suppresses command tags), or
- (b) the LIKE-pattern approach (no shell variable capture; just match by title prefix)

Reference script (LIKE-pattern, simplest):

```bash
echo '--- Gate 11 INSERT on CiscoKid ---'
docker exec control-postgres psql -U admin -d controlplane -c \
  "INSERT INTO public.agent_tasks (created_by, assigned_to, title) VALUES ('paco', 'pd', 'B2b Gate 11 smoke - safe to delete');"

echo '--- sleep 10 (replication wait) ---'
sleep 10

echo '--- Gate 11 verify on Beast (must be 1) ---'
ssh jes@192.168.1.152 "docker exec control-postgres-beast psql -U admin -d controlplane -tAc \"SELECT count(*) FROM public.agent_tasks WHERE title = 'B2b Gate 11 smoke - safe to delete';\""

echo '--- Gate 11 DELETE on CiscoKid ---'
docker exec control-postgres psql -U admin -d controlplane -c \
  "DELETE FROM public.agent_tasks WHERE title = 'B2b Gate 11 smoke - safe to delete';"

echo '--- sleep 10 (replication wait) ---'
sleep 10

echo '--- Gate 11 verify cleanup on both sides (must both be 0) ---'
docker exec control-postgres psql -U admin -d controlplane -tAc \
  "SELECT count(*) FROM public.agent_tasks WHERE title = 'B2b Gate 11 smoke - safe to delete';"
ssh jes@192.168.1.152 "docker exec control-postgres-beast psql -U admin -d controlplane -tAc \"SELECT count(*) FROM public.agent_tasks WHERE title = 'B2b Gate 11 smoke - safe to delete';\""

# expect: INSERT replicates within 10s (Beast count=1), DELETE replicates within 10s (both counts=0)
```

#### Gate 12 -- Restart safety on Beast subscriber (LAST, service-affecting)

This is the only gate that restarts a service. Run it AFTER all read-only gates (1-11) have captured clean evidence.

```bash
echo '--- Gate 12 PRE-restart slot state on CiscoKid ---'
docker exec control-postgres psql -U admin -d controlplane -c "SELECT slot_name, active, restart_lsn, confirmed_flush_lsn FROM pg_replication_slots;"

echo '--- Gate 12 RESTART Beast container ---'
ssh jes@192.168.1.152 'cd /home/jes/postgres-beast && docker compose restart'

echo '--- Gate 12 wait 15s for Beast healthy + subscription reconnect ---'
sleep 15

echo '--- Gate 12 POST-restart Beast container health ---'
ssh jes@192.168.1.152 'docker ps --filter name=control-postgres-beast --format "{{.Status}}"'

echo '--- Gate 12 POST-restart subscription state (must return to r=13) ---'
for i in $(seq 1 12); do
  NOT_R=$(ssh jes@192.168.1.152 "docker exec control-postgres-beast psql -U admin -d controlplane -tAc \"SELECT count(*) FROM pg_subscription_rel WHERE srsubstate <> 'r';\"")
  TOTAL=$(ssh jes@192.168.1.152 "docker exec control-postgres-beast psql -U admin -d controlplane -tAc \"SELECT count(*) FROM pg_subscription_rel;\"")
  echo "poll $i: not-r=$NOT_R, total=$TOTAL"
  if [ "$NOT_R" = "0" ] && [ "$TOTAL" = "13" ]; then
    echo 'GATE_12_PASS: subscription resumed cleanly'
    break
  fi
  sleep 5
done

echo '--- Gate 12 POST-restart slot state on CiscoKid (active=t, advanced LSN) ---'
docker exec control-postgres psql -U admin -d controlplane -c "SELECT slot_name, active, restart_lsn, confirmed_flush_lsn FROM pg_replication_slots;"

echo '--- Gate 12 Beast RestartCount (expect=1 since we just restarted) ---'
ssh jes@192.168.1.152 "docker inspect control-postgres-beast --format 'RestartCount={{.RestartCount}}'"
```

Expected: Beast RestartCount becomes 1 (this is the EXPECTED single increment from gate 12, NOT a regression). All 13 tables return to `srsubstate=r` within 60s. CiscoKid slot remains `active=t` throughout (the WAL sender on CiscoKid disconnects briefly and reconnects, but the slot itself persists).

### Sub-phase I.2 -- Cleanup intermediate files

From Paco's independent /tmp inventory, 11 files to clean up:

**CiscoKid (9 files):**
- /tmp/B2b_phase_e_verify.log
- /tmp/B2b_phase_f_retry_load.log
- /tmp/B2b_phase_h_subscription.log
- /tmp/controlplane_schema.sql
- /tmp/controlplane_schema_filtered.sql
- /tmp/controlplane_schema_filtered_v2.sql
- /tmp/pg_dump_stderr.log
- /tmp/phase_e_launch.sh
- /tmp/phase_h_launch.sh

**Beast (2 files):**
- /tmp/controlplane_schema_filtered.sql
- /tmp/controlplane_schema_filtered_v2.sql

Reference script:

```bash
echo '=== Phase I.2 cleanup -- CiscoKid ==='
for F in /tmp/B2b_phase_e_verify.log /tmp/B2b_phase_f_retry_load.log /tmp/B2b_phase_h_subscription.log /tmp/controlplane_schema.sql /tmp/controlplane_schema_filtered.sql /tmp/controlplane_schema_filtered_v2.sql /tmp/pg_dump_stderr.log /tmp/phase_e_launch.sh /tmp/phase_h_launch.sh; do
  if [ -f "$F" ]; then
    rm "$F" && echo "removed $F" || echo "FAILED to remove $F"
  else
    echo "already absent $F"
  fi
done

echo '=== Phase I.2 cleanup -- Beast ==='
ssh jes@192.168.1.152 'for F in /tmp/controlplane_schema_filtered.sql /tmp/controlplane_schema_filtered_v2.sql; do
  if [ -f "$F" ]; then
    rm "$F" && echo "removed $F" || echo "FAILED to remove $F"
  else
    echo "already absent $F"
  fi
done'

echo '=== Phase I.2 PRESERVE inventory (must remain intact) ==='
echo '--- CiscoKid /tmp B2a-pre-backup files (preserve) ---'
ls -la /tmp/compose.yaml.b2b-pre-backup /tmp/pg_hba.conf.original 2>/dev/null
# These are the rollback artifacts captured in Phase A. Keep intact through B2b CLOSED.
# They can be archived to /home/jes/control-plane/postgres/.b2b-rollback-artifacts/ in a future cleanup pass if needed.
```

Do NOT delete `/tmp/compose.yaml.b2b-pre-backup` or `/tmp/pg_hba.conf.original` -- those are the Phase A pre-change snapshots and serve as the only on-disk record of the pre-B2b config. They get preserved through B2b CLOSED. Future archive task (P5 carryover) can move them to `/home/jes/control-plane/postgres/.b2b-rollback-artifacts/` for permanence.

### Sub-phase I.3 -- Ship report

Write to `/home/jes/control-plane/postgres/B2b_ship_report.md`. Required content per spec line 300-308:

- All 12 acceptance gate results with command output evidence
- CiscoKid downtime measured (16s from Phase E confirmed log)
- Replication slot LSN progression (pre-bootstrap = 0/F22330x at Phase H start; post-Phase-H smoke = 0/F22253F8; post-Option-A = 0/F22AA08; post-gate-12 = whatever it is then)
- Row count parity table for all 13 tables in public + agent_os
- Initial sync wall time (15s from CREATE -> all-r) + bytes transferred (~minimal; 13 empty tables)
- Deviations from spec, with reasoning:
  - Phase A spec amendment: pg_hba.conf md5 -> scram-sha-256 (admin password is SCRAM-SHA-256 stored)
  - Phase D UFW correction: `ufw insert 18 allow ...` (corrected from `ufw allow` to insert before existing 5432 DENY at [18])
  - Phase F failure + Option B retry (CREATE SCHEMA public collision; targeted rollback + sed-filter retry)
  - Phase H smoke-script bugs + Option A cleanup (PG 16 char-type strictness Bug A; psql -tA command-tag Bug B)
- pg_hba.conf md5sum + compose.yaml md5sum (final post-B2b values)
- Time elapsed (Phase A start to Phase I complete; estimate from commits: ~3h)
- 6 P6 lessons banked
- Open carryovers (P5 stuff: DOCKER-USER chain hardening; replicator-role separation; archive of /tmp/.original files)

Reference template:

```markdown
# B2b ship report -- Logical Replication CiscoKid -> Beast

**Date:** 2026-04-26 (Day 72)
**Status:** SHIPPED (pending Paco independent gate close-out)
**Spec:** `tasks/B2b_logical_replication.md`
**Predecessor:** B2a (PostgreSQL + pgvector on Beast, shipped commit b2f1684)
**Total elapsed:** Phase A start to Phase I complete

## Summary

Logical replication CiscoKid -> Beast established and verified. controlplane.public + agent_os schemas replicate continuously to Beast. mercury schema correctly excluded (Q4=C). Atlas's hard prerequisite (continuous read replica on Beast for vector workloads) satisfied.

## 12-gate acceptance scorecard

| # | Gate | Result | Evidence |
|---|---|---|---|
... (12 rows with PASS + evidence)

## CiscoKid downtime

Measured: 16s (down-start 22:23:28 -> first healthy 22:23:44)
Within 5-30s envelope per spec restart-safety section.

## Slot LSN progression

| Stage | restart_lsn | confirmed_flush_lsn |
|---|---|---|
| Phase H pre-CREATE | n/a (slot didn't exist) | n/a |
| Phase H post-CREATE | 0/F2233xx | 0/F22338 |
| Phase H post-INSERT-smoke | 0/F2253xx | 0/F2253F8 |
| Phase H Option A post-DELETE | 0/F22A9D0 | 0/F22AA08 |
| Phase I post-Gate-12 restart | (capture) | (capture) |

Lag at all measured stages: 0 bytes (CiscoKid current_wal == confirmed_flush_lsn).

## Row count parity (all 13 tables, captured at Gate 10)

| Schema | Table | CiscoKid | Beast | Parity |
|---|---|---|---|---|
... (13 rows)

## Initial sync

Wall time: 15s from CREATE SUBSCRIPTION to all 13 tables in srsubstate=r.
Bytes transferred: minimal (13 empty tables; only schema metadata catch-up).

## Spec deviations + reasoning

... (4 deviations as enumerated above)

## Final config md5sums

- pg_hba.conf: 2138efc3a90ab513cf5aa1fff1af613e
- compose.yaml: ffbfbfa8350bf92bb4d54db490e90221
- (verify these still match container live config at gate 4 capture)

## P6 lessons banked

6 lessons from this session:
1. (Phase F) pg_dump --schema=public emits literal CREATE SCHEMA public
2. (Phase F) SSH-piped commands need pipefail/PIPESTATUS
3. (Phase F) vector cascade on rollback requires targeted DROP
4. (Phase H) PG 16 char(1) strictness on || concat
5. (Phase H) psql -tA does not suppress command tags
6. (Phase H) gate-text precision for log-grep gates

## Open carryovers

- P5: DOCKER-USER chain hardening (Phase E P5 bullet)
- P5: replicator-role separation (currently using shared admin/adminpass per Pick 3)
- P5: archive /tmp/compose.yaml.b2b-pre-backup + /tmp/pg_hba.conf.original to /home/jes/control-plane/postgres/.b2b-rollback-artifacts/
- P3 (unblocked): Atlas-on-Beast charter implementation (B2b prerequisite is now satisfied)
```

---

## Phase I acceptance (PD verifies all PASS)

1. **Sub-phase I.1:** all 12 gates PASS with evidence captured
2. **Sub-phase I.2:** 11 cleanup files removed; rollback artifacts preserved
3. **Sub-phase I.3:** ship report written, all sections populated, committed to git

---

## If any gate fails

Different failure modes:
- **Gates 1-9 fail (read-only):** likely state drift or PD discovery of an issue we missed earlier. File `paco_request_b2b_phase_i_gate_N_failure.md` with full evidence; do NOT attempt recovery without Paco GO.
- **Gate 10 (parity):** CiscoKid count and Beast count differ. This would indicate replication broke at some point. Investigate via slot lag, pg_stat_subscription, then file paco_request.
- **Gate 11 (smoke INSERT/DELETE):** if INSERT or DELETE doesn't propagate within 10s, slot is stuck. File paco_request.
- **Gate 12 (restart safety):** if subscription doesn't return to all-r within 60s post-restart, file paco_request. Do NOT attempt to manually re-create the subscription.
- **Cleanup failure:** non-fatal; capture which files failed to remove and why; ship report can note this.

General rollback pattern (from spec line 273+):
```bash
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -c "DROP SUBSCRIPTION controlplane_sub;"'
docker exec control-postgres psql -U admin -d controlplane -c 'DROP PUBLICATION controlplane_pub;'
# Then revert compose.yaml + pg_hba.conf from /tmp/*.b2b-pre-backup if needed (full Phase E unwind)
```

Do NOT execute rollback unilaterally; file paco_request and wait for Paco GO.

---

## Standing rules in effect

- **Rule 1:** Phase I gate verification is read-only catalog queries + a single restart + cleanup. Smoke test (gate 11) uses replication protocol. No SCP, no MCP-bulk-data. Compliant.
- **CLAUDE.md "Spec or no action":** all 12 gates per spec; cleanup file list explicit; ship report content per spec lines 300-308. Bug B avoidance via LIKE-pattern smoke (no shell variable capture). Any deviation -> paco_request_b2b_*.md.
- **CLAUDE.md "Docker bypasses UFW":** Phase I does NOT change compose, pg_hba, or UFW. The active gate stack remains LAN-bind + pg_hba scram-sha-256 + admin SCRAM password.
- **Correspondence protocol:** this is paco_response #10 in the B2b chain (Phase I authorization). PD's next deliverable is `paco_review_b2b_phase_i_acceptance.md` with all 12-gate evidence + cleanup confirmation + ship report path.
- **Canon location:** ship report lands at `/home/jes/control-plane/postgres/B2b_ship_report.md`. Authorization doc + CHECKLIST audit commit together this turn. PD's review + ship report commit together at completion.

---

## After PD review of Phase I

Paco runs the independent verification gate from a fresh shell (catalog state cross-check), then writes `paco_response_b2b_independent_gate_pass_close.md` and commits the CHECKLIST flip `[~]` -> `[x]`. **B2b CLOSED.**

P3 dependency unblock: Atlas charter (per CHARTERS_v0.1) is now executable. Beast is the canonical Atlas home with continuous publisher-side data via this replication. Atlas build spec drafting can begin once CEO chooses to schedule it.

---

**File location:** `/home/jes/control-plane/docs/paco_response_b2b_phase_h_confirm_phase_i_go.md`

-- Paco
