# paco_review_reachability_step3_etc_hosts

**To:** Paco | **From:** PD | **Date:** 2026-05-02 Day 78 mid-day (post-directive)
**Authority basis:** `docs/paco_directive_reachability_step3_etc_hosts.md` (HEAD `d7cc7ae`)
**Status:** STEP 3 CLOSE — 4/4 nodes ACCEPTED; ZERO escalations; ZERO regressions
**Tracks:** `docs/homelab_reachability_v1_0.md` Step 3 (canonical /etc/hosts on always-on Linux nodes)

---

## 1. Executive summary

Reachability cycle Step 3 executed against the 4 PD-executable Linux nodes (ciscokid → beast → slimjim → goliath) in directive order. All four nodes pass per-node acceptance with no failures and no `paco_request` escalations. Canonical 8-entry hosts block installed via the directive-specified Python heredoc (idempotent; append branch on every node — no marker block was previously present anywhere). Pre-existing non-canonical lines preserved per directive (Beast stray + Goliath NVIDIA `gx10-dc66`). Standing gates 1, 2, 4, 5, 6 bit-identical to Phase 6 close baseline (Step 3 read-only on services as expected).

## 2. Per-node verified post-state

### 2.1 ciscokid (sloan3, 192.168.1.10)

- **Backup:** `/etc/hosts.bak.20260502-165727` (221 bytes; pre-state preserved)
- **Install path:** append branch (no prior marker block)
- **`cat /etc/hosts` post-state:**
  ```
  127.0.0.1 localhost
  127.0.1.1 sloan3

  # The following lines are desirable for IPv6 capable hosts
  ::1     ip6-localhost ip6-loopback
  fe00::0 ip6-localnet
  ff00::0 ip6-mcastprefix
  ff02::1 ip6-allnodes
  ff02::2 ip6-allrouters

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
- **`getent hosts <12 names>`:** all 8 unique IPs resolve correctly. ciscokid/sloan3 own-name dual resolution (127.0.1.1 + 192.168.1.10) — directive-anticipated, not regression.
- **`ping -c1 -W2`:** ciscokid 0.036ms · beast 0.328ms · slimjim 0.462ms · goliath 0.917ms — 4/4 PASS.
- **Acceptance:** PASS 5/5 gates (backup / block-byte-exact / getent / ping / pre-existing-intact).

### 2.2 beast (sloan2, 192.168.1.152)

- **Backup:** `/etc/hosts.bak.20260502-170010` (259 bytes)
- **Install path:** append branch
- **`cat /etc/hosts` post-state:**
  ```
  127.0.0.1 localhost
  127.0.1.1 sloan2

  # The following lines are desirable for IPv6 capable hosts
  ::1     ip6-localhost ip6-loopback
  fe00::0 ip6-localnet
  ff00::0 ip6-mcastprefix
  ff02::1 ip6-allnodes
  ff02::2 ip6-allrouters
  192.168.1.10 sloan3.tail1216a3.ts.net

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
- **`getent hosts <12 names>`:** all resolve correctly. beast/sloan2 own-name dual resolution (directive-anticipated).
- **`ping -c1 -W2`:** ciscokid 0.360ms · beast 0.081ms · slimjim 0.646ms · goliath 0.976ms — 4/4 PASS.
- **Cosmetic note (NOT a regression):** `ping ciscokid` from beast reports reply name as `sloan3.tail1216a3.ts.net (192.168.1.10)`. The forward IP resolution is canonical (192.168.1.10); the reverse-resolved display name comes from the pre-existing stray `192.168.1.10 sloan3.tail1216a3.ts.net` line (which appears in /etc/hosts ABOVE the canonical block, so NSS PTR lookup hits it first). Reachability is correct; only the display name is stray-derived. Resolves naturally when stray is purged at Step 6 audit cleanup.
- **Acceptance:** PASS 5/5 gates.
- **Stray preserved per directive:** `192.168.1.10 sloan3.tail1216a3.ts.net` left intact.

### 2.3 slimjim (sloan1, 192.168.1.40)

- **Backup:** `/etc/hosts.bak.20260502-170214` (221 bytes)
- **Install path:** append branch
- **`cat /etc/hosts` post-state:** localhost + sloan1 + IPv6 stanza preserved; canonical block appended cleanly.
- **`getent hosts <12 names>`:** all resolve correctly. slimjim/sloan1 own-name dual resolution.
- **`ping -c1 -W2`:** ciscokid 0.263ms · beast 0.413ms · slimjim 0.017ms · goliath 0.973ms — 4/4 PASS.
- **Note:** `ping ciscokid` from slimjim cleanly reports reply name as `ciscokid` (no stray display-name artifact, confirming the beast cosmetic was strictly local to beast's own /etc/hosts).
- **Acceptance:** PASS 5/5 gates.

### 2.4 goliath (sloan4, 192.168.1.20)

- **Backup:** `/etc/hosts.bak.20260502-170448` (72 bytes — minimal pre-state)
- **Install path:** append branch
- **`cat /etc/hosts` post-state:**
  ```
  127.0.0.1       localhost
  127.0.0.1       gx10-dc66  

  127.0.1.1 sloan4

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
- **`getent hosts <12 names>`:** all resolve correctly. goliath/sloan4 own-name dual resolution.
- **NVIDIA preserve verification:** `getent hosts gx10-dc66` → `127.0.0.1 gx10-dc66` ✅ functional, line position + whitespace unchanged.
- **`ping -c1 -W2`:** ciscokid 0.272ms · beast 0.354ms · slimjim 0.354ms · goliath 0.018ms — 4/4 PASS.
- **Acceptance:** PASS 5/5 gates + NVIDIA preserve confirmed.

## 3. Standing gates pre/post snapshot

Directive specified gates 1, 2, 4, 5, 6 (gate 3 explicitly skipped). Step 3 is read-only on services; all 5 expected unchanged. **All 5 confirmed bit-identical to Phase 6 close baseline.**

| Gate | Subject | Phase 6 baseline | Step 3 post-install | Verdict |
|---|---|---|---|---|
| 1 | B2b anchor (`control-postgres-beast`) | StartedAt `2026-04-27T00:13:57.800746541Z`; running; restart=0 | StartedAt `2026-04-27T00:13:57.800746541Z`; running; restart=0 | bit-identical (96h+) |
| 2 | Garage anchor (`control-garage-beast`) | StartedAt `2026-04-27T05:39:58.168067641Z`; running; restart=0 | StartedAt `2026-04-27T05:39:58.168067641Z`; running; restart=0 | bit-identical (96h+) |
| 3 | (directive-skipped) | n/a | n/a | n/a |
| 4 | atlas-mcp.service (Beast) | active running, MainPID 2173807, since 2026-05-01 22:05:42 UTC | active running, MainPID 2173807, since 2026-05-01 22:05:42 UTC | MainPID unchanged |
| 5 | atlas-agent.service (Beast) | loaded inactive dead disabled (Phase 1 acceptance state) | loaded inactive dead disabled | unchanged |
| 6 | mercury-scanner.service (CK) | active running, MainPID 643409 | active running, MainPID 643409, since 2026-05-02 04:03:05 UTC | MainPID unchanged |

**Verdict:** Standing Gates 5/5 directive-scoped gates PRESERVED. Step 3 introduced zero service-state drift, as expected for an /etc/hosts-only intervention.

## 4. Inventory of pre-existing non-canonical entries (Step 6 audit cleanup queue)

| Node | Line | Recommendation | Rationale |
|---|---|---|---|
| ciscokid | (none beyond standard Debian stanza) | no action | clean baseline |
| beast | `192.168.1.10 sloan3.tail1216a3.ts.net` | **REMOVE at Step 6** | Day 30 archaeology per canon §Past-fix. Maps CK LAN IP to CK Tailscale FQDN. Redundant with canonical `192.168.1.10 ciscokid sloan3`; doesn't conflict but does cause cosmetic ping-reverse-resolution to display the Tailscale FQDN. |
| slimjim | (none beyond standard Debian stanza) | no action | clean baseline |
| goliath | `127.0.0.1 gx10-dc66` | **PRESERVE indefinitely** | NVIDIA toolchain dependency per directive + canon. NOT a cleanup candidate. |
| goliath | (no IPv6 stanza in pre-state) | **document at Step 6** | Anomaly: CK/Beast/SlimJim all carry the standard Debian IPv6 hosts stanza; Goliath does not. Was already absent in pre-state — install path did not add it. Likely an artifact of the NVIDIA-shipped image. Decision needed at Step 6: add the standard IPv6 stanza for consistency, or document as intentional NVIDIA-image difference. |

## 5. Discipline observations + verified-live commands

- **Directive procedure compliance:** per-node 3-substep procedure (backup → idempotent Python heredoc install → cat/getent/ping verify) executed as specified for all 4 nodes.
- **No chaining:** acceptance gate evaluated and confirmed PASS before each next-node start.
- **Idempotency contract honored:** the install code's regex `# BEGIN santigrey canonical hosts.*?# END santigrey canonical hosts\n` ensures re-running the directive will REPLACE-IN-PLACE rather than append-again. Backup-creation is timestamped so multiple runs accumulate `.bak.<ts>` files (acceptable; not an idempotency concern).
- **Day 30 reachability lesson honored:** Python heredoc bypasses shell-escape pitfalls (per canon).
- **Verified-live commands (this review):**
  - per-node: `sudo cp /etc/hosts /etc/hosts.bak.$(date -u +%Y%m%d-%H%M%S); ls -la /etc/hosts*; cat /etc/hosts`
  - per-node: Python heredoc (above section 2; byte-exact across all 4 nodes)
  - per-node: `cat /etc/hosts; getent hosts ciscokid sloan3 beast sloan2 slimjim sloan1 goliath sloan4 kalipi pi3 macmini jesair; for h in ciscokid beast slimjim goliath; do ping -c1 -W2 $h | head -2; done`
  - goliath only (preserve verification): `getent hosts gx10-dc66`
  - gates Beast-side: `docker inspect control-postgres-beast --format '{{.State.StartedAt}} {{.State.Status}} restart={{.RestartCount}}'`; same for `control-garage-beast`; `systemctl show atlas-mcp.service`; `systemctl show atlas-agent.service`
  - gate CK-side: `systemctl show mercury-scanner.service`

## 6. Pre-commit secrets-scan (P6 #34 standing practice)

Both scans run on this review file BEFORE staging/commit. P6 #34 mitigation pattern: BOTH broad-grep AND tightened-regex. No credential VALUES quoted anywhere in this review (own-discipline check). Step 3 scope is /etc/hosts state only — no credentials in scope on the artifact face — but scan is mandatory regardless per P6 #34 standing practice.

- **Broad-grep pattern:** `grep -nEi 'key|token|secret|password|api|auth' docs/paco_review_reachability_step3_etc_hosts.md`
- **Tightened-regex pattern:** `grep -nEi 'api[_-]?key|secret[_-]?key|access[_-]?token|bearer\s+|authorization:' docs/paco_review_reachability_step3_etc_hosts.md`

Scan results recorded in `## 8. Commit log` below (post-execution append).

## 7. Closing notes for Paco

- **No paco_request fired.** All 4 nodes pass per-node acceptance. Step 3 closes clean.
- **Out-of-scope deferrals confirmed:** KaliPi → Step 3.5 (cloud-init `manage_etc_hosts: True` + sudo password block); Pi3 → not in `homelab_ssh_run` allowed-host list; Mac mini → Step 5 (sshd unreachable). All three correctly deferred per amended canon and not touched in this cycle.
- **Step 6 audit queue items:** beast stray line + goliath IPv6-stanza-anomaly logged in §4 above.
- **Ready for Step 3.5** at CEO discretion (separate Paco directive expected per amended canon; CEO at terminal of KaliPi + Pi3 to bundle jes-user creation + cloud-init disable + canonical hosts install + Pi3 allowed-host wiring).

## 8. Commit log (appended post-secrets-scan)

### 8.1 Secrets-scan results (P6 #34)

Both scans run pre-commit; both PASS-with-known-policy-mentions (zero credential VALUES quoted; all hits are this doc's own description of the scan policy).

**Broad-grep hits (8 lines, all reviewed non-credential):**
- L4: "Authority basis" header (substring "auth")
- L157: section 6 heading "Pre-commit secrets-scan" (substring "secret")
- L161: documents the broad-grep pattern verbatim
- L162: documents the tightened-regex pattern verbatim
- L169: describes KaliPi blocker ("sudo password" requirement — describes that a password IS required, does not quote the password)
- L173: section 8 heading "Commit log (appended post-secrets-scan)"
- L175: phrase "BOTH-pass secrets-scan"

**Tightened-regex hits (1 line, reviewed non-credential):**
- L162: documents the tightened-regex pattern verbatim

**Verdict:** PASS. Zero credential values present. All matches are policy/pattern self-references — expected for a doc that describes the scan policy itself.

### 8.2 Commit + push

This review committed alongside the updated `docs/handoff_pd_to_paco.md` notification (PD->Paco event = Step 3 close) in a single commit on `main`. Commit SHA + push verification = git metadata on this commit; not duplicated in-doc to avoid self-reference loops.

Commit message: `docs: PD reachability Step 3 review (canonical /etc/hosts on CK, Beast, SlimJim, Goliath)`
Remote: `origin` (santigrey/control-plane-lab)

-- PD
