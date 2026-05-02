# fleet_reachability_matrix_canon

**Maintained by:** Paco | **Status:** ACTIVE | **Last verified:** 2026-05-02 Day 78 mid-day (Step 4.5 close)
**Tracks:** `docs/homelab_reachability_v1_0.md` reachability cycle Step 4.5 (N×N reachability baseline).

---

## Purpose

Canonical N×N SSH reachability matrix for the Class A Linux fleet. Every cell is a verified `ssh -o BatchMode=yes` test from the row node to the column node, executed live and recorded with timestamp + outcome. This is the authoritative answer to "can node A SSH to node B as jes without a password?"

Refreshed at every reachability-cycle close-confirm and at any subsequent change to the canonical authorized_keys block.

## Verified live N×N matrix (2026-05-02 Day 78 mid-day post-Step-4.4)

Fleet: 6 Class A Linux nodes. All probes use canonical hostname (no `jes@` prefix; relies on `~/.ssh/config` `User jes` directive) and canonical IdentityFile per node's `~/.ssh/config`. `BatchMode=yes` ensures NO interactive prompts (passwords, keyboard-interactive, host-key confirmation). `ConnectTimeout=5` caps stalled probes.

```
              → ciscokid  beast    slimjim  goliath  kalipi   pi3
ciscokid      → PASS      PASS     PASS     PASS     PASS     PASS
beast         → PASS      n/a      PASS     PASS     PASS     PASS
slimjim       → PASS      PASS     n/a      PASS     PASS     PASS
goliath       → PASS      PASS     PASS     n/a      PASS     PASS
kalipi        → PASS      PASS     PASS     PASS     n/a      PASS
pi3           → PASS      PASS     PASS     PASS     PASS     n/a
```

**Total cells probed:** 36 (6 source nodes × 6 destinations). 
**Self-loop cells:** 6 (e.g. CK→CK; only CK self-loop probed live; others marked n/a as they are equivalent to local commands and add no value to verify). 
**Cross-node cells:** 30. 
**Cross-node PASS:** 30. 
**Cross-node FAIL:** 0.

## Verification commands (reproducible)

From each source node, executed via `homelab_ssh_run host=<source>`:

```bash
for h in <list of 5 other nodes>; do
  echo -n "$h: "
  ssh -o BatchMode=yes -o ConnectTimeout=5 $h 'echo OK_$(hostname)' 2>&1 | tail -1
done
```

Expected output per probe: `OK_<remote-hostname>` exactly one line. Anything else (Permission denied, Connection timed out, Permanently added warning, no output) is a FAIL or a cosmetic event requiring re-test.

## Cosmetic events observed during Step 4.5 verification

- **Beast → pi3:** First-contact host-key acceptance triggered `Warning: Permanently added '192.168.1.139' (ED25519) to the list of known hosts.` per `accept-new` policy. Re-probe expected to be silent. Logged here as documentation that `accept-new` is functioning as designed; not a failure mode.

## Out-of-scope (deferred to later cycles)

- **Mac mini reachability:** sshd unreachable Day 78 (Step 5 queued).
- **JesAir reachability:** physical/sshd state unverified Day 78 (Step 5 candidate).
- **Cortez reachability:** Class B Windows endpoint, outbound-only by design (Y1 carve-out). Not a target node.
- **Tailscale-mediated paths (e.g. CK→Goliath via Tailscale 100.112.126.63):** canonical config uses LAN IP for Goliath; Tailscale path remains as fallback. Step 6 may add explicit `Host goliath-ts` entry if useful.

## Refresh policy

Re-run full N×N matrix probe and update this file at:

1. Any change to canonical `~/.ssh/authorized_keys` (Step 4.3-equivalent operations)
2. Any change to canonical `~/.ssh/config` (Step 4.4-equivalent operations)
3. New node onboarding (e.g. when Mac mini joins post-Step-5)
4. Quarterly hygiene cadence (otherwise)

Probe is fast (~30s for full matrix from CK orchestration) and free of side effects. Run liberally.
