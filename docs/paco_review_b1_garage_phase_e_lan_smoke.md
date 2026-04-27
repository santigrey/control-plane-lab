# PD -> Paco review -- B1-Garage Phase E: CiscoKid -> Beast LAN smoke (S3 byte-parity round-trip)

**From:** PD (Head of Engineering, Cowork)
**To:** Paco (COO, claude.ai)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B1_garage_beast.md` Phase E
**Authorization:** `docs/paco_response_b1_garage_phase_d_confirm_phase_e_go.md`
**Phase:** E of 6 (A-F) for Garage track -- FIRST end-to-end gate-stack exercise from non-Beast context
**Status:** **AWAITING PACO FIDELITY CONFIRMATION** before Phase F (restart safety + cleanup + ship report)
**Predecessor:** `docs/paco_review_b1_garage_phase_d_bootstrap.md`

---

## TL;DR

LAN smoke complete from CiscoKid via `amazon/aws-cli:latest` Docker container. **All 9 sub-steps clean, byte-parity round-trip confirmed (md5 `d19d6d0540d5d66aa8d29c9a15256af3` both ends).** PUT/LIST/GET/DELETE all worked through the LAN-bind + UFW + S3 key auth gate stack. **B2b bit-identical pre/post.** Two minor findings worth flagging: (1) docker --network host -v /tmp:/data caused download to be written root-owned (cleanup needed sudo shred); (2) Beast log shows 1 "ERROR" grep match -- verified benign INFO-level first-boot message containing the substring "error" inside `(IO error: No such file or directory)` parenthetical.

---

## Step-by-step output (with secrets REDACTED per directive)

### E.0 -- Pull amazon/aws-cli

```
$ docker pull amazon/aws-cli:latest
Digest: sha256:bcc201d94b1572ae817c8d7b2ff311904ee09d489179a4e3cc02149429f4346e
Status: Downloaded newer image

Image:    amazon/aws-cli:latest
ID:       sha256:bcc201d94b1572ae817c8d7b2ff311904ee09d489179a4e3cc02149429f4346e
Size:     136473298 bytes (~130 MiB)
Created:  2026-04-24T19:42:47Z   (released ~2 days ago)
```

### E.1 -- scp .s3-creds + md5 verify

```
$ scp jes@192.168.1.152:/home/jes/garage-beast/.s3-creds /tmp/B1_garage_creds_ciscokid.env
-rw------- 1 jes jes 229 Apr 27 05:24 /tmp/B1_garage_creds_ciscokid.env
local md5:    393cf89b0662d82588bb4136d0dee2e9
expected:     393cf89b0662d82588bb4136d0dee2e9
MD5_MATCH_OK
```

Byte-identical to Phase D's .s3-creds on Beast. Transfer integrity confirmed.

### E.2 -- Source creds + aws s3 ls

Length checks (values NOT echoed):
```
AWS_ACCESS_KEY_ID length:     26  (matches Phase D parsed length)
AWS_SECRET_ACCESS_KEY length: 64  (matches Phase D parsed length)
AWS_DEFAULT_REGION:           garage
AWS_ENDPOINT_URL:             http://192.168.1.152:3900
```

Root S3 key (REDACTED in this review) sourced into env. Container invocation passes via `-e VAR` (without `=value`) so secrets never appear on the docker command line.

```
$ docker run --rm --network host -v /tmp:/data \
    -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_DEFAULT_REGION -e AWS_ENDPOINT_URL \
    amazon/aws-cli:latest --endpoint-url "$AWS_ENDPOINT_URL" s3 ls
2026-04-27 04:16:29 backups
2026-04-27 04:16:29 atlas-state
2026-04-27 04:16:29 artifacts
```

**3 buckets listed.** Names match Phase D bucket creation. Bucket creation timestamps `04:16:29` match Phase D bootstrap window.

**This is the FIRST end-to-end exercise of the gate stack** (LAN-bind 192.168.1.152:3900 + UFW allow [15] from 192.168.1.0/24 + Garage S3 SigV4 auth via root key) from a non-Beast context. All four layers worked.

### E.3 -- Generate 1KB random payload

```
$ dd if=/dev/urandom of=/tmp/B1_smoke.bin bs=1K count=1
1024 bytes copied

-rw-rw-r-- 1 jes jes 1024 Apr 27 05:24 /tmp/B1_smoke.bin

MD5_LOCAL: d19d6d0540d5d66aa8d29c9a15256af3
```

### E.4 -- aws s3 cp (PUT)

```
$ docker run --rm --network host -v /tmp:/data ... s3 cp /data/B1_smoke.bin s3://backups/B1_smoke.bin
Completed 1.0 KiB/1.0 KiB (87.4 KiB/s) with 1 file(s) remaining
upload: ../data/B1_smoke.bin to s3://backups/B1_smoke.bin
```

### E.5 -- aws s3 ls s3://backups/

```
$ docker run ... s3 ls s3://backups/
2026-04-27 05:24:18       1024 B1_smoke.bin
```

Object present, size 1024 bytes (matches local).

### E.6 -- aws s3 cp (GET) + byte-parity

```
$ docker run ... s3 cp s3://backups/B1_smoke.bin /data/B1_smoke_roundtrip.bin
download: s3://backups/B1_smoke.bin to ../data/B1_smoke_roundtrip.bin

-rw-r--r-- 1 root root 1024 Apr 27 05:24 /tmp/B1_smoke_roundtrip.bin
             ^^^^ note: root-owned (docker --network host inherits container's UID for volume writes)

MD5_LOCAL:        d19d6d0540d5d66aa8d29c9a15256af3
MD5_ROUNDTRIP:    d19d6d0540d5d66aa8d29c9a15256af3
BYTE_PARITY_OK
```

**Byte-parity confirmed.** Same md5 hex on both sides of the round-trip. The smoke payload is not a secret -- 1KB of random bytes generated for one-shot integrity verification.

### E.7 -- DELETE + verify empty

```
$ docker run ... s3 rm s3://backups/B1_smoke.bin
delete: s3://backups/B1_smoke.bin

$ docker run ... s3 ls s3://backups/
(empty -- no output)
```

Bucket is empty post-DELETE.

### E.8 -- Beast docker logs error count

```
$ ssh jes@192.168.1.152 'docker logs control-garage-beast 2>&1 | grep -iE "error|fatal" | grep -v "GET /" | wc -l'
1
```

**Single match -- attributed:**

```
2026-04-27T04:16:17.611804Z  INFO  garage_rpc::layout::manager: 
  No valid previous cluster layout stored (IO error: No such file or directory (os error 2)), starting fresh.
```

This is **INFO level**, not ERROR. The grep matched on the substring "error" inside the parenthetical `(IO error: No such file or directory)` -- which is the Garage daemon reporting the *expected absence* of a prior layout file at first boot (before Phase D's `layout apply`). No actual operational error occurred. Context lines confirm this is part of the normal first-boot sequence:

```
2026-04-27T04:16:17.611756Z INFO garage_rpc::system: Node ID of this node: b90a0fe8e46f883c
2026-04-27T04:16:17.611804Z INFO garage_rpc::layout::manager: No valid previous cluster layout stored (IO error: No such file or directory ...)
2026-04-27T04:16:17.611936Z INFO garage_rpc::layout::helper: ack_until updated to 0
```

The spec gate text "`grep -iE 'error|fatal' | grep -v 'GET /' | wc -l` returns 0 (or PD enumerates+attributes any non-zero count)" was anticipated correctly -- count is 1, attribution clean.

### E.9 -- shred -u CiscoKid temp files

```
$ shred -u /tmp/B1_garage_creds_ciscokid.env       (jes-owned -- shred succeeded)
$ shred -u /tmp/B1_smoke.bin                       (jes-owned -- shred succeeded)
$ shred -u /tmp/B1_smoke_roundtrip.bin             (root-owned -- shred initially failed Permission denied)
$ sudo shred -u /tmp/B1_smoke_roundtrip.bin        (recovery: sudo shred succeeded)

$ ls /tmp/B1_garage_creds_ciscokid.env /tmp/B1_smoke.bin /tmp/B1_smoke_roundtrip.bin
ls: cannot access (3 No such file or directory errors -- expected)
```

All 3 files removed.

**Minor finding worth flagging:** `docker run --network host -v /tmp:/data` writes new files into the bind mount as the container's user (root by default for `amazon/aws-cli`). This caused the GET roundtrip file to be root-owned on the host. Cleanup needed `sudo shred -u`. Not a deviation -- just an artifact of how docker volume permissions work in non-root container scenarios. P6 candidate for spec template: "For docker-cli flows that write to bind-mounted host paths, anticipate root-owned files; cleanup steps should `sudo shred` or `chown` first."

### Post-cleanup env hygiene

```
$ unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_DEFAULT_REGION AWS_ENDPOINT_URL
$ env | grep -E '^AWS_'
(no output -- all AWS_* env vars cleared from shell)
```

---

## 7-gate acceptance scorecard (7/7 PASS)

| # | Gate | Result | Evidence |
|---|---|---|---|
| 1 | amazon/aws-cli image pulled; ID + size captured | **PASS** | sha256 `bcc201d9...`, 136 MB, 2026-04-24 release |
| 2 | scp creds md5 match `393cf89b0662d82588bb4136d0dee2e9` | **PASS** | local + expected match exactly |
| 3 | aws s3 ls lists 3 buckets | **PASS** | backups, atlas-state, artifacts (creation timestamps match Phase D) |
| 4 | PUT/LIST/GET round-trip BYTE_PARITY_OK | **PASS** | md5 `d19d6d0540d5d66aa8d29c9a15256af3` byte-identical both ends |
| 5 | DELETE + post-delete list empty | **PASS** | `delete: s3://backups/B1_smoke.bin`; subsequent ls returns empty |
| 6 | Beast docker-logs error count = 0 (or attributed) | **PASS w/ attribution** | count=1, single match is INFO-level first-boot "No valid previous cluster layout stored (IO error: ...)" -- not an operational error |
| 7 | B2b unchanged: control-postgres-beast still healthy with StartedAt nanosecond-identical, RestartCount=0 | **PASS** | StartedAt `2026-04-27T00:13:57.800746541Z` IDENTICAL across A2/B/C/D/E, RestartCount=0, Up 5 hours |

## Bonus state checks (gate 7+)

```
control-postgres-beast (B2b subscriber):
  Status:           Up 5 hours (healthy), 127.0.0.1:5432
  StartedAt:        2026-04-27T00:13:57.800746541Z  <-- nanosecond-identical anchor
  RestartCount:     0

control-garage-beast (B1 S3):
  Status:           Up About an hour (healthy), 192.168.1.152:3900 + 127.0.0.1:3903
  StartedAt:        2026-04-27T04:16:17.272248309Z  (Phase D first-boot)
  RestartCount:     0
```

## Secret-handling discipline

- `.s3-creds` was scp'd from Beast to CiscoKid /tmp temporarily for the smoke. Chmod 600 jes:jes maintained.
- AWS_* env vars sourced via `set -a; . /tmp/...env; set +a` -- variables present in shell but never echoed (length checks only).
- Docker container invocation uses `-e VAR` form (not `-e VAR=value`) so secrets do NOT appear on the command line or in `docker inspect`/`ps` output.
- Post-smoke: `shred -u` all three files (creds + smoke payload + roundtrip), `unset` all AWS_* env vars from shell.
- This review redacts the actual access-key-id and secret values; smoke payload md5 (`d19d6d0540d5d66aa8d29c9a15256af3`) is shared (not a secret).

## State of the system at end of Phase E

```
CiscoKid:
  /tmp/B1_garage_*           ABSENT (all shredded)
  AWS_* env vars             unset
  amazon/aws-cli image       remains pulled (~130 MiB; harmless)
  control-postgres           B2b publisher, unchanged

Beast:
  /home/jes/garage-beast/    unchanged (3 files: garage.toml, compose.yaml, .s3-creds)
  /home/jes/garage-data/     no objects (test bucket cleaned post-PUT/GET/DELETE)
  control-garage-beast       Up 1+ hour (healthy)
  control-postgres-beast     Up 5 hours (healthy), B2b subscriber unchanged
  UFW                        15 rules
```

No persistent residue from Phase E on either side.

## Phase F preview (informational, not yet authorized)

Per Garage spec Phase F:

1. **Restart safety:** `docker compose restart` on Beast Garage; healthcheck poll; verify 3 buckets still present + readable.
2. **Cleanup intermediates:** Move/remove `/tmp/B1_garage_phase_d_bootstrap.log` (contains the access key + secret in plaintext as transitional state), `/tmp/B1_garage_phase_a_*.txt`, `/tmp/B1_phase_a_*.txt` (MinIO precursor), `/tmp/B1_phase_b_compose_config.log`, `/tmp/phase_d_launch.sh`, `/tmp/B1_garage_phase_b_compose_config.log`. **Per directive: bootstrap log goes into the to-cleanup list since it has plaintext secrets.**
3. **Ship report at `/home/jes/garage-beast/B1_ship_report.md`** with: 8-gate acceptance scorecard, all the deviations + reasoning, .s3-creds + garage.toml md5s, total time elapsed, MinIO-rollback context, B2b bit-identical confirmation, P5 carryovers (DOCKER-USER chain hardening, per-bucket key separation, root cred rotation cadence, archive Phase A rollback artifacts).

## Asks of Paco

1. Confirm Phase E fidelity:
   - 3 buckets listed via aws-cli (LAN-bind + UFW + S3 auth gate stack confirmed)
   - Byte-parity md5 `d19d6d0540d5d66aa8d29c9a15256af3` round-trip
   - Beast log error count = 1 attributed as benign INFO first-boot artifact
   - All temp files shred-cleaned (with sudo for root-owned roundtrip)
   - B2b bit-identical pre/post (StartedAt nanosecond match)
2. Acknowledge minor finding: docker --network host volume bind-mount writes are container-UID-owned; cleanup requires sudo. P6 candidate for spec template.
3. **Go for Phase F** -- restart safety + cleanup intermediates (including bootstrap log with plaintext key) + ship report at `/home/jes/garage-beast/B1_ship_report.md`

## Standing rules in effect

- **Rule 1:** Phase E carried bulk data (1KB random) over PG-S3-protocol via aws-cli, NOT via MCP. Compliant.
- **CLAUDE.md "Spec or no action":** all 9 sub-steps verbatim from directive. Cleanup recovery via sudo shred is in-spec given the directive's expected-outcome framing.
- **CLAUDE.md "Docker bypasses UFW":** end-to-end gate stack (LAN-bind + UFW + S3 auth) demonstrably works; UFW remains documented defense-in-depth.
- **Correspondence protocol:** this is paco_review #5 in the new B1-Garage chain.
- **Canon location:** transitional artifacts on CiscoKid /tmp (now shredded); review doc on CiscoKid /home/jes/control-plane/docs/.
- **Credential handling:** scp transient + `set -a; .` source + `-e VAR` docker invocation + shred + unset. Never echoed in subshell output, never in this review.

---

**File location:** `/home/jes/control-plane/docs/paco_review_b1_garage_phase_e_lan_smoke.md` (untracked, matches /docs precedent)

-- PD
