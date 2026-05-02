# paco_response_reachability_step5_close_confirm

**To:** CEO (Sloan) | **From:** Paco | **Date:** 2026-05-02 Day 78 mid-day (post-Step-5)
**Authority basis:** Step 4 close-confirm (HEAD `3093c6b`); Step 5 sub-cycle ratification Day 78 mid-day (Option A: keep existing `macmini->github` key, canonicalize comment in authorized_keys block); CEO interactive Step 5.4 /etc/hosts patch; Paco-side Steps 5.1, 5.2, 5.3, 5.5, 5.6.
**Status:** STEP 5 CLOSE-CONFIRMED — 6/6 sub-steps PASS; full 7×7 N×N matrix 42/42 cross-node PASS; standing gates 5/5 bit-identical; zero `paco_request` escalations.
**Tracks:** `docs/homelab_reachability_v1_0.md` reachability cycle Step 5 (entire).

---

## Pre-directive verification finding (root cause identified)

Mac mini's actual LAN IP is `192.168.1.194` (ethernet via switch), NOT `192.168.1.13` as canonicalized at Step 3. CEO confirmed root cause Day 78 mid-day: ".13 was the wifi IP; .194 took over when I hardwired Mac mini to the switch." Pre-directive probe of Mac mini state (Step 5.0) caught this before any work proceeded — no canon-on-disk regression occurred.

**Also:** Mac mini's outbound public key (comment `macmini->github`) was already trusted across 3 fleet nodes (Beast, SlimJim, Goliath). Pre-existing key material was canonical; only the comment in canonical authorized_keys block needed canonicalization (Option A ratified by CEO).

**Also:** Mac mini's sshd was already loaded + listening on IPv4+IPv6 port 22 via launchd (no Step 5 fix work needed for sshd persistence; earlier "sshd unreachable" assumption was a Day 78 morning artifact tied to the stale .13 IP, not actual sshd state).

## Sub-step status

| Sub | Scope | Outcome | Notes |
|---|---|---|---|
| **5.1** | Update canonical `/etc/hosts` (.13→.194 macmini line) on 6 fleet nodes | PASS — marker block patched in-place, all `getent hosts macmini` returns `.194`; per-node `.bak.<ts>-step5` rollback files preserved | Idempotent marker replacement; non-canonical entries untouched |
| **5.2** | Update canonical `~/.ssh/config` (HostName `.13`→`.194` for `Host macmini`) on 6 fleet nodes | PASS — 6/6 nodes 1037 bytes, mode 600 jes:jes | atomic file write via `homelab_file_write` (paste-safe per P6 #35) |
| **5.3** | Add macmini key to canonical authorized_keys block (8→9 keys) on 6 fleet nodes | PASS — 1×BEGIN + 1×END + macmini-canonical entry verified on all 6 | Per-node `.bak.<ts>-step5` rollback files preserved |
| **5.4** | Install canonical /etc/hosts on Mac mini (CEO interactive, sudo required) | PASS — OK + 1×BEGIN + 1×END; `.bak.20260502-223225-step5` preserved | Bracketed-paste hazard avoided (macOS zsh strips markers cleanly) |
| **5.5** | Update MCP `ALLOWED_HOSTS["macmini"]` from `.13` to `.194`; verify `HOST_USERS` fallback to `SSH_USER="jes"` is correct | PASS — 1-line `sed -i` edit; commit + push + service restart | Pre-existing P5-class credential on line 25 NOT in scope for this commit (unchanged from prior state) |
| **5.6** | Install canonical `~/.ssh/config` + `~/.ssh/authorized_keys` on Mac mini; run 7×7 N×N matrix; canon baseline | PASS — macmini config 1037 bytes mode 600; authorized_keys 9-key marker block + macmini-canonical present, mode 600 jes:0; 7×7 matrix 42/42 cross-node PASS | All probes via SSH-from-CK or `homelab_ssh_run` |

## 7×7 N×N matrix verification (Step 5.6)

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

**42 cross-node cells PASS, 0 cells FAIL, 7 cells n/a (self-loops).**

Full canonical matrix updated at `docs/fleet_reachability_matrix_canon.md`.

## Standing gates pre/post snapshot

| Gate | Subject | Step 5 pre | Step 5 post | Verdict |
|---|---|---|---|---|
| 1 | B2b anchor (`control-postgres-beast`) | StartedAt `2026-04-27T00:13:57.800746541Z`; restart=0 | unchanged | bit-identical (96h+) |
| 2 | Garage anchor (`control-garage-beast`) | StartedAt `2026-04-27T05:39:58.168067641Z`; restart=0 | unchanged | bit-identical (96h+) |
| 4 | atlas-mcp.service (Beast) | MainPID 2173807, active | unchanged | unchanged |
| 5 | atlas-agent.service (Beast) | MainPID 0, inactive disabled | unchanged | unchanged |
| 6 | mercury-scanner.service (CK) | MainPID 643409, active | unchanged | unchanged |

**Verdict:** Standing Gates 5/5 PRESERVED. Step 5 was read-only on standing-gate services.

## CEO priority compliance

CEO directive (Day 78 mid-day, prior to Step 4 dispatch and continuing through Step 5): "prioritize we don't encounter any more ssh issues going forward from any node to any node."

**Discharged via design throughout Step 5:**

1. **Pre-directive verification caught .13→.194 BEFORE any canon write.** This is precisely the failure mode SR pre-directive verification rule exists to catch. No directive or canon was authored against the wrong IP.
2. **Per-node SSH verification after each authorized_keys install.** Same destructive-safe pattern as Step 4.3.
3. **Per-node verification after `~/.ssh/config` install.** Same atomic-write pattern as Step 4.4.
4. **Independent N×N matrix probe at Step 5.6.** 42/42 cells PASS confirms no regression introduced anywhere in the cycle.

**Result:** N×N matrix expanded from 6×6 (31/31 PASS at Step 4) to 7×7 (49/49 cells, 42 cross-node PASS at Step 5). Mac mini fully integrated into canonical fleet topology.

## Discipline observations (no new P6 lessons)

- **P6 pre-directive verification rule discharged its purpose this cycle.** Probe caught .13→.194 IP drift in Step 5.0 before authoring. Without that probe, Paco would have authored Step 5 against `.13`, the directive would have looked correct on paper, and execution would have failed at runtime in unpredictable ways. This is the textbook example of why the rule exists.
- **`homelab_file_write` tool path validated again** for atomic config installs across all 6 fleet nodes (Step 5.2 + Step 5.6 macmini). Zero shell-escape issues. P6 #35 mitigation strategy holding.
- **macOS zsh stripped bracketed-paste markers cleanly** during Step 5.4 CEO-interactive heredoc, in contrast to Pi3 bash earlier in session. Confirms the per-shell variability noted in P6 #35 candidate.
- **MCP service restart blip** (P6 #34 banked observation) repeated at Step 5.5 commit; expected; tool calls reconnected within seconds. Continued silent retry pattern remains the right answer.

## Step 6 audit queue (carried forward; new items)

Prior items remain queued. New items from Step 5:

1. Mac mini `/etc/hosts` retains comment block at top from initial macOS hosts template ("Host Database / localhost...") above the canonical marker block. Cosmetic only; harmless.
2. Mac mini `~/.ssh/` directory retains `id_ed25519_github` keypair alongside primary `id_ed25519`. Step 6 verify github-deploy uses still functional / consolidate if not.
3. Mac mini `authorized_keys` file ownership is `jes:wheel` (gid 0), not `jes:staff` (gid 20). macOS-default; functionally fine; Step 6 may normalize to staff for consistency with other macOS files.
4. Mac mini outbound key still has on-disk comment `macmini->github` (Option A path: comment-canonicalized in fleet authorized_keys block, on-disk left alone). Step 6 may rename for full consistency or leave (cost/benefit favors leave).

## Reachability cycle status

- [x] Step 1 — Canon doc + probe script
- [x] Step 2 — Option A user policy ratified
- [x] Step 3 — /etc/hosts on 4 PD-executable nodes
- [x] Step 3.5 — KaliPi + Pi3 onboarding
- [x] Step 4 — SSH config + authorized_keys (6 nodes)
- [x] Step 5 — Mac mini onboarding (.13→.194 IP correction; 7×7 matrix)
- [ ] Step 6 — Audit pass: dedupe authorized_keys; canonicalize comments; resolve queued items above; close cycle

## Next step

Three active queues:

1. **Reachability cycle Step 6** — Cosmetic + dedupe audit pass. Closes reachability cycle entirely. PD-executable. Could fold P5 v0.1.1 credential rotation in same cycle (the 18-credential canon-hygiene queue).
2. **CVE-2026-31431 patch cycle Step 2 onward** — PD-executable. Step 1 banked at Step 3.5. Could run in parallel with Step 6 (different services).
3. **Atlas v0.1 Phase 7** — still queued behind reachability cycle close (Step 6).

CEO direction needed on which queue advances next.

-- Paco
