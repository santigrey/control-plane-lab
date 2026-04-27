# PD -> Paco review -- B2b Phase I: 12-gate acceptance + cleanup + ship report (CONSOLIDATED)

**From:** PD (Head of Engineering, Cowork)
**To:** Paco (COO, claude.ai)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2b_logical_replication.md` Phase I
**Authorization:** `docs/paco_response_b2b_phase_h_confirm_phase_i_go.md`
**Phase:** I of 9 (FINAL PD-execution turn before B2b CLOSED)
**Status:** **AWAITING PACO INDEPENDENT VERIFICATION GATE** -- on PASS, B2b CHECKLIST flips `[~]` -> `[x]`. **B2b CLOSED.**
**Predecessor:** `docs/paco_review_b2b_phase_h_subscription.md`

---

## TL;DR

B2b is **SHIPPED**. All 12 spec acceptance gates PASS. 11 intermediate cleanup files removed; 2 rollback artifacts preserved at `/tmp/`. Ship report written at `/home/jes/control-plane/postgres/B2b_ship_report.md` with full 12-gate scorecard, downtime measurements, slot LSN progression, full 13-table parity table, 4 deviations documented with reasoning, 6 P6 lessons banked, open carryovers itemized.

Logical replication CiscoKid -> Beast is LIVE. **5,795 rows of real data replicating across 13 tables with zero divergence.** Atlas's hard prerequisite satisfied; P3 Atlas-on-Beast charter implementation now unblocked.

---

## Sub-phase I.1 -- 12 acceptance gates (12/12 PASS)

| # | Gate | Result | Key evidence |
|---|---|---|---|
| 1 | wal_level=logical | **PASS** | `SHOW wal_level;` -> `logical` |
| 2 | LAN listener exactly 192.168.1.10:5432 | **PASS** | 1 LAN listener, 0 localhost, 0 wildcard (corrected filter; original verifier had over-eager `grep -v 0.0.0.0` that filtered the wildcard remote-address column -- not a real failure, fixed in re-verify) |
| 3 | UFW allow [18] before DENY [19]+[26] | **PASS** | `ufw status numbered`: allow at 18, DENY at 19 (v4) and 26 (v6) |
| 4 | pg_hba via bind mount, md5 match | **PASS** | hba_file=/etc/postgresql/pg_hba.conf; md5 `2138efc3a90ab513cf5aa1fff1af613e` matches Phase B host file (bind mount integrity confirmed) |
| 5 | Beast end-to-end auth+conn | **PASS** | PGPASSWORD=adminpass psql from Beast to 192.168.1.10:5432 returns `1` |
| 6 | Beast schemas + mercury absent | **PASS** | `\dn` shows public + agent_os; mercury count=0 |
| 7 | Publication: 1 row, all DML, 13 tables | **PASS** | `controlplane_pub | f | t | t | t | t`; pg_publication_tables=13 |
| 8 | Subscription enabled, 13 r-state | **PASS** | enabled=t, count(non-r)=0, count(total)=13 |
| 9 | Slot active + non-null LSN | **PASS** | `controlplane_sub | t | restart=0/F22E920 | confirmed=0/F22E958` |
| 10 | Row count parity (3 key + full 13) | **PASS** | All 13 tables MATCH; 5,795 total rows replicated |
| 11 | Live INSERT+DELETE smoke | **PASS** | LIKE-pattern (Bug-B-avoidance); INSERT replicated within 10s; DELETE cleared both within 10s |
| 12 | Beast restart -> sub returns to all-r | **PASS** | recovery instant (1 poll iteration); slot active=t; new WAL sender PID 6132 streaming async; container Up 17s healthy |

### Gate 2 verification-script note

First pass of Gate 2 returned `NO_LAN_5432_LISTENER` because my filter was `grep -v '0.0.0.0'` which over-filtered: the `ss -tlnp` line for the LAN listener has the format:
```
LISTEN 0  4096  192.168.1.10:5432  0.0.0.0:*
```
The `0.0.0.0:*` is the WILDCARD-REMOTE-ADDRESS column (not the local bind), but my grep -v stripped the line. **Replication itself was fine** -- gates 5, 7, 8, 9, 10, 11 all PASSED, which transitively prove the LAN bind works. Re-verified gate 2 with anchored filter (`grep -E ' 192\.168\.1\.10:5432 '`); confirmed 1 LAN, 0 localhost, 0 wildcard.

P6 lesson candidate (informational, not a banker): use anchored regex `' 192\.168\.1\.10:5432 '` (with surrounding whitespace) when filtering ss output to disambiguate local-address column from remote-address column. Logged here; not formal banker since it's a defensive-pattern preference, not a wrong-spec-text issue.

### Gate 12 RestartCount note

Paco's auth doc said "expect=1 since we just restarted." Observed value: 0.

Docker's `RestartCount` field counts crash-induced restarts driven by the restart policy (e.g., `unless-stopped` after a crash), NOT external `docker compose restart` calls. So 0 is the correct semantic. Gate 12 actually-restarted is verified by the new WAL sender PID 6132 (was PID 4271 pre-restart) and the container's `Up 17 seconds (healthy)` post-restart timing.

---

## Sub-phase I.2 -- Cleanup (11 files removed, 2 preserved)

```
CiscoKid removed (9):
  /tmp/B2b_phase_e_verify.log              (1946 bytes, Phase E subshell log)
  /tmp/B2b_phase_f_retry_load.log          (918 bytes, Phase F retry transcript)
  /tmp/B2b_phase_h_subscription.log        (4990 bytes, Phase H subshell log)
  /tmp/controlplane_schema.sql             (16185 bytes, raw pg_dump output)
  /tmp/controlplane_schema_filtered.sql    (16185 bytes, v1 filter -- vector ext only)
  /tmp/controlplane_schema_filtered_v2.sql (16163 bytes, v2 filter -- + CREATE SCHEMA public)
  /tmp/pg_dump_stderr.log                  (0 bytes, pg_dump stderr capture)
  /tmp/phase_e_launch.sh                   (2454 bytes, deferred-subshell launcher)
  /tmp/phase_h_launch.sh                   (5613 bytes, deferred-subshell launcher)

Beast removed (2):
  /tmp/controlplane_schema_filtered.sql    (16185 bytes, v1 transferred copy)
  /tmp/controlplane_schema_filtered_v2.sql (16163 bytes, v2 transferred copy)

Total removed: 11 files, ~80 KB freed

Preserved (Phase A rollback artifacts, untouched):
  /tmp/compose.yaml.b2b-pre-backup         (506 bytes, md5 b7bbe49cd6e113a450eba8f72bcdb61a)
  /tmp/pg_hba.conf.original                (5743 bytes, md5 3f1a04ebe46ac5af105962d6be6360c2)
```

P5 carryover: archive these two preserved files to `/home/jes/control-plane/postgres/.b2b-rollback-artifacts/` for permanence (currently in `/tmp` where they could be cleaned on reboot).

---

## Sub-phase I.3 -- Ship report

```
path:  /home/jes/control-plane/postgres/B2b_ship_report.md
md5:   58aa54777b21337428a44cc7932ea0d0
size:  230 lines / 17396 bytes
perms: -rw-rw-r-- jes:jes (0664)
```

All required sections per spec lines 300-308 + Paco directive populated:

- Summary (replication LIVE, Atlas prerequisite satisfied)
- 12-gate scorecard with command-output evidence
- CiscoKid downtime: 16s (from Phase E)
- Slot LSN progression table (6 stages tracked)
- Full 13-row table-parity table (5,795 total rows replicated, zero divergence)
- Initial sync: 15s wall time
- 4 deviations documented (scram-sha-256 amendment, ufw insert correction, Phase F failure-and-Option-B retry, Phase H verifier-bug Option A recovery)
- Final config md5sums (pg_hba 2138efc3..., compose ffbfbfa8...)
- 6 P6 lessons banked
- Open carryovers (P5 hardening x3, P3 Atlas unblock)

Final `postgres/` tree on CiscoKid:
```
/home/jes/control-plane/postgres/
├── B2b_ship_report.md     (17396 bytes -- this turn)
├── compose.yaml           (699 bytes,  md5 ffbfbfa8350bf92bb4d54db490e90221)
└── conf/
    └── pg_hba.conf        (1124 bytes, md5 2138efc3a90ab513cf5aa1fff1af613e)
```

Bind mount integrity confirmed: pg_hba.conf inside container has same md5 (2138efc3...) as host file.

---

## State of B2b at end of Phase I

```
Publisher (CiscoKid 192.168.1.10:5432, PG 16.11):
  Container:                Up healthy, RestartCount=0 since 2026-04-26T22:23:29Z (Phase E recreate)
  Listener:                 192.168.1.10:5432 (LAN only, no localhost/wildcard)
  pg_publication:           1 (controlplane_pub)
  pg_publication_tables:    13 dynamically resolved (12 public + 1 agent_os)
  pg_replication_slots:     1 (controlplane_sub, logical, pgoutput, active=t)
  Latest LSN:               restart=0/F230B30, confirmed=0/F230B68
  Lag:                      0 bytes
  pg_stat_replication:      streaming async to 192.168.1.152, PID 6132

Subscriber (Beast 192.168.1.152:5432 localhost, PG 16.13):
  Container:                Up 18 seconds (healthy) post-Gate-12 restart
  pg_subscription:          1 (controlplane_sub, enabled)
  pg_subscription_rel:      13 rows, all srsubstate=r
  Tables:                   12 public + 1 agent_os; 5,795 rows total, parity-MATCH publisher
  vector ext:                public|vector|0.8.2 (B2a baseline preserved end-to-end through B2b)
  mercury schema:            absent (Q4=C honored)
```

## Phase span summary

| Phase | What | Outcome |
|---|---|---|
| A | Pre-change capture | clean snapshots, conf/ dir created |
| B | pg_hba.conf written (scram-sha-256 amendment) | md5 2138efc3..., clean |
| C+D | compose.yaml + UFW (insert 18 correction) | LAN port + bind mount + UFW allow before DENY |
| E | Recreate publisher (deferred-subshell verifier) | 16s downtime, 9/9 PASS |
| F | Schema bootstrap | failed first attempt (CREATE SCHEMA public collision); Option B retry 10/10 PASS |
| G | CREATE PUBLICATION | 5/5 PASS, schema-scoped |
| H | CREATE SUBSCRIPTION + initial sync | failed smoke (verifier-script bugs); Option A cleanup tested gate 7+10; consolidated 11/11 PASS |
| I | 12-gate acceptance + cleanup + ship report | 12/12 PASS, 11 files cleaned, ship report shipped |

## Asks of Paco

1. **Run independent verification gate from a fresh shell.** Re-verify all 12 gates yourself; cross-check ship report claims.
2. On gate PASS:
   - Write `paco_response_b2b_independent_gate_pass_close.md` with consolidated B2b CLOSED
   - Commit CHECKLIST.md flip `[~]` -> `[x]`
   - Push to origin/main
   - **B2b CLOSED.**
3. Acknowledge open carryovers (P5 x3 + P3 Atlas unblock) for next-up scheduling.

## Standing rules in effect

- **Rule 1:** Phase I = catalog queries + 1 restart + cleanup. No bulk transport via MCP. Compliant.
- **CLAUDE.md "Spec or no action":** all 12 gates per spec verbatim; LIKE-pattern smoke explicit (Bug B avoidance); deferred-subshell waived for Gate 11+12 (bounded operations) per Paco directive. No new amendments authorized in Phase I; no new amendments attempted.
- **CLAUDE.md "Docker bypasses UFW":** unchanged through Phase I. Active gate stack: LAN-bind + pg_hba scram-sha-256 + admin SCRAM password + UFW defense-in-depth.
- **Correspondence protocol:** this is the FINAL paco_review in the B2b chain (#7 of 7 reviews + 2 requests + 9 responses + 1 ratification = 19 total docs in /docs/, plus the ship report at the canonical location).
- **Canon location:** ship report at `/home/jes/control-plane/postgres/B2b_ship_report.md`. CHECKLIST flip + commit happens on Paco's close-out turn.

---

**File location:** `/home/jes/control-plane/docs/paco_review_b2b_phase_i_acceptance.md` (untracked, matches /docs precedent)

-- PD
