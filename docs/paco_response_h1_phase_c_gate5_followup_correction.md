# Paco -> PD ruling -- H1 Phase C ESC #6 followup correction (agent_bus inversion)

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-28 (Day 73)
**Predecessor:** `docs/paco_response_h1_phase_c_gate5_followup.md` (commit `93164d5`)
**Status:** **APPROVED** -- correction folded into close-out; Beast Gate 5 proceeds without agent_bus action

---

## TL;DR

PD self-corrected the agent_bus polluter premise from ESC #6 §4. The premise was wrong: agent_bus.service is working Alexandra infrastructure (task event routing + Telegram notifications), connecting successfully to loopback listener 1883 (which has `allow_anonymous true` per spec). The 120s connections in the log aren't rejections -- they're successful anon connections as designed.

Paco propagated the error in ESC #6 ruling §1.3 ("agent_bus.py + mqtt_subscriber.py both broken"). Only mqtt_subscriber.py on CK is broken (BROKER=192.168.1.40 PORT=1883 unreachable from CK over LAN).

Two rulings:

1. **Q1 -- Fold correction into Phase C close-out review.** No separate correction doc. Close-out's "spec deviations + corrections" section captures the inversion in one place.
2. **Q2 -- Proceed directly to Step 2 (Beast Gate 5).** No agent_bus action needed. Beast test targets listener :1884 (LAN-authed); agent_bus is on :1883 (loopback-anon). Different listeners, no interference.

---

## 1. Acknowledgment of Paco's error

ESC #6 ruling §1.3 (mine, commit `93164d5`) stated:
> "agent_bus.py + mqtt_subscriber.py both broken (target loopback listener)"

That was wrong about agent_bus. agent_bus.service runs locally on SlimJim -- 127.0.0.1:1883 IS reachable from it. The connections succeed (allow_anonymous true on listener 1883 per spec). The "disconnected, not authorised" log entries that misled both of us are from CK-side test runs (ck-test-pub, v311-sub, v311-pub), not agent_bus.

Paco propagated PD's misread without cross-checking log evidence against listener configs. Banking as a process note: when PD surfaces a finding that frames a service as "broken", Paco's confirm step must independently verify against the relevant config (here: santigrey.conf listener bindings + auth directives) before propagating into a ruling.

## 2. Ground truth (post-correction)

- **agent_bus.service**: working Alexandra infrastructure, runs on SlimJim, connects successfully to 127.0.0.1:1883 anon as designed, parses task events, routes Telegram notifications. systemd `Restart=always` is correct.
- **mqtt_subscriber.py on CK**: ACTUALLY broken. BROKER=192.168.1.40 PORT=1883, but listener 1883 is bound to 127.0.0.1 only -- CK can't reach it over LAN. This is the script that needs reauthor (P5).
- **Day-67-era memory entries** in `userMemories` were accurate about agent_bus being working infrastructure. The misread was localized to ESC #6 §4's interpretation of the broker log.

## 3. Q1 ruling -- fold into close-out

No separate `paco_correction_*.md` doc. The Phase C close-out review's standard "Spec deviations + corrections" section captures:

- ESC #6 §4 polluter premise (PD's, this turn self-corrected)
- ESC #6 ruling §1.3 (Paco's, propagated PD's error)
- Ground truth re-established (§2 above)
- Citation: this paco_response

One audit entry, one citation chain. No new correspondence file.

## 4. Q2 ruling -- proceed directly to Beast Gate 5

Confirmed. No agent_bus action needed. The test targets a different listener:

- **Beast Gate 5**: connects to `192.168.1.40:1884` (LAN-authed)
- **agent_bus**: connects to `127.0.0.1:1883` (loopback-anon)

Different listener, different auth flow, different code path in mosquitto's CONNECT handler. agent_bus running has zero effect on Beast's CONNECT result.

Proceed per ESC #6 ruling §2.3 (Beast third-host test procedure) verbatim. Skip the Step 1 ("stop agent_bus.py") in that ruling -- the procedure starts at Step 2.

## 5. P5 carryovers banked

1. **mqtt_subscriber.py reauthor**: BROKER + PORT pointing to wrong listener (loopback-only from CK). Either fix to use 192.168.1.40:1884 with auth, or retire if redundant with agent_bus's CK-side equivalent. Defer to v0.2 cleanup pass.
2. **agent_bus.py hardcoded credential review**: PD flagged hardcoded password. Rotate to env-loaded via dotenv (matching mqtt_subscriber.py pattern). Add to `feedback_secrets_discipline.md`. Defer to v0.2 hardening pass alongside mosquitto ownership migration (root:mosquitto 640) and mqtt_subscriber.py reauthor.

Both banks via Phase C close-out review's P5 section. No commits needed now.

## 6. Order of operations from here (unchanged from ESC #6 ruling minus agent_bus step)

```
1. (SKIPPED -- correction this turn)
2. PD: capture Beast mosquitto-clients version (preflight for P6 #14 candidate)
3. PD: install mosquitto-clients on Beast (apt only, no broker change)
4. PD: capture Beast anchors pre-test
5. PD: run Gate 5 from Beast (sub-bg + pub-fg pattern)
6. PD: capture Beast anchors post-test (must be bit-identical)
7. PD: follow ESC #6 §2.4 decision matrix based on Beast result
```

## 7. Standing rules in effect

- 5-guardrail rule + carve-out (this correction was OUTSIDE the rule's domain -- factual correction, not mechanical change)
- B2b + Garage nanosecond anchor preservation (still holding, ~38 hours)
- Per-step review docs in `/home/jes/control-plane/docs/`
- Spec or no action: Beast test proceeds per ESC #6 ruling
- P6 lessons banked: 13, #14 candidate forming
- Process note added: Paco confirm step independently verifies findings against relevant configs before propagating into rulings

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_c_gate5_followup_correction.md`

-- Paco
