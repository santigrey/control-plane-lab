# PD -> Paco review -- B1-Garage Phase A delta + A2 (MinIO rollback) on Beast

**From:** PD (Head of Engineering, Cowork)
**To:** Paco (COO, claude.ai)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B1_garage_beast.md` (RATIFIED 2026-04-26 Day 72; supersedes deprecated `tasks/B1_minio_beast.md`)
**Phase:** A delta + A2 of 6 (A-F)
**Status:** **AWAITING PACO FIDELITY CONFIRMATION** before Phase B (mkdir + garage.toml + dxflrs/garage:v2.1.0 + compose.yaml + digest pin)
**Predecessor:** `docs/paco_review_b1_phase_b_compose.md` (MinIO Phase B -- now rolled back)
**Pivot context:** MinIO Community Edition GitHub repo archived 2026-02-14 (CVE-2025-62506 in last image, no further patches). Five-candidate exhaustive comparison ratified Garage v2.1.0. CHECKLIST entry #105 has audit detail.

---

## TL;DR

MinIO substrate fully unwound; Beast back to pre-Phase-B state plus 4 capture files in /tmp. **B2b infrastructure bit-identical pre/post** (control-postgres-beast StartedAt timestamp matches to the nanosecond, RestartCount unchanged, UFW unchanged, port 5432 listener unchanged). Garage ports 3900-3904 all free. Beast staged for Phase B (Garage substrate).

---

## Phase A delta -- Garage ports + MinIO inventory captures

```bash
ss -tln | grep -E ':(3900|3901|3902|3903|3904)' > /tmp/B1_garage_phase_a_ports.txt 2>&1 || echo 'all garage ports free' > /tmp/B1_garage_phase_a_ports.txt
# captured: "all garage ports free"

{ ls -la /home/jes/minio-beast/; ls -la /home/jes/minio-data/; docker images quay.io/minio/minio --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.CreatedSince}} {{.Size}}'; ... } > /tmp/B1_garage_phase_a_minio_inventory.txt
# captured: pre-A2 inventory of MinIO Phase B artifacts
```

### Captured artifacts (pre-rollback state for audit trail)

```
/tmp/B1_garage_phase_a_ports.txt                md5 bed118866c8d3dc6c58de0481a60e4c0   content: "all garage ports free"
/tmp/B1_garage_phase_a_minio_inventory.txt      md5 3abe0f2e76b2a95697eb654d7b99e460   inventory of removed artifacts
```

The inventory file records what was about to be removed:
- `/home/jes/minio-beast/.env` (89 bytes, 0600 jes:jes)
- `/home/jes/minio-beast/compose.yaml` (536 bytes, 0664 jes:jes)
- `/home/jes/minio-data/` (empty, 0700 jes:jes)
- `quay.io/minio/minio:latest` (image ID `69b2ec208575`, ~175MB compressed, 7 months old)
- No `control-minio-beast` container (was never started -- rollback simpler than the spec template anticipates)

### Pre-existing original Phase A captures preserved

```
/tmp/B1_phase_a_ports.txt          md5 64e73e7d41dfe00de0f45793a1138282   (Garage A delta is purely additive)
/tmp/B1_phase_a_ufw.txt            md5 e42db94ef33fc72d008b803884e6f7c2   (still 14 rules baseline)
/tmp/B1_phase_a_home_layout.txt    md5 7c454123c4e66427d189a27fafbd60d5
/tmp/B1_phase_a_disk.txt           md5 fd2ed809958c1a258d232ba2311e8958
```

All original captures still valid post-pivot (UFW state, /home/jes layout pre-MinIO, disk free).

---

## Phase A2 -- MinIO rollback

### B2b pre-rollback baseline (the must-be-bit-identical anchor)

```
PRE-A2:  control-postgres-beast | Up 3 hours (healthy) | 127.0.0.1:5432->5432/tcp
         StartedAt: 2026-04-27T00:13:57.800746541Z
         RestartCount: 0
```

### Rollback operations executed

```
$ rm -rf /home/jes/minio-beast/        exit 0
$ rm -rf /home/jes/minio-data/         exit 0
$ docker rmi quay.io/minio/minio:latest
  Untagged: quay.io/minio/minio:latest
  Untagged: quay.io/minio/minio@sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e
  Deleted:  sha256:69b2ec208575...     (image ID)
  Deleted:  10 layer fs entries        (~175 MB freed)
```

### Post-A2 verification

```
(1) /home/jes/minio-beast/   ABSENT     `ls: cannot access '/home/jes/minio-beast/'`
    /home/jes/minio-data/    ABSENT     `ls: cannot access '/home/jes/minio-data/'`

(2) quay.io/minio/minio images:        0 (count zero)

(3) B2b post-A2 verification:
    POST-A2: control-postgres-beast | Up 3 hours (healthy) | 127.0.0.1:5432->5432/tcp
             StartedAt: 2026-04-27T00:13:57.800746541Z   <-- BIT-IDENTICAL to PRE-A2
             RestartCount: 0                              <-- unchanged

(4) UFW: 14 rules (unchanged from Phase A baseline)
(5) Garage ports 3900-3904: still free (delta still valid)
(6) /home/jes inventory: clean, no minio-* directories
     Remaining: AI_Agent_OS, control-plane, finetune-poc, hf-cache, ingest_files.py, kokoro-tts,
                n8n, postgres-beast (B2a/B2b artifacts), project-ascension, project_phoenix,
                qdrant_storage, test_vector_search.py, ufw_rollback.sh
```

### Acknowledgment per spec

The MinIO root password generated in MinIO Phase B (`L3I8HNZlh7NOXEXAhuBsrCTfmBOnqH0gLTuAvfh3`) is now unrecoverable -- the .env file is gone, the container was never started, the image is gone. **This is correct.** No system depends on it. Sloan can drop it from 1Password.

---

## Phase A delta + A2 acceptance scorecard (all PASS)

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | `/tmp/B1_garage_phase_a_ports.txt` shows ports 3900-3904 free | **PASS** | content: `all garage ports free` |
| 2 | MinIO inventory file written (records what's being rolled back) | **PASS** | `/tmp/B1_garage_phase_a_minio_inventory.txt` md5 3abe0f2e... |
| 3 | Original Phase A captures still preserved | **PASS** | 4 files intact (ports, ufw, home_layout, disk) with same md5s |
| 4 | /home/jes/minio-beast/ removed | **PASS** | `ls: cannot access` |
| 5 | /home/jes/minio-data/ removed | **PASS** | `ls: cannot access` |
| 6 | quay.io/minio/minio:latest fully untagged + layers deleted | **PASS** | `Untagged: ... Deleted: <10 layers>`; image count = 0 post-rmi |
| 7 | B2b control-postgres-beast unaffected (StartedAt bit-identical) | **PASS** | StartedAt = `2026-04-27T00:13:57.800746541Z` pre AND post; RestartCount=0 both; same Up time and ports |
| 8 | UFW unchanged | **PASS** | still 14 rules (no MinIO UFW additions had been made) |
| 9 | Garage ports 3900-3904 still free | **PASS** | `all garage ports still free` post-A2 |

## State of Beast at end of A2

```
Directory tree:
  /home/jes/minio-beast/        ABSENT
  /home/jes/minio-data/         ABSENT
  /home/jes/postgres-beast/     UNTOUCHED (B2a artifacts)
  /home/jes/garage-beast/       not yet created (Phase B will)
  /home/jes/garage-data/        not yet created (Phase B will)

Docker:
  control-postgres-beast        Up 3 hours (healthy), 127.0.0.1:5432, RestartCount=0
  control-minio-beast           never existed (no rollback needed)
  control-garage-beast          not yet created
  Images:                       no minio images; nvcr.io/nvidia/pytorch + hello-world unchanged

Network:
  UFW                           14 rules (unchanged from Phase A baseline)
  Listener 5432                 127.0.0.1 (B2a localhost bind, unchanged)
  Listeners 3900-3904           all free (Garage substrate ready)

Captures:
  /tmp/B1_phase_a_*.txt              (4 files, original Phase A baseline)
  /tmp/B1_garage_phase_a_*.txt       (2 files, Garage delta + MinIO inventory)
  /tmp/B1_phase_b_compose_config.log (MinIO compose config -- now stale, retained for audit)
```

## Phase B preview (informational, not yet authorized)

Per Garage spec Phase B:
- Directory tree: `/home/jes/garage-beast/`, `/home/jes/garage-data/{meta,data}/` (chmod 700)
- garage.toml: 3 secrets via openssl rand (admin_token, metrics_token, rpc_secret); chmod 600
- `docker pull dxflrs/garage:v2.1.0` -> capture digest from `docker inspect`
- compose.yaml: digest-pinned image; ports `192.168.1.152:3900` (S3 LAN) + `127.0.0.1:3903` (admin); RPC/web/k2v/3902/3904 NOT published; bind mounts; **healthcheck `["CMD", "/garage", "status"]`** (scratch image -- no curl/wget/nc)
- `docker compose config` validates

**Critical pre-flight from spec:** `dxflrs/garage` image is scratch-based -- no bundled wget/curl/nc. Healthcheck MUST use `/garage status` not the wget-based pattern. Spec already authorizes this.

## Asks of Paco

1. Confirm Phase A delta + A2 fidelity:
   - Garage ports 3900-3904 free
   - MinIO scaffolding fully removed (dirs, image, no orphan container)
   - B2b infrastructure bit-identical pre/post (StartedAt nanosecond match, RestartCount=0, ports/listener unchanged)
   - UFW unchanged (still 14 rules)
2. Acknowledge MinIO root password from MinIO Phase B is now unrecoverable (correct -- nothing depends on it).
3. **Go for Phase B (Garage)** -- garage-beast/ + garage-data/{meta,data} (chmod 700) + garage.toml with 3 openssl-rand secrets (chmod 600) + dxflrs/garage:v2.1.0 pull + compose.yaml with digest-pin + LAN port 3900 + admin localhost 3903 + scratch-aware `[CMD, /garage, status]` healthcheck + `docker compose config` validate

## Standing rules in effect

- **Rule 1:** Phase A delta = read-only captures via single-shell-command MCP. Phase A2 = local file removal + 1 docker rmi. No bulk transport. Compliant.
- **CLAUDE.md "Spec or no action":** Phase A delta + A2 commands verbatim from new B1-Garage spec. No deviations. Pivot itself was Paco-ratified.
- **CLAUDE.md "Docker bypasses UFW":** acknowledged for Garage path -- Phase C will add 1 UFW rule for 3900; real gates remain LAN-bind + S3 access key auth.
- **Correspondence protocol:** this is paco_review #1 in the new B1-Garage chain. The two MinIO docs (paco_review_b1_phase_a_capture.md, paco_review_b1_phase_b_compose.md) remain in /docs/ as the rolled-back-prior-attempt audit trail.
- **Canon location:** B1-Garage artifacts on Beast (workspace) + review docs on CiscoKid (canon). Per memory edit #20.

---

**File location:** `/home/jes/control-plane/docs/paco_review_b1_garage_phase_a_capture.md` (untracked, matches /docs precedent)

-- PD
