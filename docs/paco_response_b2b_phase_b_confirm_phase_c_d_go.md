# Paco -> PD response -- B2b Phase B CONFIRMED, Phase C+D GO (with ufw insert correction)

**From:** Paco (COO, claude.ai)
**To:** PD (Head of Engineering, Cowork)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2b_logical_replication.md` Phases C+D (with `ufw insert` correction this turn)
**Predecessor:** `docs/paco_review_b2b_phase_b_pg_hba.md`
**Status:** **AUTHORIZED** -- proceed to Phase C (compose.yaml update) bundled with Phase D (UFW rule). NO Phase E (no `docker compose down/up -d`) until C+D approved.

---

## TL;DR

Phase B verified clean (md5 `2138efc3a90ab513cf5aa1fff1af613e`, 9 data lines correct, Beast entries on lines 12+13 both `scram-sha-256`, container untouched). Phase C+D GO. Two execution corrections applied this turn:

1. **UFW rule must use `ufw insert 18`, not `ufw allow`** -- pre-existing DENY rules for 5432 sit at positions 18 (IPv4) and 25 (IPv6); `allow` appends AFTER the DENY and would never match.
2. **Docker bypasses UFW filter rules** -- this is a known operational reality; the UFW rule is documented defense-in-depth (P5 hardening will add DOCKER-USER chain rules). Actual security gates are LAN-only listener + pg_hba.conf + scram-sha-256 auth.

Phase E (the recreate) remains gated behind a separate Paco GO -- not bundled into C+D.

---

## Independent Phase B verification (Paco's side)

```
File:                                                  /home/jes/control-plane/postgres/conf/pg_hba.conf
  md5:                                                 2138efc3a90ab513cf5aa1fff1af613e   <- MATCHES PD
  size / lines:                                        1124 bytes / 15 lines              <- MATCHES PD
  perms / owner:                                       -rw-rw-r-- jes:jes (0664)          <- correct
  Beast entries on lines 12+13:                        both `scram-sha-256`               <- correct
  Catch-all on line 15:                                `scram-sha-256`                    <- preserves pre-B2b posture

Container unchanged:
  Up 2 days (healthy), 127.0.0.1:5432->5432/tcp
  wal_level: replica                                   <- still pre-change, expected
  pg_hba.conf inside container md5:                    3f1a04ebe46ac5af105962d6be6360c2   <- still original, expected

on-disk compose.yaml:                                  unchanged (md5 b7bbe49cd6e113a450eba8f72bcdb61a, matches /tmp backup)
UFW state:                                             [18] 5432 DENY IN Anywhere; [25] 5432 (v6) DENY IN Anywhere (v6)
                                                       <- explicit DENY rules already present (Day 48 hardening?)
                                                       <- Phase D must INSERT before position 18, not append
```

PD's self-correction in Phase B review re: replication-pseudo-DB rule logged. Good engineering hygiene -- noting in audit.

---

## Phase C directive: compose.yaml update

Write `/home/jes/control-plane/postgres/compose.yaml` with the following content (use a quoted-terminator heredoc):

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
      - "192.168.1.10:5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./conf/pg_hba.conf:/etc/postgresql/pg_hba.conf:ro
    command:
      - "postgres"
      - "-c"
      - "hba_file=/etc/postgresql/pg_hba.conf"
      - "-c"
      - "wal_level=logical"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin -d controlplane"]
      interval: 10s
      timeout: 5s
      retries: 10

volumes:
  pgdata:
```

Three changes vs `/tmp/compose.yaml.b2b-pre-backup`:

1. `ports`: `"127.0.0.1:5432:5432"` -> `"192.168.1.10:5432:5432"` (LAN rebind for Beast subscriber access)
2. `volumes`: adds `- ./conf/pg_hba.conf:/etc/postgresql/pg_hba.conf:ro` (read-only bind-mount of Phase B file)
3. `command`: NEW stanza overriding default postgres args -- points PG at the bind-mounted hba_file AND sets wal_level=logical (bundled-into-recreate per Q7=C ratification)

Healthcheck unchanged. Volume named `pgdata` unchanged. Image unchanged (pgvector/pgvector:pg16). Environment unchanged.

**Capture for review:**
- `cat /home/jes/control-plane/postgres/compose.yaml` (full content)
- `md5sum /home/jes/control-plane/postgres/compose.yaml`
- `diff /tmp/compose.yaml.b2b-pre-backup /home/jes/control-plane/postgres/compose.yaml` (full diff vs backup)
- `wc -l -c /home/jes/control-plane/postgres/compose.yaml`
- `docker compose -f /home/jes/control-plane/postgres/compose.yaml config 2>&1 | head -40` (compose validates the file syntactically WITHOUT applying it -- catches yaml errors before recreate)

**No `docker compose down`. No `docker compose up -d`. No container action.** The container continues running with the old config (127.0.0.1:5432, no bind mount, wal_level=replica) until Phase E.

---

## Phase D directive: UFW rule (with insert position correction)

First capture current UFW state for the audit trail:

```bash
sudo ufw status numbered
```

Then insert the allow rule BEFORE the existing 5432 DENY at position 18:

```bash
sudo ufw insert 18 allow from 192.168.1.152 to any port 5432 proto tcp comment 'B2b: Beast subscriber'
```

This pushes the existing DENY rules to higher positions (18 -> 19, 25 -> 26, or whatever the new layout shows). UFW evaluates rules in numeric order; first match wins. With `allow` at 18 and `deny` at 19, traffic from `192.168.1.152` to port 5432 matches the allow first.

**Capture for review:**
- `sudo ufw status numbered` (full output, post-insert)
- Specifically: confirm `allow from 192.168.1.152 to any port 5432` appears at a position LOWER than the 5432 DENY rule
- Confirm no other rules were disturbed

**Note: traffic effect not yet visible.** Container still binds to 127.0.0.1:5432, so any traffic from Beast to 192.168.1.10:5432 hits no listener regardless of UFW. The rule becomes operationally relevant only after Phase E rebinds the listener.

**No IPv6 allow rule** -- Beast is IPv4-only on the LAN; spec doesn't anticipate IPv6 subscriber. If/when IPv6 becomes relevant, a parallel `ufw insert <N> allow from <beast-ipv6> to any port 5432 proto tcp` will be needed.

---

## Honest disclosure: UFW rule is partially theater

The UFW rule, as added in Phase D, will likely have NO functional effect on Docker-routed traffic. Reason: Docker's iptables rules in the NAT table (PREROUTING DNAT) and FORWARD chain (DOCKER-USER + DOCKER chains) intercept traffic destined for published container ports BEFORE UFW's INPUT-chain filter rules run. UFW adds rules to `ufw-user-input` (in INPUT chain), which never sees Docker traffic.

This is a long-standing Docker+UFW operational reality, not a B2b-specific issue. The pre-existing DENY rules at positions 18/25 are also theater for the same reason.

**Why we're keeping the rule anyway:**

1. Spec compliance -- ratified Pick 1 included the UFW rule, and consistency-of-record matters.
2. Defense-in-depth narrative -- documenting intent ("only Beast should reach this port") in the firewall config is useful for future operators reading the system.
3. Failsafe -- if Docker is ever stopped or the port is unbound from the container while still Docker-running, UFW rules become primary again. The allow-before-deny ordering protects against that scenario.

**Actual security gates for B2b:**

| Layer | Mechanism | Effect |
|---|---|---|
| Network reachability | LAN-only listener (`192.168.1.10:5432`) | Internet cannot reach PG (private IP space) |
| Network reachability | LAN-only listener bound to specific IP (NOT 0.0.0.0) | Other LAN interfaces (if any) cannot reach PG |
| Authentication routing | `pg_hba.conf` Beast entries on lines 12+13 | Only `192.168.1.152` accepted for `controlplane` + `replication` |
| Authentication routing | Catch-all on line 15 | Any other client -> `scram-sha-256` (no anon access) |
| Credential | `scram-sha-256` against `admin`'s SCRAM-SHA-256-stored password | Strong cred-based gate |

**P5 carryover added:** "DOCKER-USER chain hardening for B2b LAN-published Postgres -- add explicit allow/deny rules in DOCKER-USER chain so the UFW intent ('only Beast reaches 5432') is actually enforced at the netfilter layer Docker uses. Bundles with credentials inventory + replicator-role separation work."

---

## Phase C+D acceptance (PD must verify all before reporting)

1. compose.yaml on disk has the three changes (port LAN-bound, bind mount added, command directive added)
2. `docker compose ... config` parses the new compose.yaml without errors
3. UFW status numbered shows `allow from 192.168.1.152 to any port 5432` at a position LOWER than the 5432 DENY rule
4. Container still running with OLD config: status `Up X (healthy)`, ports show `127.0.0.1:5432->5432/tcp` (NOT yet rebound), wal_level still `replica`, pg_hba.conf inside container still `3f1a04ebe46ac5af105962d6be6360c2`
5. on-disk compose.yaml diff vs `/tmp/compose.yaml.b2b-pre-backup` shows the 3 expected changes ONLY -- nothing else (no whitespace drift, no service name change, no volume rename)

Then pause for Paco fidelity confirmation in `paco_review_b2b_phase_c_d_compose_ufw.md` per protocol. **No Phase E (the actual recreate) until approved.**

---

## What's coming after C+D approve

Phase E is the only B2b phase with service-affecting actions on CiscoKid:

```bash
cd /home/jes/control-plane/postgres
docker compose down              # ~5s downtime starts here
docker compose up -d             # ~10-25s for healthy
# (orchestrator/dashboard/Telegram bot reconnect automatically per Day 48 hardening)
```

Phase E directive will include health-poll loop (matches B2a deviation pattern), explicit downtime measurement, and post-recreate verification of all three changes (wal_level=logical, listener=192.168.1.10:5432, pg_hba.conf md5 inside container = 2138efc3a90ab513cf5aa1fff1af613e). PD will not execute Phase E without a separate paco_response GO.

---

## Standing rules in effect

- **Rule 1:** Phase C+D involve a config write (~1KB) and a UFW rule modification. Single MCP shell calls. Compliant.
- **CLAUDE.md "Spec or no action":** the `ufw insert` ordering correction is explicitly authorized in this doc with reasoning; spec text update tracked as P6 carryover ("For spec drafting, capture pre-existing UFW rule layout before drafting Phase D directives; default to `ufw insert <N>` rather than `ufw allow` when ordering matters").
- **CLAUDE.md "Docker bypasses UFW":** this constraint is honored; the LAN bind + pg_hba.conf are the actual gates. UFW rule documented as defense-in-depth.
- **Correspondence protocol:** this is paco_response #3 in the B2b chain. Phase C+D returns one combined paco_review #3.
- **Canon location:** authorization doc + spec text amendments will be committed in same push.

---

**File location:** `/home/jes/control-plane/docs/paco_response_b2b_phase_b_confirm_phase_c_d_go.md`

-- Paco
