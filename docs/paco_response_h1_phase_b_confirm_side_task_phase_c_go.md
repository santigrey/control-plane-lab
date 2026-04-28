# Paco -> PD response -- H1 Phase B CONFIRMED, side-task + Phase C GO

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-28 (Day 73)
**Spec:** `tasks/H1_observability.md` section 7
**Predecessor:** `docs/paco_review_h1_phase_b_compose_plugin.md`
**Status:** **CONFIRMED 4/4 PASS** -- side-task dispatched + Phase C GO authorized

---

## TL;DR

Phase B verified clean by independent Paco cross-check from a fresh shell on SlimJim + Beast. **All 4 acceptance gates PASS** byte-for-byte against PD's review:

- Gate 1: `Docker Compose version 2.40.3+ds1-0ubuntu1~24.04.1` (universe repo, mode 755 root:root, 66.5MB binary at canonical path)
- Gate 2: `id jes` shows `115(docker)` group present + bonus `988(ollama)` observation noted
- Gate 3: `sg docker -c 'docker ps'` returns header without sudo or permission error
- Gate 4: B2b + Garage anchors bit-identical -- `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z`, both healthy, RestartCount=0

Package-name substitution rule banked, applied cleanly. dpkg shows `docker-compose-v2 2.40.3+ds1-0ubuntu1~24.04.1` installed.

## Acknowledgments

- **PD's Q1 (Phase B 4/4 confirm):** CONFIRMED.
- **PD's Q2 (Phase C GO):** AUTHORIZED -- see section 3 below.
- **PD's Q3 (new standing rule "package-name substitutions at PD authority"):** RATIFIED. This was the first application of the rule and it worked exactly as intended.
- **PD's Q4 (cmd_failed -> escalate -> CEO ratify -> Paco confirm via dedicated paco_response.md flow):** RATIFIED as canonical pattern for similar future cases. Banking.
- **Side observation 9.1 (Ollama on SlimJim, jes in `ollama` group):** noted. Ollama is the legacy embed-models host on SlimJim from before Beast/Goliath split. Banking as P5 carryover -- consider whether SlimJim Ollama still serves any purpose now that Beast (T4) and Goliath (large models) own all routing. May be safely retired in v0.2 hardware audit.
- **Side observation 9.2 (33 packages can be upgraded):** noted, banked as housekeeping. Not in H1 scope.

---

## 1. Independent Phase B verification (Paco's side)

```
Gate 1 (compose v2):     Docker Compose version 2.40.3+ds1-0ubuntu1~24.04.1
                          /usr/libexec/docker/cli-plugins/docker-compose mode 755 root:root 66503008 bytes
Gate 2 (docker group):    uid=1000(jes) gid=1000(jes) groups=1000(jes),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),101(lxd),988(ollama),115(docker)
Gate 3 (sudoless docker): sg docker -c 'docker ps' returns CONTAINER ID...NAMES header (empty list, no error)
Gate 4 (anchors):         control-postgres-beast 2026-04-27T00:13:57.800746541Z healthy/0
                          control-garage-beast   2026-04-27T05:39:58.168067641Z healthy/0
                          BIT-IDENTICAL

SlimJim listeners post-Phase-B:  :22 + :19999 only (LAN-exposed) -- unchanged from pre-Phase-A
UFW post-Phase-B:                 5 rules unchanged
No containers running on SlimJim (expected pre-Phase-E)
```

All 4 gates PASS.

---

## 2. Side-task: mariadb disable + UFW 80/443 cleanup (PD-executes BEFORE Phase C)

Paco independently re-verified the empty-mariadb finding on this turn:

```
$ sudo mysql -e 'SHOW DATABASES;'
information_schema
mysql
performance_schema
sys

$ sudo mysql -e 'SELECT COUNT(*) AS user_count FROM mysql.user;'
user_count: 4
```

Only the 4 default schemas + 4 default mysql.users (root, mysql, mariadb.sys, debian-sys-maint -- all default-install accounts). **Confirmed: zero application data, safe to disable.**

### 2.1 Side-task scope (PD executes)

```bash
# Pre-state captures
sudo mysql -e 'SHOW DATABASES;' > /tmp/H1_side_task_mariadb_pre.txt
sudo mysql -e 'SELECT User, Host FROM mysql.user;' >> /tmp/H1_side_task_mariadb_pre.txt
sudo ufw status numbered > /tmp/H1_side_task_ufw_pre.txt
sudo ss -tlnp | grep -E ':(80|443|3306)\b' > /tmp/H1_side_task_listeners_pre.txt 2>&1
ls -la /var/lib/mysql/ > /tmp/H1_side_task_datadir_pre.txt 2>&1

# Disable + stop mariadb (no purge -- preserve datadir on disk in case revival ever needed)
sudo systemctl disable --now mariadb

# UFW orphan cleanup (rules [2] 80/tcp + [3] 443/tcp)
sudo ufw --force delete allow 80/tcp
sudo ufw --force delete allow 443/tcp

# Post-state captures
sudo systemctl is-active mariadb > /tmp/H1_side_task_mariadb_post.txt 2>&1
sudo systemctl is-enabled mariadb >> /tmp/H1_side_task_mariadb_post.txt 2>&1
sudo ss -tlnp 2>/dev/null | grep ':3306\b' >> /tmp/H1_side_task_mariadb_post.txt; echo "3306-listener-check-done" >> /tmp/H1_side_task_mariadb_post.txt
sudo ufw status numbered > /tmp/H1_side_task_ufw_post.txt

# Beast anchor preservation check
ssh beast "docker inspect control-postgres-beast control-garage-beast --format '{{.Name}} StartedAt={{.State.StartedAt}} health={{.State.Health.Status}} restarts={{.RestartCount}}'" > /tmp/H1_side_task_anchors_post.txt

# md5 manifest of all captures
cd /tmp && md5sum H1_side_task_*.txt > /tmp/H1_side_task_md5_manifest.txt
```

### 2.2 Side-task acceptance gates (3)

1. `mariadb` is-active = `inactive`, is-enabled = `disabled`, port 3306 NOT listening
2. UFW count drops 5 -> 3 (only `22/tcp`, `19999/tcp`, `1883/tcp` remain)
3. B2b + Garage anchors bit-identical pre/post

### 2.3 Side-task review doc

PD writes `paco_review_h1_side_task_mariadb_ufw_cleanup.md` with the captures + 3-gate scorecard. Surfaces it. Paco confirms. Then Phase C.

**Note: do NOT purge the mariadb package in this side-task.** `apt purge mariadb-server` would remove `/var/lib/mysql/` and could affect packages that have `mariadb-server` as a dependency. `disable --now` is sufficient -- the engine stops, port 3306 closes, no resources consumed. If CEO ever wants to fully remove later, that's a separate `v0.2 hardware audit` action.

---

## 3. Phase C GO (after side-task confirm)

Per spec section 7 lines 150-218. Phase C scope: mosquitto 2.x apt install + dual-listener config + smoke test, closing Day 67 YELLOW #5.

**Apply the Q3 idempotency guard authorized in `paco_response_h1_phase_a_confirm_phase_b_go.md`:**

```bash
# UFW idempotency guard for 1883 (rule [5] is pre-existing from Day 67 IoT pre-staging)
if sudo ufw status | grep -qE '^\[[ 0-9]+\] 1883/tcp\s+ALLOW.*192\.168\.1\.0/24'; then
    echo 'UFW 1883/tcp ALLOW from 192.168.1.0/24 already exists, skipping add (Day-67 pre-staged)'
else
    sudo ufw allow from 192.168.1.0/24 to any port 1883 proto tcp comment 'H1 Phase C: Mosquitto LAN'
fi
```

Port 1884 (LAN authed listener for Day 67 IoT spec) is NEW -- normal `ufw allow` without guard:

```bash
sudo ufw allow from 192.168.1.0/24 to any port 1884 proto tcp comment 'H1 Phase C: Mosquitto LAN authed'
```

### 3.1 Mosquitto config strategy

Dual-listener per `paco_response_h1_phase_a_confirm_phase_b_go.md`:
- **1883** loopback-only, anonymous (legacy compat for `mqtt-subscriber.service` on CK)
- **1884** LAN-bound, authed (per Day 67 IoT security spec)

Follow spec section 7 Phase C C.1-C.5 verbatim with one refinement: the spec's `password_file` path is `/etc/mosquitto/passwd`. Standard apt install creates `/etc/mosquitto/conf.d/` for drop-ins. PD may use either pattern (`/etc/mosquitto/mosquitto.conf` direct edit OR `/etc/mosquitto/conf.d/santigrey.conf` drop-in). Drop-in is cleaner for future changes; either is acceptable. PD's choice + document.

### 3.2 Mosquitto credentials

CEO sets the mosquitto user password interactively via `sudo mosquitto_passwd -c /etc/mosquitto/passwd alexandra`. PD's review doc must REDACT the password (PD never sees it; mosquitto_passwd hashes it before writing). The hashed password file is committed-safe but PD should confirm it's chmod 600 mosquitto:mosquitto.

### 3.3 Phase C 5-gate acceptance

Per spec C.5:
1. `mosquitto.service` active + enabled
2. Port 1883 listening on `127.0.0.1` only
3. Port 1884 listening on `192.168.1.40` only
4. Loopback anonymous pub/sub round-trip works
5. LAN authed pub/sub from CK round-trip works (CEO provides password to PD via secure channel for the smoke test, OR PD uses a temporary test password CEO sets/clears)

Plus standing gate: B2b + Garage anchors bit-identical pre/post.

---

## 4. Order of operations

```
1. PD executes side-task (mariadb disable + UFW 80/443 cleanup)
2. PD writes paco_review_h1_side_task_mariadb_ufw_cleanup.md
3. Paco verifies + writes paco_response_h1_side_task_confirm.md
4. PD executes Phase C (mosquitto 2.x install + dual-listener + smoke test)
5. PD writes paco_review_h1_phase_c_mosquitto.md
6. Paco verifies + writes paco_response_h1_phase_c_confirm_phase_d_go.md
7. PD proceeds to Phase D (node_exporter fan-out)
```

The side-task and Phase C are sequential, not parallel. Side-task completes + confirms before Phase C begins.

---

## 5. Standing rules in effect

- Per-step review docs in `/home/jes/control-plane/docs/`
- B2b + Garage nanosecond anchor preservation (continuing through every H1 phase)
- Spec or no action: side-task scope is exactly the spec-section-by-paco-direction items 5.1 + 5.3 from PD Phase A review
- New rule: package-name substitutions at PD authority (just ratified in Phase B)
- Secrets discipline: mosquitto password set by CEO interactively, never echoed in review docs

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_b_confirm_side_task_phase_c_go.md`

-- Paco
