# paco_review_h1_phase_b_compose_plugin

**Spec:** H1 -- SlimJim observability + MQTT broker close (`tasks/H1_observability.md`, md5 `fc3f55b33bd2bf31d23c8acec2188049`)
**Step:** Phase B -- docker compose v2 plugin + jes -> docker group
**Status:** AWAITING PACO FIDELITY CONFIRMATION + PHASE C GO
**Predecessor:** `docs/paco_response_h1_phase_a_confirm_phase_b_go.md` (Phase A PASS + Phase B GO authorization)
**Auxiliary predecessor:** `docs/paco_response_h1_phase_b_pkg_name_correction.md` (commit `cc2b26b`, package-name substitution authorization)
**Author:** PD
**Date:** 2026-04-28 (Day 73)
**Target host:** SlimJim (`192.168.1.40`, hostname `sloan1`)

---

## TL;DR

Phase B executed cleanly with one Paco-authorized package-name substitution (`docker-compose-plugin` -> `docker-compose-v2`) reflecting Ubuntu noble's universe-repo distribution naming. Compose v2 (`2.40.3+ds1-0ubuntu1~24.04.1`) installed; `jes` added to `docker` group; refreshed-shell verification via `sg docker -c '...'` confirms sudoless `docker ps` works. **All 4 gates PASS.** Beast `control-postgres-beast` + `control-garage-beast` anchors bit-identical pre and post Phase B.

---

## 1. Package-name substitution (per `paco_response_h1_phase_b_pkg_name_correction.md`, commit `cc2b26b`)

The spec section 6 line `sudo apt install -y docker-compose-plugin` was substituted to `sudo apt install -y docker-compose-v2`. Both packages install the same Compose v2 Go binary at `/usr/libexec/docker/cli-plugins/docker-compose`; the difference is purely vendor (Docker CE repo vs Ubuntu universe). SlimJim has Ubuntu's `docker.io 28.2.2-0ubuntu1~24.04.1`, so the universe-path package name (`docker-compose-v2`) is correct.

New standing rule banked from Paco's response: **"Package names in Paco specs are advisory; PD verifies and corrects to the matching package on the target distro before install. Document substitution in the review doc."** Going forward this kind of substitution is at PD authority, not an escalation event.

---

## 2. Pre-install evidence: `apt-cache policy docker-compose-v2`

Captured immediately before `apt install` per directive review-doc requirement #2:

```
docker-compose-v2:
  Installed: (none)
  Candidate: 2.40.3+ds1-0ubuntu1~24.04.1
  Version table:
     2.40.3+ds1-0ubuntu1~24.04.1 500
        500 http://us.archive.ubuntu.com/ubuntu noble-updates/universe amd64 Packages
     2.24.6+ds1-0ubuntu2 500
        500 http://us.archive.ubuntu.com/ubuntu noble/universe amd64 Packages
```

Source: Ubuntu noble-updates universe repo (`http://us.archive.ubuntu.com/ubuntu`). Confirmed distro-native, no third-party repo introduction.

---

## 3. Install execution

### 3.1 Prior failed attempt context

An initial `sudo apt install -y docker-compose-plugin` (using the spec's literal package name) failed with `E: Unable to locate package docker-compose-plugin`. The `&&` chain bailed cleanly at that point: `apt update` had run (cache refresh, harmless), but `apt install`, `usermod`, `sg verify`, and anchor recheck did NOT execute. State at failure: jes still NOT in docker group, docker daemon untouched, no /usr/libexec or ~/.docker plugin paths created. Failure was reported via Cowork; CEO ratified Option (b) (skip paco_request, swap to `docker-compose-v2` directly); Paco subsequently produced `paco_response_h1_phase_b_pkg_name_correction.md` (commit `cc2b26b`) authorizing the swap and banking the new standing rule.

### 3.2 Successful install (corrected package name)

```
Fetched 14.8 MB in 2s (7,846 kB/s)
Selecting previously unselected package docker-compose-v2.
...
Preparing to unpack .../docker-compose-v2_2.40.3+ds1-0ubuntu1~24.04.1_amd64.deb ...
Unpacking docker-compose-v2 (2.40.3+ds1-0ubuntu1~24.04.1) ...
Setting up docker-compose-v2 (2.40.3+ds1-0ubuntu1~24.04.1) ...
No services need to be restarted.
No containers need to be restarted.
No user sessions are running outdated binaries.
```

Key details from apt's needrestart hook: "No services need to be restarted" -- Docker daemon untouched, no transient downtime.

### 3.3 Plugin binary path verification

```
$ ls -la /usr/libexec/docker/cli-plugins/
total 64956
drwxr-xr-x 2 root root     4096 Apr 28 09:31 .
drwxr-xr-x 3 root root     4096 Apr 28 09:31 ..
-rwxr-xr-x 1 root root 66503008 Feb 12 08:56 docker-compose
```

Binary at canonical path, mode 755 root:root, ~66.5 MB. Discovered automatically by Docker CLI as a plugin (no env-var or alias needed).

### 3.4 `docker compose version` post-install

```
Docker Compose version 2.40.3+ds1-0ubuntu1~24.04.1
```

Matches the apt candidate exactly. v2.x as required by gate 1.

---

## 4. usermod -aG docker jes

```
$ sudo usermod -aG docker jes
usermod returned: 0

$ id jes
uid=1000(jes) gid=1000(jes) groups=1000(jes),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),101(lxd),988(ollama),115(docker)

$ groups jes
jes : jes adm cdrom sudo dip plugdev lxd ollama docker
```

`docker` (gid 115) added to jes's secondary groups. Account-level state immediately reflects the change; existing shells need group refresh to pick it up (handled in section 5 via `sg`).

**Side observation:** jes is also a member of `988(ollama)` -- Ollama is installed on SlimJim. Orthogonal to H1; banking as observation, not action.

---

## 5. Refreshed-shell verification (path: `sg docker -c '<commands>'`)

Group membership is established at login time and doesn't refresh in existing shells. The two paths to verify the change in a refreshed-membership shell are: (a) logout + new ssh session, or (b) `sg docker -c '<commands>'` (single subshell with the docker group active). **PD used path (b)** since the verification is a one-shot read and does not need an interactive shell.

```
$ sg docker -c 'echo "active groups in sg subshell: $(groups)"; echo "---docker ps in sg subshell:"; docker ps 2>&1 | head -10'

active groups in sg subshell: docker adm cdrom sudo dip plugdev lxd ollama jes
---docker ps in sg subshell:
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

`docker` is active as the primary group in the subshell. `docker ps` returns the empty-list header (no containers running on SlimJim, expected pre-Phase-E). No `permission denied`, no `cannot connect to the Docker daemon socket`. Sudoless docker access confirmed.

---

## 6. Beast anchor preservation -- BOTH containers

### 6.1 Pre-Phase-B (captured during Step 1 preflight, 2026-04-28)

```
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

### 6.2 Post-Phase-B (captured immediately after install + usermod + sg verify completed)

```
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

**BIT-IDENTICAL nanosecond match across both containers.** Phase B was confined entirely to SlimJim (apt operations + usermod). No Beast service touched, no listener changed on any host. B2b nanosecond invariant continues holding from B1 close (commit `1fce00e`, 2026-04-27) through this Phase B (~36 hours of continuous undisturbed operation).

---

## 7. Phase B 4-gate acceptance scorecard

| Gate | Spec wording | Live observed | Result |
|---|---|---|---|
| 1 | `docker compose version` returns v2.x | `2.40.3+ds1-0ubuntu1~24.04.1` (v2.40.3) | **PASS** |
| 2 | `id jes` shows `docker` group | `uid=1000(jes) gid=1000(jes) groups=...,115(docker)` | **PASS** |
| 3 | `docker ps` works without sudo in refreshed shell | `sg docker -c 'docker ps'` returns `CONTAINER ID ...` header, no permission error | **PASS** |
| 4 | Both Beast nanosecond anchors bit-identical pre/post Phase B | postgres `2026-04-27T00:13:57.800746541Z` + garage `2026-04-27T05:39:58.168067641Z` (NANOSECOND-IDENTICAL) | **PASS** |

**Phase B internal scorecard: 4/4 PASS.**

---

## 8. State at end of Phase B

### SlimJim
- `docker.io 28.2.2-0ubuntu1~24.04.1` (unchanged)
- `docker-compose-v2 2.40.3+ds1-0ubuntu1~24.04.1` **(NEW, this phase)**
- `/usr/libexec/docker/cli-plugins/docker-compose` -- 66.5 MB binary, mode 755 root:root
- `jes` member of `docker` group (gid 115); existing shells refresh via `sg docker -c` or new login
- No containers running on SlimJim Docker daemon (pre-Phase-E expected)
- UFW unchanged at 5 rules
- Listeners unchanged (`:22` + `:19999` LAN-exposed; loopback-only services unchanged)
- B2b/Garage anchors NOT touched (pure SlimJim work)

### Beast (read-only confirmation)
- `control-postgres-beast` healthy, RestartCount=0, anchor preserved
- `control-garage-beast` healthy, RestartCount=0, anchor preserved

### CiscoKid (read-only confirmation)
- HEAD `cc2b26b` (no change this phase; Paco's response doc was the latest commit)
- This review doc to be untracked-pending-Paco-confirmation per standing pattern

---

## 9. Side observations (informational, no action this phase)

### 9.1 Ollama on SlimJim

`jes` membership in `988(ollama)` group implies Ollama is installed on SlimJim (likely with model service running). Not in spec scope; banking as a fleet-state observation. Could be a candidate for `node_exporter` metric scraping in Phase D if relevant; will defer to Paco direction in Phase D / E if discussion warrants.

### 9.2 Available kernel/microcode upgrades

apt's needrestart hook noted: "Running kernel seems to be up-to-date" -- so no kernel upgrade pending. "33 packages can be upgraded" was reported by `apt update` earlier (general system upgrade backlog, unrelated to H1). Banking as observation; not in H1 scope.

---

## 10. Q3/Q4 carryovers from Paco's Phase A confirmation

Per `paco_response_h1_phase_a_confirm_phase_b_go.md`:

- **Q3 (UFW [5] 1883/tcp pre-existing rule):** Phase C will use idempotency guard `sudo ufw status | grep -qE '^\[[ 0-9]+\] 1883/tcp.*ALLOW.*192\.168\.1\.0/24' || sudo ufw allow ...`. SKIP-with-grep-guard authorized. Will execute in Phase C.
- **Q4 (mariadb + UFW 80/443):** Side-task AFTER Phase B closes -- separate `paco_review_h1_side_task_mariadb_ufw_cleanup.md`. NOT folded into Phase B execution. Banking only this turn.

---

## 11. Asks of Paco

1. **Confirm Phase B 4/4 gates PASS** against the captured evidence in sections 2-7.
2. **Authorize Phase C GO** (mosquitto 2.x install + listener config + smoke test) per spec section 7 (lines 150-218), with the Q3 UFW idempotency guard already authorized in `paco_response_h1_phase_a_confirm_phase_b_go.md`.
3. **Acknowledge new standing rule** ("Package names in Paco specs are advisory; PD verifies and corrects to the matching package on the target distro before install. Document substitution in the review doc.") -- this review doc is the first application of the rule.
4. **Flag for future reference:** the `5/cmd_failed -> escalate -> CEO ratify -> Paco confirm via dedicated paco_response.md` flow worked cleanly here for a non-spec-changing process correction. Banking as the canonical pattern for similar future cases.

---

## 12. Cross-references

**Standing rules invoked:**
- Memory: `feedback_paco_review_doc_per_step.md` (per-step review docs in `/home/jes/control-plane/docs/`)
- New rule banked: package-name substitutions within agreed strategy at PD authority (per `paco_response_h1_phase_b_pkg_name_correction.md`)
- Spec or no action: substitution authorized via paco_response BEFORE install attempt
- B2b/Garage nanosecond invariant preservation: continuing from B1 close (`1fce00e`, 2026-04-27)

**Predecessor doc chain:**
- `paco_review_h1_phase_a_baseline.md` (Phase A captures + 3-gate PASS)
- `paco_response_h1_phase_a_confirm_phase_b_go.md` (Phase A confirm + Phase B GO + Q3/Q4 rulings)
- `paco_response_h1_phase_b_pkg_name_correction.md` (Phase B package-name swap authorization, commit `cc2b26b`)
- (this) `paco_review_h1_phase_b_compose_plugin.md`

**Spec section refs:**
- `tasks/H1_observability.md` lines 129-148 (Phase B body, with the package-name substitution applied)

---

## 13. Status

**AWAITING PACO FIDELITY CONFIRMATION + PHASE C GO.**

PD is paused. SlimJim infra changed: `docker-compose-v2` package installed system-wide, `jes` added to `docker` group at account level. No CiscoKid file touched beyond this review doc. No Beast service touched. B2b + Garage anchors undisturbed.

Ready to begin Phase C (mosquitto 2.x + listener config + smoke test) on Paco's go.

-- PD
