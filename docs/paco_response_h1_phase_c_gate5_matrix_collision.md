# Paco -> PD ruling -- H1 Phase C Beast-PASS matrix collision (Path B approved)

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-28 (Day 73)
**Predecessor:** `docs/paco_response_h1_phase_c_gate5_followup_correction.md` (commit `465f5d1`)
**Status:** **APPROVED** -- Path B (escalate first, no upgrade); P6 #14 banked; ESC #7 expected

---

## TL;DR

Three rulings:

1. **Path B APPROVED.** Do NOT run `apt install --only-upgrade mosquitto-clients libmosquitto1` on CK. Pre-auth's foundational assumption (version mismatch) invalidated by Beast clients version-parity (`2.0.11-1ubuntu1.2` on both Beast and CK). Running upgrade is a foregone-conclusion no-op that wastes a diagnostic cycle.
2. **P6 #14 BANKED.** Client-tooling version capture at preflight catches matrix-collision bugs before they trigger no-op actions. Lands cleanly regardless of Hypothesis F outcome.
3. **ESC #7 EXPECTED.** PD files `paco_request_h1_phase_c_gate5_hypothesis_f.md` with Beast-PASS evidence + version-parity finding + Hypothesis F surface (CK-specific environmental state).

PD's bias toward Path B is correct. PD's catch of the matrix-vs-reality collision is exactly the discipline that prevents wasted cycles.

---

## 1. Acknowledgment of Paco's matrix authoring error

ESC #6 §2.4 decision matrix (mine, commit `93164d5`) bound "Beast PASSES -> Hypothesis E confirmed -> CK upgrade." That binding implicitly assumed Beast had a different (newer) client version than CK. The matrix did not include a preflight-validation check on the version-parity scenario.

When PD's Step 2 ("capture Beast mosquitto-clients version") returned `2.0.11-1ubuntu1.2` -- the SAME version as CK -- Hypothesis E in its version-mismatch framing was already invalidated, before the test even ran. The matrix should have surfaced that collision automatically.

Process note banked: **decision matrices in spec-text must validate against preflight data, not just test outcomes.** Future rulings with conditional trigger paths pair each path with a preflight-precondition check.

PD caught the collision. Discipline working as designed.

---

## 2. Path B ruling -- approved

### Why no upgrade

1. **Foundational assumption invalidated.** Pre-auth in `paco_response_h1_phase_c_gate5_diagnostic.md` §5 was conditioned on E-as-version-mismatch. Beast's version-parity disproves that framing.
2. **Diagnostic cost > benefit.** No-op upgrade produces no new information. Both hosts at 2.0.11-1ubuntu1.2; no newer version in noble repos.
3. **Risk of false signal.** If apt re-runs postinst and touches state, we'd be misled about what fixed it. Worse than skipping the upgrade entirely.
4. **Hypothesis F is more likely than E-redux.** Same client version, different host, different result -> variable is no longer client-tooling.

### What does NOT happen

- No `apt install --only-upgrade mosquitto-clients libmosquitto1` on CK
- No re-run of Gate 5 from CK with current state
- No state changes anywhere (CK, SlimJim broker, Beast)

### What happens instead

- PD files ESC #7 with Beast-PASS evidence + version-parity + Hypothesis F surface
- Standing-rule path: diagnostic territory, outside 5-guardrail rule, correctly routed to escalation

---

## 3. Hypothesis F surface (preliminary, ESC #7 will full-frame)

Same client version on Beast (passes) and CK (fails). Variable is CK-specific environmental state. Possibilities ranked by probability:

### 3.1 Accumulated broker state for CK's IP (highest probability)

Mosquitto 2.0.18 may track per-source-IP state (connection rate, recent-rejection list, internal session table) polluted by CK's ~30+ failed CONNECTs during this debug. Beast comes in clean.

Cheapest test: `systemctl restart mosquitto` on SlimJim (clears in-memory broker state), retry Gate 5 from CK with no priming sequence. If it works post-restart, confirmed.

### 3.2 CK-side socket/library accumulated state (low probability)

Each `mosquitto_pub`/`mosquitto_sub` is a fresh process with fresh sockets. Could test via fresh CK shell after cooldown.

### 3.3 Network path quirk (low probability)

Conntrack table on SlimJim, switch-level state, or LAN topology specific to CK->SlimJim path. Pub-alone and sub-alone from CK both work, so it's not packet-level.

### 3.4 Kernel/sysctl difference Beast vs CK (low probability)

Different OS profiles, different socket-related sysctls. Easy to enumerate but probably not the cause.

**Don't lock these in.** ESC #7 surfaces full hypothesis space + PD's preferred test order.

---

## 4. P6 #14 BANKED

### Banked rule

> **Spec preflight must capture client-side tooling version on each consuming host that participates in smoke tests.** Even when version comparison ultimately disproves the working hypothesis (as it did here -- Beast 2.0.11 == CK 2.0.11), preflight version capture catches matrix-collision bugs before they trigger no-op actions. Banked from H1 Phase C Day 73 ESC #6 -> #7 transition: ESC #6 ruling matrix bound "Beast PASSES -> CK upgrade" without preflight version-parity validation; PD's Step 2 preflight surfaced the parity, exposing the binding as invalid before the no-op upgrade triggered.

P6 lessons banked count: **14** (was 13).

### Companion process note (Paco-side)

Decision matrices in spec-text must validate against preflight data. Future rulings with conditional trigger paths pair each path with a preflight-precondition check. If preflight invalidates the precondition, matrix automatically surfaces the collision rather than triggering a no-op or wrong action.

Bank in Phase C close-out review's "Spec-authoring lessons" section.

---

## 5. ESC #7 expected contents

PD files `paco_request_h1_phase_c_gate5_hypothesis_f.md` (or similar). Should include:

1. Beast Gate 5 sub + pub PASS evidence (sub_rc, pub_rc, full output)
2. Version-parity capture: `dpkg -l mosquitto-clients libmosquitto1` Beast + CK side-by-side
3. Beast anchor preservation diff (must be bit-identical)
4. Reframing: E (version-mismatch) ruled out by parity; F surface (CK-specific environmental state)
5. PD's preferred next test (PD bias likely: mosquitto restart on SlimJim -> fresh Gate 5 from CK -- testing Hypothesis F.1)
6. Standing-rule path: diagnostic, not mechanical, outside 5-guardrail rule, correctly escalated

---

## 6. State at this pause (no changes since correction commit)

- mosquitto.service active+enabled, MainPID 4086777
- Listeners: 127.0.0.1:1883 + 192.168.1.40:1884 both bound
- /etc/mosquitto/passwd: 1 entry (alexandra), mode 600 mosquitto:mosquitto
- /etc/mosquitto/conf.d/santigrey.conf: md5 `33346a752e0ef3b90cba0e6b08ca551f`
- UFW: 4 rules (22, 19999, 1883, 1884)
- agent_bus.service: running normally on SlimJim
- Beast: mosquitto-clients installed (2.0.11-1ubuntu1.2), Gate 5 PASSED, anchors bit-identical
- CK: untouched (no upgrade, no test re-run)
- B2b nanosecond anchor: `2026-04-27T00:13:57.800746541Z` -- holding
- Garage anchor: `2026-04-27T05:39:58.168067641Z` -- holding

---

## 7. Order of operations from here

```
1. PD files ESC #7 paco_request_h1_phase_c_gate5_hypothesis_f.md
2. Paco rules on ESC #7 (likely path: mosquitto restart on SlimJim -> fresh Gate 5 from CK)
3. PD executes per ruling
4. Continue until Gate 5 from CK passes
5. Phase C close-out commit folds everything
```

---

## 8. Standing rules in effect

- 5-guardrail rule + carve-out (this case OUTSIDE rule's domain -- diagnostic, correctly escalated)
- B2b + Garage nanosecond anchor preservation (still holding, ~38+ hours)
- Per-step review docs in `/home/jes/control-plane/docs/`
- Spec or no action: no upgrade, no test re-run, ESC #7 expected
- Secrets discipline: passwords REDACTED in review
- P6 lessons banked: 14 (added #14 this turn)
- Process note added: decision matrices must validate against preflight data

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_c_gate5_matrix_collision.md`

-- Paco
