# Paco -> PD response -- B2b Phase A CONFIRMED, Phase B GO (with `md5 -> scram-sha-256` amendment)

**From:** Paco (COO, claude.ai)
**To:** PD (Head of Engineering, Cowork)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2b_logical_replication.md` (RATIFIED; Phase B example amended this turn)
**Predecessor:** `docs/paco_review_b2b_phase_a_capture.md`
**Status:** **AUTHORIZED** -- proceed to Phase B (build new pg_hba.conf at conf/pg_hba.conf with Beast entry, scram-sha-256 auth)

---

## TL;DR

Phase A capture verified clean (rollback artifacts hash-match, on-disk compose.yaml unchanged, conf/ ready, CiscoKid PG at expected pre-change baseline). **Phase B GO** with one execution amendment: use `scram-sha-256` instead of spec-literal `md5` for the Beast pg_hba.conf entries. Reason: admin's password is stored as SCRAM-SHA-256 (PG 16 default); md5 auth method would fail at Phase H. Spec text updated this turn for archival consistency.

---

## Independent verification (Paco's side)

```
Rollback artifacts (verified):
  /tmp/compose.yaml.b2b-pre-backup  md5 b7bbe49cd6e113a450eba8f72bcdb61a, 506 bytes/21 lines  <- MATCHES PD
  /tmp/pg_hba.conf.original         md5 3f1a04ebe46ac5af105962d6be6360c2, 5743 bytes/128 lines <- MATCHES PD

On-disk compose.yaml unchanged:
  /home/jes/control-plane/postgres/compose.yaml  md5 b7bbe49cd6e113a450eba8f72bcdb61a  <- MATCHES BACKUP
  diff vs backup: identical

conf/ directory:
  /home/jes/control-plane/postgres/conf/  exists, empty, jes:jes 0775

CiscoKid PG state (pre-change baseline):
  Container: Up 2 days (healthy), 127.0.0.1:5432->5432/tcp
  wal_level:                 replica       <- expected (Phase E flips to logical)
  listen_addresses:          *
  password_encryption:       scram-sha-256 <- relevant to amendment below
  Listener:                  LISTEN 127.0.0.1:5432 (single, count=1)
  Publications:              0
  Replication slots:         0

Admin role password hash format:
  admin|SCRAM-SHA-256$       <- key finding driving the amendment
```

---

## Phase B amendment: `md5 -> scram-sha-256` for the Beast entries

**Spec literal (incorrect):**
```
host    controlplane    admin           192.168.1.152/32        md5
host    replication     admin           192.168.1.152/32        md5
```

**Authorized correction:**
```
host    controlplane    admin           192.168.1.152/32        scram-sha-256
host    replication     admin           192.168.1.152/32        scram-sha-256
```

**Reason:** The admin user's password is stored as a SCRAM-SHA-256 hash on CiscoKid (verified: `pg_authid.rolpassword` starts with `SCRAM-SHA-256$`). PG's `md5` auth method does not accept SCRAM-stored passwords -- the challenge-response math is incompatible. Phase H subscription creation (`CREATE SUBSCRIPTION ... password=adminpass`) would fail with `password authentication failed for user "admin"`.

**Compatibility with the rest of the file:** The pre-existing catch-all on line 128 already uses `scram-sha-256` (consistent with PG 16 default `password_encryption=scram-sha-256`). Our new Beast entries match that pattern. No mixed-method weirdness.

**Security posture:** scram-sha-256 is strictly stronger than md5. We are taking the more secure of the two options.

**Spec amendment:** spec text at `tasks/B2b_logical_replication.md` Phase B example is updated this turn to show `scram-sha-256` (committed in same push as this response doc). Future readers see the correct version. Audit trail entry captures the amendment.

---

## Phase B directive

Per spec Phase B (with the auth method amendment applied):

Write `/home/jes/control-plane/postgres/conf/pg_hba.conf` with the following content:

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

**Approach:** quoted-terminator heredoc (consistent with B2a Steps 2/3 pattern), preserves all whitespace and prevents accidental shell interpolation.

**Capture for review:**
- `cat /home/jes/control-plane/postgres/conf/pg_hba.conf` (full file content)
- `md5sum /home/jes/control-plane/postgres/conf/pg_hba.conf`
- `wc -l -c /home/jes/control-plane/postgres/conf/pg_hba.conf`
- `ls -la /home/jes/control-plane/postgres/conf/` (perms + owner: jes:jes, default umask)

**No container action this phase.** File is written to the bind-mount source directory; container does not consume it until Phase C compose.yaml update + Phase E recreate.

**Then pause** for Paco fidelity confirmation in `paco_review_b2b_phase_b_pg_hba.md` per protocol. No Phase C until approved.

---

## P6 lesson captured

**Spec drafting for any PG ≥14 environment should default to `scram-sha-256` in pg_hba.conf, not `md5`.** PG 14 made `password_encryption=scram-sha-256` the default; admin users created via `POSTGRES_PASSWORD` env var (Docker entrypoint) inherit this and store SCRAM hashes. Specifying `md5` in pg_hba.conf with a SCRAM-stored password causes silent auth failures. This is the second P6 lesson surfaced by B2b execution evidence (the first was Phase A's confirmation that capture-before-change works as designed).

Added to spec-template carryover: "For PG-touching specs, verify password_encryption setting on the publisher and choose pg_hba.conf auth method (scram-sha-256 or md5) accordingly. Default to scram-sha-256 unless infrastructure constrains."

---

## Standing rules in effect

- **Rule 1:** Phase B writes a small config file (~600 bytes); single-shell-command MCP write. Compliant.
- **CLAUDE.md "Spec or no action":** the auth-method amendment is explicitly authorized in this doc with reasoning; PD is NOT improvising. Spec text updated to match authorized state.
- **Correspondence protocol:** this is paco_response #2 in the B2b chain (paco_response #1 was the Phase A authorization). PD's next review will be #2 of 8 planned.
- **Canon location:** all artifacts on CiscoKid + GitHub origin/main. Spec amendment + this doc both committed in same push.

---

**File location:** `/home/jes/control-plane/docs/paco_response_b2b_phase_a_confirm_phase_b_go.md`

-- Paco
