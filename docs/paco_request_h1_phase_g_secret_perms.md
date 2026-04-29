# paco_request_h1_phase_g_secret_perms

**Spec:** H1 -- observability stack first container boot (`tasks/H1_observability.md` Phase G)
**Step:** Phase G -- post Path A chown applied + compose up retry. Path A landed cleanly for data dirs. New permission failure surfaced on the docker secret bind-mount (`grafana-admin.pw`).
**Status:** ESCALATION. Phase G Gate 1 still FAILING (grafana side only). Same class as ESC #1 (host UID != container UID on a bind-mount), different scope (file vs. directory). Paco architectural ruling needed on chown-vs-compose-secret-long-syntax.
**Predecessor:** `docs/paco_response_h1_phase_g_path_a_approved.md` (commit `9aef8d1`)
**Author:** PD
**Date:** 2026-04-29 (Day 74)
**Target host:** SlimJim (`192.168.1.40`)

---

## TL;DR

Path A worked perfectly for the data dirs. obs-prometheus reached `healthy` with Restarts=0 on first compose-up retry. obs-grafana enters new crash loop:

```
Getting secret GF_SECURITY_ADMIN_PASSWORD from /run/secrets/grafana_admin_pw
/run.sh: line 59: /run/secrets/grafana_admin_pw: Permission denied
```

Same mechanism as ESC #1: container UID (472) cannot read host bind-mount with mode 600 owned by host UID 1000 (jes). Different scope: secret file via Docker compose secrets, not data directory.

Resolution choice between (X) host chown of secret file to 472:472 and (Y) compose.yaml long-syntax secret with explicit uid/gid/mode mapping. PD bias slightly toward Y (operator ergonomics), but X is consistent with Path A pattern. Either works; Paco architectural call.

`docker compose down` already executed inline with CEO authorization to halt the crash loop. State preserved bit-clean. Beast anchors holding.

---

## 1. Failure evidence

### 1.1 obs-grafana state during crash loop (captured before compose-down)

```
Status=restarting ExitCode=1 Restarts=9 (climbing)
StartedAt=2026-04-29T20:05:37.57566294Z FinishedAt=2026-04-29T20:05:38.515860671Z
Error=
```

Lifetime ~1 second per attempt. `restart: unless-stopped` triggers immediate retry. Same pattern as ESC #1 prometheus, different ExitCode.

### 1.2 Grafana log (full, repeating)

```
Getting secret GF_SECURITY_ADMIN_PASSWORD from /run/secrets/grafana_admin_pw
/run.sh: line 59: /run/secrets/grafana_admin_pw: Permission denied
```

This pair repeats on every restart. Grafana's `/run.sh` entrypoint reads the secret file at line 59 (the `__FILE` env-var resolution path), can't read it, exits with code 1.

### 1.3 obs-prometheus state (counterpoint -- Path A worked here)

First compose-up attempt:
```
/obs-prometheus Status=running Health=healthy Restarts=0
```

Reached `healthy` cleanly via the wget healthcheck. Path A chown landed perfectly for prom-data. obs-prometheus is unaffected by the secret-file issue (it doesn't use the grafana secret).

### 1.4 grafana-data side-observation (informational)

During grafana's brief startup attempts, it created two subdirectories inside the chowned grafana-data:
```
drwx------ 4  472  472 4096 Apr 29 14:05 .
drwxr-xr-x 2 root root 4096 Apr 29 14:05 dashboards
drwxr-xr-x 2  472 root 4096 Apr 29 14:05 plugins
```

`dashboards` is owned `root:root`, `plugins` is owned `472:root`. This is grafana entrypoint creating dirs as root before dropping to UID 472. Likely benign (grafana later uses these as 472), but worth noting -- might want to recursively chown post-first-run, or accept the mixed ownership. Not blocking for this ESC.

---

## 2. Root cause

### 2.1 Host file ownership

```
-rw------- 1 jes jes 11 Apr 29 13:27 /home/jes/observability/grafana-admin.pw
```

Mode 600, owned `jes:jes` (UID 1000:1000), 11 bytes (CEO-written admin password).

### 2.2 compose.yaml short-syntax secret declaration

```yaml
services:
  grafana:
    environment:
      GF_SECURITY_ADMIN_PASSWORD__FILE: /run/secrets/grafana_admin_pw
    secrets:
      - grafana_admin_pw

secrets:
  grafana_admin_pw:
    file: ./grafana-admin.pw
```

Short-syntax (`- grafana_admin_pw`) bind-mounts the host file into the container at `/run/secrets/grafana_admin_pw` with **default uid/gid/mode** -- which means it inherits the HOST file's ownership and permissions, NOT a remap to container UID.

### 2.3 Mismatch

Container user (472) tries to read `/run/secrets/grafana_admin_pw` which inside the container is owned 1000:1000 mode 600. Linux DAC permission denial. `/run.sh` exits with code 1. `restart: unless-stopped` triggers immediate retry. Loop.

This is the EXACT same root-cause class as ESC #1 (host UID != container UID on a bind-mount inheriting host permissions). Just file-scoped instead of directory-scoped, and via the docker-compose `secrets:` mechanism instead of `volumes:`.

---

## 3. Why this surfaced after Path A

Path A correctly addressed the data directories. The secret file was outside Path A's scope. The Phase E spec build did NOT account for either the data-dir UID alignment (banked as P6 #18 candidate) or the secret-file UID alignment (this ESC).

The lesson set is widening: ALL bind-mounts (volumes AND secrets) inheriting host-file ownership against non-host container UIDs are a class of failure. Phase E spec amendment should cover this systematically, not just per-occurrence.

---

## 4. Resolution paths

### 4.1 Path X -- host chown of secret file to 472:472 (extends Path A pattern)

```bash
sudo chown 472:472 /home/jes/observability/grafana-admin.pw
# Mode 600 preserved (still owner-readable-only)
# Container UID 472 can now read its own file
```

**Pros:**
- Mechanically identical to Path A (just file-scoped instead of dir-scoped)
- One command, no compose.yaml edit, no guardrail 4 documentation burden
- Reversible (chown back to jes:jes)

**Cons:**
- Host `jes` user can no longer `cat` or `vi` the file directly without `sudo`
- Awkward for human-managed credential rotation (CEO would need sudo to re-write the file)
- Host file ownership becomes UNKNOWN:UNKNOWN (UID 472 has no /etc/passwd entry on host) -- visually confusing in `ls -la`

### 4.2 Path Y -- compose long-syntax secret with explicit uid/gid/mode (PD bias)

Edit compose.yaml grafana service block:

```yaml
services:
  grafana:
    secrets:
      - source: grafana_admin_pw
        target: grafana_admin_pw
        uid: "472"
        gid: "472"
        mode: 0400
```

**Pros:**
- Host file ownership stays `jes:jes` mode 600 -- ergonomic for CEO/operator credential rotation
- Declarative -- compose.yaml documents the runtime mapping intent
- Survives reboots and host-file-edits without re-chown
- Cleaner separation: host owns the file, compose handles container-side mapping
- Same approach is standard for Postgres + Garage stacks; consistent with B-substrate pattern

**Cons:**
- compose.yaml edit -- requires guardrail 4 documentation in close-out review
- New md5 for compose.yaml (currently `db89319cad27c091ab1675f7035d7aa3`)
- Phase E config-only spec didn't anticipate long-syntax; minor spec-state drift

### 4.3 Path Z -- chmod 644 the host file

```bash
chmod 644 /home/jes/observability/grafana-admin.pw
```

**Status: NOT RECOMMENDED.** Anti-pattern. The admin password becomes world-readable on the host filesystem. Security regression. Rejected.

### 4.4 Path W -- environment variable instead of file

```yaml
environment:
  GF_SECURITY_ADMIN_PASSWORD: <password-inline>
```

**Status: NOT RECOMMENDED.** Env vars are exposed via `docker inspect`, container `/proc/1/environ`, and any orchestration sidecar. File-based secrets are strictly safer. Rejected.

---

## 5. PD bias

**Path Y** -- compose long-syntax secret. Reasons:
- Operator ergonomics: CEO can rotate admin pw via simple file edit, no chown round-trip
- Architectural cleanliness: compose.yaml documents the intent, host filesystem stays canonical
- Pattern consistency: matches what we'd do for any future secret (Postgres pw, Garage S3 keys, etc.)
- The cost (one compose.yaml edit + guardrail 4 doc) is small

**Path X** is acceptable fallback if Paco prefers strict consistency with Path A's chown approach. Both work.

---

## 6. Recommended interim action -- ALREADY DONE

`docker compose down` executed inline with CEO authorization (same pattern as before ESC #1 ruling). Stack stopped clean:
- obs-grafana + obs-prometheus removed
- observability_default network removed
- prom-data + grafana-data: chown state preserved (`65534:65534` and `472:472` respectively)
- grafana-admin.pw: untouched (`jes:jes` 600)
- compose.yaml: untouched (md5 `db89319cad27c091ab1675f7035d7aa3`)
- Beast anchors: bit-identical (B2b: 2026-04-27T00:13:57.800746541Z, Garage: 2026-04-27T05:39:58.168067641Z)

Ready for either Path X or Path Y to apply cleanly and resume from Step 4 (compose up).

---

## 7. Asks of Paco

1. **Path ruling.** X (host chown) vs Y (compose long-syntax) vs other?
2. **P6 #18 amendment scope.** Should the Phase E spec amendment cover ALL bind-mount UID alignment (volumes + secrets), or stay scoped to data-dirs and bank a separate P6 #19 for secret-file alignment?
3. **`paco_response_h1_phase_g_path_a_approved.md` directive parity.** Path A response specified data-dir chown only. If the ruling is Y (compose edit), the close-out review should note that the spec-amendment is broader than Path A's directive. Paco confirms scope?
4. **mixed-ownership of grafana-data subdirs (dashboards as root:root, plugins as 472:root)** observed during grafana's failed start attempts. Bank as P5 cleanup carryover, or include in Phase G close-out chmod step?

---

## 8. State at this pause

### 8.1 What is true now

- obs-prometheus: REMOVED (was healthy on first compose-up; reached health cleanly with Path A chown applied)
- obs-grafana: REMOVED (crash-looped on secret-file permission, never reached health)
- /home/jes/observability/prom-data: drwx------ 65534:65534 (Path A applied, preserved through compose-up + compose-down cycle)
- /home/jes/observability/grafana-data: drwx------ 472:472 (Path A applied, preserved; contains stub `dashboards/` (root:root) and `plugins/` (472:root) from grafana's failed-start attempts)
- /home/jes/observability/grafana-admin.pw: -rw------- 1000:1000 jes:jes 11 bytes (UNCHANGED from CEO write)
- compose.yaml: md5 `db89319cad27c091ab1675f7035d7aa3` (UNCHANGED, Phase E artifact)
- mosquitto.service + agent-bus.service + node_exporter: unaffected
- Beast anchors: bit-identical pre/post all of Phase G work
- Phase G Gate 1: FAILING (grafana cannot start)

### 8.2 What is unchanged since `9aef8d1`

- compose.yaml content + md5
- grafana-admin.pw content + ownership + permissions
- All grafana provisioning + dashboard files
- prometheus.yml
- UFW (still 7 rules; Bridge NAT path unevaluated)
- All other hosts

---

## 9. Cross-references

**Standing rules invoked:**
- 5-guardrail rule: this is OUTSIDE the rule's domain (substantive operational decision touching credential file ownership; not mechanical correction)
- Spec or no action: PD has not improvised state changes (compose down was inline-CEO-authorized, matching prior ESC #1 pattern)
- B2b + Garage anchor preservation invariant: holding
- Handoff protocol effective (commit `65e3fd4`)

**Predecessor doc chain (Phase G):**
- `paco_response_h1_phase_f_confirm_phase_g_go.md` (commit `701e1d3`)
- `paco_request_h1_phase_g_data_dir_perms.md` (PD ESC #1)
- `paco_response_h1_phase_g_path_a_approved.md` (commit `9aef8d1`)
- (this) `paco_request_h1_phase_g_secret_perms.md` (PD ESC #2 -- secret file scope)

---

## 10. Status

**AWAITING PACO RULING on:**
1. Path X (host chown) vs Path Y (compose long-syntax secret) vs other
2. P6 #18 amendment scope (data-dirs only or broader bind-mount-UID-alignment class)
3. Phase G close-out review scope guidance if Y selected (compose.yaml change directive)
4. mixed-ownership grafana-data subdir cleanup (P5 carryover or Phase G chmod step)

PD paused. Stack down clean. Substrate undisturbed. Beast anchors bit-identical. No further changes pending Paco's response.

-- PD
