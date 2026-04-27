# PD -> Paco review -- B1 Phase B: dirs + .env + compose.yaml (digest-pinned)

**From:** PD (Head of Engineering, Cowork)
**To:** Paco (COO, claude.ai)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B1_minio_beast.md` Phase B
**Authorization:** `docs/paco_response_b1_phase_a_confirm_phase_b_go.md` (with two micro-refinements: -base64 60 password gen, deterministic digest sourcing via `docker inspect`)
**Phase:** B of 6 (A-F)
**Status:** **AWAITING PACO FIDELITY CONFIRMATION** before Phase C (2 UFW allow rules)
**Predecessor:** `docs/paco_review_b1_phase_a_capture.md`

---

## TL;DR

Phase B complete on Beast. **No service-affecting actions taken.** Three sub-steps: (B.1) directory tree (`minio-beast/` 0775 jes:jes + `minio-data/` 0700 jes:jes); (B.2) root creds generated via `openssl rand -base64 60 | tr -d '/+=' | head -c 40` -- 40-char alphanumeric, written to `.env` (chmod 600 jes:jes, 2 lines); (B.3) `docker pull quay.io/minio/minio:latest` -> digest captured -> compose.yaml written with digest-pinned image. `docker compose config` validates clean. B2a/B2b subscriber container untouched, UFW still 14 rules, ports 9000/9001 still unbound.

---

## Step B.1 -- Directory tree

```
$ mkdir -p /home/jes/minio-beast /home/jes/minio-data
$ chmod 700 /home/jes/minio-data

$ stat -c '%a %U:%G %n' /home/jes/minio-beast /home/jes/minio-data
775 jes:jes /home/jes/minio-beast      <-- default umask
700 jes:jes /home/jes/minio-data       <-- per spec (data dir restricted)
```

Note: per Paco's directive, dropped `init/` subdir from the spec text since B1 has no init scripts (bucket creation in Phase D via mc one-shot, not an init script convention like B2a's pgvector init).

## Step B.2 -- Root credentials (refined password pipeline)

```
ROOT_USER='atlas-admin'
ROOT_PASSWORD=$(openssl rand -base64 60 | tr -d '/+=' | head -c 40)
ROOT_PASSWORD_LEN=40   <-- verified before .env write

.env:                  /home/jes/minio-beast/.env
  perms:               -rw------- (0600) jes:jes
  size:                89 bytes
  lines:               2
  md5:                 2df7b7fb492e974b21e365c92a809cc1
  contains:            MINIO_ROOT_USER=atlas-admin
                       MINIO_ROOT_PASSWORD=<40-char alphanumeric>
```

The `-base64 60` source provides ~60 raw bytes of entropy; after stripping URL-unsafe `/+=` chars and truncating to 40 chars, the resulting password has approximately 40 * log2(64) ~= 240 bits of entropy (more than sufficient for the use case).

Password length pre-write check: passed (length=40, expected 40). If the trimming had stripped too much (e.g., if the openssl output had unusually many `/+=` chars), the script would have aborted before writing .env. Defensive validation per directive.

Generated password printed ONCE to subshell stdout for CEO 1Password recording. .env is now the only on-disk copy.

## Step B.3 -- Image pull + digest capture + compose.yaml

### Image pulled

```
$ docker pull quay.io/minio/minio:latest
... (10 layer fs Pull)
Digest: sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e
Status: Downloaded newer image for quay.io/minio/minio:latest
```

### Image metadata (informational)

```
Created:           2025-09-07T18:42:37Z
Size:              175494058 bytes (~167 MiB compressed)
Architecture:      amd64
Os:                linux
Base:              ubi9-micro-container (Red Hat Universal Base Image 9 Micro)
io.openshift.expose-services:  (declared)
io.k8s.description: "Very small image which doesn't install the package manager."
```

MinIO release built 2025-09-07 on a small RHEL UBI 9 micro base. Reasonable for a single-node S3 server.

### Captured RepoDigest

```
MINIO_REPODIGEST=quay.io/minio/minio@sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e
```

Validation: matched the regex `quay.io/minio/minio@sha256:*` per directive. Empty/malformed digest would have aborted the script before compose.yaml write.

### compose.yaml content (verbatim with digest substituted)

```yaml
services:
  minio:
    image: quay.io/minio/minio@sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e
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

```
compose.yaml metadata:
  path:                /home/jes/minio-beast/compose.yaml
  perms:               -rw-rw-r-- (0664) jes:jes (default umask)
  size:                536 bytes
  lines:               19
  md5:                 b965a49bc6e8ff2f5c88c043adb111ed
```

### `docker compose config` validation

Compose v5.1.3 parser resolved cleanly. Notable resolved values:

```
name: minio-beast            <-- auto-derived from directory
services.minio:
  command: [server, /data, --console-address, :9001]
  container_name: control-minio-beast
  environment:
    MINIO_ROOT_USER: atlas-admin
    MINIO_ROOT_PASSWORD: <40-char from .env>     <-- env_file resolution succeeded
  healthcheck:
    test: [CMD, mc, ready, local]
    interval: 30s
    timeout: 5s
    retries: 3
    start_period: 15s
  image: quay.io/minio/minio@sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e
  ports:
    - host_ip: 192.168.1.152, target: 9000
    - host_ip: 192.168.1.152, target: 9001
  restart: unless-stopped
  volumes:
    - type: bind, source: /home/jes/minio-data, target: /data
networks:
  default: name=minio-beast_default
```

No errors, no warnings, no unrecognized keys. Compose tooling on Beast (v5.1.3 from B2a bootstrap) handles digest-pinned images cleanly.

Full config output preserved at `/tmp/B1_phase_b_compose_config.log` (45 lines).

---

## 6-gate acceptance scorecard (6/6 PASS)

| # | Gate | Result | Evidence |
|---|---|---|---|
| 1 | minio-beast/ jes:jes; minio-data/ chmod 700 jes:jes | **PASS** | `775 jes:jes /home/jes/minio-beast`, `700 jes:jes /home/jes/minio-data` |
| 2 | .env chmod 600 jes:jes; 2 lines; password length 40 | **PASS** | `600 jes:jes`, `2 lines`, length-check passed pre-write |
| 3 | quay.io/minio/minio image pulled; digest in compose | **PASS** | image present with sha256 14cea493...; compose `image:` line shows digest-pinned form |
| 4 | compose.yaml exists, jes:jes, md5 captured | **PASS** | 0664 jes:jes, md5 `b965a49bc6e8ff2f5c88c043adb111ed` |
| 5 | docker compose config exit 0 with digest, ports, env_file | **PASS** | COMPOSE_CONFIG_OK; resolved env_file substitution + ports + bind mount + healthcheck |
| 6 | NO service-affecting changes (B2a still healthy, UFW still 14, ports still unbound) | **PASS** | control-postgres-beast Up 2 hours (healthy), StartedAt 2026-04-27T00:13:57Z (unchanged from B2b Phase E), RestartCount=0, UFW=14 rules, ports 9000/9001 still free |

## State integrity (B2a/B2b unaffected -- gate 6 detail)

```
control-postgres-beast:                       Up 2 hours (healthy), 127.0.0.1:5432->5432/tcp
  StartedAt:                                  2026-04-27T00:13:57.800Z (B2b Phase E recreate timestamp)
  RestartCount:                               0
  pg_subscription:                            (cross-host, unaffected; subscription-side state unchanged)

UFW:                                          14 rules (unchanged from Phase A baseline)
Ports 9000/9001:                              still free (no listeners)

Phase A capture artifacts:                    /tmp/B1_phase_a_*.txt -- intact
Phase B new artifacts:                        /home/jes/minio-beast/.env (md5 2df7b7fb...), /home/jes/minio-beast/compose.yaml (md5 b965a49b...), /home/jes/minio-data/ (empty 0700)
B2a/B2b artifacts:                            /home/jes/postgres-beast/ + /tmp/B2b rollback files -- untouched
```

## Phase C preview (informational, not yet authorized)

Per spec Phase C: 2 UFW allow rules for ports 9000+9001 from 192.168.1.0/24. Per Paco directive: simple `ufw allow ...` (NOT `ufw insert`) -- no DENY collision exists for these ports unlike B2b's 5432 case. New rules will land at end of UFW table (positions 15+).

Reference commands:
```bash
sudo ufw allow from 192.168.1.0/24 to any port 9000 proto tcp comment 'B1: MinIO S3 API'
sudo ufw allow from 192.168.1.0/24 to any port 9001 proto tcp comment 'B1: MinIO web console'
sudo ufw status numbered  # capture +2 new rules at end
```

## Asks of Paco

1. Confirm Phase B fidelity:
   - Directory perms (0775 / 0700)
   - .env perms (0600), 2 lines, length 40
   - Image digest captured: `sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e`
   - compose.yaml md5 `b965a49bc6e8ff2f5c88c043adb111ed` (536 bytes / 19 lines)
   - `docker compose config` exit 0
   - B2a/B2b unaffected; UFW still 14 rules; ports 9000/9001 still unbound
2. **Go for Phase C** -- 2 UFW allow rules (9000+9001 from 192.168.1.0/24) using `ufw allow` (not insert)

## Standing rules in effect

- **Rule 1:** Phase B = local file creation + 1 docker pull. No bulk transport via MCP. Compliant.
- **CLAUDE.md "Spec or no action":** two micro-refinements explicitly Paco-authorized in Phase B directive (-base64 60 password gen w/ length validation; deterministic digest via `docker inspect`). No further deviations.
- **CLAUDE.md "Docker bypasses UFW":** still defense-in-depth posture; UFW will be added in Phase C; real gates remain LAN-bind + auth (root creds via .env).
- **Correspondence protocol:** this is paco_review #2 of 6 planned for B1.
- **Canon location:** B1 artifacts on Beast (workspace) + review docs on CiscoKid (canon). Per memory edit #20.
- **Credential handling:** root password printed once to subshell stdout for CEO 1Password recording. .env (chmod 600) is the only on-disk copy. Future P5 carryover: rotate to per-service IAM.

---

**File location:** `/home/jes/control-plane/docs/paco_review_b1_phase_b_compose.md` (untracked, matches /docs precedent)

-- PD
