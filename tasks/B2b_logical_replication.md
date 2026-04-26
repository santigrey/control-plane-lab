# B2b -- Logical Replication CiscoKid -> Beast

**Owner:** Paco (spec) -> PD (execute)
**Status:** DRAFT pending CEO ratification
**Date:** 2026-04-26 (Day 72)
**Origin:** P2 data plane, B2 split successor (B2a complete)
**Predecessors:**
- `tasks/B2a_install_postgres_beast.md` (RATIFIED + SHIPPED + CLOSED) -- subscriber endpoint exists on Beast
- `docs/paco_response_b2a_independent_gate_pass_close.md` -- B2a closed and verified
- B2 investigation report (commit `a23caf1`, `tasks/B2_investigation.md`) -- Q4-Q7 ratified picks

**Successor:** Atlas-on-Beast build (per CHARTERS_v0.1 Charter 5 Build status revision; depends on B2b + B1 landing)

---

## TL;DR

Configure logical replication from CiscoKid (publisher, PG 16.11) to Beast (subscriber, PG 16.13) for the `controlplane.public` and `controlplane.agent_os` schemas. `mercury` schema (trading agent) deliberately excluded per Q4=C ratification. Achieves Atlas's hard prerequisite: working memory available on Beast via continuously-replicated copy of CiscoKid's authoritative state.

Bundles four CiscoKid changes that all require the Postgres restart per Q7=C ratification: `wal_level=logical`, port rebind to LAN, `pg_hba.conf` entry for Beast, UFW rule. Single ~5-30s downtime window for CiscoKid Postgres; orchestrator reconnects automatically.

Four structural picks flagged below for CEO ratification before PD executes.

---

## Architecture

```
   CiscoKid (publisher, PG 16.11)              Beast (subscriber, PG 16.13)
   192.168.1.10:5432                            192.168.1.152:5432 (localhost-only)
   ===========================                  ============================
   wal_level=logical                            (no special config required)
   pg_hba.conf: 192.168.1.152/32 md5            
   UFW: allow 5432 from 192.168.1.152/32        
                                                
   PUBLICATION controlplane_pub:                SUBSCRIPTION controlplane_sub:
     - public.* (12 tables incl. memory)        - connects to publisher LAN endpoint
     - agent_os.* (1 table)                     - copies initial state
     - mercury.* EXCLUDED                       - streams ongoing changes
                                                
   pg_replication_slots:                        pg_subscription:
     controlplane_sub  (active)                  controlplane_sub (status=r)
```

**Replication direction:** unidirectional (CiscoKid -> Beast). Beast is read-only relative to replicated tables; writes still go to CiscoKid. Atlas (when built) reads from Beast for memory queries to offload pgvector workload from CiscoKid.

---

## Pre-flight (PD must verify all before changes)

### Beast side
1. `docker ps --filter name=control-postgres-beast` shows running + healthy (B2a state intact)
2. `docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT version();"` returns PG 16.x
3. `docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT extname FROM pg_extension WHERE extname='vector';"` returns vector
4. Beast has `psql` client available on host (verified Day 70: postgresql-client-14 v14.22)
5. Beast can `ping -c 2 192.168.1.10` successfully

### CiscoKid side
6. `docker ps --filter name=control-postgres` shows running + healthy
7. `docker exec control-postgres psql -U admin -d controlplane -tAc "SHOW wal_level;"` returns `replica` (current state, will change to `logical`)
8. `docker exec control-postgres psql -U admin -d controlplane -tAc "SELECT count(*) FROM information_schema.schemata WHERE schema_name IN ('public','agent_os','mercury');"` returns 3
9. UFW status check: `sudo ufw status numbered`
10. Backup current compose.yaml: `cp /home/jes/control-plane/postgres/compose.yaml /tmp/compose.yaml.b2b-backup`

---

## Picks flagged for CEO ratification

**Pick 1 -- pg_hba.conf approach.** Two options:
- **Option A (inline edit):** sudo-edit `/var/lib/docker/volumes/control-plane_postgres_data/_data/pg_hba.conf` directly, then `pg_reload_conf()`.
- **Option B (bind mount, Paco recommendation):** add custom `pg_hba.conf` under `/home/jes/control-plane/postgres/conf/` and bind-mount in compose.yaml. Config-as-code, version-tracked, mirrors B2a's `init/` pattern.

Paco picks **B**: matches the spec-template/config-as-code pattern from B2a; pg_hba.conf becomes part of the repo; future changes are diff-trackable.

**Pick 2 -- Service ordering during restart.** Two options:
- **Option A (accept downtime, Paco recommendation):** Brief CiscoKid Postgres downtime (~5-30s) during `docker compose up -d`. Orchestrator + dashboard + Telegram bot reconnect automatically (they're all designed to retry).
- **Option B (graceful):** Stop orchestrator + dependent services first, then restart Postgres, then restart dependents in order.

Paco picks **A**: simpler, matches normal Postgres ops pattern; dependents already handle reconnects per Day 48 hardening; net session-disruption impact is on-the-order-of-seconds.

**Pick 3 -- Subscription password handling.** Two options:
- **Option A (use admin/adminpass):** Subscription stores `password=adminpass` in `pg_subscription`. Matches publisher; consistent with B2a posture.
- **Option B (dedicated replicator role):** Create separate `replicator` role on CiscoKid with REPLICATION attribute only (no superuser); subscription uses replicator credentials.

Paco picks **A for B2b, with rotation as a P5 follow-up**: consistent with B2a; B2b is the integration step, not the security-hardening step. Replicator-role separation belongs in a post-B2b security pass alongside the broader credentials inventory work (P5 carryover).

**Pick 4 -- Schema bootstrap transport.** Three options:
- **Option A (pg_dump + scp + psql, Paco recommendation):** `pg_dump --schema-only` on CiscoKid -> SCP to Beast -> `psql < schema.sql` on Beast. Standard idiom.
- **Option B (pipe over SSH):** `pg_dump --schema-only | ssh beast 'docker exec -i control-postgres-beast psql ...'`. One-shot, no intermediate file.
- **Option C (`homelab_file_transfer` via D3 tool):** would require D3 to ship first.

Paco picks **A**: standard pattern; produces a tangible audit artifact (the schema.sql file with md5sum); diff-friendly if we need to compare schemas later. SCP is ad-hoc bulk transfer, Rule-1-compliant (not via MCP).

If CEO ratifies these 4 picks as-is, PD proceeds. Any pick CEO wants flipped -> spec amendment.

---

## Implementation

### Phase A -- CiscoKid pre-change capture

```bash
cd /home/jes/control-plane/postgres
cp compose.yaml /tmp/compose.yaml.b2b-pre-backup
mkdir -p conf
# Capture current pg_hba.conf from inside container as starting point:
docker exec control-postgres cat /var/lib/postgresql/data/pg_hba.conf > /tmp/pg_hba.conf.original
```

### Phase B -- Build new pg_hba.conf at conf/pg_hba.conf

Contents (replicates Postgres defaults + adds Beast entry):
```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
local   replication     all                                     trust
host    replication     all             127.0.0.1/32            trust
host    replication     all             ::1/128                 trust
# B2b: Beast subscriber for logical replication (added 2026-04-26 Day 72)
host    controlplane    admin           192.168.1.152/32        md5
host    replication     admin           192.168.1.152/32        md5
```

### Phase C -- Update compose.yaml

Three changes:
1. Port rebind: `127.0.0.1:5432:5432` -> `192.168.1.10:5432:5432`
2. Bind-mount pg_hba.conf: add `- ./conf/pg_hba.conf:/etc/postgresql/pg_hba.conf:ro` to volumes (and add `command: postgres -c hba_file=/etc/postgresql/pg_hba.conf -c wal_level=logical` to service)
3. Healthcheck unchanged.

(Full new compose.yaml content delivered inline by PD during execution; PD writes via heredoc and shows diff vs backup before recreate.)

### Phase D -- UFW rule for Beast

```bash
sudo ufw allow from 192.168.1.152 to any port 5432 proto tcp comment 'B2b: Beast subscriber'
sudo ufw status numbered  # verify added
```

### Phase E -- Recreate CiscoKid Postgres with new config

```bash
cd /home/jes/control-plane/postgres
docker compose down              # stops existing container, preserves volume
docker compose up -d             # recreates with new compose.yaml + pg_hba.conf bind mount + new command line

# Health-poll (60s cap; restart-not-init, faster path)
for i in $(seq 1 12); do
  status=$(docker inspect control-postgres --format '{{.State.Health.Status}}' 2>/dev/null || echo 'pending')
  echo "[poll $i/12] health=$status"
  if [ "$status" = "healthy" ]; then break; fi
  sleep 5
done

# Verify config landed
docker exec control-postgres psql -U admin -d controlplane -tAc "SHOW wal_level;"             # expect: logical
docker exec control-postgres psql -U admin -d controlplane -tAc "SHOW listen_addresses;"     # expect: *
ss -tlnp | grep 5432                                                                          # expect: 192.168.1.10:5432
sudo ufw status | grep 5432                                                                   # expect: allowed from 192.168.1.152
```

### Phase F -- Schema bootstrap (CiscoKid -> Beast)

```bash
# On CiscoKid: dump schema-only for public + agent_os (NOT mercury)
docker exec control-postgres pg_dump -U admin -d controlplane \
  --schema-only \
  --schema=public --schema=agent_os \
  --no-owner --no-privileges \
  > /tmp/controlplane_schema.sql
md5sum /tmp/controlplane_schema.sql
wc -l /tmp/controlplane_schema.sql

# Verify excluded mercury:
grep -c 'mercury' /tmp/controlplane_schema.sql || echo 'mercury_excluded_OK'

# Transfer to Beast
scp /tmp/controlplane_schema.sql jes@192.168.1.152:/tmp/
ssh jes@192.168.1.152 'md5sum /tmp/controlplane_schema.sql'   # match CiscoKid

# On Beast: install schema (vector extension already present from B2a)
ssh jes@192.168.1.152 'docker cp /tmp/controlplane_schema.sql control-postgres-beast:/tmp/'
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -f /tmp/controlplane_schema.sql 2>&1 | tail -20'

# Verify schemas on Beast
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -c "\dn"'
# expect: public + agent_os listed; mercury absent
```

### Phase G -- Publisher setup (CiscoKid)

```bash
docker exec control-postgres psql -U admin -d controlplane -c \
  "CREATE PUBLICATION controlplane_pub FOR TABLES IN SCHEMA public, agent_os;"

# Verify
docker exec control-postgres psql -U admin -d controlplane -c \
  "SELECT pubname, schemaname FROM pg_publication_tables;" | head -20
docker exec control-postgres psql -U admin -d controlplane -c \
  "SELECT pubname, puballtables, pubinsert, pubupdate, pubdelete FROM pg_publication;"
```

### Phase H -- Subscriber setup (Beast)

```bash
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -c \
  "CREATE SUBSCRIPTION controlplane_sub \
   CONNECTION '\''host=192.168.1.10 port=5432 dbname=controlplane user=admin password=adminpass'\'' \
   PUBLICATION controlplane_pub \
   WITH (copy_data = true);"'

# Watch initial sync (poll, 5min cap for ~85MB DB)
for i in $(seq 1 60); do
  state=$(ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT srsubstate FROM pg_subscription_rel LIMIT 1;"' 2>/dev/null)
  echo "[sync-poll $i/60] state=$state (r=ready, s=synchronized, d=copying, i=initialize)"
  if [ "$state" = "r" ]; then echo 'INITIAL SYNC COMPLETE'; break; fi
  sleep 5
done
```

### Phase I -- Cleanup

```bash
rm /tmp/controlplane_schema.sql
ssh jes@192.168.1.152 'rm /tmp/controlplane_schema.sql; docker exec control-postgres-beast rm /tmp/controlplane_schema.sql'
```

---

## Acceptance gate (PD must verify all PASS)

1. **CiscoKid wal_level=logical:** `SHOW wal_level` returns `logical`
2. **CiscoKid LAN listener:** `ss -tlnp` shows exactly one `192.168.1.10:5432` listener (NOT 127.0.0.1:5432, NOT 0.0.0.0:5432)
3. **UFW rule active:** `sudo ufw status` shows `5432/tcp ALLOW IN from 192.168.1.152`
4. **pg_hba.conf via bind mount:** `docker exec control-postgres cat /etc/postgresql/pg_hba.conf` shows the Beast entry; `SHOW hba_file` returns `/etc/postgresql/pg_hba.conf`
5. **Beast can reach CiscoKid Postgres:** `ssh jes@192.168.1.152 'PGPASSWORD=adminpass psql -h 192.168.1.10 -U admin -d controlplane -c "SELECT 1;"'` returns 1 (rows)
6. **Beast schemas correct:** `\dn` on Beast lists `public` and `agent_os` only; `mercury` absent
7. **Publication exists:** CiscoKid `pg_publication` shows `controlplane_pub`; `pg_publication_tables` lists tables in `public` + `agent_os`
8. **Subscription active:** Beast `pg_subscription` shows `controlplane_sub`; all rows in `pg_subscription_rel` have `srsubstate = 'r'` (ready)
9. **Replication slot active:** CiscoKid `pg_replication_slots` shows slot `controlplane_sub`, `active = t`, with non-null `confirmed_flush_lsn`
10. **Row count parity (key tables):**
    - `agent_tasks`: count(Beast) == count(CiscoKid)
    - `messages`: count(Beast) == count(CiscoKid)
    - `memory`: count(Beast) == count(CiscoKid) (the 900+ pgvector embeddings, ~73MB)
11. **Smoke test live replication:** Insert a test row on CiscoKid `INSERT INTO agent_tasks (...) VALUES ('b2b_smoke_test', ...)`. Wait 10 seconds. Verify it appears on Beast. Delete the test row on CiscoKid. Verify it disappears on Beast.
12. **Restart safety on subscriber:** `ssh jes@192.168.1.152 'cd /home/jes/postgres-beast && docker compose restart'`. Verify subscription resumes (state goes `d` -> `s` -> `r` automatically; replication slot remains active on CiscoKid).

---

## Rollback

If any acceptance test fails or post-ship issue requires revert:

```bash
# On Beast: drop subscription (stops replication, releases slot)
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -c "DROP SUBSCRIPTION controlplane_sub;"'

# On CiscoKid: drop publication (clean up)
docker exec control-postgres psql -U admin -d controlplane -c 'DROP PUBLICATION controlplane_pub;'

# On Beast: drop replicated schemas (or leave; they're empty after subscription drop)
# (optional, only if doing full reset)

# On CiscoKid: revert compose.yaml + pg_hba.conf
cd /home/jes/control-plane/postgres
cp /tmp/compose.yaml.b2b-pre-backup compose.yaml
rm -rf conf/   # remove the bind-mount source
docker compose down
docker compose up -d
# (CiscoKid Postgres back to 127.0.0.1:5432, wal_level=replica)

# On CiscoKid: revoke UFW rule
sudo ufw delete allow from 192.168.1.152 to any port 5432
```

Beast retains its B2a state (Postgres + pgvector + empty controlplane DB on 127.0.0.1:5432). Full B2a rollback would be a separate operation per `tasks/B2a_install_postgres_beast.md` rollback section.

---

## Restart safety

**This task DOES involve CiscoKid Postgres downtime.** Expected: ~5-30 seconds during `docker compose up -d` (Phase E).

During downtime:
- Orchestrator FastAPI on `:8000` will return errors for any DB-touching endpoints (briefly)
- Telegram bot will queue messages to retry
- Dashboard will show transient connection errors
- Cowork's `homelab-mcp.service` is unaffected (doesn't depend on Postgres)

All three (orchestrator, dashboard, Telegram bot) auto-reconnect on Postgres availability per Day 48 hardening. Net session-disruption impact: seconds.

If CEO wants zero-downtime: Pick 2 Option B (graceful sequencing) is available -- spec amendment + ~2-3 minute longer execution.

---

## PD-to-Paco report (per P6 protocol)

PD writes ship report to `/home/jes/control-plane/postgres/B2b_ship_report.md` on CiscoKid (where the publisher lives; matches B2a's pattern of report-on-target-host) at completion. Report MUST contain:

- All 12 acceptance gate results (PASS/FAIL with command output evidence)
- CiscoKid downtime measured (start-of-`down` to first-healthy after `up -d`)
- Replication slot LSN progression (pre-bootstrap, post-bootstrap, after smoke test)
- Row count parity table for all 13 tables in public + agent_os
- Initial sync wall time + bytes transferred
- Any deviations from spec, with reasoning
- pg_hba.conf md5sum + compose.yaml md5sum (final post-B2b values)
- Time elapsed (Phase A start to acceptance gate complete)

PD also writes a `paco_review_b2b_*.md` doc per phase (or one per logical chunk) to `/docs/` for fidelity gating, matching the B2a review pattern. Final close: `paco_response_b2b_independent_gate_pass_close.md`.

---

## Time estimate

- Phases A-D (config prep): 5-10 min
- Phase E (recreate + verify): 2-5 min (with downtime ~5-30s)
- Phase F (schema bootstrap): 2-5 min
- Phase G (publication): <1 min
- Phase H (subscription + initial sync): 2-10 min (depends on data size; 73MB memory table is the bulk)
- Acceptance gate run: 5-10 min
- Total: 20-40 min

---

## What this enables

- **Atlas build (Charter 5).** Beast has a continuously-replicated working memory copy. Atlas reads from Beast for memory queries (offloads pgvector from CiscoKid), writes to CiscoKid for new entries (which then replicate to Beast).
- **B1 (MinIO on Beast).** Independent of B2b but adjacent; once B2b lands, Beast is a more complete data tier.
- **Mercury isolation.** Trading agent state stays only on CiscoKid (mercury schema explicitly excluded from publication). If/when Mercury's data needs to scale, separate replication topology can be designed without touching the public/agent_os pair.
- **Disaster recovery posture.** Beast becomes a warm standby for the public + agent_os tier. If CiscoKid Postgres goes hard down, Beast's replicated copy is the recovery source.
- **Read scaling.** Future read-heavy workloads (e.g., embedding search) can target Beast instead of CiscoKid, freeing CiscoKid for control-plane work.

---

## Standing rules in effect

- **Rule 1 (MCP fabric is for control, not bulk data):** Schema bootstrap uses SCP (Phase F). Initial subscription data sync uses native Postgres logical replication protocol. Both are NOT via MCP. Compliant.
- **CLAUDE.md "Docker bypasses UFW. Bind to localhost in compose.yaml":** B2b deliberately rebinds CiscoKid Postgres to LAN for cross-host access. The UFW rule + pg_hba.conf md5 auth provide compensating controls. The bind shifts from `127.0.0.1:5432` to `192.168.1.10:5432` (NOT `0.0.0.0:5432`), so external (non-LAN) traffic still cannot reach the listener.
- **CLAUDE.md "Spec or no action":** PD flags any further deviations beyond the 4 ratified picks.
- **Correspondence protocol:** PD writes per-phase `paco_review_b2b_*.md` docs; Paco writes `paco_response_b2b_*.md` rulings. Final close lands at `paco_response_b2b_independent_gate_pass_close.md` after Paco runs the independent gate.

---

## Asks of CEO

1. Ratify the 4 picks (or revise any).
2. Confirm acceptable downtime for CiscoKid Postgres (~5-30s) during Phase E. If unacceptable, flip Pick 2 to Option B (graceful sequencing).
3. On ratification: relay this spec path to PD via Cowork; PD begins Phase A.

---

**File location:** `/home/jes/control-plane/tasks/B2b_logical_replication.md` (canonical on CiscoKid + GitHub origin/main per canon-flip)

-- Paco
