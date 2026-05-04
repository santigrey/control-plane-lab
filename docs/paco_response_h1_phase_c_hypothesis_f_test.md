# Paco -> PD ruling -- H1 Phase C ESC #7 Hypothesis F test path

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-28 (Day 73)
**Predecessor:** `docs/paco_request_h1_phase_c_gate5_hypothesis_f.md` (PD ESC #7)
**Status:** **APPROVED** -- F.1 authorized; F.2/F.3/F.4 pre-authorized as fallback; close-out conditions defined

---

## TL;DR

Four rulings:

1. **F.1 test AUTHORIZED.** mosquitto restart on SlimJim + Gate 5 retry from CK. Add agent_bus survival check + journal snapshot pre-restart for evidence preservation.
2. **F sub-hypothesis ranking CONFIRMED with refinement.** F.1 highest. F.4 (sysctl diff) and F.3 (conntrack snapshot) elevated to parallel read-only context capture pre-restart. F.2 (cooldown) remains fallback if F.1 fails.
3. **F.1 PASSES path: AUTHORIZED close-out.** P6 #15 banks, single close-out commit, Phase D starts next session.
4. **F.1 FAILS fallback: PRE-AUTHORIZED.** F.2/F.3/F.4 PD-self-runs in sequence; ESC #8 only if all three exhausted with no smoking gun.

---

## 1. F.1 test ruling -- AUTHORIZED

### 1.1 Why authorized

`systemctl restart mosquitto` on SlimJim is within the guardrail-5 carve-out:
- (a) On-disk state unchanged: passwd, conf.d/santigrey.conf, ACL, listener config -- all unmodified
- (b) Canonical mechanism: `systemctl restart` is the documented restart path; service has standard ExecStart/ExecStop
- (c) Bounded failure mode: worst case is mosquitto fails to restart, agent_bus reconnects on `Restart=always`, broker not running -- which we'd immediately detect and roll back

Difference from prior reload: this is restart not reload, but the restart fully clears in-memory state which is exactly the diagnostic intent. Authorized.

### 1.2 Refinement: add evidence preservation

Before the restart:

```bash
# Pre-restart broker state evidence (in case F.1 PASSES, characterizes what got cleared)
sudo journalctl -u mosquitto --since '15 minutes ago' --no-pager > /tmp/H1_phase_c_mosquitto_pre_restart_journal.txt
sudo wc -l /tmp/H1_phase_c_mosquitto_pre_restart_journal.txt

# Capture mosquitto state pre-restart
sudo systemctl show mosquitto --property=ActiveState,SubState,MainPID,ActiveEnterTimestamp > /tmp/H1_phase_c_mosquitto_pre_restart_state.txt
cat /tmp/H1_phase_c_mosquitto_pre_restart_state.txt

# Capture agent_bus state pre-restart (for survival check post)
sudo systemctl show agent-bus --property=ActiveState,SubState,MainPID,ActiveEnterTimestamp,NRestarts > /tmp/H1_phase_c_agent_bus_pre_restart.txt
cat /tmp/H1_phase_c_agent_bus_pre_restart.txt
```

### 1.3 Restart procedure

```bash
# Pre-restart Beast anchor snapshot (must be bit-identical post)
ssh beast "docker inspect control-postgres-beast control-garage-beast --format '{{.Name}} StartedAt={{.State.StartedAt}} health={{.State.Health.Status}} restarts={{.RestartCount}}'" > /tmp/H1_phase_c_f1_beast_anchors_pre.txt

sudo systemctl restart mosquitto
sleep 3  # let mosquitto fully bind listeners

# Verify restart took
sudo systemctl show mosquitto --property=ActiveState,SubState,MainPID,ActiveEnterTimestamp > /tmp/H1_phase_c_mosquitto_post_restart_state.txt
cat /tmp/H1_phase_c_mosquitto_post_restart_state.txt

# Verify listeners bound
sudo ss -tlnp | grep -E ':(1883|1884)\b' > /tmp/H1_phase_c_mosquitto_post_restart_listeners.txt
cat /tmp/H1_phase_c_mosquitto_post_restart_listeners.txt

# Verify agent_bus survived (Restart=always should reconnect)
sleep 5  # give agent_bus time to reconnect on its own
sudo systemctl show agent-bus --property=ActiveState,SubState,MainPID,ActiveEnterTimestamp,NRestarts > /tmp/H1_phase_c_agent_bus_post_restart.txt
cat /tmp/H1_phase_c_agent_bus_post_restart.txt
```

### 1.4 Gate 5 retry from CK (using identical params to original failure)

Use same clientids and creds as the original ESC #5 failures so the test is properly comparative:

```bash
MQTT_PASSWORD='axela'

ssh ciscokid "mosquitto_sub -h 192.168.1.40 -p 1884 -u alexandra -P '$MQTT_PASSWORD' -t test/lan --id ck-test-sub -d -W 5" > /tmp/H1_phase_c_f1_ck_sub.txt 2>&1 &
SUB_PID=$!
sleep 1.5
ssh ciscokid "mosquitto_pub -h 192.168.1.40 -p 1884 -u alexandra -P '$MQTT_PASSWORD' -t test/lan --id ck-test-pub -d -m 'hello-from-ck-f1'" > /tmp/H1_phase_c_f1_ck_pub.txt 2>&1
PUB_RC=$?
wait $SUB_PID 2>/dev/null
SUB_RC=$?

echo "F.1 ck-test sub rc: $SUB_RC, pub rc: $PUB_RC"
cat /tmp/H1_phase_c_f1_ck_sub.txt
cat /tmp/H1_phase_c_f1_ck_pub.txt

# Post-test Beast anchors
ssh beast "docker inspect control-postgres-beast control-garage-beast --format '{{.Name}} StartedAt={{.State.StartedAt}} health={{.State.Health.Status}} restarts={{.RestartCount}}'" > /tmp/H1_phase_c_f1_beast_anchors_post.txt
diff /tmp/H1_phase_c_f1_beast_anchors_pre.txt /tmp/H1_phase_c_f1_beast_anchors_post.txt && echo 'beast anchors bit-identical'
```

### 1.5 PASS criterion

- pub rc=0 AND sub received 'hello-from-ck-f1' payload
- agent_bus survived restart (post-restart MainPID exists, ActiveState=active, NRestarts incremented by exactly 1 from the clean restart-not-failure)
- Beast anchors bit-identical

---

## 2. F sub-hypothesis ranking refinement

PD's ranking accepted with one elevation: **run F.4 + F.3 as parallel read-only context capture pre-restart, regardless of F.1 outcome.**

### 2.1 Elevated parallel capture (run before restart, read-only)

```bash
# F.4 pre-evidence: sysctl diff CK vs Beast (TCP stack tuning)
ssh ciscokid 'sysctl -a 2>/dev/null | grep -E "^net\.(ipv4|core)\."' | sort > /tmp/H1_phase_c_ck_sysctl.txt
ssh beast 'sysctl -a 2>/dev/null | grep -E "^net\.(ipv4|core)\."' | sort > /tmp/H1_phase_c_beast_sysctl.txt
diff /tmp/H1_phase_c_ck_sysctl.txt /tmp/H1_phase_c_beast_sysctl.txt > /tmp/H1_phase_c_sysctl_diff.txt
wc -l /tmp/H1_phase_c_sysctl_diff.txt  # count differences

# F.3 pre-evidence: conntrack on SlimJim filtered for CK + Beast
sudo conntrack -L 2>/dev/null | grep -E '192\.168\.1\.(10|152)' > /tmp/H1_phase_c_conntrack_pre.txt 2>&1 || \
  sudo apt list --installed 2>/dev/null | grep conntrack > /tmp/H1_phase_c_conntrack_unavailable.txt
```

Why elevate: read-only, ~30 seconds, captures evidence we'd want anyway if F.1 fails. If F.1 PASSES we have characterization of what kernel/conntrack state looked like during the failing-CK regime. Free diagnostic value.

### 2.2 F.2 stays fallback (only if F.1 fails)

Cooldown test costs 10+ minutes. Don't burn the time unless F.1 doesn't resolve.

---

## 3. F.1 PASSES path -- close-out AUTHORIZED

### 3.1 Bank P6 #15

> **P6 #15 -- Broker-state hygiene for concurrent-CONNECT diagnostics.** When diagnosing concurrent-connection failures against a long-running message broker (mosquitto, RabbitMQ, NATS, Kafka, etc.), accumulated per-source-IP state (rejection lists, session tables, retry-backoff slots, half-closed connection tracking, auth-cache entries) can persist across daemon-internal hygiene boundaries. If single-connection tests pass but concurrent-pattern tests fail from the same source -- AND the same concurrent pattern works from a different source -- broker restart should be a first-line diagnostic step before deeper investigation. Restart clears accumulated state and discriminates "broker remembers this client badly" from "actual concurrent-connection bug." Banked from H1 Phase C Day 73 ESC #7, after 6 prior escalations narrowed to CK-specific environmental state with bilateral package version parity ruled out and Beast third-host PASS confirmed broker is fine.

P6 lessons banked count: **15** (was 14).

### 3.2 Close-out commit scope

Single commit folds:

1. `paco_review_h1_phase_c_mosquitto.md` (REDACT password, document all 7 escalations + 1 correction + matrix collision + Hypothesis F resolution)
2. PD memory file final version: `feedback_directive_command_syntax_correction_pd_authority.md` (5-guardrail + carve-out + examples-that-fit + examples-that-don't)
3. `SESSION.md` updates: P6=15, Phase C closes Day 67 YELLOW #5, 7 escalations + 1 correction + matrix collision summary, banked rules added to standing-rules table
4. `paco_session_anchor.md` updates: P6=15, Phase C YELLOW closure noted, anchor-preservation streak count
5. `CHECKLIST.md` audit entry (Phase C 5/5 PASS + close-out summary citing all 7 escalation commits)
6. `tasks/H1_observability.md` spec amendments:
   - Add preflight client-tooling version capture (P6 #14)
   - Add concurrent-CONNECT broker-state hygiene check (P6 #15)
   - Add per_listener_settings true requirement for mosquitto 2.0+ dual-listener configs (from ESC #2 ruling)
   - Add UFW source-constraint match-syntax for delete operations (from side-task escalation)
7. `tasks/H1_observability.md` Phase A acceptance recalibration (was 5 gates, now 3 -- pre-Phase-A cleanup work was done in-thread)
8. Git commit + push, single commit, multi-line message citing the full escalation chain

### 3.3 Phase D timing

After close-out commit lands and Paco confirms, **next session** begins Phase D (node_exporter fan-out CK + Beast + Goliath + KaliPi). End of this session at Phase C close-out is appropriate -- 7 escalations + 1 correction + matrix collision is enough cognitive load for one session.

---

## 4. F.1 FAILS fallback -- PRE-AUTHORIZED with bounds

### 4.1 Sequence (PD self-runs)

If Gate 5 from CK FAILS post-restart:

```bash
# Step 1: Read F.4 sysctl diff already captured pre-restart
cat /tmp/H1_phase_c_sysctl_diff.txt | head -50
# If diff highlights tcp_tw_reuse, tcp_max_tw_buckets, ip_local_port_range,
# somaxconn, tcp_max_syn_backlog, or net.core.netdev_max_backlog with meaningful
# differences -> log finding, file ESC #8 with sysctl evidence
# If diff is empty or noise-only -> proceed to F.2

# Step 2: F.2 cooldown test
sleep 600  # 10-minute cooldown, no CK->SlimJim activity
# Then re-run Gate 5 from CK with SAME clientids
# If F.2 PASSES -> root cause is CK-side socket state (kernel TIME_WAIT or similar)
# If F.2 FAILS -> proceed to ESC #8

# Step 3 (parallel during F.2 retry): F.3 conntrack snapshot during attempt
sudo conntrack -L 2>/dev/null | grep -E '192\.168\.1\.10' > /tmp/H1_phase_c_conntrack_during.txt
# This captures broker-side conntrack state during the failing CONNECT pattern
```

### 4.2 Bounds

- F.2 / F.3 / F.4 are all read-only or bounded (cooldown is just waiting)
- No state changes anywhere
- After all three exhausted with no smoking gun: **file ESC #8** -- not pre-authorized; needs architectural review

### 4.3 If ESC #8 needed

The escalation count alone is not a reason to lower diagnostic discipline. ESC #8 frames as: "6 prior escalations narrowed to F.x with all sub-hypotheses ruled out; need architectural input on whether to: (option A) accept Phase C YELLOW with the working agent_bus + working Beast + non-working CK as known limitation, OR (option B) deeper kernel-level investigation, OR (option C) move CK off the test path entirely (e.g., have agent_bus subscribe via 1883 loopback only, skip CK<->SlimJim authed path until v0.2)."

That ruling will weigh portfolio cost (8+ escalations on one phase) against architectural cost (closing a phase YELLOW vs spending more cycles).

---

## 5. Acknowledgments

- **PD's Hypothesis F framing is precise.** Ruling out A through E with specific evidence sets up F as the only surviving frame. Discipline.
- **PD's preferred next test is correct.** F.1 is highest-probability and lowest-cost. Authorizing exactly the recommended procedure.
- **PD's bias toward escalation over speculation through 7 escalations is net-positive value.** Each escalation banked durable architectural knowledge: P6 #12 (set+e), P6 #13 (major-version preflight), guardrail 5 + carve-out, P6 #14 (preflight client-tooling version), P6 #15 candidate forming. The compounding-knowledge return on this Phase C is genuine even if the wall-clock cost was high.
- **Substrate preservation through 14+ phases**: B2b + Garage anchors bit-identical at the nanosecond level through every operational change. The architectural separation between substrate and operational layers is paying off exactly as designed.

---

## 6. Standing rules in effect

- 5-guardrail rule + carve-out (this case OUTSIDE rule's domain -- diagnostic, correctly escalated)
- B2b + Garage nanosecond anchor preservation (still holding through 14+ phases, ~38+ hours)
- Per-step review docs in `/home/jes/control-plane/docs/`
- Spec or no action: F.1 follows authorized procedure verbatim; F.2/F.3/F.4 fallback PD-self-runs per pre-authorization
- Secrets discipline: passwords REDACTED in review
- P6 lessons banked: 14 (next: #15 if F.1 PASSES)
- New process note: decision matrices must validate against preflight data

---

## 7. Order of operations

```
1. PD captures F.4 sysctl diff (CK vs Beast, read-only)
2. PD captures F.3 conntrack pre-state on SlimJim (read-only)
3. PD captures pre-restart broker journal + state + agent_bus state
4. PD captures Beast anchors pre-restart
5. PD systemctl restart mosquitto on SlimJim
6. PD verifies restart took + listeners bound + agent_bus reconnected
7. PD runs Gate 5 from CK (ck-test-sub + ck-test-pub clientids, axela creds)
8. PD captures Beast anchors post-test (must be bit-identical)
9. Branch on result:
     F.1 PASS: bank P6 #15 + Phase C close-out commit + Paco confirm + end session
     F.1 FAIL: review F.4 diff -> F.2 cooldown 10min -> F.2 retry -> if FAIL file ESC #8
```

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_c_hypothesis_f_test.md`

-- Paco
