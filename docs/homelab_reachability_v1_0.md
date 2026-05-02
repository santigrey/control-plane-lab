# Homelab Reachability Canon v1.0

**Purpose:** Single source of truth for SSH + network reachability across Project Ascension fleet.
**Created:** 2026-05-02 Day 78 mid-day per CEO directive (root-cause cycle, not another ad-hoc fix).
**Owner:** Paco maintains; Mr Robot inherits at v0.2 build.
**Probe:** `canaries/reachability_probe.sh` -- regression test; runs at every cycle close.

Past sessions (Day 30, 51, 60, 65, 78) each shipped a "permanent" SSH fix that drifted within days. Each fix was point-in-time, undocumented, untested. This doc + probe is the regression catch. Every cell here must be verifiable by the probe.

---

## Node inventory

**Class A -- always-on servers; full SSH mesh expected:**

| Node | LAN IP | Tailscale | User | Role |
|---|---|---|---|---|
| CiscoKid | 192.168.1.10 | sloan3.tail1216a3.ts.net | jes | orchestrator + canonical Postgres + Mercury + nginx |
| TheBeast | 192.168.1.152 | sloan2.tail1216a3.ts.net | jes | atlas-mcp + atlas Postgres replica + Garage anchor |
| SlimJim | 192.168.1.40 | sloan1.tail1216a3.ts.net | jes | edge / MQTT broker |
| Goliath | 192.168.1.20 | 100.112.126.63 (sloan4) | jes | GPU inference (Ollama) |
| KaliPi | 192.168.1.254 | (TBD) | jes (post Step 3.5) | pentesting (isolated). Was `sloan` until Day 78 Option A consolidation. |
| Pi3 | 192.168.1.139 | 100.71.159.102 | jes (post Step 3.5) | DNS gateway (role TBD). Was `sloanzj` until Day 78 Option A consolidation. |
| Mac mini | 192.168.1.13 | (TBD) | jes | MCP bridge host for Claude Desktop |

**Class B -- endpoints; SSH out only (no inbound expected):**

| Device | LAN IP | Tailscale | User | Role |
|---|---|---|---|---|
| JesAir | 192.168.1.155 | (TBD) | jes | macOS laptop -- CEO ops |
| Cortez | (LAN n/a) | 100.70.77.115 | sloan | Windows -- CEO ops + Cowork PD home. **Option A exception:** Windows local account fixed at OS install; consolidating to `jes` would require full reinstall. Stays `sloan`. |

## Required reachability

- **A <-> A: full mesh** (7×6 = 42 pairs). Every Class A node SSHes to every other Class A node passwordlessly with the canonical key for that source.
- **B -> A: full reach** (2×7 = 14 pairs). JesAir + Cortez SSH out to every Class A node.
- **A -> B: NOT required.** Servers don't SSH to laptops; laptops sleep.
- **Self-pairs:** trivially OK.

**Total required:** 56 pairs.

## User policy (CEO decision PENDING -- required before Step 4 of reachability cycle)

Three organic identities exist: `jes` (most nodes), `sloan` (KaliPi + Cortez), `sloanzj` (Pi3). Three resolution paths:

- **A. Consolidate to `jes` everywhere.** Add `jes` user on KaliPi + Pi3; on Cortez `jes` not feasible (Windows local account). Cost ~30 min.
- **B. Document and accept heterogeneity.** ssh config handles per-host User directive transparently; no operational cost.
- **C. Hybrid.** Consolidate Pi3 (sloanzj -> jes; ~10 min); leave KaliPi + Cortez as-is.

**Paco recommendation: B.** The fragmentation is organic, fixing it has no operational benefit, ssh config makes it transparent. Document and move on.

**CEO decision (Day 78 mid-day):** **OPTION A** -- consolidate to `jes` user across the fleet.

- **KaliPi:** add `jes` user with sudo + ssh keys (Step 3.5 below). Old `sloan` user stays available; not removed.
- **Pi3:** add `jes` user with sudo + ssh keys (Step 3.5 below). Old `sloanzj` user stays available; not removed.
- **Cortez exception:** Windows local account is fixed at OS install time; consolidating to `jes` would require full reinstall + reconfigure of Tailscale + Cowork + all CEO tooling under that user. Cost-benefit ratio inverted; **Cortez stays `sloan`** as a documented exception, not a regression.
- All canonical ssh config / authorized_keys / probe matrix below assume `jes@kalipi` and `jes@pi3` post-3.5; Cortez probes use `sloan@cortez` indefinitely.

## Canonical `/etc/hosts` (push to all Class A Linux nodes; Step 3)

```
192.168.1.10    ciscokid sloan3
192.168.1.152   beast sloan2
192.168.1.40    slimjim sloan1
192.168.1.20    goliath sloan4
192.168.1.254   kalipi
192.168.1.139   pi3
192.168.1.13    macmini
192.168.1.155   jesair
```

This is the DNS regression layer until Pi3 takes over local DNS.

## Canonical `~/.ssh/config` (push to each device; Step 4)

**Linux Class A nodes (CK / Beast / SlimJim / Goliath / Mac mini / JesAir):**

```sshconfig
Host ciscokid sloan3
    HostName 192.168.1.10
    User jes
    IdentityFile ~/.ssh/id_ed25519

Host beast sloan2
    HostName 192.168.1.152
    User jes
    IdentityFile ~/.ssh/id_ed25519

Host slimjim sloan1
    HostName 192.168.1.40
    User jes
    IdentityFile ~/.ssh/id_ed25519

Host goliath sloan4
    HostName 192.168.1.20
    User jes
    IdentityFile ~/.ssh/id_ed25519

Host kalipi
    HostName 192.168.1.254
    User jes
    IdentityFile ~/.ssh/id_ed25519

Host pi3
    HostName 192.168.1.139
    User jes
    IdentityFile ~/.ssh/id_ed25519

Host macmini
    HostName 192.168.1.13
    User jes
    IdentityFile ~/.ssh/id_ed25519

# Common
ServerAliveInterval 60
ServerAliveCountMax 3
StrictHostKeyChecking accept-new
```

**Cortez (Windows; PowerShell paths; user sloan):**

Same Host blocks; `IdentityFile` points to `~/.ssh/id_ed25519` (resolves to `%USERPROFILE%\.ssh\id_ed25519`).

**KaliPi + Pi3 (rarely SSH outbound; minimal config):**

Minimal config -- only entry needed is for CK if KaliPi/Pi3 ever push state. Optional.

## authorized_keys policy (Step 4)

Every Class A node's `~/.ssh/authorized_keys` (under the canonical user for that node) contains:

1. **Every other Class A node's outbound key** (ed25519 public key per node, comment = `<user>@<node>-canonical`)
2. **JesAir's outbound key** (`jesair-canonical`)
3. **Cortez's outbound key** (`sloan@cortez-canonical`)

**Removed at Step 4 cleanup:**
- Stale historical entries (e.g. `jesair2`, `jesair->macmini`, `slimjim-job-pipeline`) -- kept only if attributable to live use; otherwise pruned with audit log.
- Any unrecognized keys -- log to canon as suspicious; flag for Mr Robot.

Final authorized_keys inventory baseline populated by Step 6 probe; recorded in this doc's appendix.

## Mac mini sshd persistence (Step 5)

Known failure mode: `launchctl enable system/com.openssh.sshd` (Day 60) did not actually persist across reboots. Verified again Day 78 (Mac mini SSH timed out).

Real fix:
```bash
# On Mac mini, run as jes:
sudo systemsetup -f -setremotelogin on
sudo launchctl enable system/com.openssh.sshd
sudo launchctl bootout system /System/Library/LaunchDaemons/ssh.plist 2>/dev/null
sudo launchctl bootstrap system /System/Library/LaunchDaemons/ssh.plist
# Verify daemon running:
launchctl print system/com.openssh.sshd | grep state
```

If bootstrap fails ("Input/output error"), file paco_request before retrying. Real root cause may be SIP-protected plist that needs Recovery Mode reset.

**Watchdog (after sshd is up):** cron entry that probes localhost SSH every 15 min and re-bootstraps on failure. Source: `canaries/macmini_sshd_watchdog.sh` (authored at Step 5).

## Probe script

`canaries/reachability_probe.sh` -- runs from any Class A node; tests N×N matrix by SSHing to each source, then from source to each target. Outputs per-pair PASS/FAIL + summary. Exit 0 = full pass; exit 1 = any failure.

Use:
- Manual: `ssh ciscokid 'bash /home/jes/control-plane/canaries/reachability_probe.sh'`
- Atlas Domain 1 (post-Phase-7.5): scheduled 15-min cadence; FAIL writes Tier 2 atlas.events row
- Mr Robot (v0.2+): inherits as part of standing security audit

## Drift policy

When probe finds drift:
1. Atlas (or Mr Robot) emits Tier 2 atlas.events warn
2. Paco does NOT silently fix mid-cycle. Escalate to discrete reachability follow-up cycle.
3. Audit canon, update doc, re-probe. Drift becomes new baseline only after CEO ratifies.

This is the thing that makes this fix actually stick.

## Update protocol

Updates only in three cases:
1. New node joins fleet -> add to inventory + matrix + ssh config + /etc/hosts
2. CEO ratifies user policy change -> update relevant tables
3. Probe finds drift that is NOT regression (intentional new key) -> log in audit

Probe output drives doc updates, not the reverse.

## Current state baseline (PENDING -- populated at Step 6 first probe run)

To be filled in after reachability cycle Step 5 closes. Becomes the post-cycle canonical baseline.

## Past-fix archaeology (audit reference)

| Date | Fix shipped | Why it didn't stick |
|---|---|---|
| Day 30 | Cortez ssh config + key on CK/Beast/SlimJim authorized_keys | Per-device; no canon doc; .254/.40 IP confusion |
| Day 30 | JesAir ssh config (heredoc failed; rewrote with Python) | No verification probe |
| Day 51 | Mac mini sshd publickey fix abandoned -- switched MCP bridge to HTTP instead | Workaround, not fix |
| Day 60 | `launchctl enable system/com.openssh.sshd` -- declared "gremlin permanently dead" | Same gremlin returned Day 51 (3 days later) and Day 78 |
| Day 65 | Goliath SSH from Cortez via Tailscale + manual key push | One-off; no canon |
| Day 78 | Beast outbound key generated + deployed to 4 nodes | Phase 0 unblock; PD couldn't reach KaliPi as jes; Pi3 not in fleet at all |

Pattern: each fix was reactive, local, and undocumented. Drift went undetected because no probe ran. This doc + probe ends that pattern.

-- Paco
