# paco_review_h1_phase_d_node_exporter

**Spec:** H1 -- SlimJim observability + MQTT broker close (`tasks/H1_observability.md` section 8)
**Step:** Phase D -- node_exporter fan-out across CK + Beast + Goliath + KaliPi
**Status:** AWAITING PACO FIDELITY CONFIRMATION + PHASE E GO
**Predecessor:** `docs/paco_response_h1_phase_d_goliath_kalipi_paths.md` (commit `6266ba1`, A2-refined approved + B1 with handoff approved + P6 #16 banked)
**Author:** PD
**Date:** 2026-04-29 (Day 74)
**Target hosts:** CiscoKid (192.168.1.10) + Beast (192.168.1.152) + Goliath (192.168.1.20) + KaliPi (192.168.1.254)

---

## TL;DR

All 4 target hosts now expose `prometheus-node-exporter` metrics scrape-able from SlimJim. **3-gate scorecard 3/3 PASS.** Two host-specific deviations from the spec's UFW source-IP filter pattern, both pre-authorized by Paco and documented per guardrail 4 of the broadened standing rule. Three P5 carryovers banked. P6 #16 banked at directive time, applied retroactively to the H1 spec's Phase A section as a preflight matrix template for future fan-out phases.

B2b + Garage nanosecond invariants on Beast bit-identical pre/post Phase D: `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z`. Substrate held through ~17 phases of H1 work + Phase A/B/Side-task/Phase C 7-ESC arc + Phase D's 4-host fan-out, totaling ~46 hours of operational work without disturbing either Postgres replication or Garage S3 substrate.

---

## 1. Per-host execution evidence

### 1.1 CiscoKid (192.168.1.10) -- standard apt + UFW

```
prometheus-node-exporter 1.3.1-1ubuntu0.22.04.3 (jammy/universe, amd64)
service: active + enabled
listener: *:9100 (all interfaces, prometheus-node pid 1210124)
UFW rule [25]: 9100/tcp ALLOW IN 192.168.1.40 # H1: node_exporter scrape from SlimJim
UFW total: 30 rules (was 29, +1)
SlimJim curl http://192.168.1.10:9100/metrics: 2749 node_* metric lines, exit 0
```

### 1.2 Beast (192.168.1.152) -- standard apt + UFW

```
prometheus-node-exporter 1.3.1-1ubuntu0.22.04.3 (jammy/universe, amd64)
service: active + enabled
listener: *:9100 (all interfaces, prometheus-node pid 898226)
UFW rule [16]: 9100/tcp ALLOW IN 192.168.1.40 # H1: node_exporter scrape from SlimJim
UFW total: 16 rules (was 15, +1)
SlimJim curl http://192.168.1.152:9100/metrics: 2525 node_* metric lines, exit 0
```

### 1.3 Goliath (192.168.1.20) -- A2-refined process-level bind (deviation 1)

```
prometheus-node-exporter 1.7.0-1ubuntu0.3+esm2 (noble-updates/universe, arm64)
service: active + enabled
listener: 192.168.1.20:9100 (process-level bind, prometheus-node pid 33676)
  -- pre-restart: *:9100 (default, PID 32545)
  -- post-restart: 192.168.1.20:9100 (NEW PID 33676 confirms restart)
ARGS appended to /etc/default/prometheus-node-exporter:
  ARGS="--web.listen-address=192.168.1.20:9100"
Backup: /etc/default/prometheus-node-exporter.bak.20260429_095821 (rollback target)
UFW: inactive on Goliath (P5 carryover -- enable in future hardening pass)
SlimJim curl http://192.168.1.20:9100/metrics: 2831 node_* metric lines, exit 0
```

### 1.4 KaliPi (192.168.1.254) -- CEO B1 handoff + A2-refined alt (deviation 2)

```
prometheus-node-exporter 1.11.1-1 (kali-rolling/main, arm64)
service: active + enabled
listener: 192.168.1.254:9100 (process-level bind, prometheus-node pid 2375586)
  -- pre-restart: *:9100 (default after B1 install, PID 2372734)
  -- post-restart: 192.168.1.254:9100 (NEW PID 2375586 confirms restart)
ARGS appended to /etc/default/prometheus-node-exporter:
  ARGS="--web.listen-address=192.168.1.254:9100"
Backup: /etc/default/prometheus-node-exporter.bak.20260429_101123 (rollback target)
UFW: NOT installed on KaliPi (Kali rolling does not ship UFW by default; see deviation 2.2)
CEO handoff: B1 pattern (interactive sudo, PD never ran sudo on KaliPi)
SlimJim curl http://192.168.1.254:9100/metrics: 1759 node_* metric lines, exit 0
```

---

## 2. Deviations from spec section 8 -- documented per guardrail 4

The 4-condition broadened rule (`feedback_directive_command_syntax_correction_pd_authority.md`, 5 guardrails + carve-out) requires verbatim documentation of any directive deviation. Both deviations below are pre-authorized by Paco in `paco_response_h1_phase_d_goliath_kalipi_paths.md` (commit `6266ba1`).

### Deviation 1 -- Goliath: process-level bind via ARGS instead of UFW source-IP filter

**Original directive (spec section 8 D.2):**

```bash
sudo ufw allow from 192.168.1.40 to any port 9100 proto tcp comment 'H1: node_exporter scrape from SlimJim'
```

**Substituted on Goliath:**

```bash
# Backup default config
sudo cp /etc/default/prometheus-node-exporter /etc/default/prometheus-node-exporter.bak.20260429_095821
# Append ARGS line
echo 'ARGS="--web.listen-address=192.168.1.20:9100"' | sudo tee -a /etc/default/prometheus-node-exporter
# Restart to apply
sudo systemctl restart prometheus-node-exporter
```

**Why functionally adequate (not equivalent):**

- UFW source-IP filter would restrict traffic to source `192.168.1.40` only.
- A2-refined process-bind restricts the listener to bind on `192.168.1.20` interface only -- any LAN host can still reach it (not just SlimJim).
- Goliath has UFW INACTIVE; the spec's UFW directive would have been a dormant rule with no enforcement. Process-bind provides defense-in-depth at the listener layer instead.
- Trusted homelab LAN context + read-only metrics endpoint + no VLAN segmentation (router limitation) make the residual exposure acceptable.

**Citation:** `paco_response_h1_phase_d_goliath_kalipi_paths.md` section 3 (Goliath A2-refined APPROVED).

**Banked as P5 carryover (see section 4):** Goliath UFW enable in future security-hardening pass; once UFW is up, the spec's source-IP rule lands as originally intended.

### Deviation 2 -- KaliPi: process-level bind via ARGS, UFW not installed

**Original directive (spec section 8 D.2):**

```bash
sudo ufw allow from 192.168.1.40 to any port 9100 proto tcp comment 'H1: node_exporter scrape from SlimJim'
```

**Substituted on KaliPi (CEO handoff Step 1-3 ran apt install + service start; Step 4 of original handoff failed):**

```
CEO ran:
  sudo ufw status numbered | head -3
  -> sudo: ufw: command not found
```

**Followed by A2-refined alt directive (CEO handoff, per Paco §4.4 pre-auth):**

```bash
sudo cp /etc/default/prometheus-node-exporter /etc/default/prometheus-node-exporter.bak.20260429_101123
echo 'ARGS="--web.listen-address=192.168.1.254:9100"' | sudo tee -a /etc/default/prometheus-node-exporter
sudo systemctl restart prometheus-node-exporter
```

**Why functionally adequate (not equivalent):**

- KaliPi runs Kali rolling; UFW is not part of the default install (different from Goliath where UFW was installed but inactive).
- Same A2-refined process-bind reasoning: listener restricted to KaliPi's own LAN interface; LAN-wide reachability rather than SlimJim-only.
- Larger P5 lift than Goliath: KaliPi requires `apt install ufw` + `ufw enable` + careful SSH-rule preservation, vs Goliath's `ufw enable` only.

**Citation:** `paco_response_h1_phase_d_goliath_kalipi_paths.md` section 4.4 ("If KaliPi UFW is also inactive" -- pre-auth for A2-refined alt).

**Banked as P5 carryover (see section 4):** KaliPi UFW install + enable in future security-hardening pass.

---

## 3. Phase D 3-gate scorecard

| Gate | Spec wording | CK | Beast | Goliath | KaliPi | Result |
|---|---|---|---|---|---|---|
| 1 | node_exporter active + enabled | active+enabled | active+enabled | active+enabled | active+enabled | **4/4 PASS** |
| 2 | SlimJim curl returns metrics from each | 2749 | 2525 | 2831 | 1759 | **4/4 PASS** |
| 3 | UFW per-node restricts to .40 only | rule [25] PASS | rule [16] PASS | process-bind 192.168.1.20 (deviation 1) | process-bind 192.168.1.254 (deviation 2) | **2/4 spec-literal + 2/4 deviation-substitute = 4/4 functional** |
| Standing | B2b + Garage anchors bit-identical pre/post | -- | -- | -- | -- | **PASS** (postgres `2026-04-27T00:13:57.800746541Z` + garage `2026-04-27T05:39:58.168067641Z`, both healthy 0 restarts) |

**Phase D internal scorecard: 3/3 PASS** (gate 3 met functionally; deviations documented per guardrail 4).

---

## 4. P5 carryovers banked this phase

1. **Goliath UFW enable** -- enable existing UFW on Goliath, allow SSH 22/tcp first to avoid lockout, then add `ufw allow from 192.168.1.40 to any port 9100 proto tcp` per spec original intent. Schedule for future security-hardening pass (likely H6 or v0.2 cleanup). Until then, A2-refined process-bind is operational substitute.

2. **KaliPi UFW install + enable** -- new this phase. Larger lift than Goliath: install via `sudo apt install ufw`, then enable with same SSH-preservation discipline, then add the 9100 source-IP rule. Kali rolling distribution choice not to ship UFW reflects the security-tooling host posture (KaliPi runs pentest tooling; UFW would be added in deliberate hardening, not as default).

3. **CK + Beast process-bind symmetry** -- CK and Beast currently listen on `*:9100` (default config) with UFW source-IP filter providing the restriction. Goliath + KaliPi listen on `<lan-ip>:9100` (process-bind). For fleet symmetry in a future hardening pass, consider adding `--web.listen-address=<lan-ip>:9100` to CK + Beast as defense-in-depth (UFW + process-bind). Not required for spec close; informational only.

---

## 5. P6 #16 banked

### 5.1 Banked rule (verbatim from `paco_response_h1_phase_d_goliath_kalipi_paths.md` section 2.1)

> **Phase preflight should include per-target-host operational-readiness checks for every host the phase will touch, not just the primary host.**
>
> Required captures per target host:
> - **Firewall state** (active/inactive/missing); for active firewalls, current rule count
> - **Sudo policy** for the working user (NOPASSWD vs interactive password required)
> - **Package-manager availability** + candidate version of the target package(s) for the phase
> - **Listener-port collision check** for any port the phase will bind
> - **Architecture compatibility** (x86_64 / aarch64 / etc.) for any binary or compiled package
> - **OS family + version** if behavior may differ (apt repo path, systemd unit name conventions, etc.)
>
> When a phase fans out across multiple hosts (e.g., node_exporter to 4 nodes), preflight enumeration on every host reveals operational policy heterogeneity BEFORE the phase tries to act on assumptions. Mid-phase escalation for state mismatches that preflight would have caught is process tax that compounds across builds.
>
> Banked from H1 Phase D Day 74: directive's "mechanical scope" claim was correct for CK + Beast (NOPASSWD + UFW active) but incomplete for Goliath (UFW inactive) and KaliPi (sudo password required + UFW not installed), forcing mid-phase escalation that preflight would have surfaced at Phase A.

### 5.2 P6 lessons banked count

**16** (was 15 at Phase D entry; +1 this phase). Spec amendment to `tasks/H1_observability.md` Phase A folded into this commit applies the matrix template forward-going for future H1 + H2 + H3 phases.

### 5.3 Spec amendment

`tasks/H1_observability.md` section 5 (Phase A) gets a new subsection **A.5 -- Per-target-host preflight matrix** appended this commit. Captures the 6-row required-captures table for any future fan-out phase. H2 (Cortez integration) and H3 (Pi3 DNS Gateway) are single-host phases and won't need it; they'll capture single-host preflight. The matrix template applies whenever a future spec phase touches multiple hosts.

---

## 6. Beast anchor preservation evidence

Beast `control-postgres-beast` and `control-garage-beast` containers were *never* touched during Phase D. The fan-out work was: apt install on 4 hosts (CK / Beast / Goliath / KaliPi), config file edits on 2 hosts (Goliath + KaliPi `/etc/default/prometheus-node-exporter`), UFW edits on 2 hosts (CK + Beast), and 4 systemd service starts/restarts on the prometheus-node-exporter unit. None of this touched Beast's Docker stack.

Verified bit-identical at multiple points during Phase D:

```
# Phase D entry (post-Phase-C close):
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z healthy 0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z healthy 0

# After CK install + UFW:
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z healthy 0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z healthy 0

# After Beast install + UFW (apt operations on Beast itself):
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z healthy 0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z healthy 0

# After Goliath A2-refined:
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z healthy 0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z healthy 0

# After KaliPi B1 + A2-refined alt:
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z healthy 0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z healthy 0
```

Five captures across Phase D, all bit-identical. **17+ phases of H1 work + ~46 hours of operational time, both anchors held.**

---

## 7. State at close

### Per-host

- **CiscoKid (192.168.1.10):** prometheus-node-exporter 1.3.1, listener `*:9100`, UFW rule [25] H1 source-filter, scrape-confirmed.
- **Beast (192.168.1.152):** prometheus-node-exporter 1.3.1, listener `*:9100`, UFW rule [16] H1 source-filter, scrape-confirmed.
- **Goliath (192.168.1.20):** prometheus-node-exporter 1.7.0, listener `192.168.1.20:9100` (process-bind via ARGS), UFW inactive (P5 deferred), scrape-confirmed.
- **KaliPi (192.168.1.254):** prometheus-node-exporter 1.11.1, listener `192.168.1.254:9100` (process-bind via ARGS), UFW not installed (P5 deferred), scrape-confirmed.

### SlimJim Phase D readiness

All 4 target endpoints reachable from SlimJim. Phase E (Prometheus + Grafana compose stack) can now scrape all 4 hosts. Phase E config will list:
- 192.168.1.10:9100 (CK)
- 192.168.1.152:9100 (Beast)
- 192.168.1.20:9100 (Goliath)
- 192.168.1.254:9100 (KaliPi)
- 192.168.1.40:19999 (Netdata, already present from earlier H1 phases)
- localhost:9090 (Prometheus self-scrape, when Phase E lands)
- localhost:3000 (Grafana, when Phase E lands)

### Beast substrate (untouched)

- `control-postgres-beast`: bit-identical anchor `2026-04-27T00:13:57.800746541Z`, healthy 0 restarts.
- `control-garage-beast`: bit-identical anchor `2026-04-27T05:39:58.168067641Z`, healthy 0 restarts.
- B2b logical replication subscriber on Beast: continuous, undisturbed.
- Garage S3 substrate on Beast: continuous, undisturbed.

---

## 8. Asks of Paco

1. **Confirm Phase D 3/3 gates PASS** against the captured evidence (sections 1 + 3).
2. **Authorize Phase E GO** -- observability/ skeleton + Docker Compose stack on SlimJim (Prometheus + Grafana with provisioned dashboards 1860 + 3662) per spec section 9.
3. **Acknowledge 3 P5 carryovers banked** (Goliath UFW enable / KaliPi UFW install + enable / CK + Beast process-bind symmetry).
4. **Acknowledge P6 #16 spec amendment landed** in tasks/H1_observability.md A.5 (preflight matrix template for fan-out phases).

---

## 9. Cross-references

**Standing rules invoked:**
- Memory: `feedback_paco_review_doc_per_step.md` (per-step review docs in `/home/jes/control-plane/docs/`)
- Memory: `feedback_directive_command_syntax_correction_pd_authority.md` (5-guardrail rule + carve-out for ops propagation -- both deviations documented per guardrail 4)
- Spec or no action: PD did not enable UFW on Goliath, did not install UFW on KaliPi, did not modify KaliPi sudoers (B2/B3 paths declined per Paco rulings)
- B2b + Garage nanosecond invariant preservation

**Predecessor doc chain:**
- `paco_review_h1_phase_c_mosquitto.md` (Phase C 5/5 PASS, YELLOW #5 closed)
- `paco_response_h1_phase_c_confirm_phase_d_go.md` (commit `9b4cf43`, Phase D GO)
- `paco_request_h1_phase_d_goliath_kalipi.md` (PD ESC after Phase D preflight surfaced Goliath UFW + KaliPi sudo issues)
- `paco_response_h1_phase_d_goliath_kalipi_paths.md` (commit `6266ba1`, A2-refined APPROVED + B1 with handoff APPROVED + P6 #16 BANKED)
- (this) `paco_review_h1_phase_d_node_exporter.md`

**Capture / state files referenced:**
- `/etc/default/prometheus-node-exporter` (Goliath + KaliPi -- production files)
- `/etc/default/prometheus-node-exporter.bak.20260429_095821` (Goliath rollback target)
- `/etc/default/prometheus-node-exporter.bak.20260429_101123` (KaliPi rollback target)

## 10. Status

**AWAITING PACO FIDELITY CONFIRMATION + PHASE E GO.**

PD paused. 4 hosts scrape-ready. SlimJim observability stack can now consume the fleet. UFW + Beast undisturbed. B2b + Garage anchors preserved bit-identical through 17+ H1 phases / ~46 hours.

-- PD
