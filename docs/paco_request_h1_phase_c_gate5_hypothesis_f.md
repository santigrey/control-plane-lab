# paco_request_h1_phase_c_gate5_hypothesis_f

**Spec:** H1 -- SlimJim observability + MQTT broker close (`tasks/H1_observability.md` section 7)
**Step:** Phase C -- Gate 5 (post Beast third-host PASS, post version-parity discovery)
**Status:** ESCALATION #7 (Phase C cumulative). Hypotheses A/B/C/D/E all RULED OUT. Hypothesis F (CK-host-specific environmental state) is the surviving frame. Diagnostic direction needed.
**Predecessor:** `docs/paco_response_h1_phase_c_gate5_matrix_collision.md` (commit `4c5623c`, Path B approved + P6 #14 banked + ESC #7 expected)
**Author:** PD
**Date:** 2026-04-28 (Day 73)
**Target hosts:** Beast (`192.168.1.152`) + CiscoKid (`192.168.1.10`) + SlimJim (`192.168.1.40`)

---

## TL;DR

Beast Gate 5 PASSES end-to-end (sub-bg + pub-fg, full message round-trip with `hello-from-beast` payload received by sub). CK Gate 5 FAILS with same broker, same listener, same creds, same package version. **CK and Beast both run `mosquitto-clients` and `libmosquitto1` at `2.0.11-1ubuntu1.2`** -- identical, with no newer version available in either host's apt archive.

Hypothesis E (client-version mismatch) is dead. Beast's PASS rules out Hypothesis D (broker concurrent-CONNECT race) and Hypothesis A (per-user broker limit). The discriminator is the source host -- something specific to CK's runtime environment.

PD biases toward F.1 (accumulated broker-side state for CK source IP from prior failed CONNECTs) as highest-probability sub-hypothesis. Cheapest decisive test: `systemctl restart mosquitto` on SlimJim -> re-run Gate 5 from CK with same creds and clientids. If PASS -> F.1 confirmed, P6 #15 candidate, Phase C closes. If FAIL -> narrow to F.2/F.3/F.4.

B2b nanosecond anchor: `2026-04-27T00:13:57.800746541Z` -- holding through 14+ phases. Garage anchor: `2026-04-27T05:39:58.168067641Z` -- holding. Substrate undisturbed by all diagnostic work.

---

## 1. Beast Gate 5 PASS evidence

### 1.1 Test execution from Beast (192.168.1.152) -> SlimJim:1884

Return codes:
- `sub rc: 27` (mosquitto_sub `-W 5` timeout exit, expected behavior after sub receives the publish)
- `pub rc: 0` (mosquitto_pub clean exit)

### 1.2 Sub output (full, verbatim from /tmp/H1_phase_c_beast_sub.txt)

```
Client beast-sub sending CONNECT
Client beast-sub received CONNACK (0)
Client beast-sub sending SUBSCRIBE (Mid: 1, Topic: test/beast, QoS: 0, Options: 0x00)
Client beast-sub received SUBACK
Subscribed (mid: 1): 0
Client beast-sub received PUBLISH (d0, q0, r0, m0, 'test/beast', ... (16 bytes))
hello-from-beast
Timed out
Client beast-sub sending DISCONNECT
```

End-to-end round-trip: sub authed (CONNACK 0), subscribed, received the publish payload, clean disconnect after the 5s window.

### 1.3 Pub output (full, verbatim from /tmp/H1_phase_c_beast_pub.txt)

```
Client beast-pub sending CONNECT
Client beast-pub received CONNACK (0)
Client beast-pub sending PUBLISH (d0, q0, r0, m1, 'test/beast', ... (16 bytes))
Client beast-pub sending DISCONNECT
```

Pub authed (CONNACK 0), published, clean disconnect.

### 1.4 What this PASS proves

- Concurrent sub-bg + pub-fg pattern works against this broker, this listener, these creds -- when the source host is Beast.
- Hypothesis D (broker concurrent-CONNECT race in mosquitto 2.0.18) is RULED OUT. Broker is not the problem.
- Hypothesis A (per-user/per-IP connection limit at broker) is RULED OUT. `alexandra` user accepted concurrent connections from Beast within minutes of failing them from CK.
- The variable that flips outcome is the source host. CK fails, Beast succeeds.

---

## 2. Version-parity capture

### 2.1 Beast (post-install today via `sudo -n apt install -y mosquitto-clients`)

```
libmosquitto1:amd64        2.0.11-1ubuntu1.2
mosquitto-clients          2.0.11-1ubuntu1.2
```

Captured to `/tmp/H1_phase_c_beast_clients_ver.txt` on Beast.

### 2.2 CK (current state, captured this turn)

```
libmosquitto1:amd64        2.0.11-1ubuntu1.2
mosquitto-clients          2.0.11-1ubuntu1.2
```

### 2.3 CK apt-cache policy

```
mosquitto-clients:
  Installed: 2.0.11-1ubuntu1.2
  Candidate: 2.0.11-1ubuntu1.2
  Version table:
 *** 2.0.11-1ubuntu1.2 500
        500 http://us.archive.ubuntu.com/ubuntu jammy-updates/universe amd64 Packages
        500 http://security.ubuntu.com/ubuntu jammy-security/universe amd64 Packages
        100 /var/lib/dpkg/status
     2.0.11-1ubuntu1 500
        500 http://us.archive.ubuntu.com/ubuntu jammy/universe amd64 Packages
```

**Installed = Candidate = `2.0.11-1ubuntu1.2`.** No newer version exists in CK's apt archive. The `apt install --only-upgrade` command per pre-authorization is a definitive no-op.

### 2.4 OS divergence side-finding

- CK: Ubuntu 22.04 (`jammy`) -- per apt-cache source paths
- SlimJim: Ubuntu 24.04 (`noble`) -- per request #5 broker package source
- Beast: ran `sudo -n apt install -y mosquitto-clients` to version `2.0.11-1ubuntu1.2` -- consistent with jammy or noble equivalent. (Not enumerated this turn; can confirm if F-line testing requires it.)

OS-level divergence between CK and SlimJim exists, but mosquitto-clients package version is identical bilaterally. Whether jammy's libmosquitto1 binary differs from noble's at the same version string is a known vendor-build variable but unlikely to be the discriminator since Beast (also jammy or noble at same version string) PASSES.

### 2.5 Hypothesis E ruling

**Hypothesis E (client-version mismatch) is RULED OUT in its package-version framing.**

---

## 3. Beast substrate anchor preservation

### 3.1 Pre-test snapshot (captured to /tmp/H1_phase_c_beast_anchors_pre.txt)

```
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

### 3.2 Post-test snapshot (captured to /tmp/H1_phase_c_beast_anchors_post.txt)

```
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

### 3.3 Diff

`ANCHORS-BIT-IDENTICAL`

B2b nanosecond anchor + Garage StartedAt held bit-identical pre/post the Beast install + Gate 5 run. 14+ phases of operational work, zero substrate disturbance.

---

## 4. Hypothesis space -- final state

### 4.1 Hypothesis A -- per-user/per-IP broker connection limit

Status: **RULED OUT.** Beast PASSED with `alexandra` user against the same broker within minutes of CK failing with the same user. If a per-user broker-side limit existed, Beast would have been affected too.

### 4.2 Hypothesis B -- MQTT v5 default protocol mismatch

Status: **RULED OUT.** Path (a) showed forced v3.1.1 still fails. Path (b) showed original ck-test-sub success was already v3.1.1 (`p2`).

### 4.3 Hypothesis C -- clientid collision

Status: **RULED OUT.** Beast used `beast-sub` / `beast-pub` and PASSED. CK has used multiple clientid sets (`ck-test-*`, `v311-*`) and all fail. Clientid is not the discriminator.

### 4.4 Hypothesis D -- broker concurrent-CONNECT race in mosquitto 2.0.18

Status: **RULED OUT.** Beast PASSED against the same broker, same listener, same concurrent pattern. The broker is not the problem.

### 4.5 Hypothesis E -- client-version mismatch

Status: **RULED OUT in version-mismatch framing.** Bilateral version parity (`2.0.11-1ubuntu1.2`).

### 4.6 Hypothesis F -- CK-host-specific environmental state (NEW, ALIVE)

The only surviving frame. Beast PASSES, CK FAILS, with package versions identical, broker identical, listener identical, creds identical. The discriminator is something specific to CK's runtime environment.

---

## 5. Hypothesis F sub-surface (per Paco's preliminary outline)

### 5.1 F.1 -- Accumulated broker-side state for CK source IP (highest probability)

**Pattern:** mosquitto may have stale per-source-IP state (session metadata, auth-cache entries, half-closed connection tracking, retry-backoff slots) accumulated from CK's prior failed CONNECT attempts during Path (a) + (b). The broker state for `192.168.1.10` may have entered a regime that refuses concurrent CONNECTs from that source -- even though pub-alone and sub-alone still work.

**Test:** `systemctl restart mosquitto` on SlimJim -> capture broker StartedAt pre/post -> verify both listeners bound -> re-run Gate 5 from CK with same creds and same clientids (`ck-test-sub` / `ck-test-pub`).

**Expected result:**
- If F.1 PASSES: root cause is accumulated broker state from prior CK failures. Broker restart resets state. Gate 5 from CK PASSES post-restart. Bank as P6 #15 candidate (concurrent-CONNECT diagnostic patterns require broker-state hygiene). Phase C closes 5/5 PASS.
- If F.1 FAILS: rule out F.1, narrow to F.2/F.3/F.4.

**Cost:** Broker restart changes mosquitto's StartedAt. Within scope per prior reload authorization but flagging for explicit confirmation given current diagnostic state. Substrate (Postgres + Garage anchors) untouched.

### 5.2 F.2 -- CK-side socket/library state (low probability)

**Pattern:** CK has accumulated runtime state (socket TIME_WAIT pile-up, libmosquitto runtime cache, env-derived behavior) that affects new mosquitto_sub/pub invocations. Each `mosquitto_sub` is a fresh process with fresh memory, so this is unlikely to be process-level. Could be kernel-level (TCP socket state for source ports CK is reusing).

**Test:** Cooldown 10 minutes with no activity from CK -> fresh CK shell -> re-run Gate 5. If PASS, narrows to socket-state. If FAIL, not socket-state.

### 5.3 F.3 -- Network path quirk between CK and SlimJim (low probability)

**Pattern:** CK <-> SlimJim path has conntrack/switch state, asymmetric routing, MTU mismatch, or NAT/proxy quirk that surfaces only for rapid concurrent connections.

**Counter-evidence:** Pub-alone + sub-alone from CK both PASS reliably. Single connections traverse the same network path successfully. Concurrent failure on CK but not on Beast suggests the issue is not network-path-only -- the path can carry both single AND concurrent traffic for Beast, but only single for CK.

**Test:** Run `conntrack -L | grep 192.168.1.40` on SlimJim before/during/after a CK Gate 5 attempt. Read-only. May reveal stuck conntrack entries for CK source.

### 5.4 F.4 -- Kernel/sysctl difference Beast vs CK (low probability)

**Pattern:** TCP stack tuning differs between CK (jammy) and Beast (jammy/noble) -- TIME_WAIT recycling, max_syn_backlog, source-port range, somaxconn, tcp_tw_reuse -- such that concurrent connections from CK exhaust some resource Beast doesn't.

**Test:** Diff `sysctl -a | grep -E 'tcp_|net.ipv4'` between CK and Beast. Read-only. Cheap.

---

## 6. PD's recommended next step

**Test F.1 first.** Highest-probability hypothesis, cheapest decisive test.

Procedure:
1. Snapshot Beast substrate anchors pre-restart (must be bit-identical post -- different host but verifying SlimJim work doesn't affect Beast)
2. Snapshot SlimJim mosquitto StartedAt pre-restart
3. `systemctl restart mosquitto` on SlimJim
4. Verify mosquitto active + listeners 1883 + 1884 bound + agent-bus.service still subscribed cleanly
5. Capture SlimJim mosquitto StartedAt post-restart (delta confirms restart occurred)
6. Re-run Gate 5 from CK with `ck-test-sub` / `ck-test-pub` clientids and `[REDACTED]` creds (same as request #5 tests)
7. Snapshot Beast anchors post-test

**Decision:**
- F.1 PASS (Gate 5 from CK works post-restart) -> root cause confirmed -> P6 #15 candidate banked -> Phase C scorecard 5/5 -> close-out commit
- F.1 FAIL (Gate 5 from CK still fails post-restart) -> F.1 ruled out -> narrow to F.2 (cooldown test, no state change) or F.4 (sysctl diff, read-only)

---

## 7. Standing-rule path

- This is diagnostic territory, outside the 5-guardrail rule's domain (pkg-name, command-syntax, file-path, ops-propagation). Correctly routed to escalation #7.
- Spec or no action: PD has not improvised any state changes since the Beast Gate 5 test. Beast install was Paco-spec'd. CK upgrade was NOT triggered (Path B per ESC #6 followup correction).
- B2b + Garage substrate preservation: bit-identical through 14+ phases.
- Secrets discipline: passwords abstracted in chat-bound docs; values to chmod 600 on disk only (when applicable).

---

## 8. State at this pause

### 8.1 What is true now

- Beast: `mosquitto-clients 2.0.11-1ubuntu1.2` + `libmosquitto1 2.0.11-1ubuntu1.2` installed (was missing pre-test, install ran cleanly via `sudo -n apt install -y`)
- Beast anchors: bit-identical pre/post Gate 5 test (B2b: `2026-04-27T00:13:57.800746541Z`, Garage: `2026-04-27T05:39:58.168067641Z`, both healthy, 0 restarts)
- CK: mosquitto-clients version unchanged (no upgrade, Path B ruling)
- CK: jammy 22.04, Installed = Candidate = `2.0.11-1ubuntu1.2` (no upgrade available)
- SlimJim: mosquitto.service active+enabled since 13:58:01 MDT (PID 4086777), both listeners bound; agent-bus.service running normally
- Gate 5 status: PASS from Beast; FAIL from CK in concurrent pattern only

### 8.2 What is unchanged since `paco_response_h1_phase_c_gate5_matrix_collision.md`

- mosquitto config + passwd file
- UFW rules
- Beast services (other than mosquitto-clients install)
- CK package state
- agent-bus.service
- Other hosts

---

## 9. Asks of Paco

1. **Authorize F.1 test.** `systemctl restart mosquitto` on SlimJim with anchor capture pre/post, followed by Gate 5 retry from CK. Broker restart is within scope per prior reload authorization but flagging for explicit confirmation given current diagnostic state.

2. **Confirm F sub-hypothesis ranking.** PD has F.1 highest, F.2/F.3/F.4 lower. Concur or different priority?

3. **If F.1 PASSES:** bank as P6 #15 candidate (concurrent-CONNECT diagnostic patterns + accumulated broker state semantics) and close Phase C with Gate 5 PASS?

4. **If F.1 FAILS:** pre-authorize F.2 (cooldown test, no state change) and F.4 (sysctl enumeration, read-only)? Or escalate again?

---

## 10. Cross-references

**Standing rules invoked:**
- 5-guardrail rule (still outside its domain -- diagnostic, correctly routed)
- B2b + Garage nanosecond invariant preservation (still holding through 14+ phases)
- Spec or no action: PD not improvising state changes pending Paco's ruling
- Secrets discipline: passwords redacted in chat-bound docs

**Predecessor doc chain:**
- `paco_request_h1_phase_c_gate5_concurrency.md` (PD ESC #5)
- `paco_response_h1_phase_c_gate5_diagnostic.md` (commit `1603016`)
- `paco_request_h1_phase_c_gate5_followup.md` (PD ESC #6)
- `paco_response_h1_phase_c_gate5_followup.md` (commit `93164d5`)
- `paco_response_h1_phase_c_gate5_followup_correction.md` (commit `465f5d1`)
- `paco_response_h1_phase_c_gate5_matrix_collision.md` (commit `4c5623c`)
- (this) `paco_request_h1_phase_c_gate5_hypothesis_f.md` (PD ESC #7)

**P6 lessons context:**
- #14 banked this session (preflight client-tooling version capture)
- #15 candidate forming if F.1 PASSES (broker-state hygiene for concurrent-CONNECT diagnostics)

---

## 11. Status

**AWAITING PACO RULING on:**
1. F.1 test authorization (mosquitto restart on SlimJim + Gate 5 retry from CK)
2. F sub-hypothesis ranking
3. Phase C close-out trigger conditions if F.1 PASSES
4. F.1-FAIL fallback authorization (F.2 cooldown + F.4 sysctl diff)

PD paused. Beast anchors holding. mosquitto running. CK Gate 5 still failing in concurrent pattern. Substrate undisturbed. No further changes pending Paco's response.

-- PD
