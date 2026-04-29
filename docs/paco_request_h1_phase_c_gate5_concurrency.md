# paco_request_h1_phase_c_gate5_concurrency

**Spec:** H1 -- SlimJim observability + MQTT broker close (`tasks/H1_observability.md` section 7)
**Step:** Phase C -- Gate 5 (LAN authed pub/sub from CK), post-reload-+-restart, post-fresh-temp-password
**Status:** ESCALATION -- novel mosquitto concurrency pattern; PD diagnosed but cannot resolve via the 5-guardrail rule (does not fit pkg-name / command-syntax / ops-propagation classes)
**Predecessor:** `docs/paco_response_h1_phase_c_reload_approved.md` (commit `8c4c8c7`, reload approved + carve-out + ownership P5)
**Author:** PD
**Date:** 2026-04-28 (Day 73)
**Target host:** SlimJim (`192.168.1.40`) + CiscoKid (`192.168.1.10`)

---

## TL;DR

Gate 5 fails ONLY under the sub-bg-then-pub-from-same-host pattern. Sub-alone from CK works. Pub-alone from CK works. Local pub from SlimJim itself works. **Concurrent sub+pub from CK with same `alexandra` user**: pub gets `CONNACK 5` not authorised. Negative test (wrong password) also returns `CONNACK 5`, confirming auth IS enforced. This isn't a stale cache, isn't a directive bug, isn't a config-syntax issue. It's some mosquitto 2.0 concurrency / session / connection-tracking behavior PD hasn't been able to characterize despite ~10 diagnostic iterations.

PD escalates because (a) this is novel auth-related behavior outside the 5-guardrail rule's domains, (b) further diagnostic loops are not productive without Paco's architectural lens, (c) Phase C has already had 4 escalations and this one merits the 5th rather than rabbit-holing further.

B2b + Garage anchors on Beast still bit-identical: `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z`. Substrate undisturbed.

---

## 1. Confirmed-working scenarios (auth works)

### 1.1 Sub-alone from CK (multiple attempts)

```
Client ck-test-sub sending CONNECT
Client ck-test-sub received CONNACK (0)             <-- AUTH OK
Client ck-test-sub sending SUBSCRIBE (Topic: test/explicit, QoS: 0)
Client ck-test-sub received SUBACK
Subscribed (mid: 1): 0
[5 second timeout, no message received]
Client ck-test-sub sending DISCONNECT
returned: 27 (timeout, expected)
```

### 1.2 Pub-alone from CK (3 consecutive attempts via `for` loop)

```
attempt 1: returned 0
attempt 2: returned 0
attempt 3: returned 0
```

All pub-alone attempts: CONNACK 0, message accepted by broker, clean DISCONNECT.

### 1.3 Local pub from SlimJim itself to 192.168.1.40:1884

```
mosquitto_pub -h 192.168.1.40 -p 1884 -u alexandra -P '[REDACTED]' -t test/loopback-from-slimjim -m 'test-locally'
local-pub returned: 0
```

### 1.4 Negative test from CK (wrong password)

```
mosquitto_pub -h 192.168.1.40 -p 1884 -u alexandra -P 'wrong-password-test' -t test/lan -m 'should-fail-badauth'
  Connection error: Connection Refused: not authorised.
  returned: 5
```

Wrong-password rejection PROVES auth is enforced and working at the protocol level.

## 2. Failing scenario (the actual Gate 5 pattern)

### 2.1 Pub-during-sub-bg from CK (with explicit clientids + debug)

Sub backgrounded, sleep 1.5s for sub to fully subscribe, then pub fires:

```
=== sub debug (captured to /tmp during sub run) ===
Client ck-test-sub sending CONNECT
Client ck-test-sub received CONNACK (0)              <-- sub auth OK
Client ck-test-sub sending SUBSCRIBE (Topic: test/explicit, QoS: 0)
Client ck-test-sub received SUBACK
Subscribed (mid: 1): 0                                <-- sub subscribed

=== pub debug (foreground, fired during sub) ===
Connection error: Connection Refused: not authorised.
Client ck-test-pub sending CONNECT
Client ck-test-pub received CONNACK (5)              <-- pub AUTH FAIL
pub returned: 5

=== sub continued ===
[5s timeout]
Client ck-test-sub sending DISCONNECT                 <-- sub disconnected, never received any message
```

Key: same user `alexandra`, same password `[REDACTED]`, same broker, but the SECOND concurrent connection (pub) gets CONNACK 5 while the FIRST (sub) succeeded.

### 2.2 Failure is reproducible across attempts

Gate 5 retry-1, retry-2, retry-3, retry-final, plus the explicit-clientid debug test all show same pattern. Pub-during-sub-bg fails with CONNACK 5. Pub-alone or sub-alone always succeeds.

## 3. Environment versions

### 3.1 SlimJim broker
```
mosquitto 2.0.18-1build3
mosquitto-clients 2.0.18-1build3
libmosquitto1 2.0.18-1build3
(installed today via apt from Ubuntu 24.04 noble universe)
```

### 3.2 CiscoKid client
```
mosquitto-clients 2.0.11-1ubuntu1.2
libmosquitto1 2.0.11-1ubuntu1.2
(pre-installed, presumably from earlier Ubuntu 22.04 install or older noble snapshot)
```

**Version mismatch:** CK clients are mosquitto 2.0.11; SlimJim broker is 2.0.18. Difference of 7 patch releases. In normal MQTT 3.1.1/v5 protocol terms, both should interop fine (protocol-level compatibility). But specific CONNECT-handshake quirks could differ.

### 3.3 Mosquitto journal during failures

```
Apr 28 13:58:01 sloan1 mosquitto[4086777]: 1777406281: Loading config file /etc/mosquitto/conf.d/santigrey.conf
[no entries during the failing sub-bg + pub attempts -- mosquitto's default log_type doesn't include auth events]
```

Mosquitto default log_type is `error,warning,notice,information`. Auth failures log at `notice` level (which IS included by default in noble's package), but no entries appear. Possible that mosquitto is logging to a different log_dest than journald (mosquitto.conf has `log_dest file /var/log/mosquitto/mosquitto.log`).

Read-only diagnostic of `/var/log/mosquitto/mosquitto.log` would clarify; PD has not done this yet to keep escalation focused.

## 4. Hypothesis space (3 candidates)

### 4.1 Hypothesis A: per-user connection limit / session uniqueness

Mosquitto 2.0 may have specific behavior where a SECOND CONNECT with the same `alexandra` user is rejected when one is already active. CONNACK 5 (`not authorised`) is what mosquitto returns for connection-limit-exceeded in some 2.0.x versions per scattered forum reports.

**Counterevidence:** documentation does not show `max_connections per user` is on by default in mosquitto 2.0.18. If it were a per-user limit, it would also affect pub-then-sub orderings -- but PD has not tested that order.

### 4.2 Hypothesis B: client-version / MQTT-version-default mismatch

CK mosquitto-clients 2.0.11 may default to MQTT v5 connection attempts; SlimJim 2.0.18 broker may have a v5-specific quirk that's triggered by concurrent same-credential connections from same-IP. Forcing `-V mqttv311` on both ends might bypass.

**Untested.** This was the "Option B" path PD considered before escalating.

### 4.3 Hypothesis C: client-id collision in auto-generated form

Despite using `--id ck-test-sub` and `--id ck-test-pub` explicitly in the debug test, CONNACK 5 still occurs. Rules out clientid-collision as primary cause UNLESS mosquitto rejects based on some other client-discriminating field (e.g., source IP + same auth attempt within short window).

## 5. PD has NOT tested

- Pub-then-sub ordering (pub first, then sub immediately) -- might give clue about which connection direction is the limiting factor
- `-V mqttv311` flag on both ends to force MQTT v3.1.1 protocol (rule out v5 quirk)
- Reading `/var/log/mosquitto/mosquitto.log` for richer auth-event logging (mosquitto's primary log_dest)
- Pub from a third host (Beast or Goliath) to rule out CK-IP-specific issue
- Setting `log_type all` in santigrey.conf (would require additional reload, plus a config change subject to guardrail 5 -- not self-correctible without ratification)

## 6. PD recommendation: Paco rules on next diagnostic step

PD's bias is toward Hypothesis B (MQTT v5 quirk on noble broker with older client). Cheapest test: force `-V mqttv311` on both CK clients. If that fixes Gate 5, the issue is documented. If it doesn't, we know it's a connection-tracking issue (Hypothesis A) and need to look at mosquitto internals.

Alternative: read `/var/log/mosquitto/mosquitto.log` to see what mosquitto actually reports during the failing connection. This is read-only and might give us the actual reason code or message that we're missing.

## 7. Asks of Paco

1. **Rule on diagnostic path.** Paco's preferred next step:
   (a) Force `-V mqttv311` on CK sub + pub, retry Gate 5 (Hypothesis B test)
   (b) Read `/var/log/mosquitto/mosquitto.log` for richer auth-event logging
   (c) Test pub-then-sub ordering reversal (Hypothesis A elimination)
   (d) Test from third host (Beast or Goliath)
   (e) Increase mosquitto verbosity via `log_type all` in santigrey.conf (requires ratification)
   (f) Other diagnostic direction

2. **Rule on whether to upgrade CK mosquitto-clients to 2.0.18.** If client-version mismatch is the root cause, the proper fix is `apt install --only-upgrade mosquitto-clients` on CK. This would change CK's auth-related tooling, which might trigger guardrail 5. Pre-authorize, leave to PD authority, or escalate?

3. **Acknowledge: Phase C is now 5 escalations deep.** PD has been disciplined about each one (each was novel and outside the rule's safe zones). But the cost is real. After Gate 5 resolves, suggest a brief retrospective in the close-out review on whether the H1 spec needed more preflight -- `mosquitto --version` capture at preflight, MQTT v5 compatibility check, broker-vs-client version alignment check.

## 8. State at this pause

### What is true now

- mosquitto.service: active+enabled, MainPID 4086777, ActiveEnter 13:58:01 MDT
- Listeners: `127.0.0.1:1883` (loopback anon) + `192.168.1.40:1884` (LAN authed) both bound
- `/etc/mosquitto/passwd`: 1 user (`alexandra`), hashed temp password "[REDACTED]", mode 600 mosquitto:mosquitto
- `/etc/mosquitto/conf.d/santigrey.conf`: md5 `33346a752e0ef3b90cba0e6b08ca551f` (per_listener_settings true + dual listener)
- UFW: 4 rules ([1] 22, [2] 19999, [3] 1883, [4] 1884)
- Gate 4 (loopback anon): PASS
- Gate 5 (LAN authed sub-bg + pub from CK): FAIL (concurrency edge case)
- Negative tests (wrong password): correctly rejected with CONNACK 5
- Beast anchors: bit-identical pre/post all of Phase C

### What is unchanged (not touched since paco_response_h1_phase_c_reload_approved.md)

- mosquitto config
- /etc/mosquitto/passwd
- UFW rules
- Beast services
- Other hosts

## 9. Asks of Paco (summary)

1. Diagnostic path direction (section 7.1, choose a-f or other)
2. CK mosquitto-clients upgrade authorization
3. Phase C retrospective ask (informational)

---

## 10. Cross-references

**Standing rules invoked:**
- Memory: `feedback_paco_review_doc_per_step.md` (paco_request_*.md for novel/blocking issues)
- Memory: `feedback_pkg_name_substitution_pd_authority.md` (5-guardrail rule, currently in effect, ineffective for novel issues outside its 4 domains: pkg-name, command-syntax, file-path, ops-propagation)
- Spec or no action: PD did not improvise additional config changes after Gate 5 began failing
- B2b + Garage nanosecond invariant preservation

**Predecessor doc chain:**
- `paco_response_h1_phase_c_per_listener_approved.md` (commit `f43a23d`, per_listener_settings + 5th guardrail + P6 #13)
- `paco_request_h1_phase_c_mosquitto_reload.md` (PD ESC #4)
- `paco_response_h1_phase_c_reload_approved.md` (commit `8c4c8c7`, reload approved + carve-out + ownership P5)
- (this) `paco_request_h1_phase_c_gate5_concurrency.md` (PD ESC #5)

## 11. Status

**AWAITING PACO RULING on diagnostic path + CK upgrade authorization.**

PD paused. mosquitto running, Gate 5 failing in concurrent-pattern only. UFW + Beast undisturbed. No further changes pending Paco's response.

-- PD
