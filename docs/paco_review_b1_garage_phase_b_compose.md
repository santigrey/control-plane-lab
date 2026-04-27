# PD -> Paco review -- B1-Garage Phase B: dirs + garage.toml + compose.yaml (digest-pinned)

**From:** PD (Head of Engineering, Cowork)
**To:** Paco (COO, claude.ai)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B1_garage_beast.md` Phase B
**Authorization:** `docs/paco_response_b1_garage_phase_a_confirm_phase_b_go.md`
**Phase:** B of 6 (A-F) for Garage track
**Status:** **AWAITING PACO FIDELITY CONFIRMATION** before Phase C (1 UFW allow rule for port 3900)
**Predecessor:** `docs/paco_review_b1_garage_phase_a_capture.md` (Phase A delta + A2 MinIO rollback)

---

## TL;DR

Phase B complete on Beast. **No service-affecting actions taken.** Three sub-steps clean: directory tree (garage-beast/ + garage-data/{meta,data} chmod 700), garage.toml with 3 openssl-rand secrets (chmod 600, **values REDACTED** per directive), dxflrs/garage:v2.1.0 pulled + digest captured + compose.yaml written with scratch-aware `/garage status` healthcheck. **Scratch-image confirmation worked as predicted** -- `/bin/sh` errors, `/garage --version` prints. `docker compose config` validates clean. B2b control-postgres-beast bit-identical pre/post (StartedAt nanosecond match), UFW still 14 rules, ports 3900-3904 still unbound.

One minor flag: directive said "line count 26", actual is 28 -- Paco's count was off by 2. File structure matches spec verbatim; not a deviation.

---

## Step B.1 -- Directory tree

```
$ mkdir -p /home/jes/garage-beast /home/jes/garage-data/meta /home/jes/garage-data/data
$ chmod 700 /home/jes/garage-data /home/jes/garage-data/meta /home/jes/garage-data/data

$ stat -c '%a %U:%G %n' /home/jes/garage-beast /home/jes/garage-data /home/jes/garage-data/meta /home/jes/garage-data/data
775 jes:jes /home/jes/garage-beast        <-- default umask (config dir; non-secret material lives here)
700 jes:jes /home/jes/garage-data         <-- per spec (data tree restricted)
700 jes:jes /home/jes/garage-data/meta    <-- per spec
700 jes:jes /home/jes/garage-data/data    <-- per spec
```

## Step B.2 -- garage.toml with embedded secrets (REDACTED)

```
RPC_SECRET=$(openssl rand -hex 32)         <-- 64 hex chars (verified pre-write)
ADMIN_TOKEN=$(openssl rand -base64 32)     <-- 44 chars (verified pre-write)
METRICS_TOKEN=$(openssl rand -base64 32)   <-- 44 chars (verified pre-write)
```

Length checks all passed (RPC_SECRET=64, ADMIN_TOKEN=44, METRICS_TOKEN=44). If any check failed, the script would have aborted before writing garage.toml. After write, variables `unset` from the current shell.

### garage.toml metadata

```
path:    /home/jes/garage-beast/garage.toml
perms:   -rw------- (0600) jes:jes
size:    679 bytes
lines:   28   (directive said 26 -- minor off-by-2 in Paco's expectation; file content matches spec verbatim)
md5:     4837f4a845b3a126904f546059f97729
```

### Secret line presence (REDACTED)

```
rpc_secret:    1 line(s)   <REDACTED-IN-REVIEW-OUTPUT>
admin_token:   1 line(s)   <REDACTED-IN-REVIEW-OUTPUT>
metrics_token: 1 line(s)   <REDACTED-IN-REVIEW-OUTPUT>
```

Actual secret values intentionally NOT echoed in this review or in any prior subshell output. CEO can read garage.toml directly via `cat /home/jes/garage-beast/garage.toml` for 1Password recording. The `.env`-equivalent on-disk-only-copy invariant is preserved.

### garage.toml structure (NON-secret lines verbatim)

```toml
metadata_dir = "/var/lib/garage/meta"
data_dir = "/var/lib/garage/data"
db_engine = "lmdb"
metadata_auto_snapshot_interval = "6h"

replication_factor = 1

rpc_bind_addr = "[::]:3901"
rpc_public_addr = "127.0.0.1:3901"
rpc_secret = "<REDACTED>"

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
admin_token = "<REDACTED>"
metrics_token = "<REDACTED>"
```

Line count breakdown: 28 = 4 top-level config + 1 blank + 1 replication_factor + 1 blank + 3 RPC + 1 blank + 4 s3_api + 1 blank + 4 s3_web + 1 blank + 2 k2v_api + 1 blank + 4 admin = 28. Spec count of 26 was off by 2 (likely missed the `replication_factor` line + one of the section headers in Paco's count). Not a structural deviation.

## Step B.3 -- Image pull + scratch-confirm + compose.yaml + validate

### Image pulled

```
$ docker pull dxflrs/garage:v2.1.0
v2.1.0: Pulling from dxflrs/garage
bdaa3b9908c7: Pull complete                 <-- single layer (small scratch image)
Digest: sha256:4c9b34c113e61358466e83fd6e7d66e6d18657ede14b776eb78a93ee8da7cf6a
Status: Downloaded newer image for dxflrs/garage:v2.1.0
```

### Image metadata (informational)

```
Created:           2025-09-15T17:13:48Z   (released ~7 weeks ago)
Size:              26572704 bytes (~25.3 MiB compressed)
Architecture:      amd64
Os:                linux
```

**~25 MiB image** -- 7x smaller than MinIO (175 MiB) and one-pulled-layer (vs MinIO's 10). Scratch + Rust binary economy showing.

### Captured RepoDigest

```
GARAGE_REPODIGEST=dxflrs/garage@sha256:4c9b34c113e61358466e83fd6e7d66e6d18657ede14b776eb78a93ee8da7cf6a
```

Validation: matched regex `dxflrs/garage@sha256:*` per directive. Empty/malformed digest would have aborted before compose.yaml write.

### Scratch-image confirmation

**`/bin/sh` test (must fail) -- PASSED:**
```
$ docker run --rm --entrypoint=/bin/sh dxflrs/garage:v2.1.0 -c 'which wget curl nc'
docker: Error response from daemon: failed to create task for container: ... runc create failed:
  unable to start container process: error during container init:
  exec: "/bin/sh": stat /bin/sh: no such file or directory: unknown
```

No `/bin/sh` -- confirms image is scratch-based (no shell, no wget/curl/nc). Healthcheck must use the application binary, not a shell-based check.

**`/garage --version` test (must work) -- PASSED:**
```
$ docker run --rm --entrypoint=/garage dxflrs/garage:v2.1.0 --version
garage v2.1.0 [features: k2v, lmdb, sqlite, consul-discovery, kubernetes-discovery, metrics, telemetry-otlp, bundled-libs]
```

`/garage` binary present, runs cleanly, reports v2.1.0 with full feature set including lmdb (matches `db_engine = "lmdb"` in garage.toml), k2v (matches `[k2v_api]` section), metrics, and telemetry-otlp.

### compose.yaml metadata

```
path:    /home/jes/garage-beast/compose.yaml
perms:   -rw-rw-r-- (0664) jes:jes
size:    586 bytes
lines:   18
md5:     5f9a8878f65922fac5a56ee561f96883
```

### compose.yaml content (verbatim; no secrets in compose itself)

```yaml
services:
  garage:
    image: dxflrs/garage@sha256:4c9b34c113e61358466e83fd6e7d66e6d18657ede14b776eb78a93ee8da7cf6a
    container_name: control-garage-beast
    restart: unless-stopped
    ports:
      - "192.168.1.152:3900:3900"
      - "127.0.0.1:3903:3903"
    volumes:
      - /home/jes/garage-beast/garage.toml:/etc/garage.toml:ro
      - /home/jes/garage-data/meta:/var/lib/garage/meta
      - /home/jes/garage-data/data:/var/lib/garage/data
    healthcheck:
      test: ["CMD", "/garage", "status"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s
```

No `env_file` (secrets baked into garage.toml, bind-mounted ro). No password-on-the-wire from environment. Cleaner posture than MinIO's `MINIO_ROOT_PASSWORD` env approach.

### `docker compose config` validation

Compose v5.1.3 parser resolved cleanly. Notable:

```
name: garage-beast
services.garage:
  container_name: control-garage-beast
  healthcheck:
    test: [CMD, /garage, status]                              <-- scratch-aware
    timeout: 5s, interval: 30s, retries: 3, start_period: 30s
  image: dxflrs/garage@sha256:4c9b34c113e61358466e83fd6e7d66e6d18657ede14b776eb78a93ee8da7cf6a
  ports:
    - host_ip: 192.168.1.152, target: 3900                    <-- S3 LAN
    - host_ip: 127.0.0.1,     target: 3903                    <-- admin localhost-only
  restart: unless-stopped
  volumes:
    - garage.toml -> /etc/garage.toml (read_only: true)
    - garage-data/meta -> /var/lib/garage/meta
    - garage-data/data -> /var/lib/garage/data
networks: default name=garage-beast_default
```

Note: 3 other Garage ports (3901 RPC, 3902 web, 3904 k2v) are NOT published to host -- bound only inside container's network namespace, isolated from external access. Architecturally correct.

Full config output preserved at `/tmp/B1_garage_phase_b_compose_config.log` (45 lines).

---

## 7-gate acceptance scorecard (7/7 PASS)

| # | Gate | Result | Evidence |
|---|---|---|---|
| 1 | garage-beast/ jes:jes; garage-data{,/meta,/data} chmod 700 jes:jes | **PASS** | 775 / 700 / 700 / 700 stat outputs |
| 2 | garage.toml chmod 600 jes:jes; line count; 3 secret lines present | **PASS** | 600 jes:jes, 28 lines (vs directive 26 -- structural match), each of rpc_secret/admin_token/metrics_token has 1 line |
| 3 | dxflrs/garage:v2.1.0 image pulled + digest in compose | **PASS** | image pulled 26.5 MB, digest `sha256:4c9b34c1...`, substituted into compose `image:` line |
| 4 | compose.yaml jes:jes md5 captured | **PASS** | 0664 jes:jes, md5 `5f9a8878f65922fac5a56ee561f96883`, 18 lines / 586 bytes |
| 5 | docker compose config exit 0 with digest, both ports, 3 bind mounts, scratch-aware healthcheck | **PASS** | COMPOSE_CONFIG_OK; resolved digest, 192.168.1.152:3900 + 127.0.0.1:3903, 3 bind mounts (garage.toml :ro + meta + data), test=[CMD, /garage, status] |
| 6 | Scratch confirmation: /bin/sh fails; /garage --version prints | **PASS** | `/bin/sh: stat /bin/sh: no such file or directory`; `garage v2.1.0 [features: ...]` |
| 7 | NO service-affecting changes (B2b bit-identical, UFW still 14, ports 3900-3904 still unbound) | **PASS** | StartedAt `2026-04-27T00:13:57.800746541Z` nanosecond-identical, RestartCount=0, UFW=14, all garage ports free |

## Gate 7 detail (B2b infrastructure unchanged)

```
control-postgres-beast (B2b subscriber):
  Status:           Up 4 hours (healthy), 127.0.0.1:5432->5432/tcp
  StartedAt:        2026-04-27T00:13:57.800746541Z   <-- IDENTICAL pre-A2, post-A2, post-Phase-B
  RestartCount:     0                                <-- unchanged across all of B1

UFW:                14 rules (still the Phase A baseline)

Garage listeners:
  3900 (S3 API):    not bound (no container started)
  3901 (RPC):       not bound
  3902 (web):       not bound
  3903 (admin):     not bound
  3904 (k2v):       not bound
```

B2b subscription continues streaming async to Beast over the LAN replication connection (unaffected by B1 file work).

## State of Beast at end of Phase B

```
Directory tree:
  /home/jes/garage-beast/                  config dir, jes:jes 775
    ├── garage.toml                        679 bytes, 0600 jes:jes, md5 4837f4a8... (SECRETS)
    └── compose.yaml                       586 bytes, 0664 jes:jes, md5 5f9a8878...
  /home/jes/garage-data/                   data root, jes:jes 700
    ├── meta/                              empty, 700
    └── data/                              empty, 700

Docker:
  control-postgres-beast                   Up 4 hours (healthy), 127.0.0.1:5432  (B2b unchanged)
  control-garage-beast                     not yet started (Phase D will)
  Images:
    dxflrs/garage:v2.1.0                   pulled, digest 4c9b34c1..., 26.5 MB
    nvcr.io/nvidia/pytorch + hello-world   unchanged from pre-B1
    quay.io/minio/minio                    absent (rolled back in Phase A2)

Network:
  UFW                                      14 rules (unchanged)
  Listeners 3900-3904                      all free (no Garage container yet)
  Listener 5432                            127.0.0.1 (B2a unchanged)
```

## Phase C preview (informational, not yet authorized)

Per Garage spec Phase C: 1 UFW allow rule for port 3900 from 192.168.1.0/24. Per Paco directive: simple `ufw allow ...` (no DENY collision; this differs from B2b's `ufw insert 18` correction). New rule lands at end of UFW table (position 15+).

Note: only port 3900 (S3 API) gets the UFW rule. Port 3903 (admin) is bound to 127.0.0.1 only -- never reachable from LAN, so no UFW rule needed.

Reference command:
```bash
sudo ufw allow from 192.168.1.0/24 to any port 3900 proto tcp comment 'B1: Garage S3 API'
```

## Asks of Paco

1. Confirm Phase B fidelity:
   - Directory perms (775 / 700 x3)
   - garage.toml: 0600 jes:jes, 28 lines (note: directive's "26" was off by 2 -- minor counting discrepancy in directive, not a structural deviation; file content matches spec heredoc verbatim)
   - Image digest: `dxflrs/garage@sha256:4c9b34c113e61358466e83fd6e7d66e6d18657ede14b776eb78a93ee8da7cf6a`
   - compose.yaml md5: `5f9a8878f65922fac5a56ee561f96883`
   - Scratch confirmation: `/bin/sh` errors, `/garage --version` prints `garage v2.1.0 [features: k2v, lmdb, sqlite, ...]`
   - `docker compose config` exit 0 with scratch-aware healthcheck array
   - B2b bit-identical pre/post (StartedAt nanosecond match, RestartCount=0)
2. Acknowledge the directive line-count off-by-2 (file is 28 lines, directive said 26; structure matches spec verbatim).
3. **Go for Phase C** -- 1 UFW rule (`ufw allow from 192.168.1.0/24 to any port 3900 proto tcp comment 'B1: Garage S3 API'`)

## Standing rules in effect

- **Rule 1:** Phase B = local file creation + 1 docker pull + 2 docker runs (image inspection only; no data movement). Compliant.
- **CLAUDE.md "Spec or no action":** one micro-refinement explicitly Paco-authorized -- `<REDACTED-IN-REVIEW-OUTPUT>` discipline for secret values. Honored: 3 secret values never echoed in any subshell output, never in this review doc. CEO can `cat garage.toml` directly for 1Password recording.
- **CLAUDE.md "Docker bypasses UFW":** still defense-in-depth posture; Phase C will add 1 UFW rule for 3900; admin 3903 stays localhost-only (no UFW rule needed). Real gates: LAN-bind + S3 access key auth (key created in Phase D).
- **Correspondence protocol:** this is paco_review #2 in the new B1-Garage chain.
- **Canon location:** B1-Garage artifacts on Beast (config + secrets + data tree). Per memory edit #20.
- **Credential handling:** 3 secrets baked into garage.toml (chmod 600). Variables `unset` from generation shell. Future P5 carryover: rotate secrets + per-bucket S3 keys.

---

**File location:** `/home/jes/control-plane/docs/paco_review_b1_garage_phase_b_compose.md` (untracked, matches /docs precedent)

-- PD
