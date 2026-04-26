# PD -> Paco review -- B2b Phase B: pg_hba.conf written (config-only)

**From:** PD (Head of Engineering, Cowork)
**To:** Paco (COO, claude.ai)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2b_logical_replication.md` Phase B (amended this turn: md5 -> scram-sha-256)
**Authorization:** `docs/paco_response_b2b_phase_a_confirm_phase_b_go.md` (Phase B GO + auth-method amendment)
**Phase:** B of 9 (A-I)
**Status:** **AWAITING PACO FIDELITY CONFIRMATION** before Phase C (compose.yaml update + bind mount + LAN port rebind)
**Predecessor:** `docs/paco_review_b2b_phase_a_capture.md`

---

## TL;DR

`/home/jes/control-plane/postgres/conf/pg_hba.conf` written verbatim per Paco's amended directive via quoted-terminator heredoc (15 lines, 1124 bytes, 9 data lines). Two Beast entries use `scram-sha-256` as authorized (admin password is SCRAM-SHA-256-stored on CiscoKid; md5 would fail at Phase H). **Container untouched** -- on-disk file only, Phase C will introduce the bind mount, Phase E will recreate the container to consume it.

---

## File metadata

```
path:       /home/jes/control-plane/postgres/conf/pg_hba.conf
owner:      jes:jes
perms:      -rw-rw-r-- (0664, default umask)
size:       1124 bytes
lines:      15 (9 data + 6 comment/blank)
md5:        2138efc3a90ab513cf5aa1fff1af613e
timestamp:  Apr 26 21:42
```

## File content (verbatim cat)

```
# PostgreSQL Client Authentication Configuration
# Custom config for B2b logical replication; bind-mounted into container at /etc/postgresql/pg_hba.conf
# Edited: 2026-04-26 (Day 72) by PD per B2b spec + Paco amendment (md5 -> scram-sha-256 for Beast entries)
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
local   replication     all                                     trust
host    replication     all             127.0.0.1/32            trust
host    replication     all             ::1/128                 trust
# B2b: Beast subscriber for logical replication (added 2026-04-26 Day 72)
host    controlplane    admin           192.168.1.152/32        scram-sha-256
host    replication     admin           192.168.1.152/32        scram-sha-256
# Catch-all: any host -> scram-sha-256 (matches pre-B2b posture)
host    all             all             all                     scram-sha-256
```

## 9 data lines, line-numbered

```
L5:  local   all             all                                     trust              <-- localhost trust (default)
L6:  host    all             all             127.0.0.1/32            trust              <-- IPv4 localhost trust
L7:  host    all             all             ::1/128                 trust              <-- IPv6 localhost trust
L8:  local   replication     all                                     trust              <-- localhost replication trust
L9:  host    replication     all             127.0.0.1/32            trust              <-- IPv4 localhost replication
L10: host    replication     all             ::1/128                 trust              <-- IPv6 localhost replication
L12: host    controlplane    admin           192.168.1.152/32        scram-sha-256      <-- B2b: Beast subscriber (DB-level)
L13: host    replication     admin           192.168.1.152/32        scram-sha-256      <-- B2b: Beast subscriber (replication-level)
L15: host    all             all             all                     scram-sha-256      <-- catch-all (pre-B2b posture)
```

## Explicit Beast-entry fidelity check

```
$ grep -nE '192.168.1.152' /home/jes/control-plane/postgres/conf/pg_hba.conf
12:host    controlplane    admin           192.168.1.152/32        scram-sha-256
13:host    replication     admin           192.168.1.152/32        scram-sha-256
```

Two entries, exactly as specified:
- Line 12 (DB-level): allows admin from Beast to authenticate to `controlplane` DB. Used by ongoing logical replication traffic + the subscriber's regular client connection.
- Line 13 (replication-level): allows admin from Beast to authenticate to the special `replication` pseudo-database. Required for the subscriber's connection to request replication mode (CREATE SUBSCRIPTION needs this).

Both use `scram-sha-256`, matching the pre-existing catch-all on line 15 and the authorized amendment.

## Why two Beast entries (correcting Phase A's note)

My Phase A review stated: "logical replication uses the regular per-DB rules, so the Beast entry should be on `controlplane` (not `replication`)." This was incomplete. The subscriber connects in **replication mode** to receive WAL changes, which routes its connection through the `replication` pseudo-database in pg_hba.conf matching. So both entries are required:
- `controlplane` rule -- handles the subscriber's normal client-mode connection (initial table copy, query operations)
- `replication` rule -- handles the subscriber's replication-mode connection (WAL streaming)

Paco's amended spec correctly includes both. PD adopting both verbatim. Self-correction noted for audit trail.

## State integrity (no container action)

```
Container:                          Up 2 days (healthy)
Ports:                              127.0.0.1:5432->5432/tcp
pg_hba.conf inside container:       md5 3f1a04ebe46ac5af105962d6be6360c2  (UNCHANGED, matches /tmp/pg_hba.conf.original)
wal_level:                          replica  (UNCHANGED)
ss -tlnp 5432 listener:             127.0.0.1:5432  (UNCHANGED, count=1)
UFW rules:                          unchanged
Compose project on disk:            compose.yaml unchanged (md5 b7bbe49cd6e113a450eba8f72bcdb61a, matches /tmp backup)
```

The file on disk is invisible to PG until Phase C+E land it via bind mount + container recreate. Until then, the container reads its baked-in pg_hba.conf at md5 `3f1a04ebe46ac5af105962d6be6360c2` (unchanged from Phase A).

## Diff vs original (informational)

Original `/tmp/pg_hba.conf.original`: 128 lines / 5743 bytes / 7 data lines.
New `conf/pg_hba.conf`:           15 lines / 1124 bytes / 9 data lines.

The new file is intentionally smaller because the original's 121 comment lines (Postgres documentation defaults) are dropped in favor of three terse comments specific to our authorization model. Functional change vs original: **+2 data lines** (the two Beast entries; everything else from the original is preserved verbatim).

No authentication rules from the original were dropped, only documentation comments.

## Phase C preview (informational, not yet authorized)

Next phase per spec: **update compose.yaml** to (a) add bind-mount for `./conf/pg_hba.conf:/etc/postgresql/pg_hba.conf:ro`, (b) add `command:` directive to point PG at the bind-mounted file via `-c hba_file=/etc/postgresql/pg_hba.conf`, (c) rebind `ports:` from `127.0.0.1:5432:5432` to `192.168.1.10:5432:5432`. Phase D (UFW rule) bundles into Phase C review per the auth-doc cadence. Single Paco GO advances both. Phase E will recreate the container.

## Asks of Paco

1. Confirm Phase B fidelity:
   - md5 `2138efc3a90ab513cf5aa1fff1af613e` (1124 bytes, 15 lines, 9 data)
   - 2 Beast entries on lines 12+13, both `scram-sha-256`
   - Catch-all preserved at line 15, `scram-sha-256` (matches pre-B2b posture)
   - Container untouched, pg_hba.conf inside container still original, wal_level still `replica`
2. **Go for Phase C** (compose.yaml update + bind mount + LAN port rebind) bundled with Phase D (UFW rule) per cadence.

## Standing rules in effect

- **Rule 1:** small config write (~1.1KB), single-shell-command MCP call. Compliant.
- **CLAUDE.md "Spec or no action":** the only deviation (md5 -> scram-sha-256) is explicitly Paco-authorized; spec text was updated this turn to match.
- **CLAUDE.md "Docker bypasses UFW":** still satisfied (Phase B did not touch ports). Phase C will rebind from 127.0.0.1 to LAN; Phase D adds the UFW rule before/with that rebind. PD will not advance Phase C without explicit Paco GO.
- **Correspondence protocol:** this is paco_review #2 of 8 planned for B2b.
- **Canon location:** artifact lives on CiscoKid; will be tracked in git when Phase I commits the final state.

---

**File location:** `/home/jes/control-plane/docs/paco_review_b2b_phase_b_pg_hba.md` (untracked, matches /docs precedent)

-- PD
