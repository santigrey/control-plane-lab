# paco_request_homelab_patch_cycle2_ppa_unreachable_blocks_kernel_modules

**To:** Paco | **From:** PD (Cowork) | **Date:** 2026-05-03 Day 79 late evening
**Status:** BLOCKED -- Stage B ABORT triggered per directive section 2.2 Stage B.3 ("STOP if any `E:` or `dpkg: error` lines appear")
**Tracks:** `docs/paco_directive_homelab_patch_cycle2_cve_2026_31431.md`
**Authority basis:** PD execution; directive Stage B.3 explicitly mandates STOP+paco_request on `E:` lines.

---

## 0. TL;DR

Stage B `apt-get -y dist-upgrade` aborted **before any unpack/install** with 4 fatal `E: Failed to fetch` errors + 1 `E: Unable to fetch some archives` summary. The PPA `ppa.launchpadcontent.net` (185.125.190.80) is **TCP/443 unreachable from both Goliath AND CK** -- confirmed not a Goliath-network-specific issue but an upstream Canonical/Launchpad infra outage (DNS resolves cleanly from both).

**2 of the 4 unfetchable packages are exactly the kernel-NVIDIA-modules packages required by Stage C verify-before-reboot ABORT gate.** They are PPA-binary-only with no alternate noble-updates mirror (the `+1000` ABI suffix is DGX-OS-specific).

System is at clean pre-Stage-B state: `dpkg --audit` + `dpkg -C` both exit 0; kernel still `6.11.0-1016-nvidia`; driver still `580.95.05`; modules still `6.11.0-1016.16+1000`; compose-plugin hold preserved; ollama.service inactive (Stage A.2 stop awaiting reverse).

**Directive Decision A3 / section 0.2(b) preflight gap:** characterized PPA as cosmetic ("already-installed packages unaffected"). This held for the **index** (`Ign:` lines = OK) but did NOT extend to **binary fetch** (`E:` lines = ABORT). Apt-simulation (row 5) succeeded because simulation uses cached package metadata, not the binary-fetch path.

---

## 1. Verified live (PD post-abort, 2026-05-03 ~22:19Z)

| # | Probe | Result |
|---|---|---|
| 1 | apt-get process endstate | `APT_DONE`; 5 `E:` lines at log lines 822-826 |
| 2 | dpkg state | `sudo dpkg --audit` exit 0; `sudo dpkg -C` exit 0 (clean pre-unpack abort) |
| 3 | Goliath kernel | `6.11.0-1016-nvidia` (UNCHANGED) |
| 4 | `linux-image-nvidia-hwe-24.04` | `ii 6.11.0-1016.16` (UNCHANGED) |
| 5 | `linux-modules-nvidia-580-open-nvidia-hwe-24.04` | `ii 6.11.0-1016.16+1000` (UNCHANGED) |
| 6 | `libnvidia-compute-580` | `ii 580.95.05-0ubuntu0.24.04.2` (UNCHANGED) |
| 7 | `apt-mark showhold` | `docker-compose-plugin` (Stage A.1 hold preserved) |
| 8 | `ollama.service` | `inactive` (Stage A.2 stop, not yet restored) |
| 9 | Goliath PPA TCP/443 | `TCP_FAIL` via `</dev/tcp`; `curl --max-time 5` returned no headers |
| 10 | CK PPA TCP/443 | `TCP_FAIL` via `</dev/tcp` (cross-host confirms upstream outage) |
| 11 | DNS resolution | `185.125.190.80` (resolves OK from both) |
| 12 | apt log | 826 lines; 5 `E:` lines (lines 822-826); ~2965 MB fetched before failure |

**12 forensic rows. System state: clean pre-Stage-B baseline + Stage A.1 hold + Stage A.2 ollama-stopped.**

---

## 2. The 4 unfetchable packages

| Pkg | PPA path | Stage C role |
|---|---|---|
| `linux-modules-nvidia-580-open-nvidia-hwe-24.04_6.17.0-1014.14+1000` | `canonical-nvidia/nvidia-desktop-edge / linux-restricted-modules-nvidia-6.17` | **CRITICAL -- Stage C.1 meta package; required for verify gate** |
| `linux-modules-nvidia-580-open-6.17.0-1014-nvidia_6.17.0-1014.14+1000` | `canonical-nvidia/nvidia-desktop-edge / linux-restricted-signatures-nvidia-6.17` | **CRITICAL -- Stage C.1 version-pinned package; provides the .ko files for Stage C.2** |
| `libvulkan1_1.4.328.1-1~1` | `canonical-nvidia/vulkan-packages-nv-desktop / vulkan-loader` | non-critical (Vulkan loader; affects Vulkan workloads, NOT Ollama/CUDA) |
| `wpasupplicant_2.11-0ubuntu5~24.04.1` | `canonical-nvidia/nvidia-desktop-edge / wpa` | non-critical (Wi-Fi supplicant; Goliath is wired) |

The first two cannot be substituted from any other source. They are version-pinned to the kernel ABI `6.17.0-1014.14+1000`.

---

## 3. Why directive A3 / 0.2(b) didn't catch this

Decision A3 + section 0.2(a)(b) characterized PPA timeouts as cosmetic, citing the analogue of Beast's deadsnakes PPA in Cycle 1 where "already-installed packages from these PPAs are unaffected." That framing held for the **index** (`Ign:` lines = OK) but did NOT extend to **binary fetch** (`E:` lines = ABORT).

Cycle 1 Beast deadsnakes was index-only: python3.11 was already installed; no new package needed fetching from deadsnakes. Cycle 2 Goliath canonical-nvidia is different: the kernel-NVIDIA-modules upgrade specifically requires NEW binaries from this PPA (the `+1000` ABI suffix is DGX-OS-specific and not on noble-updates).

Paco preflight row 5's `apt-get -s dist-upgrade` succeeded because simulation uses cached package metadata, not the binary-fetch path.

This is a directive-level gap, not a PD execution error. **PD-proposed P6 #38:** binary-fetch reachability probe required when upgrade scope includes PPA-only packages. Specifically: for each unique source URL contributing to the upgradable set, run `curl --max-time 5 -sI <source>/dists/<dist>/InRelease` AND `apt-get download --print-uris <pkg> | head -1 | xargs curl --max-time 5 -sI` to verify both index AND binary-fetch paths. Natural extension of P6 #37 (blast-radius categorization).

---

## 4. Path forward options

**Option 1 (PD recommended):** Hold position; wait for PPA reachability; retry Stage B when PPA recovers.
- Pros: zero risk; preserves cycle plan as-is
- Cons: indeterminate wait; Goliath production inference remains stopped (unless ollama is restored decoupled from cycle; see ask #2)
- Mitigation: PD probes PPA hourly via `timeout 5 bash -c '</dev/tcp/ppa.launchpadcontent.net/443'`; on first TCP_OK, notify Sloan + request authorization to retry Stage B.1

**Option 2:** Continue with `apt-get -y dist-upgrade --fix-missing`.
- **DO NOT PURSUE.** Would install kernel 6.17 WITHOUT matching NVIDIA modules -> Stage C verify gate would mandatorily ABORT -> leaves system with 6.17 installed alongside 6.11 -> risk of accidental boot into 6.17 with no GPU. Unsafe.

**Option 3:** Fetch the 4 packages via alternate route.
- No alternate canonical mirror exists for the +1000 ABI variants. Pre-cached copy on LAN unlikely; haven't checked. Proxy through Tailscale to a different egress unlikely to help (same upstream infra).

**Option 4:** Defer kernel + driver + container-runtime updates; restrict Cycle 2 to non-PPA packages only.
- Requires: (a) probe to enumerate non-PPA packages in the 581+26 set, (b) new directive scoped to that subset, (c) preserves CVE-2026-31431 partial mitigation but NOT kernel CVE coverage.
- Larger preflight + reduced security value. Defer kernel/driver to Cycle 2.5 once PPA returns.

**Option 5:** Defer Cycle 2 entirely until PPA returns; advance Cycle 3 (KaliPi/Pi3) or other queues meanwhile.

---

## 5. Asks for Paco

1. **Confirm Option 1 (hold + wait for PPA).** Or specify alternative path (2/3/4/5).
2. **Authorize ollama.service restore now.** PD recommendation: yes -- Goliath production inference shouldn't sit idle while waiting on Canonical PPA infra. Restarting ollama is pure baseline restore (no cycle progress).
3. **Compose-plugin hold:** PD recommendation: **keep** -- hold is harmless and saves a step on Stage B retry.
4. **Cadence for PPA reachability re-check.** Suggest: PD probes hourly via `timeout 5 bash -c '</dev/tcp/ppa.launchpadcontent.net/443'`; on first TCP_OK, notify Sloan + request authorization to retry Stage B from launch (B.1).
5. **P6 #38 banking.** PD-proposed: "PPA binary-fetch reachability probe required when upgrade scope includes PPA-only packages." Natural extension of P6 #37. See section 3.

---

PD standing by. No further actions taken without Paco direction.

-- PD
