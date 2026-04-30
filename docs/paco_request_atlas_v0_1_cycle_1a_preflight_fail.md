# paco_request_atlas_v0_1_cycle_1a_preflight_fail

**Spec:** Atlas v0.1 -- Cycle 1A package skeleton on Beast (`tasks/atlas_v0_1.md`)
**Step:** Cycle 1A Step 1 -- P6 #16 single-host preflight on Beast
**Status:** ESCALATION. 3 real preflight failures + 1 spec authoring error in the URL Paco wrote. Per spec directive "If any preflight fails, STOP and file paco_request. Do NOT improvise."
**Predecessor:** `docs/handoff_paco_to_pd.md` (Day 75, cleared per protocol; HEAD `e370c67`)
**Author:** PD
**Date:** 2026-04-30 (Day 75)
**Target host:** Beast (`192.168.1.152`)

---

## TL;DR

P6 #16 preflight on Beast surfaces 3 dependencies missing or unconfigured: (a) Python 3.11+ not installed (only 3.10.12), (b) `replicator_role` Postgres auth not pre-configured (no `~/.pgpass`), (c) Tailscale CLI + tailscale0 interface absent. Plus 1 spec authoring error: the Garage health URL in the preflight block (`http://localhost:3900/health`) is wrong -- Garage's S3 listener on `:3900` rejects anonymous + the admin endpoint is on `:3903`. Correct URL `http://127.0.0.1:3903/health` returns "Garage is fully operational" -- so Garage is healthy and the spec just needs a URL fix.

mcp Python SDK is installable from PyPI at 1.27.0; disk is fine (4.0T free); both Beast Docker substrates (Postgres + Garage) are healthy + bit-identical to all H1 captures. PD has not improvised any fixes.

Four Paco rulings needed.

---

## 1. Preflight evidence (verbatim)

### 1.1 Python version

```
Python 3.10.12
```

```
ls -la /usr/bin/python3.* 2>&1
-rwxr-xr-x 1 root root 5937704 Mar  3 11:56 /usr/bin/python3.10
lrwxrwxrwx 1 root root      34 Mar  3 11:56 /usr/bin/python3.10-config -> x86_64-linux-gnu-python3.10-config
```

```
apt-cache policy python3.11
python3.11:
  Installed: (none)
  Candidate: 3.11.0~rc1-1~22.04
  Version table:
     3.11.0~rc1-1~22.04 500
        500 http://us.archive.ubuntu.com/ubuntu jammy-updates/universe amd64 Packages
```

**Status:** FAIL. Beast runs Ubuntu 22.04 (jammy). The only python3.11 candidate in jammy's repos is `3.11.0~rc1-1~22.04` (release-candidate-1 from August 2022). Production-grade 3.11+ requires deadsnakes PPA, pyenv, or build-from-source.

### 1.2 Disk free

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2       4.4T  143G  4.0T   4% /
```

**Status:** PASS by orders of magnitude.

### 1.3 B2b replica psql

```
ls: cannot access '/home/jes/.pgpass': No such file or directory
Password for user replicator_role:
psql: error: connection to server at "localhost" (127.0.0.1), port 5432 failed: fe_sendauth: no password supplied
```

Docker inspect for context:
```
control-postgres-beast: running health=healthy
```

Listening sockets:
```
LISTEN 0 4096 127.0.0.1:5432  (postgres)
```

**Status:** FAIL. Postgres container is up + healthy + LAN-bound to localhost. No credential file for `replicator_role` on Beast filesystem. Atlas runtime needs to query the replica; needs credentials available somehow.

### 1.4 Garage health endpoint

Spec command (verbatim from handoff):
```
curl -s --max-time 4 http://localhost:3900/health
```

Result: empty response (S3 listener on :3900 rejected the path silently).

Diagnostic on the actual Garage layout:
```
LISTEN 0 4096    127.0.0.1:3903  (admin endpoint)
LISTEN 0 4096 192.168.1.152:3900  (S3 LAN endpoint)
```

Correct URL test:
```
curl -s http://127.0.0.1:3903/health
Garage is fully operational
Consult the full health check API endpoint at /v2/GetClusterHealth for more details
```

Docker inspect:
```
control-garage-beast: running health=healthy restarts=0
```

**Status:** Garage is HEALTHY. The spec's preflight URL was authored wrong. The S3 protocol port (`:3900`) is for S3 API calls (which return XML AccessDenied for unauthenticated `/health`). The plain HTTP admin port (`:3903`) serves the operational health endpoint.

**Spec fix:** preflight URL should be `http://127.0.0.1:3903/health` (or the v2 endpoint with bearer token if richer info is wanted).

### 1.5 Tailscale to Goliath

```
tailscale ping -c 2 sloan4 2>&1 | head -5
bash: line 18: tailscale: command not found

dpkg-query: no packages found matching tailscale

ip -br addr 2>&1 | head -5
lo               UNKNOWN        127.0.0.1/8 ::1/128
eno3             UP             192.168.1.152/24 metric 100 fd29:bbcc:2b89:4239:...
[no tailscale0 interface]
```

**Status:** FAIL. Beast not enrolled in Tailscale at all. Per device map (`AGENT-OS.md`), Goliath is reached via Tailscale `100.112.126.63 / sloan4`. For Beast to talk to Goliath via Tailscale, Beast needs the `tailscale` package + enrollment.

**Note:** Goliath also has a LAN IP `192.168.1.20` per the device map. If Atlas only needs Beast->Goliath connectivity, LAN may be sufficient and Tailscale may be over-spec for Cycle 1A. But the preflight literally tested Tailscale, so the gap is real per current spec.

### 1.6 mcp Python SDK

```
mcp (1.27.0)
Available versions: 1.27.0, 1.26.0, ... down to 0.9.1
```

**Status:** PASS. Latest 1.27.0 available on PyPI.

---

## 2. Substrate state at this pause

No state changes. Beast Docker daemon untouched.

```
control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

Bit-identical to H1 ship state. Bit-identical to Day 71 establishment. Holding.

---

## 3. Resolution paths -- one per failure

### 3.1 Python 3.11+ on Beast

**Path A:** Add deadsnakes PPA + `apt install python3.11 python3.11-venv python3.11-dev`. Standard pattern for jammy hosts needing newer Python. Adds a third-party PPA to Beast.

**Path B:** pyenv install. Per-user Python build. No system changes; venv tracks the user-build.

**Path C:** Build from source. Most controlled, most lift.

**Path D:** Relax Atlas spec to Python 3.10. Atlas v0.1 doesn't (yet) use any 3.11-only features that I've inspected. Could close the gap by amendment.

PD bias: **Path A** (deadsnakes). Standard, low-friction, scales to other Beast python tools, single apt source addition. Path D is also reasonable if 3.11 isn't strictly required by an Atlas dep.

### 3.2 Postgres replicator_role auth on Beast

**Path A:** Create `~/.pgpass` on Beast with `localhost:5432:alexandra_replica:replicator_role:<password>`, mode 600. Atlas runtime (and PD's preflight) auto-picks up.

**Path B:** Pass password via env-loaded `.env` file; Atlas reads it via dotenv pattern. Cleaner for application-layer auth, but doesn't help PD's preflight smoke test.

**Path C:** Use PostgreSQL peer auth or SCRAM with a different mechanism (e.g., generate a separate Atlas-specific role with limited replica-read perms, embed cert auth).

PD bias: **Path A** for preflight + dev convenience, OR **Path A + Path B** combined (Atlas reads via dotenv at runtime; .pgpass for psql convenience).

**Critical:** PD does NOT have the replicator_role password value. CEO or Paco needs to provide it (or instruct PD to fetch it from a known location like 1Password / control-plane secrets).

### 3.3 Garage health URL (spec author fix)

No path needed -- Garage IS healthy. Spec preflight URL just needs amendment from `http://localhost:3900/health` to `http://127.0.0.1:3903/health`. One-line spec fix when Paco rules.

### 3.4 Tailscale on Beast

**Path A:** Install Tailscale + enroll. Standard `curl -fsSL https://tailscale.com/install.sh | sh` then `sudo tailscale up`. Requires CEO interaction for tailnet auth.

**Path B:** Skip Tailscale; rely on LAN connectivity (`192.168.1.20` for Goliath). Atlas Cycle 1A and most Cycles are Beast-internal; the Tailscale check was forward-looking. Defer enrollment to v0.2 if not actually needed for Cycle 1+.

**Path C:** Hybrid -- preflight checks LAN reachability for now (not Tailscale), Tailscale enrollment deferred to whenever cycles actually need it.

PD bias: **Path B** unless Cycle 1A or Cycle 1+ has a hard Tailscale dependency I'm missing. Path A is fine if Atlas runtime needs Tailscale routes specifically.

---

## 4. Asks of Paco

1. **Python 3.11 path ruling.** A (deadsnakes) / B (pyenv) / C (build) / D (relax to 3.10) -- which?
2. **PG creds path ruling + password value.** Option A (.pgpass) approved? Provide replicator_role password value (CEO or Paco from secrets store; PD doesn't have it).
3. **Spec URL fix authorization.** Approve one-line amendment of preflight Garage URL from `:3900` to `:3903`. Whoever pushes spec amendment also amends `tasks/atlas_v0_1.md` with the correct URL for future cycle preflights.
4. **Tailscale path ruling.** A (install + enroll) / B (skip, use LAN) / C (hybrid)?

If the rulings would constitute an Atlas v0.1 spec amendment (Python version constraint changing, Tailscale being dropped from preflight), Paco's ruling formalizes it.

---

## 5. PD has NOT done

- Installed any Python or Tailscale packages on Beast
- Created any `.pgpass` file
- Modified the spec
- Touched the substrate (Docker / containers)
- Created `/home/jes/atlas/` or any project files
- Initialized any git repo

Beast filesystem state: untouched since H1 ship. Substrate state: bit-identical to H1 ship.

---

## 6. Cross-references

**Spec:** `tasks/atlas_v0_1.md` (commit `9176634`)
**Predecessor handoff:** `docs/handoff_paco_to_pd.md` (cleared per protocol)
**Standing rules invoked:**
- Spec or no action: PD did not improvise any fixes for the 3 real preflight failures
- 5-guardrail rule: this is OUTSIDE its domain (substantive operational decisions about runtime dependencies, not mechanical syntax corrections)
- B2b + Garage anchor preservation: holding
- Bidirectional one-liner format spec on handoffs: this ESC's paired handoff follows it

---

## 7. Status

**AWAITING PACO RULING on:**
1. Python 3.11+ install path (A/B/C/D)
2. Postgres creds path + password value for replicator_role
3. Garage URL spec fix authorization
4. Tailscale path (A/B/C)

PD paused at Cycle 1A Step 1 preflight FAIL. Substrate undisturbed. No further changes pending Paco's response.

-- PD
