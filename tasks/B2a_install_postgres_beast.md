# B2a -- Install PostgreSQL on Beast

**Owner:** Paco (spec) -> PD (execute)
**Status:** RATIFIED 2026-04-26 (Day 72) by CEO. Queued for PD execution.
**Date:** 2026-04-26 (Day 72)
**Origin:** P2 data plane, B2 split per Q3 + probe outcome
**Predecessor:** B2 investigation (commit `a23caf1`, `tasks/B2_investigation.md`)
**Successor:** B2b -- logical replication setup, depends on B2a complete
**Mirror:** iCloud `/AI/Santigrey/tasks/B2a_install_postgres_beast.md`

---

## Goal

Install a working PostgreSQL 16 instance on Beast (`sloan2`), version- and extension-matched to CiscoKid, ready to be configured as a logical replication subscriber in B2b.

---

## Seam between B2a and B2b (architecturally important)

**B2a delivers (this spec):**
- Running Postgres on Beast via Docker `pgvector/pgvector:pg16`
- Empty `controlplane` DB created
- `admin` superuser with REPLICATION role
- `vector` extension installed in `controlplane`
- 127.0.0.1:5432 binding
- Healthcheck passing
- NO schemas, NO tables, NO replication config, NO connection from/to CiscoKid

**B2b will deliver (separate spec, drafted after B2a ships):**
- CiscoKid: `wal_level=logical`, port rebind to LAN IP, `pg_hba.conf` entry, UFW rule
- Beast: schema bootstrap via `pg_dump --schema-only` (public + agent_os schemas) restored
- CiscoKid: `CREATE PUBLICATION` for tables in public + agent_os
- Beast: `CREATE SUBSCRIPTION` and replication slot active
- Initial data sync verified

**Why this seam:** B2a is fully independent of CiscoKid health. If CiscoKid is down or under maintenance, B2a still ships. B2b is one cohesive change touching both hosts together with controlled service ordering.

---

## Pre-flight (PD must verify all before changes)

1. `hostname` returns `sloan2` (confirms target = Beast)
2. `ls /var/lib/postgresql 2>&1` returns "No such file or directory" (greenfield)
3. `docker ps` succeeds (Docker daemon healthy)
4. `df -h /` shows `/dev/sda2` with >100GB free
5. `ss -tlnp | grep 5432` returns empty (no existing listener)

---

## Implementation

### Step 1 -- Create directory structure

```bash
mkdir -p /home/jes/postgres-beast/init
cd /home/jes/postgres-beast
```

### Step 2 -- Write `compose.yaml`

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: control-postgres-beast
    restart: unless-stopped
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-adminpass}
      POSTGRES_DB: controlplane
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin -d controlplane"]
      interval: 10s
      timeout: 5s
      retries: 10

volumes:
  pgdata:
```

### Step 3 -- Write `init/01-pgvector.sql`

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

This runs once on first container start (Docker postgres image entrypoint convention).

### Step 4 -- Password handling (matches CiscoKid pattern)

Default behavior: no `.env` file -> password defaults to `adminpass` (consistent with current CiscoKid posture, where probe confirmed no `.env` exists). Password rotation is a P5 credentials inventory concern, not a B2a concern.

If a different password is desired at install time:

```bash
echo 'POSTGRES_PASSWORD=<value>' > /home/jes/postgres-beast/.env
chmod 600 /home/jes/postgres-beast/.env
```

### Step 5 -- Pull image and start

```bash
cd /home/jes/postgres-beast
docker compose pull
docker compose up -d
```

### Step 6 -- Wait + verify

```bash
sleep 15
docker compose ps
docker exec control-postgres-beast psql -U admin -d controlplane -c 'SELECT version();'
docker exec control-postgres-beast psql -U admin -d controlplane -c 'SELECT extname, extversion FROM pg_extension;'
docker exec control-postgres-beast psql -U admin -d controlplane -c '\l'
```

---

## Acceptance gate (PD must verify all PASS before declaring shipped)

1. `docker ps --filter name=control-postgres-beast` shows running + healthy
2. `SELECT version()` returns "PostgreSQL 16.x" (16.11 preferred to match CiscoKid; any 16.x acceptable for logical replication)
3. `SELECT extname FROM pg_extension WHERE extname='vector'` returns one row, version 0.8.x
4. `\l` shows `controlplane` DB exists, owned by `admin`
5. `\du admin` shows superuser + `Replication=t`
6. `ss -tlnp` shows exactly one 5432 listener, bound to 127.0.0.1
7. `docker compose restart` returns container to healthy within 60s

---

## Rollback (if any acceptance test fails)

```bash
cd /home/jes/postgres-beast
docker compose down -v   # removes container + pgdata volume
rm -rf /home/jes/postgres-beast
```

This fully reverses B2a. Beast returns to pre-B2a state (no Postgres server, only client tools).

---

## Restart safety

This task touches **only Beast**. CiscoKid is not affected. No orchestrator downtime. No MCP fabric impact. No service ordering needed. Safe to run any time.

---

## PD-to-Paco report (P6 lesson: explicit deliverable)

PD writes a ship report to `/home/jes/postgres-beast/B2a_ship_report.md` on Beast at completion. Report MUST contain:

- All 7 acceptance gate results (PASS/FAIL each, with command output as evidence)
- Container ID and image digest (`docker inspect control-postgres-beast --format '{{.Id}} {{.Image}}'`)
- Disk usage of `pgdata` volume (`docker system df -v | grep pgdata`)
- md5sum of final `compose.yaml` and `init/01-pgvector.sql`
- Any deviations from this spec, with reasoning
- Time elapsed (start-to-healthy)

Then PD notifies Paco via session message with the report path.

Paco runs an independent verification gate against the same 7 acceptance items + spot-checks via fresh psql connection from a new shell session.

---

## Time estimate

15-25 minutes (includes Docker image pull on Beast's bandwidth; pgvector/pgvector:pg16 is ~400MB).

---

## What this enables

After B2a ships, Beast has a clean PostgreSQL 16 + pgvector ready. B2b can then:

- Bootstrap schemas via `pg_dump --schema-only` restore
- Configure CiscoKid as publisher (WAL change + ACLs)
- Create subscription on Beast
- Verify replication active

All without further infrastructure changes on Beast itself.
