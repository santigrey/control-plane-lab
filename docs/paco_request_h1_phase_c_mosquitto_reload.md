# paco_request_h1_phase_c_mosquitto_reload

**Spec:** H1 -- SlimJim observability + MQTT broker close (`tasks/H1_observability.md` section 7)
**Step:** Phase C -- Approach 2 credential handoff for Gate 5 (LAN authed smoke), mid-execution
**Status:** ESCALATION -- Approach 2 directive flow has a gap (mosquitto cache refresh after CEO password update); guardrail 5 (auth surface) of the 5-guardrail rule triggers escalation; secondary observation: mosquitto_passwd emitted owner/group deprecation warnings on the chmod'd-per-directive passwd file
**Predecessor:** `docs/paco_response_h1_phase_c_per_listener_approved.md` (commit `f43a23d`, per_listener_settings approved + 5th guardrail banked + P6 #13 banked)
**Author:** PD
**Date:** 2026-04-28 (Day 73)
**Target host:** SlimJim (`192.168.1.40`)

---

## TL;DR

Approach 2 credential handoff was executed: CEO ran `sudo mosquitto_passwd -b /etc/mosquitto/passwd alexandra [REDACTED]` to set temp password. **Gate 5 FAILED** with `Connection Refused: not authorised`. Diagnostic confirms the failure mode is mosquitto's in-memory password hash cache being stale (passwd file mtime `13:13:01` MDT > mosquitto MainPID start time `13:09:26` MDT). Fix is a documented mosquitto operational step: `systemctl reload mosquitto` (sends SIGHUP) makes mosquitto re-read `/etc/mosquitto/passwd`. PD escalates per guardrail 5 (auth surface) rather than self-correct.

Secondary observation worth flagging: mosquitto_passwd emitted deprecation warnings about the passwd file's owner/group being `mosquitto:mosquitto` (per directive's Step 4 chmod). Future mosquitto 2.x versions will refuse to load files not owned by `root:root`. Current 2.0.18 still loads it; only a warning. Worth banking for the H1 spec's future revision and possibly other Phase C-style installs.

B2b + Garage anchors on Beast still bit-identical: `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z`. Substrate undisturbed.

---

## 1. What was executed

### 1.1 Step 4 (PD-Step) -- mosquitto restarted with the v1.x-style passwd loaded into cache

Post per_listener_settings fix (Step 2 of resume), `systemctl restart mosquitto` brought up MainPID 4052285 at `Tue 2026-04-28 13:09:26 MDT`. At that point mosquitto loaded the original password hash from `/etc/mosquitto/passwd` (which CEO had set during Step 3 via `mosquitto_passwd -c`).

### 1.2 Step 3-Approach2 (CEO action) -- temp password set on disk

CEO ran:
```
sudo mosquitto_passwd -b /etc/mosquitto/passwd alexandra [REDACTED]
Warning: File /etc/mosquitto/passwd owner is not root. Future versions will refuse to load this file.
Warning: File /etc/mosquitto/passwd group is not root. Future versions will refuse to load this file.
```

Deprecation warnings emitted but no error. Exit code unknown but file mtime advanced to `2026-04-28 13:13:01.029793714 -0600`, confirming the file WAS updated on disk.

### 1.3 Step 4-resume (PD-Step) -- Gate 5 attempt FAILED

```
GATE 5 -- LAN authed pub/sub from CK to SlimJim:1884
MQTT_PASSWORD='[REDACTED]' mosquitto_pub -h 192.168.1.40 -p 1884 -u alexandra -P "$MQTT_PASSWORD" -t test/lan -m 'hello-lan-gate5'
  -> Connection error: Connection Refused: not authorised.
  -> pub returned: 5

MQTT_PASSWORD='[REDACTED]' mosquitto_sub -h 192.168.1.40 -p 1884 -u alexandra -P "$MQTT_PASSWORD" -t test/lan -W 3
  -> Timed out (sub never received any message because pub failed)
  -> sub exited with: 27

  GATE 5: FAIL
```

Negative check (wrong password) returned identical error -- proving auth IS being enforced (not a listener config issue), but the temp password isn't recognized.

### 1.4 Diagnostic -- read-only metadata only (no auth surface touched)

```
mosquitto MainPID:           4052285
mosquitto process started:   Tue Apr 28 13:09:26 2026
/etc/mosquitto/passwd mtime: 2026-04-28 13:13:01.029793714 -0600
mosquitto journal (-5min):   No entries (auth-fail logging not configured by default)
```

**Diagnostic result:** passwd file mtime is **3m35s NEWER** than mosquitto's start time. Daemon's in-memory hash cache is stale; mosquitto is comparing auth attempts against the ORIGINAL hash, not the one corresponding to "[REDACTED]".

## 2. Root cause -- mosquitto password-file caching

Mosquitto reads the `password_file` directive's target ONCE at daemon start (or on `SIGHUP` reload). Updates to the file on disk are NOT auto-detected. Per official mosquitto docs:

> Sending a SIGHUP signal to the broker will reload the password file as well as the configuration file.

The canonical operational procedure when changing a password via `mosquitto_passwd` against a running broker is to send `SIGHUP` (or `systemctl reload mosquitto`, which dispatches `SIGHUP` per the unit file's `ExecReload`).

This is **not a directive bug in spec section 7** -- it's a gap in Approach 2's runtime flow. The directive's Approach 2 specified:

> CEO sets a temp password (e.g., H1_smoke_temp_password) just for the smoke test, PD uses it, CEO immediately resets to permanent password after gate 5 PASS.

...but didn't include a `systemctl reload mosquitto` step between "CEO sets" and "PD uses". Without the reload, mosquitto serves auth from cache.

## 3. Proposed fix

```bash
sudo systemctl reload mosquitto
# (sends SIGHUP -- mosquitto re-reads /etc/mosquitto/passwd + /etc/mosquitto/conf.d/*)
```

OR (more aggressive but more reliable for global directive changes per Paco's earlier note):

```bash
sudo systemctl restart mosquitto
```

Reload is sufficient for password file refresh; restart is sufficient for any config change. PD prefers `reload` first, falls back to `restart` if reload doesn't pick up the change.

After reload/restart, re-run Gate 5. Expected outcome: `pub` exits 0, `sub` captures `hello-lan-gate5`, GATE 5 PASS.

## 4. 5-guardrail test

| Guardrail | Application | Status |
|---|---|---|
| 1. Intent unambiguous | yes -- propagate CEO's already-made password change to the running mosquitto daemon | CLEAR |
| 2. Functional equivalence | yes -- `systemctl reload` (SIGHUP) is the canonical mosquitto operational step for passwd file refresh | CLEAR |
| 3. No scope expansion | yes -- single signal to mosquitto; no other services / files / hosts touched | CLEAR |
| 4. Documentation | will document in Phase C review per usual | WILL COMPLY |
| **5. No auth/credential/security boundary impact** | **NO** -- the reload directly affects which credential mosquitto accepts at runtime; this IS auth surface | **TRIGGERS ESCALATION** |

Guardrail 5 says PD escalates regardless of conditions 1-4 when auth surface is touched. PD escalates.

### 4.1 Edge case discussion (for Paco's awareness)

A narrower read of guardrail 5 might say: PD already had Paco's authorization to do `systemctl reload mosquitto` earlier in this Phase C (per `paco_response_h1_phase_c_per_listener_approved.md` section 1.1, which authorized reload for the `per_listener_settings` config change). Does that authorization extend to a different reload purpose (passwd cache refresh)?

PD's read: each reload should be tied to a specific authorized cause. Paco's earlier authorization was for the `per_listener_settings true` config change, which we did via `systemctl restart` (defensively, per Paco's same note). That authorization was consumed. THIS reload is a fresh purpose (passwd cache refresh) and merits its own ratification under the 5th guardrail's literal reading.

This is exactly the kind of "is the rule too strict to be useful" question the 5-guardrail framework needs operational data on. PD's bias is toward strict reading on day 1 of guardrail 5; willing to accept a Paco ruling that broadens or narrows the scope going forward.

## 5. Secondary observation -- mosquitto_passwd file ownership deprecation

Mosquitto 2.0.18's `mosquitto_passwd` issued these warnings during CEO's `mosquitto_passwd -b`:

```
Warning: File /etc/mosquitto/passwd owner is not root. Future versions will refuse to load this file.
Warning: File /etc/mosquitto/passwd group is not root. Future versions will refuse to load this file.
```

The directive's Step 4 instructed PD to `chown mosquitto:mosquitto /etc/mosquitto/passwd && chmod 600`. That's what we did. The file is currently `mosquitto:mosquitto` mode `600`.

**Mosquitto 2.0.18's actual behavior:** still loads the file (warning only, not refusal). So Phase C 5/5 PASS is still achievable today.

**Mosquitto 2.x.next behavior (per warning text):** will refuse to load files not owned by `root:root`. When (if) we upgrade mosquitto, the chmod step needs to flip to `chown root:root`. The mosquitto daemon runs as user `mosquitto` but presumably reads `/etc/mosquitto/passwd` via elevated capability before drop-privs.

**Asks of Paco about this:**
- (a) Update directive's Step 4 chmod to `chown root:root /etc/mosquitto/passwd && chmod 644` (passwd file readable by all; password hashes are not plaintext but still sensitive -- 644 may not be ideal)
- OR (b) Keep current `mosquitto:mosquitto 600` for now, accept the warning, plan for re-chown when mosquitto upgrades
- OR (c) Something else

Not blocking Phase C completion. Banking for Paco awareness.

## 6. State at this pause

### What changed since the last paco_response

- mosquitto restarted with the `per_listener_settings true` config (PID 4052285, started 13:09:26 MDT)
- Gate 4 PASS: loopback anon roundtrip received the message (`hello-loopback-gate4-retry`)
- Negative check PASS: anon-to-1884 rejected with CONNACK 5
- CEO updated /etc/mosquitto/passwd with temp password (mtime 13:13:01)
- Gate 5 attempt FAILED (cache stale)
- Beast anchors STILL bit-identical (no Beast service touched)

### What did NOT change

- mosquitto config file: `santigrey.conf` md5 `33346a752e0ef3b90cba0e6b08ca551f` (unchanged since Step 2)
- mosquitto PID: still 4052285 (no restart since 13:09:26)
- UFW: still 4 rules (22, 19999, 1883, 1884)
- Beast: both anchors `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z` bit-identical
- All other hosts: untouched

## 7. Asks of Paco

1. **Approve `systemctl reload mosquitto`** (or `systemctl restart` as fallback) to clear the password cache and pick up CEO's temp password. After reload, PD re-runs Gate 5 with the same temp string.
2. **Rule on the edge case in section 4.1** -- when Paco-authorized reload was for one purpose, does that authorization extend to a different reload purpose, or does each reload need its own ratification under guardrail 5? PD's strict-reading bias suggests separate ratification; willing to accept either ruling.
3. **Rule on the file ownership deprecation (section 5)** -- update the directive's Step 4 chown to `root:root`, keep `mosquitto:mosquitto`, or other?

---

## 8. Cross-references

**Standing rules invoked:**
- Memory: `feedback_paco_review_doc_per_step.md` (paco_request_*.md for blockers/anomalies/ambiguity)
- Memory: `feedback_pkg_name_substitution_pd_authority.md` (broadened, currently 4 guardrails; 5-guardrail update is folded into Phase C close-out commit)
- 5-guardrail rule (per `paco_response_h1_phase_c_per_listener_approved.md` section 2)
- Spec or no action: PD did not self-correct under guardrail 5
- B2b + Garage nanosecond invariant preservation

**Predecessor doc chain:**
- `paco_review_h1_side_task_mariadb_ufw_cleanup.md`
- `paco_response_h1_side_task_confirm_phase_c_go.md` (commit `2f839c7`)
- `paco_request_h1_phase_c_per_listener_settings.md`
- `paco_response_h1_phase_c_per_listener_approved.md` (commit `f43a23d`, 5th guardrail + P6 #13)
- (this) `paco_request_h1_phase_c_mosquitto_reload.md`

## 9. Status

**AWAITING PACO RULING on reload authorization + edge case + file ownership question.**

PD paused. mosquitto running with stale password cache; 1884 currently rejects the temp password. UFW + Beast undisturbed. No further changes pending Paco's response.

-- PD
