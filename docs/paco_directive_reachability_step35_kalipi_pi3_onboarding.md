# paco_directive_reachability_step35_kalipi_pi3_onboarding

**To:** CEO (Sloan) | **From:** Paco | **Date:** 2026-05-02 Day 78 mid-day
**Authority:** Reachability cycle Step 3 closed (paco_response commit `cbb316e`); Option A user policy ratified Day 78 mid-day; Step 3.5 GO.
**Status:** ACTIVE — CEO playbook for KaliPi + Pi3 onboarding + MCP `HOST_USERS` update.
**Tracks:** `docs/homelab_reachability_v1_0.md` reachability cycle Step 3.5 (canon §3.5 amended this commit per pre-directive verification corrections).
**Bundled:** patch cycle Step 1 kernel + sudo probe (KaliPi + Pi3) — already gathered during Paco pre-directive verification this session; recorded in §Verified live below; no separate CEO action needed.

---

## Background

Reachability cycle Step 3.5: onboard `jes` user on KaliPi + Pi3 with NOPASSWD sudo + canonical ssh keys + canonical `/etc/hosts`, then update MCP server `HOST_USERS` so PD reaches both nodes as `jes` from Step 4 onward. CEO at terminal (or via SSH from Cortez); per-step CEO authorization to Paco between sub-steps remains the rule.

## Verified live (2026-05-02 Day 78 mid-day, Paco pre-directive)

### KaliPi (192.168.1.254 as `sloan`)

| Probe | Output |
|---|---|
| `whoami` | `sloan` |
| `uname -r` | `6.12.34+rpt-rpi-2712` |
| `cat /etc/os-release \| grep PRETTY_NAME` | `Kali GNU/Linux Rolling 2025.4` |
| `sudo -n true; echo $?` | `1` (password required for sloan) |
| `id jes` | `no such user` (no useradd conflict) |
| `getent group sudo` | `sudo:x:27:kali,sloan` |
| `ls /home/` | `kali sloan` (no jes home) |
| `systemctl is-active cloud-init.service` | `inactive` |
| `systemctl list-unit-files 'cloud*'` | all enabled but currently inactive |
| `stat /etc/hosts` mtime | `2025-11-17 11:56:11` (5+ months old; many boots since) |
| `grep manage_etc_hosts /etc/cloud/cloud.cfg` | (no match; only template files contain it) |
| `ls /etc/sudoers.d/` | permission denied (sudo+password required) |

**Key conclusion:** cloud-init exists but is dormant. `/etc/hosts` is empirically static across reboots (mtime stale despite uptime cycles). Drop-in disable is belt-and-suspenders against future cloud-init reset/clean, not a real necessity for current behavior.

### Pi3 (192.168.1.139 as `sloanzj`)

| Probe | Output |
|---|---|
| `hostname` | `PI3` |
| `whoami` | `sloanzj` |
| `uname -r` | `6.12.75+rpt-rpi-v8` |
| `cat /etc/os-release` | `Debian GNU/Linux 13 (trixie)` |
| `sudo -n true; echo $?` | `0` (NOPASSWD sudo) |
| `id jes` | `no such user` |
| `ls /home/` | `sloanzj` only |

**Key conclusion:** Pi3 already has NOPASSWD sudo. Cloud-init state TBD — Sloan probes at Phase B.0 (`systemctl is-active cloud-init.service`); apply drop-in for canon parity if cloud-init is present.

### MCP server config (CK `/home/jes/control-plane/mcp_server.py`)

| Setting | Current | Target |
|---|---|---|
| `ALLOWED_HOSTS["kalipi"]` | `192.168.1.254` | unchanged (already correct) |
| `ALLOWED_HOSTS["pi3"]` | `192.168.1.139` | unchanged (already present — corrects earlier "not in allowed-host list" assumption) |
| `HOST_USERS["kalipi"]` | `sloan` | `jes` (after Phase A complete) |
| `HOST_USERS["pi3"]` | `sloanzj` | `jes` (after Phase B complete) |
| `homelab-mcp.service` | active running, MainPID 31842 | restart at end of Phase C |

### CK canonical outbound public key

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKk48m0m/IUkVfy/8ErpRsCIfrp5qivanpuXCTDCudwL jes@sloan3
```

Bootstraps both KaliPi and Pi3 jes user `authorized_keys` (Phase A.3 + B.3). Comment-suffix canonicalization (`jes@sloan3-canonical`) deferred to Step 4 authorized_keys policy enforcement.

### Canon-hygiene exposure flagged (P6 #34, NOT in scope for this directive)

`mcp_server.py` line 25 contains a literal `DB_PASS` assignment exposing the P5-class weak credential. Updates the canon-hygiene exposure inventory: 17 known total → 18 known total (the +1 is this finding). Forward-redaction discipline applies (P6 #34): no new references to the credential VALUE; rotation is the cure (P5 v0.1.1 cycle). Phase C edits target lines 41 + 43 (HOST_USERS) only — line 25 is untouched and not introduced by this commit.

## Procedure

CEO executes one phase at a time. Per-phase CEO authorization to Paco between phases (chat: "Phase X done"). Paco surfaces one command at a time during execution per Sloan's preferences.

### Phase A — KaliPi onboarding (CEO at SSH session: `ssh sloan@192.168.1.254` from Cortez or LAN)

- **A.0** Pre-state confirmation (kernel + sudoers.d existence + cloud-init status; sudo+password as needed)
- **A.1** `sudo useradd -m -s /bin/bash jes` + verify `id jes`
- **A.2** `sudo usermod -aG sudo jes` + write `/etc/sudoers.d/99-jes-nopasswd` + `sudo visudo -c`
- **A.3** Install CK canonical pub key in `/home/jes/.ssh/authorized_keys` (mode 0600; parent dir 0700; owner jes:jes)
- **A.4** Cloud-init defensive drop-in: `/etc/cloud/cloud.cfg.d/99-disable-managed-hosts.cfg` containing `manage_etc_hosts: false`
- **A.5** Install canonical `/etc/hosts` via Step 3 marker-block Python heredoc (with `sudo cp /etc/hosts /etc/hosts.bak.<ts>` first)
- **A.6** Verify locally + verify CK→jes@kalipi passwordless ssh (Sloan SSHes from CK to kalipi as jes)

### Phase B — Pi3 onboarding (CEO at SSH session: `ssh sloanzj@192.168.1.139` from Cortez or LAN)

- **B.0** Pre-state confirmation (cloud-init status check: `systemctl is-active cloud-init.service`; sudoers.d ls)
- **B.1** `sudo useradd -m -s /bin/bash jes` + verify `id jes`
- **B.2** `sudo usermod -aG sudo jes` + write `/etc/sudoers.d/99-jes-nopasswd` + `sudo visudo -c`
- **B.3** Install CK canonical pub key in `/home/jes/.ssh/authorized_keys` (mode 0600; 0700; jes:jes)
- **B.4** Cloud-init defensive drop-in (only if cloud-init present per B.0; otherwise skip with rationale logged)
- **B.5** Install canonical `/etc/hosts` via Step 3 marker-block Python heredoc
- **B.6** Verify locally + verify CK→jes@pi3 passwordless ssh

### Phase C — MCP server `HOST_USERS` update (CEO on CK as `jes`)

- **C.0** Backup `mcp_server.py` to `mcp_server.py.bak.<ts>`
- **C.1** Edit lines 41 + 43: `"kalipi": "sloan"` → `"kalipi": "jes"`; `"pi3": "sloanzj"` → `"pi3": "jes"` (sed acceptable for 2-line change)
- **C.2** Diff-only secrets-scan (broad + tightened) on the staged changes — verify the diff introduces zero credential VALUES (the pre-existing `DB_PASS` assignment on line 25 (P5-class credential) is not part of the diff; not introduced by this commit)
- **C.3** Commit + push (commit message acknowledges the canon-hygiene exposure inventory bump)
- **C.4** `sudo systemctl restart homelab-mcp.service` + `systemctl is-active homelab-mcp.service`

**Note on restart blip:** Paco's `homelab_ssh_run` tool calls may briefly fail during the service restart (~few seconds). CEO chat messages over Anthropic transport are unaffected; only homelab-MCP-tunneled tool calls. Sloan reports "Phase C done" in chat; Paco retries verification probes.

### Phase D — Paco close-confirm

- **D.1** Paco verifies via `homelab_ssh_run host=kalipi command='whoami; uname -r; sudo -n true && echo OK'` → expect `jes / 6.12.34+rpt-rpi-2712 / OK`
- **D.2** Paco verifies via `homelab_ssh_run host=pi3 command='whoami; uname -r; sudo -n true && echo OK'` → expect `jes / 6.12.75+rpt-rpi-v8 / OK`
- **D.3** Paco verifies canonical /etc/hosts on both via `getent hosts ciscokid sloan3 beast sloan2 ...`
- **D.4** Paco writes `docs/paco_response_reachability_step35_close_confirm.md`
- **D.5** Anchor amend: Step 3.5 [~] → [x]
- **D.6** Next-step decision surfaced: reachability Step 4 (PD-executable now), or pivot per CEO direction

## Acceptance per phase

- **Phase A:** `ssh jes@kalipi 'whoami; sudo -n true && echo OK'` from CK returns `jes / OK` passwordlessly.
- **Phase B:** `ssh jes@pi3 'whoami; sudo -n true && echo OK'` from CK returns `jes / OK` passwordlessly.
- **Phase C:** `homelab_ssh_run host=kalipi command='whoami'` returns `jes`; same for `pi3`.

Any phase acceptance fail → STOP + paco_request + CEO ratifies recovery.

## Rollback

- Each phase is additive: jes user creation does not modify existing users; old user (`sloan`/`sloanzj`) untouched on each node.
- `/etc/hosts.bak.<ts>` created before edit on each node.
- `mcp_server.py.bak.<ts>` created before Phase C edit; Phase C also commits to git, so `git revert` is the canonical revert path.
- Sudoers.d drop-in: `sudo rm /etc/sudoers.d/99-jes-nopasswd` to revert NOPASSWD; `sudo gpasswd -d jes sudo` to remove from sudo group; `sudo userdel -r jes` to remove jes entirely.

## Discipline reminders

- One command at a time. CEO authorizes each next sub-step explicitly via chat.
- Pre-directive verification discipline applies to Pi3 cloud-init state — Sloan probes at B.0 before applying B.4.
- mcp_server.py line 25 (the `DB_PASS` assignment, P5-class credential) is a pre-existing exposure, not introduced by this commit. Do not redact in this commit; rotation cycle (P5 v0.1.1) handles.
- Phase C diff-only secrets-scan vs full-file scan distinction matters here: full-file would hit line 25; diff-only correctly scopes to changes-being-introduced.
- After Phase C restart, the homelab-mcp tool docstring still says only 7 hosts (cosmetic stale; functionally accepts pi3 already and now points kalipi at jes). Optional Step 4 cleanup task: update the docstring at line 67 + 99 to include pi3.

-- Paco
