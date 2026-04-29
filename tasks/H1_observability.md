# H1 -- SlimJim observability + MQTT broker close

**Owner:** Paco (architect) -> PD (executor)
**Target host:** SlimJim (192.168.1.40)
**Auxiliary hosts:** CiscoKid, Beast, Goliath, KaliPi (node_exporter targets)
**Status:** DRAFT, awaiting CEO ratification before PD execution

---

## 1. Goal

Deploy a fleet-wide observability stack on SlimJim that gives Sloan:

1. Real-time per-second per-node metrics dashboard (deep-dive)
2. Long-term metric storage (30-day retention) for trend analysis + alerting hooks
3. Industry-standard tooling visible in the portfolio narrative (Prometheus + Grafana)
4. A working MQTT broker on SlimJim, closing the long-standing YELLOW item from Day 67

## 2. Architecture

```
  +------------------+
  |  Grafana :3000   |  <-- LAN-bound, dashboards + future alerting
  +--------+---------+
           | datasource
           v
  +------------------+         +------------------+
  |  Prometheus :9090 | <----- |  scrape config   |
  +--------+---------+         +------------------+
           | scrapes (every 15s)
           |
  +--------+---------+--------+--------+--------+--------+
  |        |         |        |        |        |        |
  v        v         v        v        v        v        v
  Netdata  node_exp  node_exp node_exp node_exp node_exp self
  SlimJim  CK        Beast    Goliath  KaliPi   SlimJim  Prom
  :19999   :9100     :9100    :9100    :9100    :9100    :9090
  (existing)  (NEW)

  Mosquitto :1883 LAN  <-- MQTT broker, parallel sub-track
  (anonymous + authed listeners per Day 67 IoT security spec)
```

Netdata stays as primary deep-dive UI on SlimJim. Prometheus scrapes Netdata's `/api/v1/allmetrics?format=prometheus` endpoint AND each node's `node_exporter` for uniform fleet metrics. Grafana provides centralized dashboards backed by Prometheus.

## 3. Picks (architectural commitments)

| # | Pick | Reason |
|---|---|---|
| 1 | Deploy Prometheus + Grafana + Mosquitto via **Docker Compose v2** on SlimJim | Idiom matches B1/B2a/B2b. Single restart pattern. |
| 2 | **node_exporter** on CK / Beast / Goliath / KaliPi via apt + systemd unit (NOT Docker) | Native package = simpler deploy, no per-node Docker dependency. KaliPi is Pi 4-class so Docker overhead matters there. |
| 3 | SlimJim's own metrics: **scrape Netdata** (already running :19999) + node_exporter container | Netdata is already deployed; double-coverage is fine. |
| 4 | **Prometheus retention: 30 days, 10 GB cap** | Fits SlimJim disk (204 GB free); reasonable trend window. |
| 5 | **Scrape interval: 15s default** | Standard balance between resolution and storage cost. |
| 6 | **LAN-bind only** for 9090 + 3000 + 1883 (UFW restricts to 192.168.1.0/24) | No internet exposure; access from CK / Beast / workstation. |
| 7 | **Persistent volumes** at `/home/jes/observability/{prom-data,grafana-data,mosquitto-data,mosquitto-config}` chmod 700 | Survives restarts; bind-mounted for inspection. |
| 8 | **Default dashboards on Grafana**: Node Exporter Full (1860), Prometheus Stats (3662) -- imported via provisioning, not manual | Reproducible; spec-canonical. |
| 9 | **No alertmanager in v0.1** | Alerts come in v0.2 once Atlas is built and can act on them. |
| 10 | **Mosquitto 2.x with TWO listeners**: localhost-anon (for legacy `mqtt-subscriber.service` on CK) + LAN-authed (per Day 67 IoT spec) | Closes YELLOW #5; preserves working integrations. |

## 4. Phase outline

9 phases. PD executes one at a time, surfaces review per step, Paco confirms before next phase. Same protocol as B1.

```
A -- baseline + dependency check + UFW orphan cleanup
B -- install docker compose v2 plugin + add jes to docker group
C -- mosquitto 2.x install + listener config + smoke test (closes YELLOW #5)
D -- node_exporter fan-out (4 nodes: CK, Beast, Goliath, KaliPi)
E -- /home/jes/observability/ skeleton + compose.yaml + prometheus.yml + grafana provisioning files
F -- UFW rules: 9090 + 3000 + 1883 + 9100 (the last one inbound from SlimJim only on each target)
G -- docker compose up + healthcheck poll (Prometheus + Grafana)
H -- Grafana datasource auto-provisioned + dashboards imported + LAN smoke from CK
I -- restart safety + ship report (15-gate scorecard)
```

## 5. Phase A -- baseline + dependency check + UFW orphan cleanup

**Goal:** capture pre-state, verify clean ground, remove dead UFW rules.

### A.1 -- Capture pre-state

```bash
mkdir -p /tmp/H1_phase_a_captures
cd /tmp/H1_phase_a_captures
uname -a > os.txt
cat /etc/os-release >> os.txt
docker --version > docker.txt
docker info 2>/dev/null >> docker.txt || sudo docker info >> docker.txt
free -h > mem.txt
df -h / >> mem.txt
ss -tlnp 2>/dev/null > listeners.txt; sudo ss -tlnp >> listeners.txt
sudo ufw status numbered > ufw_pre.txt
dpkg -l | grep -E 'netdata|prometheus|grafana|node-exporter|mosquitto' > packages.txt
systemctl list-units --type=service --all | grep -iE 'netdata|mosquitto|prom|grafana' > services.txt
ls /home/jes > home_pre.txt

# P6 #14 preflight: capture client-side mosquitto-clients version on each consuming host
# (banked Phase C close-out 2026-04-28; matrix-collision discriminator on Day 73 ESC #6 -> #7)
ssh jes@192.168.1.10 'dpkg -l mosquitto-clients libmosquitto1 2>/dev/null | grep ^ii' > /tmp/H1_phase_a_captures/ck_mqtt_client_version.txt 2>&1 || true
ssh jes@192.168.1.152 'dpkg -l mosquitto-clients libmosquitto1 2>/dev/null | grep ^ii' > /tmp/H1_phase_a_captures/beast_mqtt_client_version.txt 2>&1 || true
```

Report: `paco_review_h1_phase_a_baseline.md` with each capture summarized (md5s, key values).

### A.2 -- Investigate UFW orphans (8084) + identify owner of 8080

From Paco's pre-flight: ports 8080 and 8084 have UFW rules but only 8080 has a listener (a `python3` process).

```bash
ps -p $(sudo ss -tlnp | grep ':8080' | grep -oP 'pid=\d+' | head -1 | cut -d= -f2) -o pid,user,cmd 2>/dev/null
ls -la /proc/$(...) 2>/dev/null  # work backwards if needed
```

**Acceptance:** PD reports what is on 8080 and proposes whether to keep, archive, or remove it. CEO ratifies before A.3.

### A.3 -- UFW orphan cleanup

Remove the UFW rule for 8084 if no business case found. Decision on 8080 deferred to CEO.

```bash
sudo ufw delete allow 8084/tcp from 192.168.1.0/24
sudo ufw status numbered > /tmp/H1_phase_a_captures/ufw_post.txt
```

### A.4 -- Acceptance gates (6)

1. All 6 captures written to /tmp/H1_phase_a_captures/, md5s recorded
2. Docker version >= 24.0 confirmed
3. SlimJim disk has >= 50 GB free (we have 204 GB)
4. SlimJim RAM available >= 4 GB (we have 22 GB)
5. UFW orphan 8084 removed; 8080 decision documented
6. CK + Beast mosquitto-clients version captured at preflight (P6 #14 -- catches matrix-collision before triggering no-op upgrades; banked from Phase C ESC #6 -> #7)

### A.5 -- Per-target-host preflight matrix (P6 #16, banked Phase D close-out 2026-04-29)

For phases that fan out across multiple hosts (e.g., D = node_exporter on 4 nodes), preflight enumeration on every target host is required, not just the primary. Required captures per target host:

| Capture | Why |
|---|---|
| **Firewall state** (active/inactive/missing) + rule count | Reveals UFW posture before phase relies on it (Goliath had UFW inactive; KaliPi has UFW not-installed -- both surfaced as Phase D deviations) |
| **Sudo policy** for working user (NOPASSWD vs interactive password) | Reveals whether PD can run sudo non-interactively or needs CEO handoff (KaliPi has interactive sudo by design as pentest host) |
| **Package-manager candidate version** of target package(s) | Reveals architecture/version skew + repo path differences (jammy/noble/kali-rolling all served prometheus-node-exporter at different versions in Phase D) |
| **Listener-port collision check** for any port the phase binds | Reveals existing services that would conflict |
| **Architecture compatibility** (x86_64 / aarch64 / etc.) | Reveals binary/build incompatibilities for compiled packages |
| **OS family + version** | Reveals systemd unit name conventions, apt repo path conventions, config layout differences |

**When a phase fans out across multiple hosts**, preflight enumeration on every host reveals operational policy heterogeneity BEFORE the phase tries to act on assumptions. Mid-phase escalation for state mismatches that preflight would have caught is process tax that compounds across builds.

**Banked from H1 Phase D Day 74**: directive's "mechanical scope" claim was correct for CK + Beast (NOPASSWD + UFW active) but incomplete for Goliath (UFW inactive) and KaliPi (sudo password required + UFW not installed), forcing mid-phase escalation (`paco_request_h1_phase_d_goliath_kalipi.md`) that preflight would have surfaced at Phase A. Resolution: Goliath A2-refined process-bind via ARGS + KaliPi same pattern via CEO handoff. Both pre-authorized in `paco_response_h1_phase_d_goliath_kalipi_paths.md` (commit `6266ba1`).

**Single-host phases** (H2 Cortez integration, H3 Pi3 DNS Gateway) capture single-host preflight only; the matrix template applies whenever a future spec phase touches multiple hosts.

### A.6 -- Upstream-product env var convention preflight (P6 #17, banked Phase E close-out 2026-04-29)

When a spec phase references upstream-product env vars (e.g., `GF_SECURITY_ADMIN_PASSWORD__FILE` for Grafana, `POSTGRES_PASSWORD_FILE` for Postgres, `MQTT_BROKER_*` for Mosquitto, etc.), cross-check the env var name against current upstream docs at directive-author time. Single-vs-double-underscore conventions, hyphen-vs-underscore in YAML keys, capitalization quirks, and trailing-colon syntax all silent-fail at runtime instead of raising parse errors. The fix at directive-write-time is one URL fetch; the fix at deploy-time costs at minimum one escalation roundtrip and at worst ships broken silently.

**Banked from H1 Phase E Day 74**: spec wrote `GF_SECURITY_ADMIN_PASSWORD_FILE` (single underscore + `_FILE`); Grafana 11.x canonical is `GF_SECURITY_ADMIN_PASSWORD__FILE` (double underscore + `__FILE`); single-underscore variant is silently ignored (Grafana parses as setting a non-existent config key `[security].admin_password_file`). PD's guardrail 5 reflex caught the discrepancy mid-write via auth-surface awareness, reverted to spec literal pre-deploy, escalated for Paco ruling. Paco approved Option A (amend at Phase E review time, single follow-up commit folded with Phase F) -- Correction 1 is this spec amendment; Correction 2 is the on-disk compose.yaml fix at `/home/jes/observability/compose.yaml` (md5 changed from `b40dd1ed...` to `db89319cad27c091ab1675f7035d7aa3`).

**Cross-reference**: `docs/paco_response_h1_phase_e_confirm_phase_f_go.md` (commit `dcd41ef`).

## 6. Phase B -- docker compose v2 plugin + docker group

**Goal:** enable `docker compose` (v2) and let `jes` use Docker without sudo.

```bash
sudo apt update
sudo apt install -y docker-compose-plugin
docker compose version  # confirm v2
sudo usermod -aG docker jes
# logout/login or `newgrp docker` to refresh shell membership
id jes  # confirm 'docker' group present
docker ps  # should NOT need sudo now
```

### B.1 -- Acceptance gates (4)

1. `docker compose version` returns Docker Compose v2.x
2. `id jes` shows `docker` group
3. `docker ps` works without sudo
4. No service-affecting changes elsewhere (Netdata still running, B2b/B1 anchors unchanged on Beast)

## 7. Phase C -- mosquitto 2.x install + listener config

**Goal:** close Day 67 YELLOW #5. Install via apt (NOT snap -- snap version had the listener-config bug). Configure 2 listeners.

### C.1 -- Install

```bash
sudo apt install -y mosquitto mosquitto-clients
sudo systemctl stop mosquitto  # we'll start after configuring
```

### C.2 -- Config

Write `/etc/mosquitto/mosquitto.conf`:

```
# /etc/mosquitto/mosquitto.conf -- Santigrey Homelab MQTT broker
# H1 Phase C, 2026-04-27 (per_listener_settings line added 2026-04-28 ESC #1 close)

# CRITICAL: mosquitto 2.0+ default auth-scoping changed (security directives apply
# globally with last-wins by default). per_listener_settings true restores v1.x-style
# per-listener auth semantics required by this dual-listener config.
# (Source: Phase C ESC #1, P6 #13 banked.)
per_listener_settings true

persistence true
persistence_location /var/lib/mosquitto/
log_dest file /var/log/mosquitto/mosquitto.log
log_type all

# Listener 1: localhost-only, anonymous (for existing mqtt-subscriber.service on CK via SSH tunnel or future loopback use)
listener 1883 127.0.0.1
allow_anonymous true

# Listener 2: LAN-bound, authed (per Day 67 IoT security spec)
listener 1884 192.168.1.40
allow_anonymous false
password_file /etc/mosquitto/passwd
acl_file /etc/mosquitto/acl
```

**NOTE on the original Day 67 spec:** that spec called for port 1883 LAN-bound + authed. This draft splits into 1883 (loopback, anon) for the simplest legacy compat AND 1884 (LAN, authed) for proper IoT integration. **CEO decision needed:** is the legacy `mqtt-subscriber.service` on CK actually using port 1883? If yes, this dual-listener works. If it's already designed for 1884, we go single-listener.

### C.3 -- Credentials

```bash
sudo mosquitto_passwd -c /etc/mosquitto/passwd alexandra
# CEO enters password interactively
sudo touch /etc/mosquitto/acl
# ACL contents per Day 67 spec (topic subscriptions per service)
sudo chmod 600 /etc/mosquitto/passwd /etc/mosquitto/acl
sudo chown mosquitto:mosquitto /etc/mosquitto/passwd /etc/mosquitto/acl
sudo systemctl enable --now mosquitto
sudo systemctl status mosquitto
```

### C.4 -- Smoke test

```bash
# Loopback anon
mosquitto_pub -h 127.0.0.1 -p 1883 -t test/loopback -m "hello-loopback"
mosquitto_sub -h 127.0.0.1 -p 1883 -t test/loopback -W 3

# LAN authed (from CK)
ssh jes@192.168.1.10 'mosquitto_pub -h 192.168.1.40 -p 1884 -u alexandra -P <pw> -t test/lan -m "hello-lan"'
```

### C.5 -- Acceptance gates (5)

1. mosquitto.service active + enabled
2. Port 1883 listening on 127.0.0.1 only
3. Port 1884 listening on 192.168.1.40 only
4. Loopback anonymous pub/sub round-trip works
5. LAN authed pub/sub from CK round-trip works

### C.6 -- Diagnostic preflight: broker-state hygiene (P6 #15, banked Phase C close-out)

If concurrent-CONNECT smoke tests fail from one source (e.g., CK) while passing from a
different source (e.g., Beast) AND single-connection tests pass from both -- BEFORE
deeper investigation, run `sudo systemctl restart mosquitto` on SlimJim and re-run the
failing smoke. Mosquitto 2.0.18 (and likely other MQTT brokers) accumulates per-source-IP
state from rapid failed CONNECT sequences that affects subsequent connection attempts
even after the failures stop. Restart clears in-memory state and discriminates "broker
remembers this client badly" from "actual concurrent-connection bug." Banked from Phase C
ESC #7 F.1 PASS (Day 73 / 2026-04-28).

## 8. Phase D -- node_exporter fan-out

**Goal:** install node_exporter on CK, Beast, Goliath, KaliPi as native systemd services on port 9100, LAN-bound only, listening only for SlimJim.

### D.1 -- Per-node install (apt-based on Ubuntu/Debian, manual binary on KaliPi if needed)

For each of CK, Beast, Goliath:
```bash
sudo apt install -y prometheus-node-exporter
sudo systemctl enable --now prometheus-node-exporter
# default config listens on :9100 all interfaces
ss -tln | grep 9100
```

For KaliPi (Kali rolling, may need different approach):
```bash
sudo apt install -y prometheus-node-exporter || (
  curl -L https://github.com/prometheus/node_exporter/releases/download/v1.8.2/node_exporter-1.8.2.linux-arm64.tar.gz -o /tmp/ne.tar.gz
  cd /tmp && tar xzf ne.tar.gz
  sudo install -m 755 node_exporter*/node_exporter /usr/local/bin/
  # write systemd unit, enable, start
)
```

### D.2 -- Per-node UFW rule

On each target node:
```bash
sudo ufw allow from 192.168.1.40 to any port 9100 proto tcp comment 'H1: node_exporter scrape from SlimJim'
```

**Note:** the rule is sourced from SlimJim's IP, not from the whole LAN. Defense in depth: only the Prometheus host can scrape the metrics.

### D.3 -- Verify from SlimJim

```bash
for ip in 192.168.1.10 192.168.1.20 192.168.1.152 192.168.1.254; do
  echo "--- $ip ---"
  curl -s --max-time 3 http://$ip:9100/metrics | head -5
done
```

Each target should return Prometheus-format metrics.

### D.4 -- Acceptance gates (3)

1. node_exporter active + enabled on all 4 target nodes
2. SlimJim can curl each target's :9100/metrics endpoint
3. UFW rule on each target only allows from 192.168.1.40

## 9. Phase E -- observability/ skeleton + compose + prometheus.yml + grafana provisioning

### E.1 -- Directory layout

```
/home/jes/observability/
  compose.yaml
  prometheus/
    prometheus.yml
  grafana/
    provisioning/
      datasources/datasource.yml
      dashboards/dashboard.yml
    dashboards/
      node-exporter-full.json    (Grafana dashboard 1860 export)
      prometheus-stats.json      (Grafana dashboard 3662 export)
  prom-data/        (volume, chmod 700)
  grafana-data/     (volume, chmod 700)
```

**Filesystem-prep (per P6 #18 broadened, banked Day 74 Phase G ESC #1 + #3):**

After creating the bind-mount targets above, align ownership to each container's runtime UID:

```bash
sudo chown -R 65534:65534 /home/jes/observability/prom-data
sudo chown -R 472:472 /home/jes/observability/grafana-data
sudo chown 472:472 /home/jes/observability/grafana-admin.pw  # secret file (mode 600 stays)
```

Why: Docker bind-mounts inherit host file ownership inside the container. Containers running as non-root UIDs (Prometheus=65534, Grafana=472) cannot read/write paths owned by host UID 1000 mode 700/600. Without this chown, first compose-up enters crash loop on `permission denied`. Compose v2 secrets long-syntax `uid`/`gid`/`mode` fields are swarm-only (P6 #19) -- chown the host file directly.

### E.2 -- compose.yaml (digest-pinned per B1 precedent)

```yaml
name: observability
services:
  prometheus:
    image: prom/prometheus:v2.55.1@sha256:<resolved-at-pull>
    container_name: obs-prometheus
    restart: unless-stopped
    ports:
      - "192.168.1.40:9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prom-data:/prometheus
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.path=/prometheus
      - --storage.tsdb.retention.time=30d
      - --storage.tsdb.retention.size=10GB
      - --web.enable-lifecycle
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s

  grafana:
    image: grafana/grafana:11.3.0@sha256:<resolved-at-pull>
    container_name: obs-grafana
    restart: unless-stopped
    ports:
      - "192.168.1.40:3000:3000"
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD__FILE: /run/secrets/grafana_admin_pw  # double underscore: Grafana 11.x file-provider convention (Correction 1, banked P6 #17 Phase E close 2026-04-29)
      GF_USERS_ALLOW_SIGN_UP: "false"
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
      - ./grafana-data:/var/lib/grafana
    secrets:
      - grafana_admin_pw
    depends_on:
      prometheus:
        condition: service_healthy

secrets:
  grafana_admin_pw:
    file: ./grafana-admin.pw
```

Grafana admin password lives in `/home/jes/observability/grafana-admin.pw` chmod 600 (CEO writes the literal password there).

### E.3 -- prometheus.yml

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: ['localhost:9090']

  - job_name: node
    static_configs:
      - targets:
          - '192.168.1.10:9100'   # CiscoKid
          - '192.168.1.20:9100'   # Goliath
          - '192.168.1.40:9100'   # SlimJim (will deploy on SlimJim too)
          - '192.168.1.152:9100'  # Beast
          - '192.168.1.254:9100'  # KaliPi
        labels:
          fleet: santigrey

  - job_name: netdata
    metrics_path: /api/v1/allmetrics
    params:
      format: ['prometheus']
    static_configs:
      - targets: ['192.168.1.40:19999']
        labels:
          fleet: santigrey
          source: netdata-slimjim
```

### E.4 -- node_exporter for SlimJim itself (within compose, OR separate apt install)

Deploy via apt on SlimJim too for consistency with the other 4 nodes (NOT in compose):

```bash
sudo apt install -y prometheus-node-exporter
sudo ufw allow from 127.0.0.1 to any port 9100  # local-only since Prom container scrapes it
```

(This decision keeps node_exporter management uniform across all 5 fleet nodes.)

### E.5 -- Grafana datasource provisioning

`grafana/provisioning/datasources/datasource.yml`:
```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

### E.6 -- Grafana dashboard provisioning

`grafana/provisioning/dashboards/dashboard.yml`:
```yaml
apiVersion: 1
providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    options:
      path: /var/lib/grafana/dashboards
```

Download dashboard 1860 (Node Exporter Full) and 3662 (Prometheus Stats) JSON exports into `grafana/dashboards/`.

**Note (banked Day 74 Phase H close-out):** Dashboard 3662 (Prometheus 2.0 Overview) renders all panels N/A under Grafana 11.x as of H1 ship. Root cause: deprecated `singlestat` panel + old variable query syntax; Grafana 11 auto-migration insufficient. P5 carryover for v0.2 replacement (3 candidates evaluated: 15489, 3681, hand-rolled minimal). See `docs/paco_review_h1_phase_h_grafana_smoke.md` + `docs/feedback_phase_closure_literal_vs_spirit.md`.

### E.7 -- Acceptance gates (4)

1. All directories created with correct ownership/perms
2. compose.yaml syntactically valid (`docker compose config` passes)
3. prometheus.yml syntactically valid (`promtool check config` if available)
4. grafana-admin.pw exists chmod 600

## 10. Phase F -- UFW for SlimJim

After mosquitto + node_exporter + (next phase) Prometheus/Grafana, add UFW rules:

```bash
sudo ufw allow from 192.168.1.0/24 to any port 9090 proto tcp comment 'H1: Prometheus LAN'
sudo ufw allow from 192.168.1.0/24 to any port 3000 proto tcp comment 'H1: Grafana LAN'
sudo ufw allow from 192.168.1.0/24 to any port 1884 proto tcp comment 'H1: Mosquitto LAN authed'
# 1883 stays loopback-only, no UFW rule needed
# 9100 already has implicit rule from local-only bind
sudo ufw status numbered
```

### F.1 -- Acceptance gates (3)

1. UFW count increased by exactly 3 new rules
2. No existing rules modified or removed
3. Pre-existing IoT DENY block preserved

## 11. Phase G -- compose up + healthcheck

```bash
cd /home/jes/observability
docker compose pull
docker compose up -d
# healthcheck poll cap 120s
for i in $(seq 1 24); do
  STATUS=$(docker inspect obs-prometheus --format '{{.State.Health.Status}}' 2>/dev/null || echo unknown)
  echo "poll $i/24: prometheus=$STATUS"
  [ "$STATUS" = "healthy" ] && break
  sleep 5
done
docker ps --filter name=obs- --format '{{.Names}} {{.Status}}'
```

**Bridge NAT for SlimJim self-scrapes (per Path 1 generalization, ratified Day 74 Phase G):**

When Prometheus runs in a Docker container with default bridge network and Prometheus scrapes a target on the same host (e.g., SlimJim's own node_exporter on `:9100` or netdata on `:19999`), the scrape arrives at the host's UFW from the bridge subnet (e.g., `172.18.0.0/16`), NOT from `127.0.0.1` or the LAN. UFW must explicitly allow the bridge subnet to reach those host-published ports.

Apply per-target on Phase G first-boot:

```bash
BRIDGE_SUBNET=$(docker network inspect observability_default --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}')
sudo ufw allow from $BRIDGE_SUBNET to any port 9100 proto tcp comment 'H1 Phase G: Prom container scrape via bridge NAT'
sudo ufw allow from $BRIDGE_SUBNET to any port 19999 proto tcp comment 'H1 Phase G: Prom container scrape via bridge NAT (netdata)'
```

PD self-auth applies for any future scrape target failing with bridge-NAT context-deadline-exceeded. Document each rule in close-out review per guardrail 4.

### G.1 -- Acceptance gates (4)

1. Both containers Up healthy within 120s
2. RestartCount=0 on both
3. SlimJim listeners include 192.168.1.40:9090 + 192.168.1.40:3000
4. B2b nanosecond-stable on Beast (anchor preserved through H1)

## 12. Phase H -- Grafana smoke + LAN smoke from CK

```bash
# From SlimJim
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
# Expected: 7 targets all 'up' (1 prom + 5 nodes + 1 netdata)

# From CK (LAN smoke)
ssh jes@192.168.1.10 'curl -sI http://192.168.1.40:9090/-/healthy'
ssh jes@192.168.1.10 'curl -sI http://192.168.1.40:3000/api/health'
```

### H.1 -- Acceptance gates (3)

1. All 7 Prometheus targets `up`
2. Grafana :3000 reachable from CK with 200 OK
3. Default dashboards loaded in Grafana UI (manual confirm via browser)

## 13. Phase I -- restart safety + ship report

### I.1 -- Restart safety

```bash
cd /home/jes/observability
docker compose restart
# poll healthy, capture POST_RESTART_STARTED
docker exec obs-prometheus wget -qO- http://localhost:9090/-/healthy
```

### I.2 -- Ship report at /home/jes/observability/H1_ship_report.md (mode 644)

17 sections per B1 precedent. Includes:
- Executive summary
- Architecture decision log (why both Netdata + Prometheus + Grafana)
- All 8 ratified Picks
- All 15 spec gates with command-output evidence
- Image digests (Prometheus + Grafana)
- File md5s (compose.yaml, prometheus.yml, mosquitto.conf, grafana provisioning)
- Service inventory (mosquitto + obs-prometheus + obs-grafana + 5 node_exporters)
- Restart safety result
- Spec deviations summary
- P5 carryovers (alertmanager, federation, long-term storage)
- P6 lessons banked
- Time elapsed
- Open follow-ups

### I.3 -- Acceptance gates (3 final)

1. Restart safety: containers healthy post-restart, all 7 scrape targets still `up`
2. Ship report at canonical path with all 17 sections, mode 644
3. CHECKLIST.md flipped from `[ ]` H1 to `[x]` H1 with audit banner

## 14. 15-gate scorecard summary

| # | Gate | Phase |
|---|---|---|
| 1 | Docker compose v2 installed | B |
| 2 | jes in docker group | B |
| 3 | Mosquitto active, dual listener (1883 lo, 1884 LAN) | C |
| 4 | MQTT loopback + LAN authed pub/sub round-trip | C |
| 5 | node_exporter on 4 remote nodes (CK, Beast, Goliath, KaliPi) | D |
| 6 | node_exporter on SlimJim (apt install) | E |
| 7 | UFW per-node :9100 ALLOW only from SlimJim | D |
| 8 | observability/ tree + compose.yaml valid | E |
| 9 | prometheus.yml has 5 node + 1 netdata + 1 self target | E |
| 10 | UFW SlimJim adds 3 rules (9090, 3000, 1884) | F |
| 11 | obs-prometheus + obs-grafana Up healthy | G |
| 12 | Prometheus reports 7 targets `up` | H |
| 13 | Grafana reachable from CK; default dashboards loaded | H |
| 14 | Restart safety: containers + targets resume cleanly | I |
| 15 | B2b bit-identical preserved across all H1 phases | every |

## 15. P5 carryovers (post-H1)

- alertmanager + alert rules (gated on Atlas being able to route alerts)
- Prometheus federation (if fleet grows)
- Long-term storage (Thanos / Cortex / VictoriaMetrics)
- Loki for log aggregation
- Grafana SSO via Tailscale identity
- Dashboard for Garage S3 metrics (custom exporter, gated on B1 maturity)
- Dashboard for Postgres + B2b replication lag (postgres_exporter, dedicated mini-spec)

## 16. Open questions for CEO before PD execution

1. **Port 8080 on SlimJim** has a python3 listener. What is it? Keep, archive, or remove? (Phase A.2)
2. **Mosquitto listener strategy:** dual (1883 lo + 1884 LAN, my draft) OR single LAN-authed at 1883 (Day 67 original spec)? Difference matters for legacy `mqtt-subscriber.service` on CK.
3. **node_exporter on KaliPi**: Kali rolling repos may not have `prometheus-node-exporter`. If apt fails, fall back to manual binary install -- approved or do you want a different approach?
4. **Grafana admin password**: stored at `/home/jes/observability/grafana-admin.pw` chmod 600 on SlimJim. CEO sets it. OK?

---

**Spec ready for ratification.** PD does not start until CEO replies on the 4 open questions and confirms the 9-phase outline + 10 Picks.
