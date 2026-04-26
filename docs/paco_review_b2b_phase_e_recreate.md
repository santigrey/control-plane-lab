# PD -> Paco review -- B2b Phase E: recreate (deferred-subshell verification)

**From:** PD (Head of Engineering, Cowork)
**To:** Paco (COO, claude.ai)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2b_logical_replication.md` Phase E
**Authorization:** `docs/paco_response_b2b_phase_c_d_confirm_phase_e_go.md`
**Phase:** E of 9 (A-I) -- first service-affecting phase
**Status:** **AWAITING PACO FIDELITY CONFIRMATION** before Phase F (schema bootstrap pg_dump + scp + psql)
**Predecessor:** `docs/paco_review_b2b_phase_c_d_compose_ufw.md`

---

## TL;DR

Phase E recreate completed cleanly via Paco's reference deferred-subshell pattern. **Downtime: 16 seconds** (well within the 5-30s envelope). All 9 acceptance gates PASS. Container is running on the new compose: LAN-bound `192.168.1.10:5432`, `wal_level=logical`, bind-mounted `pg_hba.conf` (md5 `2138efc3...` matches Phase B file), PID 1 args reflect the command stanza, no restart loops, `pg_isready` accepting connections, max_wal_senders/max_replication_slots both 10. Independent cross-check from a separate SSH context confirms the subshell findings.

---

## Mechanics adopted

Used Paco's reference script verbatim (no mechanical variation). Wrote launcher to `/tmp/phase_e_launch.sh` via heredoc, ran it; launcher fired the nohup'd subshell (PID 2875350) and returned in <1s with `Phase E backgrounded.` echo. Subshell exec'd its own stdout/stderr to `/tmp/B2b_phase_e_verify.log`. Polled the log for `=== PHASE E COMPLETE ===` marker; found at iteration 3 (~15s wait). Total subshell runtime end-to-end ~17s.

The deferred-subshell pattern (originally surfaced from D2 on Day 71) once again insulated the verification record from any session disruption during the down-window. SSH session itself was unaffected (CiscoKid postgres restart did NOT kill the MCP-side ssh subprocess because they're in different cgroups), but the pattern is correct defensive practice.

---

## Full subshell log (46 lines)

```
[2026-04-26T22:23:28+00:00] === PHASE E START ===
[2026-04-26T22:23:28+00:00] PRE-DOWN container state:
control-postgres        Up 3 days (healthy)     127.0.0.1:5432->5432/tcp
[2026-04-26T22:23:28+00:00] docker compose down
 Container control-postgres Stopping
 Container control-postgres Stopped
 Container control-postgres Removing
 Container control-postgres Removed
 Network postgres_default Removing
 Network postgres_default Removed
[2026-04-26T22:23:29+00:00] down completed in 1s
[2026-04-26T22:23:29+00:00] docker compose up -d
 Network postgres_default Creating
 Network postgres_default Created
 Container control-postgres Creating
 Container control-postgres Created
 Container control-postgres Starting
 Container control-postgres Started
[2026-04-26T22:23:29+00:00] up -d returned in 0s
[2026-04-26T22:23:29+00:00] === HEALTH POLL (cap 60s) ===
[2026-04-26T22:23:29+00:00] poll 1/12: health=starting
[2026-04-26T22:23:34+00:00] poll 2/12: health=starting
[2026-04-26T22:23:39+00:00] poll 3/12: health=starting
[2026-04-26T22:23:44+00:00] poll 4/12: health=healthy
[2026-04-26T22:23:44+00:00] downtime (down-start to healthy): 16s
[2026-04-26T22:23:44+00:00] === POST-RECREATE VERIFICATION ===
--- ps ---
control-postgres        Up 15 seconds (healthy) 192.168.1.10:5432->5432/tcp
--- wal_level ---
logical
--- hba_file ---
/etc/postgresql/pg_hba.conf
--- internal pg_hba.conf md5 (expect 2138efc3a90ab513cf5aa1fff1af613e from Phase B) ---
2138efc3a90ab513cf5aa1fff1af613e  /etc/postgresql/pg_hba.conf
--- PID 1 cmdline ---
postgres -c hba_file=/etc/postgresql/pg_hba.conf -c wal_level=logical
--- listener ---
LISTEN 0      4096                  192.168.1.10:5432       0.0.0.0:*
--- max_wal_senders / max_replication_slots ---
10
10
--- pg_isready (gate 8) ---
/var/run/postgresql:5432 - accepting connections
--- RestartCount (gate 9) ---
0
[2026-04-26T22:23:45+00:00] === PHASE E COMPLETE ===
```

## Cross-check from a fresh SSH context (Step 3)

```
--- docker ps ---
control-postgres   Up 40 seconds (healthy)   192.168.1.10:5432->5432/tcp

--- ss -tlnp 5432 ---
LISTEN 0  4096  192.168.1.10:5432  0.0.0.0:*    (count=1)

--- SHOW wal_level ---
logical

--- internal pg_hba.conf md5 ---
2138efc3a90ab513cf5aa1fff1af613e  /etc/postgresql/pg_hba.conf

--- ufw 5432 rules ---
Status: active
[18] 5432/tcp     ALLOW IN  192.168.1.152   # B2b: Beast subscriber
[19] 5432         DENY IN   Anywhere
[26] 5432 (v6)    DENY IN   Anywhere (v6)

--- additional sanity ---
pg_publication count:               0  (clean baseline; Phase G will create controlplane_pub)
pg_replication_slots count:         0  (clean baseline; Phase H subscriber will create slot)
Up since:                           2026-04-26T22:23:29.359863746Z
RestartCount:                       0
PID:                                2875588
Image SHA:                          sha256:0a07c4114ba6d1d04effcce3385e9f5ce305eb02e56a3d35948a415a52f193ec
```

All cross-check values match the subshell log -- no drift between in-subshell view and live state.

## 9-gate acceptance scorecard (9/9 PASS)

| # | Gate | Spec | Result | Evidence |
|---|---|---|---|---|
| 1 | Container running on new image | `Up Xs (healthy)`, `192.168.1.10:5432->5432/tcp` (NOT 127.0.0.1) | **PASS** | `Up 40 seconds (healthy)  192.168.1.10:5432->5432/tcp` |
| 2 | wal_level = logical | was replica | **PASS** | `SHOW wal_level` returns `logical` |
| 3 | Internal pg_hba.conf via bind mount | `SHOW hba_file = /etc/postgresql/pg_hba.conf`; md5 = `2138efc3a90ab513cf5aa1fff1af613e` | **PASS** | both confirmed: hba_file path correct + md5 matches Phase B file byte-for-byte |
| 4 | PID 1 args reflect command stanza | `postgres -c hba_file=... -c wal_level=logical` | **PASS** | `postgres -c hba_file=/etc/postgresql/pg_hba.conf -c wal_level=logical` |
| 5 | Listener on LAN IP | exactly one `192.168.1.10:5432`; NO `127.0.0.1:5432`, NO `0.0.0.0:5432` | **PASS** | `LISTEN 0 4096 192.168.1.10:5432 0.0.0.0:*` count=1 |
| 6 | Replication parameters intact | max_wal_senders >= 10; max_replication_slots >= 10 | **PASS** | both = 10 |
| 7 | Downtime measured | 5-30s expected | **PASS** | **16 seconds** (down-start to first healthy) |
| 8 | Health endpoint responds | pg_isready succeeds | **PASS** | `/var/run/postgresql:5432 - accepting connections` |
| 9 | RestartCount = 0 | no crash loops | **PASS** | `RestartCount: 0` |

## Measured downtime breakdown

```
22:23:28  docker compose down issued
22:23:29  down completed (1s)
22:23:29  docker compose up -d issued, returned
22:23:29  poll 1: starting
22:23:34  poll 2: starting
22:23:39  poll 3: starting
22:23:44  poll 4: healthy   <-- pg_isready accepting + healthcheck transition
          ============
          16s total down-start to healthy
```

The 16s is dominated by PG's startup: bind-mounted hba_file parsing, WAL-level switch, healthcheck CMD-SHELL `pg_isready` polling internal at 10s intervals. First two polls (5s, 10s post-up) caught `starting`; third poll at 15s caught `healthy`. Within spec's 5-30s envelope.

## Notable observation (informational, not a B2b concern)

`systemctl is-active ai-operator` returns `inactive`. This is the orchestrator service that B2b spec assumed would auto-reconnect during the down window. The service was already inactive *before* Phase E (this is not a Phase-E-induced state). The auto-reconnect resilience design is therefore not exercised in this run. **Not a B2b failure** -- B2b's only requirement at this layer is that PG itself recovers cleanly, which it did.

Flag for awareness: if the orchestrator is supposed to be running, that's a separate operational task (start/enable the service). Not in B2b scope. Capturing here so it doesn't get lost.

## Image SHA observation

CiscoKid's `pgvector/pgvector:pg16` image: `sha256:0a07c4114ba6d1d04effcce3385e9f5ce305eb02e56a3d35948a415a52f193ec`
Beast's same-tag image (from B2a): `sha256:8ed3192326bb9d114cd5ef9acace453d5dae17425bd089d089330584c84c5a34`

Different SHAs because CiscoKid pulled the floating `:pg16` tag earlier (PG 16.11 era) and Beast pulled it 8 weeks ago (PG 16.13 era). This is the canonical reason CiscoKid is publisher 16.11 and Beast is subscriber 16.13. Per Paco's ratification: subscriber >= publisher within-major drift is the canonical direction for logical replication. To be re-confirmed in B2b ship report.

## State of CiscoKid at end of Phase E

- Container: `Up 40+ seconds (healthy)`, recreated cleanly with new compose
- Listener: `192.168.1.10:5432` (LAN, single listener)
- wal_level: `logical`
- hba_file: `/etc/postgresql/pg_hba.conf` (bind-mounted)
- pg_hba.conf inside container: md5 `2138efc3a90ab513cf5aa1fff1af613e` (matches Phase B host file)
- PID 1 args: `postgres -c hba_file=... -c wal_level=logical`
- max_wal_senders / max_replication_slots: both 10
- pg_publication: 0 (clean for Phase G)
- pg_replication_slots: 0 (clean for Phase H)
- RestartCount: 0
- UFW: allow at [18], DENY at [19] (v4) + [26] (v6)
- Backup artifacts intact: `/tmp/compose.yaml.b2b-pre-backup`, `/tmp/pg_hba.conf.original`, `/tmp/B2b_phase_e_verify.log`

Ready for Phase F (schema bootstrap CiscoKid -> Beast via pg_dump + scp + psql, per Pick 4 ratification).

## Phase F preview (informational, requires separate Paco GO)

Per spec Phase F:
```
# On CiscoKid:
docker exec control-postgres pg_dump -U admin -d controlplane --schema-only \
  --schema=public --schema=agent_os > /tmp/controlplane_schema.sql
md5sum /tmp/controlplane_schema.sql
scp /tmp/controlplane_schema.sql jes@192.168.1.152:/tmp/controlplane_schema.sql
# On Beast:
ssh jes@192.168.1.152 'md5sum /tmp/controlplane_schema.sql'  # transfer parity
ssh jes@192.168.1.152 'docker exec -i control-postgres-beast psql -U admin -d controlplane < /tmp/controlplane_schema.sql'
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -c "\\dn"'  # post-restore schema list
```

`mercury` schema is excluded per Q4=C ratification. Initial-data sync happens at Phase H (subscriber-driven via PG logical replication protocol), not via pg_dump.

## Asks of Paco

1. Confirm Phase E fidelity:
   - All 9 gates PASS (subshell log + cross-check both green)
   - Measured downtime 16s within 5-30s envelope
   - pg_publication=0, pg_replication_slots=0 (clean baseline for F+G+H)
   - Container Up 40+ seconds, RestartCount 0
2. Acknowledge orchestrator-inactive observation (informational, not a B2b concern)
3. **Go for Phase F** -- schema bootstrap pg_dump + scp + psql, CiscoKid -> Beast.

## Standing rules in effect

- **Rule 1:** Phase E used local docker tooling on CiscoKid only; SSH carried single shell-command outputs. Compliant. Phase F's `scp` is the explicit Rule-1 carve-out (bulk schema SQL goes via SCP, not MCP; spec Pick 4 ratified this transport).
- **CLAUDE.md "Spec or no action":** no new amendments. Reference script adopted verbatim.
- **CLAUDE.md "Docker bypasses UFW":** the LAN bind is now active; UFW rule + pg_hba.conf scram-sha-256 + admin SCRAM password are the active layered controls.
- **CLAUDE.md deferred-restart pattern (memory feedback from D2):** applied here for the recreate; verification log in `/tmp/B2b_phase_e_verify.log` survives independent of SSH-session state.
- **Correspondence protocol:** this is paco_review #4 of 8 planned for B2b.

---

**File location:** `/home/jes/control-plane/docs/paco_review_b2b_phase_e_recreate.md` (untracked, matches /docs precedent)

-- PD
