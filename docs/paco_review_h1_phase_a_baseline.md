# paco_review_h1_phase_a_baseline

**Spec:** H1 -- SlimJim observability + MQTT broker close (`tasks/H1_observability.md`, md5 `fc3f55b33bd2bf31d23c8acec2188049`, 558 lines)
**Step:** Phase A (baseline + dependency check) -- A.1 capture + A.4 3-gate verify; A.2 + A.3 SKIPPED per Paco directive (already done in-thread)
**Status:** AWAITING PACO FIDELITY CONFIRMATION + PHASE B GO
**Predecessor:** Paco directive 2026-04-28 "H1-Observability spec ratified. Begin Phase A." (HEAD `56462e0` on origin/main)
**Author:** PD
**Date:** 2026-04-28 (Day 73)
**Target host:** SlimJim (`192.168.1.40`, hostname `sloan1`)

---

## TL;DR

Phase A executed against the recalibrated 3-gate acceptance scorecard (A.4 was 5 gates in spec, recalibrated to 3 since Paco's pre-thread cleanup already removed sabnzbd/mosquitto/wire-pod/cockpit + UFW orphans 8080+8084). 8 capture files written to `/tmp/H1_phase_a_captures/` on SlimJim with md5 manifest. **All 3 gates PASS.** B2b nanosecond invariant (`2026-04-27T00:13:57.800746541Z`) preserved bit-identical pre and post Phase A on Beast.

Three pre-existing observations on SlimJim are flagged for Paco awareness (none blocking, all benign): mariadbd loopback :3306 / UFW rule [5] for `1883/tcp` already pre-staged from Day 67 IoT spec / UFW [2]+[3] for 80+443 pre-existing.

---

## 1. Pre-Phase-A cleanup acknowledgment

Per Paco's directive section "IMPORTANT context: pre-Phase-A cleanup already done in-thread by Paco", the following changes were made on SlimJim *before* this Phase A capture and are reflected as ABSENT in the captured baseline:

| Item | Pre-cleanup | Post-cleanup (captured baseline) |
|---|---|---|
| `sabnzbd` snap | running on `:8080` loopback | REMOVED (no `sabnzbd` in `snap list`) |
| `mosquitto` snap | broken (Day 67 listener-config bug) | REMOVED (no `mosquitto` snap; only `not-found inactive dead` residual systemd unit name) |
| `wire-pod.service` | 29,320-restart crash loop | `inactive` + `disabled` |
| `cockpit.socket` | holding `:9090` via socket-activation | `inactive` (port 9090 freed for Prometheus arrival in Phase E) |
| UFW rule for `8080/tcp` | orphan ALLOW | DELETED |
| UFW rule for `8084/tcp` | orphan ALLOW | DELETED |
| UFW rule count | 7 (Paco's note) | 5 (verified) |

A.2 (investigate :8080 owner) + A.3 (orphan cleanup) are therefore documented as **completed-pre-phase** by Paco; PD did not re-execute them.

---

## 2. A.1 -- Capture evidence

**Capture directory:** `/tmp/H1_phase_a_captures/` on SlimJim (mode 775 jes:jes, 8 capture files + 1 md5_manifest)

### 2.1 md5 manifest (`md5_manifest.txt`)

```
7b438da8bf6df672aa972b077445adb5  docker.txt          (1298 bytes)
9fac83b94478fc702226218fb52e0eb9  home_pre.txt        (329 bytes)
2ed22197e7bd3f0c31e93f549c426fda  listeners.txt       (2024 bytes)
ce409b9fe423d505439ed6da94750a7c  mem.txt             (338 bytes)
ae1fe5ae32c719ede463694167916689  os.txt              (527 bytes)
81b6e11932900073a14021a9a3c215e6  packages.txt        (2874 bytes)
b60ddd9898b6faf2f111833435b52de8  services.txt        (498 bytes)
f3e22a2869484e1c20e67099391a7b70  ufw_pre.txt         (470 bytes)
```

### 2.2 Per-capture summary

**`os.txt`** -- Ubuntu 24.04.4 LTS "Noble Numbat", kernel `6.8.0-110-generic` x86_64, hostname `sloan1`. Kernel build `#110-Ubuntu SMP PREEMPT_DYNAMIC Thu Mar 19 15:09:20 UTC 2026`.

**`docker.txt`** -- `Docker version 28.2.2, build 28.2.2-0ubuntu1~24.04.1`. 0 containers running. 1 image cached. Server reachable without sudo (existing docker group membership). Confirms Phase B's `docker compose v2` plugin install can proceed against a known-clean engine.

**`mem.txt`**:
- RAM: total 30 GiB, used 1.3 GiB, free 22 GiB, **available 29 GiB** (post-cleanup, Netdata + mariadbd + a few systemd services)
- Swap: total 8.0 GiB, used 0
- Disk `/`: `/dev/mapper/ubuntu--vg-ubuntu--lv` 271 G total, 56 G used, **204 G available** (22% used)

**`listeners.txt`** -- 10 distinct LISTEN sockets total (across IPv4 + IPv6, both unprivileged + sudo views):

| Bind | Port | Owner | Visibility |
|---|---|---|---|
| `0.0.0.0` | 22 | sshd (pid 631576) | LAN |
| `0.0.0.0` | 19999 | netdata (pid 3654798) | LAN |
| `127.0.0.1` | 43301 | containerd (pid 1508) | loopback only |
| `127.0.0.53%lo` | 53 | systemd-resolve (pid 1167) | loopback only |
| `127.0.0.54` | 53 | systemd-resolve | loopback only |
| `127.0.0.1` | 4317 | otel-plugin (pid 3655515, netdata sub) | loopback only |
| `127.0.0.1` | 8125 | netdata statsd | loopback only |
| `127.0.0.1` | 3306 | **mariadbd** (pid 1738) | loopback only |
| `[::]` | 22 | sshd | LAN (IPv6) |
| `[::]` | 19999 | netdata | LAN (IPv6) |

LAN-exposed surfaces: only `:22` + `:19999` -- matches Paco's pre-clean assertion.

**`ufw_pre.txt`** -- 5 numbered rules, all ALLOW IN from `192.168.1.0/24`:

```
[ 1] 22/tcp
[ 2] 80/tcp
[ 3] 443/tcp
[ 4] 19999/tcp
[ 5] 1883/tcp
```

**`packages.txt`** -- 19 `netdata-*` packages installed (full plugin set including ebpf / otel / systemd-units / scripts / pythond / network-viewer / etc.). **NO** prometheus / grafana / node-exporter / mosquitto APT packages present. Confirms Phase B-E will install all four cleanly without conflicts.

**`services.txt`** (3 entries):
- `netdata.service` -- loaded / active / running
- `snap.mosquitto.mosquitto.service` -- `not-found inactive dead` (residual unit name from removed snap; harmless, no unit file)
- `systemd-journald@netdata.service` -- loaded / active / running (per-namespace journal for netdata)

No `prometheus.service`, no `grafana.service`, no apt `mosquitto.service` -- clean ground for Phase C+E.

**`home_pre.txt`** -- `/home/jes` directory listing (19 entries):
- Day-67-era scaffolding: `agent_bus.py`(+bak), `applications.csv`, `build_index.py`, `query_ai.py`, `query_ai_old.py`, `rag_env/`, `knowledge_base/`, `knowledge_base_index/`, `New_Portfolio.md`, `job_pipeline.py`
- Watchdog scaffolding: `dock-watchdog.{log,pid,sh}`, `dock-watchdog.sh.bak.2026-01-18-190401`
- Residual: `wire-pod/` (project dir from removed service), `mosquitto_rollback.sh` (prior rollback helper, no current dependency), `snap/` (snap state)
- D2 smoke artifact: `my_first_remote_file.txt` (created during D2 verification, harmless)

None block H1. Phase E's `observability/` skeleton will be created at `/home/jes/observability/` -- no name collision with anything in `home_pre.txt`.

---

## 3. A.4 -- 3-gate acceptance scorecard

| Gate | Spec wording | Live observed | Result |
|---|---|---|---|
| 1 | All baseline captures written, md5s recorded | 8 captures + `md5_manifest.txt` written to `/tmp/H1_phase_a_captures/`; 8 md5s recorded in manifest | **PASS** |
| 2 | Docker version >= 24.0 (we have 28.2.2) | Docker major version `28` -> **28.2.2** confirmed live | **PASS** |
| 3 | Disk >= 50 GB free (204 GB) AND RAM >= 4 GB free (we have 22 GB) | Disk available `204 G` / RAM available `29 G` (free column read 22 GiB; available column 29 GiB; both >= 4 GB) | **PASS** |

**Phase A internal scorecard: 3/3 PASS.**

---

## 4. State integrity -- B2b nanosecond invariant

```
# Pre-Phase-A (Beast):
control-postgres-beast: 2026-04-27T00:13:57.800746541Z healthy RestartCount=0

# Post-Phase-A (Beast):
control-postgres-beast: 2026-04-27T00:13:57.800746541Z healthy RestartCount=0
```

BIT-IDENTICAL nanosecond match. Phase A operations were entirely confined to `/tmp/` on SlimJim -- no Beast service touched, no listener moved, no UFW rule changed on any host. Anchor preserved from B1 close (commit `1fce00e`) through this Phase A capture, +1 day +21 hours of continuous undisturbed operation.

---

## 5. Pre-existing observations worth flagging (none blocking)

These surfaced during baseline capture. None are H1 blockers; flagging for Paco awareness so they don't surprise Phase B+ work.

### 5.1 `mariadbd` on `127.0.0.1:3306` (LOOPBACK-ONLY)

Observed: `mariadbd (pid 1738)` listening on `127.0.0.1:3306`. NOT LAN-exposed. NO UFW rule for 3306. Purpose unknown to PD -- predates H1 spec, possibly from an earlier scaffolding effort. Doesn't conflict with any H1 substrate. Phase E's compose stack uses port `9090` (Prometheus), `3000` (Grafana), `9100` (node_exporter), `1883` (Mosquitto) -- no collision with 3306.

**Recommendation:** document existence; no action this spec.

### 5.2 UFW rule [5] for `1883/tcp` already present

UFW already has `[5] 1883/tcp ALLOW from 192.168.1.0/24` from Day 67's IoT-security pre-staging. **Phase C MUST NOT double-add the rule** -- inserting again would create a duplicate. PD will detect this in Phase C and skip the `ufw allow 1883/tcp` step (or use `ufw status | grep -q '1883/tcp'` as a guard). Spec line 252-260 (Phase D) and Phase C UFW step both need this guard added if not already present in the spec body.

**Recommendation:** Phase C should either (a) delete + re-add with a comment for canonical-state cleanliness, or (b) skip and document the pre-existing rule as continuation. PD prefers (b) -- the rule is already correct shape, deleting and re-adding risks transient gaps and doesn't change UFW behavior.

### 5.3 UFW rules [2] 80/tcp + [3] 443/tcp pre-existing

Observed: ALLOW from `.0/24` for 80 + 443. No HTTP listener observed on either port (no `:80` or `:443` in listeners.txt). Likely pre-existing from older scaffolding (perhaps a Caddy/reverse-proxy iteration that didn't ship). Don't conflict with H1; both ports are dormant LAN-allows.

**Recommendation:** flag for Q4 cleanup; not a Phase A action.

---

## 6. Asks of Paco

1. **Confirm Phase A 3/3 gates PASS** against the captured md5 manifest and per-capture summary in section 2.
2. **Authorize Phase B GO** (docker compose v2 plugin + docker group) per spec section 6 lines 129-148.
3. **Rule on observation 5.2** (UFW [5] 1883/tcp pre-existing): does Phase C skip the rule-add (PD recommendation) or delete+re-add for canonical state? Suggest skip to minimize churn; pre-existing rule is functionally identical to what spec mandates.
4. **Rule on observations 5.1 + 5.3** (mariadbd + UFW 80/443): bank as P5 carryover or document-and-move-on? PD suggests document-and-move-on -- they're orthogonal to H1 and surfacing them in this review serves the audit-trail purpose.

---

## 7. Cross-references

**Standing rules invoked:**
- Memory: `feedback_paco_review_doc_per_step.md` (per-step review docs in `/home/jes/control-plane/docs/`)
- Memory: `feedback_mcp_deferred_restart_verify.md` (not invoked this phase -- no MCP/service restart)
- B2b nanosecond invariant preservation (continuing from B1 close on 2026-04-27)
- Spec or no action -- A.2/A.3 skipped per explicit Paco directive only

**Captures on disk (SlimJim):**
- `/tmp/H1_phase_a_captures/{os,docker,mem,listeners,ufw_pre,packages,services,home_pre}.txt`
- `/tmp/H1_phase_a_captures/md5_manifest.txt`

**Spec section refs:**
- `tasks/H1_observability.md` lines 77-128 (Phase A complete section, including A.4 5-gate spec text superseded by Paco's 3-gate recalibration)

**Predecessor doc:**
- Paco directive 2026-04-28 (this thread, in-CEO-relay -- not yet captured as a `paco_response_*.md` file since the directive arrived as conversational ratification + Phase A authorization in one turn)

---

## 8. Status

**AWAITING PACO FIDELITY CONFIRMATION + PHASE B GO.**

PD is paused. No SlimJim infra touched beyond `/tmp/H1_phase_a_captures/`. No CiscoKid file touched beyond this review doc + (pending Sloan direction) git operations. No Beast service touched. B2b anchor undisturbed.

Ready to begin Phase B (docker compose plugin + docker group) on Paco's go.

-- PD
