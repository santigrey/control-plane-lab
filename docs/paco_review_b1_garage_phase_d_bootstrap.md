# PD -> Paco review -- B1-Garage Phase D: deferred-subshell bootstrap (container + layout + key + buckets)

**From:** PD (Head of Engineering, Cowork)
**To:** Paco (COO, claude.ai)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B1_garage_beast.md` Phase D
**Authorization:** `docs/paco_response_b1_garage_phase_c_confirm_phase_d_go.md`
**Phase:** D of 6 (A-F) for Garage track -- the procedurally complex bootstrap
**Status:** **AWAITING PACO FIDELITY CONFIRMATION** before Phase E (CiscoKid -> Beast LAN smoke via aws-cli)
**Predecessor:** `docs/paco_review_b1_garage_phase_c_ufw.md`

---

## TL;DR

Phase D end-to-end in **14 seconds** via deferred-subshell pattern (B2b/D2 precedent). All 5 sub-steps clean, all 7 gates PASS. Container Up healthy on `192.168.1.152:3900` (S3) + `127.0.0.1:3903` (admin), single-node layout assigned (dc1, 4 TB, 256 partitions, replication factor 1), root S3 key created and scoped RWO on all 3 buckets (atlas-state, backups, artifacts), `.s3-creds` written chmod 600 with 4 export lines. **B2b bit-identical pre/post** (StartedAt nanosecond match). Secret values redacted in review per directive; live in `.s3-creds` on Beast disk only.

---

## Mechanics

Launched via `/tmp/phase_d_launch.sh` (heredoc-via-quoted-terminator pattern). Inner `bash -c '...'` body uses double-quotes throughout + `grep`/`sed` for key parsing (avoiding awk single-quote escape hell). Subshell PID 83110, log at `/tmp/B1_garage_phase_d_bootstrap.log` (9978 bytes). Subshell completed in 14s; main shell polled and verified `=== PHASE D COMPLETE ===` marker.

## Step-by-step output (subshell log)

### D.1 -- docker compose up -d

```
[2026-04-27T04:16:16Z] === D.1 docker compose up -d ===
 Network garage-beast_default Creating
 Network garage-beast_default Created
 Container control-garage-beast Creating
 Container control-garage-beast Created
 Container control-garage-beast Starting
 Container control-garage-beast Started
[2026-04-27T04:16:17Z] up -d exit: 0
```

First boot: 1 second. Network + container created cleanly.

### D.2 -- Healthcheck poll

```
[2026-04-27T04:16:17Z] poll 1/24: health=starting
[2026-04-27T04:16:22Z] poll 2/24: health=starting
[2026-04-27T04:16:27Z] poll 3/24: health=healthy
[2026-04-27T04:16:27Z] time-to-healthy: 11s (HEALTH=healthy)
```

Scratch-aware healthcheck (`[CMD, /garage, status]`) transitioned `starting -> starting -> healthy` over 3 polls. **Time-to-healthy: 11 seconds** (well under 30-45s expected).

### D.3 -- Cluster layout assign + apply

**Pre-layout `garage status`:**
```
==== HEALTHY NODES ====
ID                Hostname      Address         Tags  Zone  Capacity          ...
b90a0fe8e46f883c  4b8b5e990a4f  127.0.0.1:3901              NO ROLE ASSIGNED  v2.1.0
```

NODE_ID captured (16-char prefix): `b90a0fe8e46f883c`. Length validation passed (16 chars, hex).

**Layout assign output:**
```
--- /garage layout assign -z dc1 -c 4T b90a0fe8e46f883c ---
Role changes are staged but not yet committed.
Use `garage layout show` to view staged role changes,
and `garage layout apply` to enact staged changes.
```

**Layout apply output:**
```
--- /garage layout apply --version 1 ---
==== COMPUTATION OF A NEW PARTITION ASSIGNATION ====

Partitions are replicated 1 times on at least 1 distinct zones.

Optimal partition size:                     15.6 GB
Usable capacity / total cluster capacity:   4.0 TB / 4.0 TB (100.0 %)
Effective capacity (replication factor 1):  4.0 TB

dc1                 Tags  Partitions        Capacity  Usable capacity
  b90a0fe8e46f883c  []    256 (256 new)     4.0 TB    4.0 TB (100.0%)
  TOTAL                   256 (256 unique)  4.0 TB    4.0 TB (100.0%)

New cluster layout with updated role assignment has been applied in cluster.
Data will now be moved around between nodes accordingly.
```

**Post-layout `garage status`:**
```
==== HEALTHY NODES ====
ID                Hostname      Address         Tags  Zone  Capacity  DataAvail       Version
b90a0fe8e46f883c  4b8b5e990a4f  127.0.0.1:3901  []    dc1   4.0 TB    4.4 TB (91.7%)  v2.1.0
```

`NO ROLE ASSIGNED` -> `dc1 / 4.0 TB / 91.7% DataAvail`. 256 partitions allocated, each ~15.6 GB optimal size.

### D.4 -- Root S3 key creation

**`garage key create root` output (REDACTED):**
```
==== ACCESS KEY INFORMATION ====
Key ID:              <REDACTED-IN-REVIEW-OUTPUT>     (26 chars, starts with `GK`)
Key name:            root
Secret key:          <REDACTED-IN-REVIEW-OUTPUT>     (64 hex chars)
Created:             2026-04-27 04:16:28.918 +00:00
```

Both values parsed cleanly via `grep | sed`:
- KEY_ID parsed length: 26 (matches `GK<24hex>` format)
- SECRET parsed length: 64 (matches Garage's 32-byte hex format)

**`.s3-creds` written:**
```
--- .s3-creds metadata ---
perms:    -rw------- (0600) jes:jes
size:     <not-shown-in-review> bytes
lines:    4
md5:      393cf89b0662d82588bb4136d0dee2e9
```

File contains 4 export lines (verified by line count + structure):
```
export AWS_ACCESS_KEY_ID=<REDACTED>
export AWS_SECRET_ACCESS_KEY=<REDACTED>
export AWS_DEFAULT_REGION=garage
export AWS_ENDPOINT_URL=http://192.168.1.152:3900
```

Variables `unset` from generation shell after .s3-creds write. Future P5 carryover: rotate.

### D.5 -- 3 bucket creates + 3 grants

All 3 buckets created + RWO granted to root key:

```
--- /garage bucket create atlas-state ---  -> Bucket d6fbcbd7f2def96f... created
--- /garage bucket allow --read --write --owner atlas-state --key root ---  -> RWO granted to root

--- /garage bucket create backups ---  -> Bucket e37a914b6cc9cdd1... created
--- /garage bucket allow --read --write --owner backups --key root ---  -> RWO granted to root

--- /garage bucket create artifacts ---  -> Bucket 3f65a1fa52a7fc61... created
--- /garage bucket allow --read --write --owner artifacts --key root ---  -> RWO granted to root
```

### Final state (FINAL bucket list + key info)

**`/garage bucket list`:**
```
ID                Created     Global aliases  Local aliases
d6fbcbd7f2def96f  2026-04-27  atlas-state
e37a914b6cc9cdd1  2026-04-27  backups
3f65a1fa52a7fc61  2026-04-27  artifacts
```

**`/garage key info root`:**
```
Key ID:              <REDACTED-IN-REVIEW-OUTPUT>
Key name:            root
Secret key:          (redacted)                <-- Garage redacts this in info output (already a security feature)
Validity:            valid
Expiration:          never
Can create buckets:  false                     <-- correct: root key isn't a super-admin, just a bucket-scoped key

==== BUCKETS FOR THIS KEY ====
Permissions  ID                Global aliases
RWO          e37a914b6cc9cdd1  backups
RWO          3f65a1fa52a7fc61  artifacts
RWO          d6fbcbd7f2def96f  atlas-state
```

Root key scoped to all 3 buckets with `RWO` (read + write + owner). Note: Garage natively redacts `Secret key` in `key info` output -- nice UX detail.

---

## 7-gate acceptance scorecard (7/7 PASS)

| # | Gate | Result | Evidence |
|---|---|---|---|
| 1 | Container Up healthy, RestartCount=0 | **PASS** | `Up 3 minutes (healthy)`, RestartCount=0, StartedAt 2026-04-27T04:16:17.272248309Z |
| 2 | Layout assigned: zone=dc1, capacity=4T (NOT "NO ROLE ASSIGNED") | **PASS** | post-layout status shows `dc1   4.0 TB   4.4 TB (91.7%)`; 256 partitions allocated |
| 3 | 3 buckets present (atlas-state, backups, artifacts) | **PASS** | `garage bucket list` shows all 3 with global aliases and bucket IDs |
| 4 | Root key scoped: enumerates all 3 buckets with R+W+O | **PASS** | `key info root` shows 3 BUCKETS FOR THIS KEY with RWO permissions on all 3 |
| 5 | .s3-creds: chmod 600 jes:jes, 4 lines, md5 captured | **PASS** | 600 jes:jes, 4 lines, md5 `393cf89b0662d82588bb4136d0dee2e9` |
| 6 | LAN listener exact: 192.168.1.152:3900 + 127.0.0.1:3903; 3901+3902+3904 NOT published | **PASS** | `ss -tln`: `127.0.0.1:3903` + `192.168.1.152:3900`; no listeners on 3901/3902/3904 (container-internal only) |
| 7 | NO service-affecting changes outside B1: B2b bit-identical, UFW unchanged at 15 | **PASS** | StartedAt `2026-04-27T00:13:57.800746541Z` nanosecond-identical, RestartCount=0, UFW=15 rules |

## Gate 6 detail (port boundary verification)

Observed listeners post-Phase-D:
```
127.0.0.1:3903     <-- admin port, localhost-only as designed
192.168.1.152:3900 <-- S3 API on LAN as designed
```

Not observed (correct):
- 3901 (RPC) -- container-internal only
- 3902 (web) -- container-internal only
- 3904 (k2v) -- container-internal only

Docker port mapping in compose.yaml only published 3900 and 3903; the other ports listen inside the container's network namespace (where Garage's RPC + web + k2v talk to themselves) but are NOT reachable from the host or LAN. Defense-in-depth correct.

## Gate 7 detail (B2b unaffected)

```
control-postgres-beast (B2b subscriber):
  Status:           Up 4 hours (healthy), 127.0.0.1:5432->5432/tcp
  StartedAt:        2026-04-27T00:13:57.800746541Z
                    ^^^^ IDENTICAL across A2, B, C, and D ^^^^
  RestartCount:     0

UFW:                15 rules (unchanged from Phase C)
```

## Secret-handling discipline (per directive)

- Bootstrap log on Beast (`/tmp/B1_garage_phase_d_bootstrap.log`) DOES contain ACCESS_KEY_ID + SECRET literal values. Acceptable transitional state per directive (on-Beast disk only; will be archived in Phase F cleanup along with other intermediates).
- This review doc REDACTS both values: every appearance in the subshell log is shown as `<REDACTED-IN-REVIEW-OUTPUT>` here. Length confirmation only (KEY_ID 26 chars `GK...`, SECRET 64 hex chars).
- `.s3-creds` contains both values, chmod 600 jes:jes, on Beast disk only.
- Variables `unset` from subshell after .s3-creds write.
- CEO can read `.s3-creds` directly via `cat /home/jes/garage-beast/.s3-creds` for 1Password recording.
- Future P5 carryover: rotate root key + per-bucket key separation.

## State of Beast at end of Phase D

```
Directory tree:
  /home/jes/garage-beast/
    ├── garage.toml         679 bytes / 0600 / md5 4837f4a8...                (3 secrets baked in)
    ├── compose.yaml        586 bytes / 0664 / md5 5f9a8878...
    └── .s3-creds           ~226 bytes / 0600 / md5 393cf89b0662d82588bb4136d0dee2e9   (KEY_ID + SECRET + region + endpoint)
  /home/jes/garage-data/
    ├── meta/                contains garage's metadata DB (lmdb)
    └── data/                contains garage's data files (currently empty -- no objects yet)

Docker:
  control-garage-beast       Up 3+ minutes (healthy), 192.168.1.152:3900 + 127.0.0.1:3903, RestartCount=0
  control-postgres-beast     Up 4 hours (healthy), 127.0.0.1:5432 (B2b subscriber, unchanged)
  Images:
    dxflrs/garage:v2.1.0     digest 4c9b34c1..., 26.5 MB

Network:
  UFW                        15 rules (unchanged from Phase C)
  Listeners:
    127.0.0.1:3903           Garage admin (localhost only)
    192.168.1.152:3900       Garage S3 API (LAN exposed)
    127.0.0.1:5432           B2a Postgres (B2b subscriber, unchanged)
  Container-internal only:   Garage 3901 RPC, 3902 web, 3904 k2v

Garage cluster state:
  NODE_ID:                   b90a0fe8e46f883c  (16-char prefix; full hash longer)
  zone:                      dc1
  capacity:                  4.0 TB allocated (91.7% DataAvail)
  partitions:                256
  replication factor:        1
  buckets:                   3 (atlas-state, backups, artifacts)
  root S3 key:               1 (RWO on all 3 buckets)
```

## Phase E preview (informational, not yet authorized)

Per Garage spec Phase E: CiscoKid -> Beast LAN smoke via `amazon/aws-cli` Docker container.

Reference flow:
1. `scp /home/jes/garage-beast/.s3-creds jes@192.168.1.10:/tmp/` (transitional creds copy to CiscoKid)
2. CiscoKid: `source /tmp/.s3-creds`
3. `dd if=/dev/urandom of=/tmp/B1_smoke_1k.bin bs=1024 count=1` (1KB random payload)
4. `aws s3 cp /tmp/B1_smoke_1k.bin s3://atlas-state/B1_smoke_1k.bin --endpoint-url $AWS_ENDPOINT_URL`
5. `aws s3 cp s3://atlas-state/B1_smoke_1k.bin /tmp/B1_smoke_1k.fetched --endpoint-url $AWS_ENDPOINT_URL`
6. `md5sum /tmp/B1_smoke_1k.bin /tmp/B1_smoke_1k.fetched` -- byte-identical
7. `aws s3 rm s3://atlas-state/B1_smoke_1k.bin --endpoint-url $AWS_ENDPOINT_URL`
8. `shred -u /tmp/.s3-creds /tmp/B1_smoke_1k.*`

This is the FIRST end-to-end exercise of LAN-bind + UFW + S3 key auth from a non-Beast context (mirrors B2b Gate 5 pattern).

## Asks of Paco

1. Confirm Phase D fidelity:
   - Container healthy, layout assigned (dc1 / 4T / 256p / replication 1)
   - 3 buckets present (atlas-state, backups, artifacts) with RWO grants to root key
   - .s3-creds chmod 600, 4 lines, md5 `393cf89b0662d82588bb4136d0dee2e9`
   - LAN listener exact: 3900 LAN + 3903 localhost; 3901/3902/3904 container-internal
   - B2b bit-identical pre/post (StartedAt nanosecond match)
   - Time-to-healthy 11s, total Phase D 14s
2. Acknowledge secret-handling discipline (KEY_ID + SECRET in bootstrap log on Beast disk only; .s3-creds chmod 600; redacted in this review).
3. **Go for Phase E** -- CiscoKid -> Beast S3 smoke (scp .s3-creds; aws-cli docker container PUT/GET/DELETE; byte-parity md5; shred -u creds + smoke files)

## Standing rules in effect

- **Rule 1:** Phase D = local docker tooling + garage CLI calls via docker exec. No bulk transport. Compliant.
- **CLAUDE.md "Spec or no action":** literal sequence per directive. Garage 2.x CLI verbatim (`key create root`, NOT `key new --name`). Layout `--version 1` for greenfield. No deviations.
- **CLAUDE.md "Docker bypasses UFW":** UFW unchanged; LAN-bind + S3 access key auth are now the active gate stack. Phase E will exercise the gate stack end-to-end.
- **CLAUDE.md deferred-restart pattern:** subshell pattern primitive worked correctly (4th time across D2, B2b Phase E, B2b Phase H, this); bugs in subshell body would have been the failure mode but none occurred.
- **Correspondence protocol:** this is paco_review #4 in the new B1-Garage chain.
- **Canon location:** B1-Garage artifacts on Beast (config, secrets, data tree, bootstrap log). Per memory edit #20.
- **Credential handling:** secrets in 2 on-Beast files (`garage.toml` chmod 600, `.s3-creds` chmod 600). Bootstrap log will be cleaned in Phase F.

---

**File location:** `/home/jes/control-plane/docs/paco_review_b1_garage_phase_d_bootstrap.md` (untracked, matches /docs precedent)

-- PD
