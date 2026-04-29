# paco_request_h1_phase_d_goliath_kalipi

**Spec:** H1 -- SlimJim observability (`tasks/H1_observability.md` section 8)
**Step:** Phase D -- node_exporter fan-out, CK + Beast complete; Goliath + KaliPi blocked on different issues
**Status:** ESCALATION -- mid-Phase-D, two host-specific issues outside the broadened standing rule's safe self-correct domains
**Predecessor:** `docs/paco_response_h1_phase_c_confirm_phase_d_go.md` (commit `9b4cf43`, Phase D GO + mechanical scope assertion)
**Author:** PD
**Date:** 2026-04-29 (Day 74)
**Target hosts:** Goliath (192.168.1.20) + KaliPi (192.168.1.254)

---

## TL;DR

Phase D split-execution per CEO ratification: CK + Beast installed cleanly (50% complete). Goliath + KaliPi blocked on host-specific issues:

- **Goliath:** UFW is INACTIVE on the box. The directive's `ufw allow ... 9100 ...` rule would be dormant. Three resolution paths; touches firewall posture (security-boundary-adjacent per guardrail 5).
- **KaliPi:** PD's MCP→KaliPi connection has no NOPASSWD sudo. `sudo apt install` and `sudo ufw allow` both fail with "a password is required". Three resolution paths; touches credential surface per guardrail 5.

Both issues are escalation territory under the 5-guardrail rule. CEO ratified split-execution path; PD requests Paco ruling on the resolution paths.

B2b + Garage anchors on Beast still bit-identical: `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z`. Substrate undisturbed.

---

## 1. What's complete (CK + Beast)

### 1.1 CiscoKid (192.168.1.10)

```
prometheus-node-exporter 1.3.1-1ubuntu0.22.04.3 (jammy/universe)
service: active + enabled
listener: *:9100 (all interfaces, prometheus-node pid 1210124)
UFW rule [25]: 9100/tcp ALLOW IN 192.168.1.40 # H1: node_exporter scrape from SlimJim
UFW total: 30 rules (was 29, +1)
SlimJim curl http://192.168.1.10:9100/metrics: 2749 node_* metric lines, exit 0
```

### 1.2 Beast (192.168.1.152)

```
prometheus-node-exporter 1.3.1-1ubuntu0.22.04.3 (jammy/universe)
service: active + enabled
listener: *:9100 (all interfaces, prometheus-node pid 898226)
UFW rule [16]: 9100/tcp ALLOW IN 192.168.1.40 # H1: node_exporter scrape from SlimJim
UFW total: 16 rules (was 15, +1)
SlimJim curl http://192.168.1.152:9100/metrics: 2525 node_* metric lines, exit 0
```

### 1.3 Beast anchor preservation through CK + Beast installs

```
Pre + post Phase D partial:
  /control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z healthy 0
  /control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z healthy 0
```

BIT-IDENTICAL nanosecond match. apt install + UFW edit on Beast did not touch container state.

---

## 2. Issue 1: Goliath UFW INACTIVE

### 2.1 Diagnostic

```
ssh goliath 'sudo ufw status numbered'
  -> Status: inactive
```

Goliath does not have UFW running. The spec's `ufw allow from 192.168.1.40 to any port 9100 proto tcp` would silently no-op on an inactive UFW (rule gets stored but isn't enforced).

### 2.2 Other Goliath state

- prometheus-node-exporter: NOT installed. apt candidate available: `1.7.0-1ubuntu0.3+esm2` (noble-updates/universe, arm64)
- Port 9100: free
- Architecture: aarch64 (GX10 ARM)
- OS: Ubuntu 24.04 (noble)
- Tailscale: presumably on (per device map; not verified this turn)

### 2.3 Three resolution paths (PD analysis)

#### Option A1 -- Enable UFW on Goliath first

```bash
# On Goliath, allow SSH first (so we don't lock ourselves out):
sudo ufw allow 22/tcp
sudo ufw enable
# Then add the H1 rule:
sudo ufw allow from 192.168.1.40 to any port 9100 proto tcp comment 'H1: node_exporter scrape from SlimJim'
```

- Pros: matches spec verbatim; defense in depth
- Cons: introduces UFW as a new attack/admin surface on Goliath; risk of SSH lockout if rule order is wrong; out of Phase D scope (spec assumes UFW is already running)
- Risk: moderate -- could lock out PD/CEO from Goliath if rules misordered, requires careful execution

#### Option A2 -- Bind node_exporter to 192.168.1.40 only at the listener level (PD recommendation)

Ubuntu's `prometheus-node-exporter` debian package uses `/etc/default/prometheus-node-exporter` for ARGS configuration. Add `--web.listen-address=192.168.1.20:9100` (Goliath's own LAN IP) to ARGS, then restart the service. The listener binds only to the local LAN IP, not 0.0.0.0.

Wait -- that's per-host bind (Goliath listens on Goliath's IP only). The spec's UFW rule logic was "only SlimJim source can connect." Process-level bind isn't equivalent -- it just makes Goliath listen on a single interface. Anyone on the LAN that can reach 192.168.1.20:9100 (anyone in the .0/24) can scrape.

**Refined Option A2:** Even though process-bind doesn't EXACTLY replicate the UFW source-IP filter, it does limit listener exposure. For an internal LAN with only trusted hosts (homelab), this is reasonable defense in depth. Pair with a P5 carryover to enable UFW on Goliath when bandwidth allows.

- Pros: minimal new attack surface (no UFW); still LAN-scoped
- Cons: slightly weaker than spec intent (any LAN host can scrape, not just SlimJim)
- Risk: low; reversible at any time

#### Option A3 -- Skip UFW on Goliath, document as P5 carryover

Install + start node_exporter on Goliath, accept that the metrics endpoint is wide-open on the LAN (any LAN host can scrape). Document as P5 "enable UFW on Goliath in security audit phase."

- Pros: zero work on Goliath beyond install
- Cons: weakest security posture; defense by trust-the-LAN only
- Risk: low (trusted LAN) but unprincipled

---

## 3. Issue 2: KaliPi sudo requires password

### 3.1 Diagnostic

```
ssh kalipi 'sudo ufw status numbered'
  -> sudo: a terminal is required to read the password; either use ssh's -t option or configure an askpass helper
  -> sudo: a password is required
```

PD's MCP→KaliPi connection runs `ssh sloan@192.168.1.254 ...` (or similar). The KaliPi `/etc/sudoers` for user `sloan` does NOT have NOPASSWD set. Any `sudo` invocation requires interactive password entry, which a non-interactive ssh_run cannot satisfy.

Other hosts (CK, Beast, Goliath, SlimJim) all have `(ALL) NOPASSWD: ALL` for the working user -- which is why PD has been able to run sudo cleanly on those.

### 3.2 Other KaliPi state

- prometheus-node-exporter: NOT installed. apt candidate available: `1.10.2-1` (kali-rolling/main, arm64)
- Port 9100: free
- Architecture: aarch64 (Pi 4-class)
- OS: Kali rolling
- Tailscale: 100.66.90.76 per device map

### 3.3 Three resolution paths (PD analysis)

#### Option B1 -- CEO runs install + UFW commands directly (PD recommendation)

CEO SSHes to KaliPi and runs the install + UFW commands. Same handoff pattern as the mosquitto_passwd handoff in Phase C. PD provides exact commands; CEO executes; CEO confirms back; PD verifies via SlimJim curl.

```bash
# CEO action on KaliPi:
ssh sloan@192.168.1.254
sudo apt install -y prometheus-node-exporter
sudo systemctl enable --now prometheus-node-exporter
sudo ufw allow from 192.168.1.40 to any port 9100 proto tcp comment 'H1: node_exporter scrape from SlimJim'
sudo ss -tlnp | grep ':9100\b'  # confirm listener
sudo ufw status numbered | grep 9100  # confirm UFW rule
exit
```

- Pros: matches established Phase C handoff pattern; no NOPASSWD config change to KaliPi sudoers (security-boundary-adjacent)
- Cons: one round-trip for CEO action
- Risk: minimal; CEO is already authorized for sudo on KaliPi

#### Option B2 -- CEO sets up NOPASSWD for `sloan` on KaliPi

Add `/etc/sudoers.d/sloan-nopasswd` with `sloan ALL=(ALL) NOPASSWD:ALL` (or scoped to specific commands). PD then proceeds with install + UFW like other hosts.

- Pros: future ops on KaliPi don't need CEO handoffs
- Cons: persistent change to KaliPi sudoers (security-boundary-adjacent); requires CEO ratification of the policy change
- Risk: low; matches other homelab hosts' policy

#### Option B3 -- Skip KaliPi for now, document as P5 carryover

Document that KaliPi is a Phase D out-of-scope target due to sudo-password constraint. Resolve in a separate spec when CEO is ready to grant NOPASSWD or do a manual install. Goliath + CK + Beast complete Phase D's intent (3/4 fleet observability) and the spec's metric scrape works for the bulk of the homelab.

- Pros: zero work on KaliPi; clean Phase D close on the 3 working hosts
- Cons: KaliPi metrics not in the fleet; spec intent only 75% met
- Risk: low; can be added later

### 3.4 Note on `ssh -t` workaround

PD could use `ssh -t kalipi 'sudo ...'` to allocate a TTY and satisfy sudo's terminal requirement. But the password prompt would still need interactive input -- there's no way for PD to non-interactively type a password. The TTY workaround would only help if NOPASSWD were configured. Not viable for current state.

---

## 4. PD recommendations

- **Goliath: A2 refined** -- bind node_exporter to `192.168.1.20:9100` via `/etc/default/prometheus-node-exporter` ARGS. Document the divergence from spec (UFW source-IP filter not present) as P5 carryover. Cleanest trade-off given Goliath UFW state; defers UFW enable to a future security-hardening spec.
- **KaliPi: B1** -- CEO handoff. Matches the established Phase C credential-handoff pattern. No persistent sudoers change. Adds one round-trip but is the minimum-change path.

---

## 5. Asks of Paco

1. **Rule on Goliath path** (A1, A2-refined, A3, or other). PD recommendation A2-refined.
2. **Rule on KaliPi path** (B1, B2, B3, or other). PD recommendation B1.
3. **Acknowledge Phase D's "mechanical scope" assumption was incomplete** -- two host-specific gotchas surfaced (Goliath UFW state, KaliPi sudo policy) that aren't directive-correctable under any of the broadened rule's safe domains. Could the H1 spec's preflight have caught these earlier? Specifically: a per-host preflight matrix capturing UFW state + sudo NOPASSWD status + apt-cache availability would have surfaced both issues at Phase A. Worth banking as P6 lesson candidate (after this specific resolution): *"Phase preflight should include per-target-host operational-readiness checks (firewall state, sudo policy, package-manager availability) for every host the phase will touch, not just the primary host."*

---

## 6. State at this pause

### What changed

- CK: prometheus-node-exporter installed + UFW rule [25] added (29 -> 30 rules)
- Beast: prometheus-node-exporter installed + UFW rule [16] added (15 -> 16 rules)
- SlimJim: 2 successful curl verifications (CK 2749 metrics, Beast 2525 metrics)

### What is unchanged

- Goliath: prometheus-node-exporter NOT installed; UFW still inactive; no listener on :9100
- KaliPi: prometheus-node-exporter NOT installed; sudo barrier untouched
- SlimJim: no Phase D state changes (just performed curl scrapes)
- Beast `control-postgres-beast`: anchor bit-identical
- Beast `control-garage-beast`: anchor bit-identical
- All other hosts (CiscoKid Postgres, mosquitto, etc.): untouched

---

## 7. Cross-references

**Standing rules invoked:**
- Memory: `feedback_paco_review_doc_per_step.md` (paco_request_*.md for novel/blocking issues)
- Memory: `feedback_pkg_name_substitution_pd_authority.md` (5-guardrail rule, currently in effect; guardrail 5 triggers escalation for Goliath UFW + KaliPi sudo, both auth/firewall/credential surface)
- Spec or no action: PD did not enable UFW on Goliath or modify KaliPi sudoers
- B2b + Garage nanosecond invariant preservation

**Predecessor doc chain:**
- `paco_review_h1_phase_c_mosquitto.md` (Phase C close)
- `paco_response_h1_phase_c_confirm_phase_d_go.md` (commit `9b4cf43`, Phase D GO)
- (this) `paco_request_h1_phase_d_goliath_kalipi.md`

## 8. Status

**AWAITING PACO RULING on Goliath path + KaliPi path.**

PD paused. CK + Beast complete. Goliath + KaliPi unchanged. SlimJim + Beast services + all anchors preserved.

-- PD
