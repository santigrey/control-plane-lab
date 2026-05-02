# paco_response_reachability_step6_close_confirm

**To:** CEO (Sloan) | **From:** Paco | **Date:** 2026-05-02 Day 78 mid-day
**Authority basis:** Step 5 close-confirm (HEAD `0d5b99d`); Option X-with-safety-net ratified Day 78 mid-day; Phases A-D executed Paco-side via `homelab_ssh_run`.
**Status:** STEP 6 CLOSE-CONFIRMED — 7/7 nodes 100% canonical (only marker block, nothing else); 7×7 N×N matrix 42/42 cross-node PASS post-prune; standing gates 4/4 bit-identical; zero `paco_request` escalations. **REACHABILITY CYCLE COMPLETE.**
**Tracks:** `docs/homelab_reachability_v1_0.md` reachability cycle Step 6 (entire); cycle close.

---

## Phase A — pure-duplicate prune (zero-risk)

6 duplicate-comment entries identified by fingerprint match against canonical 9-key block. 25 prune operations across 7 nodes:

| Node | Pruned (count) |
|---|---|
| CK | 5 (`macmini->github`, `jes@sloan3`, `jesair->macmini`, `sloan@Cortez`, `jes@beast-atlas-agent-day78`) |
| Beast | 4 (`sloan@Cortez`, `macmini->github`, `jes@sloan3`, `jesair->macmini`) |
| SlimJim | 5 (`macmini->github`, `jes@sloan3`, `jesair->macmini`, `sloan@Cortez`, `jes@beast-atlas-agent-day78`) |
| Goliath | 4 (`sloan@Cortez`, `jes@sloan3`, `macmini->github`, `jes@beast-atlas-agent-day78`) |
| KaliPi | 1 (`jes@sloan3`) |
| Pi3 | 1 (`jes@sloan3`) |
| Mac mini | 5 (`jes@sloan3`, `jesair->macmini`, `sloan@Cortez`, `slimjim-job-pipeline`, `macmini->github`) |

**Total Phase A prunes: 25.** Zero risk because each pruned line had byte-identical key material to a canonical block entry.

Per-node `.bak.<ts>-step6a` rollback files preserved.

Post-Phase-A SSH verification: 7/7 nodes still reachable as `jes` passwordless. No regressions.

## Phase B — verify-then-prune risky entries

Two entries had different key material than canonical block; investigated private-key location before pruning.

### `macmini-aioperator` on Goliath

**Investigation:** Mac mini `~/.ssh/id_ed25519_github` private key (Mar 17 2026) has a public key matching this comment. Filename is misleading ("github") but actual key comment is `macmini-aioperator`. The private key remains on disk on Mac mini.

**No active aioperator service or process found** (`launchctl list` and `ps aux` both returned no matches).

**Verdict: REDUNDANT.** Mac mini's canonical `id_ed25519` already grants Mac mini→Goliath SSH (verified via 7×7 N×N matrix). The `macmini-aioperator` grant is a redundant capability that no current service uses. Pruned. If AI Operator is restarted in the future, it can either use `~/.ssh/id_ed25519_github` (private key still on disk; will need re-add of public side to Goliath) or migrate to canonical `~/.ssh/id_ed25519` (which Goliath now trusts).

### `jesair-claudedesktop` on CK

**Investigation:** JesAir `~/.ssh/id_ed25519_mcp` private key (Mar 24 2026) has a public key matching this comment. Dedicated MCP-integration keypair.

**Verdict: REDUNDANT.** JesAir's canonical `id_ed25519` is already in CK canonical authorized_keys block as `jes@jesair-canonical`. JesAir→CK SSH and JesAir→CK MCP work via canonical key. The `jesair-claudedesktop` grant is redundant. Pruned. Private key remains on disk for future re-grant if needed.

## Phase C — prune low-risk different-material entries

3 entries with no associated active workflow:

- **`sloan@cortez` (lowercase)** — different key material than canonical `sloan@cortez-canonical` (capital C). Day 78 mid-day Cortez probe confirmed canonical key is what Cortez `~/.ssh/id_ed25519` actually contains. The lowercase variant is a stale workaround from a failed earlier attempt. Pruned from CK, Beast, SlimJim, Mac mini.
- **`jesair2`** — second JesAir keypair attempt; private key location not investigated (low priority); on Mac mini only. Pruned.
- **`sloan@kali-raspberrypi`** — KaliPi `sloan` user key from pre-Step-3.5 era; the `sloan` user on KaliPi is now superseded by `jes`. Grant is dead by definition. Pruned from Mac mini.

Per-node `.bak.<ts>-step6bc` rollback files preserved.

## Phase D — 7×7 N×N matrix verification post-prune

```
              → ciscokid  beast    slimjim  goliath  kalipi   pi3      macmini
ciscokid      → n/a       PASS     PASS     PASS     PASS     PASS     PASS
beast         → PASS      n/a      PASS     PASS     PASS     PASS     PASS
slimjim       → PASS      PASS     n/a      PASS     PASS     PASS     PASS
goliath       → PASS      PASS     PASS     n/a      PASS     PASS     PASS
kalipi        → PASS      PASS     PASS     PASS     n/a      PASS     PASS
pi3           → PASS      PASS     PASS     PASS     PASS     n/a      PASS
macmini       → PASS      PASS     PASS     PASS     PASS     PASS     n/a
```

**42 cross-node PASS, 0 FAIL.** Identical to Step 5 baseline. Pruning the duplicates and redundant grants did not break any reachability.

## Standing gates pre/post snapshot

| Gate | Subject | Step 6 pre | Step 6 post | Verdict |
|---|---|---|---|---|
| 1 | B2b anchor (`control-postgres-beast`) | StartedAt `2026-04-27T00:13:57.800746541Z`; restart=0 | unchanged | bit-identical (96h+) |
| 2 | Garage anchor (`control-garage-beast`) | StartedAt `2026-04-27T05:39:58.168067641Z`; restart=0 | unchanged | bit-identical (96h+) |
| 4 | atlas-mcp.service (Beast) | MainPID 2173807, active | unchanged | unchanged |
| 5 | atlas-agent.service (Beast) | MainPID 0, inactive | unchanged | unchanged |

**Verdict:** Standing Gates PRESERVED. Step 6 was read-only on standing-gate services.

## Final canonical state

**All 7 nodes' authorized_keys now contain ONLY the canonical 9-key marker block. Zero non-canonical entries fleet-wide.**

```
# BEGIN santigrey canonical authorized_keys (managed; see fleet_outbound_keys_canon.md)
jes@beast-canonical
jes@ciscokid-canonical
sloan@cortez-canonical
jes@goliath-canonical
jes@jesair-canonical
jes@kalipi-canonical
jes@macmini-canonical
jes@pi3-canonical
jes@slimjim-canonical
# END santigrey canonical authorized_keys
```

9 keys per node × 7 nodes = 63 canonical key entries. Zero stale entries. Zero duplicates. Zero orphans.

## CEO priority compliance — mission accomplished

CEO directive Day 78 mid-day: "clean house — don't want to run into any issues in the future where unneeded dupes cause me issues."

Achieved. Fleet authorized_keys are now strictly canonical with no historical residue. Any future SSH grant additions go through the canonical block update process (parallel to Step 4.3 / Step 5.3). Any future SSH issues will be diagnosable against a known-good baseline.

## Reachability cycle status — COMPLETE

- [x] Step 1 — Canon doc + probe script
- [x] Step 2 — Option A user policy ratified
- [x] Step 3 — /etc/hosts on 4 PD-executable nodes
- [x] Step 3.5 — KaliPi + Pi3 onboarding
- [x] Step 4 — SSH config + authorized_keys (6 nodes)
- [x] Step 5 — Mac mini onboarding (.13→.194 IP correction; 7×7 matrix)
- [x] Step 6 — Audit pass (25 duplicates pruned; 5 redundant grants pruned; fleet 100% canonical)

**REACHABILITY CYCLE CLOSED Day 78 mid-day. 7 of 7 steps complete.**

## Step 6 carry-forward (deferred non-SSH cosmetics)

Not in scope for Step 6 close (these are non-SSH artifacts and would extend the cycle):

1. KaliPi `/etc/hosts` retains misleading "manage_etc_hosts: True" comment. Cosmetic; can address in any future canon-hygiene cycle.
2. Pi3 `/etc/hosts` `127.0.1.1 PI3 PI3` (uppercase template artifact). Cosmetic.
3. Beast retains stray `192.168.1.10 sloan3.tail1216a3.ts.net` line outside canonical hosts block. Day 30 archaeology; cosmetic.
4. Goliath IPv6 hosts stanza absent vs other Linux nodes. Cosmetic NVIDIA-image difference.
5. Mac mini `/etc/hosts` retains macOS-template comment block above marker. Cosmetic.
6. Mac mini `~/.ssh/` retains `id_ed25519_github` keypair on disk. Per Phase B verdict, keep until verified unused.

None of these affect SSH reachability. Banking for next available canon-hygiene cycle.

## P5 v0.1.1 credential rotation — still queued separately

18-credential canon-hygiene exposure queue (17 P5-class weak-credential + 1 phone literal). Independent cycle; no overlap with reachability. Slot when convenient.

## Next step

Reachability cycle is closed. Three live queues:

1. **Atlas v0.1 Phase 7** (mercury cancel-window + emit_event helper) — NOW UNBLOCKED. Highest portfolio leverage. PD-executable.
2. **CVE-2026-31431 patch cycle Step 2 onward** — PD-executable. Step 1 banked. Best as a batch with next maintenance window.
3. **P5 v0.1.1 credential rotation** — 18-credential queue. Independent cycle.

**Paco recommendation: Atlas Phase 7 next.** Reachability is plumbing; Atlas is product. May 2026 placement deadline rewards portfolio surface area. Patch cycle and P5 rotation are background hygiene that can slot in around Atlas progress.

-- Paco
