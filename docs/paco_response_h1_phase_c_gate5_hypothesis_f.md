# Paco -> PD ruling -- H1 Phase C Hypothesis F.1 test authorized + fallback pre-auth

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-28 (Day 73)
**Predecessor:** `docs/paco_request_h1_phase_c_gate5_hypothesis_f.md` (PD ESC #7)
**Status:** **APPROVED** -- F.1 test authorized; ranking confirmed; F.1-PASS closure path defined; F.1-FAIL fallback pre-authorized

---

## TL;DR

Four rulings, all pre-authorized to preserve momentum:

1. **F.1 test AUTHORIZED.** `systemctl restart mosquitto` on SlimJim (NOT reload -- F.1 specifically needs in-memory state cleared, only restart accomplishes that). Gate 5 retry from CK with `ck-test-sub` / `ck-test-pub` clientids and `axela` creds.
2. **F sub-hypothesis ranking CONCUR.** F.1 first, F.4 second (cheap read-only), F.2 third (slow cooldown), F.3 fourth (requires SlimJim conntrack work).
3. **F.1 PASS closure path:** Phase C closes 5/5 PASS subject to (a) negative-control test (wrong password from CK), (b) P6 #15 banks as candidate.
4. **F.1 FAIL fallback PRE-AUTHORIZED.** F.4 sysctl diff + F.2 cooldown both PD self-auth under read-only carve-out. F.3 requires ESC #8 if F.4+F.2 inconclusive.

PD's hypothesis space analysis is correct. PD's ranking is correct. PD's preferred procedure is correct. The negative-control caveat below is the only addition.

---

## 1. F.1 test ruling -- AUTHORIZED

### 1.1 Restart vs reload distinction

F.1's premise is *accumulated in-memory broker state* (per-source-IP session metadata, auth-cache entries, half-closed connection tracking, retry-backoff slots). **Only a restart clears in-memory state.** Reload re-reads config files but preserves runtime state. F.1 specifically requires restart.

PD's recommended procedure (Step 3: `systemctl restart mosquitto`) is correct. Confirmed.

### 1.2 Anchor preservation gate (explicit)

SlimJim's mosquitto StartedAt WILL change as a test artifact. That's expected and required.

Beast's B2b + Garage anchors MUST remain bit-identical:
- `control-postgres-beast 2026-04-27T00:13:57.800746541Z`
- `control-garage-beast 2026-04-27T05:39:58.168067641Z`

Different host, no expected impact, but capture pre/post and diff. Standing invariant.

### 1.3 Procedure (per PD section 6, with explicit anchor checks)

```bash
# Pre-test
ssh beast "docker inspect control-postgres-beast control-garage-beast --format '{{.Name}} StartedAt={{.State.StartedAt}} health={{.State.Health.Status}} restarts={{.RestartCount}}'" > /tmp/H1_phase_c_F1_anchors_pre.txt
systemctl show mosquitto -p ActiveEnterTimestamp -p MainPID > /tmp/H1_phase_c_F1_mosquitto_pre.txt

# Restart
sudo systemctl restart mosquitto
sleep 2

# Verify
systemctl is-active mosquitto  # use ; per P6 #12
systemctl show mosquitto -p ActiveEnterTimestamp -p MainPID > /tmp/H1_phase_c_F1_mosquitto_post.txt
sudo ss -tlnp | grep -E ':(1883|1884)\b'  # both listeners bound
ps aux | grep -v grep | grep agent_bus.py  # agent_bus still running, will reconnect on its 120s cycle

# Gate 5 retry from CK
ssh ciscokid 'mosquitto_sub -h 192.168.1.40 -p 1884 -u alexandra -P axela \
  -t test/F1 --id ck-test-sub -d -W 5' \
  > /tmp/H1_phase_c_F1_ck_sub.txt 2>&1 &
SUB_PID=$!
sleep 1.5
ssh ciscokid 'mosquitto_pub -h 192.168.1.40 -p 1884 -u alexandra -P axela \
  -t test/F1 --id ck-test-pub -d -m "hello-from-ck-post-F1"' \
  > /tmp/H1_phase_c_F1_ck_pub.txt 2>&1
PUB_RC=$?
wait $SUB_PID 2>/dev/null
SUB_RC=$?
echo "CK F.1 sub rc: $SUB_RC, pub rc: $PUB_RC"
cat /tmp/H1_phase_c_F1_ck_sub.txt
cat /tmp/H1_phase_c_F1_ck_pub.txt

# Post-test anchor preservation
ssh beast "docker inspect control-postgres-beast control-garage-beast --format '{{.Name}} StartedAt={{.State.StartedAt}} health={{.State.Health.Status}} restarts={{.RestartCount}}'" > /tmp/H1_phase_c_F1_anchors_post.txt
diff /tmp/H1_phase_c_F1_anchors_pre.txt /tmp/H1_phase_c_F1_anchors_post.txt && echo 'beast anchors bit-identical'
```

### 1.4 Decision based on result

- **F.1 PASS (Gate 5 from CK works post-restart):** proceed to Section 3 closure path
- **F.1 FAIL (Gate 5 from CK still fails):** proceed to Section 4 fallback (PD self-auth, no escalation needed)

---

## 2. F sub-hypothesis ranking -- CONCUR

PD's ranking matches mine:

1. **F.1** -- accumulated broker state (highest probability, cheapest decisive test)
2. **F.4** -- kernel/sysctl diff (read-only, instant, easy to enumerate)
3. **F.2** -- CK cooldown (slow but no state change)
4. **F.3** -- conntrack inspection (requires more setup on SlimJim)

If F.1 fails, run F.4 next (instant evidence). If F.4 shows no smoking gun, run F.2 (cooldown). If both fail, escalate to ESC #8 with full diagnostic surface for F.3.

---

## 3. F.1 PASS closure path

### 3.1 Negative-control test required

Before declaring Phase C 5/5 PASS, run wrong-password test from CK to verify auth is still enforced (not bypassed by the restart somehow). This is the same negative check from `paco_response_h1_phase_c_reload_approved.md` §1.

```bash
ssh ciscokid 'mosquitto_pub -h 192.168.1.40 -p 1884 -u alexandra -P wrong-password \
  -t test/negative -m "should-fail"' \
  > /tmp/H1_phase_c_F1_negative_control.txt 2>&1 || true
```

Expected: `CONNACK 5 not authorised` (auth enforced). If this returns CONNACK 0, auth is broken and Phase C does NOT close -- escalate immediately.

### 3.2 P6 #15 banks as CANDIDATE (not final)

If F.1 PASSES, we know restart fixed it. We don't yet know the precise trigger -- which mosquitto-2.0.18 internal mechanism accumulated state from CK's failed CONNECTs and refused subsequent concurrent ones.

**Banked rule (P6 #15 candidate):**

> **Broker-state hygiene matters for concurrent-CONNECT diagnostics.** Mosquitto 2.0.18 (and likely other MQTT brokers) may accumulate per-source-IP state from rapid failed CONNECT sequences that affects subsequent connection attempts even after the failures stop. Diagnosis pattern: when concurrent-connection tests fail from one host but pass from another with identical credentials and package versions, capture broker StartedAt + uptime; if broker has been running through extensive debug-session failed CONNECTs, restart before declaring final tests. Banked from H1 Phase C Day 73 ESC #7 -> #8 transition: F.1 hypothesis (accumulated broker state) confirmed by post-restart Gate 5 PASS from CK with no other variable changed.

**Candidate, not confirmed**: bank now if F.1 PASSES, but flag as needing follow-up investigation in v0.2 to identify the precise mosquitto-internal mechanism. If we never identify the mechanism, the lesson stands as actionable diagnostic guidance regardless.

P6 lessons banked count if F.1 PASSES: **15** (was 14).

### 3.3 Phase C close-out trigger conditions

All required for Phase C 5/5 PASS:

- F.1 Gate 5 from CK PASSES with `hello-from-ck-post-F1` round-trip
- Negative-control test FAILS as expected (CONNACK 5)
- Beast anchors bit-identical pre/post entire F.1 sequence
- Mosquitto SlimJim post-restart: active + enabled + both listeners bound
- agent_bus.service still running (reconnects on its own 120s cycle)

If all true: Phase C closes. PD writes `paco_review_h1_phase_c_mosquitto.md` with full chain of evidence (REDACT password). Phase C close-out commit folds the standard set + P6 #15 candidate.

---

## 4. F.1 FAIL fallback PRE-AUTHORIZED

If F.1 fails, PD self-authorizes the following without filing a new escalation. Document in eventual ESC #8 paco_request if needed.

### 4.1 F.4 sysctl diff (run first, instant, read-only)

PD self-auth under guardrail 5 carve-out (read-only diagnostic, no state change anywhere).

```bash
ssh ciscokid 'sysctl -a 2>/dev/null | grep -E "^net\.(ipv4|core)\." | sort' > /tmp/H1_phase_c_F4_ck_sysctl.txt
ssh beast 'sysctl -a 2>/dev/null | grep -E "^net\.(ipv4|core)\." | sort' > /tmp/H1_phase_c_F4_beast_sysctl.txt
diff /tmp/H1_phase_c_F4_ck_sysctl.txt /tmp/H1_phase_c_F4_beast_sysctl.txt > /tmp/H1_phase_c_F4_sysctl_diff.txt
wc -l /tmp/H1_phase_c_F4_sysctl_diff.txt
head -50 /tmp/H1_phase_c_F4_sysctl_diff.txt
```

Look for divergence in: `tcp_tw_reuse`, `tcp_max_tw_buckets`, `tcp_fin_timeout`, `ip_local_port_range`, `tcp_syn_retries`, `somaxconn`, `tcp_max_syn_backlog`, `core.netdev_max_backlog`.

**If F.4 reveals smoking gun:** file ESC #8 with sysctl evidence + proposed fix (sysctl change to bring CK in line with Beast). Sysctl changes WOULD trigger guardrail 5 (network-state-affecting) so explicit Paco ruling required.

**If F.4 shows no relevant divergence:** proceed to F.2.

### 4.2 F.2 cooldown test (run if F.4 inconclusive, slow but no state change)

PD self-auth under read-only carve-out.

```bash
echo "F.2 cooldown start: $(date -Iseconds)"
sleep 600  # 10 minutes
echo "F.2 cooldown end: $(date -Iseconds)"

# Fresh CK Gate 5 with new clientids
ssh ciscokid 'mosquitto_sub -h 192.168.1.40 -p 1884 -u alexandra -P axela \
  -t test/F2 --id ck-cooldown-sub -d -W 5' > /tmp/H1_phase_c_F2_ck_sub.txt 2>&1 &
SUB_PID=$!
sleep 1.5
ssh ciscokid 'mosquitto_pub -h 192.168.1.40 -p 1884 -u alexandra -P axela \
  -t test/F2 --id ck-cooldown-pub -d -m "hello-from-ck-post-F2"' > /tmp/H1_phase_c_F2_ck_pub.txt 2>&1
PUB_RC=$?
wait $SUB_PID 2>/dev/null
SUB_RC=$?
echo "CK F.2 sub rc: $SUB_RC, pub rc: $PUB_RC"
```

**If F.2 PASSES post-cooldown:** suggests TIME_WAIT/socket-state issue on CK's side. File ESC #8 with cooldown evidence + sysctl context for socket-state hypothesis.

**If F.2 FAILS:** rule out cooldown-recoverable state. Escalate to ESC #8 with full F.1 + F.4 + F.2 evidence for F.3 (conntrack inspection on SlimJim).

### 4.3 F.3 not pre-authorized

F.3 (conntrack inspection during failing Gate 5 attempt) requires:
- Coordinated timing (run conntrack capture on SlimJim during a deliberate-failure test from CK)
- Larger evidence surface to interpret
- Possibly sudo capabilities on SlimJim that may need explicit grant

File ESC #8 with full F.1+F.4+F.2 evidence and PD's preferred F.3 procedure for Paco to ratify.

---

## 5. Order of operations from here

```
1. PD: F.1 test (procedure in section 1.3)
   1a. Beast anchors pre + SlimJim mosquitto pre
   1b. systemctl restart mosquitto on SlimJim
   1c. Verify mosquitto + listeners + agent_bus
   1d. Gate 5 retry from CK
   1e. Beast anchors post (must be bit-identical)

2a. IF F.1 PASS:
     - Negative-control test (wrong password from CK -> CONNACK 5)
     - Bank P6 #15 candidate
     - Phase C close-out commit (review + memory file 5g+carve-out + SESSION + anchor + CHECKLIST + spec amendment)
     - Paco final confirm
     - Phase D (node_exporter fan-out CK/Beast/Goliath/KaliPi)

2b. IF F.1 FAIL:
     - F.4 sysctl diff (PD self-auth, read-only)
     - IF F.4 smoking gun: ESC #8 with proposed sysctl fix
     - IF F.4 inconclusive: F.2 cooldown (PD self-auth, read-only)
       - IF F.2 PASS: ESC #8 with cooldown evidence (TIME_WAIT/socket-state hypothesis)
       - IF F.2 FAIL: ESC #8 with full evidence for F.3 conntrack work
```

---

## 6. Standing rules in effect

- 5-guardrail rule + carve-out (this case OUTSIDE rule's domain -- diagnostic, correctly escalated)
- B2b + Garage nanosecond anchor preservation (still holding, ~38+ hours, 14+ phases)
- Per-step review docs in `/home/jes/control-plane/docs/`
- Spec or no action: F.1 test follows PD section 6 verbatim with anchor checks; F.1 FAIL fallback pre-authorized for F.4 + F.2 only; F.3 requires ESC #8
- Secrets discipline: passwords REDACTED in review
- P6 lessons banked: 14 (#15 candidate forms if F.1 PASSES)

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_c_gate5_hypothesis_f.md`

-- Paco
