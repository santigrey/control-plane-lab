# B2 Investigation Report

**Owner:** Paco
**Date:** 2026-04-26 (Day 72)
**Probe scope:** Shallow -- Postgres state on CiscoKid + Beast, network reachability, disk capacity, replication readiness
**Goal:** Surface facts needed for B2 spec drafting (Postgres logical replication CiscoKid -> Beast)
**Probe artifacts:** `/tmp/b2_probe_ciscokid.txt`, `/tmp/b2_probe_ciscokid_v2.txt`, `/tmp/b2_probe_beast.txt`

---

## TL;DR

- **CiscoKid Postgres exists** (Docker `control-postgres`, pgvector/pgvector:pg16, PG 16.11). Three config changes needed for replication to work.
- **Beast Postgres ABSENT** (only client tools installed). 4 TB free, Docker available.
- **Q3 resolves to split:** B2a = install Postgres on Beast, B2b = configure logical replication.
- **Four new structural decisions surfaced** for CEO measure (Q4-Q7) before spec drafting.

---

## CiscoKid -- current Postgres state

### Container
- Image: `pgvector/pgvector:pg16` (PostgreSQL 16.11 on Debian 12)
- Container: `control-postgres`, healthy, restart unless-stopped
- Compose file: `/home/jes/control-plane/postgres/compose.yaml`
- Volume: `pgdata` (Docker named volume)
- **Port mapping: `127.0.0.1:5432:5432`** -- LAN-invisible by design (per Day 48 security memory: PostgreSQL must be rebound to localhost because Docker bypasses UFW iptables)
- Healthcheck: `pg_isready -U admin -d controlplane`

### Database structure
- **Single DB: `controlplane`** (85 MB on disk)
- Multi-schema reality (Q2 "agent-platform only" is a within-DB scope question, not a DB selection):
  - `public` schema -- 12 tables: `agent_tasks`, `messages`, `chat_history`, `memory` (12 rows but 73 MB -- pgvector embeddings), `iot_audit_log`, `iot_security_events`, `job_applications`, `pending_events`, `tasks`, `user_profile`, plus 2 `_retired_*` tables
  - `mercury` schema -- 4 tables: `ai_predictions` (475 rows), `trades` (142), `market_snapshots` (30), `daily_performance` (19) -- autonomous trading agent state
  - `agent_os` schema -- 1 table: `documents` (0 rows, 2.4 MB allocated)

### Replication readiness (live config)
| Setting | Current value | Required for B2 | Action |
|---|---|---|---|
| `wal_level` | `replica` | `logical` | **Change required** (restart) |
| `max_wal_senders` | 10 | >=1 | OK |
| `max_replication_slots` | 10 | >=1 | OK |
| `listen_addresses` | `*` (inside container) | reachable from Beast | Container is fine; **Docker port mapping is the limiter** |
| `shared_preload_libraries` | (empty) | n/a for logical rep | OK |
| `wal_compression` | off | optional | Could enable to reduce LAN traffic |

### Roles
- `admin` -- superuser + `rolreplication=t` -- already capable of being publisher
- `alexandra_user` -- no replication role (correct; app user)
- 0 publications exist, 0 replication slots active -- clean slate

### Extensions in `controlplane`
- `plpgsql` 1.0
- `vector` 0.8.1 (pgvector)

---

## Beast -- current Postgres state

### Server: ABSENT
- No `/var/lib/postgresql`, no `/opt/postgresql`
- No postgresql systemd unit (`Unit postgresql.service could not be found`)
- No postgres-named Docker containers (running or stopped)
- 0 listeners on TCP/5432

### Client tools: present
- `/usr/bin/psql` -- postgresql-client-14 v14.22
- `libpq5` 14.22

### apt availability
- `postgresql` 14+238 (Ubuntu 22.04 jammy main) -- only PG 14 via apt; would need PGDG repo for PG 16 to match CiscoKid version

### Capacity
- `/dev/sda2` mounted `/`: 4.4T total, 4.0T free, 4% used -- ample
- Docker installed (`/usr/bin/docker`), 0 running containers

### Other
- Hostname: `sloan2`
- Architecture: x86_64
- Tailscale: NOT installed on Beast -- replication will use plain LAN (both hosts on 192.168.1.0/24)

---

## Network reachability

| Path | Result | Note |
|---|---|---|
| CiscoKid -> Beast TCP/22 | OK | SSH path confirmed |
| CiscoKid -> Beast TCP/5432 | timeout | Expected -- no Postgres on Beast yet |
| Beast -> CiscoKid TCP/5432 | (untested, but blocked by design) | CiscoKid Postgres bound to 127.0.0.1 only |

---

## Implications for B2 spec

### Q3 resolved
Decompose into:
- **B2a** -- Install Postgres on Beast (greenfield; no migration needed)
- **B2b** -- Configure logical replication CiscoKid -> Beast (publication + subscription + slot)

B2a is independent and can ship first. B2b depends on B2a + Q4-Q7 decisions.

### Surfaced for CEO measure (Q4 - Q7)

**Q4 -- Scope mapping in single-DB multi-schema reality.** "Agent-platform only" (Q2=B from prior turn) cannot be done at DB level because `controlplane` is the only meaningful DB. Scope must be expressed at schema or table level.

**Q5 -- Replica install path on Beast.** Docker (matches CiscoKid pattern) vs apt + PGDG (Postgres 16 from PostgreSQL Global Development Group repo, since Ubuntu only ships 14).

**Q6 -- Network exposure for replication traffic.** CiscoKid Postgres is currently 127.0.0.1-only. Three options to make it reachable from Beast.

**Q7 -- WAL level change timing.** Changing `wal_level` from `replica` to `logical` requires Postgres restart, which means orchestrator + agent task pipeline downtime. When/how do we accept that.

(Detailed options in chat -- this file is the fact base, the chat is the decision surface.)
