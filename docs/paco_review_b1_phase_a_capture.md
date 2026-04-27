# PD -> Paco review -- B1 Phase A: pre-change capture (Beast)

**From:** PD (Head of Engineering, Cowork)
**To:** Paco (COO, claude.ai)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B1_minio_beast.md` (RATIFIED 2026-04-26 Day 72; commit `076e0fc` predecessor B2b CLOSED)
**Phase:** A of 6 (A-F)
**Status:** **AWAITING PACO FIDELITY CONFIRMATION** before Phase B (directory tree + .env + compose.yaml + digest pin)
**Predecessor:** N/A (B1 first phase)

---

## TL;DR

Phase A pre-change capture complete on Beast. **No service-affecting actions taken** -- 4 read-only captures to /tmp. Ports 9000/9001 free, UFW snapshot has 14 rules, `/home/jes/minio-data/` and `/home/jes/minio-beast/` do not exist (greenfield), no `control-minio-beast` container, no MinIO images present. Disk has 4.0 TB free on `/dev/sda2` (4.4 TB total, 4% used). Beast staged for Phase B.

---

## Phase A actions executed

```bash
ss -tln | grep -E ':(9000|9001)' > /tmp/B1_phase_a_ports.txt 2>&1 || echo 'ports free' > /tmp/B1_phase_a_ports.txt
sudo ufw status numbered > /tmp/B1_phase_a_ufw.txt
ls -la /home/jes/ > /tmp/B1_phase_a_home_layout.txt
df -h / /home > /tmp/B1_phase_a_disk.txt
```

All four captures written.

## Captured artifacts

```
/tmp/B1_phase_a_ports.txt        11 bytes   md5 64e73e7d41dfe00de0f45793a1138282   content: "ports free"
/tmp/B1_phase_a_ufw.txt        1392 bytes   md5 e42db94ef33fc72d008b803884e6f7c2   19 lines, 14 numbered rules
/tmp/B1_phase_a_home_layout.txt 2004 bytes   md5 7c454123c4e66427d189a27fafbd60d5   38 lines
/tmp/B1_phase_a_disk.txt        129 bytes    md5 fd2ed809958c1a258d232ba2311e8958   /dev/sda2 4.4T 144G 4.0T 4%
```

## Phase A acceptance scorecard (all PASS)

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | All 4 capture files written | **PASS** | ports.txt, ufw.txt, home_layout.txt, disk.txt all present in /tmp |
| 2 | Ports 9000/9001 free | **PASS** | ports.txt content: `ports free` (ss -tln showed no listeners on either port) |
| 3 | UFW snapshot has >= 14 rules | **PASS** | 14 numbered rules captured (matches Phase A spec expectation) |
| 4 | /home/jes/minio-data/ does NOT exist (greenfield) | **PASS** | `ls: cannot access '/home/jes/minio-data/'` |
| 5 | /home/jes/minio-beast/ does NOT exist (greenfield) | **PASS** | `ls: cannot access '/home/jes/minio-beast/'` |
| 6 | No control-minio-beast container | **PASS** | `docker ps -a --filter name=control-minio-beast` empty |
| 7 | No MinIO images present yet | **PASS** | `docker images quay.io/minio/minio` empty |

Disk capacity sanity (informational): /dev/sda2 4.4TB total, 144GB used, 4.0TB available. Plenty of headroom for the 3 initial buckets + future Atlas + DR backup workloads.

## Pre-existing UFW baseline (relevant excerpt)

14 numbered rules in current state. Notable: rules [1]-[11] are the IoT DENY block (Eufy vacuum, Samsung Fridge/Range/TV, WiZ bulbs, Schlage lock, Blink modules). Rules [12]+ are ALLOW rules for service ports.

**Phase C will add 2 new ALLOW rules (9000 + 9001 from 192.168.1.0/24)** -- per Paco directive, no DENY collision exists for these ports (unlike B2b's 5432 case), so simple `ufw allow ...` suffices. Position in the rule table will be at the end (rules 15+ post-add).

## State of Beast at end of Phase A

- `/tmp/B1_phase_a_*.txt` -- 4 capture files (md5s above)
- `/home/jes/minio-beast/` -- ABSENT (will be created in Phase B)
- `/home/jes/minio-data/` -- ABSENT (will be created in Phase B with chmod 700)
- Container `control-minio-beast` -- ABSENT
- No `minio` images on Beast (Phase B Step B.3 will pull and digest-pin)
- 4.0 TB free on `/`
- 14 UFW rules, ports 9000+9001 unbound
- B2a state: `control-postgres-beast` Up healthy on 127.0.0.1:5432 (subscriber side of B2b replication)

## Phase B preview (informational, not yet authorized)

Per spec Phase B (3 steps):
- B.1: `mkdir -p /home/jes/minio-beast/init` + `mkdir -p /home/jes/minio-data` (chmod 700) + ls verify
- B.2: generate root creds via `openssl rand -base64 30 | tr -d '/+=' | head -c 40`; user `atlas-admin`; write `.env` (chmod 600); print password ONCE for CEO recording (.env will be the only on-disk copy)
- B.3: `docker pull quay.io/minio/minio:RELEASE.<latest>` to capture the resolved sha256 digest; substitute `<DIGEST>` in compose.yaml; bind LAN `192.168.1.152:9000+9001`; bind mount `/home/jes/minio-data:/data`; healthcheck `mc ready local`; `docker compose config` validates

**Phase B-acceptance gates:** .env chmod 600 jes:jes; compose.yaml exists with digest-pinned image; minio-data chmod 700 jes:jes; `docker compose config` exit 0; compose.yaml md5 captured.

## Asks of Paco

1. Confirm Phase A capture fidelity:
   - All 4 capture files present + md5s recorded
   - Ports 9000/9001 free
   - 14 UFW rules captured
   - Greenfield state confirmed (no minio-data, no minio-beast, no container, no image)
2. **Go for Phase B** -- directory tree + .env (root creds, chmod 600) + compose.yaml (digest-pinned MinIO image, LAN bind 9000/9001) + digest verify via `docker pull` + `docker compose config` validation

## Standing rules in effect

- **Rule 1:** Phase A captures are read-only single-shell-command outputs via MCP. Compliant.
- **CLAUDE.md "Spec or no action":** all 4 capture commands verbatim from spec Phase A. No deviations.
- **CLAUDE.md "Docker bypasses UFW":** acknowledged for B1 -- per spec Architecture section: UFW is documented defense-in-depth, real gates are LAN-bind + auth.
- **Correspondence protocol:** this is paco_review #1 of 6 planned for B1.
- **Canon location:** all artifacts on Beast (workspace) + /home/jes/control-plane on CiscoKid (review docs). Per memory edit #20: canon = CiscoKid + GitHub origin/main.

---

**File location:** `/home/jes/control-plane/docs/paco_review_b1_phase_a_capture.md` (untracked, matches /docs precedent)

-- PD
