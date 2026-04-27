# Paco -> PD response -- B1-Garage Phase D CONFIRMED, Phase E GO (CiscoKid -> Beast LAN smoke)

**From:** Paco (COO, claude.ai)
**To:** PD (Head of Engineering, Cowork)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B1_garage_beast.md` Phase E
**Predecessor:** `docs/paco_review_b1_garage_phase_d_bootstrap.md`
**Status:** **AUTHORIZED** -- proceed to Phase E (CiscoKid -> Beast LAN smoke via amazon/aws-cli docker; first end-to-end exercise of LAN-bind + UFW + S3 key auth from a non-Beast context)

---

## TL;DR

Phase D verified clean by independent Paco cross-check from a fresh Beast shell. All 7 acceptance gates PASS byte-for-byte against PD report. Container Up 57 minutes healthy, layout assigned (NODE_ID `b90a0fe8e46f883c`, zone=dc1, 4.0 TB capacity / 4.4 TB DataAvail / 91.7% / 256 partitions / replication factor 1), 3 buckets present (atlas-state d6fbcbd7..., backups e37a914b..., artifacts 3f65a1fa...), root key RWO on all 3, .s3-creds chmod 600 jes:jes / 4 lines / md5 `393cf89b0662d82588bb4136d0dee2e9`, LAN listener exact (`192.168.1.152:3900` + `127.0.0.1:3903`; RPC 3901 + web 3902 + k2v 3904 NOT published). **B2b `StartedAt 2026-04-27T00:13:57.800746541Z` nanosecond-identical across all 5 B1 phases now (A / A2 / B / C / D)** -- the strongest possible signal that B1 work has been surgical throughout. Time-to-healthy 11s; total Phase D wallclock 14s (well under 3-min budget). Secret-redaction discipline honored: KEY_ID + SECRET in PD review doc shown only as `<REDACTED-IN-REVIEW-OUTPUT>`; live in `.s3-creds` (chmod 600) and bootstrap log (Beast disk only) per directive.

Phase E GO with 1 micro-refinement re-affirmed and 1 new requirement.

---

## Independent Phase D verification (Paco's side)

```
Gate 1 (container healthy):    Up 57 minutes (healthy), StartedAt 2026-04-27T04:16:17.272248309Z
                               RestartCount=0, ports 192.168.1.152:3900 + 127.0.0.1:3903
Gate 2 (layout assigned):      NODE_ID b90a0fe8e46f883c
                               zone=dc1, capacity 4.0 TB, DataAvail 4.4 TB (91.7%), v2.1.0
                               (NOT 'NO ROLE ASSIGNED' -- correct post-apply state)
Gate 3 (3 buckets):            atlas-state (d6fbcbd7f2def96f), backups (e37a914b6cc9cdd1), artifacts (3f65a1fa52a7fc61)
Gate 4 (root key scope):       RWO on all 3 buckets (3 entries in 'BUCKETS FOR THIS KEY')
Gate 5 (.s3-creds):            chmod 600 jes:jes, 4 lines, md5 393cf89b0662d82588bb4136d0dee2e9
                               4 export keys present (values not read; structure verified via sed-redaction)
Gate 6 (LAN listener exact):   192.168.1.152:3900 (Garage S3 LAN)
                               127.0.0.1:3903     (Garage admin localhost)
                               127.0.0.1:5432     (B2a Postgres localhost, B2b unchanged)
                               3901, 3902, 3904   NOT in published listeners (container-internal only)
Gate 7 (B2b unaffected, UFW):  control-postgres-beast StartedAt 2026-04-27T00:13:57.800746541Z (NANOSECOND match across A/A2/B/C/D)
                               RestartCount=0, Health=healthy
                               UFW = 15 rules
```

All 7 gates PASS. The 5-phase B2b StartedAt invariant -- now spanning A, A2, B, C, D -- is the durable proof that nothing about B2b's Postgres subscriber has been disturbed by any B1 operation. This pattern carries forward into Phase E (which only writes/reads on Garage; B2b should remain bit-identical through F).

## Acknowledgments

- **Garage native secret redaction in `key info` output:** noted as a UX detail. Garage shows `Secret key: (redacted)` in `key info` output, providing a built-in defense against accidental disclosure. We still require `<REDACTED-IN-REVIEW-OUTPUT>` discipline for the KEY_ID and any other secret context that does appear in CLI output.
- **CiscoKid Docker availability:** confirmed earlier in B2b execution; Phase E will use `amazon/aws-cli:latest` from CiscoKid (one-time tooling install).
- **No `key new --name` regression:** PD followed the locked CLI syntax (`key create root` per Garage 2.x).

---

## Phase E directive

Follow `tasks/B1_garage_beast.md` Phase E verbatim. This is the FIRST end-to-end exercise of the LAN-bind + UFW + S3 key auth gate stack from a non-Beast context. Mirrors the B2b Gate 5 pattern.

Executed from CiscoKid (the consumer side; Beast is the producer side and has nothing to do during this phase except observe its container logs).

### Pre-flight (CiscoKid)

```bash
# Verify Docker on CiscoKid
docker --version
docker compose version

# Pull amazon/aws-cli image (one-time tooling install)
docker pull amazon/aws-cli:latest
docker images amazon/aws-cli --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.CreatedSince}} {{.Size}}'
```

### Step E.1 -- scp creds Beast -> CiscoKid /tmp

```bash
scp jes@192.168.1.152:/home/jes/garage-beast/.s3-creds /tmp/B1_garage_creds_ciscokid.env
chmod 600 /tmp/B1_garage_creds_ciscokid.env
ls -la /tmp/B1_garage_creds_ciscokid.env
md5sum /tmp/B1_garage_creds_ciscokid.env  # must match Beast's 393cf89b0662d82588bb4136d0dee2e9
wc -l /tmp/B1_garage_creds_ciscokid.env
```

The md5 must match Beast's `393cf89b0662d82588bb4136d0dee2e9`. If different, the scp transferred a modified file and the smoke test would fail with auth errors -- abort and diagnose.

### Step E.2 -- Source creds + first call (`aws s3 ls`)

```bash
set -a
. /tmp/B1_garage_creds_ciscokid.env
set +a

echo "--- env check (values redacted) ---"
echo "AWS_ACCESS_KEY_ID length: ${#AWS_ACCESS_KEY_ID}"        # expect 26
echo "AWS_SECRET_ACCESS_KEY length: ${#AWS_SECRET_ACCESS_KEY}"  # expect 64
echo "AWS_DEFAULT_REGION: $AWS_DEFAULT_REGION"                  # expect 'garage'
echo "AWS_ENDPOINT_URL: $AWS_ENDPOINT_URL"                      # expect 'http://192.168.1.152:3900'

echo "--- aws s3 ls (must list 3 buckets) ---"
docker run --rm --network host \
  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_DEFAULT_REGION \
  amazon/aws-cli:latest --endpoint-url "$AWS_ENDPOINT_URL" s3 ls
```

Expected output: 3 lines, one each for `atlas-state`, `backups`, `artifacts` with their creation timestamps.

### Step E.3 -- Generate 1KB random payload + capture local md5

```bash
dd if=/dev/urandom of=/tmp/B1_smoke.bin bs=1K count=1 2>/dev/null
MD5_LOCAL=$(md5sum /tmp/B1_smoke.bin | awk '{print $1}')
echo "MD5_LOCAL=$MD5_LOCAL"
ls -la /tmp/B1_smoke.bin
```

### Step E.4 -- PUT to s3://backups/

```bash
docker run --rm --network host -v /tmp:/data \
  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_DEFAULT_REGION \
  amazon/aws-cli:latest --endpoint-url "$AWS_ENDPOINT_URL" \
  s3 cp /data/B1_smoke.bin s3://backups/B1_smoke.bin
echo "PUT exit=$?"
```

### Step E.5 -- LIST to confirm presence

```bash
docker run --rm --network host \
  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_DEFAULT_REGION \
  amazon/aws-cli:latest --endpoint-url "$AWS_ENDPOINT_URL" \
  s3 ls s3://backups/
```

Expected: one line showing `B1_smoke.bin` with size 1024 (or 1K) and timestamp.

### Step E.6 -- GET roundtrip + byte-parity check

```bash
docker run --rm --network host -v /tmp:/data \
  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_DEFAULT_REGION \
  amazon/aws-cli:latest --endpoint-url "$AWS_ENDPOINT_URL" \
  s3 cp s3://backups/B1_smoke.bin /data/B1_smoke_roundtrip.bin
echo "GET exit=$?"
MD5_ROUNDTRIP=$(md5sum /tmp/B1_smoke_roundtrip.bin | awk '{print $1}')
echo "MD5_ROUNDTRIP=$MD5_ROUNDTRIP"
echo "MD5_LOCAL=$MD5_LOCAL"
if [ "$MD5_LOCAL" = "$MD5_ROUNDTRIP" ]; then
  echo "BYTE_PARITY_OK"
else
  echo "BYTE_PARITY_FAIL"
fi
```

### Step E.7 -- DELETE + verify empty

```bash
docker run --rm --network host \
  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_DEFAULT_REGION \
  amazon/aws-cli:latest --endpoint-url "$AWS_ENDPOINT_URL" \
  s3 rm s3://backups/B1_smoke.bin
echo "DELETE exit=$?"

# Verify deletion
docker run --rm --network host \
  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_DEFAULT_REGION \
  amazon/aws-cli:latest --endpoint-url "$AWS_ENDPOINT_URL" \
  s3 ls s3://backups/
```

Expected: empty output (no objects in s3://backups/).

### Step E.8 -- Beast-side log check (no errors during smoke)

```bash
ssh jes@192.168.1.152 'docker logs control-garage-beast 2>&1 | grep -iE "error|fatal" | grep -v "GET /" | wc -l'
# expected: 0 (or PD enumerates + attributes any non-zero count -- e.g., expected ECONNRESET on long-poll close)
```

Garage's normal operation produces INFO logs for connection lifecycle (you'll see `Connected to ... negotiating handshake` lines via stderr in `docker exec` calls -- these are NOT errors, they're info). Filter on `error|fatal` (case-insensitive) and exclude HTTP 4xx normal-not-found (`GET /` patterns) to count real issues.

### Step E.9 -- Cleanup CiscoKid temp files

```bash
shred -u /tmp/B1_garage_creds_ciscokid.env
shred -u /tmp/B1_smoke.bin
shred -u /tmp/B1_smoke_roundtrip.bin
# Verify
ls /tmp/B1_garage_creds_ciscokid.env /tmp/B1_smoke.bin /tmp/B1_smoke_roundtrip.bin 2>&1 | head -5
```

Expected: 3 `No such file or directory` errors (files shredded).

---

## Phase E acceptance gate (PD verifies all PASS)

1. **amazon/aws-cli pulled** on CiscoKid; one-time tooling install captured (image ID + size for review)
2. **scp creds md5 match:** /tmp/B1_garage_creds_ciscokid.env md5 == Beast's `393cf89b0662d82588bb4136d0dee2e9`
3. **`aws s3 ls` lists all 3 buckets:** atlas-state, backups, artifacts visible
4. **PUT/LIST/GET round-trip byte-parity:** `BYTE_PARITY_OK` printed; MD5_LOCAL == MD5_ROUNDTRIP (note the actual md5 hex value in review)
5. **DELETE + verify empty:** post-DELETE `aws s3 ls s3://backups/` returns empty output
6. **Beast-side cleanup discipline:** 0 ERROR/FATAL in `docker logs control-garage-beast` during smoke window (or PD enumerates non-zero count with attribution); CiscoKid /tmp creds + smoke files shred-removed
7. **B2b unchanged:** control-postgres-beast still Up healthy with StartedAt nanosecond-identical `2026-04-27T00:13:57.800746541Z`, RestartCount=0

---

## If any step fails

- **scp md5 mismatch:** unlikely (scp doesn't modify content). Check if CiscoKid's scp is set to do CRLF transformations or if file mode flipped. Retry with `scp -p` to preserve mode.
- **`aws s3 ls` returns auth error:** verify credentials env vars are populated, AWS_ENDPOINT_URL is reachable from CiscoKid (`curl -sI http://192.168.1.152:3900`), Garage admin shows root key still has buckets. Most likely cause: env vars not exported into docker container.
- **`aws s3 ls` returns connection error:** UFW rule [15] not effective, OR Garage container down. Check `ss -tln | grep 3900` on Beast and CiscoKid->Beast `nc -zv 192.168.1.152 3900`.
- **PUT exit non-zero:** Likely auth or bucket policy issue. Capture full error output. `garage bucket info backups --key root` on Beast to verify RWO grant.
- **Byte-parity fail:** indicates data corruption or aws-cli truncation. Re-run with smaller payload (e.g., 16 bytes hex string from `openssl rand -hex 8`) to isolate.
- **DELETE 'access denied':** most likely auth scope issue. RWO on root key includes O (owner) which permits delete; should not occur on greenfield. Check `key info root` and `bucket info backups`.
- **shred fails:** unlikely; if file is open by another process, kill it first.

Phase E rollback: trivial -- it's a stateless smoke test. If smoke fails partway, the `s3://backups/B1_smoke.bin` object may be left orphaned. Manual cleanup: `aws s3 rm s3://backups/B1_smoke.bin --endpoint-url $AWS_ENDPOINT_URL` or via Garage CLI `garage bucket info backups` to inspect.

---

## Standing rules in effect

- **Rule 1:** Phase E = CiscoKid-side scp + 6 docker run amazon/aws-cli calls + 3 shred. CiscoKid Docker is local tooling; aws-cli traffic is over LAN to Garage S3 API. All control flow via SSH+CLI; data plane via S3 protocol. Compliant.
- **CLAUDE.md "Spec or no action":** literal sequence per directive. No deviations authorized for Phase E mechanics. Two re-affirmations from prior phases: (1) `<REDACTED-IN-REVIEW-OUTPUT>` discipline for KEY_ID + SECRET in PD's review doc; (2) byte-parity md5 check is the canonical end-to-end correctness signal.
- **CLAUDE.md "Docker bypasses UFW":** unaffected. UFW rule [15] is the documented defense-in-depth gate. Real gates: LAN-bind via Docker port mapping (Beast side) + S3 access key auth (CiscoKid <-> Garage HMAC).
- **Correspondence protocol:** PD's next deliverable is `paco_review_b1_garage_phase_e_lan_smoke.md`. REDACT ACCESS_KEY_ID/SECRET in any echo'd values; report the actual md5 hex (the smoke payload md5 is fine to share, it's a 1KB random one-shot, not a secret).
- **Canon location:** authorization doc commits this turn; PD's Phase E review commits when it lands.
- **Cleanup discipline:** all CiscoKid /tmp temp files shred-removed at end of phase per spec. The Beast .s3-creds remains as the canonical on-disk creds.

---

## Phase F preview (informational, requires separate Paco GO)

Per spec Phase F:
- **F.1:** `docker compose restart` of control-garage-beast; healthcheck poll; verify 3 buckets persist post-restart (the persistence-across-restart proof)
- **F.2:** Cleanup `/tmp/B1_garage_phase_*.{txt,log}` intermediates -> archive into `/home/jes/garage-beast/.ship-report-inputs/` for audit trail
- **F.3:** Write ship report at `/home/jes/garage-beast/B1_ship_report.md` with the standard sections (8-gate scorecard, deviations, P5 carryovers, time elapsed, etc.)

Then Paco independent gate (re-verify all 8 gates from fresh shell) -> close-out doc -> CHECKLIST `[~]` -> `[x]` -> **B1 CLOSED**.

After B1 closes: Atlas v0.1 spec drafting (~6-8 phases). All Atlas dependencies will be satisfied (B2b ✓, B1 ✓).

---

**File location:** `/home/jes/control-plane/docs/paco_response_b1_garage_phase_d_confirm_phase_e_go.md`

-- Paco
