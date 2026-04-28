# Paco -> PD ruling -- H1 Phase C Gate 5 diagnostic path (paths a + b parallel, CK upgrade authorized)

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-28 (Day 73)
**Spec:** `tasks/H1_observability.md` section 7
**Predecessor:** `docs/paco_request_h1_phase_c_gate5_concurrency.md` (PD ESC #5)
**Status:** **APPROVED** -- run paths (a) + (b) in parallel, CK mosquitto-clients upgrade pre-authorized

---

## TL;DR

Three rulings:

1. **Diagnostic path: run (a) `-V mqttv311` test AND (b) read full mosquitto.log in parallel.** Both are read-only / no security surface change. Cheapest decisive test.
2. **CK mosquitto-clients upgrade PRE-AUTHORIZED** under guardrail 5 carve-out. Client tooling is operational; doesn't touch broker's auth surface.
3. **Phase C retrospective ASK CONFIRMED.** Will fold into close-out review. P6 candidate #14 is real: spec preflight should include client-tooling version capture, not just service version.

---

## 1. Why both (a) and (b), not just one

PD's hypothesis space is plausible but unproven. Three plausible roots: client-version v5 default mismatch (B), per-user/per-IP connection limit (A), session takeover semantics (C). The mosquitto log evidence I just read suggests the failures cluster on rapid second-connections from same source IP -- that's consistent with B (v5 protocol-level rejection) OR C (session takeover) but not cleanly diagnostic between them.

**Path (a) test (`-V mqttv311`)** decisively rules out v5 quirk (Hypothesis B):
- If forces-v3.1.1 fixes Gate 5: B confirmed, document and ship
- If forces-v3.1.1 doesn't fix: B ruled out, fall to A or C diagnosis

**Path (b) (full log read)** is zero-cost evidence we should have already and gives ground truth:
- Captures complete chronology of CONNECT / SUBACK / DISCONNECT events
- Shows whether mosquitto reports session-takeover, rate-limit, or auth-reject internally
- Mosquitto's CONNACK 5 (`not authorised`) is overloaded -- it represents multiple reject reasons that the log_text might distinguish

Running them in parallel costs ~5 minutes total. No additional state change beyond what's already approved.

## 2. Path (a) -- force MQTT v3.1.1 on both ends

```bash
# Sub side (background) on CK
ssh ciscokid 'MQTT_PASSWORD=axela mosquitto_sub -V mqttv311 -h 192.168.1.40 -p 1884 \
  -u alexandra -P "$MQTT_PASSWORD" -t test/v311 --id v311-sub -d -W 5' \
  > /tmp/H1_phase_c_v311_sub.txt 2>&1 &
SUB_PID=$!
sleep 1.5

# Pub side from CK
ssh ciscokid 'MQTT_PASSWORD=axela mosquitto_pub -V mqttv311 -h 192.168.1.40 -p 1884 \
  -u alexandra -P "$MQTT_PASSWORD" -t test/v311 --id v311-pub -d -m "hello-v311"' \
  > /tmp/H1_phase_c_v311_pub.txt 2>&1
PUB_RC=$?

wait $SUB_PID 2>/dev/null
SUB_RC=$?

echo "v3.1.1 pub rc: $PUB_RC"
echo "v3.1.1 sub rc: $SUB_RC"
echo "--- sub output ---"
cat /tmp/H1_phase_c_v311_sub.txt
echo "--- pub output ---"
cat /tmp/H1_phase_c_v311_pub.txt
```

**Pass criterion:** `pub rc=0` AND `sub` received `hello-v311` payload.

## 3. Path (b) -- full mosquitto.log capture

```bash
sudo cp /var/log/mosquitto/mosquitto.log /tmp/H1_phase_c_mosquitto_full.log
sudo chown jes:jes /tmp/H1_phase_c_mosquitto_full.log
wc -l /tmp/H1_phase_c_mosquitto_full.log
head -80 /tmp/H1_phase_c_mosquitto_full.log     # broker start to first auth events
sed -n '/ck-test-sub/,/ck-test-pub.*not authorised/ p' /tmp/H1_phase_c_mosquitto_full.log | head -30
```

Look specifically for any line containing `'not authorised'` and capture the full context around it. If mosquitto is hitting an internal rate limit, session takeover, or memory limit, the log line *before* the disconnect often tells us.

## 4. Decision tree

```
IF (a) v3.1.1 fixes Gate 5:
  -> Bank as P6 #14: "MQTT broker/client version-default mismatch (broker v2.0.18 default v5,
     client v2.0.11 default v3.1.1) can produce silent CONNACK 5 on concurrent same-credential
     connections. Force protocol version explicitly when broker and client major-version-skew exists."
  -> Phase C scorecard updated to use -V mqttv311 in Gate 5 commands
  -> Phase C closes

ELIF (a) doesn't fix but (b) reveals rate-limit / session-takeover / specific reject reason:
  -> File new paco_request with specific log evidence
  -> Targeted ruling on the specific issue

ELIF (a) doesn't fix and (b) shows nothing diagnostic:
  -> Upgrade CK mosquitto-clients to 2.0.18 (PRE-AUTHORIZED in section 5)
  -> Re-run Gate 5
  -> If still fails, file new paco_request -- we're now in mosquitto-2.0.18-version-skew territory and need broader investigation
```

## 5. CK mosquitto-clients upgrade -- PRE-AUTHORIZED

Apt-upgrade of mosquitto-clients on CK does NOT touch the broker's auth surface. It upgrades the *client tooling* PD uses to test. Same category as upgrading curl, jq, openssh-client. Carve-out applies (operational tooling propagation).

**Pre-authorization conditions:**
- Only if path (a) fails (v3.1.1 doesn't fix Gate 5) AND path (b) doesn't reveal a smoking gun
- Use `apt install --only-upgrade mosquitto-clients libmosquitto1` on CK
- Document in Phase C review per guardrail 4
- Re-run Gate 5 after upgrade

This is informational pre-authorization -- PD doesn't need to come back for ratification before running it IF the conditions hold.

## 6. Phase C retrospective -- CONFIRMED

Fold into Phase C close-out review (when 5/5 PASS lands). Single section noting:
- 5 escalations across Phase C (per_listener_settings, reload, gate5-concurrency, plus the rule-update ones)
- Each escalation banked durable knowledge: P6 #12 (set+e), P6 #13 (major-version preflight), guardrail 5 + carve-out, P6 #14 (if v3.1.1 fixes it)
- Lesson for future spec preflight: capture **client-tooling version** at preflight, not just service-on-target-host version. Mismatched broker-vs-client-versions are a real failure class.
- Bank as P6 lesson #15 candidate (separate from #14): "Spec preflight must capture client-side tooling version on each consuming host that participates in smoke tests."

If the retrospective surfaces other generalizable patterns from these 5 escalations, banks them as additional P6 lessons.

## 7. Acknowledgments

- **PD's discipline through 5 escalations is correct.** Each one was novel, none rabbit-holed, each banked something durable. Cost is real but compounding value is realer.
- **The 5-guardrail rule's "safe zones"** PD identified (pkg-name, command-syntax, file-path, ops-propagation) is a useful framing. The Gate 5 concurrency issue genuinely lives outside those zones -- it's a **diagnostic-hypothesis** issue, not a mechanical-substitution issue. The 5-guardrail rule was never designed to cover these. Diagnostic hypotheses correctly route to escalation. Working as intended.
- **The agent_bus / mqtt_subscriber.py finding in section 1.1 of the request:** the log shows it briefly connecting at the start of the day. It's a separate issue (script broken: connects to BROKER='192.168.1.40' on PORT=1883 which is loopback-only-bound and unreachable from CK over LAN). Not the cause of Gate 5 failure but worth noting for a future H1 v0.2 cleanup. Bank as informational / P5 carryover. Not in Phase C scope.

## 8. Standing rules in effect

- Per-step review docs in `/home/jes/control-plane/docs/`
- B2b + Garage nanosecond anchor preservation
- 5-guardrail rule with carve-out (this case is OUTSIDE the rule's domain -- it's diagnostic, not mechanical correction)
- Spec or no action: Phase C continues following spec section 7 with explicit diagnostic detours authorized here
- Secrets discipline: passwords REDACTED in review
- P6 lessons banked: 13 (next: #14 candidate from path (a) result)

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_c_gate5_diagnostic.md`

-- Paco
