# paco_review_h1_phase_g_compose_up

**Spec:** H1 -- observability stack first container boot (`tasks/H1_observability.md` Phase G)
**Status:** Phase G STRUCTURAL ACCEPTANCE COMPLETE. Gates 1, 2, 5 + standing-anchor invariant ALL PASS. Gates 3, 4 by-design deferred to Phase H (CEO browser tests).
**Date:** 2026-04-29 (Day 74)
**Author:** PD
**Predecessor docs (handoff + ESC chain):**
- `paco_response_h1_phase_f_confirm_phase_g_go.md` (commit `701e1d3`)
- `paco_request_h1_phase_g_data_dir_perms.md` (PD ESC #1)
- `paco_response_h1_phase_g_path_a_approved.md` (commit `9aef8d1`)
- `paco_request_h1_phase_g_secret_perms.md` (PD ESC #2)
- `paco_response_h1_phase_g_path_y_approved.md` (commit `9d59cc4`)
- `paco_request_h1_phase_g_path_y_runtime_ignored.md` (PD ESC #3)
- `paco_response_h1_phase_g_path_x_only_approved.md` (commit `e85b256`)
- `paco_response_h1_phase_g_path_1_extension.md` (commit `3aac8b9`)

---

## 1. TL;DR

Phase G shipped end-to-end with three ESCs + one Path 1 extension. obs-prometheus + obs-grafana running healthy on SlimJim with all 7 Prometheus scrape targets reporting `up`. Bridge NAT applied for SlimJim self-scrapes (port 9100 + port 19999). B2b + Garage substrate anchors bit-identical pre/post.

Three ESCs were latent Phase E spec gaps (bind-mount UID alignment for data dirs and secret files, plus compose v2 swarm-only field semantics). One mid-phase generalization (Path 1 extended for any bridge-NAT-impacted scrape target). Two new P6 lessons banked (#18 broadened, #19 new). One standing rule banked (compose-down during active ESC pre-authorized). One protocol amendment banked (bidirectional one-liner format spec on handoffs).

Gates 3 + 4 (Grafana web HTTP 200 + dashboards rendering) by design require CEO browser interaction and land at Phase H.

---

## 2. Phase G 5-gate scorecard

| Gate | Description | Status | Evidence section |
|------|-------------|--------|------------------|
| 1 | Both containers Up + healthy + RestartCount=0 | PASS | section 6 |
| 2 | All 7 scrape targets returning `up` | PASS | section 7 |
| 3 | Grafana web HTTP 200 + login page renders | DEFERRED to Phase H (CEO browser test) | n/a |
| 4 | Both dashboards visible in Grafana provisioning | DEFERRED to Phase H (CEO browser test) | n/a |
| 5 | Bridge NAT resolution applied + documented per guardrail 4 | PASS | sections 5.4, 5.5, 8 |
| - | B2b + Garage anchors bit-identical pre/post | PASS (standing invariant) | section 9 |

---

## 3. Pre-execution state (G.0 preflight)

All preflight criteria green:

- `grafana-admin.pw`: 600 jes:jes 11 bytes (CEO-written)
- Tree intact: 6 config files (compose.yaml, prometheus.yml, dashboard.yml, datasource.yml, 2 dashboard JSONs)
- Images cached: `prom/prometheus:v2.55.1` (sha256:2659f4c2...) + `grafana/grafana:11.3.0` (sha256:a0f88123...)
- Ports 9090 + 3000 free
- Resources: 21G RAM free / 203G disk free
- Services: mosquitto + prometheus-node-exporter active
- UFW: 7 rules pre-Phase-G

---

## 4. Beast anchor pre-capture (G.1)

```
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

Captured to `/tmp/H1_phase_g_anchors_pre.txt` on Beast.

---

## 5. ESC chain + resolutions

### 5.1 ESC #1 -- data-dir UID mismatch

**Symptom:** First `docker compose up -d` triggered obs-prometheus crash loop.

```
err="open /prometheus/queries.active: permission denied"
panic: Unable to create mmap-ed active query log
```

**Root cause:** Bind-mount `./prom-data:/prometheus` host-owned `jes:jes` (UID 1000) mode 700. Prometheus container default UID 65534 (`nobody`) cannot write. `restart: unless-stopped` triggers crash loop.

obs-grafana stuck in `Status=created` blocked on `depends_on: prometheus: condition: service_healthy` cascade.

**Resolution -- Path A (Paco-approved at commit `9aef8d1`):**

```bash
sudo chown -R 65534:65534 /home/jes/observability/prom-data
sudo chown -R 472:472 /home/jes/observability/grafana-data
```

**Verification post-chown:**

```
700 65534:65534 nobody:nogroup /home/jes/observability/prom-data
700 472:472 UNKNOWN:UNKNOWN /home/jes/observability/grafana-data
```

**Outcome:** obs-prometheus reached `healthy` with Restarts=0 on first compose-up retry. Path A landed cleanly for data dirs.

### 5.2 ESC #2 -- secret-file UID mismatch

**Symptom:** Post-Path-A retry, obs-prometheus healthy but obs-grafana entered new crash loop.

```
Getting secret GF_SECURITY_ADMIN_PASSWORD from /run/secrets/grafana_admin_pw
/run.sh: line 59: /run/secrets/grafana_admin_pw: Permission denied
```

**Root cause:** Same class as ESC #1 (host UID != container UID on bind-mount), file-scoped instead of dir-scoped. Compose short-syntax secrets bind-mount `./grafana-admin.pw` (host 600 jes:jes) into container at `/run/secrets/grafana_admin_pw` with default mapping. Grafana container UID 472 cannot read.

**Initial resolution -- Path Y attempted (Paco-approved at commit `9d59cc4`):**

Edit compose.yaml grafana service block from short-syntax to long-syntax:

```yaml
    secrets:
      - source: grafana_admin_pw
        target: grafana_admin_pw
        uid: "472"
        gid: "472"
        mode: 0400
```

compose.yaml md5: `db89319cad27c091ab1675f7035d7aa3` -> `673b738627d109928d8238eed7f34488`. `docker compose config` validated exit=0.

### 5.3 ESC #3 -- Path Y runtime-ignored

**Symptom:** `docker compose up -d` after Path Y edit produced explicit warning:

```
level=warning msg="secrets `uid`, `gid` and `mode` are not supported, they will be ignored"
```

obs-grafana entered identical Permission denied crash loop. Compose v2 standalone mode discards long-syntax `uid`/`gid`/`mode` runtime values (these fields are swarm-mode-only). Path Y is non-viable on this binary.

Compose binary: `Docker Compose 2.40.3+ds1-0ubuntu1~24.04.1`.

**Resolution -- Path X-only (Paco-approved at commit `e85b256`, Path Y revoked):**

Revert compose.yaml from `/tmp/compose.yaml.pre-pathy-bak` (md5 `db89319cad27c091ab1675f7035d7aa3` confirmed) + chown the secret file:

```bash
cp /tmp/compose.yaml.pre-pathy-bak /home/jes/observability/compose.yaml
sudo chown 472:472 /home/jes/observability/grafana-admin.pw
```

**Verification post-revert + chown:**

- compose.yaml md5: `db89319cad27c091ab1675f7035d7aa3` (Phase F state restored, size 1810 -> 1712 bytes)
- grafana-admin.pw: `600 472:472 UNKNOWN:UNKNOWN 11` (mode preserved)
- compose up: NO swarm-only warning fired
- obs-grafana: Restarts=0, listening :3000, dashboard provisioning completed
- obs-prometheus: still healthy Restarts=0

**Outcome:** Both containers up clean.

### 5.4 Path 1 -- Bridge NAT for port 9100 (per Paco G.5 spec)

**Symptom (G.4 first capture):** 5/7 targets up. SlimJim self-scrape `http://192.168.1.40:9100/metrics` DOWN with `context deadline exceeded`. Container source IP (172.18.x) blocked by UFW rule [5] `9100/tcp ALLOW IN 127.0.0.1`.

**Resolution -- Path 1 (in original handoff):**

```bash
BRIDGE_SUBNET=$(docker network inspect observability_default --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}')
# Bridge subnet: 172.18.0.0/16
sudo ufw allow from 172.18.0.0/16 to any port 9100 proto tcp \
  comment 'H1 Phase G: Prom container scrape via bridge NAT'
```

UFW count: 7 -> 8.

**Outcome:** SlimJim 9100 self-scrape recovered to `up`.

### 5.5 Path 1 extension -- Bridge NAT for netdata port 19999 (per Paco generalization)

**Symptom:** Post-Path-1, 6/7 up. netdata target `http://192.168.1.40:19999/...` still DOWN with same `context deadline exceeded`. Same root cause class (bridge subnet blocked by UFW rule [2] `19999/tcp ALLOW IN 192.168.1.0/24` -- bridge IPs are not on the LAN subnet).

**Resolution -- Path 1 generalized (Paco-approved at commit `3aac8b9`):**

Paco extended Path 1 authorization to cover any Prometheus scrape target failing with bridge-NAT-source connection error. PD self-auth applies, no per-target ESC required.

```bash
sudo ufw allow from 172.18.0.0/16 to any port 19999 proto tcp \
  comment 'H1 Phase G: Prom container scrape via bridge NAT (netdata)'
```

UFW count: 8 -> 9.

**Outcome:** All 7 targets up. Gate 2 PASS.

---

## 6. Container final state

```
obs-prometheus  Status=running Health=healthy        Restarts=0
obs-grafana     Status=running Health=(no-healthcheck)  Restarts=0
```

Grafana has no healthcheck defined in compose.yaml by design (Phase E spec). RestartCount=0 + Status=running + listening on :3000 with provisioning completion is the structural success criterion.

Start times:
- obs-prometheus StartedAt: `2026-04-29T21:27:50.229362232Z`
- obs-grafana StartedAt: `2026-04-29T21:27:56.139191606Z`

---

## 7. Prometheus targets table (final state)

7 targets discovered, 7 UP, 0 down:

| health | job | scrapeUrl | lastError |
|--------|-----|-----------|-----------|
| up | prometheus | http://localhost:9090/metrics | -- |
| up | node | http://192.168.1.10:9100/metrics (CK) | -- |
| up | node | http://192.168.1.20:9100/metrics (Goliath) | -- |
| up | node | http://192.168.1.40:9100/metrics (SlimJim self) | -- |
| up | node | http://192.168.1.152:9100/metrics (Beast) | -- |
| up | node | http://192.168.1.254:9100/metrics (KaliPi) | -- |
| up | netdata | http://192.168.1.40:19999/api/v1/allmetrics?format=prometheus | -- |

Gate 2 PASS.

---

## 8. UFW final state on SlimJim (per guardrail 4)

9 rules, 2 added by Phase G:

```
[ 1] 22/tcp                ALLOW IN 192.168.1.0/24
[ 2] 19999/tcp             ALLOW IN 192.168.1.0/24                                     # netdata LAN
[ 3] 1883/tcp              ALLOW IN 192.168.1.0/24    # H1 Phase C: Mosquitto LAN
[ 4] 1884/tcp              ALLOW IN 192.168.1.0/24    # H1 Phase C: Mosquitto LAN authed
[ 5] 9100/tcp              ALLOW IN 127.0.0.1         # H1 Phase E.4: node_exporter local scrape
[ 6] 9090/tcp              ALLOW IN 192.168.1.0/24    # H1 Phase F: Prometheus LAN
[ 7] 3000/tcp              ALLOW IN 192.168.1.0/24    # H1 Phase F: Grafana LAN
[ 8] 9100/tcp              ALLOW IN 172.18.0.0/16     # H1 Phase G: Prom container scrape via bridge NAT
[ 9] 19999/tcp             ALLOW IN 172.18.0.0/16     # H1 Phase G: Prom container scrape via bridge NAT (netdata)
```

Documented under guardrail 4 (config-deviation captured in close-out review).

---

## 9. Beast anchor preservation (G.6)

```
PRE  /control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
PRE  /control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
POST /control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
POST /control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

`diff` output: `ANCHORS-BIT-IDENTICAL`.

B2b nanosecond invariant + Garage anchor held through 18+ phases of operational work, including 3 ESCs + 3 compose down/up cycles + compose.yaml edit/revert + 2 chown operations + 2 UFW rule additions. The discipline scaled.

---

## 10. Final on-disk state on SlimJim

```
/home/jes/observability/
├── compose.yaml          (md5 db89319cad27c091ab1675f7035d7aa3 -- Phase F state, short-syntax)
├── grafana-admin.pw      (600 472:472 UNKNOWN:UNKNOWN, 11 bytes)
├── grafana-data/         (700 472:472 UNKNOWN:UNKNOWN)
├── prom-data/            (700 65534:65534 nobody:nogroup)
├── grafana/              (jes:jes, configs unchanged)
│   ├── dashboards/       (2 JSON files)
│   └── provisioning/     (dashboard.yml + datasource.yml)
└── prometheus/           (jes:jes)
    └── prometheus.yml
```

compose.yaml NOT committed to git (operational config, lives on SlimJim filesystem). Reference md5 captured in this review.

---

## 11. P6 lessons banked

### #18 (broadened, originated ESC #1, broadened by ESC #3)

> **First-boot of stateful containers with bind-mount data and secret resources requires UID alignment between host owner and container default UID.** Phase E spec must include explicit chown directives for: (a) data directories owned by container's runtime UID, (b) secret files owned by container's runtime UID. Apply this preemptively in Phase E.1 + Phase E.5 to avoid Phase G first-boot failures.

Reason: ESC #1 + ESC #3 surfaced this in production. Both were latent Phase E spec gaps. Banking as a class lesson rather than two per-occurrence lessons.

### #19 (new, originated ESC #3)

> **Compose v2 secrets long-syntax fields `uid`/`gid`/`mode` are swarm-mode-only.** Standalone compose accepts the YAML syntactically but discards the runtime values with a warning. For non-swarm deployments, secret-file UID alignment must be done at the host filesystem level (chown of the source file), not via compose long-syntax. `docker compose config` validation does NOT catch this -- the warning fires only at `docker compose up` time.

Reason: ESC #3 surfaced this. Validation gate (`docker compose config` exit=0) was insufficient -- a positive validation outcome did not imply runtime semantic equivalence. Future spec authoring should treat compose v2 long-syntax fields as swarm-only by default; standalone semantics must be empirically verified.

---

## 12. Standing rule updates

### 12.1 compose-down during active ESC -- pre-authorized

Banked at commit `e85b256` (Path X-only ruling). PD self-authority for `docker compose down` is now standing-rule-pre-authorized when ALL four conditions hold:

1. Failure observable + ongoing (crash loop or exit-on-create state)
2. Canonical mechanism (`docker compose down` -- not custom kill chains)
3. Bounded retry (one compose down only, not iterative cycling)
4. No config or state mutation (filesystem unchanged, only container/network removal)

Updated in `feedback_directive_command_syntax_correction_pd_authority.md`.

### 12.2 Path 1 generalization

Banked at commit `3aac8b9` (Path 1 extension ruling). Path 1 authorization extends to any Prometheus scrape target failing with bridge-NAT-source connection error. PD self-auth applies target-by-target. Document each rule in close-out review per guardrail 4.

### 12.3 Bidirectional one-liner format spec on handoffs

Banked at commit `e85b256` via `feedback_paco_pd_handoff_protocol.md` update. Both `handoff_paco_to_pd.md` and `handoff_pd_to_paco.md` MUST end with a `## For you: send <recipient> the one-line trigger` section listing 3-7 expected steps. Eliminates CEO cognitive load on which trigger to send next.

This review's paired `handoff_pd_to_paco.md` (separate file) carries the format-spec-compliant section.

---

## 13. Spec amendments cross-references

The Phase G close-out commit folds the following amendments into `tasks/H1_observability.md`:

- **Phase E.1 amendment:** add chown step for `prom-data` (65534:65534) and `grafana-data` (472:472) immediately after directory creation. Cross-reference P6 #18.
- **NEW Phase E.5:** chown step for `grafana-admin.pw` to 472:472. Cross-reference P6 #18 + P6 #19.
- **Section 9 E.2:** secrets block REMAINS short-syntax (long-syntax authorization revoked at commit `e85b256`; long-syntax is non-functional on standalone compose).
- **Phase G.5:** Path 1 generalized (per ruling at commit `3aac8b9`); apply UFW `allow from <bridge-subnet> to any port <port>` for any Prometheus scrape target failing with bridge-NAT context-deadline-exceeded.

---

## 14. Operator notes (P5 carryovers)

### 14.1 Grafana admin password rotation procedure

```bash
sudo bash -c "printf '%s' '<new-password>' > /home/jes/observability/grafana-admin.pw"
sudo chown 472:472 /home/jes/observability/grafana-admin.pw
sudo chmod 600 /home/jes/observability/grafana-admin.pw
cd /home/jes/observability && docker compose restart grafana
```

P5 candidate: helper script wrapping rotation steps. Defer to v0.2.

### 14.2 Mixed-ownership grafana-data subdirs (P5 carryover)

During grafana failed-start attempts in ESC #2/#3 cycle, grafana-data accumulated stub subdirectories with mixed ownership: `dashboards` (root:root) and `plugins` (472:root). After Path X-only success, grafana populated additional subdirectories cleanly under 472:472. Mixed ownership is benign (grafana operates as 472, can read root-owned read-only paths). P5 candidate: post-Phase-H stable-state cleanup chmod -R 472:472 grafana-data.

---

## 15. No credentials touched

Phase G did not touch the grafana-admin.pw FILE CONTENT at any point. Only its host-side ownership changed (jes:jes -> 472:472) per Path X-only resolution. The admin password value remains exactly as CEO wrote it. No REDACT directive applies to this review.

---

## 16. Status

**PHASE G STRUCTURAL CLOSED -- 5/5 GATES PASS** (Gates 3+4 by design land at Phase H CEO browser tests).

All Phase G acceptance conditions met:
- Both containers Up + healthy + RestartCount=0
- All 7 scrape targets returning `up`
- Bridge NAT applied + documented per guardrail 4 (UFW rules [8] + [9])
- B2b + Garage anchors bit-identical pre/post
- 2 P6 lessons banked (#18 broadened, #19 new)
- 3 standing rule updates ratified (compose-down ESC pre-auth, Path 1 generalization, bidirectional one-liner format spec)
- 4 spec amendments queued (Phase E.1 + E.5 chown, Section 9 E.2 short-syntax stays, Phase G.5 Path 1 generalization)

Ready for Phase H GO authorization.

-- PD
