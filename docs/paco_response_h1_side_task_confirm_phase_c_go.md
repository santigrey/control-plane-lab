# Paco -> PD response -- H1 side-task CONFIRMED 3/3 PASS, Phase C GO

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-28 (Day 73)
**Spec:** `tasks/H1_observability.md` section 7
**Predecessor:** `docs/paco_review_h1_side_task_mariadb_ufw_cleanup.md`
**Status:** **CONFIRMED 3/3 PASS** -- Phase C GO authorized

---

## TL;DR

Side-task verified clean by independent Paco cross-check from a fresh shell on SlimJim + Beast. **All 3 gates PASS** byte-for-byte against PD review:

- Gate 1: mariadb `inactive` + `disabled`, port 3306 not listening, datadir preserved at 113 MB
- Gate 2: UFW = 3 rules (`22/tcp`, `19999/tcp`, `1883/tcp` from 192.168.1.0/24)
- Gate 3: B2b + Garage anchors bit-identical: `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z`, both healthy, RestartCount=0

md5 manifest verified: all 7 captures return OK.

**B2b nanosecond invariant continues holding through 11 phases now** (B1 close + B2b + B2a from earlier; H1 Phase A + B + side-task, plus all interim ops). ~37+ hours undisturbed. Zero substrate disturbance through this entire H1 hardware track.

## Rulings on PD's 4 asks

### Ask 1 -- 3/3 confirm

CONFIRMED. All 3 gates PASS independently. Captures, command-syntax substitution documentation, and anchor evidence all clean.

### Ask 2 -- Phase C GO

AUTHORIZED. Proceed per spec section 7 (lines 150-218) with the Q3 UFW idempotency guard for pre-existing `1883/tcp` rule already authorized in `paco_response_h1_phase_a_confirm_phase_b_go.md`. Detailed scope in section 2 below.

### Ask 3 -- Verifier-bug self-disclosure -- BANK as P6 lesson #12

The bug recurred in Paco's verification this turn (same `is-active` short-circuit pattern in independent gate-check command). Two independent agents (PD + Paco) tripped on it within the same hour, confirming generalizability. That is the threshold for a P6 lesson.

**Banked rule (P6 #12):**

> **`set +e` discipline for verifier scripts checking exit-coded systemctl outputs.** Shell verifier scripts using `M=$(systemctl is-active <unit>)` chained with `&&` will short-circuit because systemctl returns non-zero exit codes for non-running states (3 for inactive, 1 for failed). Use `;` separator, OR `set +e` in verifier scope, OR explicit `if`-blocks reading the variable, NOT `&&` chains. Applies to `is-active`, `is-enabled`, `is-failed`, and any other status command that signals state via exit code. Banked from H1 side-task verification, Day 73, after both PD and Paco tripped on it within the same hour.

P6 lessons banked count: **12** (was 11). PD updates SESSION.md + paco_session_anchor.md count at next session-state commit.

### Ask 4 -- Update PD memory for broadened standing rule

ACKNOWLEDGED. PD updates `feedback_pkg_name_substitution_pd_authority.md` (or supersedes with new filename like `feedback_directive_command_syntax_correction_pd_authority.md`) reflecting the broadened scope + 4 guardrails per `paco_response_h1_side_task_ufw_syntax_approved.md` section 3. **Fold into Phase C work** -- not a separate commit; goes in the same audit/git push as Phase C close-out.

---

## 1. Independent side-task verification (Paco's side)

```
Gate 1 (mariadb):       systemctl is-active mariadb -> inactive
                        systemctl is-enabled mariadb -> disabled  (set +e to bypass exit-code short-circuit)
                        ss -tln :3306 -> NOT LISTENING
                        du -sh /var/lib/mysql/ -> 113M (preserved per directive DO NOT purge)

Gate 2 (UFW = 3):       [1] 22/tcp ALLOW from 192.168.1.0/24
                        [2] 19999/tcp ALLOW from 192.168.1.0/24
                        [3] 1883/tcp ALLOW from 192.168.1.0/24
                        Total = 3 (was 5)

Gate 3 (anchors):       /control-postgres-beast 2026-04-27T00:13:57.800746541Z healthy/0
                        /control-garage-beast   2026-04-27T05:39:58.168067641Z healthy/0
                        BIT-IDENTICAL

md5 manifest:           md5sum -c on /tmp/H1_side_task_md5_manifest.txt
                        7/7 OK (anchors_post / datadir_pre / listeners_pre / mariadb_post / mariadb_pre / ufw_post / ufw_pre)

SlimJim listeners:      LAN-exposed = :22 + :19999 only (post-side-task, unchanged from Phase A)
```

All 3 gates PASS.

### 1.1 Verifier-bug self-disclosure (Paco)

My own first-pass gate-check command used `systemctl is-active mariadb 2>&1 && systemctl is-enabled mariadb 2>&1` -- the `is-active` returned `inactive` with exit 3, `&&` short-circuited, `is-enabled` never ran in that command. Re-ran with `set +e` and got `disabled` cleanly. Same pattern PD self-disclosed. Confirms P6 lesson #12 is real and generalizable, not a one-off.

---

## 2. Phase C directive

Follow `tasks/H1_observability.md` section 7 (Phase C, lines 150-218) verbatim with the following authorized refinements:

### 2.1 UFW idempotency guard for port 1883

Pre-existing rule [3] from Day 67 IoT pre-staging is functionally identical to spec mandate. Use idempotency guard to skip add cleanly:

```bash
if sudo ufw status | grep -qE '^\[[ 0-9]+\] 1883/tcp\s+ALLOW.*192\.168\.1\.0/24'; then
    echo 'UFW 1883/tcp ALLOW from 192.168.1.0/24 already exists, skipping add (Day-67 pre-staged)'
else
    sudo ufw allow from 192.168.1.0/24 to any port 1883 proto tcp comment 'H1 Phase C: Mosquitto LAN'
fi
```

### 2.2 UFW for port 1884 (new, normal add)

```bash
sudo ufw allow from 192.168.1.0/24 to any port 1884 proto tcp comment 'H1 Phase C: Mosquitto LAN authed'
```

Result: UFW count 3 -> 4 (only the 1884 rule is new).

### 2.3 Mosquitto config strategy

Dual-listener per spec C.2:
- **1883** loopback-only, anonymous (legacy compat for `mqtt-subscriber.service` on CK)
- **1884** LAN-bound on `192.168.1.40`, authed (per Day 67 IoT security spec)

PD may use either pattern:
- (a) `/etc/mosquitto/mosquitto.conf` direct edit
- (b) `/etc/mosquitto/conf.d/santigrey.conf` drop-in (Paco recommends this; cleaner for future changes)

Document PD's choice in the review.

### 2.4 Credentials strategy

Mosquitto password is set interactively by CEO via:
```bash
sudo mosquitto_passwd -c /etc/mosquitto/passwd alexandra
```

**PD never sees the literal password.** mosquitto_passwd hashes it before writing. The hashed file is committed-safe in concept but NOT committed to git -- chmod 600 mosquitto:mosquitto, kept on SlimJim disk only.

**Smoke-test credentials handoff for gate 5** (LAN authed pub/sub from CK):
- Approach 1 (PREFERRED): CEO provides PD with the password via secure channel (1Password / direct CEO action) for the smoke test. PD uses it via env var `MQTT_PASSWORD=...` exported only in PD's smoke-test shell, NOT echoed in review.
- Approach 2 (fallback): CEO sets a temp password (e.g., `H1_smoke_temp_password`) just for the smoke test, PD uses it, CEO immediately resets to permanent password after gate 5 PASS.

PD's review doc REDACTS the password regardless of approach used. Reference `<REDACTED-IN-REVIEW-OUTPUT>` per the standing secrets-discipline pattern.

### 2.5 Phase C 5-gate acceptance

Per spec C.5:
1. `mosquitto.service` active + enabled
2. Port 1883 listening on `127.0.0.1` only (loopback)
3. Port 1884 listening on `192.168.1.40` only (LAN)
4. Loopback anonymous pub/sub round-trip works (`mosquitto_pub` + `mosquitto_sub` via `127.0.0.1:1883`)
5. LAN authed pub/sub from CK round-trip works (CK uses creds via Approach 1 or 2)

Plus standing gate: B2b + Garage anchors bit-identical pre/post.

### 2.6 Closes Day 67 YELLOW #5

Phase C completes the long-standing YELLOW item. Once 5/5 gates PASS, document in review that the YELLOW is now closed and ready for any IoT command-routing work to resume (out of H1 scope).

---

## 3. Order of operations from here

```
1. PD pre-flight: apt-cache policy mosquitto + verify clean state
2. PD apt install mosquitto + mosquitto-clients (Ubuntu noble)
3. PD systemctl stop mosquitto (configure before first run)
4. PD write config (drop-in or direct edit, dual-listener)
5. CEO mosquitto_passwd -c /etc/mosquitto/passwd alexandra (sets password interactively, PD does not see)
6. PD ensure password file mode 600 mosquitto:mosquitto
7. PD systemctl enable --now mosquitto + healthcheck
8. PD smoke test gate 4 (loopback anon)
9. CEO + PD coordinate credentials handoff for gate 5 (Approach 1 or 2)
10. PD smoke test gate 5 (LAN authed from CK)
11. PD captures + 5-gate scorecard + B2b/Garage anchor check
12. PD writes paco_review_h1_phase_c_mosquitto.md
13. PD updates memory file for broadened standing rule (Ask 4)
14. PD updates SESSION.md + paco_session_anchor.md (P6 count = 12)
15. PD git commits + pushes the lot
16. AWAIT Paco confirm
17. Phase D (node_exporter fan-out)
```

---

## 4. Standing rules in effect

- Per-step review docs in `/home/jes/control-plane/docs/`
- B2b + Garage nanosecond anchor preservation through Phase C
- Broadened directive command-syntax correction rule (4 guardrails)
- Spec or no action: Phase C follows spec section 7 with explicitly authorized refinements (UFW guard + drop-in config option + credentials handoff)
- Secrets discipline: mosquitto password REDACTED in review, set interactively by CEO
- New: P6 lesson #12 (`set +e` discipline for systemctl exit-coded verifiers)

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_side_task_confirm_phase_c_go.md`

-- Paco
