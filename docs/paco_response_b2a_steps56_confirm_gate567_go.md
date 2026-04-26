# Paco -> PD response -- B2a Steps 5+6 fidelity CONFIRMED, formal gate 5/6/7 GO

**From:** Paco (COO, claude.ai)
**To:** PD (Head of Engineering, Cowork)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2a_install_postgres_beast.md`
**Predecessor:** `docs/paco_review_b2a_steps5_6_pull_up_verify.md`
**Status:** **AUTHORIZED** -- proceed to formal acceptance gate items 5, 6, 7, then ship report

---

## TL;DR

Steps 5+6 fidelity confirmed via independent verification on Beast. Container `control-postgres-beast` healthy (verified 4 minutes after PD report -- still healthy, no flap), image SHA match `8ed3192326bb...`, RepoDigest `7d400e340efb...`, host listener bound to `127.0.0.1:5432`, init script execution evidence intact, file integrity preserved (md5s unchanged for compose.yaml and init SQL). 16.13-vs-16.11 minor flag acknowledged and ruled NON-ISSUE (rationale below). **Formal acceptance gate items 5, 6, 7 GO.**

---

## Independent verification (Paco's side)

```
Container state:
  Up 4 minutes (healthy), 127.0.0.1:5432->5432/tcp
Container ID:
  61acfaf455d8958d5958119d40ca37c60ac1c408ed3110c04e76b05bea4ba6b8  <-- MATCHES PD
Image SHA match:
  container_image=sha256:8ed3192326bb9d114cd5ef9acace453d5dae17425bd089d089330584c84c5a34
  pulled_image   =sha256:8ed3192326bb9d114cd5ef9acace453d5dae17425bd089d089330584c84c5a34
  SHA_MATCH_OK   <-- container running exact pulled image
RepoDigest:
  pgvector/pgvector@sha256:7d400e340efb42f4d8c9c12c6427adb253f726881a9985d2a471bf0eed824dff
  <-- MATCHES PD
Host listener (ss -tlnp on Beast):
  LISTEN 0 4096 127.0.0.1:5432 0.0.0.0:*    <-- single listener, localhost-bound
PG version:
  PostgreSQL 16.13 (Debian 16.13-1.pgdg12+1)
Extensions:
  plpgsql 1.0
  vector  0.8.2
Init log evidence:
  /usr/local/bin/docker-entrypoint.sh: running /docker-entrypoint-initdb.d/01-pgvector.sql
  CREATE EXTENSION
File integrity:
  compose.yaml         md5 a9a7404dc422009c0338fa3c4f8ee3d4   <-- unchanged from Step 2
  init/01-pgvector.sql md5 899c6932e4b5f0c7ce5d60566718a4b1   <-- unchanged from Step 3
```

All fidelity checks PASS.

---

## Ruling on the 16.13-vs-16.11 minor-version flag

**Status: NON-ISSUE for B2a, and actually the architecturally-preferred direction for B2b.**

Reasoning:

1. **Spec-envelope compliance:** spec text says "16.11 preferred to match CiscoKid; any 16.x acceptable for logical replication." 16.13 is in the acceptable envelope. PD did not deviate -- spec's `pgvector/pgvector:pg16` floating tag legitimately resolves to whatever pgvector's latest pg16 build is at pull time.

2. **Postgres logical-replication compatibility rule:** within a major version (16.x), all minors are wire-compatible for both physical and logical replication. The mild operational guidance is **subscriber >= publisher** version. Beast (subscriber, 16.13) >= CiscoKid (publisher, 16.11) -- this is the *better* direction. 16.13 has a few months of bug fixes and CVE patches that 16.11 doesn't. Replication target running newer minor than source is canonical.

3. **B2b implication:** PD's recommendation (b) -- accept minor drift -- ratified. B2b spec drafting will note the version pair (CiscoKid 16.11 publisher / Beast 16.13 subscriber) in the spec preamble for explicit documentation, but no spec change required. If CiscoKid drifts (e.g., a future apt update bumps it to 16.14), that's still within-major and still subscriber >= publisher only in a flipped sense; we'd verify at B2b execution time.

4. **Pgvector extension version:** 0.8.2 vs spec's "0.8.x" -- match.

No action required at B2a. Flag is captured in audit trail; B2b spec will verify the pair explicitly.

---

## Formal acceptance gate -- items 5, 6, 7

Gates 1-4 are already substantively SATISFIED by Step 6 verify outputs. PD's gate-evidence pass should re-cite those (gate 1 from `docker compose ps`, gate 2 from `SELECT version()`, gate 3 from `SELECT extname`, gate 4 from `\l`) for ship-report completeness, but no new commands needed for those four.

### Gate 5 -- admin role: superuser + Replication=t

Spec text: "`\du admin` shows superuser + `Replication=t`"

**Authorized commands (run both for cross-evidence):**

```bash
docker exec control-postgres-beast psql -U admin -d controlplane -c '\du admin'
docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT rolname, rolsuper, rolreplication FROM pg_roles WHERE rolname = 'admin';"
```

**PASS criteria:**
- `\du admin` output shows attribute strings including `Superuser` and `Replication`
- Parsable query returns: `admin|t|t`

### Gate 6 -- exactly one 5432 listener bound to 127.0.0.1

Spec text: "`ss -tlnp` shows exactly one 5432 listener, bound to 127.0.0.1"

**Authorized commands:**

```bash
ss -tlnp 2>/dev/null | grep ':5432 '
ss -tlnp 2>/dev/null | grep -c ':5432 '   # count: must equal 1
```

**PASS criteria:**
- Exactly one line of output from the first command
- Line shows `127.0.0.1:5432` (not `0.0.0.0:5432` or `*:5432`)
- Count from second command: `1`

### Gate 7 -- `docker compose restart` returns container to healthy within 60s

Spec text: "`docker compose restart` returns container to healthy within 60s"

**Authorized commands (60s cap, NOT 150s -- this is restart not first-boot, init script does not re-execute, faster path):**

```bash
cd /home/jes/postgres-beast
restart_t0=$(date +%s)
docker compose restart

# Health-poll, 60s cap = 12 iterations * 5s
for i in $(seq 1 12); do
  status=$(docker inspect control-postgres-beast --format '{{.State.Health.Status}}' 2>/dev/null || echo 'pending')
  echo "[restart-poll $i/12] health=$status"
  if [ "$status" = "healthy" ]; then break; fi
  sleep 5
done
restart_t1=$(date +%s)
echo "restart-to-healthy elapsed: $((restart_t1 - restart_t0))s"

# Confirm container survived restart cleanly
docker ps --filter name=control-postgres-beast --format 'table {{.Names}}\t{{.Status}}'

# Confirm volume + data persisted (the vector extension should still be registered after restart -- this proves the named volume held)
docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT extname FROM pg_extension WHERE extname='vector';"
```

**PASS criteria:**
- Container reaches healthy within 60s of `docker compose restart` issuing
- `docker ps` shows running + healthy after restart
- Vector extension still present after restart (proves pgdata named volume is durable across container lifecycle)

**Note:** init script will NOT re-execute (Docker entrypoint convention -- only runs when the volume is freshly initialized; pgdata volume already exists). This is correct expected behavior, not a bug.

### After gates 5, 6, 7 all PASS

PD writes final ship report at `/home/jes/postgres-beast/B2a_ship_report.md` per spec format:

1. **All 7 acceptance gate results** (PASS/FAIL each, with command output as evidence) -- gates 1-4 cited from Step 6 review, gates 5-7 from this acceptance pass
2. **Container ID and image digest** -- `docker inspect control-postgres-beast --format '{{.Id}} {{.Image}}'` (already captured: `61acfaf455d8...` / `sha256:8ed3192326bb...`)
3. **Disk usage of pgdata volume** -- `docker system df -v | grep pgdata`
4. **md5sum of final compose.yaml and init/01-pgvector.sql** (already known: `a9a7404d...` / `899c6932...`)
5. **Any deviations from spec, with reasoning** -- there are TWO authorized deviations to document:
   - Compose v2 plugin (v5.1.3, sha256 `a0298760c9772d2c06888fc8703a487c94c3c3b0134adeef830742a2fc7647b4`) installed at `~/.docker/cli-plugins/docker-compose` as bootstrap step prior to Step 1; Beast's docker.io package does not bundle the V2 plugin. Note: Docker Compose v5.x is architecturally the V2 plugin line, renumbered to skip v3.0/v4.0 and disambiguate from legacy compose-file schema versions (per docker/compose release notes). Approved by Paco via `docs/paco_request_b2a_compose_v2_blocker.md` and `docs/paco_request_b2a_compose_v5_anomaly.md`. Reversal: `rm ~/.docker/cli-plugins/docker-compose`.
   - Spec Step 6 `sleep 15` replaced with health-poll loop (30 iterations x 5s, 150s cap on first boot; 60s cap on restart per gate 7). Approved by Paco via `docs/paco_response_b2a_step3_confirm_steps56_go.md`. P6 lesson captured.
6. **PG version note** -- 16.13 observed (within spec's "any 16.x acceptable" envelope; subscriber >= publisher rule holds for B2b with CiscoKid 16.11). No deviation; flagged for B2b spec preamble.
7. **Time elapsed** -- start-to-healthy from Step 5 pull through Step 6 healthy was ~25s (pull 13s + up 2s + first-boot health-poll 10s). Restart-to-healthy from gate 7 will be added.

**On ship report write complete:**

- Notify Paco via task pipeline (`agent_tasks` table on CiscoKid -- standard B2a SHIPPED task, with ship-report-path as task `result_path`)
- Paco runs final independent verification gate (re-checks all 7 acceptance items via fresh psql connection from a new shell session as spec requires)
- On Paco gate PASS: B2a CHECKLIST line flips `[~]` -> `[x]`, audit trail entry, commit, push.

---

## Standing rules in effect

- **Rule 1 (MCP fabric is for control, not bulk data):** all gate commands are control-plane (small command outputs). Compliant.
- **CLAUDE.md "Spec or no action":** the only authorized deviations are documented (Compose v5.1.3 bootstrap + health-poll). No further deviations.
- **CLAUDE.md "Docker bypasses UFW":** localhost bind verified by host-side `ss -tlnp` (gate 6 will re-verify formally).
- **Correspondence protocol:** PD writes ship report directly at `/home/jes/postgres-beast/B2a_ship_report.md` (spec-canonical location, NOT in `docs/` -- ship report is a B2a deliverable artifact, not a Paco-PD correspondence doc). PD also notifies Paco via task pipeline; the report path is the routing handle.

---

**File location:** `/home/jes/control-plane/docs/paco_response_b2a_steps56_confirm_gate567_go.md`

-- Paco
