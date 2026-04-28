# Paco -> PD ruling -- H1 Phase C `per_listener_settings true` approved + 5th guardrail + P6 #13

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-28 (Day 73)
**Spec:** `tasks/H1_observability.md` section 7
**Predecessor:** `docs/paco_request_h1_phase_c_per_listener_settings.md`
**Status:** **APPROVED** -- fix authorized, 5th guardrail added to standing rule, P6 #13 banked

---

## TL;DR

Three rulings:

1. **Fix APPROVED** -- prepend `per_listener_settings true` to `santigrey.conf` per PD section 3.2. Resume Phase C from Gate 4 re-run.
2. **5th guardrail BANKED** to broadened standing rule -- auth/credential/security-boundary corrections always escalate, regardless of conditions 1-4.
3. **P6 lesson #13 BANKED** -- major-version behavior-change preflight checks for directives targeting software with v-boundary semantics shifts.

CEO's instinct to escalate (Option B over Option A) was correct architecture. The 5th guardrail formalizes that instinct as a rule. PD's discipline of pattern-matching the 4-condition test cleanly THEN deferring to CEO on ambiguity is exactly the behavior the rule should produce.

---

## 1. Ruling on the fix -- APPROVED

PD's proposed `per_listener_settings true` addition (section 3.2) is correct. Mosquitto 2.0 default-scoping change is documented behavior, and `per_listener_settings true` is the canonical mechanism to restore v1.x-style per-listener auth semantics that the directive's surrounding language implies.

### 1.1 Apply the corrected config

Use PD's section 6 resume scope verbatim. Single edit to `/etc/mosquitto/conf.d/santigrey.conf` to prepend the directive (with explanatory comment), then `systemctl reload mosquitto` (or restart if reload doesn't pick up new global directives -- mosquitto sometimes requires restart for global scope changes).

### 1.2 Re-run Gate 4 + continue to Gate 5

After config change + reload:
- Gate 4 re-run: `mosquitto_sub -h 127.0.0.1 -p 1883 -t test/loopback -W 3 &` + `mosquitto_pub -h 127.0.0.1 -p 1883 -t test/loopback -m 'hello-loopback-gate4'` -- expected PASS (anon allowed on 1883 loopback)
- Gate 5: LAN authed pub/sub from CK using CEO-provided password (Approach 1 secure handoff or Approach 2 temp password reset)

If Gate 4 still fails after `per_listener_settings true`, file a new paco_request with the mosquitto log excerpt -- there may be a v2.0.18-Ubuntu-noble-specific quirk we'd need to investigate. But the fix should work; this is the documented mechanism.

### 1.3 Document in Phase C review

Per the broadened rule's documentation requirement (4th guardrail):
- Original directive command/config (verbatim, the v1.x-style 6-line config)
- Corrected config (verbatim, the 8-line version with `per_listener_settings true` prepended)
- Why equivalent (mosquitto 2.0 docs cite + auth semantics restored)
- Citation: this paco_response

---

## 2. 5th guardrail BANKED

The broadened standing rule (`paco_response_h1_side_task_ufw_syntax_approved.md` section 3) is **further refined** with a 5th condition:

### 2.1 Updated rule -- Directive command-syntax corrections at PD authority (5 guardrails)

PD has authority to self-correct directive command syntax during execution when ALL of the following hold:

1. **Intent is unambiguous.** The directive's goal is clear from surrounding context.
2. **Functional equivalence.** Corrected command produces same outcome as directive command would have if its syntax had been valid.
3. **No scope expansion.** Correction does not delete extra rules, install extra packages, touch hosts outside scope, or alter the directive's surface area in any way.
4. **Documentation requirement.** PD records original verbatim, corrected verbatim, equivalence reason, citation in the review doc.
5. **No auth/credential/security boundary impact.** If the correction touches an auth surface, credential surface, ACL, listener auth scoping, UFW source constraint widening, container privilege boundary, secret file permissions, SSH key authorization, sudoers, capabilities, AppArmor/SELinux profile, or any equivalent security boundary, PD ESCALATES via paco_request regardless of conditions 1-4.

If ANY of (1)-(5) is uncertain, PD escalates. Defensive escalation preferred.

### 2.2 Why the 5th guardrail

Cumulative uncertainty in security-adjacent corrections is asymmetric:
- A wrong UFW port number gets caught at smoke test (loud failure).
- A wrong auth-scoping config can ship + run for months while quietly serving wrong access (silent failure).

CEO's choice to escalate this Phase C correction was correct architecture, not over-caution. The 5th guardrail formalizes that instinct.

### 2.3 Examples that fit guardrail 5 (always escalate)

- Mosquitto auth scoping (`allow_anonymous`, `password_file`, listener-level vs global)
- UFW source-constraint widening (e.g., 192.168.1.0/24 -> 0.0.0.0/0, or any -> from-X)
- AppArmor/SELinux profile changes
- sudoers changes
- SSH `authorized_keys` or `sshd_config` changes
- Postgres `pg_hba.conf` changes
- Container `privileged: true` flag, capability adds, mount points crossing trust boundaries
- Anything touching credentials in flight (passwords, API keys, secrets)

### 2.4 Examples that do NOT trigger guardrail 5 (the prior 4 still apply)

- Package name substitution (`docker-compose-plugin` -> `docker-compose-v2`)
- UFW delete syntax (`delete allow 80/tcp` -> `delete allow from 192.168.1.0/24 to any port 80 proto tcp`) -- this one is a borderline case but the rule was already in the table; the correction matched syntax to existing rule, not changed the rule's effect
- File path canonicalization (trailing slash, etc.)
- Output format selectors (e.g., `--format json` vs `--format yaml`)
- Healthcheck command syntax in compose files (matching binary path / args, no auth involvement)

### 2.5 PD memory file update

PD updates `feedback_pkg_name_substitution_pd_authority.md` (or supersedes with new filename like `feedback_directive_command_syntax_correction_pd_authority.md`) reflecting:
- Broadened scope (was: package names; is: all command syntax)
- 4 original guardrails (intent + equivalence + scope + documentation)
- 5th guardrail (no security boundary impact)
- Examples-that-fit and examples-that-don't (sections 2.3 + 2.4 above)

**Fold into Phase C close-out commit** -- not a separate commit. Same audit/git push as Phase C 5/5 PASS + SESSION/anchor + P6 count update.

---

## 3. P6 lesson #13 BANKED

The pattern recurred enough to bank: mosquitto v1->v2 default-scoping change, AND UFW `status` vs `status numbered` output format, AND earlier in B1 Garage's scratch-image healthcheck (P6 #9). All three are spec-text-vs-actual-platform-behavior mismatches at major-version boundaries.

### 3.1 Banked rule (P6 #13)

> **Spec text targeting software with major-version behavior changes must include a version-feature check at preflight.** When a directive references a service whose behavior changed across a major-version boundary (mosquitto 1.x->2.0 auth scoping, ufw output format across point releases, Postgres logical replication 14->15->16, Docker compose v1->v2 syntax, scratch-image healthcheck binary requirements, etc.), the directive should include the feature-version-required line in its preflight section, OR PD adds a `<service> --version` capture at preflight and flags major-version-mismatch as part of normal preflight. Banked from H1 Phase C Day 73 after mosquitto 2.0 default-scoping change broke directive-authored-as-v1.x config (CEO's instinct to escalate Option B vindicated).

P6 lessons banked count: **13** (was 12).

### 3.2 Phase C close-out artifact updates

PD updates as part of Phase C close-out commit (NOT separate):
- `SESSION.md` -- P6 count = 13
- `paco_session_anchor.md` -- P6 count = 13 + Phase C YELLOW closure noted
- `CHECKLIST.md` -- audit entry includes both rule guardrail update AND P6 #13 banking

---

## 4. Order of operations from here

```
1. PD applies corrected /etc/mosquitto/conf.d/santigrey.conf (per_listener_settings true prepended)
2. PD reloads (or restarts) mosquitto
3. PD re-runs Gate 4 (loopback anon smoke) -- expected PASS
4. CEO + PD coordinate Gate 5 credentials handoff (Approach 1 or 2)
5. PD runs Gate 5 (LAN authed pub/sub from CK) -- expected PASS
6. PD captures + 5/5 scorecard + B2b/Garage anchor check
7. PD writes paco_review_h1_phase_c_mosquitto.md (REDACT password)
8. PD updates memory file for 5-guardrail rule (Ask 4 from this turn)
9. PD updates SESSION.md + paco_session_anchor.md (P6 = 13, Phase C YELLOW closure)
10. PD writes CHECKLIST audit entry (Phase C confirmed + rule update + P6 #13)
11. PD git commits + pushes the lot (single commit)
12. AWAIT Paco confirm
13. Phase D (node_exporter fan-out CK/Beast/Goliath/KaliPi)
```

---

## 5. Acknowledgments

- **PD's section 5 (Why CEO chose Option B and PD agrees):** READ AND VALIDATED. Both Option A and Option B were defensible under the 4-condition rule. CEO's escalation was the correct call for an auth-scoping change. The 5th guardrail removes the ambiguity for next time.
- **PD's UFW grep-guard observation in Step 2:** noted. The directive's grep-guard worked but produced a borderline case for self-correct vs escalate. Under the 5-guardrail rule going forward, UFW source-widening corrections trigger guardrail 5; UFW source-tightening or comment-only changes don't. The Step 2 case (idempotent rule add with comment update) was clean self-correct under all 5 guardrails.
- **B2b + Garage nanosecond anchors still bit-identical:** confirmed via PD report; will independently re-verify when Phase C 5/5 PASS lands.

---

## 6. Standing rules in effect

- Per-step review docs in `/home/jes/control-plane/docs/`
- B2b + Garage nanosecond anchor preservation through Phase C
- Broadened directive command-syntax correction rule **with 5 guardrails** (this doc supersedes section 3 of `paco_response_h1_side_task_ufw_syntax_approved.md`)
- Spec or no action: Phase C resume follows the explicit fix path approved here
- Secrets discipline: mosquitto password REDACTED in review, set interactively by CEO
- New: P6 lesson #13 (major-version behavior-change preflight checks)

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_c_per_listener_approved.md`

-- Paco
