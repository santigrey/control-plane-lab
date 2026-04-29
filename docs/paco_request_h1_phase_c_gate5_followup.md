# paco_request_h1_phase_c_gate5_followup

**Spec:** H1 -- SlimJim observability + MQTT broker close (`tasks/H1_observability.md` section 7)
**Step:** Phase C -- Gate 5 followup (post diagnostic paths a + b)
**Status:** ESCALATION #6 (Phase C cumulative). Hypothesis B definitively ruled out. New hypotheses D + E surface. Diagnostic path direction needed.
**Predecessor:** `docs/paco_response_h1_phase_c_gate5_diagnostic.md` (commit `1603016`, paths a+b approved + CK upgrade pre-authorized)
**Author:** PD
**Date:** 2026-04-28 (Day 73)
**Target hosts:** SlimJim (`192.168.1.40`) + CiscoKid (`192.168.1.10`)

---

## TL;DR

Path (a) `-V mqttv311` test FAILED -- Hypothesis B (MQTT v5 default mismatch) definitively ruled out. Independently confirmed by path (b) log evidence showing the original successful ck-test-sub run was already MQTT v3.1.1 (`p2` flag).

Path (b) full mosquitto.log read revealed:
- **Two distinct rejection patterns** at the broker -- successful CONNECTs produce a `New client connected as X (p2, c1, k60, u'alexandra')` log line; failed CONNECTs produce only a `New connection from X` + `Client X disconnected, not authorised` pair, with no `New client connected` line in between. Rejection happens at CONNECT-packet validation, BEFORE the client is registered as connected.
- **Background polluter (P5 finding, not on Gate 5 code path):** `agent_bus.py` running on SlimJim since Apr 24 connects to 127.0.0.1:1883 (anon listener) every 120 seconds and is rejected as not authorised. Worth stopping to clean diagnostic noise.

Config, passwd, and bind topology all verified clean. Same creds work in single-connection patterns (pub-alone, sub-alone, local-pub) but fail in concurrent patterns (sub-bg + pub from CK). Same protocol (v3.1.1), same client tooling, same broker -- outcome correlated only with concurrency.

Two new hypotheses surface: (D) concurrent CONNECT race in mosquitto 2.0.18 with `per_listener_settings true`, or (E) client-side issue in mosquitto-clients 2.0.11 producing malformed second concurrent CONNECT from the same library instance.

B2b nanosecond anchor: `2026-04-27T00:13:57.800746541Z` -- holding. Garage anchor: `2026-04-27T05:39:58.168067641Z` -- holding. Substrate untouched across all diagnostic work.

---

## 1. Path (a) result -- `-V mqttv311` forced both ends

### 1.1 Test run (CK)

```
v3.1.1 pub rc: 5, sub rc: 5
--- sub output ---
Connection error: Connection Refused: not authorised.
Client v311-sub sending CONNECT
Client v311-sub received CONNACK (5)
Client v311-sub sending DISCONNECT
--- pub output ---
Connection error: Connection Refused: not authorised.
Error: The connection was refused.
Client v311-pub sending CONNECT
Client v311-pub received CONNACK (5)
```

Both sub and pub got CONNACK 5 with `-V mqttv311`. Sub failure here is a state change from the request #5 baseline (where sub-alone passed) -- but only because the test pattern was sub-bg+pub-fg, with both connections firing in close sequence.

### 1.2 Conclusion

Hypothesis B ruled out via two independent lines:
- Forcing v3.1.1 didn't fix the failure
- Path (b) log evidence shows the original successful ck-test-sub was already v3.1.1 (`p2` in connect log)

---

## 2. Path (b) result -- full mosquitto.log analysis

185-line capture at `/tmp/H1_phase_c_mosquitto_full.log` on SlimJim.

### 2.1 Successful CONNECT log pattern (the original ck-test-sub PASS)

```
1777406521: New client connected from 192.168.1.10:58402 as ck-test-sub (p2, c1, k60, u'alexandra').
```

Format: source-IP + clientid + protocol + clean_session + keepalive + username. The `(p2, c1, k60, u'alexandra')` parse:
- `p2` = MQTT v3.1.1 (mosquitto codes v3.1.0=p1, v3.1.1=p2, v5=p5)
- `c1` = clean_session=1
- `k60` = keepalive 60s
- `u'alexandra'` = username

This confirms PD's original ck-test-sub PASS was already MQTT v3.1.1. Hypothesis B was never alive.

### 2.2 Failed CONNECT log pattern (ck-test-pub, v311-sub, v311-pub)

```
1777406523: New connection from 192.168.1.10:58412 on port 1884.
1777406523: Client ck-test-pub disconnected, not authorised.
```

Two log lines, no `New client connected as X` between them. The `Client X disconnected, not authorised` message appears when mosquitto's CONNECT-packet handler returns failure. The client ID is captured (parsed from the CONNECT packet) but never registered into the broker's connected-clients table.

Same pattern repeats for v311-sub and v311-pub:

```
1777409054: New connection from 192.168.1.10:33510 on port 1884.
1777409054: Client v311-sub disconnected, not authorised.
1777409056: New connection from 192.168.1.10:33520 on port 1884.
1777409056: Client v311-pub disconnected, not authorised.
```

Within ~2 seconds: sub New connection -> sub disconnected, pub New connection -> pub disconnected. Both at CONNECT-validation stage.

### 2.3 What the log pattern rules in / out

Rules IN:
- Rejection happens at CONNECT packet validation (parse clientid, validate creds, return CONNACK)
- Mosquitto received the packet, parsed the clientid, then rejected
- Pattern is reproducible -- three failed runs (ck-test-pub, v311-sub, v311-pub) all show the same pattern

Rules OUT:
- Network-level reject (TCP would have closed before broker logged anything)
- Listener bind/topology issue (sockets bound correctly, see section 3.3)
- TLS or transport issue (no TLS configured on this listener)

What the log does NOT distinguish: WHY mosquitto's CONNECT validator returns failure. CONNACK 5 is overloaded. Mosquitto 2.0 returns CONNACK 5 for: bad-username-password, anonymous-not-allowed, plugin-rejected, max-connections-exceeded, and several other internal validation failures. The current `log_type` (`error,warning,notice,information` default) does not surface the specific reason code internally.

---

## 3. Config + passwd + bind topology verified

### 3.1 santigrey.conf

```
per_listener_settings true

listener 1883 127.0.0.1
allow_anonymous true

listener 1884 192.168.1.40
allow_anonymous false
password_file /etc/mosquitto/passwd
```

md5 `33346a752e0ef3b90cba0e6b08ca551f` -- matches PD's tracked anchor. Config is exactly what spec calls for.

### 3.2 /etc/mosquitto/passwd

- 1 entry: username `alexandra`, hash `<REDACTED-IN-REVIEW-OUTPUT>`
- mode 600, owner mosquitto:mosquitto
- File present, readable by broker, format conforms to mosquitto_passwd output

### 3.3 Listening sockets (verified via ss -lntp)

```
LISTEN 0 100  192.168.1.40:1884  0.0.0.0:*  users:(("mosquitto",pid=4086777,fd=6))
LISTEN 0 100     127.0.0.1:1883  0.0.0.0:*  users:(("mosquitto",pid=4086777,fd=5))
```

mosquitto PID 4086777 holding both. Bind topology matches spec exactly.

### 3.4 mosquitto.conf top-level

```
persistence true
persistence_location /var/lib/mosquitto/
log_dest file /var/log/mosquitto/mosquitto.log
include_dir /etc/mosquitto/conf.d
```

Standard. No per-user limits, no max_connections, no ACL files. The only auth surface is via the per-listener `password_file` directive in santigrey.conf.

---

## 4. agent_bus.py polluter -- P5 carryover, NOT on Gate 5 code path

### 4.1 Process detected on SlimJim

```
jes 1141247 1 0 Apr24 ?  00:00:23  /usr/bin/python3 /home/jes/agent_bus.py
```

Running since Apr 24 (4-day uptime), parent PID 1 (orphaned/daemonized), as user `jes`. PD has not yet read agent_bus.py contents but the broker log shows it connecting from 127.0.0.1:* to port 1883 every 120 seconds and being rejected as not authorised.

### 4.2 Why this is rejected on the anon listener

With `per_listener_settings true` + `allow_anonymous true` on listener 1883: anonymous connections (no creds in CONNECT packet) are accepted. BUT if the client SENDS credentials and they don't validate against an existing passwd file, mosquitto 2.0 rejects the connection. The 1883 listener has no `password_file` directive -- no creds can be validated -- any client sending creds gets CONNACK 5.

agent_bus.py is most likely sending credentials (probably env-derived) that have nowhere to validate against. This explains the every-120s rejection on what should be an unauthenticated listener.

### 4.3 Not on Gate 5 code path

Gate 5 is on listener 1884 (LAN authed). agent_bus is on listener 1883 (loopback anon). Different listeners. agent_bus is not directly causing Gate 5 failures.

### 4.4 But it should be stopped before next diagnostic round

Reasons:
- Cleans up broker log signal (no more 120s noise during diagnostic)
- Removes the variable of "is concurrent broker activity affecting auth state" from the hypothesis space
- The agent_bus.py script itself is broken (request #5 bonus finding noted BROKER=192.168.1.40 PORT=1883 -- 1883 is loopback-only so it can't reach the broker over LAN; the local connections from 127.0.0.1 we see in the log must be a different code path or local fallback)

PD recommends stopping `agent_bus.py` before the next Gate 5 diagnostic. Approval needed because killing a long-running user process changes node state.

---

## 5. Updated hypothesis space

### Hypothesis A -- per-user / per-IP connection limit (FROM REQUEST #5)

Status: NOT ELIMINATED but lowered priority.

Counter-evidence: pub-alone-3-attempts succeeded with 3 sequential CONNECTs from same IP, same user, same listener -- within seconds of each other. If a per-user/per-IP limit existed, those would have failed too.

### Hypothesis B -- MQTT v5 protocol default mismatch (FROM REQUEST #5)

Status: DEFINITIVELY RULED OUT. Path (a) showed forced v3.1.1 still fails. Path (b) showed original ck-test-sub success was already v3.1.1.

### Hypothesis C -- client_id collision (FROM REQUEST #5)

Status: NOT ELIMINATED but unlikely. Each test uses unique clientids (ck-test-sub/pub, v311-sub/pub).

### Hypothesis D (NEW) -- concurrent CONNECT race in mosquitto 2.0.18 with per_listener_settings true

Pattern: pub-alone PASS (3/3), sub-alone PASS, but sub-bg+pub-fg -- second connection rejected at CONNECT-validation stage. Mosquitto's auth validation might have a shared-state issue when multiple CONNECTs arrive in rapid sequence on the same per-listener-settings auth-context.

This would be a broker bug or undocumented behavior. Mosquitto 2.0.x has had concurrent-connection issues in the past (per release notes). 2.0.18 is from 2024 -- could have a regression here.

### Hypothesis E (NEW) -- client-side malformed second CONNECT in mosquitto-clients 2.0.11

CK clients are mosquitto-clients 2.0.11 (from older noble snapshot or 22.04 carryover). Broker is 2.0.18. The 7-patch gap could include a fix in libmosquitto's CONNECT-packet construction when the library is invoked twice in close sequence (e.g., from sub-bg + pub-fg in the same shell).

This hypothesis is exactly what the CK upgrade pre-authorization is for. If E is the root cause, `apt install --only-upgrade mosquitto-clients libmosquitto1` on CK should fix it.

---

## 6. PD has NOT tested

- Stopping agent_bus.py and re-running Gate 5 (could change broker state in a way that helps or hurts)
- Running Gate 5 from a third host (Beast or Goliath) -- would distinguish CK-specific (Hypothesis E) from broker-side (Hypothesis D)
- Reading agent_bus.py contents to understand what it's doing
- Increasing mosquitto `log_type all` (would require config change + reload -- guardrail 5 territory; not self-correctible)
- Running the Gate 5 test from the SlimJim host itself (eliminates network variable; isolates broker behavior)

---

## 7. Asks of Paco

### 7.1 Authorize stopping agent_bus.py

Recommend `kill 1141247` (or `pkill -f agent_bus.py`) on SlimJim before next diagnostic round. Cleans broker log signal and removes one variable from the hypothesis space.

PD authority sufficient or escalation needed?

### 7.2 Direction on next diagnostic step

Options ranked by PD's preferred order:

(i) **Test Gate 5 from a third host (Beast or Goliath).** If it PASSES from Beast/Goliath but FAILS from CK -- Hypothesis E (CK client library) confirmed -- trigger CK upgrade per pre-authorization. If it FAILS from Beast/Goliath too -- Hypothesis D (broker race) confirmed -- escalate further. Most decisive single test.

(ii) **Trigger CK mosquitto-clients upgrade per pre-authorization.** Skips the third-host test. Riskier diagnostically -- if upgrade DOESN'T fix it, we still don't know if D or A is the cause. But it's faster.

(iii) **Increase mosquitto `log_type all` on broker.** Would require config change + reload (guardrail 5 territory). Would surface the specific internal reason mosquitto returns CONNACK 5. Most expensive but most informative.

(iv) **Run Gate 5 test from SlimJim host itself.** Eliminates the network variable. If it PASSES from SlimJim's own loopback -- the failure is somehow IP-source or LAN-listener specific. If it FAILS from SlimJim -- broker-internal, narrows to Hypothesis D.

PD bias: (i) first, then if confirmed CK-specific -> (ii) per pre-auth. If (i) shows broker-side, escalate before (iii) which touches config.

### 7.3 If E is the most likely root cause, do we go straight to CK upgrade?

The pre-authorization in `paco_response_h1_phase_c_gate5_diagnostic.md` section 5 was conditional: "Only if path (a) fails AND path (b) doesn't reveal a smoking gun." Path (a) DID fail. Path (b) revealed evidence (the connect-stage rejection pattern) but not a definitive smoking gun pointing at one specific root.

Asking Paco to rule on whether the current evidence triggers the pre-auth conditions -- or whether we should test from Beast/Goliath first to isolate CK-vs-broker before mutating CK tooling.

### 7.4 Phase C escalation count

This is escalation #6 (cumulative across Phase C). Each one banked durable knowledge: P6 #12 (set+e), P6 #13 (major-version preflight), guardrail 5 + carve-out, P6 #14 candidate (broker/client default-MQTT-version preflight) -- and now likely P6 #15 candidate (concurrent CONNECT diagnostic patterns in mosquitto 2.0.x).

PD acknowledges the cost. Each escalation has been disciplined. Compounding value remains net positive.

---

## 8. State at this pause

### What is true now

- mosquitto.service: active+enabled, MainPID 4086777, Active since 13:58:01 MDT today
- Listeners: `127.0.0.1:1883` (anon) + `192.168.1.40:1884` (authed) -- both bound, verified ss -lntp
- /etc/mosquitto/passwd: 1 entry (`alexandra`), mode 600 mosquitto:mosquitto
- /etc/mosquitto/conf.d/santigrey.conf: md5 `33346a752e0ef3b90cba0e6b08ca551f` -- matches anchor
- Gate 4 (loopback anon): PASS
- Gate 5 (LAN authed sub-bg + pub from CK): FAIL (concurrent pattern), Hypothesis B ruled out
- agent_bus.py polluter: still running, still polluting log every 120s
- Beast anchors: bit-identical pre/post Path (a)+(b)+config-read (B2b: `2026-04-27T00:13:57.800746541Z`, Garage: `2026-04-27T05:39:58.168067641Z`)

### What is unchanged since `paco_response_h1_phase_c_gate5_diagnostic.md`

- mosquitto config (santigrey.conf md5 unchanged)
- /etc/mosquitto/passwd (line count + mode + owner unchanged)
- UFW rules
- Beast services
- Other hosts
- CK mosquitto-clients version (still 2.0.11)

---

## 9. Cross-references

**Standing rules invoked:**
- 5-guardrail rule (this case is OUTSIDE the rule's domain -- diagnostic, not mechanical correction; correctly routed to escalation)
- B2b + Garage nanosecond invariant preservation (still holding)
- Spec or no action: PD did not improvise additional config changes after Gate 5 began failing
- Secrets discipline: passwd hashes redacted as `<REDACTED-IN-REVIEW-OUTPUT>`; values to chmod 600 on disk only

**Predecessor doc chain:**
- `paco_response_h1_phase_c_per_listener_approved.md` (commit `f43a23d`)
- `paco_request_h1_phase_c_mosquitto_reload.md` (PD ESC #4)
- `paco_response_h1_phase_c_reload_approved.md` (commit `8c4c8c7`)
- `paco_request_h1_phase_c_gate5_concurrency.md` (PD ESC #5)
- `paco_response_h1_phase_c_gate5_diagnostic.md` (commit `1603016`)
- (this) `paco_request_h1_phase_c_gate5_followup.md` (PD ESC #6)

---

## 10. Status

**AWAITING PACO RULING on:**
1. Authorization to stop agent_bus.py (section 7.1)
2. Direction on next diagnostic step -- recommend (i) third-host test (section 7.2)
3. CK upgrade pre-auth trigger conditions met yes/no (section 7.3)

PD paused. mosquitto running, Gate 5 failing in concurrent pattern only. Substrate undisturbed. No further changes pending Paco's response.

-- PD
