# B1 -- MinIO on Beast (S3-compatible object store)

**Status:** RATIFIED 2026-04-26 Day 72 by CEO (all 6 picks Option A as Paco recommended)
**Owner:** Paco spec, PD execute
**Predecessor:** B2b (CLOSED Day 72, commit `076e0fc`)
**Successor:** Atlas v0.1 build (depends on B1 + B2b landing; B2b ✓, B1 in flight)
**Drafted:** 2026-04-26 Day 72 by Paco

---

## Purpose

Stand up a single-node MinIO server on Beast as the canonical homelab object store. Three foreseeable consumers:

1. **Atlas v0.1+** -- runtime artifacts (decision traces, observation snapshots, ad-hoc blob writes from agent loops)
2. **CiscoKid backup jobs** -- DR target for Postgres dumps, MCP server snapshots, control-plane config tarballs (per CAPACITY_v1.1 line 46)
3. **Brand & Market artifacts** -- demo videos, portfolio assets, fine-tune checkpoints (currently scattered in `/home/jes/finetune-poc/`, `/home/jes/hf-cache/`, etc.)

B1 is **single-tenant, LAN-only, root-credentials-only** in v1. Per-service IAM and TLS-from-Tailscale are P5 carryovers.

---

## Ratified picks (CEO 2026-04-26)

| # | Pick | Decision | Rationale |
|---|---|---|---|
| 1 | Deployment vehicle | **Option A: Docker Compose** | Mirrors B2a/B2b idiom; PD muscle memory; restart-safety solved |
| 2 | Image tag | **Option A: pinned by digest + date tag** | B2a P6 lesson; reproducible recreate |
| 3 | Bind address | **Option A: LAN bind 192.168.1.152:9000 (S3) + 192.168.1.152:9001 (console)** | Same gate stack as B2b; avoids SSH-tunnel scaffolding for CiscoKid backup jobs |
| 4 | Initial bucket scaffolding | **Option A: 3 buckets at first boot** (`atlas-state`, `backups`, `artifacts`) via `mc` one-shot | Buckets are metadata-only; pre-creating known consumers means downstream specs don't bundle bucket creation |
| 5 | Credential model | **Option A: root creds only** in `.env` (chmod 600, gitignored); per-svc IAM deferred to P5 | Same logic as B2b admin/adminpass; v1 single-tenant; hardening as separate spec |
| 6 | Disk layout | **Option A: SNSD on `/home/jes/minio-data/`** | Single 4.4TB drive; erasure coding without multiple physical drives is theater |

---

## Architecture

```
              CiscoKid backup jobs                  Atlas v0.1+
              (192.168.1.10)                       (Beast, Docker host net)
                     |                                    |
                     | S3 API over LAN                    | S3 API via 127.0.0.1
                     | (192.168.1.152:9000)               | (host network = Beast localhost)
                     v                                    v
         +----------------------------------+----------------------+
         |                                                          |
         |   MinIO server container (control-minio-beast)          |
         |   - Image: quay.io/minio/minio:RELEASE.YYYY-MM-DD-HHMM... |
         |     pinned by sha256 digest                              |
         |   - Listening: 192.168.1.152:9000 (S3 API)               |
         |   - Listening: 192.168.1.152:9001 (web console)          |
         |   - Data volume: /home/jes/minio-data -> /data           |
         |   - Config volume: /home/jes/minio-beast/config -> /root/.minio (optional)
         |   - Env: MINIO_ROOT_USER + MINIO_ROOT_PASSWORD from .env |
         |   - Healthcheck: GET /minio/health/live every 30s        |
         +----------------------------------+----------------------+
                            |
                            | docker network (compose default bridge)
                            v
                        bind mount: /home/jes/minio-data/ (host)
```

Gate stack (defense in depth):
1. **LAN-bind:** listener on 192.168.1.152:9000/9001, NOT 0.0.0.0
2. **UFW:** allow IN from 192.168.1.0/24 to 9000/9001 (will land BEFORE pre-existing IoT DENY rules at [1]-[11])
3. **Auth:** MinIO root credentials (long random password, generated at install time)
4. **TLS:** **NOT in v1.** S3 API is plaintext on LAN. P5 carryover: TLS via Tailscale serve or self-signed cert.

Docker iptables bypass disclosure (B2b precedent): UFW rules apply at INPUT chain; Docker DNAT bypasses INPUT. So UFW is documented defense-in-depth. Real gates are LAN-bind + auth.

---

## Phase A -- Pre-change capture

```bash
# On Beast: capture pre-state
ss -tln | grep -E ':(9000|9001)' > /tmp/B1_phase_a_ports.txt 2>&1 || echo 'ports free' > /tmp/B1_phase_a_ports.txt
sudo ufw status numbered > /tmp/B1_phase_a_ufw.txt
ls -la /home/jes/ > /tmp/B1_phase_a_home_layout.txt
df -h / /home > /tmp/B1_phase_a_disk.txt
```

**Phase A acceptance:**
- All 4 capture files written
- Ports 9000/9001 confirmed free
- UFW snapshot has at least the existing 14 rules
- /home/jes/minio-data/ does NOT yet exist (greenfield)

---

## Phase B -- Directory structure + .env + compose.yaml + init script

### Step B.1 -- Create /home/jes/minio-beast/ directory tree

```bash
mkdir -p /home/jes/minio-beast/init
mkdir -p /home/jes/minio-data
chmod 700 /home/jes/minio-data
ls -la /home/jes/minio-beast/ /home/jes/minio-data/
```

### Step B.2 -- Generate root credentials + write .env

Generate a long random root password (40+ chars, alphanumeric + symbols safe for env files) using `openssl rand -base64 30`. Capture for `.env`:

```bash
ROOT_USER='atlas-admin'
ROOT_PASSWORD=$(openssl rand -base64 30 | tr -d '/+=' | head -c 40)
echo "Generated root user: $ROOT_USER"
echo "Generated root password: $ROOT_PASSWORD (save -- this is the ONLY copy)"

cat > /home/jes/minio-beast/.env <<EOF
MINIO_ROOT_USER=$ROOT_USER
MINIO_ROOT_PASSWORD=$ROOT_PASSWORD
EOF

chmod 600 /home/jes/minio-beast/.env
ls -la /home/jes/minio-beast/.env
md5sum /home/jes/minio-beast/.env
```

Print the generated password ONCE for CEO to record (e.g. in 1Password or equivalent). After this step the .env file is the only on-disk copy.

### Step B.3 -- Write compose.yaml

File location: `/home/jes/minio-beast/compose.yaml`. Use the latest stable MinIO release as of Day 72 (PD verifies actual current digest at execution time -- this spec writes against the digest-pinning *pattern*, not a frozen value).

Reference content:

```yaml
services:
  minio:
    image: quay.io/minio/minio:RELEASE.2025-09-07T16-13-09Z@sha256:<DIGEST>
    container_name: control-minio-beast
    restart: unless-stopped
    ports:
      - "192.168.1.152:9000:9000"
      - "192.168.1.152:9001:9001"
    env_file:
      - .env
    volumes:
      - /home/jes/minio-data:/data
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 15s
```

PD step: before writing, run `docker pull quay.io/minio/minio:RELEASE.<latest>` and capture the resolved sha256 digest from `docker inspect`; substitute `<DIGEST>` in the compose.yaml.

**Phase B acceptance:**
- /home/jes/minio-beast/.env exists, chmod 600, owner jes:jes
- /home/jes/minio-beast/compose.yaml exists with digest-pinned image
- /home/jes/minio-data/ exists, chmod 700, owner jes:jes
- `docker compose config` exit 0 (validates compose syntax, env_file resolution, volume paths)
- compose.yaml md5 captured for ship report

---

## Phase C -- UFW rules

Pre-existing UFW state on Beast (Phase A capture): 11 IoT DENY rules at [1]-[11], LAN ALLOW for 22/tcp [12], 11434/tcp [13], 8800/tcp [14]. **No DENY rule for 9000/9001 currently exists**, so order doesn't matter the way it did in B2b -- a simple `ufw allow` suffices.

```bash
sudo ufw allow from 192.168.1.0/24 to any port 9000 proto tcp comment 'B1: MinIO S3 API'
sudo ufw allow from 192.168.1.0/24 to any port 9001 proto tcp comment 'B1: MinIO console'
sudo ufw status numbered | grep -E '(9000|9001)'
sudo ufw status numbered > /tmp/B1_phase_c_ufw_post.txt
```

**Phase C acceptance:**
- 2 new UFW rules visible at the bottom of the rule list
- Both with the LAN-restricted source 192.168.1.0/24
- Both with the documented comment
- All 14 pre-existing rules still present (no rule re-ordering)

---

## Phase D -- First boot + healthcheck wait + bucket creation

### Step D.1 -- Boot the container (deferred-subshell pattern; service-affecting in the sense that it occupies new ports)

```bash
cd /home/jes/minio-beast
docker compose up -d
echo "compose up ssh-exit=$?"
```

### Step D.2 -- Wait for healthy (poll-don't-sleep per B2a P6 lesson)

```bash
for i in $(seq 1 24); do
  STATUS=$(docker inspect control-minio-beast --format '{{.State.Health.Status}}' 2>/dev/null || echo 'unknown')
  echo "poll $i/24: $STATUS"
  if [ "$STATUS" = "healthy" ]; then
    echo "GATE_HEALTHY_OK"
    break
  fi
  sleep 5
done
```

Max wait: 24 * 5 = 120s. MinIO usually healthy within 10-15s on first boot.

### Step D.3 -- Create 3 buckets via one-shot mc container

Use the official `quay.io/minio/mc` image. Pull, configure alias, create 3 buckets:

```bash
# Pull mc image (capture digest for ship report)
docker pull quay.io/minio/mc:latest
MC_DIGEST=$(docker inspect quay.io/minio/mc:latest --format '{{index .RepoDigests 0}}')
echo "mc image digest: $MC_DIGEST"

# Source root creds from .env (in same shell context)
set -a; . /home/jes/minio-beast/.env; set +a

# Configure mc alias + create buckets in one shot
docker run --rm --network host \
  -e MC_HOST_local="http://${MINIO_ROOT_USER}:${MINIO_ROOT_PASSWORD}@127.0.0.1:9000" \
  quay.io/minio/mc:latest <<'MCEOF'
mb -p local/atlas-state
mb -p local/backups
mb -p local/artifacts
ls local
MCEOF
```

**Phase D acceptance:**
- Container `control-minio-beast` Up healthy
- Health endpoint: `curl -s http://192.168.1.152:9000/minio/health/live` returns 200 OK with no body (per MinIO convention)
- 3 buckets visible: `atlas-state`, `backups`, `artifacts`
- mc one-shot run had ssh-exit=0
- Container RestartCount=0
- No ERROR or FATAL lines in `docker logs control-minio-beast`

---

## Phase E -- LAN reachability verification (CiscoKid -> Beast S3)

This is the FIRST end-to-end exercise of the LAN-bind + UFW + auth gate stack from a non-Beast context.

From CiscoKid:

```bash
# Pull mc on CiscoKid (one-time tooling install)
docker pull quay.io/minio/mc:latest

# Source root creds (PD reads them from /tmp/B1_root_creds.tmp written by Beast Phase B step,
# OR PD reads them via SSH back to Beast cat /home/jes/minio-beast/.env -- BUT NEVER COMMITS).
# For this spec: PD will SCP the root password from Beast to CiscoKid /tmp/, use it, delete it.
scp jes@192.168.1.152:/home/jes/minio-beast/.env /tmp/B1_minio_creds_ciscokid.env
chmod 600 /tmp/B1_minio_creds_ciscokid.env

# Configure alias and verify
set -a; . /tmp/B1_minio_creds_ciscokid.env; set +a
docker run --rm --network host \
  -e MC_HOST_beast="http://${MINIO_ROOT_USER}:${MINIO_ROOT_PASSWORD}@192.168.1.152:9000" \
  quay.io/minio/mc:latest ls beast

# Smoke: write a 1KB test object, read it back, delete it
dd if=/dev/urandom of=/tmp/B1_smoke.bin bs=1K count=1 2>/dev/null
docker run --rm --network host -v /tmp:/data \
  -e MC_HOST_beast="http://${MINIO_ROOT_USER}:${MINIO_ROOT_PASSWORD}@192.168.1.152:9000" \
  quay.io/minio/mc:latest cp /data/B1_smoke.bin beast/backups/B1_smoke.bin
docker run --rm --network host \
  -e MC_HOST_beast="http://${MINIO_ROOT_USER}:${MINIO_ROOT_PASSWORD}@192.168.1.152:9000" \
  quay.io/minio/mc:latest ls beast/backups
docker run --rm --network host \
  -e MC_HOST_beast="http://${MINIO_ROOT_USER}:${MINIO_ROOT_PASSWORD}@192.168.1.152:9000" \
  quay.io/minio/mc:latest rm beast/backups/B1_smoke.bin

# Cleanup the temporary creds file
shred -u /tmp/B1_minio_creds_ciscokid.env /tmp/B1_smoke.bin
```

**Phase E acceptance:**
- `mc ls beast` returns 3 buckets
- 1KB test object PUT succeeds (`Total: 1 KiB` in mc output)
- 1KB test object visible in `mc ls beast/backups`
- 1KB test object DELETE succeeds (mc rm exit 0)
- /tmp/B1_minio_creds_ciscokid.env shred-deleted from CiscoKid
- No new ERROR lines in `docker logs control-minio-beast` on Beast

---

## Phase F -- Restart safety + cleanup + ship report

### Step F.1 -- Restart safety check

```bash
docker compose restart control-minio-beast
# wait for healthy
for i in $(seq 1 24); do
  STATUS=$(docker inspect control-minio-beast --format '{{.State.Health.Status}}' 2>/dev/null || echo 'unknown')
  echo "poll $i/24: $STATUS"
  if [ "$STATUS" = "healthy" ]; then break; fi
  sleep 5
done
# verify buckets still present (NOT recreated -- persistence)
docker run --rm --network host \
  -e MC_HOST_local="http://$(grep ROOT_USER /home/jes/minio-beast/.env | cut -d= -f2):$(grep ROOT_PASSWORD /home/jes/minio-beast/.env | cut -d= -f2)@127.0.0.1:9000" \
  quay.io/minio/mc:latest ls local
```

### Step F.2 -- Cleanup intermediate Phase A capture files (preserve ship report inputs first)

```bash
# Move Phase A captures to ship-report-inputs dir so they survive cleanup
mkdir -p /home/jes/minio-beast/.ship-report-inputs
mv /tmp/B1_phase_a_ports.txt /tmp/B1_phase_a_ufw.txt /tmp/B1_phase_a_home_layout.txt /tmp/B1_phase_a_disk.txt /tmp/B1_phase_c_ufw_post.txt /home/jes/minio-beast/.ship-report-inputs/
ls /home/jes/minio-beast/.ship-report-inputs/
```

### Step F.3 -- Ship report

File location on Beast: `/home/jes/minio-beast/B1_ship_report.md`. Required sections:

- Summary (MinIO LIVE; gate stack; 3 consumers preregistered)
- All 8 acceptance gates with command output evidence
- Bind address / UFW rules / health endpoint URL
- Image digest (locked) for both minio and mc
- Bucket inventory + sizes (all 0 bytes at install)
- Generated root credentials disclosure pattern (NOT the actual password; just the .env path + perms + how to read)
- Restart safety: container persists across restart; buckets present post-restart
- Smoke test from CiscoKid: PUT/LIST/DELETE round trip
- 4 spec deviations possible (PD documents any)
- Open carryovers (P5: per-svc IAM, TLS, reverse SSH key from Beast to CiscoKid for admin convenience)
- Time elapsed (Phase A start to F end)

**Phase F acceptance:**
- Container Up healthy post-restart, RestartCount=1 (the manual restart counts in Docker semantics? Per B2b Gate 12 finding: NO -- `docker compose restart` does NOT increment RestartCount; only crash-driven restarts do. So expected: still 0.)
- All 3 buckets present post-restart (`mc ls local` shows atlas-state, backups, artifacts)
- Ship report at /home/jes/minio-beast/B1_ship_report.md, all sections populated
- Phase A inputs archived to .ship-report-inputs/

---

## 8-gate acceptance scorecard (PD verifies all PASS)

1. **Container Up healthy:** `docker ps` shows control-minio-beast Up X (healthy); `docker inspect` health.status=healthy
2. **LAN listener exact:** `ss -tln` shows exactly 192.168.1.152:9000 + 192.168.1.152:9001 (no 127.0.0.1 binds, no 0.0.0.0 binds)
3. **UFW allow active:** `ufw status numbered` shows 2 new ALLOW rules for 9000+9001 from 192.168.1.0/24
4. **Health endpoint responds:** `curl -s -o /dev/null -w "%{http_code}" http://192.168.1.152:9000/minio/health/live` returns 200
5. **3 buckets present:** `mc ls local` (from Beast) + `mc ls beast` (from CiscoKid) both list atlas-state, backups, artifacts
6. **Smoke PUT/GET/DELETE from CiscoKid:** 1KB random object round-trips successfully
7. **Persistence across restart:** post-restart, all 3 buckets still present, container healthy, no data loss
8. **No ERROR/FATAL in container logs:** `docker logs control-minio-beast 2>&1 | grep -iE 'error|fatal' | wc -l` returns 0 (or PD enumerates and attributes any non-zero count)

---

## Rollback

If any phase fails and rollback is needed:

```bash
# Beast
cd /home/jes/minio-beast
docker compose down -v   # -v removes named volumes; bind mount /home/jes/minio-data is preserved
rm -rf /home/jes/minio-data/.minio.sys 2>/dev/null  # only if full reset desired

sudo ufw delete allow from 192.168.1.0/24 to any port 9000 proto tcp
sudo ufw delete allow from 192.168.1.0/24 to any port 9001 proto tcp

# Optional: shred .env if abandoning
shred -u /home/jes/minio-beast/.env
rm -rf /home/jes/minio-beast/
```

No other system component depends on B1 yet; rollback is clean.

---

## Time estimate

- Phase A (capture): <5 min
- Phase B (compose + .env + dirs): 5-10 min (most of which is generating + verifying digest pin)
- Phase C (UFW): <5 min
- Phase D (first boot + buckets): 5-10 min
- Phase E (CiscoKid smoke): 5-10 min
- Phase F (restart + cleanup + ship report): 10-15 min

**Total estimate: 30-55 min PD execution + ~15 min Paco independent verification.**

---

## PD-to-Paco report (per P6 protocol)

PD writes per-phase paco_review_b1_*.md docs to /home/jes/control-plane/docs/, matching B2b cadence. Final ship report at /home/jes/minio-beast/B1_ship_report.md (matches B2a's report-on-target-host pattern). Final close: paco_response_b1_independent_gate_pass_close.md.

---

## Standing rules in effect

- **Rule 1 (MCP for control, not bulk data):** B1 control plane via SSH + Compose; data plane via S3 protocol over LAN. MCP carries control commands only. Compliant.
- **CLAUDE.md "Spec or no action":** all 6 picks ratified pre-draft; deviations require paco_request_b1_*.md.
- **CLAUDE.md "Docker bypasses UFW":** acknowledged; UFW is documented defense-in-depth. Real gates: LAN-bind + auth.
- **Correspondence protocol:** per-phase paco_review_b1_*.md; final paco_response_b1_independent_gate_pass_close.md.
- **Canon location:** spec at /home/jes/control-plane/tasks/B1_minio_beast.md, ship report at /home/jes/minio-beast/B1_ship_report.md, correspondence at /home/jes/control-plane/docs/.

---

## P5 carryovers banked (post-B1)

- Per-service IAM accounts (atlas-svc, backups-svc, artifacts-svc) with scoped policies
- TLS for S3 API (Tailscale serve / self-signed cert / Let's Encrypt over Tailscale)
- Reverse SSH key from Beast to CiscoKid (admin convenience; not B1 dependency)
- Bucket lifecycle policies (auto-expire old artifacts, versioning for backups)
- Backup retention policy for the `backups` bucket (off-site DR target)

---

**Spec status:** RATIFIED. Ready for PD execution.

-- Paco
