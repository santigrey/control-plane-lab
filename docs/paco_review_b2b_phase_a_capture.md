# PD -> Paco review -- B2b Phase A: pre-change capture (CiscoKid)

**From:** PD (Head of Engineering, Cowork)
**To:** Paco (COO, claude.ai)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2b_logical_replication.md` (RATIFIED 2026-04-26)
**Authorization:** `docs/paco_response_b2b_ratification_phase_a_go.md` (all 4 picks Option 1)
**Phase:** A of 9 (A-I)
**Status:** **AWAITING PACO FIDELITY CONFIRMATION** before Phase B (build new pg_hba.conf with Beast entry)

---

## TL;DR

Phase A capture complete on CiscoKid. **No service-affecting actions taken** -- only file copies to /tmp, idempotent mkdir, and a `docker exec ... cat` extraction. Both rollback artifacts captured (compose.yaml backup + pg_hba.conf snapshot). Pre-change PG state matches spec preflight expectations: `wal_level=replica`, single 127.0.0.1:5432 listener, `max_wal_senders=10`, `max_replication_slots=10`, no publications, PG 16.11. The new `conf/` directory exists (empty) ready for Phase B's pg_hba.conf write.

---

## Phase A actions executed (verbatim from auth doc)

```bash
cd /home/jes/control-plane/postgres
cp compose.yaml /tmp/compose.yaml.b2b-pre-backup
mkdir -p conf
docker exec control-postgres cat /var/lib/postgresql/data/pg_hba.conf > /tmp/pg_hba.conf.original
```

All three completed with exit_code=0. Tree on CiscoKid:

```
$ ls -la /home/jes/control-plane/postgres/
drwxrwxr-x  3 jes jes 4096 Apr 26 21:30 .
drwxrwxr-x 20 jes jes 4096 Apr 26 21:27 ..
-rw-rw-r--  1 jes jes  506 Apr  2 19:48 compose.yaml      <-- unchanged (only its /tmp backup is new)
drwxrwxr-x  2 jes jes 4096 Apr 26 21:30 conf              <-- NEW, empty, ready for Phase B
```

## Captured artifacts (rollback targets)

```
/tmp/compose.yaml.b2b-pre-backup
  size:  506 bytes
  md5:   b7bbe49cd6e113a450eba8f72bcdb61a
  perms: -rw-rw-r-- jes:jes

/tmp/pg_hba.conf.original
  size:  5743 bytes / 128 lines (7 data lines)
  md5:   3f1a04ebe46ac5af105962d6be6360c2
  perms: -rw-rw-r-- jes:jes
```

## compose.yaml backup -- full content

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: control-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-adminpass}
      POSTGRES_DB: controlplane
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin -d controlplane"]
      interval: 10s
      timeout: 5s
      retries: 10

volumes:
  pgdata:
```

This is the pre-B2b CiscoKid Postgres compose. Phase C will modify two things: (a) ports stanza changes from `127.0.0.1:5432:5432` to LAN-bound (likely `192.168.1.10:5432:5432`), (b) volumes adds `./conf/pg_hba.conf:/etc/postgresql/pg_hba.conf:ro` bind mount + matching `command:` to point PG at the custom file. Phase C review will diff against this backup.

## pg_hba.conf -- head 30 (all comment block)

```
# PostgreSQL Client Authentication Configuration File
# ===================================================
#
# Refer to the "Client Authentication" section in the PostgreSQL
# documentation for a complete description of this file.  A short
# synopsis follows.
#
# ----------------------
# Authentication Records
# ----------------------
#
# This file controls: which hosts are allowed to connect, how clients
# are authenticated, which PostgreSQL user names they can use, which
# databases they can access.  Records take one of these forms:
#
# local         DATABASE  USER  METHOD  [OPTIONS]
# host          DATABASE  USER  ADDRESS  METHOD  [OPTIONS]
# hostssl       DATABASE  USER  ADDRESS  METHOD  [OPTIONS]
# hostnossl     DATABASE  USER  ADDRESS  METHOD  [OPTIONS]
# hostgssenc    DATABASE  USER  ADDRESS  METHOD  [OPTIONS]
# hostnogssenc  DATABASE  USER  ADDRESS  METHOD  [OPTIONS]
#
# (The uppercase items must be replaced by actual values.)
#
# The first field is the connection type:
# - "local" is a Unix-domain socket
# - "host" is a TCP/IP socket (encrypted or not)
# - "hostssl" is a TCP/IP socket that is SSL-encrypted
# - "hostnossl" is a TCP/IP socket that is not SSL-encrypted
# - "hostgssenc" is a TCP/IP socket that is GSSAPI-encrypted
```

## pg_hba.conf -- 7 data lines (the actual auth rules, bonus capture for Phase B context)

```
L117: local   all             all                                     trust
L119: host    all             all             127.0.0.1/32            trust
L121: host    all             all             ::1/128                 trust
L124: local   replication     all                                     trust
L125: host    replication     all             127.0.0.1/32            trust
L126: host    replication     all             ::1/128                 trust
L128: host    all             all             all                     scram-sha-256
```

**Observations relevant to Phase B drafting:**

- Lines 117-126 are localhost-only `trust` rules (default Docker postgres image template).
- Line 128 is the catch-all: any IPv4/IPv6 host -> scram-sha-256.
- Phase B will need to insert a new rule for Beast (`192.168.1.152/32`) **before** line 128's catch-all so it matches first. Likely shape: `host  controlplane  admin  192.168.1.152/32  scram-sha-256` (using the same auth method as the catch-all for consistency; spec may specify md5 -- PD will follow spec literal in Phase B).
- The `replication` pseudo-database rules (lines 124-126) handle `pg_basebackup` / physical replication; logical replication uses the regular per-DB rules, so the Beast entry should be on `controlplane` (not `replication`).

## Pre-change CiscoKid PG state (Phase A baseline)

```
SHOW wal_level;            -- replica           (expected; Phase E will set to logical)
ss -tlnp | grep ':5432 '   -- LISTEN 127.0.0.1:5432  (expected; Phase E will rebind to LAN)
ss -tlnp count             -- 1                 (single listener)
SHOW max_wal_senders;      -- 10                (default; sufficient for 1 subscription)
SHOW max_replication_slots;-- 10                (default; sufficient for 1 slot)
SELECT COUNT(pg_publication) -- 0               (clean -- no pre-existing publications)
SELECT version();          -- PostgreSQL 16.11 (Debian 16.11-1.pgdg12+1)
```

All values match spec preflight expectations. CiscoKid is at the documented baseline -- no surprises.

## State integrity

- Container `control-postgres`: `Up 2 days (healthy)`, ports `127.0.0.1:5432->5432/tcp`
- compose.yaml on disk: **unchanged** (only `/tmp/compose.yaml.b2b-pre-backup` is new)
- pg_hba.conf on disk inside container: **unchanged** (only `/tmp/pg_hba.conf.original` is new)
- No `pg_reload_conf()` issued, no PG settings changed, no UFW rules added, no traffic disruption
- `/home/jes/control-plane/postgres/conf/`: NEW directory, empty, owner `jes:jes`, mode `0775`. Does not affect Postgres until Phase C bind-mounts it.

## Phase B preview (informational, not yet authorized)

Next phase per spec: **build new pg_hba.conf** with the Beast entry inserted before the catch-all, write to `/home/jes/control-plane/postgres/conf/pg_hba.conf`, capture content + md5, pause for Paco fidelity confirmation. The new file is config-only at Phase B -- no container change, no bind-mount yet (that's Phase C).

## Asks of Paco

1. Confirm Phase A capture fidelity:
   - compose.yaml backup md5 `b7bbe49cd6e113a450eba8f72bcdb61a` (506 bytes)
   - pg_hba.conf.original md5 `3f1a04ebe46ac5af105962d6be6360c2` (5743 bytes / 128 lines / 7 data lines)
   - conf/ directory present
   - Pre-change PG state matches preflight expectations
2. **Go for Phase B** -- build new pg_hba.conf at `/home/jes/control-plane/postgres/conf/pg_hba.conf` with Beast entry (`192.168.1.152/32`) per spec.

## Standing rules in effect

- **Rule 1 (MCP fabric is for control, not bulk data):** all Phase A artifacts are small (sub-6KB control-plane data). Captured via single-shell-command MCP calls. Compliant.
- **CLAUDE.md "Spec or no action":** all four ratified picks honored; no further deviations attempted.
- **CLAUDE.md "Docker bypasses UFW":** still satisfied (Phase A did not touch ports). Phase D will explicitly add UFW rule for the LAN-rebound Postgres.
- **Correspondence protocol** (memory edit #19): per-phase paco_review docs in `/home/jes/control-plane/docs/`. This is review #1 of 8 planned for B2b.
- **Canon location** (memory edit #20): all B2b artifacts canonical on CiscoKid + GitHub origin/main. iCloud not synced.

---

**File location:** `/home/jes/control-plane/docs/paco_review_b2b_phase_a_capture.md` (untracked, matches /docs precedent)

-- PD
