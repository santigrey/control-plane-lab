# paco_response_reachability_step35_close_confirm

**To:** CEO (Sloan) | **From:** Paco | **Date:** 2026-05-02 Day 78 mid-day (post-Phase-D)
**Authority basis:** Step 3.5 directive `docs/paco_directive_reachability_step35_kalipi_pi3_onboarding.md` (HEAD `a6616bc`); Phase C commit `5517775` (mcp_server.py HOST_USERS update); CEO interactive execution Phase A/B/C; Paco verification Phase D.
**Status:** STEP 3.5 CLOSE-CONFIRMED — 6/6 phases PASS (A.0 through D verified); standing gates 5/5 bit-identical; zero `paco_request` escalations.
**Tracks:** `docs/homelab_reachability_v1_0.md` reachability cycle Step 3.5

---

## Verified live (2026-05-02 Day 78 mid-day, post-Phase-D)

### Cross-node SSH as `jes` (acceptance gate)

| Verification | Probe | Output |
|---|---|---|
| CK → jes@kalipi via direct ssh | `ssh -i /home/jes/.ssh/id_ed25519 jes@192.168.1.254 'whoami; uname -r; sudo -n true && echo OK'` | `jes / 6.12.34+rpt-rpi-2712 / OK` (passwordless, NOPASSWD sudo) |
| CK → jes@pi3 via direct ssh | `ssh -i /home/jes/.ssh/id_ed25519 jes@192.168.1.139 'whoami; hostname; sudo -n true && echo OK'` | `jes / PI3 / OK` |
| MCP → kalipi via homelab_ssh_run | `homelab_ssh_run host=kalipi 'whoami'` | `jes` (HOST_USERS mapping live) |
| MCP → pi3 via homelab_ssh_run | `homelab_ssh_run host=pi3 'whoami'` | `jes` (HOST_USERS mapping live) |

### Per-node post-state

| Node | jes uid | NOPASSWD sudo | Authorized_keys | /etc/hosts canonical block | Cloud-init drop-in |
|---|---|---|---|---|---|
| KaliPi | 1005 | yes (`/etc/sudoers.d/99-jes-nopasswd`, mode 440, visudo-validated) | mode 600 jes:jes; CK canonical pub key byte-exact | 889 bytes; 1× BEGIN/END marker; backup `/etc/hosts.bak.20260502-180424` | `/etc/cloud/cloud.cfg.d/99-disable-managed-hosts.cfg` (mode 644 root:root, 24 bytes) |
| Pi3 | 1001 | yes (`/etc/sudoers.d/99-jes-nopasswd`, mode 440, visudo-validated) | mode 600 jes:jes; CK canonical pub key byte-exact | 863 bytes; 1× BEGIN/END marker; backups `.bak.20260502-182120` (Paco) + `.bak.20260502-182258` (CEO retry) | `/etc/cloud/cloud.cfg.d/99-disable-managed-hosts.cfg` (mode 644 root:root, 24 bytes) |

### MCP server config (post-Phase-C)

| Setting | Pre | Post | Effect |
|---|---|---|---|
| `HOST_USERS["kalipi"]` | `sloan` | `jes` | PD now reaches KaliPi as jes (NOPASSWD) |
| `HOST_USERS["pi3"]` | `sloanzj` | `jes` | PD now reaches Pi3 as jes (NOPASSWD) |
| `homelab-mcp.service` MainPID | 31842 | 1640430 | Restarted at `Sat 2026-05-02 18:37:13 UTC` |
| Commit | n/a | `5517775` | 1 file changed, 2 insertions, 2 deletions; pushed to origin/main |
| Diff-only secrets-scan | broad + tightened | both PASS-no-matches | Zero credential VALUES in diff (line 25 P5-class credential pre-existing, not in scope) |

## Standing gates pre/post snapshot

| Gate | Subject | Step 3.5 pre | Step 3.5 post | Verdict |
|---|---|---|---|---|
| 1 | B2b anchor (`control-postgres-beast`) | StartedAt `2026-04-27T00:13:57.800746541Z`; running; restart=0 | StartedAt `2026-04-27T00:13:57.800746541Z`; running; restart=0 | bit-identical (96h+) |
| 2 | Garage anchor (`control-garage-beast`) | StartedAt `2026-04-27T05:39:58.168067641Z`; running; restart=0 | StartedAt `2026-04-27T05:39:58.168067641Z`; running; restart=0 | bit-identical (96h+) |
| 4 | atlas-mcp.service (Beast) | MainPID 2173807, active running | MainPID 2173807, active running | unchanged |
| 5 | atlas-agent.service (Beast) | MainPID 0, inactive disabled (Phase 1 acceptance state) | MainPID 0, inactive disabled | unchanged |
| 6 | mercury-scanner.service (CK) | MainPID 643409, active | MainPID 643409, active | unchanged |

**Verdict:** Standing Gates 5/5 PRESERVED. Step 3.5 was read-only on standing-gate services. Only `homelab-mcp.service` changed (intentional Phase C restart); not part of standing-gate set.

## Per-phase close-confirm

- **Phase A (KaliPi):** A.0 pre-state verified → A.1 jes uid=1005 created → A.2 sudo group + NOPASSWD drop-in (visudo OK) → A.3 ssh key bootstrap (mode 700/600 jes:jes) → A.4 cloud-init drop-in → A.5 canonical /etc/hosts marker block (Python heredoc successful first-try) → A.6 CK→jes@kalipi passwordless ssh + NOPASSWD sudo verified. **PASS.**
- **Phase B (Pi3):** B.0 verified by Paco (NOPASSWD sudo, no jes user, dormant cloud-init) → B.1 jes uid=1001 created → B.2 sudo group + drop-in (visudo OK) → B.3 ssh key bootstrap → B.4 cloud-init drop-in → B.5 canonical /etc/hosts: first attempt failed (bracketed-paste artifacts on bash; see Discipline observations); Paco re-ran via homelab_ssh_run — PASS; CEO retry second-attempt also succeeded idempotently (additive `.bak` only, byte-zero net change to /etc/hosts) → B.6 CK→jes@pi3 passwordless ssh verified. **PASS.**
- **Phase C (MCP HOST_USERS):** C.0 backup `mcp_server.py.bak.20260502-182638` → C.1 `sed -i` lines 41 + 43 → C.2 grep + diff verified (2 lines changed, no collateral) → C.3a stage + diff-only secrets-scan (broad + tightened both PASS) → C.3b commit `5517775` + push to origin/main → C.4 restart `homelab-mcp.service` (MainPID 31842 → 1640430). **PASS.**
- **Phase D (Paco verification):** Brief MCP tunnel staleness post-restart (~4 min until reconnect; CEO interactively verified Phase D acceptance gate from CK terminal in the meantime: both nodes return `jes / hostname / OK`) → MCP reconnected; Paco re-verified via homelab_ssh_run as jes on both nodes → standing gates re-checked. **PASS.**

## Patch cycle Step 1 banked (bundled into Step 3.5 verification)

Kernel + sudo capability now known for KaliPi + Pi3 under post-onboarding `jes` user (the user PD will use for patching):

| Node | Kernel | OS | Sudo as jes |
|---|---|---|---|
| KaliPi | `6.12.34+rpt-rpi-2712` | Kali GNU/Linux Rolling 2025.4 | NOPASSWD |
| Pi3 | `6.12.75+rpt-rpi-v8` | Debian GNU/Linux 13 (trixie) | NOPASSWD |

Patch cycle Step 1 (`docs/paco_directive_homelab_patch_cycle_cve_2026_31431.md`) is materially complete; remaining patch-cycle steps (Step 2 SlimJim onward) are now PD-executable when authorized.

## Discipline observations (P6 candidate)

**Bracketed-paste vs heredoc on bash terminals (P6 #35 candidate).** Phase B.5 first-attempt heredoc failed on Pi3 because the bash shell did not strip bracketed-paste markers (`^[[200~`, `^[[201~`) sent by the CEO's terminal emulator. KaliPi's zsh stripped them silently; Pi3's bash did not, and the leading `^[[200~sudo` was interpreted as an unknown command. Mitigation paths exercised:
- Paco re-ran the heredoc via `homelab_ssh_run` (paste-bypass via MCP transport).
- CEO retried interactively second-attempt; succeeded (terminal/shell state had reset).

**Lesson statement (for future P6 banking):** When authoring a CEO-playbook directive (vs PD-executable directive), heredocs are paste-fragile across shell+terminal combinations. Mitigation patterns: (a) prefer single-line commands wrapped via `bash -c '...'` over heredocs; (b) when multi-line is unavoidable, dispatch via `homelab_ssh_run` from Paco-side (paste-bypass); (c) document a one-time terminal-side bracketed-paste disable (`printf '\e[?2004l'`) for the CEO to type before the paste.

Formal P6 #35 banking will land in a follow-up canon-hygiene amendment (separate commit) per measure-twice discipline; surfaced here for transparency.

**MCP tunnel staleness post-service-restart.** Phase C.4 restart of `homelab-mcp.service` invalidated the persistent MCP-bridge connection on Cortez. Paco's `homelab_ssh_run` calls timed out (~4 min) until the bridge auto-reconnected. CEO's chat path (Anthropic transport, independent of homelab-mcp) was unaffected throughout. CEO's terminal SSH (Cortez → CK) was also unaffected. Mitigation: CEO performed Phase D acceptance verification from CK terminal during the gap; Paco resumed verification once MCP reconnected. **No new P6 lesson** — expected behavior; the MCP-bridge reconnects automatically; the Phase C directive predicted this caveat.

## Step 6 audit queue (carried forward)

Prior items from Step 3 close-confirm remain queued. New items from Step 3.5:

1. KaliPi `/etc/hosts` retains the misleading cloud-init "manage_etc_hosts: True" comment block at the top — cosmetic only; harmless residue. Step 6 cleanup decision: strip the comment OR leave as historical context.
2. Pi3 `/etc/hosts` same as above.
3. KaliPi `127.0.1.1 kali-raspberrypi kali-raspberrypi` (template hostname duplication) — cosmetic; harmless. Step 6 may leave as-is.
4. Pi3 `127.0.1.1 PI3 PI3` (uppercase hostname; template artifact) — cosmetic; case-insensitive resolution makes it functionally fine. Step 6 may canonicalize to lowercase.
5. CK known_hosts gained two new entries (kalipi LAN-name, pi3 LAN-name) via `accept-new` first-contact during verification. Step 6 may audit for entry hygiene.

## Anchor + canon updates queued (this commit)

- `paco_session_anchor.md`: Step 3.5 [~] → [x]; last-updated bumped.
- `docs/homelab_reachability_v1_0.md`: no further structural amendments needed (this cycle landed against the amended canon §3.5).
- (Deferred to follow-up commit) `docs/feedback_paco_pre_directive_verification.md`: P6 #35 banking (bracketed-paste hazard).

## Next step

Three active queues:

1. **Reachability cycle continues** — Step 4 (push canonical `~/.ssh/config` + `authorized_keys` to all 9 devices). PD-executable now (KaliPi + Pi3 both reachable as jes via homelab_ssh_run). Paco-authored directive expected when CEO authorizes.
2. **CVE-2026-31431 patch cycle** — Step 1 effectively complete (banked above); Step 2 onward PD-executable when CEO authorizes. Could run in parallel with reachability Step 4 if desired (different services, no overlap).
3. **Atlas v0.1 Phase 7** — still queued behind reachability cycle close (Step 6).

CEO direction needed on which queue advances next.

-- Paco
