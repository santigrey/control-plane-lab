# feedback_directive_command_syntax_correction_pd_authority

**Type:** PD memory / standing rule
**Status:** ACTIVE (banked Phase C close-out, Day 73 / 2026-04-28)
**Supersedes:** `feedback_pkg_name_substitution_pd_authority.md` (banked 2026-04-27, narrow scope: package-name substitutions only)
**Source rulings:**
- `docs/paco_response_h1_side_task_ufw_syntax_approved.md` §3 -- broadened scope from pkg-name to all command-syntax; original 4 guardrails
- `docs/paco_response_h1_phase_c_per_listener_approved.md` §2 -- 5th guardrail added (auth/security boundary)
- `docs/paco_response_h1_phase_c_reload_approved.md` §2 -- guardrail 5 carve-out for operational propagation of CEO-authorized state changes

---

## 1. The rule -- Directive command-syntax corrections at PD authority (5 guardrails)

PD has authority to self-correct directive command syntax during execution when ALL of the following hold:

1. **Intent is unambiguous.** The directive's goal is clear from surrounding context (e.g., "remove the orphan 80/443 rules," "install the Compose v2 plugin," "add per_listener_settings true to santigrey.conf").

2. **Functional equivalence.** The corrected command produces the same outcome as the directive command would have if its syntax had been valid (same UFW rule objects gone, same package binary installed at same path, same config directive applied to same scope).

3. **No scope expansion.** The correction does not delete extra rules, install extra packages, touch hosts outside scope, or alter the directive's surface area in any way.

4. **Documentation requirement.** PD records in the review doc:
   - The original directive command (verbatim)
   - The corrected command (verbatim)
   - The reason they're equivalent (one-line)
   - Citation to the paco_response that authorized the broader rule (this memory file's source rulings) OR to a Paco ruling on this specific class of correction

5. **No auth/credential/security boundary impact.** If the correction touches an auth surface, credential surface, ACL, listener auth scoping, UFW source-constraint widening, container privilege boundary, secret file permissions, SSH key authorization, sudoers, capabilities, AppArmor/SELinux profile, or any equivalent security boundary, PD ESCALATES via paco_request regardless of conditions 1-4. (Subject to the carve-out in §2.)

If ANY of (1)-(5) is uncertain, PD escalates via `paco_request_*.md` and pauses. **Defensive escalation is preferred over wrong execution.**

---

## 2. Guardrail 5 carve-out -- Operational propagation of CEO-authorized state changes

The 5th guardrail says PD escalates whenever a correction touches an auth/credential/security surface. That principle holds. Strict reading would create process overhead in cases where the auth decision was already made by the authorized party (CEO) and the only remaining action is operational propagation to the running service.

**Carve-out: Operational propagation of CEO-authorized state changes is at PD authority** when ALL three sub-conditions hold:

(a) **The on-disk state change is already complete and CEO-authorized.** PD is not modifying the auth/credential/security file content; PD is only signaling the daemon to re-read what's already there.

(b) **The propagation method is the canonical/documented mechanism for the daemon.** `systemctl reload` for SIGHUP-aware services. `nginx -s reload`. `pg_reload_conf()`. `kubectl rollout restart`. NOT custom scripts, signals to undocumented FDs, or manipulation of internal daemon state.

(c) **Failure mode is bounded.** Worst case from the propagation step is "daemon didn't reload, service still running with old state, retry." If the propagation step could itself break the service, expand auth surface, or leave the daemon in an undefined state, escalate.

### 2.1 Single-purpose-per-authorization principle

Each reload/propagation action is tied to a specific purpose. A prior Paco authorization for purpose A does NOT extend to purpose B. Under the carve-out:

- Purpose A: `per_listener_settings` config change (Paco-authorized; PD did via restart)
- Purpose B: passwd cache refresh after CEO password change (PD-authorized under carve-out, since CEO made the underlying change first)

Going forward: PD self-issues reloads when carve-out conditions hold, documents purpose explicitly in review per guardrail 4.

### 2.2 Why the carve-out is principled, not just convenient

The principle behind guardrail 5: "Don't let PD make security decisions without CEO/Paco architectural review." When CEO has already made the security decision (wrote the password, edited the ACL, rotated the key), the running daemon catching up to that decision is plumbing -- it executes CEO's already-authorized intent. Asking CEO/Paco to re-ratify the operational signal is process overhead, not a security check.

The carve-out preserves the principle (PD doesn't make auth decisions) while removing the overhead (PD can implement CEO's already-made decisions via documented mechanisms).

---

## 3. Examples that FIT the rule (PD self-corrects under guardrails 1-4)

- Package name substitution within an apt repo (`docker-compose-plugin` → `docker-compose-v2`): same binary, same path, same outcome.
- UFW delete syntax mismatch when source-constraint is in actual rule state but missing from directive: same rule object removed, same UFW table state.
- A typo in a `systemctl <noun>` command where the corrected noun has the obvious meaning (e.g., `systemctl restartt` → `systemctl restart`).
- File path with extra/missing trailing slash where canonicalization is unambiguous on the target filesystem.
- Output format selector swap that doesn't affect data extracted (e.g., `--format json` ↔ `--format yaml` when both are valid for the same fields).
- Healthcheck command syntax in compose files (matching binary path / args, no auth involvement).

---

## 4. Examples that FIT the carve-out (PD self-corrects under guardrails 1-4 + §2)

- mosquitto `systemctl reload` after CEO ran `mosquitto_passwd` to add/update a credential
- nginx `nginx -s reload` after CEO edited a config in `/etc/nginx/`
- sshd `systemctl reload sshd` after CEO edited `authorized_keys` or `sshd_config`
- postgres `SELECT pg_reload_conf()` after CEO edited `pg_hba.conf` or `postgresql.conf`
- ufw `ufw reload` after CEO edited `/etc/ufw/`
- systemd `systemctl daemon-reload` after CEO edited a unit file
- kubernetes `kubectl rollout restart deployment/<name>` after CEO updated a configmap that the deployment mounts

---

## 5. Examples that do NOT fit the rule (PD escalates regardless)

### 5.1 Triggers guardrail 5 (security/auth surface)

- Mosquitto auth scoping (`allow_anonymous`, `password_file`, listener-level vs global)
- UFW source-constraint widening (e.g., `192.168.1.0/24` → `0.0.0.0/0`, or any → from-X)
- AppArmor / SELinux profile changes
- sudoers changes
- SSH `authorized_keys` or `sshd_config` changes
- Postgres `pg_hba.conf` changes
- Container `privileged: true` flag, capability adds, mount points crossing trust boundaries
- Anything touching credentials in flight (passwords, API keys, secrets)

### 5.2 Does NOT fit the carve-out (escalate per main guardrail 5)

- PD modifying `/etc/mosquitto/passwd` content (PD didn't author CEO's password)
- PD changing ACL file contents
- PD generating or rotating credentials, certs, keys
- PD changing UFW source constraints (widening or tightening access)
- PD editing `sudoers`, `pg_hba.conf`, `sshd_config`, `nginx.conf` directly
- PD changing container privilege flags or capability adds
- PD applying a daemon command that itself rewrites the auth state (e.g., `pg_ctl reload` is fine; `pg_ctl init` is not)

### 5.3 Other guardrail-1-3 fails

- A command that *does* work but PD believes a different command would be "better" (this is scope expansion / opinion override, not syntax correction).
- A package name that maps to multiple candidates (e.g., `python-cryptography` vs `python3-cryptography` -- requires a Python-version decision).
- Any change that affects more rules / files / services than the directive named.
- Any case where PD is uncertain whether (1)-(5) hold.

---

## 6. Why guardrail 5 specifically (asymmetric failure mode)

Cumulative uncertainty in security-adjacent corrections is asymmetric:

- A wrong UFW port number gets caught at smoke test (loud failure).
- A wrong auth-scoping config can ship + run for months while quietly serving wrong access (silent failure).

Defensive escalation on auth surfaces is not over-caution -- it's correct architecture given the asymmetry. The carve-out (§2) preserves this principle while removing process overhead for cases where the security decision is already made.

---

## 7. Application history

| Date | Phase / Step | Application | Outcome |
|---|---|---|---|
| 2026-04-27 (Day 72) | H1 Phase B | `docker-compose-plugin` → `docker-compose-v2` substitution | Originally escalated (rule didn't exist yet); banked narrow-scope rule from this case |
| 2026-04-28 (Day 73) | H1 side-task | UFW delete syntax correction | Originally escalated (rule was new, UFW felt high-stakes); banked broadened-scope rule (4 guardrails) from this case |
| 2026-04-28 (Day 73) | H1 Phase C ESC #1 | mosquitto `per_listener_settings` config change | Escalated correctly under new guardrail 5 (auth-scoping); rule added 5th guardrail from this case |
| 2026-04-28 (Day 73) | H1 Phase C ESC #4 | mosquitto reload after CEO `mosquitto_passwd` | Escalated under strict-reading of guardrail 5; ruling banked carve-out for operational propagation |

Going forward: PD self-corrects under guardrails 1-5 + carve-out as documented above, escalates when uncertain, and documents per guardrail 4 in every applicable review doc.
