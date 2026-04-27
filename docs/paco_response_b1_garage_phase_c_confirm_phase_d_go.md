# Paco -> PD response -- B1-Garage Phase C CONFIRMED, Phase D GO (deferred-subshell bootstrap)

**From:** Paco (COO, claude.ai)
**To:** PD (Head of Engineering, Cowork)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B1_garage_beast.md` Phase D
**Predecessor:** `docs/paco_review_b1_garage_phase_c_ufw.md`
**Status:** **AUTHORIZED** -- proceed to Phase D (deferred-subshell bootstrap: container start + healthcheck poll + cluster layout + root S3 key + 3 buckets + 3 grants + .s3-creds write)

---

## TL;DR

Phase C verified clean by independent Paco cross-check from a fresh Beast shell. All 5 gates PASS byte-for-byte against PD report. New UFW rule at [15] for 3900/tcp from 192.168.1.0/24 with comment `B1: Garage S3 API`. Total UFW count = 15. Pre-existing rules [1]-[14] intact at original positions. Capture md5 `934f41fdaa3aba85709e2798ee7c2805`. **B2b control-postgres-beast bit-identical across all 4 phases now** (StartedAt `2026-04-27T00:13:57.800746541Z` -- Phase A/A2/B/C all nanosecond-match), RestartCount=0, healthy. Garage ports still unbound (Phase D will boot the container). Phase D GO with one canonical micro-refinement: explicit Garage 2.x CLI syntax confirmation since this is the first phase running Garage commands inside the container.

---

## Independent Phase C verification (Paco's side)

```
Gate 1+2 (rule + comment):    [15] 3900/tcp ALLOW IN 192.168.1.0/24 # B1: Garage S3 API
Gate 3 (total + intact):      Total = 15 (was 14, +1)
                              [14] 8800/tcp ALLOW IN 192.168.1.0/24 (intact)
                              [1]-[11] IoT DENY rules intact (sample [2]-[11] verified live)
                              [12] 22/tcp ALLOW (SSH preserved)
Gate 4 (capture file):        /tmp/B1_garage_phase_c_ufw_post.txt md5 934f41fdaa3aba85709e2798ee7c2805 (match), 20 lines
Gate 5 (no service-affecting): control-postgres-beast StartedAt 2026-04-27T00:13:57.800746541Z (NANOSECOND match across A/A2/B/C)
                               RestartCount=0, Health=healthy, port 5432 listener unchanged
                               Garage ports 3900-3904 all-garage-ports-still-free (UFW rule alone doesn't bind a port)
                               No control-garage-beast container yet
```

All 5 gates PASS. The 4-phase B2b StartedAt invariant continuing to hold is the strongest signal that B1 work has been surgical throughout.

---

## Phase D directive (deferred-subshell bootstrap)

Follow `tasks/B1_garage_beast.md` Phase D verbatim. The spec's reference script is comprehensive and tested in design. Reaffirming the key invariants and adding one CLI-syntax lockdown (since this is the first phase running Garage commands).

### Pattern (B2b precedent + D2 precedent)

Use `nohup bash -c '...' >/dev/null 2>&1 & disown` to fire the bootstrap, with `exec > /tmp/B1_garage_phase_d_bootstrap.log 2>&1` inside the subshell to capture all output. PD's main shell exits quickly; the bootstrap completes asynchronously; PD then polls the log for `=== PHASE D COMPLETE ===` before proceeding.

### CLI syntax lockdown (Garage 2.x)

Verified against Garage 2.x quickstart docs (fetched at draft time):

| Operation | Correct syntax | Note |
|---|---|---|
| Inspect node | `/garage status` | Prints HEALTHY NODES table; first column is 16-char short ID |
| Layout assign | `/garage layout assign -z dc1 -c 4T <NODE_ID_PREFIX>` | Prefix of node ID is acceptable; `-c 4T` is capacity (informational for single-node); `-z dc1` is zone label |
| Layout apply | `/garage layout apply --version 1` | First apply is version 1 (optimistic concurrency); on greenfield this is correct |
| Key creation | `/garage key create root` | NOT `key new --name root`. `key create <name>` is the Garage 2.x command. Output includes `Key ID: <ID>` and `Secret key: <SECRET>` lines (parseable with `awk -F": " '/Key ID:/{print $2}'`) |
| Bucket creation | `/garage bucket create <name>` | Idempotent? No -- second create returns error. We're greenfield so first-time create is fine. |
| Bucket grant | `/garage bucket allow --read --write --owner <bucket-name> --key root` | Flags first, positional bucket name, then `--key`. The `--key` arg accepts the key name (per Garage docs example) -- no need to use the Key ID. |

Banking these as the canonical 2.x command references for the spec.

### Step D.1 -- Boot the container

```bash
cd /home/jes/garage-beast
docker compose up -d
echo "compose-up exit=$?"
```

First-boot side effects: lmdb metadata initialization in /home/jes/garage-data/meta/ (creates a few KB of files); rpc/admin/s3/web/k2v port binding inside the container; node ID auto-generation (random hex on first boot).

### Step D.2 -- Healthcheck poll

Cap 120s (24 polls x 5s). Garage typically goes healthy in 10-30s on first boot.

```bash
for i in $(seq 1 24); do
  STATUS=$(docker inspect control-garage-beast --format '{{.State.Health.Status}}' 2>/dev/null || echo unknown)
  echo "[$(date -Iseconds)] poll $i/24: $STATUS"
  if [ "$STATUS" = "healthy" ]; then
    echo "[$(date -Iseconds)] container healthy"
    break
  fi
  sleep 5
done
```

**Expected first-boot timeline:**
- t=0: `compose up -d` returns; container created, daemon starting
- t=~5-15s: lmdb init done, ports bound
- t=~15-30s: first healthcheck (`/garage status` exit 0) succeeds
- t=~30-45s: Docker marks container `healthy` (3 successful checks at 30s intervals + start_period buffer)

If still `starting` at poll 24/24 (120s), capture `docker logs control-garage-beast` and file paco_request.

### Step D.3 -- Capture node ID + assign + apply layout

```bash
echo "[$(date -Iseconds)] === garage status (capture node ID) ==="
docker exec control-garage-beast /garage status
NODE_ID=$(docker exec control-garage-beast /garage status 2>/dev/null | awk '/^[0-9a-f]{16}/{print substr($1,1,16); exit}')
echo "[$(date -Iseconds)] NODE_ID=$NODE_ID"
if [ -z "$NODE_ID" ]; then
  echo "[$(date -Iseconds)] FATAL: could not capture node ID"
  exit 1
fi

echo "[$(date -Iseconds)] === garage layout assign -z dc1 -c 4T $NODE_ID ==="
docker exec control-garage-beast /garage layout assign -z dc1 -c 4T "$NODE_ID"

echo "[$(date -Iseconds)] === garage layout apply --version 1 ==="
docker exec control-garage-beast /garage layout apply --version 1

echo "[$(date -Iseconds)] === garage status post-layout ==="
docker exec control-garage-beast /garage status
```

After `layout apply`, the `garage status` output should show the node with role assigned: zone=dc1, capacity=4T (instead of `NO ROLE ASSIGNED`).

### Step D.4 -- Root S3 key creation + capture credentials + write .s3-creds

```bash
echo "[$(date -Iseconds)] === garage key create root ==="
KEY_OUTPUT=$(docker exec control-garage-beast /garage key create root)
echo "$KEY_OUTPUT"
ACCESS_KEY_ID=$(echo "$KEY_OUTPUT" | awk -F': ' '/Key ID:/{print $2}')
SECRET_KEY=$(echo "$KEY_OUTPUT" | awk -F': ' '/Secret key:/{print $2}')
echo "[$(date -Iseconds)] ACCESS_KEY_ID=$ACCESS_KEY_ID"
echo "[$(date -Iseconds)] SECRET_KEY=$SECRET_KEY (will be written to .s3-creds and never echoed in review)"

if [ -z "$ACCESS_KEY_ID" ] || [ -z "$SECRET_KEY" ]; then
  echo "[$(date -Iseconds)] FATAL: key parsing failed"
  exit 1
fi

cat > /home/jes/garage-beast/.s3-creds <<CREDS_EOF
# Garage root S3 credentials -- generated $(date -Iseconds) by B1 Phase D
# DO NOT COMMIT. chmod 600. P5 carryover: rotate to per-bucket keys.
export AWS_ACCESS_KEY_ID=$ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY=$SECRET_KEY
export AWS_DEFAULT_REGION=garage
export AWS_ENDPOINT_URL=http://192.168.1.152:3900
CREDS_EOF
chmod 600 /home/jes/garage-beast/.s3-creds
ls -la /home/jes/garage-beast/.s3-creds
md5sum /home/jes/garage-beast/.s3-creds
```

**Note on log content:** the bootstrap log at /tmp/B1_garage_phase_d_bootstrap.log will contain the actual ACCESS_KEY_ID and SECRET_KEY values (echoed during D.4). This is acceptable transitional state: the log is on Beast disk only (not transmitted), and Phase F's cleanup step archives /tmp captures into /home/jes/garage-beast/.ship-report-inputs/ where they live alongside .s3-creds (chmod 600). PD's review doc, however, REDACTS both values per the standing directive -- echo `<REDACTED-IN-REVIEW-OUTPUT>` in the review, never the literal key/secret.

The `.s3-creds` file uses `192.168.1.152:3900` as the canonical AWS_ENDPOINT_URL. Both Beast-local (Atlas) and CiscoKid-side (backup jobs) clients reach Garage at this address. Future optimization (P5): Beast-local clients could override to `127.0.0.1:3900` for slightly lower-latency access -- not blocking.

### Step D.5 -- 3 bucket creates + 3 grants

```bash
for B in atlas-state backups artifacts; do
  echo "[$(date -Iseconds)] === garage bucket create $B ==="
  docker exec control-garage-beast /garage bucket create "$B"
  echo "[$(date -Iseconds)] === garage bucket allow --read --write --owner $B --key root ==="
  docker exec control-garage-beast /garage bucket allow --read --write --owner "$B" --key root
done

echo "[$(date -Iseconds)] === garage bucket list ==="
docker exec control-garage-beast /garage bucket list

echo "[$(date -Iseconds)] === garage key info root ==="
docker exec control-garage-beast /garage key info root

echo "[$(date -Iseconds)] === Final container state ==="
docker ps --filter name=control-garage-beast --format '{{.Names}} {{.Status}} {{.Ports}}'
docker inspect control-garage-beast --format 'RestartCount={{.RestartCount}} Health={{.State.Health.Status}}'

echo "[$(date -Iseconds)] === PHASE D COMPLETE ==="
```

The `garage key info root` output will list `Authorized buckets:` with all 3 buckets (atlas-state, backups, artifacts) and read+write+owner permissions on each.

### Wait + read log (PD main shell)

```bash
for i in $(seq 1 36); do
  if grep -qE '=== PHASE D (COMPLETE|.*FATAL) ===' /tmp/B1_garage_phase_d_bootstrap.log 2>/dev/null; then
    cat /tmp/B1_garage_phase_d_bootstrap.log
    break
  fi
  sleep 5
done
```

Max wait: 36 polls x 5s = 180s. Total Phase D wallclock budget: ~3 minutes from `up -d` to PHASE D COMPLETE.

---

## Phase D acceptance gate (PD verifies all PASS)

1. **Container Up healthy:** `docker ps` shows control-garage-beast Up X (healthy); `docker inspect` health.status=healthy; RestartCount=0
2. **Layout assigned:** `garage status` post-layout shows the node listed under HEALTHY NODES with zone=dc1 and capacity=4T (not `NO ROLE ASSIGNED`)
3. **3 buckets present:** `garage bucket list` shows atlas-state, backups, artifacts
4. **Root key scoped to all 3 buckets:** `garage key info root` shows `Authorized buckets:` enumerating all 3 with R+W+O each
5. **.s3-creds file written:** /home/jes/garage-beast/.s3-creds exists chmod 600 jes:jes; 6 lines (1 comment + 1 comment + 4 export); md5 captured for review
6. **LAN listener exact:** `ss -tln` on Beast shows 192.168.1.152:3900 (S3 API) AND 127.0.0.1:3903 (admin); RPC 3901, web 3902, k2v 3904 NOT in published listener list (container-internal only)
7. **No service-affecting changes outside B1:** B2a `control-postgres-beast` still Up healthy with StartedAt nanosecond-identical `2026-04-27T00:13:57.800746541Z`, RestartCount=0; UFW unchanged at 15 rules

---

## If any step fails

- **Container fails to come up:** `docker compose up -d` exit 0 but container restarts repeatedly -- likely garage.toml syntax issue. Capture `docker logs control-garage-beast` and full toml content. File paco_request.
- **Healthcheck never goes healthy in 120s:** capture `docker exec control-garage-beast /garage status` directly; if daemon fails to start, capture logs. May indicate bind-mount permission issue on /home/jes/garage-data (chmod 700 may not be enough for container user; Garage runs as UID 0 inside scratch image, but bind-mounted dirs need to be readable from inside).
- **Node ID extraction returns empty:** garage status output may have changed format. Try `docker exec control-garage-beast /garage node id` as alternative -- this prints just the node ID@host:port. Strip @ and beyond.
- **Layout apply fails with `version mismatch`:** version is wrong. Run `garage layout show` to see current version, use that+1.
- **`garage key create root` fails with "already exists":** unlikely on greenfield, but if so, `garage key delete root` then re-create. (Recovery; not a real failure -- the key state would be coherent.)
- **`garage bucket create` fails:** capture exact error. Possibly already exists (re-run); possibly permission error from container.
- **`garage bucket allow` fails:** verify both bucket name and key name are correct; check `garage bucket info <name>` and `garage key info root` for state inspection.

Rollback for full Phase D: `docker compose down -v` (keeps bind-mount data; meta+data dirs preserve what was created). For clean re-run: also `rm -rf /home/jes/garage-data/meta/* /home/jes/garage-data/data/*` (but NOT the dirs themselves; the chmod 700 + jes:jes ownership must be preserved).

---

## Standing rules in effect

- **Rule 1:** Phase D = `docker compose up -d` + `docker exec` calls + 1 file write (.s3-creds) + 1 capture write (bootstrap log). No bulk transport via MCP. Compliant.
- **CLAUDE.md "Spec or no action":** all 6 picks ratified pre-draft. CLI syntax lockdown clarifies (does not deviate from) spec text. One refinement re-affirmed this directive: REDACT secret values in PD's Phase D review doc per the standing convention from Phase B.
- **CLAUDE.md "Docker bypasses UFW":** UFW rule for 3900 is in place; LAN-bind via Docker port mapping is the primary gate; S3 access key (created this phase) is the auth gate.
- **Correspondence protocol:** PD's next deliverable is `paco_review_b1_garage_phase_d_bootstrap.md`. REDACT actual ACCESS_KEY_ID/SECRET_KEY values; report file paths + perms + md5 + bucket list + key authorization scope only.
- **Canon location:** authorization doc commits this turn; PD's Phase D review commits when it lands.

---

## Phase E preview (informational, requires separate Paco GO)

First end-to-end exercise of LAN-bind + UFW + S3-key auth from CiscoKid:
- `scp jes@192.168.1.152:/home/jes/garage-beast/.s3-creds /tmp/B1_garage_creds_ciscokid.env` (chmod 600 on copy)
- `aws s3 ls` (lists 3 buckets)
- 1KB random file PUT -> LIST -> GET -> md5 byte-parity verify -> DELETE
- `shred -u` the temp creds + smoke files

This is the gate that proves the entire stack works end-to-end before we close B1.

---

**File location:** `/home/jes/control-plane/docs/paco_response_b1_garage_phase_c_confirm_phase_d_go.md`

-- Paco
