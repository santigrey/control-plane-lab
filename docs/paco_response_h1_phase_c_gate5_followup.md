# Paco -> PD ruling -- H1 Phase C Gate 5 followup (ESC #6 resolved)

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-28 (Day 73)
**Spec:** `tasks/H1_observability.md` section 7
**Predecessor:** `docs/paco_request_h1_phase_c_gate5_followup.md` (PD ESC #6)
**Status:** **APPROVED** -- agent_bus stop authorized; third-host test directed; CK upgrade pre-auth held pending result

---

## TL;DR

Three rulings:

1. **Stop agent_bus.py: AUTHORIZED** under guardrail 5 carve-out. Operational cleanup, not security surface change.
2. **Next diagnostic step: Path (i) third-host test from Beast.** Most decisive single test in current hypothesis space (D vs E).
3. **CK upgrade pre-auth: HOLD until third-host result.** Pre-auth conditions strictly require both path (a) fail AND no smoking gun -- partial smoking gun in path (b). Third-host test discriminates D from E; pre-auth auto-triggers IF Beast PASSES.

PD's hypothesis framing in section 5 is correct. PD's recommendation order in section 7.2 (third-host test first, then conditional CK upgrade) is correct. PD's escalation discipline through 6 cumulative escalations remains net-positive value.

---

## 1. Ruling on stopping agent_bus.py -- AUTHORIZED

### 1.1 Why this fits guardrail 5 carve-out

agent_bus.py is a broken background script (BROKER=192.168.1.40 PORT=1883 against a loopback-only listener -- per request #5 bonus finding). It cannot be doing useful work because it cannot connect. Stopping it is operational cleanup:

- (a) On-disk state change: PD is not modifying the script, the broker config, the passwd file, or any auth surface. Just sending SIGTERM to a process.
- (b) Canonical mechanism: `pkill -f agent_bus.py` is standard process termination.
- (c) Bounded failure: worst case is the process exits and stays exited. No daemon to break, no service to disrupt -- it's not even reaching the broker.

Carve-out applies. PD self-authorize.

### 1.2 Procedure

```bash
ps aux | grep -v grep | grep agent_bus.py    # capture pre-state PID + start time
pkill -f agent_bus.py
sleep 1
ps aux | grep -v grep | grep agent_bus.py || echo 'agent_bus.py gone'
```

Document in Phase C review under guardrail 4 (citation: this paco_response).

### 1.3 Bank as P5

agent_bus.py needs reauthoring -- it's currently misconfigured (targets unreachable listener). Separate spec, NOT in Phase C scope. Bank as P5 for v0.2 cleanup pass: "agent_bus.py: rewrite to use correct broker (192.168.1.40:1884 with auth, NOT loopback :1883) OR retire if functionally redundant with mqtt_subscriber.py."

Note: mqtt_subscriber.py on CK has the same misconfiguration (request #5 bonus finding) -- it sets BROKER='192.168.1.40' PORT=1883 but 1883 is loopback-only. Both scripts are broken in the same way. Likely both are Day-67-era scaffolding from before the dual-listener design landed.

---

## 2. Ruling on next diagnostic step -- Path (i) third-host test from Beast

### 2.1 Why third-host first

Path (i) is the cleanest discriminator between Hypothesis D (broker concurrent-CONNECT race) and Hypothesis E (CK client library issue):

- Same broker, same listener, same creds, same protocol
- Only variable changed: source host (and therefore source-IP and client-tooling version)
- If Beast passes: broker is fine, CK-specific
- If Beast fails identically: broker-side, mosquitto 2.0.18 has the bug

This test costs ~5 minutes and decisively narrows the hypothesis space.

### 2.2 Why not the others (i ranked first)

- (ii) CK upgrade direct: faster IF E is right, but if D is right we mutate CK for no benefit and still don't have answer
- (iii) `log_type all` config change: requires reload (PD self-auth under carve-out, that's fine) but still doesn't tell us if D or E without third-host test anyway
- (iv) Gate 5 from SlimJim itself: useful but tests loopback-from-broker, not LAN-from-third-host -- different network path, less decisive

Path (i) wins on decisiveness per minute spent.

### 2.3 Procedure

```bash
# Pre-flight: is mosquitto-clients on Beast?
ssh beast 'apt list --installed 2>/dev/null | grep mosquitto-clients' || \
  ssh beast 'sudo apt install -y mosquitto-clients'

# Capture Beast's mosquitto-clients version (P6 #14 candidate evidence)
ssh beast 'dpkg -l mosquitto-clients libmosquitto1 2>/dev/null | grep -E "^ii" | awk "{print \$2, \$3}"' \
  > /tmp/H1_phase_c_beast_clients_ver.txt
cat /tmp/H1_phase_c_beast_clients_ver.txt

# Beast anchor preservation pre-test
ssh beast "docker inspect control-postgres-beast control-garage-beast --format '{{.Name}} StartedAt={{.State.StartedAt}} health={{.State.Health.Status}} restarts={{.RestartCount}}'" \
  > /tmp/H1_phase_c_beast_anchors_pre.txt

# Gate 5 from Beast (sub-bg + pub-fg pattern, same as failing CK pattern)
ssh beast 'mosquitto_sub -h 192.168.1.40 -p 1884 -u alexandra -P axela \
  -t test/beast --id beast-sub -d -W 5' \
  > /tmp/H1_phase_c_beast_sub.txt 2>&1 &
SUB_PID=$!
sleep 1.5
ssh beast 'mosquitto_pub -h 192.168.1.40 -p 1884 -u alexandra -P axela \
  -t test/beast --id beast-pub -d -m "hello-from-beast"' \
  > /tmp/H1_phase_c_beast_pub.txt 2>&1
PUB_RC=$?
wait $SUB_PID 2>/dev/null
SUB_RC=$?

echo "Beast sub rc: $SUB_RC, pub rc: $PUB_RC"
cat /tmp/H1_phase_c_beast_sub.txt
cat /tmp/H1_phase_c_beast_pub.txt

# Beast anchor preservation post-test
ssh beast "docker inspect control-postgres-beast control-garage-beast --format '{{.Name}} StartedAt={{.State.StartedAt}} health={{.State.Health.Status}} restarts={{.RestartCount}}'" \
  > /tmp/H1_phase_c_beast_anchors_post.txt
diff /tmp/H1_phase_c_beast_anchors_pre.txt /tmp/H1_phase_c_beast_anchors_post.txt && echo 'anchors bit-identical'
```

Beast anchor preservation gate: the apt install + Gate 5 from Beast must NOT touch control-postgres-beast or control-garage-beast. Standing invariant continues holding.

### 2.4 Decision matrix from result

| Beast result | Conclusion | Next action (PD) |
|---|---|---|
| Beast PASSES Gate 5 (sub + pub roundtrip) | Hypothesis E confirmed (CK-side library) | Auto-trigger CK upgrade per Ruling 3 below; re-run Gate 5 from CK |
| Beast FAILS Gate 5 same CONNACK 5 pattern | Hypothesis D confirmed (broker concurrent-CONNECT race) | Escalate ESC #7 with Beast log evidence; broker-bug territory |
| Beast partial (sub passes, pub fails OR vice versa) | New hypothesis territory | Escalate ESC #7 with details |

---

## 3. Ruling on CK upgrade pre-auth -- HOLD pending Beast result

### 3.1 Why hold

`paco_response_h1_phase_c_gate5_diagnostic.md` section 5 stated: "Only if path (a) fails AND path (b) doesn't reveal a smoking gun."

Strict reading:
- Path (a) failed: TRUE (v3.1.1 force test rejected)
- Path (b) smoking gun: PARTIAL -- log evidence narrowed the rejection stage (CONNECT-validation, not auth-flow), but did not point at a single root cause (D and E both fit the log pattern)

Partial smoking gun ≠ definitive smoking gun. The pre-auth conditions are not yet cleanly met. Third-host test makes the determination cleaner.

### 3.2 Auto-trigger condition

If Beast PASSES Gate 5:
- Hypothesis D ruled out (broker is fine -- it served Beast successfully)
- Hypothesis E confirmed by elimination (only CK-specific variable remaining is the older client tooling)
- CK upgrade now has clear diagnostic justification
- Pre-auth automatically triggers -- PD self-issues:
  ```bash
  ssh ciscokid 'sudo apt install --only-upgrade mosquitto-clients libmosquitto1'
  # then re-run Gate 5 from CK with original creds
  ```
- Document in Phase C review per guardrail 4
- No new paco_request needed for the upgrade itself; document inline

If Beast FAILS Gate 5: do NOT upgrade CK. The bug is broker-side. Different fix path.

If Beast partial: do NOT upgrade CK. New hypothesis territory; escalate.

---

## 4. P6 lessons -- holding

P6 #14 candidate is forming around either:
- (E confirmed) "Spec preflight must capture client-side tooling version on each consuming host"
- (D confirmed) "Major-broker-version + minor-client-version skew can produce silent concurrent-CONNECT races"
- (other) reframes once known

Don't bank yet. Wait for third-host result. Lesson lands cleanly once root cause is definitive.

P6 lessons banked count remains: 13.

---

## 5. Acknowledgments

- **Path (a) ruled out Hypothesis B definitively** -- exactly the cheap decisive test we needed
- **Path (b) log evidence narrowed rejection stage** to CONNECT-packet validation, not auth-flow -- crucial framing for next steps
- **agent_bus.py finding** (auto-rejecting every 120s on loopback listener) -- separate broken script, banks as P5; not the cause of Gate 5 failures but cleans diagnostic noise
- **Beast anchors preserved through all of Phase C** -- substrate untouched 13+ phases now (~38 hours)
- **Escalation cumulative count: 6**, each banked durable knowledge: P6 #12, P6 #13, guardrail 5, carve-out, P6 #14 candidate forming, possibly P6 #15 from next ESC

---

## 6. Order of operations

```
1. PD: pkill -f agent_bus.py on SlimJim (self-auth under carve-out)
2. PD: capture Beast mosquitto-clients version (preflight evidence for P6 #14)
3. PD: install mosquitto-clients on Beast (apt install only, no broker-side change)
4. PD: capture Beast anchors pre-test
5. PD: run Gate 5 from Beast (sub-bg + pub-fg pattern)
6. PD: capture Beast anchors post-test (must be bit-identical)
7. PD: based on Beast result, follow Ruling 2 decision matrix:
     7a. Beast PASS -> auto-trigger CK upgrade per Ruling 3 -> re-run Gate 5 from CK
     7b. Beast FAIL same pattern -> file ESC #7 (broker-bug territory)
     7c. Beast partial -> file ESC #7 (new hypothesis)
8. PD: write paco_review_h1_phase_c_mosquitto.md (REDACT password) when 5/5 PASS lands
     - Document agent_bus stop under guardrail 4
     - Document third-host diagnostic + result
     - Document CK upgrade (if triggered) under guardrail 4
     - Document P6 #14 lesson once root cause known
9. PD: Phase C close-out commit (single commit) folds:
     - paco_review_h1_phase_c_mosquitto.md
     - PD memory file 5-guardrail+carve-out final version
     - SESSION.md (P6 = 14, Phase C closes Day 67 YELLOW #5)
     - paco_session_anchor.md (P6 = 14, Phase C YELLOW closure)
     - CHECKLIST audit entry
     - tasks/H1_observability.md spec amendment for P6 #14 (preflight check addition)
10. PD git commits + pushes
11. Paco final confirm
12. Phase D (node_exporter fan-out)
```

---

## 7. Standing rules in effect

- Per-step review docs in `/home/jes/control-plane/docs/`
- B2b + Garage nanosecond anchor preservation through Phase C
- 5-guardrail rule + carve-out (this case is OUTSIDE the rule's domain -- diagnostic, not mechanical correction; correctly routed to escalation)
- Spec or no action: Phase C continues following spec section 7 with explicit diagnostic detours authorized here
- Secrets discipline: passwords REDACTED in review
- P6 lessons: 13 banked, #14 candidate forming

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_c_gate5_followup.md`

-- Paco
