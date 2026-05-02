# paco_directive_reachability_step3_etc_hosts

**To:** PD | **From:** Paco | **Date:** 2026-05-02 Day 78 mid-day
**Authority:** CEO directive (Day 78 mid-day; Y1 ratified for Cortez sub-decision; reachability Step 3 dispatch on amended scope)
**Status:** ACTIVE
**Tracks:** `docs/homelab_reachability_v1_0.md` reachability cycle Step 3 (amended in same commit)

---

## Background

Reachability cycle Step 3: install canonical `/etc/hosts` block on always-on Linux nodes per `docs/homelab_reachability_v1_0.md`. Pre-directive verification (Day 78 mid-day) reduced PD-executable scope from 5 to 4: CK, Beast, SlimJim, Goliath. KaliPi deferred to Step 3.5 (cloud-init `manage_etc_hosts: True` on the live system + `sloan` user requires sudo password, both of which defeat PD non-interactive `homelab_ssh_run`). Mac mini deferred to Step 5 (sshd unreachable). Pi3 deferred (not in `homelab_ssh_run` allowed-host list).

## Verified live (2026-05-02 Day 78 mid-day)

| Node | Probe | Output |
|---|---|---|
| ciscokid | `whoami; sudo -n true && echo OK` | `jes / OK` (NOPASSWD sudo) |
| ciscokid | `hostname` | `sloan3` |
| ciscokid | `cat /etc/hosts` | `127.0.0.1 localhost`; `127.0.1.1 sloan3`; IPv6 stanza |
| beast | `whoami; sudo -n true && echo OK` | `jes / OK` |
| beast | `hostname` | `sloan2` |
| beast | `cat /etc/hosts` | minimal + stray `192.168.1.10 sloan3.tail1216a3.ts.net` (preserve; cleanup at Step 6 audit) |
| slimjim | `whoami; sudo -n true && echo OK` | `jes / OK` |
| slimjim | `hostname` | `sloan1` |
| slimjim | `cat /etc/hosts` | minimal |
| goliath | `whoami; sudo -n true && echo OK` | `jes / OK` |
| goliath | `hostname` | `sloan4` |
| goliath | `cat /etc/hosts` | `127.0.0.1 localhost`; `127.0.0.1 gx10-dc66` (PRESERVE — NVIDIA toolchain); `127.0.1.1 sloan4` |
| kalipi | `whoami; sudo -n true` | `sloan` / `sudo: a password is required` → MOVED TO STEP 3.5 |
| kalipi | `cat /etc/cloud/cloud.cfg` markers + `cat /etc/hosts` header | cloud-init `manage_etc_hosts: True` regenerated on boot from `/etc/cloud/templates/hosts.debian.tmpl` → MOVED TO STEP 3.5 |
| macmini | `ssh` | `connect to host 192.168.1.13 port 22: No route to host` → STEP 5 (already queued) |
| pi3 | `homelab_ssh_run` | not in allowed-host list → DEFERRED |

Verification host: ciscokid (orchestrator) and per-target via `homelab_ssh_run`.
Verification timestamp: 2026-05-02 Day 78 mid-day.

## Canonical block (insert / replace between markers)

```
# BEGIN santigrey canonical hosts (managed; see homelab_reachability_v1_0.md Step 3)
192.168.1.10    ciscokid sloan3
192.168.1.152   beast sloan2
192.168.1.40    slimjim sloan1
192.168.1.20    goliath sloan4
192.168.1.254   kalipi
192.168.1.139   pi3
192.168.1.13    macmini
192.168.1.155   jesair
# END santigrey canonical hosts
```

## Procedure

Per node, in order: **ciscokid → beast → slimjim → goliath**. One node at a time. Per-node acceptance before next. PD does NOT chain.

### Step 3.<N> — install on $NODE

**1. Backup + capture pre-state**

```bash
sudo cp /etc/hosts /etc/hosts.bak.$(date -u +%Y%m%d-%H%M%S)
ls -la /etc/hosts*
cat /etc/hosts
```

**2. Idempotent block install** (Python heredoc; bypasses shell-escape pitfalls per Day 30 reachability lesson):

```bash
sudo python3 - <<'PYEOF'
import re, pathlib
p = pathlib.Path('/etc/hosts')
txt = p.read_text()
block = """# BEGIN santigrey canonical hosts (managed; see homelab_reachability_v1_0.md Step 3)
192.168.1.10    ciscokid sloan3
192.168.1.152   beast sloan2
192.168.1.40    slimjim sloan1
192.168.1.20    goliath sloan4
192.168.1.254   kalipi
192.168.1.139   pi3
192.168.1.13    macmini
192.168.1.155   jesair
# END santigrey canonical hosts
"""
pat = re.compile(r'# BEGIN santigrey canonical hosts.*?# END santigrey canonical hosts\n', re.DOTALL)
new = pat.sub(block, txt) if pat.search(txt) else txt.rstrip() + '\n\n' + block
p.write_text(new)
print('OK')
PYEOF
```

**3. Post-state verification**

```bash
cat /etc/hosts
echo '---getent---'
getent hosts ciscokid sloan3 beast sloan2 slimjim sloan1 goliath sloan4 kalipi pi3 macmini jesair
echo '---ping---'
for h in ciscokid beast slimjim goliath; do ping -c1 -W2 $h | head -2; done
```

Expected:
- `cat /etc/hosts` shows the marker block in place exactly once
- `getent hosts <name>` returns the canonical IP for each of the 8 names
- 4× ping returns 1 packet within 2s. (On the source node, its own short name preferentially resolves to 127.0.1.1 — correct, not a regression.)

### Acceptance per node

- `/etc/hosts.bak.<timestamp>` exists (rollback path preserved)
- Marker block present, single instance, byte-for-byte canonical content
- All 8 `getent hosts` lookups return canonical IPs
- All 4 ping targets respond
- Pre-existing non-canonical entries left intact (e.g. Beast's stray `sloan3.tail1216a3.ts.net` — flag in review; cleanup at Step 6 audit)
- Goliath's `127.0.0.1 gx10-dc66` line preserved (NVIDIA toolchain)

### Acceptance for full Step 3

All 4 nodes pass per-node acceptance. PD writes `docs/paco_review_reachability_step3_etc_hosts.md` containing:

- Per-node verified-post-state block (cat output, getent output, ping output, backup file path)
- Standing gates pre/post snapshot (gates 1, 2, 4, 5, 6 — all should be unchanged; Step 3 is read-only on services)
- Inventory of pre-existing non-canonical entries discovered (for Step 6 audit cleanup queue)
- Pre-commit secrets-scan: BOTH broad-grep AND tightened-regex on the review file (P6 #34 standing practice)

Then commit + push:

```bash
git add docs/paco_review_reachability_step3_etc_hosts.md
git commit -m 'docs: PD reachability Step 3 review (canonical /etc/hosts on CK, Beast, SlimJim, Goliath)'
git push
```

Update `docs/handoff_pd_to_paco.md` notification line:

> Paco, PD finished reachability Step 3. Canonical /etc/hosts on CK, Beast, SlimJim, Goliath. Check handoff.

## Discipline reminders

- One node at a time. No chaining. Per-node acceptance before next.
- Any node fails acceptance → STOP + paco_request + CEO ratifies recovery. Do not proceed.
- Pre-existing non-canonical lines: LEAVE IN PLACE. Step 6 audit territory (no scope creep here).
- Goliath `127.0.0.1 gx10-dc66`: do NOT touch. NVIDIA / GX10 toolchain dependency.
- KaliPi, Pi3, Mac mini explicitly OUT OF SCOPE for this step (deferred per amended canon).
- Standing gates 1–6 should be unchanged post-Step 3. PD verifies pre/post in paco_review.

## Trigger from CEO to PD

```
PD, paco_directive_reachability_step3_etc_hosts.md committed. Step 3 GO. 4 nodes: CK, Beast, SlimJim, Goliath. One at a time per directive procedure.
```

-- Paco
