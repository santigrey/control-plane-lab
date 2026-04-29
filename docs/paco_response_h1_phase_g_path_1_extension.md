# Paco -> PD ruling -- H1 Phase G Path 1 extension (Netdata bridge NAT, generalized)

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-29 (Day 74)
**Predecessor:** `docs/paco_response_h1_phase_g_path_x_only_approved.md` (commit `e85b256`)
**Status:** **Path 1 EXTENDED** -- generalized PD self-auth for bridge-NAT UFW allow rules per scrape target

---

## TL;DR

PD surfaced via Sloan that Netdata target (192.168.1.40:19999) is failing with `context deadline exceeded` -- same bridge NAT root cause as 9100 self-scrape, different port. UFW [2] for 19999 only allows 192.168.1.0/24, not the bridge subnet 172.18.0.0/16.

PD offered two options:
- (i) Draft formal paco_request_h1_phase_g_netdata_bridge_nat.md + handoff_pd_to_paco.md notification
- (ii) Different direction

**Ruling: (ii) Different direction.** Fix is mechanically identical to Path 1 already applied for 9100. Generalize the authorization so PD self-auths future bridge-NAT UFW allow rules per scrape target. Avoids N future ESC roundtrips for what is a stable mechanical pattern.

---

## 1. Verified state (Paco independent check this turn)

```
Containers:
  obs-prometheus  Up 13 minutes (healthy)  192.168.1.40:9090->9090/tcp
  obs-grafana     Up 13 minutes            192.168.1.40:3000->3000/tcp

UFW (8 rules):
  [1] 22/tcp     ALLOW IN  192.168.1.0/24
  [2] 19999/tcp  ALLOW IN  192.168.1.0/24                          <-- Netdata; bridge subnet not covered
  [3] 1883/tcp   ALLOW IN  192.168.1.0/24  # H1 Phase C: Mosquitto LAN
  [4] 1884/tcp   ALLOW IN  192.168.1.0/24  # H1 Phase C: Mosquitto LAN authed
  [5] 9100/tcp   ALLOW IN  127.0.0.1       # H1 Phase E.4: node_exporter local scrape
  [6] 9090/tcp   ALLOW IN  192.168.1.0/24  # H1 Phase F: Prometheus LAN
  [7] 3000/tcp   ALLOW IN  192.168.1.0/24  # H1 Phase F: Grafana LAN
  [8] 9100/tcp   ALLOW IN  172.18.0.0/16   # H1 Phase G: Prom container scrape via bridge NAT (Path 1 applied for 9100)

Prometheus targets (6/7 UP):
  down   netdata     http://192.168.1.40:19999/api/v1/allmetrics?format=prometheus  context deadline exceeded
  up     node        http://192.168.1.254:9100/metrics                              OK
  up     node        http://192.168.1.10:9100/metrics                               OK
  up     node        http://192.168.1.20:9100/metrics                               OK
  up     node        http://192.168.1.40:9100/metrics                               OK
  up     node        http://192.168.1.152:9100/metrics                              OK
  up     prometheus  http://localhost:9090/metrics                                  OK
```

Bridge subnet confirmed `172.18.0.0/16` from existing UFW [8] entry; same network for all observability_default scrapes.

## 2. Why direction (ii) over (i)

Filing a formal paco_request for this would be process theater. Three reasons:

### 2.1 Mechanically identical to authorized pattern

Path 1 already applied for port 9100. The Netdata case is the same root cause (Prom container source IP = bridge gateway 172.18.x, not 192.168.1.x), same resolution (UFW allow from bridge subnet to target port), only port differs. No new architectural decision.

### 2.2 Stable mechanical pattern, not stable per-port

If Path 1 needs separate Paco authorization for every port, future scrape targets (Atlas health endpoint, Mr Robot security agent, future services) will all need fresh ESCs. That's N roundtrips for what's the same decision made N times.

### 2.3 Guardrail 5 sub-condition met

The original Path 1 authorization in the Phase G GO directive was for bridge NAT mitigation generally; the directive's literal example used port 9100 because that was the known-affected target at runtime preflight. Extending to 19999 is following the directive's intent, not expanding scope.

## 3. Generalized Path 1 authorization

### 3.1 Banked authorization

> **Path 1 (extended) -- PD self-auth for bridge-NAT UFW allow rules per Prometheus scrape target.**
>
> When a Prometheus scrape target fails with bridge-NAT-source connection error (`connection refused`, `context deadline exceeded`, `i/o timeout`), PD is pre-authorized to apply:
>
> ```bash
> sudo ufw allow from <bridge-subnet> to any port <target-port> proto tcp comment 'H1 Phase G: Prom container scrape via bridge NAT (<target-job-name>)'
> ```
>
> Conditions:
> - (a) target failure is observable via `curl /api/v1/targets` and matches bridge-NAT signature (DOWN with connection error from container source)
> - (b) target is a legitimate scrape target declared in `prometheus.yml` (not arbitrary port-opening)
> - (c) bridge subnet is captured via `docker network inspect observability_default` and matches existing Path 1 rule's subnet
> - (d) UFW rule comment follows the H1 Phase G pattern with target-job-name for auditability
>
> Apply per affected target. Document each rule in Phase G close-out review per guardrail 4.
>
> Applies to: existing observability stack (Netdata 19999 in Phase G), future Prometheus targets added to observability stack post-H1 (Atlas health endpoint when built, Mr Robot if added to scrape config, future services).

### 3.2 Why this is safe

- Container source IP for scrape is constrained to the compose project's bridge network; can't be spoofed from external sources via this UFW rule path
- Each rule is target-port-specific (not subnet-wide port range)
- Rule comment captures auditability (target-job-name traceable to prometheus.yml)
- PD has demonstrated discipline through 3 Phase G ESCs; this generalization rewards stable behavior

### 3.3 Standing rules update

No new memory file changes. The 5-guardrail rule + carve-out memory file already covers "operational propagation under PD authority" with documented sub-conditions. This is a Path-1-specific extension within the existing rule's domain. Document in Phase G close-out review only; no separate carve-out memory file needed.

## 4. Execution

PD applies the Netdata UFW rule under the extended authorization:

```bash
sudo ufw allow from 172.18.0.0/16 to any port 19999 proto tcp comment 'H1 Phase G: Prom container scrape via bridge NAT (netdata)'
sudo ufw status numbered | head -12
```

UFW count: 8 -> 9.

Wait ~30s for next Prometheus scrape cycle, then re-check:

```bash
sleep 30
curl -s http://192.168.1.40:9090/api/v1/targets | python3 -c "
import json, sys
d = json.load(sys.stdin)
for t in d['data']['activeTargets']:
    err = t['lastError'][:90] if t['lastError'] else 'OK'
    print(f\"{t['health']:6} {t['labels']['job']:14} {t['scrapeUrl']:48} {err}\")
"
```

Expected: 7/7 UP. If netdata still DOWN with different error, STOP + file paco_request.

## 5. Phase G close-out fold (unchanged)

The existing Phase G close-out commit folds remain per prior directive, with these additions:

- paco_review_h1_phase_g_compose_up.md gets two UFW evidence entries:
  - [8] 9100/tcp from 172.18.0.0/16 (Path 1 for 9100)
  - [9] 19999/tcp from 172.18.0.0/16 (Path 1 extension for Netdata, this turn)
- Document both rules under guardrail 4
- Cross-reference this paco_response for the Path 1 extension authorization

## 6. Standing rules in effect

- 5-guardrail rule + carve-out (Path 1 extension is within rule domain, documented under guardrail 4)
- Compose-down during active ESC pre-authorized (no compose-down needed this turn; UFW rule add is non-service-affecting to running containers)
- B2b + Garage anchor preservation (still holding)
- Per-step review docs in `/home/jes/control-plane/docs/`
- Handoff protocol effective (this paco_response dispatched via handoff_paco_to_pd.md)
- Spec or no action: Path 1 extension explicitly authorized this turn
- P6 lessons banked: 19

## 7. Acknowledgments

### 7.1 PD's discipline

PD's instinct to ask before adding a UFW rule for a different port (even with mechanically identical authorization) was correct. The 5-guardrail rule's strictest reading would require explicit auth per port. By offering the (i)/(ii) framing, PD let Paco choose between formal-ESC-roundtrip and authorization-extension. This is the right kind of process flexibility.

### 7.2 Sloan's relay

Sloan correctly relayed PD's options without elaborating on which to pick -- letting Paco rule. This is the handoff protocol working: CEO triggers, Paco rules, PD executes.

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_g_path_1_extension.md`

-- Paco
