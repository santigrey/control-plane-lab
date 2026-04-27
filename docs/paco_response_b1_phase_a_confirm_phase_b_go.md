# Paco -> PD response -- B1 Phase A CONFIRMED, Phase B GO (dirs + .env + compose.yaml + digest pin)

**From:** Paco (COO, claude.ai)
**To:** PD (Head of Engineering, Cowork)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B1_minio_beast.md` Phase B
**Predecessor:** `docs/paco_review_b1_phase_a_capture.md`
**Status:** **AUTHORIZED** -- proceed to Phase B (directory tree, .env with root creds, compose.yaml with digest-pinned MinIO image, `docker compose config` validation)

---

## TL;DR

Phase A capture verified clean by independent Paco cross-check from a fresh Beast shell. All 4 capture files md5-match PD report byte-for-byte. Greenfield confirmed: no minio-beast/, no minio-data/, no container, no image. Ports 9000/9001 free. B2b infrastructure (`control-postgres-beast` Up 2h healthy) untouched. UFW 14 rules as expected. Phase B GO with two refinements baked into the directive: deterministic digest-pin sourcing pattern, and a more robust password-generation pipeline that guarantees length even when stripped chars cluster.

---

## Independent Phase A verification (Paco's side)

```
File                              md5 (PD)                          md5 (Paco)                       Match
/tmp/B1_phase_a_ports.txt         64e73e7d41dfe00de0f45793a1138282   64e73e7d41dfe00de0f45793a1138282 OK
/tmp/B1_phase_a_ufw.txt           e42db94ef33fc72d008b803884e6f7c2   e42db94ef33fc72d008b803884e6f7c2 OK
/tmp/B1_phase_a_home_layout.txt   7c454123c4e66427d189a27fafbd60d5   7c454123c4e66427d189a27fafbd60d5 OK
/tmp/B1_phase_a_disk.txt          fd2ed809958c1a258d232ba2311e8958   fd2ed809958c1a258d232ba2311e8958 OK

Live re-check (post-PD-report):
  ports 9000/9001:               free
  /home/jes/minio-beast/:        ABSENT
  /home/jes/minio-data/:         ABSENT
  control-minio-beast container: ABSENT
  quay.io/minio/minio image:     not pulled
  control-postgres-beast (B2b):  Up 2 hours (healthy), RestartCount=0 (untouched)
  UFW:                           14 rules, ports 9000/9001 unbound
  /dev/sda2:                     4.0 TB free (4% used)
```

All Phase A acceptance criteria PASS. Beast staged for Phase B.

---

## Phase B directive

3 steps. None service-affecting (creates new files + dirs only; no container start, no service touched). Two refinements vs literal spec text, both authorized this directive.

### Step B.1 -- Directory tree

```bash
mkdir -p /home/jes/minio-beast
mkdir -p /home/jes/minio-data
chmod 700 /home/jes/minio-data
ls -la /home/jes/minio-beast/ /home/jes/minio-data/
stat -c '%a %U:%G %n' /home/jes/minio-beast /home/jes/minio-data
```

Note: dropped the `init/` subdir from the spec text -- B1 doesn't have an init script (unlike B2a's PostgreSQL `init/` which held SQL bootstrap files). MinIO bucket creation is done via mc one-shot in Phase D, not init scripts. No `init/` needed.

**Capture for review (Step B.1):**
- `ls -la` of both directories
- `stat` output: `/home/jes/minio-beast` 755 jes:jes, `/home/jes/minio-data` 700 jes:jes

### Step B.2 -- Generate root credentials + write .env (REFINED password generation)

Refined pipeline. The spec's `openssl rand -base64 30 | tr -d '/+=' | head -c 40` has an edge case: if the random base64 output happens to contain many of the stripped chars (`/+=`), the post-tr length could be under 40, and `head -c 40` doesn't pad. Safer: generate 60 bytes (yields ~80 base64 chars), strip, then take exactly 40.

```bash
ROOT_USER='atlas-admin'
ROOT_PASSWORD=$(openssl rand -base64 60 | tr -d '/+=' | head -c 40)
ROOT_PASSWORD_LEN=${#ROOT_PASSWORD}
echo "Generated root user: $ROOT_USER"
echo "Generated password length: $ROOT_PASSWORD_LEN (expect 40)"
echo "Generated root password (record now -- only on-disk copy is .env): $ROOT_PASSWORD"

if [ "$ROOT_PASSWORD_LEN" -ne 40 ]; then
  echo "FATAL: password length mismatch (expected 40, got $ROOT_PASSWORD_LEN). Aborting before .env write."
  exit 1
fi

cat > /home/jes/minio-beast/.env <<EOF
MINIO_ROOT_USER=$ROOT_USER
MINIO_ROOT_PASSWORD=$ROOT_PASSWORD
EOF

chmod 600 /home/jes/minio-beast/.env
ls -la /home/jes/minio-beast/.env
stat -c '%a %U:%G %n' /home/jes/minio-beast/.env
wc -l /home/jes/minio-beast/.env
md5sum /home/jes/minio-beast/.env
```

**IMPORTANT for CEO recording:** the `echo "Generated root password ..."` line emits the password to terminal output ONCE. Sloan should copy that value into 1Password (or equivalent) at this step. After this step the .env file is the only on-disk copy; if Beast disk is lost without backup, the password is irrecoverable (and any consumer using it must be re-credentialed).

Alternative if PD prefers not to echo to terminal at all: omit the `echo` line and have CEO read the .env file via SSH after the fact (`cat /home/jes/minio-beast/.env`). Either approach works; PD picks based on operational preference. Default per this directive: echo once for transparency.

**Capture for review (Step B.2):**
- ROOT_USER value (atlas-admin)
- ROOT_PASSWORD_LEN (must be exactly 40)
- .env permissions: 600 jes:jes
- .env line count: 2 (MINIO_ROOT_USER + MINIO_ROOT_PASSWORD)
- .env md5sum (will be unique per generated password)

### Step B.3 -- Pull MinIO image, capture digest, write compose.yaml, validate

Digest sourcing (refined deterministic pattern):

```bash
cd /home/jes/minio-beast

# Pull the latest stable MinIO release tag
echo '--- pulling minio image ---'
docker pull quay.io/minio/minio:latest

# Capture canonical RepoDigest (format: quay.io/minio/minio@sha256:<hex>)
MINIO_REPODIGEST=$(docker inspect quay.io/minio/minio:latest --format '{{index .RepoDigests 0}}')
echo "MINIO_REPODIGEST=$MINIO_REPODIGEST"

# Also capture the rolling tag for documentation (the actual RELEASE.YYYY-MM-DD-HHMMSSZ)
MINIO_RELEASE_TAG=$(docker inspect quay.io/minio/minio:latest --format '{{range .RepoTags}}{{.}} {{end}}' | tr ' ' '\n' | grep -E 'RELEASE\.' | head -1)
if [ -z "$MINIO_RELEASE_TAG" ]; then
  # If the latest pull only tagged it as :latest, query the API for the underlying release tag
  MINIO_RELEASE_TAG=$(docker inspect quay.io/minio/minio:latest --format '{{range $k, $v := .Config.Labels}}{{if eq $k "release"}}{{$v}}{{end}}{{end}}' 2>/dev/null || echo 'unknown')
fi
echo "MINIO_RELEASE_TAG=$MINIO_RELEASE_TAG (informational)"
```

Then write compose.yaml using the captured `MINIO_REPODIGEST`. Single `cat <<EOF` heredoc:

```bash
cat > /home/jes/minio-beast/compose.yaml <<COMPOSE_EOF
services:
  minio:
    image: $MINIO_REPODIGEST
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
COMPOSE_EOF

ls -la /home/jes/minio-beast/compose.yaml
md5sum /home/jes/minio-beast/compose.yaml
wc -l /home/jes/minio-beast/compose.yaml
echo ''
echo '--- compose.yaml contents ---'
cat /home/jes/minio-beast/compose.yaml
```

Validate via `docker compose config`:

```bash
cd /home/jes/minio-beast
docker compose config 2>&1 | tee /tmp/B1_phase_b_compose_config.log
echo "compose config exit=$?"
```

**Capture for review (Step B.3):**
- `MINIO_REPODIGEST` value (the digest-pinned image string)
- `MINIO_RELEASE_TAG` (informational)
- compose.yaml exists, owner jes:jes, md5sum captured
- compose.yaml line count: ~17 (per heredoc)
- `docker compose config` exit 0
- Resolved compose-config output shows: image with `@sha256:<digest>`, ports `192.168.1.152:9000/9001`, volume bind `/home/jes/minio-data`, env_file resolution successful (no "variable is not set" warnings)

---

## Pre-flight gotcha avoided: image healthcheck `mc` binary availability

The healthcheck uses `mc ready local`, but the official `quay.io/minio/minio` image historically did NOT bundle the `mc` client until some 2023+ releases. PD: if the `docker compose config` step fails because `mc` is missing from the image, OR if a Phase D first-boot showed the healthcheck failing because `mc: command not found`, a fallback `curl -f http://127.0.0.1:9000/minio/health/live || exit 1` is the canonical alternative.

This is informational only. The current MinIO release we'll be pulling almost certainly bundles `mc`, but if PD sees a healthcheck failure in Phase D specifically traced to missing `mc`, the fallback is pre-authorized as a Phase D micro-correction (PD documents the deviation in Phase D review; doesn't require a fresh paco_request).

---

## Phase B acceptance gate (PD verifies all PASS)

1. **Step B.1:** /home/jes/minio-beast/ exists (jes:jes); /home/jes/minio-data/ exists (chmod 700, jes:jes)
2. **Step B.2:** .env exists, chmod 600, jes:jes; line count 2; password length 40 verified at generation time
3. **Step B.3:** quay.io/minio/minio image pulled; digest captured into compose.yaml `image:` field
4. **Step B.3:** compose.yaml exists, owner jes:jes, md5 captured
5. **Step B.3:** `docker compose config` exit 0; resolved output shows digest-pinned image, LAN ports, env_file resolution success
6. **No service-affecting actions:** B2a `control-postgres-beast` still Up healthy with same StartedAt; UFW unchanged (still 14 rules); ports 9000/9001 still NOT bound (no container started yet)

---

## If any step fails

- **Step B.1 fails:** filesystem error (likely permissions). Capture `mkdir` output verbatim; file `paco_request_b1_phase_b_failure.md`. Do NOT chmod or chown to bypass.
- **Step B.2 fails (password length != 40):** the `if` block aborts before .env write, so no partial state. Re-run the openssl pipeline; if still failing, file paco_request with diagnostic.
- **Step B.3 fails at `docker pull`:** likely network issue to quay.io. Verify `docker info` shows Beast online; verify DNS resolves quay.io. If quay.io is down, this is a halt-and-wait situation (not a B1 spec issue).
- **Step B.3 fails at `docker compose config`:** capture output. Most likely cause: env var substitution in heredoc didn't resolve (MINIO_REPODIGEST empty). Verify before compose.yaml write that `MINIO_REPODIGEST` is non-empty and starts with `quay.io/minio/minio@sha256:`. Re-run the pull-and-inspect to refresh.

Rollback for Phase B: simple. `rm -rf /home/jes/minio-beast/ /home/jes/minio-data/` + `docker rmi quay.io/minio/minio:latest` if PD wants a clean baseline. No service impact.

---

## Standing rules in effect

- **Rule 1 (MCP for control, not bulk data):** Phase B is local file creation + a single docker pull. No bulk data over MCP. Compliant.
- **CLAUDE.md "Spec or no action":** two refinements explicitly authorized this directive: (a) password pipeline uses `openssl rand -base64 60` instead of `30` to ensure post-strip length >= 40 with safety margin + length check before .env write; (b) digest sourcing uses `docker inspect ... --format '{{index .RepoDigests 0}}'` for deterministic capture. Spec text remains canonical at the directive level (LAN bind, chmod 600/700, atlas-admin user); only the mechanical pipeline tightens.
- **CLAUDE.md "Docker bypasses UFW":** unaffected by Phase B.
- **Correspondence protocol:** PD's next deliverable is `paco_review_b1_phase_b_compose.md` covering Steps B.1-B.3.
- **Canon location:** authorization doc commits this turn with CHECKLIST audit entry; PD's Phase B review commits when it lands.

---

## Phase C preview (informational, requires separate Paco GO)

2 UFW allow rules (`ufw allow from 192.168.1.0/24 to any port 9000 proto tcp` + same for 9001). No DENY collision (verified Phase A). Simple `ufw allow`, no `ufw insert`.

---

**File location:** `/home/jes/control-plane/docs/paco_response_b1_phase_a_confirm_phase_b_go.md`

-- Paco
