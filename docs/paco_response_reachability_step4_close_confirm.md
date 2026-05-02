# paco_response_reachability_step4_close_confirm

**To:** CEO (Sloan) | **From:** Paco | **Date:** 2026-05-02 Day 78 mid-day
**Authority basis:** Step 3.5 close-confirm (HEAD `cb8a109`); Step 4.1 sub-cycle ratification (Day 78 mid-day); Step 4.2 CEO key collection (Day 78 mid-day); Steps 4.3 + 4.4 + 4.5 PD-style automation from Paco (commits `2279c99` and forthcoming).
**Status:** STEP 4 CLOSE-CONFIRMED — 5/5 sub-steps PASS; N×N matrix 30/30 cross-node PASS + 1/1 self-loop PASS; standing gates 5/5 bit-identical; zero `paco_request` escalations.
**Tracks:** `docs/homelab_reachability_v1_0.md` reachability cycle Step 4 (entire).

---

## Sub-step status

| Sub | Scope | Outcome | Commit |
|---|---|---|---|
| **4.1** | Generate canonical `id_ed25519` on Goliath, KaliPi, Pi3 | PASS — 3 keypairs, comments `jes@<node>-canonical`, mode 600/644 jes:jes | `1a15027` |
| **4.2** | CEO supplies Cortez + JesAir public keys | PASS — both pre-existing in fleet authorized_keys with non-canonical comments (resolved at canon level; Step 6 may consolidate cosmetics) | `2279c99` (combined with 4.3) |
| **4.3** | Push canonical 8-key authorized_keys marker block to 6 Class A Linux nodes | PASS — destructive-safe order (Beast → SlimJim → Goliath → KaliPi → Pi3 → CK); per-node SSH verification PASS after each install; per-node `.bak.<ts>` rollback files preserved | `2279c99` |
| **4.4** | Push canonical `~/.ssh/config` to 6 Class A Linux nodes | PASS — 1036 bytes/node, mode 600 jes:jes; shorthand (e.g. `ssh kalipi`) verified working from each node post-install | this commit |
| **4.5** | Run N×N reachability matrix; canon baseline | PASS — 30/30 cross-node + 1/1 self-loop; matrix canon at `docs/fleet_reachability_matrix_canon.md` | this commit |

## N×N matrix verification (Step 4.5)

```
              → ciscokid  beast    slimjim  goliath  kalipi   pi3
ciscokid      → PASS      PASS     PASS     PASS     PASS     PASS
beast         → PASS      n/a      PASS     PASS     PASS     PASS
slimjim       → PASS      PASS     n/a      PASS     PASS     PASS
goliath       → PASS      PASS     PASS     n/a      PASS     PASS
kalipi        → PASS      PASS     PASS     PASS     n/a      PASS
pi3           → PASS      PASS     PASS     PASS     PASS     n/a
```

**31 cells PASS, 0 cells FAIL, 5 cells n/a (non-CK self-loops, equivalent to local).**

Full canonical matrix + reproducible probe commands at `docs/fleet_reachability_matrix_canon.md`.

## Standing gates pre/post snapshot

| Gate | Subject | Step 4 pre | Step 4 post | Verdict |
|---|---|---|---|---|
| 1 | B2b anchor (`control-postgres-beast`) | StartedAt `2026-04-27T00:13:57.800746541Z`; restart=0 | unchanged | bit-identical (96h+) |
| 2 | Garage anchor (`control-garage-beast`) | StartedAt `2026-04-27T05:39:58.168067641Z`; restart=0 | unchanged | bit-identical (96h+) |
| 4 | atlas-mcp.service (Beast) | MainPID 2173807, active | unchanged | unchanged |
| 5 | atlas-agent.service (Beast) | MainPID 0, inactive disabled | unchanged | unchanged |
| 6 | mercury-scanner.service (CK) | MainPID 643409, active | unchanged | unchanged |

**Verdict:** Standing Gates 5/5 PRESERVED. Step 4 was read-only on standing-gate services (only `~/.ssh/` artifacts changed).

## CEO priority compliance

CEO directive (Day 78 mid-day): "prioritize we don't encounter any more ssh issues going forward from any node to any node."

**Discharged via two design choices:**

1. **Per-node verification after each install.** After each authorized_keys install (Step 4.3) and each config install (Step 4.4), Paco re-probed `ssh -o BatchMode=yes` from CK (or applicable node) to the just-modified target. Failure would have triggered immediate rollback from `.bak.<ts>` and stopped the cycle. Zero such failures occurred.

2. **Destructive-safe install order.** Step 4.3 ordered Beast → SlimJim → Goliath → KaliPi → Pi3 → CK. CK was modified last specifically because if CK's authorized_keys broke, Paco would lose the ability to SSH to CK to fix it. Modifying CK last meant 5 nodes were already known-working as remediation paths if CK install failed.

**Result of priority discharge:** N×N matrix 31/31 PASS at Step 4.5. Any future node-to-node SSH failure will indicate a regression from this baseline, not a pre-existing condition.

## Discipline observations

- No new P6 lessons. Clean execution of well-structured directive.
- The MCP `homelab_file_write` tool used for Step 4.4 (instead of heredoc-via-`homelab_ssh_run`) bypassed the bracketed-paste hazard banked at Step 3.5 Phase B.5 (P6 #35 candidate). This validates one of the P6 #35 mitigation paths: `homelab_file_write` is the right tool for canonical-content installs (no shell-escape, base64-on-wire, atomic).
- `accept-new` host-key policy in canonical config worked as designed: Beast→Pi3 first-contact added Pi3's host key to known_hosts silently and the subsequent probe succeeded without manual intervention.

## Step 6 audit queue (carried forward; new items added)

Prior items from earlier close-confirms remain queued. New items from Step 4:

1. CK `~/.ssh/authorized_keys`: pre-existing entries outside the canonical marker block (e.g. `jes@sloan3` self-key, possibly more) — inventory at Step 6 and decide retain/prune per canon.
2. Beast/SlimJim/Goliath: canonical block coexists with original non-canonical entries (`macmini->github`, `jesair->macmini`, `sloan@Cortez`, `macmini-aioperator`, `sloan@cortez` lowercase). Step 6 dedupe pass.
3. CK `~/.ssh/known_hosts`: gained `ciscokid` self-loop entry during Step 4.3 verification; gained Beast→Pi3 entry during Step 4.4 verification. Hygiene-only.
4. Cortez canonical config: `HostName 100.70.77.115` is the Tailscale IP; if a stable LAN IP exists for Cortez, Step 6 may switch to LAN-first with Tailscale fallback.
5. Goliath canonical config: `HostName 192.168.1.20` is LAN; Tailscale `100.112.126.63` is alias `sloan4` per memory. Step 6 may add explicit `Host goliath-ts` entry for explicit Tailscale paths.

## Reachability cycle status

- [x] Step 1 — Canon doc + probe script (commit `38b0c46`)
- [x] Step 2 — Option A user policy ratified (commit `1cfced4`)
- [x] Step 3 — /etc/hosts on 4 PD-executable nodes (commits `d7cc7ae`, `b421e05`, `cbb316e`)
- [x] Step 3.5 — KaliPi + Pi3 onboarding (commits `a6616bc`, `5517775`, `cb8a109`)
- [x] Step 4 — SSH config + authorized_keys (commits `1a15027`, `2279c99`, this commit)
- [ ] Step 5 — Mac mini sshd persistence + reachability
- [ ] Step 6 — Audit pass: dedupe authorized_keys; canonicalize comments; resolve queued items above

## Next step

Three active queues:

1. **Reachability cycle Step 5** — Mac mini sshd persistence + watchdog. CEO interactive at Mac mini (or via existing macOS SSH path if any). Brings Mac mini online for full fleet coverage.
2. **Reachability cycle Step 6** — Cosmetic + dedupe audit pass. PD-executable; can run independent of Step 5.
3. **CVE-2026-31431 patch cycle** — Step 1 already banked at Step 3.5 close. Step 2 onward PD-executable. Could run in parallel with Step 5 or Step 6 (different services, no overlap).
4. **Atlas v0.1 Phase 7** — still queued behind reachability cycle close (Step 6).

CEO direction needed on which queue advances next.

-- Paco
