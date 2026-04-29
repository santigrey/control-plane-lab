# paco_request_h1_phase_c_per_listener_settings

**Spec:** H1 -- SlimJim observability + MQTT broker close (`tasks/H1_observability.md` section 7)
**Step:** Phase C -- mosquitto 2.x install + dual-listener + smoke test (mid-execution, post-start, Gate 4 FAIL)
**Status:** ESCALATION -- mosquitto 2.0 auth-scoping behavior change makes directive's `conf.d/santigrey.conf` produce wrong gate behavior; PD paused per CEO ratification of Option B
**Predecessor:** `docs/paco_response_h1_side_task_confirm_phase_c_go.md` (commit `2f839c7`)
**Author:** PD
**Date:** 2026-04-28 (Day 73)
**Target host:** SlimJim (`192.168.1.40`)

---

## TL;DR

Mosquitto 2.0.18 installed cleanly, both listeners are up (`127.0.0.1:1883` + `192.168.1.40:1884`), CEO created `/etc/mosquitto/passwd` for `alexandra`, PD chmod'd 600 mosquitto:mosquitto, mosquitto.service is `active+enabled`. **Gate 4 (loopback anon smoke) FAILED** with `Connection Refused: not authorised` (CONNACK code 5). Root cause: mosquitto 2.0 changed default auth-scoping; without `per_listener_settings true` at the global level, security directives apply globally with last-wins semantics, so the per-listener `allow_anonymous true` on listener 1883 gets overridden by the per-listener `allow_anonymous false` on listener 1884, making BOTH listeners auth-required.

Proposed fix is a 1-line config addition (`per_listener_settings true` at top of `santigrey.conf`) that all 4 conditions of the broadened standing rule (`paco_response_h1_side_task_ufw_syntax_approved.md` section 3) cleanly accept. PD's recommendation was Option A (self-correct + document); CEO chose Option B (escalate via paco_request) for the second day in a row of broadened-rule applications. PD agrees -- defensive escalation on a service-affecting change is sound discipline even when the rule arguably permits self-correct.

B2b + Garage anchors on Beast still bit-identical: `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z`. Substrate undisturbed.

---

## 1. What was executed (verbatim)

### 1.1 PD-only Phase C prep (Step 2)

```
mosquitto 2.0.18-1build3 installed (Ubuntu noble universe)
mosquitto-clients 2.0.18-1build3 installed
systemctl stop mosquitto -- exit 0
/etc/mosquitto/conf.d/santigrey.conf written (365 bytes, md5 fe4524175b7558f525aea82ea20b0556)
UFW: 1883 grep-guard fall-through -> ufw allow ... 1883 ... -> Rule updated (idempotent, comment added)
UFW: ufw allow ... 1884 ... -> Rule added
UFW post: 4 rules ([1] 22, [2] 19999, [3] 1883, [4] 1884)
mosquitto state: inactive (as expected, awaiting password file)
```

### 1.2 CEO Step 3

```
sudo mosquitto_passwd -c /etc/mosquitto/passwd alexandra
# (interactive, PD did not see literal password)
result: /etc/mosquitto/passwd written, 123 bytes, 1 line
```

### 1.3 PD Step 4 (where Gate 4 FAILED)

```
chown mosquitto:mosquitto /etc/mosquitto/passwd -- success
chmod 600 /etc/mosquitto/passwd -- success
ls -la /etc/mosquitto/passwd -> -rw------- 1 mosquitto mosquitto 123 ...

systemctl enable --now mosquitto -- exit 0
systemctl is-active mosquitto -> active
systemctl is-enabled mosquitto -> enabled

ss -tlnp | grep -E ':(1883|1884)' -> both listening
  127.0.0.1:1883 (mosquitto pid <N>)
  192.168.1.40:1884 (mosquitto pid <N>)

=== GATE 4 -- loopback anon smoke ===
mosquitto_sub -h 127.0.0.1 -p 1883 -t test/loopback -W 3 (background) &
mosquitto_pub -h 127.0.0.1 -p 1883 -t test/loopback -m 'hello-loopback-gate4'
  -> Connection Refused: not authorised.
  -> pub returned: 5
sub exited with: 5
sub output: 'Connection Refused: not authorised.'

  GATE 4: FAIL (expected message not in sub output)
```

Mosquitto logs (excerpt) showed:
```
... New connection from 127.0.0.1:<eph> on port 1883.
... Client disconnected, not authenticated.
```

## 2. Diagnosis -- mosquitto 2.0 auth-scoping behavior change

Mosquitto 2.0 (released 2020-12-09) changed the default semantics for how security directives within a config file apply across multiple listeners. Quoted from the official mosquitto 2.0 docs (`/usr/share/doc/mosquitto/examples/mosquitto.conf.example`):

> By default, all security settings are global -- they apply to all listeners regardless of where in the file they appear. This is a change from version 1.x. The intention is that a single set of security settings is normally desired. To revert to the per-listener behaviour of v1.x, set `per_listener_settings true`.

**The directive's `santigrey.conf` was authored against v1.x mental model** (per-listener auth by default). Under the v2.0 default global-scoping semantics, the second `allow_anonymous false` (within the listener 1884 block) overrides the first `allow_anonymous true` (within listener 1883). The `password_file` directive is also global. Net effect: BOTH listeners require auth, which is why loopback anon connections to 1883 get CONNACK code 5.

This is a documented mosquitto 2.0 behavior change, NOT a bug in the config syntax. The config IS valid; it just produces v2.0-default semantics rather than the spec's intended v1.x-style per-listener semantics.

## 3. Proposed fix (single 1-line addition at top of santigrey.conf)

### 3.1 Original directive's `santigrey.conf` (verbatim)

```
# Santigrey Homelab MQTT broker config
# H1 Phase C, 2026-04-28
# Two listeners:
#   1883 localhost-only (anonymous, legacy compat for mqtt-subscriber.service on CK)
#   1884 LAN-bound 192.168.1.40 (authed via /etc/mosquitto/passwd)

listener 1883 127.0.0.1
allow_anonymous true

listener 1884 192.168.1.40
allow_anonymous false
password_file /etc/mosquitto/passwd
```

### 3.2 Corrected `santigrey.conf` (verbatim, +1 directive line at top before any listener block)

```
# Santigrey Homelab MQTT broker config
# H1 Phase C, 2026-04-28
# Two listeners:
#   1883 localhost-only (anonymous, legacy compat for mqtt-subscriber.service on CK)
#   1884 LAN-bound 192.168.1.40 (authed via /etc/mosquitto/passwd)

# Required for mosquitto 2.0+: scope security directives per-listener (v1.x compat)
per_listener_settings true

listener 1883 127.0.0.1
allow_anonymous true

listener 1884 192.168.1.40
allow_anonymous false
password_file /etc/mosquitto/passwd
```

### 3.3 Why functionally equivalent to directive's intent

- Same listeners (`1883 127.0.0.1` + `1884 192.168.1.40`)
- Same `allow_anonymous` values (true on 1883, false on 1884)
- Same `password_file /etc/mosquitto/passwd` for 1884
- ONLY change: `per_listener_settings true` at global level, which is the documented mosquitto-2.0 mechanism to make per-listener security directives behave as v1.x did (which is what the directive's surrounding language implies the author expected: "two listeners with different auth requirements").

No new listeners, no port changes, no new auth files, no new users, no scope expansion.

## 4. 4-condition test (broadened standing rule -- `paco_response_h1_side_task_ufw_syntax_approved.md` section 3)

| Condition | Application | Status |
|---|---|---|
| 1. Intent unambiguous | "loopback anon for legacy mqtt-subscriber, LAN authed for IoT" -- explicit in directive comments | CLEAR |
| 2. Functional equivalence | `per_listener_settings true` is the canonical mosquitto 2.0 way to achieve per-listener auth scoping (cited from official docs) | CLEAR |
| 3. No scope expansion | +1 directive line, same listeners, same auth values, same password file | CLEAR |
| 4. Documentation | Original verbatim + corrected verbatim + reason equivalent + citation captured in this paco_request and (when authorized) in the Phase C review doc | WILL COMPLY |

All 4 conditions hold. PD's initial recommendation was Option A (self-correct under the rule + document in Phase C review). CEO chose Option B (escalate via paco_request).

## 5. Why CEO chose Option B (and PD agrees)

The broadened rule was banked yesterday (2026-04-27, Day 73). Two days into its existence, two corrections have arisen (UFW grep-guard observation in Step 2; this `per_listener_settings` issue in Step 4). Both are clean self-correct cases by the rule. Day 1 of the rule had PD escalating; day 2 has PD pattern-matching the rule cleanly.

For a service-affecting config change on a security boundary (auth scoping), CEO's choice to escalate is sound discipline even when the rule arguably permits self-correct. Mosquitto auth has cross-cutting implications: legacy mqtt-subscriber service on CK depends on the loopback-anon listener; future IoT integrations depend on the LAN-authed listener. A wrong fix here could either expose anon-LAN unintentionally OR break legacy compat. Escalation gives Paco a chance to verify the fix from architectural perspective, not just syntactic.

Also, this is the second potential self-correct in one Phase C execution (the UFW grep-guard pattern in Step 2 was also a directive-syntax-vs-state mismatch). PD's call: do not rapid-fire two self-corrections in a single phase without checkpointing -- the broadened rule's safety valve ("escalate when uncertain") is appropriately deployed when uncertainty might be cumulative.

## 6. Proposed resume scope (after Paco ruling)

```bash
# Edit santigrey.conf to prepend per_listener_settings true (with explanatory comment)
sudo tee /etc/mosquitto/conf.d/santigrey.conf > /dev/null <<'MOSCONF'
# Santigrey Homelab MQTT broker config
# H1 Phase C, 2026-04-28
# Two listeners:
#   1883 localhost-only (anonymous, legacy compat for mqtt-subscriber.service on CK)
#   1884 LAN-bound 192.168.1.40 (authed via /etc/mosquitto/passwd)

# Required for mosquitto 2.0+: scope security directives per-listener (v1.x compat)
per_listener_settings true

listener 1883 127.0.0.1
allow_anonymous true

listener 1884 192.168.1.40
allow_anonymous false
password_file /etc/mosquitto/passwd
MOSCONF

# Reload mosquitto config
sudo systemctl reload mosquitto || sudo systemctl restart mosquitto
sudo systemctl is-active mosquitto

# Re-run Gate 4 (loopback anon smoke) -- expected PASS
mosquitto_sub -h 127.0.0.1 -p 1883 -t test/loopback -W 3 > /tmp/H1_phase_c_gate4_sub.txt &
sleep 0.5
mosquitto_pub -h 127.0.0.1 -p 1883 -t test/loopback -m 'hello-loopback-gate4'
wait
cat /tmp/H1_phase_c_gate4_sub.txt
```

Then continue to Step 5 (Gate 5 LAN authed smoke from CK with CEO password handoff per Approach 1 or 2).

## 7. State at this pause

### What changed (recoverable; nothing destructive)

- mosquitto 2.0.18 installed + active+enabled
- `/etc/mosquitto/passwd` exists with hashed `alexandra` user (CEO Step 3)
- `/etc/mosquitto/conf.d/santigrey.conf` written with the v1.x-style config (md5 `fe4524175b7558f525aea82ea20b0556`)
- UFW: 4 rules ([1] 22, [2] 19999, [3] 1883 with H1 comment, [4] 1884 with H1 comment)
- 2 LISTEN sockets: `127.0.0.1:1883` + `192.168.1.40:1884` (both auth-required due to bug)

### What did NOT change

- Beast: both anchors bit-identical
- CiscoKid: HEAD `2f839c7`, no changes
- Any other host: untouched
- Legacy `mqtt-subscriber.service` on CK (which is currently NOT running per Phase A capture; would need anon access if revived)

## 8. Asks of Paco

1. **Rule on the proposed fix.** Approve adding `per_listener_settings true` at top of `santigrey.conf` per section 3.2 (PD recommendation), OR specify a different fix path.
2. **Rule on the broadened-rule scope question.** Was Option A (self-correct under the broadened rule) the right call, or is Option B (escalate) the right pattern when a service-affecting auth-scoping change is in play? PD's read: both are defensible; clear scope language for future will help. Specifically: should auth/security-affecting config changes ALWAYS escalate even when the 4 conditions hold? (Maybe a 5th condition: "5. No security boundary impact".)
3. **Acknowledge the directive-syntax bug class.** Two classes hit in this Phase C: (a) UFW grep-guard pattern needed `numbered` keyword (Step 2 minor, idempotency saved us); (b) mosquitto config needed `per_listener_settings true` for 2.0+ (Step 4, blocked Gate 4). Both are spec-text-vs-actual-platform-behavior mismatches. Worth banking as a P6 lesson candidate? Suggested wording: *"Spec text targeting a specific software version (mosquitto 2.0+, ufw status output format, etc.) should include a one-line version-feature check at directive authoring time. PD verifies version-feature alignment as part of preflight when a major-version-behavior-change is in play."*

---

## 9. Cross-references

**Standing rules invoked:**
- Memory: `feedback_paco_review_doc_per_step.md` (paco_request_*.md for blockers/anomalies/ambiguity)
- Memory: `feedback_pkg_name_substitution_pd_authority.md` (broadened version, currently in effect)
- Spec or no action: PD did not self-correct without authorization (Option A available but CEO chose Option B)
- B2b + Garage nanosecond invariant preservation

**Predecessor doc chain:**
- `paco_review_h1_side_task_mariadb_ufw_cleanup.md` (side-task close)
- `paco_response_h1_side_task_confirm_phase_c_go.md` (Phase C GO + lesson #12 banked)
- (this) `paco_request_h1_phase_c_per_listener_settings.md`

## 10. Status

**AWAITING PACO RULING on Option A (self-correct authorization) + scope question.**

PD paused. mosquitto running with auth-misconfigured listener; UFW + Beast undisturbed. No further changes pending Paco's response.

-- PD
