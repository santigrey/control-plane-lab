# Mr Robot Backlog v1.0

**Owner:** Mr Robot (Charter 7 Security; sub-agent not yet built; v0.2 candidate per Charters v0.2 Day 77)
**Maintained by:** Paco at CEO direction; CEO and PD can append items
**Status:** OPEN -- accumulating items pre-Mr-Robot-build
**Created:** 2026-05-02 Day 78 morning per CEO directive

---

## Note on operational urgency vs Mr Robot scope

Items in this backlog have two lifecycles:

1. **Operational lifecycle (now):** items with active exploit risk get handled NOW by CEO + PD without waiting for Mr Robot build. Backlog records the work + outcome.
2. **Mr Robot lifecycle (future):** when Mr Robot is built (v0.2 cycle), it inherits all OPEN items. Mr Robot SOP at `docs/mr_robot_sop_v1_0.md` covers scope.

No backlog item is allowed to be 'deferred until Mr Robot exists' if it has active exploit risk. The backlog is a record of the work, not a queue for the unbuilt.

---

## Job #1 -- CVE-2026-31431 ('Copy Fail') Linux kernel local privilege escalation

**Logged:** 2026-05-02 Day 78 morning per CEO directive (Alexandra-sourced via web search; PD or Mr Robot to verify against Ubuntu USN + NVD before patch operation)
**Priority:** P0 -- active exploit; public PoC; affects entire fleet
**Disclosure date:** 2026-04-29 (public)
**Status:** PENDING patch cycle -- not yet executed; CEO + PD coordinate

### Vulnerability summary (CEO-provided; verify before action)

- **CVE:** CVE-2026-31431
- **Name:** Copy Fail
- **Type:** Local privilege escalation (LPE)
- **Mechanism:** Abuses AF_ALG + splice mechanisms to corrupt page cache of setuid binaries -> root
- **Affected:** Linux kernels since 2017 (~4.14 onwards); all major distros
- **Exploit:** 732-byte public PoC available; consistently grants root
- **Severity per sources:** High / Critical

### Sources to verify against before action

1. NVD: https://nvd.nist.gov/vuln/detail/CVE-2026-31431 (authoritative)
2. Ubuntu USN advisory: https://ubuntu.com/blog/copy-fail-vulnerability-fixes-available
3. Rocky Linux discussion: https://forums.rockylinux.org/t/cve-2026-31431-copy-fail-linux-kernel-crypto-vulnerability/20375
4. Sesame Disk write-up: https://sesamedisk.com/linux-vulnerability-cve-2026-31431-security/
5. The Hacker News: https://thehackernews.com/2026/04/new-linux-copy-fail-vulnerability.html

### Fleet exposure (verified live Day 78 morning)

| Node | IP | Kernel | Distro | Patch status |
|---|---|---|---|---|
| CiscoKid | 192.168.1.10 | 5.15.0-176-generic | Ubuntu 22.04.5 LTS | PENDING |
| TheBeast | 192.168.1.152 | 5.15.0-176-generic | Ubuntu 22.04.5 LTS | PENDING |
| SlimJim | 192.168.1.40 | 6.8.0-110-generic | Ubuntu 24.04.4 LTS | PENDING |
| KaliPi | 192.168.1.254 | not probed (sloan-user; jes-key declined) | Kali Linux | PENDING -- CEO probe |
| Goliath | 192.168.1.20 | 6.11.0-1016-nvidia | Ubuntu 24.04.3 LTS | PENDING |
| Mac mini | 192.168.1.13 | not probed (SSH timed out) | macOS | NOT applicable (Linux-only CVE) |
| JesAir | 192.168.1.155 | not probed | macOS | NOT applicable |
| Cortez | TS 100.70.77.115 | n/a | Windows | NOT applicable |
| Pi3 | 192.168.1.139 / TS 100.71.159.102 | not probed | Debian 13 aarch64 | PENDING -- CEO probe |

Five Linux nodes confirmed VULNERABLE pending patch (kernels in affected range 4.14+); two more (KaliPi, Pi3) need probe; three macOS/Windows nodes are out of scope.

### Action plan (operational, NOT waiting for Mr Robot build)

This item executes BEFORE Mr Robot is built. Sequencing:

1. **CEO authorization:** confirm patching cycle authorized (kernel update + reboot per node).
2. **Patch order (least-risk first, high-impact last):**
   - Probe KaliPi + Pi3 kernel versions (CEO runs `uname -r` on each)
   - SlimJim (edge node; lowest service density)
   - KaliPi (pentesting; isolated)
   - Pi3 (DNS gateway TBD; check service criticality)
   - Goliath (model inference; has uptime impact for Atlas + Mercury via model calls)
   - TheBeast (atlas-mcp.service + atlas Postgres replica + Garage anchor) -- coordinate reboot with Atlas + substrate anchor preservation
   - CiscoKid (orchestrator + Mercury + nginx + canonical Postgres) -- last; biggest blast radius
3. **Standard Ubuntu kernel-patch procedure (per memory P5 lesson):** `sudo apt-get update && sudo apt-get dist-upgrade && sudo reboot` (NOT `apt-get upgrade` -- doesn't pull kernel meta-package; per memory)
4. **Anchor preservation:** Beast reboot WILL break B2b + Garage anchor StartedAt timestamps -- this is unavoidable for kernel patch. Document the new anchors as the post-patch baseline. Standing Gate 1+2 reset -- expected and acceptable.
5. **Monitoring:** Atlas Domain 1 infrastructure monitoring (Phase 3, live) will detect post-reboot service uptime + anchor drift. Treat as expected-event during patch window.
6. **Verification per node post-patch:**
   - `uname -r` confirms new kernel
   - `systemctl is-active` for each homelab service
   - For Beast: atlas-mcp.service comes back up; Postgres + Garage containers restart with new anchors
   - For CK: orchestrator + Mercury + nginx + Postgres all healthy

### Mr Robot inheritance

When Mr Robot is built (v0.2 cycle), it inherits this entry transitioned to:
- Continuous CVE feed monitoring (NVD + Ubuntu USN + Rocky + Debian advisories)
- Per-node kernel version tracking + drift alerts
- Auto-flag when fleet runs >N days behind upstream patch
- Emergency Tier 3 alert on any new P0 CVE disclosure affecting fleet kernel range

Mr Robot SOP Section 3 (Vulnerability monitoring) and Section 5 (Patch hygiene) will own this workflow.

### Tracking

- Status here updates as nodes patch (PENDING -> IN PROGRESS -> PATCHED <kernel-version> <date>)
- CHECKLIST audit entry added when patching cycle executes
- Final closure when all 5+ Linux nodes confirmed running patched kernel + verified via `uname -r` + Mr Robot can take over monitoring at build time

---

## Future job slots (placeholder)

- #2 -- (open)
- #3 -- (open)
- ...

---

## Update protocol

- CEO appends new items at any time
- Paco appends at CEO direction or when discovering security-relevant items in cycle work
- PD appends if discovering security gaps during build cycles
- Mr Robot inherits ownership when v0.2 cycle starts; until then, items execute via CEO + PD coordination

-- Paco (initial author)
