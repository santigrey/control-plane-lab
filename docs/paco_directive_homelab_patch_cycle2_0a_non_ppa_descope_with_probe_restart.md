# paco_directive_homelab_patch_cycle2_0a_non_ppa_descope_with_probe_restart

**To:** PD (Cowork) | **From:** Paco | **Date:** 2026-05-04 Day 80 ~17:05 MT (~23:05 UTC)
**Cycle:** Cycle 2.0a non-PPA descope (Option B pulled FORWARD from cap-escalation to NOW per CEO direction "don't want more drift") + parallel probe loop restart (substrate hygiene; loop died 21h+ ago).
**Authority:** CEO Sloan ratified scope 2026-05-04 ~16:55 MT after Paco state-back of (a) probe loop dead since 2026-05-04T01:21:03Z; (b) only 3 ticks recorded; (c) one-shot tick at 22:51 UTC shows asymmetric outage: `launchpad.net` recovered (HTTP 200/TCP-OK) but `ppa.launchpadcontent.net` still TCP/443 Connection refused; (d) Cycle 2 ruling Option B (descope) was pre-staged at cap escalation but CEO chose to pull forward.
**Repo HEAD at directive author:** `bcdad31` (anchor hygiene cycle close).
**Cumulative state at author:** P6=47, SR=8.
**B0 standing meta-authority:** ACTIVE for this directive (PD authorized to fix Paco source-surface errors at execution time per Bug 1+2 cycle precedent; structural/clerical only; intent inviolable). **Second-clean-PD-execution invocation candidate** -- if cycle clean, qualifies B0 for SR #9 promotion at close-confirm.
**Predecessor:** `docs/paco_response_homelab_patch_cycle2_ppa_unreachable_ruling.md` (Cycle 2 ruling at HEAD `0d3bf8c`) + `docs/paco_directive_homelab_patch_cycle_cve_2026_31431.md` (original Cycle 1+2+3 directive).

---

## 0. TL;DR

Two execution blocks. Single directive, single dispatch, single commit.

**Block A -- Probe loop restart (Goliath; small, safe):**
- Append the 22:51 UTC one-shot tick already captured by Paco into `/tmp/cycle2_ppa_probe_history.log` for continuity.
- Author `/tmp/cycle2_ppa_probe_loop.sh` with proper nohup'd daemonized loop (hourly Layer 1 probe of both `ppa.launchpadcontent.net:443` AND `launchpad.net:443` per Cycle 2 ruling §4.1).
- Start the loop with `nohup` + `disown` so terminal close doesn't kill it again (root cause of prior loop death).
- Verify process visible in `ps -ef`; verify next tick lands within ~65min.

**Block B -- Cycle 2.0a non-PPA descope upgrade (Goliath; substantial):**
- Hold the canonical-nvidia PPA packages (4 known unfetchable + their kernel-meta dependencies that pull them in transitively).
- Run `apt-get dist-upgrade` (skips held packages by apt's transactional integrity).
- ~520 noble-updates non-PPA packages install; canonical-nvidia content stays UNCHANGED.
- K + D + M (kernel + driver + modules) MUST remain bit-identical pre/post (`6.11.0-1016-nvidia` / `580.95.05` / `6.11.0-1016.16+1000`).
- Standing gates 6/6 must remain bit-identical.
- ollama service quiesced for upgrade window then restored per SR #8.
- compose-plugin hold preserved.

**What this cycle deliberately DOES NOT do:**
- Touch kernel `6.17.0-1014-nvidia` (deferred to future Cycle 2.0b once `lpc` recovers).
- Touch the 4 PPA-only binaries (deferred to 2.0b).
- Reboot Goliath (held packages exclude kernel/modules so no reboot needed).
- Modify the original Cycle 2 directive in canon (this is a sibling cycle, not an amendment).

---

## 1. Verified-live block (Paco source-surface preflight per SR #7)

All probes run by Paco at directive-author time via homelab MCP read-only.

| Surface | Probe | Verified value at author |
|---|---|---|
| Goliath kernel | `ssh sloan4 'uname -r'` | `6.11.0-1016-nvidia` (UNCHANGED from Cycle 2 abort baseline) |
| NVIDIA driver | `nvidia-smi --query-gpu=driver_version` | `580.95.05` (UNCHANGED) |
| linux-image-nvidia-hwe-24.04 dpkg | `dpkg -l \| grep` | `ii 6.11.0-1016.16` (UNCHANGED) |
| linux-modules-nvidia-580-open-nvidia-hwe-24.04 dpkg | `dpkg -l \| grep` | `ii 6.11.0-1016.16+1000` (UNCHANGED) |
| compose-plugin hold | `apt-mark showhold` | `docker-compose-plugin` (Cycle 2 ruling preservation confirmed) |
| ollama service | `systemctl show -p ActiveState -p MainPID ollama.service` | `MainPID=185171 ActiveState=active` (matches Cycle 2 ruling restoration baseline) |
| dpkg --audit | `sudo dpkg --audit` | exit 0; clean |
| dpkg -C | `sudo dpkg -C` | exit 0; clean |
| Probe history log | `tail -1 /tmp/cycle2_ppa_probe_history.log` on Goliath | `2026-05-04T01:21:03Z lpc=FAIL lp=FAIL` (last tick 21h+ ago; loop dead) |
| Probe loop process | `ps -ef \| grep -E 'cycle2\|launchpad\|ppa\|while.*sleep'` on Goliath | NO_PROCESS_MATCH (confirmed loop dead) |
| One-shot probe at 22:51 UTC | `curl -I + /dev/tcp` from Goliath | `lpc HTTP=000 TCP=FAIL` + `lp HTTP=200 TCP=OK` (asymmetric outage; Layer-1 1/2) |
| Standing gates | per anchor + boot probes | 6/6 bit-identical: atlas-mcp PID 1212 / atlas-agent PID 4753 NR=0 / mercury PID 7800 / postgres-beast `2026-05-03T18:38:24.910689151Z` r=0 / garage-beast `2026-05-03T18:38:24.493238903Z` r=0 / atlas .env empty 0600 |
| Repo HEAD | `git log --oneline -1` | `bcdad31` (anchor hygiene cycle close) |

**Token-uniqueness preflight (P6 #45 application):**
- New artifact paths chosen (`/tmp/cycle2_ppa_probe_loop.sh` and `/tmp/cycle2_0a_apt.log` and `/tmp/cycle2_0a_pre_held.txt`) are content-fresh; PD verifies absence at DPF before writing.

---

## 2. Pre-flight verification (PD MUST PASS before execution)

### Block A pre-flight (probe restart)

DPF.A1 -- Probe history log exists + last-tick matches Paco capture:
```
ssh sloan4 'tail -1 /tmp/cycle2_ppa_probe_history.log; wc -l /tmp/cycle2_ppa_probe_history.log'
```
Expected: last line `2026-05-04T01:21:03Z lpc=FAIL lp=FAIL`; total tick count `3`.

DPF.A2 -- No probe loop currently running (confirms restart needed):
```
ssh sloan4 'ps -ef | grep -E "cycle2|launchpad|while.*sleep 3600" | grep -v grep' || echo NO_RUNNING
```
Expected: `NO_RUNNING` or empty output.

DPF.A3 -- New artifact paths free:
```
ssh sloan4 'test -e /tmp/cycle2_ppa_probe_loop.sh && echo EXISTS || echo FREE; test -e /tmp/cycle2_ppa_probe.stderr && echo EXISTS || echo FREE'
```
Expected: both `FREE`.

### Block B pre-flight (Cycle 2.0a descope)

DPF.B1 -- K+D+M baseline unchanged from Cycle 2 abort:
```
ssh sloan4 'uname -r; nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1; dpkg -l | grep -E "linux-image-nvidia-hwe-24.04 |linux-modules-nvidia-580-open-nvidia-hwe-24.04 " | awk "{print \$2, \$3}"'
```
Expected: `6.11.0-1016-nvidia` + `580.95.05` + the two HWE packages at `6.11.0-1016.16` and `6.11.0-1016.16+1000`.

DPF.B2 -- compose-plugin hold preserved:
```
ssh sloan4 'apt-mark showhold | grep docker-compose-plugin'
```
Expected: matches.

DPF.B3 -- ollama active + healthy:
```
ssh sloan4 'systemctl show -p ActiveState -p MainPID ollama.service; curl -s -m 5 http://localhost:11434/api/tags | python3 -c "import sys,json; d=json.load(sys.stdin); print(\"models:\",len(d[\"models\"]))"'
```
Expected: ActiveState=active + 3 models present (qwen2.5:72b + deepseek-r1:70b + llama3.1:70b).

DPF.B4 -- dpkg health clean:
```
ssh sloan4 'sudo dpkg --audit; echo audit_exit=$?; sudo dpkg -C; echo check_exit=$?'
```
Expected: both `=0`.

DPF.B5 -- apt-get update success (timeout-tolerant; PPA may err but other sources should succeed):
```
ssh sloan4 'sudo apt-get update 2>&1 | tee /tmp/cycle2_0a_apt_update.log | tail -20'
```
Expected: completion within ~3 min; `Err:` lines for canonical-nvidia (expected; lpc still down); 0 `Err:` lines for archive.ubuntu.com / ports.ubuntu.com / esm.ubuntu.com (primary archives reachable).

DPF.B6 -- Identify PPA-contributed packages in upgrade scope:
```
ssh sloan4 'sudo apt-get -s dist-upgrade 2>&1 > /tmp/cycle2_0a_simulation.log; grep "^Inst" /tmp/cycle2_0a_simulation.log | grep -E "canonical-nvidia|nvidia-desktop-edge|vulkan-packages" | awk "{print \$2}" > /tmp/cycle2_0a_ppa_packages.txt; cat /tmp/cycle2_0a_ppa_packages.txt'
```
Expected: list of canonical-nvidia-PPA-sourced packages. Should include the 4 known + likely also `linux-image-nvidia-hwe-24.04` (kernel meta) and `linux-modules-*` if simulation shows them. Capture full list for review.

DPF.B7 -- Total upgrade scope vs PPA scope:
```
ssh sloan4 'TOTAL=$(grep -c "^Inst" /tmp/cycle2_0a_simulation.log); PPA=$(wc -l < /tmp/cycle2_0a_ppa_packages.txt); echo "total=$TOTAL ppa_subset=$PPA non_ppa=$((TOTAL-PPA))"'
```
Expected: total ~520 (per Cycle 2 abort log); PPA 4-8 (the known 4 plus possible kernel-meta dep); non-PPA ~510-516.

DPF.B8 -- Standing gates baseline (paste outputs into review for pre/post comparison):
```
ssh beast 'systemctl show -p MainPID -p NRestarts atlas-mcp.service atlas-agent.service'
ssh ciscokid 'systemctl show -p MainPID mercury-scanner.service'
ssh beast 'docker inspect control-postgres-beast --format "{{.State.StartedAt}} r={{.RestartCount}}"'
ssh beast 'docker inspect control-garage-beast --format "{{.State.StartedAt}} r={{.RestartCount}}"'
```
Expected: bit-identical to §1 verified-live block.

DPF.B9 -- atlas.tasks cadence pre-cycle baseline:
```
ssh beast 'docker exec control-postgres-beast psql -U admin -d controlplane -t -c "SELECT COUNT(*) FROM atlas.tasks WHERE created_at > NOW() - interval '\''1 hour'\'';"'
```
Expected: ~250-260 (matches established ~253/hr cadence).

DPF.B10 -- Disk space + bandwidth:
```
ssh sloan4 'df -h / | tail -1; df -h /var | tail -1'
```
Expected: free space > 5GB on / (apt cache + unpacks).

---

## 3. Execution

One-step-at-a-time per SR #3. Standing-gate sentinel re-check between major stages.

### Block A -- Probe loop restart (do FIRST so probe accumulates evidence from cycle minute 0)

#### Step A1 -- Append captured 22:51 UTC tick to history log (continuity)
```
ssh sloan4 'echo "2026-05-04T22:51:00Z lpc=FAIL lp=PASS" >> /tmp/cycle2_ppa_probe_history.log; tail -5 /tmp/cycle2_ppa_probe_history.log; wc -l /tmp/cycle2_ppa_probe_history.log'
```
Expected: last line is the new entry; total tick count goes 3 -> 4.

*(Note: this is the Paco-captured one-shot from 22:51 UTC; tick records asymmetric state for the probe history. Real probe loop will produce ticks tagged FAIL or PASS based on the gate logic.)*

#### Step A2 -- Author probe loop script
```
ssh sloan4 'cat > /tmp/cycle2_ppa_probe_loop.sh << "EOF"
#!/bin/bash
# Cycle 2 PPA probe loop -- Paco directive Day 80 ~23:05 UTC
# Layer 1 probe per Cycle 2 ruling §4.1
# Logs to /tmp/cycle2_ppa_probe_history.log
# Self-terminates at 2026-05-07T22:23Z (cap deadline) OR on TERM signal
# Cap: 72h hard cap from 2026-05-04 22:23Z

LOG=/tmp/cycle2_ppa_probe_history.log
CAP_EPOCH=$(date -u -d "2026-05-07T22:23:00Z" +%s)

while true; do
  NOW_EPOCH=$(date -u +%s)
  if [ "$NOW_EPOCH" -ge "$CAP_EPOCH" ]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) cap_reached_terminate" >> "$LOG"
    break
  fi

  TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  # Layer 1 TCP probes (timeout 5s each)
  if timeout 5 bash -c "</dev/tcp/ppa.launchpadcontent.net/443" 2>/dev/null; then LPC=PASS; else LPC=FAIL; fi
  if timeout 5 bash -c "</dev/tcp/launchpad.net/443" 2>/dev/null; then LP=PASS; else LP=FAIL; fi
  echo "$TS lpc=$LPC lp=$LP" >> "$LOG"

  sleep 3600
done
EOF
chmod +x /tmp/cycle2_ppa_probe_loop.sh
ls -la /tmp/cycle2_ppa_probe_loop.sh'
```
Stop condition: script exists at `/tmp/cycle2_ppa_probe_loop.sh`; +x; non-zero size.

#### Step A3 -- Start the loop with proper backgrounding
```
ssh sloan4 'nohup bash /tmp/cycle2_ppa_probe_loop.sh </dev/null >/tmp/cycle2_ppa_probe.stdout 2>/tmp/cycle2_ppa_probe.stderr & disown; sleep 2; ps -ef | grep -E "cycle2_ppa_probe_loop" | grep -v grep'
```
Expected: 1 line of `ps` output showing the loop running; PID assigned.

Stop condition: `ps` returns 1 row matching the script. If 0 rows, halt + paco_request (loop didn't start).

#### Step A4 -- Verify loop wrote initial tick within 5 seconds
```
ssh sloan4 'tail -1 /tmp/cycle2_ppa_probe_history.log'
```
Expected: a NEW tick at current minute UTC (loop's first iteration runs immediately, then sleeps 3600s).

Stop condition: tick count goes 4 -> 5 with current UTC timestamp.

### Block B -- Cycle 2.0a non-PPA descope upgrade

#### Step B1 -- Pre-quiesce ollama (Stage A.2 from original Cycle 2 directive; SR #8 abort-restore covers reverse path)
```
ssh sloan4 'sudo systemctl stop ollama.service; sleep 2; systemctl show -p ActiveState ollama.service'
```
Expected: ActiveState=inactive.

Stop condition: service still active after 5s -> halt; check journal.

#### Step B2 -- Snapshot pre-upgrade state to /tmp/
```
ssh sloan4 'echo "== pre-upgrade snapshot $(date -u +%Y-%m-%dT%H:%M:%SZ) ==" > /tmp/cycle2_0a_pre.log; uname -r >> /tmp/cycle2_0a_pre.log; nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1 >> /tmp/cycle2_0a_pre.log; dpkg -l | grep -E "linux-image|linux-modules-nvidia|libnvidia|libvulkan|wpasupplicant|docker-compose" | awk "{print \$2, \$3}" >> /tmp/cycle2_0a_pre.log; apt-mark showhold >> /tmp/cycle2_0a_pre.log; cat /tmp/cycle2_0a_pre.log | head -30'
```
Stop condition: snapshot file written.

#### Step B3 -- Hold the PPA-contributed packages identified at DPF.B6 + their kernel-meta deps

PD reads `/tmp/cycle2_0a_ppa_packages.txt` and runs `apt-mark hold` on each. Plus defensive holds on the kernel meta packages that may pull in 6.17 transitively:
```
ssh sloan4 'cat /tmp/cycle2_0a_ppa_packages.txt | while read PKG; do sudo apt-mark hold "$PKG"; done; sudo apt-mark hold linux-image-nvidia-hwe-24.04 linux-modules-nvidia-580-open-nvidia-hwe-24.04; apt-mark showhold | sort | tee /tmp/cycle2_0a_holds.log'
```
Expected: hold list now includes original `docker-compose-plugin` + the 4-8 PPA packages + the 2 kernel-metas. Total ~6-10 hold entries.

Stop condition: hold log file written; `apt-mark showhold` returns expected entries.

#### Step B4 -- Re-simulate dist-upgrade with holds applied
```
ssh sloan4 'sudo apt-get -s dist-upgrade 2>&1 > /tmp/cycle2_0a_simulation_post_hold.log; grep -E "^Inst" /tmp/cycle2_0a_simulation_post_hold.log | wc -l; grep -E "canonical-nvidia" /tmp/cycle2_0a_simulation_post_hold.log | head -5'
```
Expected: `Inst` count drops from ~520 to ~512-516 (PPA + kernel-meta excluded); canonical-nvidia grep should now return ZERO `Inst` lines (held packages don't appear in upgrade plan).

Stop condition: any `^Inst.*canonical-nvidia` lines remain after holds applied -> halt + paco_request (incomplete hold list).

#### Step B5 -- Standing-gate sentinel mid-cycle (before destructive Stage)
Run DPF.B8 + DPF.B9 again. Compare to baseline. If any drift -> halt + paco_request.

#### Step B6 -- Execute dist-upgrade (NON-INTERACTIVE; held packages skipped)
```
ssh sloan4 'sudo DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::="--force-confold" -o Dpkg::Options::="--force-confdef" dist-upgrade 2>&1 | tee /tmp/cycle2_0a_apt.log | tail -50'
```
Expected: clean completion; ~510-516 packages upgraded; 0 errors; all `Get:` lines from archive.ubuntu.com / ports.ubuntu.com / esm.ubuntu.com (no canonical-nvidia in successful Get list).

Stop condition: any `E: Failed to fetch` (other than from PPA which is held -- shouldn't appear since held packages skip the fetch path); any `dpkg: error processing`; any unpack errors. Halt + paco_request.

#### Step B7 -- Post-upgrade dpkg health check
```
ssh sloan4 'sudo dpkg --audit; echo audit_exit=$?; sudo dpkg -C; echo check_exit=$?'
```
Expected: both `=0`.

Stop condition: non-zero exit. Halt + paco_request.

#### Step B8 -- Verify K+D+M unchanged (CRITICAL gate)
```
ssh sloan4 'echo "== post-upgrade K+D+M =="; uname -r; nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1; dpkg -l | grep -E "linux-image-nvidia-hwe-24.04 |linux-modules-nvidia-580-open-nvidia-hwe-24.04 " | awk "{print \$2, \$3}"'
```
Expected (CRITICAL):
- Kernel: `6.11.0-1016-nvidia` (UNCHANGED from pre-cycle)
- Driver: `580.95.05` (UNCHANGED)
- linux-image-nvidia-hwe-24.04: `6.11.0-1016.16` (UNCHANGED)
- linux-modules-nvidia-580-open-nvidia-hwe-24.04: `6.11.0-1016.16+1000` (UNCHANGED)

Stop condition: ANY drift in K+D+M values -> CRITICAL FAILURE; immediate rollback Stage; halt + paco_request.

#### Step B9 -- Restart ollama (SR #8 abort-restore equivalent for clean-completion path)
```
ssh sloan4 'sudo systemctl start ollama.service; sleep 5; systemctl show -p ActiveState -p MainPID ollama.service; curl -s -m 5 http://localhost:11434/api/tags | python3 -c "import sys,json; d=json.load(sys.stdin); print(\"models:\",len(d[\"models\"]),\"names:\",[m[\"name\"] for m in d[\"models\"]])"'
```
Expected: ActiveState=active; new MainPID; 3 models present (qwen2.5:72b + deepseek-r1:70b + llama3.1:70b same names as pre-cycle).

Stop condition: service fails to start within 30s OR models missing -> halt + paco_request (SR #8 abort-restore failed).

#### Step B10 -- Standing-gate sentinel post-cycle
Run DPF.B8 + DPF.B9. Compare to baseline. **MUST be bit-identical** (Goliath's ollama MainPID change is expected and not a fleet-SG metric; the 6 fleet SGs are atlas-mcp / atlas-agent / mercury / postgres-beast / garage-beast / atlas .env).

Stop condition: any drift in 6 fleet SGs -> halt + paco_request.

#### Step B11 -- atlas.tasks cadence post-cycle
Run DPF.B9 30 min after Step B6 completion. Expected: cadence within ±25% of pre-cycle baseline.

#### Step B12 -- Capture full forensics for review doc
```
ssh sloan4 'echo "== post-upgrade snapshot $(date -u +%Y-%m-%dT%H:%M:%SZ) ==" > /tmp/cycle2_0a_post.log; uname -r >> /tmp/cycle2_0a_post.log; nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1 >> /tmp/cycle2_0a_post.log; dpkg -l | grep -E "linux-image|linux-modules-nvidia|libnvidia|libvulkan|wpasupplicant|docker-compose" | awk "{print \$2, \$3}" >> /tmp/cycle2_0a_post.log; apt-mark showhold >> /tmp/cycle2_0a_post.log; diff /tmp/cycle2_0a_pre.log /tmp/cycle2_0a_post.log | head -40'
```
Stop condition: post-snapshot written; diff captured.

---

## 4. Acceptance Criteria

### MUST-PASS
- **AC.1 (Block A)** Probe loop running on Goliath as backgrounded process; visible in `ps -ef`; survives terminal close.
- **AC.2 (Block A)** History log has at least 5 ticks total post-cycle (3 original + 1 captured + 1 fresh from restarted loop); tick count keeps increasing on hourly cadence.
- **AC.3 (Block B)** Goliath kernel `6.11.0-1016-nvidia` UNCHANGED.
- **AC.4 (Block B)** Goliath NVIDIA driver `580.95.05` UNCHANGED.
- **AC.5 (Block B)** linux-image-nvidia-hwe-24.04 still `6.11.0-1016.16`; linux-modules-nvidia-580-open-nvidia-hwe-24.04 still `6.11.0-1016.16+1000`.
- **AC.6 (Block B)** ~510-516 packages successfully upgraded; 0 fetch errors from primary archives; canonical-nvidia content untouched (still at pre-cycle versions per `dpkg -l`).
- **AC.7 (Block B)** dpkg `--audit` and `-C` both exit 0 post-upgrade.
- **AC.8 (Block B)** ollama active + 3 models present + querying via /api/tags returns same 3 model names as pre-cycle.
- **AC.9 (Block B)** apt-mark showhold contains: `docker-compose-plugin` + the 4-8 PPA packages + 2 kernel-metas (linux-image-nvidia-hwe-24.04 + linux-modules-nvidia-580-open-nvidia-hwe-24.04).
- **AC.10 (Block B)** atlas.tasks cadence post-cycle within ±25% of pre-cycle ~253/hr baseline.
- **AC.11** Standing gates 6/6 bit-identical pre/cycle/post (atlas-mcp PID 1212 / atlas-agent PID 4753 NR=0 / mercury PID 7800 / postgres-beast `2026-05-03T18:38:24.910689151Z` r=0 / garage-beast `2026-05-03T18:38:24.493238903Z` r=0 / atlas .env empty 0600).
- **AC.12** Both secrets-scan layers + literal-sweep CLEAN on review doc + any new artifacts.
- **AC.13** Single git commit on `main` covering review doc; HEAD advances; push succeeds.

### SHOULD-PASS
- **AS.1** No reboot triggered (no kernel/module upgrade in this cycle scope).
- **AS.2** Block A probe loop's first tick lands within 5 seconds of `nohup` start (immediate-iteration design).
- **AS.3** Cycle elapsed time < 75 min (ample headroom; if longer, capture timing data for retro).

---

## 5. Path B authorizations

- **B0 (CEO standing meta-authority -- second clean-PD-execution invocation candidate):** ACTIVE. PD authorized to verify Paco's source-surface claims at execution time and adapt to ground truth WITHOUT halting, when error is structural/clerical AND adaptation preserves directive intent UNCHANGED AND adaptation is documented in review (Paco-stated -> PD-observed -> PD-applied -> rationale). **Clean execution this cycle qualifies B0 for SR #9 promotion at close-confirm.**
- **B1 (PPA package list discovery):** if DPF.B6's grep filter misses canonical-nvidia-sourced packages (e.g. simulation lists them with different source repo string), PD adapts the filter via inspection of full simulation log; documents the actual source filter used.
- **B2 (kernel-meta dependency identification):** if Step B3's defensive holds on `linux-image-nvidia-hwe-24.04` + `linux-modules-nvidia-580-open-nvidia-hwe-24.04` are insufficient (transitive dep pulls 6.17 anyway), PD adds additional holds (e.g. `linux-image-6.17.0-*-nvidia`, `linux-modules-6.17.0-*-nvidia`) and documents.
- **B3 (apt-get options):** if `--force-confold` causes config file drift not desired, PD switches to `--force-confnew` for specific packages (rare; typical noble-updates packages don't trigger this).
- **B4 (ollama restore failure):** if Step B9 ollama fails to start, PD invokes SR #8 abort-restore: capture journal, attempt service-file refresh, paco_request if persistent.
- **B5 (standing-gate drift):** if mid-cycle (Step B5) sentinel detects SG drift, PD HALTS execution before destructive Step B6; paco_request with full SG diff.

### NOT authorized (halt + paco_request)

- ANY action that touches kernel `6.17.0-1014-nvidia` or attempts to install it.
- ANY action that modifies the 4 known PPA-only binaries (linux-modules-nvidia-580-open-nvidia-hwe-24.04 + linux-modules-nvidia-580-open-6.17.0-1014-nvidia + libvulkan1 + wpasupplicant).
- ANY reboot of Goliath.
- ANY modification to nginx / Tailscale / systemd unit files outside ollama.service start/stop.
- ANY change to `/etc/apt/sources.list.d/*` (PPA list stays as-is; we hold packages, we don't unsubscribe sources).
- Force-push to origin.
- Modifying probe loop cadence below 1h (would risk triggering Launchpad rate-limit defenses).

---

## 6. Rollback

### Block A rollback (probe loop)
```
ssh sloan4 'pkill -f cycle2_ppa_probe_loop.sh; rm -f /tmp/cycle2_ppa_probe_loop.sh; ls /tmp/cycle2_ppa_probe_loop.sh 2>&1'
```
Expected: process killed; script removed.

### Block B rollback (Cycle 2.0a if catastrophic)

If K+D+M drift detected at Step B8 (CRITICAL FAILURE) OR ollama unrecoverable at Step B9:

```
# 1. Stop ollama if running
ssh sloan4 'sudo systemctl stop ollama.service'

# 2. Identify packages upgraded (from /tmp/cycle2_0a_apt.log)
ssh sloan4 'grep -E "^Setting up" /tmp/cycle2_0a_apt.log | awk "{print \$3}" > /tmp/cycle2_0a_upgraded.txt; wc -l /tmp/cycle2_0a_upgraded.txt'

# 3. For each upgraded package, attempt downgrade to pre-cycle version (per /tmp/cycle2_0a_pre.log snapshot)
# This is per-package and may fail if pre-cycle version no longer in apt cache.
# PD must identify pre-cycle version from /tmp/cycle2_0a_pre.log and apt-cache madison <pkg>.
# If downgrade infeasible: paco_request with severity escalation.

# 4. Remove the holds we added (keep compose-plugin hold)
ssh sloan4 'sudo apt-mark unhold $(comm -23 <(apt-mark showhold | sort) <(echo docker-compose-plugin))'

# 5. Restart ollama
ssh sloan4 'sudo systemctl start ollama.service'
```

**CRITICAL:** if K+D+M drifted (kernel changed despite holds), Goliath may need GRUB intervention to boot back into 6.11. This is severity-2 escalation; PD writes paco_request_homelab_patch_cycle2_0a_kernel_drift.md immediately.

### Rollback acceptance
- K+D+M restored to pre-cycle values.
- ollama active + 3 models present.
- Standing gates 6/6 bit-identical to pre-cycle baseline.
- apt-mark hold list reverts to pre-cycle (`docker-compose-plugin` only).

---

## 7. Close-confirm artifacts (PD writes)

- `docs/paco_review_homelab_patch_cycle2_0a_non_ppa_descope.md` covering:
  - DPF.A1-A3 + DPF.B1-B10 outputs verbatim
  - Step A1-A4 + Step B1-B12 commands run + outputs
  - AC.1-AC.13 PASS/FAIL with evidence quotes
  - AS.1-AS.3 PASS/FAIL
  - Standing gates pre/mid/post comparison table
  - B0 invocation status: explicitly state YES (with adaptations table) or NO (clean first-try). **This is the data point that promotes B0 to SR #9 at Paco close-confirm.**
  - DB forensic discipline N/A this cycle (no DB writes)
  - K+D+M pre/post snapshot diff
  - PPA package hold list with source attribution
  - Probe history log with new ticks since restart
- Both secrets-scan layers + literal-sweep CLEAN before commit
- Single git commit; HEAD on origin/main moves
- No SESSION.md update from PD; Paco handles at close-confirm-ratification

---

## 8. Pre-flight-checked code surface (Paco verification per P6 #42)

- **Indent convention:** bash heredoc; no language-specific indent constraints in the embedded shell script.
- **HTTP method:** /healthz on Goliath = ollama /api/tags (GET; no /healthz on ollama service); curl -s -m 5 returns JSON.
- **Restart requirement:** ollama service stop/start; no systemd reload needed (unit file unchanged).
- **DB target:** N/A this cycle.
- **Background process discipline:** `nohup` + `</dev/null` + `>/path/stdout` + `2>/path/stderr` + `& disown` -- the `disown` is key; without it, terminal close sends SIGHUP and kills the loop (root cause of prior loop death).
- **Loop self-termination:** at cap (`2026-05-07T22:23:00Z`) the loop writes a final `cap_reached_terminate` line and exits cleanly. PD verifies cap-time math at DPF (date arithmetic).
- **Hold strategy:** `apt-mark hold` honors transactional integrity; held packages skip both fetch AND unpack stages atomically.
- **Force-conf flags:** `--force-confold` keeps existing config files; `--force-confdef` defers to maintainer's default. Standard non-interactive upgrade combo for noble-updates.
- **Cadence:** 1h sleep -- NOT shorter (Launchpad rate-limit safety).
- **Source filter:** DPF.B6 grep targets `canonical-nvidia` literal in apt simulation source string; B1 Path B covers filter drift.

---

## 9. Out-of-scope / future

- **Cycle 2.0b** -- the *kernel + NVIDIA modules + libvulkan1 + wpasupplicant* upgrade deferred to when `lpc` recovers. Probe loop's eventual gate-pass triggers paco_request_homelab_patch_cycle2_0b_lpc_recovered.md (PD-authored) -> Paco issues fresh ruling authorizing 2.0b dispatch.
- **B0 SR #9 promotion** -- if this cycle clean, qualifies for promotion at close-confirm. Paco close-confirm doc will explicitly call the promotion.
- **Probe loop terminal hygiene** -- once cap reached or 2.0b ships, PD removes `/tmp/cycle2_ppa_probe_loop.sh` + history log archive into `docs/cycle2_probe_history_archive_<date>.md` for audit trail.

-- Paco

Status: AWAITING APPROVAL
