# fleet_reachability_matrix_canon

**Maintained by:** Paco | **Status:** ACTIVE | **Last verified:** 2026-05-02 Day 78 mid-day (Step 5 close)
**Tracks:** `docs/homelab_reachability_v1_0.md` reachability cycle Step 5 (Mac mini onboarding + N×N expansion to 7 nodes).

---

## Purpose

Canonical N×N SSH reachability matrix for the Class A Linux+macOS fleet. Every cell is a verified `ssh -o BatchMode=yes` test from the row node to the column node, executed live and recorded with timestamp + outcome. Authoritative answer to "can node A SSH to node B as jes (or cortez=sloan) without a password?"

## Verified live N×N matrix (2026-05-02 Day 78 mid-day, post-Step-5)

Fleet: 7 Class A nodes (6 Linux + Mac mini macOS). All probes use canonical hostname (no `jes@` prefix; relies on `~/.ssh/config` `User jes` directive) and canonical IdentityFile per node's `~/.ssh/config`. `BatchMode=yes` ensures NO interactive prompts. `ConnectTimeout=5` caps stalled probes.

```
              → ciscokid  beast    slimjim  goliath  kalipi   pi3      macmini
ciscokid      → PASS      PASS     PASS     PASS     PASS     PASS     PASS
beast         → PASS      n/a      PASS     PASS     PASS     PASS     PASS
slimjim       → PASS      PASS     n/a      PASS     PASS     PASS     PASS
goliath       → PASS      PASS     PASS     n/a      PASS     PASS     PASS
kalipi        → PASS      PASS     PASS     PASS     n/a      PASS     PASS
pi3           → PASS      PASS     PASS     PASS     PASS     n/a      PASS
macmini       → PASS      PASS     PASS     PASS     PASS     PASS     n/a
```

**Total cells:** 49 (7 source nodes × 7 destinations). 
**Cross-node cells:** 42. 
**Cross-node PASS:** 42. 
**Cross-node FAIL:** 0. 
**Self-loop cells:** 7 (only CK self-loop probed live previously; macmini self-loop n/a; others marked n/a as equivalent to local commands).

## Verification commands (reproducible)

From each source node, executed via `homelab_ssh_run host=<source>` (or for macmini, via SSH from CK due to MCP allowed-host wiring):

```bash
for h in <list of 6 other nodes>; do
  printf "%s: " "$h"
  ssh -o BatchMode=yes -o ConnectTimeout=5 "$h" 'echo OK_$(hostname)' 2>&1 | tail -1
done
```

Expected output per probe: `OK_<remote-hostname>` exactly one line. Anything else (Permission denied, Connection timed out, host-key warnings, no output) is a FAIL or cosmetic event requiring re-test.

## Cosmetic events observed

- Step 4.5 (prior baseline): Beast → pi3 first-contact host-key acceptance via `accept-new`. Re-probe at Step 5 silent. 
- Step 5: macmini → all 6 first-contact host-key acceptance via `accept-new` for each fleet node it had not contacted before. All silent on subsequent re-probe.

## Out-of-scope (deferred to later cycles)

- **JesAir reachability:** physical/sshd state unverified Day 78 (Step 5+ candidate; key already in canonical authorized_keys block).
- **Cortez reachability:** Class B Windows endpoint, outbound-only by design (Y1 carve-out). Not a target node.
- **Tailscale-mediated paths:** canonical config uses LAN IP for in-network nodes; Tailscale fallback works automatically via Tailscale magic-DNS for Cortez. Step 6 may add explicit `Host *-ts` entries if useful.

## Refresh policy

Re-run full N×N matrix probe and update this file at:

1. Any change to canonical `~/.ssh/authorized_keys` (Step 4.3-equivalent operations)
2. Any change to canonical `~/.ssh/config` (Step 4.4-equivalent operations)
3. New node onboarding (e.g. when JesAir joins)
4. Quarterly hygiene cadence (otherwise)

Probe is fast (~45s for full 7×7 matrix orchestrated from CK) and free of side effects. Run liberally.
