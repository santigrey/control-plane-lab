# paco_review_h1_phase_c_mosquitto

**Spec:** H1 -- SlimJim observability + MQTT broker close (`tasks/H1_observability.md` section 7)
**Step:** Phase C -- mosquitto 2.x install + dual-listener + 5-gate smoke (CLOSE-OUT)
**Status:** AWAITING PACO FINAL CONFIRM + PHASE D GO
**Predecessor:** `docs/paco_response_h1_phase_c_gate5_hypothesis_f.md` (ESC #7 ruling: F.1 test authorized + F.1-PASS closure path defined + F.1-FAIL fallback pre-authorized)
**Author:** PD
**Date:** 2026-04-28 (Day 73)
**Target hosts:** SlimJim (`192.168.1.40`) primary; CiscoKid (`192.168.1.10`) + Beast (`192.168.1.152`) secondary

---

## TL;DR

Phase C closes **5/5 PASS** after a 7-escalation diagnostic arc. Gate 5 (LAN authed pub/sub from CK to SlimJim:1884) was the long-tail blocker; resolution path was Hypothesis F.1 -- accumulated mosquitto-internal per-source-IP state from extensive Phase C debug-session failed CONNECTs. Single corrective action: `systemctl restart mosquitto` on SlimJim. Gate 5 from CK then PASSES with full round-trip (`hello-from-ck-post-F1` payload received by sub). Negative-control test (wrong password from CK) returns `not authorised` -- auth layer intact. Beast `control-postgres-beast` + `control-garage-beast` nanosecond anchors **bit-identical pre/post** entire F.1 sequence (`2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z` -- holding through 14+ phases / ~38 hours). Two P6 lessons banked this phase: **#14** (spec preflight must capture client-side tooling version on each consuming host) and **#15** (broker-state hygiene for concurrent-CONNECT diagnostics -- restart before deeper investigation when single-host vs concurrent patterns diverge). Standing 5-guardrail rule extended with 5th guardrail (auth/security-boundary) and operational-propagation carve-out, both banked mid-phase.

---

## 1. ESC #1-#7 chain (Phase C cumulative)

| # | Trigger | Ruling | Banked output | Commit |
|---|---|---|---|---|
| 1 | mosquitto 2.0 default auth-scoping change made dual-listener config produce wrong gate behavior (Gate 4 FAIL with `CONNACK 5` on loopback anon) | `per_listener_settings true` prepended to `santigrey.conf`; resume from Gate 4 | 5th guardrail (auth/security-boundary always escalates); P6 #13 (major-version behavior-change preflight) | `f43a23d` |
| 2 | (inline) Approach 1 vs Approach 2 credential handoff selection at Gate 5 setup -- CEO ratified Approach 2 mid-execution | Approach 2 temp-password path approved within ESC #1 response thread (no separate request doc) | n/a (operational) | within `f43a23d` thread |
| 3 | (inline) `mosquitto_passwd` ownership deprecation warnings on `/etc/mosquitto/passwd` (mosquitto:mosquitto vs future-required root:root) | Defer migration to mosquitto upgrade; banked as P5 carryover | P5 (file ownership deprecation) | within ESC #4 ruling |
| 4 | Gate 5 FAIL post temp-password set -- mosquitto in-memory hash cache stale (passwd file mtime > broker MainPID start time) | `systemctl reload mosquitto` approved; SIGHUP re-read | guardrail 5 carve-out (operational propagation of CEO-authorized state changes at PD authority under 3 sub-conditions); P5 ownership deferral | `8c4c8c7` |
| 5 | Gate 5 FAIL post-reload under concurrent sub+pub-from-same-host pattern; sub-alone, pub-alone, local-pub-from-SlimJim all PASS; novel concurrency behavior outside 5-guardrail rule's domain | Diagnostic paths (a) `-V mqttv311` + (b) full mosquitto.log read approved; CK client upgrade pre-authorized contingent on Beast third-host result | n/a (diagnostic authorization) | `1603016` |
| 6 | Hypothesis B (MQTT v5 default mismatch) ruled out via path (a); path (b) revealed concurrent-CONNECT rejection pattern; Hypotheses D (broker concurrent-CONNECT race) + E (client-version mismatch) surface | Beast third-host test approved (Beast == known-working source); decision matrix bound "Beast PASSES → CK upgrade." Inline correction: agent_bus.py polluter premise self-corrected (it's working Alexandra infra connecting to anon listener 1883 by design, not a polluter). Beast result + CK/Beast version-parity finding triggered Path B (escalate, no upgrade) | P6 #14 (spec preflight must capture client-side tooling version on each consuming host) | `93164d5` (followup) → `4c5623c` (matrix_collision) |
| 7 | Beast Gate 5 PASSES end-to-end with `hello-from-beast` round-trip; CK/Beast both at `mosquitto-clients 2.0.11-1ubuntu1.2` (version-parity ruled out); Hypotheses A/B/C/D/E all eliminated; surviving frame is Hypothesis F (CK-host-specific environmental state) | F.1 test authorized (`systemctl restart mosquitto` on SlimJim → re-run Gate 5 from CK). F.4 sysctl diff + F.2 cooldown PD-self-auth pre-authorized as F.1-FAIL fallback. F.3 conntrack would require ESC #8. F.1-PASS closure path defined: negative-control test + Beast anchor preservation gate + P6 #15 candidate. | F.1 PASSED (this phase close); P6 #15 (broker-state hygiene for concurrent-CONNECT diagnostics) banked | (response doc on disk; this review folds the close-out commit) |

---

## 2. F.1 test execution (per ESC #7 ruling section 1.3)

### 2.1 Pre-test capture (SlimJim mosquitto + Beast anchors)

SlimJim mosquitto pre-restart (`/tmp/H1_phase_c_F1_mosquitto_pre.txt`):
```
MainPID=4086777
ActiveState=active
ActiveEnterTimestamp=Tue 2026-04-28 13:58:01 MDT
```

Beast anchors pre-restart (`/tmp/H1_phase_c_F1_anchors_pre.txt`):
```
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

### 2.2 Restart

```
sudo systemctl restart mosquitto
sleep 2
```

Exit 0. No errors.

### 2.3 Post-restart verification

SlimJim mosquitto post-restart (`/tmp/H1_phase_c_F1_mosquitto_post.txt`):
```
MainPID=50604
ActiveState=active
ActiveEnterTimestamp=Tue 2026-04-28 17:41:13 MDT
```

New MainPID (`50604` ≠ pre `4086777`) confirms restart actually occurred.

Both listeners bound to new PID:
```
LISTEN 0  100  192.168.1.40:1884  0.0.0.0:*  users:(("mosquitto",pid=50604,fd=6))
LISTEN 0  100     127.0.0.1:1883  0.0.0.0:*  users:(("mosquitto",pid=50604,fd=5))
```

agent_bus.service still running (reconnect on its own 120s cycle, per ESC #6 followup_correction self-correction).

### 2.4 Gate 5 retry from CK (the decisive test)

Subscriber output (`/tmp/H1_phase_c_F1_ck_sub.txt` on CiscoKid):
```
Client ck-test-sub sending CONNECT
Client ck-test-sub received CONNACK (0)
Client ck-test-sub sending SUBSCRIBE (Mid: 1, Topic: test/F1, QoS: 0, Options: 0x00)
Client ck-test-sub received SUBACK
Subscribed (mid: 1): 0
Client ck-test-sub received PUBLISH (d0, q0, r0, m0, 'test/F1', ... (21 bytes))
hello-from-ck-post-F1
Timed out
Client ck-test-sub sending DISCONNECT
```

Publisher output (`/tmp/H1_phase_c_F1_ck_pub.txt` on CiscoKid):
```
Client ck-test-pub sending CONNECT
Client ck-test-pub received CONNACK (0)
Client ck-test-pub sending PUBLISH (d0, q0, r0, m1, 'test/F1', ... (21 bytes))
Client ck-test-pub sending DISCONNECT
```

Return codes: `sub rc: 27` (mosquitto_sub `-W 5` clean timeout exit after publish received), `pub rc: 0` (clean exit). Full end-to-end round-trip from CK source. **F.1 PASS confirmed.**

Command template (password REDACTED -- on file with CEO, set via `mosquitto_passwd -b /etc/mosquitto/passwd alexandra <REDACTED>`):
```
mosquitto_sub -h 192.168.1.40 -p 1884 -u alexandra -P [REDACTED] \
  -t test/F1 --id ck-test-sub -d -W 5
mosquitto_pub -h 192.168.1.40 -p 1884 -u alexandra -P [REDACTED] \
  -t test/F1 --id ck-test-pub -d -m 'hello-from-ck-post-F1'
```

### 2.5 Beast anchor preservation post-test

```
=== anchors_pre ===
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
=== anchors_post ===
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
=== diff ===
IDENTICAL
```

Nanosecond-bit-identical. B2b + Garage substrate undisturbed by F.1 sequence.

---

## 3. Negative-control test (per ESC #7 ruling section 3.1)

Wrong-password test from CK to verify auth still enforced post-restart:

```
mosquitto_pub -h 192.168.1.40 -p 1884 -u alexandra -P wrong-password \
  -t test/negative -m 'should-fail'
```

Output (`/tmp/H1_phase_c_F1_negative_control.txt` on CiscoKid):
```
Connection error: Connection Refused: not authorised.
Error: The connection was refused.
```

Expected `CONNACK 5 not authorised` -- received. Auth layer intact post-restart. **No CONNACK 0 false-positive.** Phase C 5/5 closure conditions all satisfied.

---

## 4. Phase C 5-gate acceptance scorecard

| Gate | Spec wording | Resolution path | Result |
|---|---|---|---|
| 1 | mosquitto 2.x installed + service active | `mosquitto 2.0.18-1build3` from Ubuntu noble universe; `systemctl is-active` = active; both listeners (1883 loopback + 1884 LAN) bound | **PASS** |
| 2 | UFW LAN-only allow on 1884; pre-existing 1883 rule preserved idempotently | UFW rules `[3] 1883/tcp ALLOW 192.168.1.0/24` + `[4] 1884/tcp ALLOW 192.168.1.0/24` (idempotency grep-guard authorized in Phase A → B handoff) | **PASS** |
| 3 | Per-listener auth: 1883 anon allowed (loopback only), 1884 password-required (LAN) | Resolved via ESC #1 (`per_listener_settings true`); verified by gate-1 listener bind topology and gate-4/5 behavior | **PASS** |
| 4 | Loopback anon smoke (`mosquitto_pub` to 127.0.0.1:1883 from SlimJim) | PASSED post-ESC #1 fix | **PASS** |
| 5 | LAN authed pub/sub from CK to 192.168.1.40:1884 | PASSED post-ESC #7 F.1 (mosquitto restart cleared accumulated per-source-IP state) + negative-control verified auth still enforced | **PASS** |

**Phase C internal scorecard: 5/5 PASS.**

---

## 5. P6 lessons banked this phase

### 5.1 P6 #14 -- Spec preflight must capture client-side tooling version on each consuming host

> Spec preflight must capture client-side tooling version on each consuming host that participates in smoke tests. Even when version comparison ultimately disproves the working hypothesis (as it did here -- Beast 2.0.11 == CK 2.0.11), preflight version capture catches matrix-collision bugs before they trigger no-op actions. Banked from H1 Phase C Day 73 ESC #6 → #7 transition: ESC #6 ruling matrix bound "Beast PASSES → CK upgrade" without preflight version-parity validation; PD's Step 2 preflight surfaced the parity, exposing the binding as invalid before the no-op upgrade triggered.

Source: `paco_response_h1_phase_c_gate5_matrix_collision.md` (commit `4c5623c`).

### 5.2 P6 #15 -- Broker-state hygiene for concurrent-CONNECT diagnostics

> When diagnosing concurrent-connection failures against a long-running message broker (mosquitto, RabbitMQ, NATS, Kafka, etc.), accumulated per-source-IP state (rejection lists, session tables, retry-backoff slots, half-closed connection tracking, auth-cache entries) can persist across daemon-internal hygiene boundaries. If single-connection tests pass but concurrent-pattern tests fail from the same source -- AND the same concurrent pattern works from a different source -- broker restart should be a first-line diagnostic step before deeper investigation. Restart clears accumulated state and discriminates "broker remembers this client badly" from "actual concurrent-connection bug." Banked from H1 Phase C Day 73 ESC #7, after 6 prior escalations narrowed to CK-specific environmental state with bilateral package version parity ruled out and Beast third-host PASS confirmed broker is fine.

Source: `paco_response_h1_phase_c_hypothesis_f_test.md` (ESC #7 ruling). Confirmed by F.1 PASS this phase close.

P6 lessons banked total: **15** (was 13 at Phase C entry; +2 this phase).

---

## 6. Standing rules state at Phase C close

- **5-guardrail rule** extended with **5th guardrail** (auth/credential/security-boundary corrections always escalate, ESC #1 banking).
- **Guardrail 5 carve-out** banked (operational propagation of CEO-authorized state changes is at PD authority under 3 sub-conditions: (a) on-disk state already complete + CEO-authorized, (b) propagation via canonical/documented mechanism, (c) failure mode bounded). ESC #4 banking.
- **B2b + Garage nanosecond anchor preservation** holding through 14+ phases / ~38 hours. Standing invariant. Bit-identical pre/post entire Phase C arc.
- **Spec or no action** discipline maintained throughout 7 escalations. No infrastructure change without paco_response or banked carve-out citation.
- **Per-step paco_review docs** in `/home/jes/control-plane/docs/`. This review fulfills the Phase C close-out per-step requirement.
- **Secrets discipline:** `alexandra` MQTT password REDACTED in this review; held by CEO; written to `/etc/mosquitto/passwd` via `mosquitto_passwd` only (PD never saw literal value).

---

## 7. State at end of Phase C

### SlimJim (`192.168.1.40`)
- `mosquitto 2.0.18-1build3` active + enabled
- MainPID: `50604` (post-F.1-restart at `2026-04-28 17:41:13 MDT`)
- Listeners: `127.0.0.1:1883` (anon, loopback) + `192.168.1.40:1884` (password-required, LAN)
- `/etc/mosquitto/conf.d/santigrey.conf` -- includes `per_listener_settings true` (ESC #1 fix)
- `/etc/mosquitto/passwd` -- mode 600 mosquitto:mosquitto, 1 user (`alexandra`), root:root migration deferred to upgrade (P5)
- UFW: `[1] 22 | [2] 19999 | [3] 1883 LAN | [4] 1884 LAN`
- agent_bus.service running (reconnect on 120s cycle to anon 1883 loopback by design)

### CiscoKid (`192.168.1.10`)
- mosquitto-clients `2.0.11-1ubuntu1.2` (version-parity with Beast confirmed)
- Gate 5 LAN authed round-trip verified post-F.1 + post-negative-control
- mqtt_subscriber.py status -- still flagged as broken (BROKER=192.168.1.40 PORT=1883 unreachable from CK over LAN per ESC #6 followup_correction); orthogonal to Phase C scope, banked for v0.2

### Beast (`192.168.1.152`)
- `control-postgres-beast` healthy, RestartCount=0, anchor `2026-04-27T00:13:57.800746541Z` preserved
- `control-garage-beast` healthy, RestartCount=0, anchor `2026-04-27T05:39:58.168067641Z` preserved
- mosquitto-clients `2.0.11-1ubuntu1.2` (third-host PASS evidence host)

---

## 8. Cross-references

**ESC chain doc trail (Phase C cumulative):**
- `paco_request_h1_phase_c_per_listener_settings.md` → `paco_response_h1_phase_c_per_listener_approved.md` (ESC #1, commit `f43a23d`)
- `paco_request_h1_phase_c_mosquitto_reload.md` → `paco_response_h1_phase_c_reload_approved.md` (ESC #4, commit `8c4c8c7`)
- `paco_request_h1_phase_c_gate5_concurrency.md` → `paco_response_h1_phase_c_gate5_diagnostic.md` (ESC #5, commit `1603016`)
- `paco_request_h1_phase_c_gate5_followup.md` → `paco_response_h1_phase_c_gate5_followup.md` + `paco_response_h1_phase_c_gate5_followup_correction.md` + `paco_response_h1_phase_c_gate5_matrix_collision.md` (ESC #6, commits `93164d5` + `4c5623c`)
- `paco_request_h1_phase_c_gate5_hypothesis_f.md` → `paco_response_h1_phase_c_hypothesis_f_test.md` + `paco_response_h1_phase_c_gate5_hypothesis_f.md` (ESC #7)

**P6 lesson source docs:**
- P6 #13 (preflight major-version behavior-change) -- ESC #1 ruling
- P6 #14 (preflight client-side version capture) -- ESC #6 matrix_collision
- P6 #15 (broker-state hygiene for concurrent-CONNECT) -- ESC #7 hypothesis_f_test (banked candidate, confirmed by this F.1 PASS)

**Spec section refs:**
- `tasks/H1_observability.md` section 7 (Phase C body)
- Pending spec amendment in this close-out commit fold: P6 #14 + #15 preflight checks

---

## 9. Asks of Paco

1. **Confirm Phase C 5/5 gates PASS** against the captured evidence (sections 2-4).
2. **Confirm 7-ESC chain narrative** (section 1 table) matches Paco's ledger.
3. **Confirm P6 #14 + #15 banked** as final (no longer candidate state).
4. **Authorize Phase D GO** -- node_exporter fan-out across CK / Beast / Goliath / KaliPi per `tasks/H1_observability.md` section 8.

---

## 10. Status

**AWAITING PACO FINAL CONFIRM + PHASE D GO.**

PD is paused. SlimJim mosquitto restarted (one corrective action this phase close). Beast + Garage anchors undisturbed. CiscoKid orchestrator/MCP/PG infrastructure untouched throughout Phase C arc. Phase C close-out commit folds: this review + memory file (5g+carve-out) + SESSION + paco_session_anchor + CHECKLIST audit entry + spec amendment.

Ready to begin Phase D (node_exporter fan-out) on Paco's go.

-- PD
