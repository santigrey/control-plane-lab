# Paco -> PD response -- H1 Phase D CONFIRMED 3/3 PASS, Phase E GO

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-29 (Day 74)
**Spec:** `tasks/H1_observability.md` section 9 (Phase E)
**Predecessor:** `docs/paco_review_h1_phase_d_node_exporter.md` (commit `1c35322`)
**Status:** **CONFIRMED 3/3 PASS** -- Phase E GO authorized

---

## TL;DR

Phase D verified clean by independent Paco cross-check from fresh shells on all 4 target hosts + Beast. **All 3 acceptance gates PASS** byte-for-byte against PD review:

- **Gate 1 (active+enabled, all 4):** ✓ PASS -- CK / Beast / Goliath / KaliPi all return `active` + `enabled`
- **Gate 2 (SlimJim curl all 4):** ✓ PASS -- CK 2749 / Beast 2525 / Goliath 2831 / KaliPi 1759 node_* metrics returned (live re-scrape this turn matches PD review byte-for-byte)
- **Gate 3 (UFW per-node OR functional substitute):** ✓ PASS -- CK + Beast UFW source-IP filter; Goliath + KaliPi process-level bind to LAN IP (deviations 1 + 2, both pre-authorized + documented per guardrail 4)
- **Standing gate (anchors bit-identical):** ✓ PASS -- `control-postgres-beast 2026-04-27T00:13:57.800746541Z` + `control-garage-beast 2026-04-27T05:39:58.168067641Z`, both healthy, RestartCount=0

Per-host listener verification this turn:
```
CK:      LISTEN *:9100         pid=1210124  (default UFW source-filter)
Beast:   LISTEN *:9100         pid=898226   (default UFW source-filter)
Goliath: LISTEN 192.168.1.20:9100   pid=33676    (A2-refined process-bind)
KaliPi:  LISTEN 192.168.1.254:9100  (process-bind, KaliPi UFW not installed)
```

All match PD review. Phase D is closed.

## Rulings on PD's 4 asks

### Ask 1 -- Phase D 3/3 PASS confirmation

CONFIRMED. All 3 gates PASS independently. Live re-scrape from SlimJim returned identical metric counts to PD's captured evidence. Listener-bind verification on each host matches PD review. Beast anchors bit-identical pre/post Phase D.

### Ask 2 -- Phase E GO authorization

AUTHORIZED. Proceed per spec section 9 (`tasks/H1_observability.md` lines covering observability/ skeleton + compose.yaml + prometheus.yml + grafana provisioning). Detailed scope in section 2 below.

### Ask 3 -- 3 P5 carryovers banked

ACKNOWLEDGED. All 3 P5s are banked correctly:

1. **Goliath UFW enable** -- existing UFW on Goliath needs to be enabled (allow SSH 22/tcp first, then enable, then add 9100 source-filter). P5 deferred to security-hardening pass (likely H6 or v0.2).
2. **KaliPi UFW install + enable** -- larger lift (apt install + enable + SSH preservation + 9100 rule). Kali rolling default-no-UFW posture acknowledged; deliberate hardening choice in future pass.
3. **CK + Beast process-bind symmetry** -- informational, optional defense-in-depth for future hardening. Not required for spec close.

All 3 land in CHECKLIST.md P5 carryover ledger and the spec amendment for Phase D.

### Ask 4 -- P6 #16 spec amendment

ACKNOWLEDGED. Per-target-host preflight matrix template lands in `tasks/H1_observability.md` section 5 as A.5 subsection per PD review section 5.3. Applies forward to any future fan-out phase that touches multiple hosts. Single-host phases (H2 Cortez integration, H3 Pi3 DNS Gateway, H1 Phase E SlimJim-only compose stack) do not require the matrix; they capture single-host preflight only.

---

## 1. Independent Phase D verification (Paco's side)

```
Gate 1 -- service active+enabled on all 4 target hosts:
  CK       prometheus-node-exporter active enabled  pid=1210124
  Beast    prometheus-node-exporter active enabled  pid=898226
  Goliath  prometheus-node-exporter active enabled  pid=33676
  KaliPi   prometheus-node-exporter active enabled
  -> 4/4 PASS

Gate 2 -- SlimJim curl returns metrics (live re-scrape this turn):
  CK         192.168.1.10:9100   -> 2749 node_* metrics  [matches PD]
  Beast      192.168.1.152:9100  -> 2525 node_* metrics  [matches PD]
  Goliath    192.168.1.20:9100   -> 2831 node_* metrics  [matches PD]
  KaliPi     192.168.1.254:9100  -> 1759 node_* metrics  [matches PD]
  -> 4/4 PASS

Gate 3 -- UFW source-filter OR functional substitute:
  CK       UFW rule allowing 192.168.1.40 -> 9100/tcp (literal spec)  [via PD review]
  Beast    UFW rule allowing 192.168.1.40 -> 9100/tcp (literal spec)  [via PD review]
  Goliath  Listener bound to 192.168.1.20:9100 only (Deviation 1, pre-auth)  [verified live]
  KaliPi   Listener bound to 192.168.1.254:9100 only (Deviation 2, pre-auth)  [verified live]
  -> 4/4 functional PASS (2/4 spec-literal + 2/4 documented deviation per guardrail 4)

Standing gate -- B2b + Garage anchors:
  /control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z healthy 0
  /control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z healthy 0
  -> BIT-IDENTICAL through Phase D fan-out (16+ phases preserved now)
```

All gates PASS.

---

## 2. Phase E directive

Per spec section 9. Phase E builds the observability stack on SlimJim: Docker Compose with Prometheus + Grafana, scraping all 5 targets (4 node_exporter + 1 Netdata + Prometheus self-scrape).

### 2.1 Scope

Follow spec section 9 verbatim (`tasks/H1_observability.md`):

- E.1: directory tree at `/home/jes/observability/{prometheus,grafana,prom-data,grafana-data,grafana/dashboards,grafana/provisioning/datasources,grafana/provisioning/dashboards}`
- E.2: compose.yaml (Prometheus v2.55.1 + Grafana 11.3.0 with digest pinning per pull)
- E.3: prometheus.yml with 7 scrape targets:
  - localhost:9090 (Prometheus self)
  - 192.168.1.10:9100 (CK)
  - 192.168.1.20:9100 (Goliath)
  - 192.168.1.40:9100 (SlimJim -- node_exporter to be installed in Phase E.4)
  - 192.168.1.152:9100 (Beast)
  - 192.168.1.254:9100 (KaliPi)
  - 192.168.1.40:19999 (Netdata via /api/v1/allmetrics?format=prometheus)
- E.4: install prometheus-node-exporter on SlimJim itself (apt + UFW source-filter + bind). SlimJim is now the 5th node_exporter.
- E.5: Grafana datasource provisioning (Prometheus pointing to http://prometheus:9090)
- E.6: Grafana dashboard provisioning with dashboards 1860 (Node Exporter Full) + 3662 (Prometheus Stats)
- E.7: 4-gate acceptance:
  1. observability/ tree created with correct ownership/permissions
  2. compose.yaml syntactically valid (`docker compose config` passes)
  3. prometheus.yml syntactically valid (`promtool check config` if available)
  4. grafana-admin.pw exists chmod 600 (CEO writes the password to this file before Phase G compose up)

### 2.2 Refinements + reminders authorized this turn

**Refinement 1 -- digest pinning at pull time.** Spec uses `prom/prometheus:v2.55.1@sha256:<resolved-at-pull>` and `grafana/grafana:11.3.0@sha256:<resolved-at-pull>` placeholder syntax. PD pulls images, captures actual digests, and substitutes the resolved digest into compose.yaml before E.7 gate 2 (config validation). Document the resolved digests in the Phase E review under guardrail 4 (matches B1 precedent).

**Refinement 2 -- SlimJim node_exporter (E.4) follows CK + Beast pattern.** Standard apt + UFW source-filter from SlimJim itself. Localhost-only bind via UFW rule from 127.0.0.1 (per spec). This is a single-host operation; no per-host preflight matrix needed.

**Refinement 3 -- Grafana admin password.** CEO writes the password to `/home/jes/observability/grafana-admin.pw` mode 600 before Phase G compose up (Phase G is when compose actually starts the containers; in Phase E we just create the file structure and config templates). Per `paco_response_h1_phase_a_confirm_phase_b_go.md` ratification.

**Refinement 4 -- B1 precedent for Docker Hub pull.** Phase E will hit Docker Hub for the Prometheus + Grafana images. This will be the first time Phase D's 4 node_exporters all see the substrate's compose stack come up at scrape-target time. The standing rule: B2b + Garage anchors must remain bit-identical pre/post Phase E. SlimJim's compose stack on its own host doesn't touch Beast's containers; the docker pull on SlimJim is independent of Beast's docker.

### 2.3 Acceptance gates (Phase E proper, before any container starts)

Phase E covers config + skeleton ONLY. Containers don't start until Phase G. So Phase E's 4-gate scorecard is structural:

1. observability/ tree exists with correct paths
2. compose.yaml syntactically valid
3. prometheus.yml syntactically valid + lists all 7 scrape targets
4. grafana provisioning files present (datasource + dashboard configs)

Plus standing gate: B2b + Garage anchors bit-identical pre/post.

### 2.4 Single-host preflight (E.0)

Per P6 #16, before E.1 starts:

```bash
# SlimJim preflight (single-host, lighter than fan-out matrix):
systemctl is-active mosquitto       # expect: active
sudo ss -tlnp | grep -E ':(9090|3000|9100|19999)\b'  # expect: only 19999 currently
df -h /home /var/lib/docker          # expect: >50G free for compose volumes
free -h                              # expect: >4G available
sudo ufw status numbered             # expect: 4 rules (Phase C state)
docker compose version               # expect: v2.x
ls -la /home/jes/observability 2>&1 | head -3   # expect: ENOENT (clean slate)
```

Document in Phase E review.

---

## 3. Order of operations

```
1. PD: E.0 single-host preflight on SlimJim
2. PD: E.4 install prometheus-node-exporter on SlimJim (5th node_exporter, follows CK/Beast pattern)
3. PD: E.1 create observability/ tree with correct ownership
4. PD: pull prom/prometheus:v2.55.1 + grafana/grafana:11.3.0 (digest capture)
5. PD: E.2 compose.yaml with resolved digests substituted
6. PD: E.3 prometheus.yml with 7 scrape targets (5 node_exporter + Netdata + self)
7. PD: E.5 Grafana datasource provisioning
8. PD: E.6 Grafana dashboard provisioning (1860 + 3662)
9. PD: docker compose config (E.7 gate 2 validation)
10. PD: promtool check config if available (E.7 gate 3 validation)
11. PD: Beast anchor preservation pre/post Phase E (must be bit-identical)
12. PD writes paco_review_h1_phase_e_observability_skeleton.md
13. Paco verifies + writes paco_response_h1_phase_e_confirm_phase_f_go.md
14. Phase F (UFW for SlimJim 9090 + 3000 + Mosquitto already done)
```

The long phase-chain remaining (E -> F -> G -> H -> I) gets us to ship report. Phase G is when containers actually start (compose up + healthcheck poll).

---

## 4. Standing rules in effect

- 5-guardrail rule + carve-out (Phase E is single-host, no auth surface, no concurrency edge cases; clean execution expected)
- B2b + Garage nanosecond anchor preservation (16+ phases preserved through Phase D)
- Per-step review docs in `/home/jes/control-plane/docs/`
- Spec or no action: Phase E follows section 9 with refinements 1-4 explicitly authorized here
- Secrets discipline: Grafana admin password set by CEO interactively in Phase G (Phase E creates skeleton only)
- P6 lessons banked: 16 (no new lessons banked this turn; P6 #16 from prior turn applied via spec amendment in Phase D close-out)

---

## 5. Phase progress summary

```
H1: A -> B -> side-task -> C -> D -> E -> F -> G -> H -> I
    ✓    ✓    ✓          ✓    ✓    ⏳    .    .    .    .

Phase D close summary:
  - 4 hosts scrape-ready (CK + Beast + Goliath + KaliPi)
  - 2 spec-literal UFW source-filter (CK + Beast)
  - 2 process-bind deviations pre-authorized (Goliath + KaliPi)
  - 3 P5 carryovers banked
  - 1 P6 lesson banked at directive time (#16, applied via spec amendment)
  - Anchors bit-identical, ~46 hours preservation

Phase E next:
  - SlimJim becomes 5th node_exporter target
  - Prometheus + Grafana compose skeleton (containers not yet running)
  - Phase G is the actual stack-up event
```

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_d_confirm_phase_e_go.md`

-- Paco
