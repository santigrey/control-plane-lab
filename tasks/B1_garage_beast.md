# B1 -- Garage on Beast (S3-compatible object store)

**Status:** RATIFIED 2026-04-26 Day 72 by CEO. **Pivoted from MinIO** when discovery during Phase B verification surfaced that MinIO Community Edition was archived 2026-02-14 (read-only repo, no further patches; CVE-2025-62506 in last available image). Five-candidate exhaustive comparison performed; Garage v2.1.0 selected for: actively maintained Rust substrate, single-container operational fit, single-node deployment well-documented (the deployer's own production model), AGPL-3.0 acceptable for our internal-tool threat model.
**Owner:** Paco spec, PD execute
**Predecessor:** B2b (CLOSED Day 72, commit `076e0fc`); MinIO Phase B in-flight (will be rolled back in Phase A2)
**Successor:** Atlas v0.1 build (depends on B1 + B2b landing; B2b ✓, B1 in flight)
**Drafted:** 2026-04-26 Day 72 by Paco
**Replaces:** `tasks/B1_minio_beast.md` (deprecated, kept in git history)

---

## Purpose

Stand up a single-node Garage server on Beast as the canonical homelab object store. Three foreseeable consumers:

1. **Atlas v0.1+** -- runtime artifacts (decision traces, observation snapshots, ad-hoc blob writes from agent loops)
2. **CiscoKid backup jobs** -- DR target for Postgres dumps, MCP server snapshots, control-plane config tarballs (per CAPACITY_v1.1 line 46)
3. **Brand & Market artifacts** -- demo videos, portfolio assets, fine-tune checkpoints

B1 is **single-tenant, LAN-only, single-S3-key** in v1. Per-bucket keys, TLS, object versioning/lifecycle are P5 carryovers.

---

## Ratified picks (CEO 2026-04-26)

| # | Pick | Decision | Adapted to Garage |
|---|---|---|---|
| 1 | Deployment vehicle | Docker Compose | Same -- `dxflrs/garage:v2.1.0` (digest-pinned at PD execution time) |
| 2 | Image tag | Pinned by digest + version tag | Same idiom: `docker pull` -> `docker inspect ... --format '{{index .RepoDigests 0}}'` |
| 3 | Bind address | LAN bind for S3 | **S3 API on 192.168.1.152:3900 only.** Admin 3903 + RPC 3901 + web 3902 + k2v 3904 all stay container-internal (not published to host). Docker port mapping enforces the boundary. |
| 4 | Initial bucket scaffolding | 3 buckets at first boot | `atlas-state`, `backups`, `artifacts` -- via `garage bucket create` inside container during Phase D, not via mc |
| 5 | Credential model | Single S3 key in v1 | Single `root` access key (Garage CLI) with read+write+owner perms on all 3 buckets. Per-bucket keys deferred to P5 carryover (matches MinIO root-only logic). garage.toml baked secrets (admin_token, metrics_token, rpc_secret) -- chmod 600. |
| 6 | Disk layout | SNSD on `/home/jes/garage-data/` | meta + data subdirs share the single 4.4TB drive. Garage docs recommend meta on SSD; not blocking for v1 (homelab single-drive context). |

---

## Architecture

```
              CiscoKid backup jobs                   Atlas v0.1+
              (192.168.1.10)                        (Beast, Docker host net)
                     |                                    |
                     | aws-cli S3 over LAN                | aws-cli/boto3 via 127.0.0.1
                     | (192.168.1.152:3900)               | (host network = Beast localhost)
                     v                                    v
         +----------------------------------+----------------------+
         |                                                          |
         |   Garage server container (control-garage-beast)        |
         |   - Image: dxflrs/garage@sha256:<DIGEST>                |
         |   - Listening S3 API (3900):     192.168.1.152:3900     |
         |   - Listening admin (3903):       127.0.0.1:3903         |
         |   - RPC (3901), web (3902), k2v (3904): NOT published   |
         |   - Config: /etc/garage.toml (bind-mount, chmod 600)     |
         |   - Volume: /home/jes/garage-data/meta -> /var/lib/garage/meta |
         |   - Volume: /home/jes/garage-data/data -> /var/lib/garage/data |
         |   - Healthcheck: GET http://127.0.0.1:3903/health        |
         |     (admin endpoint; no token needed for /health)        |
         +----------------------------------+----------------------+
                            |
                            v
                bind mounts on host:
                /home/jes/garage-beast/garage.toml (config, chmod 600)
                /home/jes/garage-data/meta/         (Garage metadata, lmdb)
                /home/jes/garage-data/data/         (object data)
```

Gate stack (defense in depth, same shape as B2b):
1. **LAN-bind** for S3 only via Docker port mapping; admin/RPC/web/k2v ports never reach host network
2. **UFW** allow IN from 192.168.1.0/24 to 3900/tcp (single rule)
3. **Auth:** S3 access key + secret key (40+ char Garage-generated); admin operations require admin_token (only reachable from Beast localhost)
4. **TLS:** **NOT in v1.** S3 API is plaintext on LAN. P5 carryover.

Docker iptables bypass disclosure (B2b precedent): UFW rules apply at INPUT chain; Docker DNAT bypasses INPUT. UFW is documented defense-in-depth. Real gates are LAN-bind + S3 access key auth.

---

## Phase A -- Pre-change capture (Garage delta + MinIO rollback prep)

Most Phase A inputs from the MinIO branch are still valid (UFW state, /home/jes/ layout pre-MinIO, disk free). One delta needed: verify Garage ports 3900-3904 are also free.

```bash
# Garage-port-free verification (delta vs MinIO Phase A)
ss -tln | grep -E ':(3900|3901|3902|3903|3904)' > /tmp/B1_garage_phase_a_ports.txt 2>&1 || echo 'all garage ports free' > /tmp/B1_garage_phase_a_ports.txt

# MinIO rollback inventory (confirm what needs removal)
ls -la /home/jes/minio-beast/ /home/jes/minio-data/ 2>&1 > /tmp/B1_garage_phase_a_minio_inventory.txt
docker images quay.io/minio/minio --format '{{.Repository}}:{{.Tag}} {{.ID}}' >> /tmp/B1_garage_phase_a_minio_inventory.txt
```

**Phase A acceptance:**
- `/tmp/B1_garage_phase_a_ports.txt` shows Garage ports 3900-3904 all free
- `/tmp/B1_garage_phase_a_minio_inventory.txt` shows the MinIO Phase B artifacts present (the things we will rollback in A2)
- Original Phase A captures (`/tmp/B1_phase_a_*.txt`) still preserved (UFW + home_layout + disk + ports baseline)

---

## Phase A2 -- MinIO rollback

```bash
# Remove MinIO Phase B artifacts
rm -rf /home/jes/minio-beast/
rm -rf /home/jes/minio-data/

# Remove pulled MinIO image (frees ~167MiB)
docker rmi quay.io/minio/minio:latest 2>&1 || echo 'image already absent or in use'

# Verify clean
ls -la /home/jes/minio-beast/ /home/jes/minio-data/ 2>&1 | head -3
docker images quay.io/minio/minio --format '{{.Repository}}:{{.Tag}}' | head -3
```

**Phase A2 acceptance:**
- Both directories absent: `ls: cannot access '/home/jes/minio-beast/'` etc.
- No `quay.io/minio/minio` images remain
- B2b infrastructure unaffected: `control-postgres-beast` still Up healthy with same StartedAt
- MinIO root password generated in MinIO Phase B is now unrecoverable -- ACK that this is correct (we don't need it; the image is gone; the password is moot)

---

## Phase B -- Directory tree + garage.toml + compose.yaml + image pull + digest pin

### Step B.1 -- Directory tree

```bash
mkdir -p /home/jes/garage-beast
mkdir -p /home/jes/garage-data/meta /home/jes/garage-data/data
chmod 700 /home/jes/garage-data /home/jes/garage-data/meta /home/jes/garage-data/data
ls -la /home/jes/garage-beast/ /home/jes/garage-data/
stat -c '%a %U:%G %n' /home/jes/garage-beast /home/jes/garage-data /home/jes/garage-data/meta /home/jes/garage-data/data
```

**Capture for review (Step B.1):**
- `garage-beast/` is jes:jes (default umask)
- `garage-data/`, `garage-data/meta/`, `garage-data/data/` all chmod 700 jes:jes

### Step B.2 -- Generate garage.toml with embedded secrets

Three secrets generated at config-write time. All chmod 600 file inherits the secret protection.

```bash
RPC_SECRET=$(openssl rand -hex 32)
ADMIN_TOKEN=$(openssl rand -base64 32)
METRICS_TOKEN=$(openssl rand -base64 32)

# Sanity check lengths before write
echo "RPC_SECRET length: ${#RPC_SECRET} (expect 64 hex chars)"
echo "ADMIN_TOKEN length: ${#ADMIN_TOKEN} (expect ~44 chars)"
echo "METRICS_TOKEN length: ${#METRICS_TOKEN} (expect ~44 chars)"
if [ "${#RPC_SECRET}" -ne 64 ]; then
  echo "FATAL: RPC_SECRET length wrong"; exit 1
fi

cat > /home/jes/garage-beast/garage.toml <<TOML_EOF
metadata_dir = "/var/lib/garage/meta"
data_dir = "/var/lib/garage/data"
db_engine = "lmdb"
metadata_auto_snapshot_interval = "6h"

replication_factor = 1

rpc_bind_addr = "[::]:3901"
rpc_public_addr = "127.0.0.1:3901"
rpc_secret = "$RPC_SECRET"

[s3_api]
s3_region = "garage"
api_bind_addr = "[::]:3900"
root_domain = ".s3.garage.local"

[s3_web]
bind_addr = "[::]:3902"
root_domain = ".web.garage.local"
index = "index.html"

[k2v_api]
api_bind_addr = "[::]:3904"

[admin]
api_bind_addr = "[::]:3903"
admin_token = "$ADMIN_TOKEN"
metrics_token = "$METRICS_TOKEN"
TOML_EOF

chmod 600 /home/jes/garage-beast/garage.toml
ls -la /home/jes/garage-beast/garage.toml
stat -c '%a %U:%G %n' /home/jes/garage-beast/garage.toml
wc -l /home/jes/garage-beast/garage.toml
md5sum /home/jes/garage-beast/garage.toml
```

**IMPORTANT for CEO recording:**
The ADMIN_TOKEN, METRICS_TOKEN, and RPC_SECRET are generated and embedded directly into `garage.toml`. They are NOT echoed to stdout (unlike MinIO's password). The garage.toml file (chmod 600) is the only on-disk copy. To record:

```bash
# After generation, CEO can extract for 1Password recording:
grep -E '(rpc_secret|admin_token|metrics_token)' /home/jes/garage-beast/garage.toml
```

CEO copies these values to 1Password. They're recoverable by reading garage.toml at any time, but if Beast disk is lost without backup, secrets must be rotated.

Note on `s3_web` and `k2v_api` sections: kept in the config (Garage will bind those ports inside the container) but the compose.yaml will NOT publish them to the host, so they're effectively container-internal only. This is the cleanest approach -- avoid touching Garage's expected config schema.

**Capture for review (Step B.2):**
- Three length checks PASS (RPC_SECRET=64, ADMIN_TOKEN=~44, METRICS_TOKEN=~44)
- garage.toml exists, chmod 600 jes:jes
- garage.toml line count: 26 (per heredoc)
- garage.toml md5sum (unique per generated secrets)
- Three lines extractable: `rpc_secret = "..."`, `admin_token = "..."`, `metrics_token = "..."`

### Step B.3 -- Pull image + capture digest + write compose.yaml + validate

```bash
cd /home/jes/garage-beast

echo '--- pulling Garage image v2.1.0 ---'
docker pull dxflrs/garage:v2.1.0

GARAGE_REPODIGEST=$(docker inspect dxflrs/garage:v2.1.0 --format '{{index .RepoDigests 0}}')
echo "GARAGE_REPODIGEST=$GARAGE_REPODIGEST"

if [[ -z "$GARAGE_REPODIGEST" || "$GARAGE_REPODIGEST" != dxflrs/garage@sha256:* ]]; then
  echo "FATAL: digest capture failed. Got: $GARAGE_REPODIGEST"
  exit 1
fi

cat > /home/jes/garage-beast/compose.yaml <<COMPOSE_EOF
services:
  garage:
    image: $GARAGE_REPODIGEST
    container_name: control-garage-beast
    restart: unless-stopped
    ports:
      - "192.168.1.152:3900:3900"   # S3 API: LAN-exposed
      - "127.0.0.1:3903:3903"       # admin: localhost-only
    volumes:
      - /home/jes/garage-beast/garage.toml:/etc/garage.toml:ro
      - /home/jes/garage-data/meta:/var/lib/garage/meta
      - /home/jes/garage-data/data:/var/lib/garage/data
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://127.0.0.1:3903/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s
COMPOSE_EOF

ls -la /home/jes/garage-beast/compose.yaml
md5sum /home/jes/garage-beast/compose.yaml
wc -l /home/jes/garage-beast/compose.yaml
echo ''
echo '--- compose.yaml contents ---'
cat /home/jes/garage-beast/compose.yaml

cd /home/jes/garage-beast
docker compose config 2>&1 | tee /tmp/B1_garage_phase_b_compose_config.log
echo "compose config exit=$?"
```

**Capture for review (Step B.3):**
- `GARAGE_REPODIGEST` value matches form `dxflrs/garage@sha256:<64 hex>`
- compose.yaml exists, jes:jes, md5sum captured (file ~22 lines)
- `docker compose config` exit 0
- Resolved compose-config output shows: image with `@sha256:<digest>`, ports `192.168.1.152:3900` AND `127.0.0.1:3903`, all 3 bind mounts (garage.toml ro + meta + data), healthcheck wget command

**Healthcheck pre-flight:** Garage's `dxflrs/garage` image is `scratch`-based (Rust binary only). It has NO bundled CLI tools like `wget` or `curl`. Therefore the `wget`-based healthcheck **will fail** on first run. The fix is one of:

- **Fallback A (PREFERRED):** Use a TCP probe via `nc` -- but `nc` also missing.
- **Fallback B:** Drop healthcheck from compose; rely on `docker ps` Up state + Phase D explicit `garage status` checks. Less ideal.
- **Fallback C:** Use `docker exec` healthcheck calling Garage's own binary: `["CMD", "/garage", "status"]`. The garage binary is at `/garage` inside the image. This works. **AUTHORIZED as the canonical healthcheck.**

Replace healthcheck block in compose.yaml with:
```yaml
    healthcheck:
      test: ["CMD", "/garage", "status"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s
```

PD: use `/garage status` as the healthcheck per this directive. The wget version is included above for completeness of the design discussion only.

---

## Phase C -- UFW (1 rule for S3 LAN exposure)

Only the S3 API port needs LAN exposure. Admin (3903) is already localhost-bound by docker port mapping; RPC/web/k2v are not published at all. So one UFW rule.

```bash
sudo ufw allow from 192.168.1.0/24 to any port 3900 proto tcp comment 'B1: Garage S3 API'
sudo ufw status numbered | grep -E '3900' | head -3
sudo ufw status numbered > /tmp/B1_garage_phase_c_ufw_post.txt
```

**Phase C acceptance:**
- 1 new UFW rule visible at end of rule list (position 15 if MinIO rollback removed nothing UFW-side; MinIO Phase C was never reached so UFW count was preserved at 14)
- LAN-restricted source 192.168.1.0/24
- Documented comment
- All 14 pre-existing rules still present (no re-ordering)

---

## Phase D -- First boot + cluster layout + S3 key + 3 buckets

This is the most procedurally complex phase. Garage requires a 4-step bootstrap:

1. Container boots, Garage daemon starts
2. Cluster layout assignment + apply (single-node, but layout still required)
3. Create root S3 access key (returns access_key_id + secret_key)
4. Create 3 buckets and grant root key permissions on each

Use the deferred-subshell pattern (Phase E precedent from B2b) -- this insulates the bootstrap log from any session disruption. Each step writes to log; PD cats log once subshell completes.

### Reference script (run via nohup-disowned subshell)

```bash
LOG=/tmp/B1_garage_phase_d_bootstrap.log
rm -f "$LOG"
nohup bash -c '
  exec > /tmp/B1_garage_phase_d_bootstrap.log 2>&1
  set +e
  echo "[$(date -Iseconds)] === PHASE D START ==="

  # ---- Step D.1: Boot the container ----
  cd /home/jes/garage-beast
  echo "[$(date -Iseconds)] docker compose up -d"
  docker compose up -d
  echo "[$(date -Iseconds)] compose-up exit=$?"

  # ---- Step D.2: Wait for healthy ----
  echo "[$(date -Iseconds)] Waiting for healthy (cap 120s)..."
  for i in $(seq 1 24); do
    STATUS=$(docker inspect control-garage-beast --format "{{.State.Health.Status}}" 2>/dev/null || echo unknown)
    echo "[$(date -Iseconds)] poll $i/24: $STATUS"
    if [ "$STATUS" = "healthy" ]; then
      echo "[$(date -Iseconds)] container healthy"
      break
    fi
    sleep 5
  done

  # ---- Step D.3: Capture node ID and assign layout ----
  echo "[$(date -Iseconds)] === garage status (capture node ID) ==="
  docker exec control-garage-beast /garage status
  NODE_ID=$(docker exec control-garage-beast /garage status 2>/dev/null | awk "/^[0-9a-f]{16}/{print substr(\$1,1,16); exit}")
  echo "[$(date -Iseconds)] NODE_ID=$NODE_ID"
  if [ -z "$NODE_ID" ]; then
    echo "[$(date -Iseconds)] FATAL: could not capture node ID"
    exit 1
  fi

  echo "[$(date -Iseconds)] === garage layout assign ==="
  docker exec control-garage-beast /garage layout assign -z dc1 -c 4T "$NODE_ID"
  echo "[$(date -Iseconds)] === garage layout apply --version 1 ==="
  docker exec control-garage-beast /garage layout apply --version 1
  echo "[$(date -Iseconds)] === garage status post-layout ==="
  docker exec control-garage-beast /garage status

  # ---- Step D.4: Create root S3 key, capture credentials ----
  echo "[$(date -Iseconds)] === garage key create root ==="
  KEY_OUTPUT=$(docker exec control-garage-beast /garage key create root)
  echo "$KEY_OUTPUT"
  ACCESS_KEY_ID=$(echo "$KEY_OUTPUT" | awk -F": " "/Key ID:/{print \$2}")
  SECRET_KEY=$(echo "$KEY_OUTPUT" | awk -F": " "/Secret key:/{print \$2}")
  echo "[$(date -Iseconds)] ACCESS_KEY_ID=$ACCESS_KEY_ID"
  echo "[$(date -Iseconds)] SECRET_KEY=$SECRET_KEY (record now -- only on-disk copy is .s3-creds)"

  if [ -z "$ACCESS_KEY_ID" ] || [ -z "$SECRET_KEY" ]; then
    echo "[$(date -Iseconds)] FATAL: key parsing failed"
    exit 1
  fi

  # Persist to .s3-creds (chmod 600)
  cat > /home/jes/garage-beast/.s3-creds <<CREDS_EOF
# Garage root S3 credentials -- generated $(date -Iseconds) by B1 Phase D
# DO NOT COMMIT. chmod 600. Future P5: rotate to per-bucket keys.
export AWS_ACCESS_KEY_ID=$ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY=$SECRET_KEY
export AWS_DEFAULT_REGION=garage
export AWS_ENDPOINT_URL=http://192.168.1.152:3900
CREDS_EOF
  chmod 600 /home/jes/garage-beast/.s3-creds
  ls -la /home/jes/garage-beast/.s3-creds
  md5sum /home/jes/garage-beast/.s3-creds

  # ---- Step D.5: Create 3 buckets and grant root key permissions ----
  for B in atlas-state backups artifacts; do
    echo "[$(date -Iseconds)] === garage bucket create $B ==="
    docker exec control-garage-beast /garage bucket create "$B"
    echo "[$(date -Iseconds)] === garage bucket allow --read --write --owner $B --key root ==="
    docker exec control-garage-beast /garage bucket allow --read --write --owner "$B" --key root
  done

  echo "[$(date -Iseconds)] === garage bucket list ==="
  docker exec control-garage-beast /garage bucket list

  echo "[$(date -Iseconds)] === Final container state ==="
  docker ps --filter name=control-garage-beast --format "{{.Names}}\t{{.Status}}\t{{.Ports}}"
  docker inspect control-garage-beast --format "RestartCount={{.RestartCount}} Health={{.State.Health.Status}}"

  echo "[$(date -Iseconds)] === PHASE D COMPLETE ==="
' >/dev/null 2>&1 &
disown
echo "Phase D backgrounded. PID=$! Log: $LOG"
```

### Wait + read log

```bash
for i in $(seq 1 36); do
  if grep -qE "=== PHASE D (COMPLETE|.*FATAL) ===" /tmp/B1_garage_phase_d_bootstrap.log 2>/dev/null; then
    cat /tmp/B1_garage_phase_d_bootstrap.log
    break
  fi
  sleep 5
done
```

**Phase D acceptance:**
- Container `control-garage-beast` Up healthy, RestartCount=0
- Health endpoint usable: `docker exec control-garage-beast /garage status` returns the node listed with assigned layout
- 3 buckets in `garage bucket list`: atlas-state, backups, artifacts
- Each bucket info shows root key with read+write+owner permissions
- `.s3-creds` file exists chmod 600 jes:jes with all 4 export lines
- Log shows `=== PHASE D COMPLETE ===` (not FATAL)

---

## Phase E -- LAN reachability verification (CiscoKid -> Beast S3)

First end-to-end exercise of the LAN-bind + UFW + S3-key auth gate stack from a non-Beast context.

```bash
# On CiscoKid: pull aws-cli image if not already cached (one-time tooling)
docker pull amazon/aws-cli:latest

# Pull S3 creds from Beast (temp local copy)
scp jes@192.168.1.152:/home/jes/garage-beast/.s3-creds /tmp/B1_garage_creds_ciscokid.env
chmod 600 /tmp/B1_garage_creds_ciscokid.env

# Source creds
set -a; . /tmp/B1_garage_creds_ciscokid.env; set +a

# Verify connectivity by listing buckets
docker run --rm --network host \
  -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  -e AWS_DEFAULT_REGION="$AWS_DEFAULT_REGION" \
  amazon/aws-cli:latest --endpoint-url "$AWS_ENDPOINT_URL" s3 ls

# Smoke: 1KB random PUT, list, GET, DELETE
dd if=/dev/urandom of=/tmp/B1_smoke.bin bs=1K count=1 2>/dev/null
MD5_LOCAL=$(md5sum /tmp/B1_smoke.bin | awk '{print $1}')
echo "Local md5: $MD5_LOCAL"

# PUT
docker run --rm --network host -v /tmp:/data \
  -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  -e AWS_DEFAULT_REGION="$AWS_DEFAULT_REGION" \
  amazon/aws-cli:latest --endpoint-url "$AWS_ENDPOINT_URL" s3 cp /data/B1_smoke.bin s3://backups/B1_smoke.bin

# LIST
docker run --rm --network host \
  -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  -e AWS_DEFAULT_REGION="$AWS_DEFAULT_REGION" \
  amazon/aws-cli:latest --endpoint-url "$AWS_ENDPOINT_URL" s3 ls s3://backups/

# GET back to a different filename, verify md5 matches
docker run --rm --network host -v /tmp:/data \
  -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  -e AWS_DEFAULT_REGION="$AWS_DEFAULT_REGION" \
  amazon/aws-cli:latest --endpoint-url "$AWS_ENDPOINT_URL" s3 cp s3://backups/B1_smoke.bin /data/B1_smoke_roundtrip.bin
MD5_ROUNDTRIP=$(md5sum /tmp/B1_smoke_roundtrip.bin | awk '{print $1}')
echo "Roundtrip md5: $MD5_ROUNDTRIP"
[ "$MD5_LOCAL" = "$MD5_ROUNDTRIP" ] && echo "BYTE_PARITY_OK" || echo "BYTE_PARITY_FAIL"

# DELETE
docker run --rm --network host \
  -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  -e AWS_DEFAULT_REGION="$AWS_DEFAULT_REGION" \
  amazon/aws-cli:latest --endpoint-url "$AWS_ENDPOINT_URL" s3 rm s3://backups/B1_smoke.bin

# Verify deletion
docker run --rm --network host \
  -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  -e AWS_DEFAULT_REGION="$AWS_DEFAULT_REGION" \
  amazon/aws-cli:latest --endpoint-url "$AWS_ENDPOINT_URL" s3 ls s3://backups/

# Cleanup local temp + creds
shred -u /tmp/B1_garage_creds_ciscokid.env /tmp/B1_smoke.bin /tmp/B1_smoke_roundtrip.bin
```

**Phase E acceptance:**
- `aws s3 ls` returns 3 buckets (atlas-state, backups, artifacts)
- 1KB PUT exit 0
- LIST shows the new object in s3://backups/
- GET roundtrip md5 byte-matches local md5 (`BYTE_PARITY_OK`)
- DELETE exit 0
- Final LIST shows empty s3://backups/
- Local creds file shred-removed from CiscoKid
- No new ERROR/FATAL in `docker logs control-garage-beast` (Beast side)

---

## Phase F -- Restart safety + cleanup + ship report

### Step F.1 -- Restart safety

```bash
cd /home/jes/garage-beast
docker compose restart
for i in $(seq 1 24); do
  STATUS=$(docker inspect control-garage-beast --format '{{.State.Health.Status}}' 2>/dev/null || echo unknown)
  echo "poll $i/24: $STATUS"
  [ "$STATUS" = "healthy" ] && break
  sleep 5
done
# Verify buckets persist post-restart
docker exec control-garage-beast /garage bucket list
docker exec control-garage-beast /garage status
```

### Step F.2 -- Cleanup intermediate Phase A inputs (preserve via archive)

```bash
mkdir -p /home/jes/garage-beast/.ship-report-inputs
mv /tmp/B1_garage_phase_a_*.txt /tmp/B1_garage_phase_b_compose_config.log /tmp/B1_garage_phase_c_ufw_post.txt /tmp/B1_garage_phase_d_bootstrap.log /home/jes/garage-beast/.ship-report-inputs/
# Keep the original Phase A captures from the MinIO branch in /tmp -- they're already the homelab baseline:
ls -la /tmp/B1_phase_a_*.txt 2>/dev/null
ls -la /home/jes/garage-beast/.ship-report-inputs/
```

### Step F.3 -- Ship report

File location on Beast: `/home/jes/garage-beast/B1_ship_report.md`. Content sections same as the original B1 spec plus:

- Pivot rationale: MinIO Community Edition archived 2026-02-14; CVE-2025-62506 in last image; alternatives evaluated (SeaweedFS, Garage, RustFS, MinIO-from-source); Garage selected for: actively maintained, single-container fit, single-node well-supported
- 8-gate scorecard with command output evidence
- Generated secrets disclosure pattern (NOT actual values; just file path + perms + how to read)
- Ports map: 3900 LAN exposed, 3903 localhost, 3901/3902/3904 container-internal only
- Restart safety: container persists; 3 buckets persist; node layout persists
- Smoke test from CiscoKid: byte-identical PUT/GET round-trip
- 6 P6 lessons banked from B1 (image archival as failure mode; pivot mid-spec; healthcheck must use /garage binary not wget)
- Open carryovers (P5: per-bucket IAM keys, TLS, object versioning, lifecycle policies)
- Time elapsed (Phase A start to F end)

**Phase F acceptance:**
- Container Up healthy post-restart
- All 3 buckets present post-restart
- `garage status` post-restart shows node still in HEALTHY NODES with assigned layout
- Ship report at /home/jes/garage-beast/B1_ship_report.md, all sections populated
- Phase A/B/C/D inputs archived to .ship-report-inputs/

---

## 8-gate acceptance scorecard (PD verifies all PASS)

1. **Container Up healthy:** `docker ps` shows control-garage-beast Up X (healthy); `docker inspect` health.status=healthy
2. **LAN listener exact:** `ss -tln` on Beast shows 192.168.1.152:3900 (S3 API) AND 127.0.0.1:3903 (admin); does NOT show 0.0.0.0:* on either; ports 3901/3902/3904 NOT in `ss -tln` Docker-published list
3. **UFW allow active:** `ufw status numbered` shows new ALLOW rule for 3900 from 192.168.1.0/24
4. **garage status healthy:** `docker exec control-garage-beast /garage status` returns the node with HEALTHY NODES + assigned layout (zone=dc1, capacity=4T)
5. **3 buckets present:** `garage bucket list` (from Beast) shows atlas-state, backups, artifacts, each with root key permissions
6. **Root key valid + scoped:** `garage key info root` shows authorized buckets = [atlas-state, backups, artifacts] with read+write+owner each
7. **Smoke PUT/GET/DELETE byte-parity from CiscoKid:** 1KB random object md5 matches between local and roundtrip; DELETE clears
8. **Persistence across restart:** post-restart, all 3 buckets still present, container healthy, node layout preserved, no data corruption

---

## Rollback

```bash
cd /home/jes/garage-beast
docker compose down -v
docker rmi dxflrs/garage:v2.1.0 2>/dev/null
sudo ufw delete allow from 192.168.1.0/24 to any port 3900 proto tcp
shred -u /home/jes/garage-beast/garage.toml /home/jes/garage-beast/.s3-creds 2>/dev/null
rm -rf /home/jes/garage-beast/ /home/jes/garage-data/
```

No other system component depends on B1 yet; rollback is clean.

---

## Time estimate

- Phase A delta + A2 rollback: <10 min
- Phase B (dirs + garage.toml + compose + image pull): 10-15 min
- Phase C (UFW): <5 min
- Phase D (deferred-subshell bootstrap): 10-15 min
- Phase E (CiscoKid smoke): 10-15 min
- Phase F (restart + cleanup + ship report): 15-20 min

**Total estimate: 50-80 min PD execution + ~15 min Paco independent verification.**

(MinIO branch had ~30 min of work done; ~10 min lost to rollback; ~50-80 min ahead. Net pivot cost: ~40-60 min.)

---

## PD-to-Paco report

Per-phase paco_review_b1_*.md docs to /home/jes/control-plane/docs/. Final ship report at /home/jes/garage-beast/B1_ship_report.md. Final close: paco_response_b1_independent_gate_pass_close.md.

---

## Standing rules

- **Rule 1:** B1 control plane via SSH + Compose + `garage` CLI inside container; data plane via S3 protocol over LAN. MCP control commands only. Compliant.
- **CLAUDE.md "Spec or no action":** all 6 picks ratified pre-draft; deviations require paco_request_b1_*.md.
- **CLAUDE.md "Docker bypasses UFW":** acknowledged; UFW is documented defense-in-depth. Real gates: LAN-bind + S3 access key auth.
- **Correspondence protocol:** per-phase paco_review_b1_*.md; final paco_response_b1_independent_gate_pass_close.md.

---

## P5 carryovers banked (post-B1)

- Per-bucket S3 keys (atlas-svc, backups-svc, artifacts-svc) with scoped permissions (replaces single-root-key v1)
- TLS for S3 API (Tailscale serve / self-signed cert / Let's Encrypt over Tailscale)
- Object lifecycle policies (auto-expire old artifacts, retention windows on backups)
- Versioning on the `backups` bucket (point-in-time recovery for Postgres dumps)
- Reverse SSH key from Beast to CiscoKid (admin convenience; not B1 dependency)

---

## P6 lessons banked at draft time (from MinIO discovery)

- **#7 -- Validate upstream maintenance status before drafting infra specs.** A pre-spec check on "is the Docker image in active distribution" should be standard for foundational substrates. MinIO Community Edition's archive happened ~2 months before our spec; one web search at draft time would have caught it.
- **#8 -- Pivot mid-spec is the right call when foundation is wrong.** Sloan's mantra ("end is the beginning") + measure-twice-cut-once held: catching the issue at Phase B (1 phase deep) cost ~40-60 min vs catching it post-ship which would have cost ~hours of integration unwind across Atlas + CiscoKid backups + portfolio assets.
- **#9 -- Healthcheck must use binaries that exist in the image.** `dxflrs/garage` is scratch-based, has no wget/curl/nc. Solution: use the application's own binary (`/garage status`). Future spec drafts: confirm healthcheck binary exists in target image before authoring.

---

**Spec status:** RATIFIED. Ready for PD execution.

-- Paco
