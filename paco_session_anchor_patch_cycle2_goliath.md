# paco_session_anchor_patch_cycle2_goliath

**Purpose:** Bootstrap a fresh Paco session for CVE-2026-31431 Patch Cycle 2 (Goliath dedicated). Self-contained — paste this file's path at session start; Paco runs the boot probe + reads queued canon + proceeds to directive authoring with all decisions pre-ratified.

**Anchor authored:** 2026-05-03 Day 79 evening (post-Patch-Cycle-1 close-confirm; SR #7 third application + P6 #37 first application complete)
**Active until:** Cycle 2 close-confirm OR replaced by next anchor

---

## Identity reminder

You are Paco — COO + systems architect for Santigrey Enterprises. CEO is Sloan. PD is Cowork. Operating mode: anchor-as-pointer (canon is source of truth). Address Sloan as Sloan. Operations motto: measure twice, cut once.

---

## Why this is a SEPARATE anchor (not just paco_session_anchor.md)

Cycle 2 (Goliath) is **the highest-complexity cycle banked to date.** Per CEO standing instruction "keep sessions manageable, start new if in doubt," Cycle 2 deserves its own dedicated session with full context budget for:
- P6 #37's first proper application (blast-radius categorization for 584 packages — some of this is done in this anchor's preflight section, but directive authoring needs fresh context)
- 5 ratified decisions (A3/B3/C2/D2/E2 — see below)
- Major kernel jump 6.11.0-1016-nvidia → 6.17.0-1014.14 + NVIDIA driver dkms rebuild + CUDA 13.0→13.2 toolkit upgrade
- One known partial deferral (docker-compose-plugin v5 held for separate cycle per B3)

The risk profile of Cycle 2 alone justifies session-fresh treatment. This anchor preserves all preflight + decisions so the fresh Paco can author the directive without re-doing 6+ turns of context-building.

---

## Boot probe (run via homelab MCP at session start)

```
ssh ciscokid 'cd /home/jes/control-plane && git log --oneline -1' -> expect HEAD 9be9765 (or later)
ssh beast 'cd /home/jes/atlas && git log --oneline -1' -> expect c28310b (UNCHANGED post-Atlas-ship)
ssh beast 'systemctl show -p MainPID -p NRestarts -p ActiveState -p UnitFileState atlas-agent.service' -> expect MainPID 4753 NRestarts 0 active enabled (post-Patch-Cycle-1 baseline)
ssh beast 'docker inspect control-postgres-beast --format "{{.State.StartedAt}}"' -> expect 2026-05-03T18:38:24.910689151Z (NEW SG2 anchor post-Cycle-1)
ssh beast 'docker inspect control-garage-beast --format "{{.State.StartedAt}}"' -> expect 2026-05-03T18:38:24.493238903Z (NEW SG3 anchor post-Cycle-1)
ssh ciscokid 'systemctl show -p MainPID mercury-scanner.service' -> expect 7800 (NEW SG6 post-Cycle-1)
ssh goliath 'uname -r; uptime' -> expect 6.11.0-1016-nvidia; uptime ~3-N days (Cycle 2 scope confirmation)
```

**If any baseline value diverges:** SR #6 self-state probe before assuming. Something happened between this anchor write and fresh-session resume. Investigate via journalctl + git log before authoring directive.

---

## Read on boot (in priority order)

1. THIS FILE (`paco_session_anchor_patch_cycle2_goliath.md`) — has all preflight + decisions
2. `paco_session_anchor.md` — running anchor; Day 79 evening state including Patch Cycle 1 close
3. `docs/feedback_paco_pre_directive_verification.md` — cumulative P6=37 SR=7 ledger; canonical source of truth for cumulative count; standing rules through #7; standing practices
4. `docs/paco_response_homelab_patch_cycle1_close_confirm.md` — Cycle 1 close-confirm; new SG canonical baseline; Path B B1+B2 ratification context; P6 #37 banking rationale
5. `docs/paco_review_homelab_patch_cycle1_cve_2026_31431.md` — PD's Cycle 1 review; Path B B1+B2 implementation details; nohup-to-tmpfile pattern reusable for Cycle 2 (584 packages = guaranteed >30s apt-get)
6. `docs/paco_directive_homelab_patch_cycle1_cve_2026_31431.md` — Cycle 1 directive; Cycle 2 directive should follow same skeleton with Goliath-specific corrections

---

## CEO ratifications (decisions pre-resolved before fresh session)

All 5 decisions surfaced + ratified during Day 79 evening session. Fresh-session Paco does NOT re-surface; proceeds directly to directive authoring with these baked in.

### Decision A: GPG key remediation strategy = A3 (do not touch workbench repo)

**Rationale:** apt-get update on Goliath returns expired-key error for `https://workbench.download.nvidia.com/stable/linux/debian` (signing key `EXPKEYSIG CD63F8B21266DE3C svc-workbench@nvidia.com`). However, apt has ALREADY excluded workbench packages from the 584 upgradable list (the GPG error blocks fetching the package index, so apt doesn't know what's upgradable there). The 584 we see are all from working-key repos. Cleanest path: leave workbench alone, address GPG key in a separate maintenance cycle. No risk of accidentally patching from an expired-key source.

**Implication for directive:** Section 0 directive corrections include a documented "workbench repo skipped this cycle; GPG key refresh tracked as separate maintenance" note. Pre-flight `apt-get update` will show the GPG warning — PD should treat as cosmetic-expected, NOT as a blocking error.

### Decision B: Container runtime patches = B3 (patch most, hold docker-compose-plugin v5)

**Rationale:** containerd 1.7.26→2.2.1 + docker-ce 28.3.3→29.2.1 + docker-buildx-plugin 0.26→0.31 are routine major-version-bump patches. **docker-compose-plugin 2.39.1→5.0.2 has known breaking config changes** (compose v5 syntax differences). Goliath isn't currently running production docker-compose stacks, but the v5 jump deserves explicit verification (test compose files; verify v5 parses them) which is bigger than this cycle's scope.

**Implication for directive:** Pre-patch step includes `sudo apt-mark hold docker-compose-plugin` to prevent the v5 jump. Post-patch verification confirms docker-compose-plugin remains at 2.39.1. v5 upgrade banked as separate maintenance cycle.

### Decision C: Reboot policy on dkms rebuild failure = C2 (verify-before-reboot)

**Rationale:** Goliath's whole purpose is large-model inference (Tesla T4 + CUDA + Ollama via routing layer). A reboot to a kernel without NVIDIA support takes Goliath offline for the time it takes to recover. Verify dkms status post-install; only reboot if dkms shows all modules built; abort+rollback otherwise.

**Implication for directive:** After kernel install, BEFORE reboot, run `dkms status` and verify all NVIDIA driver modules show `installed` for the new kernel `6.17.0-1014`. If any show `not installed` or rebuild errors — STOP, abort cycle, paco_request with dkms output. Do NOT proceed to reboot.

### Decision D: Ollama large-model inference quiesce-before-patch = D2 (explicit stop)

**Rationale:** Same maintenance-window-flip discipline as Beast atlas-agent in Cycle 1. Document as planned interruption.

**Implication for directive:** Pre-patch step includes `sudo systemctl stop ollama.service` (verify service name; may be `ollama.service` or different). Document as planned interruption. Post-reboot (after dkms verification), `systemctl start ollama.service` + verify with quick inference probe.

### Decision E: Per-node SG snapshot = E2 (spot-snapshot only; no canon SG addition)

**Rationale:** Goliath's role in canon SGs has not been ratified for general v0.1; adding mid-cycle is scope creep. Spot-check this cycle; consider full SG7 banking as a v0.1.1 question.

**Implication for directive:** Cycle 2 captures pre/post Goliath service inventory (ollama, nvidia-persistenced, any other GPU-related services) for THIS cycle's review only. New canonical SGs for Goliath are NOT canonized.

---

## P6 #37 blast-radius categorization (pre-staged from Day 79 evening preflight)

| Category | Examples | Risk | Pre-staged Path B verifications |
|---|---|---|---|
| **A. Kernel + NVIDIA HWE bundle** | linux-nvidia-hwe-24.04 6.11→6.17, linux-image-nvidia-hwe-24.04, linux-modules-nvidia-580-open-nvidia-hwe-24.04, linux-headers-nvidia-hwe-24.04, linux-tools-nvidia-hwe-24.04 | **CRITICAL** — major version jump, new kernel ABI for NVIDIA drivers | dkms rebuild for NVIDIA modules (verify BEFORE reboot per Decision C2); reboot-and-verify nvidia-smi; ollama service health post-reboot; CUDA libs intact |
| **B. CUDA toolkit 13.0.0 → 13.0.3 / 13.2.75** | cuda-command-line-tools-13-0, cuda-compiler-13-0, cuda-libraries-13-0, cuda-toolkit-13-0, cuda-cudart-*, etc. (~15 packages) | HIGH — minor CUDA version bump may break compiled-against-13.0.0 user apps | nvcc --version verify post-patch; CUDA sample app or simple ollama inference probe to confirm CUDA still functional |
| **C. Container runtime: Docker + containerd (PARTIAL per B3)** | docker-ce 28.3.3→29.2.1, containerd.io 1.7.26→2.2.1, docker-buildx-plugin 0.26→0.31 — INCLUDED. docker-compose-plugin 2.39.1→5.0.2 — HELD via apt-mark hold | **CRITICAL** for containerd 1→2 major API jump | docker daemon healthy post-upgrade; existing containers (if any running on Goliath) restart cleanly; runtime config compatibility; verify docker-compose-plugin stays at 2.39.1 |
| **D. Python3.12 (system Python)** | libpython3.12-*, python3-cryptography, python3-jwt, python3-ldb, python3-apt | LOW — minor patch versions; ABI-compatible | smoke-test `python3 --version`; basic Python imports |
| **E. NVIDIA workbench packages** | (BLOCKED by expired GPG key per Decision A3; NOT in 584 upgradable list) | EXCLUDED THIS CYCLE | n/a |
| **F. Ubuntu noble updates (rest)** | ~520 packages of standard Ubuntu LTS updates (libraries, command-line tools, etc.) | LOW per Ubuntu LTS update discipline | smoke-test critical commands post-patch |
| **G. Tailscale + standard tools** | (probe at directive author time; small count) | LOW | tailscale status verify post-patch |

**Total scope:** ~570 packages (584 minus ~14 docker-compose-plugin or related held packages).

**High-blast-radius categories requiring explicit pre-staged Path B verifications: A (kernel+driver) and C (container runtime).** Both must be in directive section 2.x with verify-before-reboot (A) and verify-after-patch (C) discipline.

---

## Goliath baseline state (probed Day 79 evening; verify at fresh-session boot probe before authoring)

```
Kernel:                6.11.0-1016-nvidia (NVIDIA-vendored aarch64; Ubuntu 24.04.3 LTS noble)
Uptime at probe:       2 days 23 hours
Users logged in:       3 (worth checking; others may be using Goliath)
No reboot pending:     /var/run/reboot-required absent
Disk root:             1.8T total, 1.5T free (ample for kernel install)
Disk /boot/efi:        511M total, 505M free
Upgradable packages:   584 (after Decision A3 apt-get update; workbench excluded)
Sudo:                  NOPASSWD jes
GPG repo error:        ai-workbench-desktop.sources signing key EXPKEYSIG (workbench excluded from 584; per Decision A3)
Unreachable PPAs:      3 Canonical NVIDIA PPAs at ppa.launchpadcontent.net (cosmetic; like Beast deadsnakes)
```

---

## Other live state to verify at boot probe

```
SlimJim kernel:      6.8.0-111-generic (post-Cycle-1)
Beast kernel:        5.15.0-177-generic (post-Cycle-1)
CK kernel:           5.15.0-177-generic (post-Cycle-1)
Goliath kernel:      6.11.0-1016-nvidia (PRE-CYCLE-2 baseline)

atlas-agent.service:    PID 4753 NRestarts 0 active enabled (post-Cycle-1 SG5)
atlas.tasks growth:     ~258 rows/hour sustained
Substrate anchors:      postgres+garage StartedAt 2026-05-03T18:38:24.* (post-Cycle-1 SG2/SG3)
mercury-scanner @ CK:   PID 7800 active (post-Cycle-1 SG6)
atlas-mcp:              PID 1212 active (post-Cycle-1 SG4)

P6 lessons:             37 (last bank: P6 #37 blast-radius categorization Day 79 evening)
Standing rules:         7 (last bank: SR #7 source-surface preflight Day 78 evening)
First-try streak:       8 (Phases 4-10 Atlas + Patch Cycle 1)
paco_request escalations: 0
```

---

## Three queues at anchor time

1. **Patch Cycle 2 (Goliath)** — NEXT (this anchor's purpose). Decisions A3/B3/C2/D2/E2 ratified; preflight done; directive authoring on fresh-session resume.
2. **Patch Cycle 3 (KaliPi+Pi3 non-kernel apt)** — lower-risk; 1559 KaliPi + 24 Pi3 packages without kernel paths. RPi kernel update is a separate cycle (rpi-update bypasses apt). Queued.
3. **P5 v0.1.1 credential rotation** — 18-credential queue (independent).
4. **Atlas v0.1.1 candidate list** — 9 items banked (see paco_response_atlas_v0_1_phase10_close_confirm.md). Suggest revisit ~Day 86 after a week of v0.1 production observation.

---

## What just happened (Day 79 session retrospective)

Day 79 was a marathon: shipped Atlas v0.1 (Phases 9 + 10 close-confirms; 11 of 11 phases COMPLETE; 7 consecutive first-try acceptance passes; SR #7 banked Phase 8 + validated Phases 9 & 10), then ran Patch Cycle 1 (SlimJim + Beast + CK Ubuntu kernel bumps; 11/11 acceptance PASS; 2 Path B ratified under SR #4; new canonical SG baseline established post-cycle; P6 #37 banked).

**Key discoveries that shape Cycle 2 directive authoring:**
- atlas-agent observation gap during Beast reboot was 9m04s (vs directive's 90-180s estimate). Root cause sound: server-class POST + initramfs + NVIDIA + dependency-chain startup. Goliath similar profile; expect 5-15min observation gap during Goliath reboot (longer due to 584 packages + larger NVIDIA stack init).
- nohup-to-tmpfile pattern (Path B B2 from Cycle 1) is REQUIRED for Cycle 2 — 584 packages will definitely exceed MCP 30s timeout on apt-get dist-upgrade.
- P6 #37 mandates blast-radius categorization. This anchor pre-stages it; fresh-session Paco builds directive section 0 with corrections + section 1 with verified-live block + section 2 with Path B pre-staging for categories A, C.

---

## Recommended fresh-session opening prompt

When Sloan returns to a fresh Paco session, paste at the top:

```
You are Paco. Read /home/jes/control-plane/paco_session_anchor_patch_cycle2_goliath.md and execute the boot probe. Then proceed directly to Patch Cycle 2 directive authoring — all 5 decisions (A3/B3/C2/D2/E2) are pre-ratified. Apply SR #7 source-surface preflight (verify the Day 79 evening preflight findings still hold; categorization is pre-staged in the anchor). Then dispatch directive to PD. CEO is Sloan; address as Sloan.
```

---

## Tool/schema notes

- homelab MCP tool schema: function definitions show `params`-wrapped (verified via current refresh). Server has historically alternated; first call confirms current enforcement — if validation error "params required", use wrap; if "params.params forbidden", use flat. Trust validation error feedback.
- MCP tunnel may go stale after long outages (e.g. CK reboot during Cycle 1 caused ~2.5min MCP outage; Claude Desktop tunnel needed manual restart to recover). If post-reboot tool calls hang on Goliath cycle, Claude Desktop restart on JesAir/Cortez may be needed.
- nohup-to-tmpfile pattern (from Cycle 1 Path B B2) for long apt-get under MCP 30s timeout: `nohup sudo DEBIAN_FRONTEND=noninteractive apt-get -y dist-upgrade > /tmp/cycle2_apt.log 2>&1 &` then poll `/tmp/cycle2_apt.log` size + grep for completion markers.

---

## Directive skeleton (fresh-session Paco fills in)

Follow Cycle 1 directive structure (`docs/paco_directive_homelab_patch_cycle1_cve_2026_31431.md`) as template. Cycle 2 specific sections:

- Section 0: 6 directive corrections including: (a) workbench repo GPG warning is cosmetic-expected per Decision A3; (b) docker-compose-plugin held via apt-mark per Decision B3; (c) verify-before-reboot dkms check per Decision C2; (d) ollama maintenance-window flip per Decision D2; (e) Goliath SGs are spot-only per Decision E2; (f) nohup-to-tmpfile mandatory for apt-get dist-upgrade.
- Section 1: SR #7 verified-live block (~15-20 rows; reuse Day 79 evening probe results + verify-still-current at fresh session)
- Section 2: Stage A pre-flight (apt-mark hold compose-plugin; ollama stop) + Stage B install (nohup apt-get; dkms verify; ABORT IF DKMS FAILS) + Stage C reboot + Stage D post-reboot (nvidia-smi; ollama start; verify CUDA; verify docker daemon; verify compose held at 2.39.1) + Stage E spot-SG snapshot Goliath services
- Section 3: 12-15 acceptance criteria covering all 7 categories
- Section 4: Cowork PD trigger prompt

**Estimated directive size:** 22-28KB (larger than Cycle 1's 17KB due to Goliath complexity).

---

## Final checklist for fresh-session Paco

At session start, after boot probe:
1. [ ] Verify all baseline values match (boot probe + git HEAD + SG values)
2. [ ] Verify Goliath kernel still 6.11.0-1016-nvidia (Cycle 2 hasn't accidentally happened)
3. [ ] Verify atlas-agent still PID 4753 NRestarts 0 (Beast hasn't been touched since Cycle 1)
4. [ ] Re-run apt list --upgradable on Goliath; confirm count is still ~584 (±10 acceptable)
5. [ ] Confirm CEO is at terminal and ready to dispatch PD when directive is committed
6. [ ] Author directive per skeleton above; commit + push; update paco_session_anchor.md change-log; provide CEO with PD trigger prompt
7. [ ] DO NOT execute Cycle 2 in Paco session; PD-executable per Decision F (continuing Cycle 1 pattern)

-- Paco (Day 79 evening; comprehensive Cycle 2 anchor for fresh-session resume)
