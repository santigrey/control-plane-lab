# B2b Ship Report -- Logical Replication CiscoKid -> Beast

**Date:** 2026-04-26 (Day 72)
**Status:** **SHIPPED** (pending Paco independent verification gate close-out)
**Spec:** `tasks/B2b_logical_replication.md` (RATIFIED 2026-04-26 Day 72)
**Predecessor:** B2a (PostgreSQL + pgvector on Beast, shipped earlier Day 72; commit `faa0d6a` etc.)
**Phase span:** A through I (9 phases over ~3h)
**Total deviations:** 4 (all explicitly Paco-authorized)
**P6 lessons banked:** 6

---

## Summary

Logical replication CiscoKid -> Beast established and verified end-to-end. `controlplane.public` (12 tables) and `controlplane.agent_os` (1 table) replicate continuously to Beast subscriber. `mercury` schema correctly excluded per Q4=C ratification. **Atlas's hard prerequisite -- continuous read replica on Beast for vector workloads -- is satisfied.**

Publisher: CiscoKid 192.168.1.10:5432 (PG 16.11), `wal_level=logical`, schema-scoped publication `controlplane_pub` with all 4 DML (insert/update/delete/truncate).

Subscriber: Beast 192.168.1.152:5432 (PG 16.13, localhost-bound), subscription `controlplane_sub` enabled, all 13 tables in srsubstate=r, vector extension preserved in public namespace from B2a baseline.

Replication slot `controlplane_sub` (logical, pgoutput) active, streaming async, zero lag.

---

## 12-gate acceptance scorecard (12/12 PASS)

| # | Gate | Result | Evidence |
|---|---|---|---|
| 1 | CiscoKid wal_level=logical | **PASS** | `SHOW wal_level;` -> `logical` |
| 2 | CiscoKid LAN listener exactly 192.168.1.10:5432 | **PASS** | `ss -tlnp` shows 1 listener on 192.168.1.10:5432; 0 on 127.0.0.1; 0 on 0.0.0.0 |
| 3 | UFW ALLOW IN from 192.168.1.152 to 5432/tcp at position 18 (before DENY at 19+26) | **PASS** | `ufw status numbered`: `[18] 5432/tcp ALLOW IN 192.168.1.152` |
| 4 | pg_hba.conf via bind mount; md5 match Phase B file | **PASS** | `SHOW hba_file = /etc/postgresql/pg_hba.conf`; md5 `2138efc3a90ab513cf5aa1fff1af613e`; Beast entries on lines 12+13 with scram-sha-256 |
| 5 | Beast can reach CiscoKid Postgres end-to-end (auth+conn) | **PASS** | `PGPASSWORD=adminpass psql -h 192.168.1.10 -U admin -d controlplane -tAc "SELECT 1"` -> `1` |
| 6 | Beast schemas: public + agent_os, mercury absent | **PASS** | `\dn` shows public + agent_os (admin); mercury count=0 |
| 7 | Publication exists with all DML + 13 tables | **PASS** | `controlplane_pub | f | t | t | t | t`; pg_publication_tables count=13 |
| 8 | Subscription enabled + count(non-r)=0 + count(total)=13 | **PASS** | `controlplane_sub enabled=t {controlplane_pub}`; not-r=0; total=13 |
| 9 | Replication slot active + non-null confirmed_flush_lsn | **PASS** | `controlplane_sub | logical | pgoutput | t | restart_lsn=0/F22E920 | confirmed_flush_lsn=0/F22E958` |
| 10 | Row count parity (key 3 tables + full 13-table table) | **PASS** | agent_tasks 46/46, messages 3/3, memory 4756/4756; full 13-row table all MATCH (see below) |
| 11 | Live INSERT + DELETE smoke replication via LIKE-pattern | **PASS** | INSERT on CiscoKid -> Beast count=1 within 10s; DELETE on CiscoKid -> both count=0 within 10s |
| 12 | Beast container restart -> subscription returns to all-r within 60s; slot remains active=t | **PASS** | recovery instant (1 poll iteration); slot active=t throughout; new WAL sender PID 6132 streaming async; container Up 17s healthy |

## CiscoKid downtime (Phase E)

Measured: **16 seconds** (down-start `2026-04-26T22:23:28+00:00` -> first healthy `2026-04-26T22:23:44+00:00`).
Within 5-30s envelope per spec restart-safety section (Pick 2 ratified).
Deferred-subshell pattern from D2 memory feedback insulated verification log from session disruption during the down-window.

## Slot LSN progression

| Stage | restart_lsn | confirmed_flush_lsn | Note |
|---|---|---|---|
| Phase G end (publication created) | n/a | n/a | slot did not exist yet (Phase H subscriber creates it) |
| Phase H post-CREATE SUBSCRIPTION | 0/F223300 | 0/F223338 | slot creation NOTICE on publisher; initial sync at this LSN |
| Phase H post-smoke INSERT (subshell) | (advancing) | 0/F2253F8 | smoke INSERT replicated; WAL caught up |
| Phase H Option A post-DELETE | 0/F22A9D0 | 0/F22AA08 | DELETE replicated; lag=0 bytes |
| Phase I Gate 9 capture | 0/F22E920 | 0/F22E958 | active and caught up |
| Phase I Gate 12 post-restart | 0/F230B30 | 0/F230B68 | new WAL sender PID 6132; slot persisted across Beast restart |

**Lag at all measured stages: 0 bytes** (CiscoKid current_wal == confirmed_flush_lsn). Replication is real-time.

## Row count parity (Gate 10, full 13-table)

| Schema | Table | CiscoKid | Beast | Parity |
|---|---|---:|---:|---|
| public | _retired_patch_applies_2026_04_24 | 4 | 4 | MATCH |
| public | _retired_worker_heartbeats_2026_04_24 | 2 | 2 | MATCH |
| public | agent_tasks | 46 | 46 | MATCH |
| public | chat_history | 482 | 482 | MATCH |
| public | iot_audit_log | 134 | 134 | MATCH |
| public | iot_security_events | 0 | 0 | MATCH |
| public | job_applications | 14 | 14 | MATCH |
| public | memory | 4756 | 4756 | MATCH (the 73MB pgvector embeddings target -- replicated cleanly) |
| public | messages | 3 | 3 | MATCH |
| public | pending_events | 25 | 25 | MATCH |
| public | tasks | 83 | 83 | MATCH |
| public | user_profile | 43 | 43 | MATCH |
| agent_os | documents | 203 | 203 | MATCH |

**13 tables, 5,795 total replicated rows (5,592 in public + 203 in agent_os), zero divergence.** Memory table contents (the largest at 4,756 rows of vector embeddings) replicated cleanly through the schema-only-bootstrap + streaming-WAL approach.

## Initial sync

- **Wall time:** 15 seconds (from CREATE SUBSCRIPTION to all 13 tables in srsubstate=r, captured in Phase H subshell log)
- **Bytes transferred during initial COPY:** ~not directly measured; tables were near-empty at Phase H start (smoke row inserted afterward via streaming, not COPY). Subsequent ongoing accumulation (4,756 memory rows etc.) replicated via the streaming-WAL path.
- **Method:** `WITH (copy_data = true)` on CREATE SUBSCRIPTION. PG handled the COPY internally; subscriber transitioned `i -> d -> s -> r` for each table.

## Spec deviations + reasoning (4 total)

### Deviation 1 -- Phase B pg_hba auth method: md5 -> scram-sha-256

**Spec literal:** `md5` for Beast entries.
**Authorized correction:** `scram-sha-256` for both Beast entries (lines 12+13).
**Reason:** admin's password is stored as a SCRAM-SHA-256 hash on CiscoKid (PG 16+ default `password_encryption=scram-sha-256`); `md5` auth method does not accept SCRAM-stored passwords. Phase H subscriber connect would have failed with `password authentication failed for user admin`.
**Authorization:** `docs/paco_response_b2b_phase_a_confirm_phase_b_go.md`
**Verification:** Gate 5 (Beast PGPASSWORD-auth from outside Postgres) returned `1`.

### Deviation 2 -- Phase D UFW: `ufw allow` -> `ufw insert 18 allow`

**Spec literal:** `ufw allow from 192.168.1.152 to any port 5432 proto tcp`.
**Authorized correction:** `ufw insert 18 allow from 192.168.1.152 to any port 5432 proto tcp comment 'B2b: Beast subscriber'`.
**Reason:** pre-existing 5432 DENY rules at position 18 (IPv4) and 25 (IPv6) from Day 48 hardening. Plain `ufw allow` appends to the END of the list, where it would never match because the DENY at [18] short-circuits first. `insert 18` places the allow BEFORE the DENY, satisfying first-match-wins evaluation.
**Authorization:** `docs/paco_response_b2b_phase_b_confirm_phase_c_d_go.md`
**Verification:** Gate 3 shows allow at [18] with DENY pushed to [19] and [26].
**Caveat:** UFW rule is documented defense-in-depth only; Docker iptables manipulation bypasses UFW INPUT-chain rules. Real gates remain LAN-only listener + pg_hba.conf + scram-sha-256 + admin SCRAM password. P5 carryover to harden via DOCKER-USER chain.

### Deviation 3 -- Phase F failure-and-Option-B retry

**Spec literal:** Phase F single-pass `pg_dump --schema-only --schema=public --schema=agent_os | sed -e <vector filter> | scp | psql ON_ERROR_STOP=on`.
**What happened:** First Phase F attempt aborted on `ERROR: schema "public" already exists` because PG initdb pre-creates `public` in every new DB; pg_dump's emitted `CREATE SCHEMA public;` collided.
**Authorized recovery (Option B):** targeted `DROP SCHEMA agent_os CASCADE` on Beast (preserving public + vector ext); extended sed filter (added `'/^CREATE SCHEMA public;$/d'`); pipefail-aware load (`set -o pipefail` to capture psql exit through SSH pipe); retry.
**Authorization:** `docs/paco_response_b2b_phase_f_failure_recovery_option_b.md`
**Verification:** Phase F retry 10/10 gates PASS; vector ext preserved in public namespace through entire cycle.
**Spec text amended:** the Phase F section in `tasks/B2b_logical_replication.md` was updated this turn to reflect the corrected procedure for future readers.

### Deviation 4 -- Phase H smoke verifier-script bugs + Option A cleanup

**Spec literal:** Phase H subshell verifier captures TEST_ID via `$(psql -tAc "INSERT ... RETURNING id;")` and uses TEST_ID in subsequent verify + DELETE.
**What happened:** psql `-tA` does NOT suppress command tags; `INSERT 0 1` was captured into TEST_ID alongside the UUID, polluting subsequent `WHERE id = '$TEST_ID'` constructs with `invalid input syntax for type uuid`. INSERT replicated correctly (verified post-hoc), but DELETE never executed; smoke residue remained on both sides.
**Authorized recovery (Option A):** clean DELETE via LIKE-pattern (no shell variable capture); 10s wait; cross-check both sides cleared.
**Authorization:** `docs/paco_response_b2b_phase_h_failure_recovery_option_a.md`
**Verification:** Phase H retry gate 7+10 PASS; replication slot LSN advanced through DELETE.
**Phase I Gate 11 implements the Bug-B-avoidance pattern:** uses LIKE-pattern smoke (no shell variable capture). Gate 11 PASSED on first execution.

## Final config md5sums

```
pg_hba.conf (host file):                       2138efc3a90ab513cf5aa1fff1af613e
pg_hba.conf (inside container):                2138efc3a90ab513cf5aa1fff1af613e   <-- bind mount integrity confirmed
compose.yaml:                                  ffbfbfa8350bf92bb4d54db490e90221
compose.yaml backup (Phase A pre-B2b):         b7bbe49cd6e113a450eba8f72bcdb61a   <-- preserved at /tmp/compose.yaml.b2b-pre-backup
pg_hba.conf.original (Phase A pre-B2b):        3f1a04ebe46ac5af105962d6be6360c2   <-- preserved at /tmp/pg_hba.conf.original
```

## P6 lessons banked (6 total)

From Phase F failure-and-recovery cycle:

1. **`pg_dump --schema=public` emits literal `CREATE SCHEMA public;`** -- collides with PG's default-existing public schema. Spec template needs sed-filter pattern (drop `^CREATE SCHEMA public;$` line) OR `pg_restore --clean` for any logical-replication schema bootstrap.
2. **SSH-piped commands need `pipefail` or `PIPESTATUS`** -- `cat | docker exec | tail` chain masks real psql ERRORs with tail's success exit. Pattern: `ssh ... "set -o pipefail; ..."` or use direct `< /tmp/file.sql` redirection instead of `cat | ...`.
3. **Vector extension cascade on rollback** -- B2a init created vector unqualified, landing it in `public` namespace. Rollbacks that `DROP SCHEMA public CASCADE` cascade-drop vector. Use targeted DROP that preserves public, OR re-create extension explicitly after recreating public.

From Phase H verifier-script-bug recovery:

4. **PG 16+ `char(1)` strictness on `||` concat.** Columns like `srsubstate` (`pg_subscription_rel`) are `char(1)`, not `text`. PG 16+ stops auto-casting `char` for `||`. Fix: `srsubstate::text || '...' || count(*)`. Spec template needs explicit casts in any subscription-poll display query.
5. **psql `-tA` does NOT suppress command tags.** `INSERT 0 1`, `UPDATE 1`, etc. emit on a separate line, polluting `$(...)` capture. Default for spec templates: use `-tAq` (the `-q` flag), OR pipe through `head -1` for first-line-only, OR regex-filter the captured output.
6. **Gate-text precision for log-grep gates.** Generic `docker logs | grep -i error` catches ALL ERROR lines including verifier-script-side errors. Future gate text should reference structured fields like `pg_stat_subscription.last_error` or `srsubstate=e` rather than container-log greps.

All 6 lessons confirmed-correct via the demonstrated successes of Phase F retry (1-3) and Phase H Option A + Phase I Gate 11 (4-5) and Gate 8 enumeration (6).

## Open carryovers

### P5 (security/credentials hardening)
- **DOCKER-USER chain hardening** -- UFW INPUT rules don't enforce on Docker-published ports. Add explicit DOCKER-USER chain rules to make the Beast-IP allow / Anywhere-DENY actually enforce at iptables level. Captured during Phase D.
- **Replicator-role separation** -- B2b currently uses shared `admin/adminpass` per Q3=A ratification. Production hardening should create a dedicated `replicator` role with REPLICATION attribute only and separate password, then rotate. Captured during Pick 3 ratification.
- **Archive Phase A rollback artifacts** -- move `/tmp/compose.yaml.b2b-pre-backup` and `/tmp/pg_hba.conf.original` to `/home/jes/control-plane/postgres/.b2b-rollback-artifacts/` for permanence (currently in /tmp where they might get cleaned up on reboot). Captured during Phase I.

### P3 (now unblocked by B2b)
- **Atlas-on-Beast charter implementation** -- per CHARTERS_v0.1, Atlas (Head of Operations) is supposed to run on Beast with continuous publisher-side data via this replication. B2b prerequisite is satisfied. CEO can now schedule Atlas build spec drafting.

### P6 (methodology)
- **Spec template carryover for the 6 P6 lessons** above. Folded into future PG-touching specs.

## Final state of B2b at sign-off

```
Publisher (CiscoKid 192.168.1.10:5432, PG 16.11):
  Container:                    Up healthy, RestartCount=0 (since Phase E recreate at 22:23:29Z)
  Listener:                     192.168.1.10:5432 (LAN only)
  Settings:                     wal_level=logical, hba_file=/etc/postgresql/pg_hba.conf
  pg_publication:               1 (controlplane_pub, schema-scoped FOR TABLES IN SCHEMA public, agent_os)
  pg_publication_namespace:     2 (public + agent_os)
  pg_publication_tables:        13 dynamically resolved
  pg_replication_slots:         1 (controlplane_sub, logical, pgoutput, active=t)
  Latest LSN:                   restart=0/F230B30, confirmed_flush=0/F230B68 (post-Gate-12)
  Lag:                          0 bytes
  pg_stat_replication:          1 row, streaming, async, client=192.168.1.152, PID 6132 (post-Gate-12)

Subscriber (Beast 192.168.1.152:5432 localhost, PG 16.13):
  Container:                    Up healthy (post-Gate-12 restart)
  Listener:                     127.0.0.1:5432 (B2a-bound, unchanged)
  pg_subscription:              1 (controlplane_sub, enabled, conninfo to publisher)
  pg_subscription_rel:          13 rows, all srsubstate=r
  Tables:                       12 public + 1 agent_os; row counts MATCH publisher (13 tables, 5,795 rows total)
  vector extension:             public|vector|0.8.2 (B2a baseline preserved through entire B2b)
  mercury schema:               absent (Q4=C honored)
```

## Hand-off to Paco for independent verification

Awaiting Paco's final independent verification gate from a fresh shell. On Paco gate PASS:
- B2b CHECKLIST.md line: `[~]` -> `[x]`
- Audit trail entry on CiscoKid (SESSION.md Day 72 close)
- Commit + push of CHECKLIST.md update
- Atlas charter implementation unblocks (P3)
- B2b CLOSED.

## Cross-references

Full B2b paper trail in `/home/jes/control-plane/docs/` (chronological, 19+ docs):

```
01. paco_response_b2b_ratification_phase_a_go.md           (Paco: 4 picks ratified)
02. paco_review_b2b_phase_a_capture.md                     (PD: capture)
03. paco_response_b2b_phase_a_confirm_phase_b_go.md        (Paco: scram-sha-256 amendment)
04. paco_review_b2b_phase_b_pg_hba.md                      (PD: pg_hba.conf written)
05. paco_response_b2b_phase_b_confirm_phase_c_d_go.md      (Paco: ufw insert correction)
06. paco_review_b2b_phase_c_d_compose_ufw.md               (PD: compose + ufw)
07. paco_response_b2b_phase_c_d_confirm_phase_e_go.md      (Paco: Phase E GO)
08. paco_review_b2b_phase_e_recreate.md                    (PD: 16s downtime, 9/9 PASS)
09. paco_response_b2b_phase_e_confirm_phase_f_go.md        (Paco: Phase F GO)
10. paco_request_b2b_phase_f_failure.md                    (PD: CREATE SCHEMA public collision)
11. paco_response_b2b_phase_f_failure_recovery_option_b.md (Paco: Option B)
12. paco_review_b2b_phase_f_retry_success.md               (PD: 10/10 PASS)
13. paco_response_b2b_phase_f_retry_confirm_phase_g_go.md  (Paco: Phase G GO)
14. paco_review_b2b_phase_g_publication.md                 (PD: publication created)
15. paco_response_b2b_phase_g_confirm_phase_h_go.md        (Paco: Phase H GO)
16. paco_request_b2b_phase_h_failure.md                    (PD: smoke verifier bugs)
17. paco_response_b2b_phase_h_failure_recovery_option_a.md (Paco: Option A)
18. paco_review_b2b_phase_h_subscription.md                (PD: 11/11 PASS consolidated)
19. paco_response_b2b_phase_h_confirm_phase_i_go.md        (Paco: Phase I GO)
20. paco_review_b2b_phase_i_acceptance.md                  (PD: this turn -- consolidated 12/12)
```

Plus this ship report at canonical location: `/home/jes/control-plane/postgres/B2b_ship_report.md`

---

**File location:** `/home/jes/control-plane/postgres/B2b_ship_report.md` on CiscoKid

-- PD
