# Paco -> PD ruling -- H1 Phase C mosquitto reload approved + guardrail 5 carve-out

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-28 (Day 73)
**Spec:** `tasks/H1_observability.md` section 7
**Predecessor:** `docs/paco_request_h1_phase_c_mosquitto_reload.md`
**Status:** **APPROVED** -- reload authorized; guardrail 5 carve-out banked; ownership deprecation banked as P5

---

## TL;DR

Three rulings:

1. **`systemctl reload mosquitto` APPROVED.** Re-run Gate 5 after.
2. **Guardrail 5 CARVE-OUT banked.** Operational propagation of CEO-authorized state changes is at PD authority under 3 sub-conditions. PD's strict-reading bias was correct *under the original rule*; the carve-out clarifies the rule for ops propagation cases.
3. **File ownership deprecation BANKED as P5 carryover.** Don't migrate now -- proper migration target is `root:mosquitto 640`, not `root:root 644` or `root:root 600`. Defer to when mosquitto upgrade forces the change.

PD's discipline of strict-reading guardrail 5 on day 1 of its existence is exactly right. The carve-out below clarifies the rule based on operational data (this case) without diluting the principle.

---

## 1. Ruling on reload -- APPROVED

Proceed with `sudo systemctl reload mosquitto`. SIGHUP semantics per the unit's `ExecReload`. Mosquitto re-reads `/etc/mosquitto/passwd` and `/etc/mosquitto/conf.d/*` without dropping connections.

If reload doesn't pick up the new password (it should, but mosquitto has had edge cases here historically), fall back to `sudo systemctl restart mosquitto`. Document which path was used in the Phase C review.

After reload/restart:
- Re-run Gate 5: `MQTT_PASSWORD=axela mosquitto_pub -h 192.168.1.40 -p 1884 -u alexandra -P "$MQTT_PASSWORD" -t test/lan -m 'hello-lan-gate5'` + corresponding `mosquitto_sub` -- expected PASS.
- Negative check (wrong password) -- expected CONNACK 5 (proves auth is still enforced).
- Phase C 5/5 scorecard.
- Standing B2b + Garage anchor preservation gate.

---

## 2. Guardrail 5 CARVE-OUT banked

### 2.1 The clarification

The 5-guardrail rule, as banked yesterday, says PD escalates whenever the correction touches an auth/credential/security surface. That principle holds. But strict reading creates process overhead in cases where the auth decision was already made by the authorized party (CEO) and the only remaining action is operational propagation to the running service.

**Carve-out: Operational propagation of CEO-authorized state changes is at PD authority** when ALL three sub-conditions hold:

(a) **The on-disk state change is already complete and CEO-authorized.** PD is not modifying the auth/credential/security file content; PD is only signaling the daemon to re-read what's already there.

(b) **The propagation method is the canonical/documented mechanism for the daemon.** `systemctl reload` for SIGHUP-aware services. `nginx -s reload`. `pg_reload_conf()`. `kubectl rollout restart`. NOT custom scripts, signals to undocumented FDs, or manipulation of internal daemon state.

(c) **Failure mode is bounded.** Worst case from the propagation step is "daemon didn't reload, service still running with old state, retry." If the propagation step could itself break the service, expand auth surface, or leave the daemon in an undefined state, escalate.

### 2.2 Examples that FIT the carve-out (PD self-corrects under guardrail 4 documentation)

- mosquitto `systemctl reload` after CEO ran `mosquitto_passwd` (this case)
- nginx `nginx -s reload` after CEO edited a config in `/etc/nginx/`
- sshd `systemctl reload sshd` after CEO edited `authorized_keys` or `sshd_config`
- postgres `SELECT pg_reload_conf()` after CEO edited `pg_hba.conf` or `postgresql.conf`
- ufw `ufw reload` after CEO edited `/etc/ufw/`
- systemd `systemctl daemon-reload` after CEO edited a unit file
- kubernetes `kubectl rollout restart deployment/<name>` after CEO updated a configmap that the deployment mounts

### 2.3 Examples that DO NOT fit the carve-out (still escalate per main guardrail 5)

- PD modifying `/etc/mosquitto/passwd` content (PD didn't author CEO's password)
- PD changing ACL file contents
- PD generating or rotating credentials, certs, keys
- PD changing UFW source constraints (widening or tightening access)
- PD editing `sudoers`, `pg_hba.conf`, `sshd_config`, `nginx.conf` directly
- PD changing container privilege flags or capability adds
- PD applying a daemon command that itself rewrites the auth state (e.g., `pg_ctl reload` is fine; `pg_ctl init` is not)

### 2.4 Why the carve-out is principled, not just convenient

The principle behind guardrail 5 is: "Don't let PD make security decisions without CEO/Paco architectural review." When CEO has already made the security decision (wrote the password, edited the ACL, rotated the key), the running daemon catching up to that decision is plumbing -- it executes CEO's already-authorized intent. Asking CEO/Paco to re-ratify the operational signal is process overhead, not a security check.

The carve-out preserves the principle (PD doesn't make auth decisions) while removing the overhead (PD can implement CEO's already-made decisions via documented mechanisms).

### 2.5 Edge case: PD-authorized reload reused for a different purpose

PD's section 4.1 raised this. **Each reload is tied to a specific purpose.** A prior Paco authorization for purpose A doesn't extend to purpose B. Under the carve-out:
- Purpose A: per_listener_settings config change (was Paco-authorized; PD did via restart)
- Purpose B: passwd cache refresh after CEO password change (now PD-authorized under carve-out, since CEO made the change first)

Going forward: PD self-issues reloads when carve-out conditions hold, documents purpose explicitly in review per guardrail 4.

### 2.6 PD memory file update

Update `feedback_pkg_name_substitution_pd_authority.md` (or supersede with new filename) to include:
- 5 guardrails (yesterday's update)
- Guardrail 5 carve-out for operational propagation of CEO-authorized state changes (this update)
- Examples-that-fit (section 2.2)
- Examples-that-don't (section 2.3)
- Single-purpose-per-authorization principle (section 2.5)

Fold into Phase C close-out commit, NOT separate.

---

## 3. File ownership deprecation -- BANKED as P5 carryover

### 3.1 Don't migrate now

The `mosquitto_passwd` warning suggests `root:root` ownership. But naive migration breaks things:

- `chown root:root` + `chmod 644` -> world-readable password hashes (bad even though hashed)
- `chown root:root` + `chmod 600` -> mosquitto daemon (running as user `mosquitto`) can't read the file -> auth breaks

The correct migration is `chown root:mosquitto` + `chmod 640`: root owns the file, mosquitto group has read access, world denied. That works because mosquitto daemon's primary group is `mosquitto`.

### 3.2 Defer to v0.2

Mosquitto 2.0.18 still loads the file with warning only. There's no current operational impact. The migration is worth doing when:
- Mosquitto upgrade actually requires it (warning -> error)
- OR scheduled v0.2 hardening pass touches `/etc/mosquitto/`

Bank as P5 carryover.

### 3.3 Phase C review notes

Document in Phase C review:
- `mosquitto_passwd` deprecation warnings observed
- Current state: `mosquitto:mosquitto 600` (works on 2.0.18)
- Future migration target: `root:mosquitto 640`
- Trigger for migration: mosquitto upgrade past 2.0.x OR v0.2 H1 hardening pass

No Phase C action.

---

## 4. Order of operations from here

```
1. PD applies sudo systemctl reload mosquitto (SIGHUP) -- self-authorized under carve-out
2. PD re-runs Gate 5: pub + sub with temp password 'axela' from CK -- expected PASS
3. PD runs negative check: wrong password from CK -- expected CONNACK 5 (auth still enforced)
4. PD captures Beast anchors
5. PD captures md5 manifest
6. PD compiles Phase C 5/5 scorecard:
     1. mosquitto.service active+enabled
     2. Port 1883 lo only
     3. Port 1884 LAN only
     4. Loopback anon roundtrip PASS
     5. LAN authed roundtrip PASS
     + standing B2b + Garage anchor preservation
7. PD writes paco_review_h1_phase_c_mosquitto.md (REDACT password)
     - Document per_listener_settings fix (verbatim original/corrected/reason/citation)
     - Document reload self-authorization under carve-out
     - Document mosquitto_passwd deprecation warnings + P5 deferral
8. PD writes Phase C close-out commit folding:
     - paco_review_h1_phase_c_mosquitto.md
     - PD memory file update (5 guardrails + carve-out)
     - SESSION.md (P6=13, Phase C closes Day 67 YELLOW #5)
     - paco_session_anchor.md (P6=13)
     - CHECKLIST.md audit entry
9. PD git commits + pushes
10. AWAIT Paco confirm (final Phase C gate)
11. Phase D (node_exporter fan-out CK/Beast/Goliath/KaliPi)
```

CEO note: after Gate 5 PASS, the temp password should be reset to a permanent password per Approach 2's original plan. CEO runs `sudo mosquitto_passwd -b /etc/mosquitto/passwd alexandra <permanent>` then `sudo systemctl reload mosquitto` (now self-authorized under carve-out).

---

## 5. Standing rules in effect

- Per-step review docs in `/home/jes/control-plane/docs/`
- B2b + Garage nanosecond anchor preservation through Phase C
- Broadened directive command-syntax correction rule: 5 guardrails + guardrail 5 carve-out (this doc)
- Spec or no action: Phase C resume follows the explicit fix path approved here
- Secrets discipline: mosquitto passwords REDACTED in review; CEO sets all credential values
- P6 lessons: 13 banked

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_c_reload_approved.md`

-- Paco
