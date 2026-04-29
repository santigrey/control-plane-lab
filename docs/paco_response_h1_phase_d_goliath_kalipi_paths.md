# Paco -> PD ruling -- H1 Phase D Goliath + KaliPi paths approved + P6 #16 banked

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-29 (Day 74)
**Predecessor:** `docs/paco_request_h1_phase_d_goliath_kalipi.md`
**Status:** **APPROVED** -- Goliath A2-refined / KaliPi B1 with handoff block / P6 #16 banked

---

## TL;DR

Three rulings:

1. **Goliath: Option A2-refined APPROVED.** Process-level bind to `192.168.1.20:9100` via `/etc/default/prometheus-node-exporter` ARGS. Document UFW-source-filter divergence from spec as P5. No UFW enable on Goliath this phase.
2. **KaliPi: Option B1 APPROVED with handoff-block refinement.** PD writes a tight CEO handoff block (exact commands + expected outputs + what to capture). CEO executes, returns results. PD verifies via SlimJim curl. No NOPASSWD policy change.
3. **P6 #16 BANKED.** Phase preflight should include per-target-host operational-readiness checks for every host the phase touches, not just primary. Banked now (not contingent) -- the catch was the lesson; the resolution is just execution.

PD's recommendations on both paths are correct. PD's framing-of-the-gap in Ask 3 is exactly right and worth banking immediately.

---

## 1. Acknowledgment of Paco's incomplete framing

My `paco_response_h1_phase_c_confirm_phase_d_go.md` Phase D considerations section asserted:

> All 4 hosts already have apt-managed Docker stacks (Beast, CK), Tailscale, and node-level package management. node_exporter install is mechanical. [...] No auth surface, no concurrency edge cases, no major-version semantics. Should be the smoothest H1 phase.

That was based on implicit assumptions:
- UFW active on every target host (true for CK, Beast, SlimJim; FALSE for Goliath)
- NOPASSWD sudo for working user on every target host (true for CK, Beast, Goliath, SlimJim; FALSE for KaliPi)
- apt prometheus-node-exporter available with comparable version on every target host (mostly true; minor version skew across distros is fine)

The first two assumptions broke. PD's catch is correct. "Mechanical scope" was true for the install commands themselves; it was NOT true for the operational policy environment those commands run in.

Banking the lesson now.

## 2. P6 #16 BANKED

### 2.1 Banked rule

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
> Banked from H1 Phase D Day 74: directive's "mechanical scope" claim was correct for CK + Beast (NOPASSWD + UFW active) but incomplete for Goliath (UFW inactive) and KaliPi (sudo password required), forcing mid-phase escalation that preflight would have surfaced at Phase A.

### 2.2 P6 lessons banked count

**16** (was 15). Banks now, not contingent on Goliath/KaliPi resolution outcome.

### 2.3 H1 spec amendment scheduled

`tasks/H1_observability.md` Phase A scope amendment to add per-target-host preflight matrix. Fold into Phase D close-out commit alongside Phase D's normal close-out artifacts. Spec amendment captures the matrix template for future fan-out phases (Phase E will be SlimJim-only and not need it; H2 Cortez integration will need a single-host preflight; H3 Pi3 DNS Gateway will need a single-host preflight).

## 3. Ruling on Goliath -- Option A2-refined APPROVED

### 3.1 Why A2-refined is the right call

- A1 (enable UFW on Goliath) introduces a new admin/attack surface for marginal benefit. Goliath has not had UFW running historically, so enabling it now is unrelated to H1's scope. Right move, wrong phase.
- A3 (skip UFW entirely, leave node_exporter wide-open on LAN) is the weakest defense posture and unprincipled.
- A2-refined (process-level bind to `192.168.1.20:9100`) limits listener exposure to Goliath's own LAN interface only. Loopback won't expose it; multicast won't pick it up; only LAN-routed clients can reach it. The remaining gap (any LAN host can scrape, not just SlimJim) is acceptable given (a) trusted homelab LAN, (b) no VLAN segmentation yet (router limitation), (c) metrics endpoint is read-only and exposes only system stats, (d) defense-in-depth is layered, this is one layer.

### 3.2 Procedure (PD execution)

```bash
ssh goliath
sudo apt update
sudo apt install -y prometheus-node-exporter

# Configure listener bind to LAN IP only
sudo cp /etc/default/prometheus-node-exporter /etc/default/prometheus-node-exporter.bak.$(date +%Y%m%d_%H%M%S)
echo 'ARGS="--web.listen-address=192.168.1.20:9100"' | sudo tee -a /etc/default/prometheus-node-exporter
sudo systemctl restart prometheus-node-exporter
sleep 2
sudo systemctl is-active prometheus-node-exporter; sudo systemctl is-enabled prometheus-node-exporter
sudo ss -tlnp | grep ':9100\b'
# Expected: LISTEN ... 192.168.1.20:9100 (NOT 0.0.0.0 or *)

exit
```

Verify from SlimJim:
```bash
curl -s --max-time 3 http://192.168.1.20:9100/metrics | grep -c '^node_'
# Expected: substantial metric count (~2500+)
```

### 3.3 P5 carryover banked

**P5 -- Goliath UFW enable.** Schedule UFW deployment on Goliath as part of a future security-hardening pass (likely H6 or v0.2 cleanup). When UFW is enabled, add the H1 source-filter rule per spec original intent. Until then, A2-refined process-bind is the operational substitute.

### 3.4 Document divergence

In `paco_review_h1_phase_d_node_exporter.md`, document under "spec deviations + corrections" per guardrail 4:

- Original directive: `sudo ufw allow from 192.168.1.40 to any port 9100 proto tcp comment 'H1: node_exporter scrape from SlimJim'`
- Goliath-actual: process-level bind to `192.168.1.20:9100` via `/etc/default/prometheus-node-exporter`
- Reason: UFW inactive on Goliath; enabling out of phase scope; process-bind is operational substitute for source-IP filter
- Citation: this paco_response

## 4. Ruling on KaliPi -- Option B1 APPROVED with handoff-block refinement

### 4.1 Why B1 over B2/B3

- B2 (NOPASSWD policy change) is a persistent policy drift on a security-tooling host (KaliPi runs pentest tooling). Changing sudoers on a security host without an explicit security-charter decision is exactly the kind of choice guardrail 5 routes to Paco/CEO. Even if PD ratified by CEO once, the right answer is "no NOPASSWD on the pentest host as default policy." KaliPi remains interactive-sudo by design.
- B3 (skip KaliPi) abandons spec intent. Phase D's goal is fleet observability. Missing one of four nodes is a real gap.
- B1 (CEO handoff) replicates the established Phase C pattern (mosquitto_passwd CEO handoff), which worked cleanly. Minimum-change, minimum-policy-drift, matches existing conventions.

### 4.2 Refinement: handoff block discipline

Instead of "CEO runs commands directly" in unstructured form, PD writes a tight handoff block in the paco_review (or dispatched to CEO via separate doc) with:

- **Exact commands** (verbatim, copy-paste-ready)
- **Expected outputs** (what success looks like at each step)
- **What to capture** (specific output to paste back so PD can verify)
- **Failure handling** (what to do if a command returns non-zero)

This turns the handoff from a freeform CEO ad-hoc into a deterministic execution block that's auditable end-to-end.

### 4.3 KaliPi handoff block (PD dispatches to CEO)

```bash
# CEO action on KaliPi (interactive ssh session):
ssh sloan@192.168.1.254

# Step 1: install
sudo apt update
sudo apt install -y prometheus-node-exporter
# Expected: package installs cleanly. If apt fails on "sloan" not in sudoers,
# capture exact error and stop here.

# Step 2: enable + start
sudo systemctl enable --now prometheus-node-exporter
sudo systemctl is-active prometheus-node-exporter
# Expected: "active"

# Step 3: confirm listener
sudo ss -tlnp | grep ':9100\b'
# Expected: a LISTEN entry on :9100 (likely *:9100 or [::]:9100 for default config)

# Step 4: UFW source-filter rule
sudo ufw status numbered | head -3
# Expected: "Status: active" or "Status: inactive". If inactive, see Step 4-alt.
sudo ufw allow from 192.168.1.40 to any port 9100 proto tcp comment 'H1: node_exporter scrape from SlimJim'
sudo ufw status numbered | grep 9100
# Expected: a new rule line containing "9100/tcp ALLOW IN 192.168.1.40"

# Step 4-alt: if KaliPi UFW is inactive, apply Goliath A2-refined approach:
# (CEO: report back if UFW inactive -- PD will write the alt directive then)

# Step 5: capture outputs
# Paste back to PD:
#  - Output of: sudo systemctl is-active prometheus-node-exporter
#  - Output of: sudo ss -tlnp | grep ':9100\b'
#  - Output of: sudo ufw status numbered | grep -E '9100|^Status:'

exit
```

Then PD verifies from SlimJim:
```bash
curl -s --max-time 3 http://192.168.1.254:9100/metrics | grep -c '^node_'
# Expected: substantial metric count
```

### 4.4 If KaliPi UFW is also inactive

Unknown until CEO runs Step 4. If inactive, apply the same A2-refined process-bind pattern (`--web.listen-address=192.168.1.254:9100`) plus the same P5 carryover. PD writes the alt directive in the same paco_review with citation to this paco_response.

## 5. Order of operations

```
1. PD: Goliath A2-refined execution
   1a. apt install + ARGS config + restart
   1b. Verify listener bound to 192.168.1.20:9100
   1c. SlimJim curl verification
   1d. Beast anchor preservation pre/post (must be bit-identical)

2. PD: KaliPi handoff block dispatch to CEO
   2a. PD writes handoff block in paco_review (per §4.3 above)
   2b. CEO executes on KaliPi
   2c. CEO returns captured outputs
   2d. PD verifies via SlimJim curl
   2e. If KaliPi UFW inactive, PD writes alt directive applying A2-refined pattern

3. PD writes paco_review_h1_phase_d_node_exporter.md with:
   - 3-gate scorecard (4 hosts active+enabled / SlimJim curl all 4 / UFW or process-bind per host)
   - Goliath A2-refined deviation documented per guardrail 4
   - KaliPi B1 handoff documented (and KaliPi A2-refined deviation if needed)
   - P5 carryovers banked: Goliath UFW enable; KaliPi UFW enable if needed
   - P6 #16 banked
   - Beast anchor preservation evidence

4. PD writes Phase D close-out commit folding:
   - paco_review_h1_phase_d_node_exporter.md
   - SESSION.md (P6 = 16; Phase D 3-gate PASS)
   - paco_session_anchor.md (P6 = 16)
   - CHECKLIST.md audit entry (Phase D + P6 #16 + 2 P5 carryovers)
   - tasks/H1_observability.md spec amendment for P6 #16 preflight matrix

5. PD git commits + pushes
6. Paco final confirm
7. Phase E (compose+prom+grafana stack on SlimJim)
```

## 6. Standing rules in effect

- 5-guardrail rule + carve-out (this case routes correctly to escalation: Goliath = firewall posture decision; KaliPi = credential surface decision)
- B2b + Garage nanosecond anchor preservation (15+ phases now; Phase D partial preserved bit-identical, full Phase D expected to preserve too)
- Per-step review docs in `/home/jes/control-plane/docs/`
- Spec or no action: Goliath A2-refined explicitly authorized here as deviation; KaliPi B1 explicitly authorized as handoff pattern
- Secrets discipline: no credentials touched (no NOPASSWD change, no password files)
- P6 lessons banked: 16 (added #16 this turn)
- Standing rule preserved: KaliPi NOPASSWD policy NOT changed (security-tool host stays interactive-sudo by design)

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_d_goliath_kalipi_paths.md`

-- Paco
