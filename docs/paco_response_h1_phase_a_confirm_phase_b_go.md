# Paco -> PD response -- H1 Phase A CONFIRMED, Phase B GO

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-28 (Day 73)
**Spec:** `tasks/H1_observability.md` (md5 `fc3f55b33bd2bf31d23c8acec2188049`)
**Predecessor:** `docs/paco_review_h1_phase_a_baseline.md`
**Status:** **AUTHORIZED** -- proceed to Phase B (docker compose v2 plugin + docker group)

---

## TL;DR

Phase A verified clean by independent Paco cross-check from a fresh shell on SlimJim + Beast. **All 3 acceptance gates PASS** byte-for-byte against PD's review:

- Gate 1: 8 captures + md5_manifest.txt present, all 8 files verify `OK` via `md5sum -c md5_manifest.txt`
- Gate 2: Docker 28.2.2 (>= 24)
- Gate 3: 204 GB free disk, 22 GB free RAM (29 GB available column)

**B2b nanosecond invariant continues holding:** `control-postgres-beast` `StartedAt 2026-04-27T00:13:57.800746541Z` bit-identical pre and post Phase A. Garage anchor also still holding at `2026-04-27T05:39:58.168067641Z`. Both containers healthy, RestartCount=0.

Observations 5.1-5.3 acknowledged with refinements (see section 3).

---

## 1. Independent Phase A verification (Paco's side)

```
Gate 1 (captures + md5s):  /tmp/H1_phase_a_captures/ has 8 .txt + md5_manifest.txt;
                            md5sum -c md5_manifest.txt -> all 8 files OK
Gate 2 (docker version):    Docker version 28.2.2, build 28.2.2-0ubuntu1~24.04.1
Gate 3 (disk + RAM):        Disk 204G avail / Mem 22Gi free (29Gi available)

B2b anchor (Beast):         control-postgres-beast 2026-04-27T00:13:57.800746541Z
                            healthy, RestartCount=0 -- BIT-IDENTICAL
Garage anchor (Beast):      control-garage-beast 2026-04-27T05:39:58.168067641Z
                            healthy, RestartCount=0 -- BIT-IDENTICAL
```

All 3 gates PASS. Substrate untouched.

---

## 2. Acknowledgments

- **Pre-Phase-A cleanup acknowledgment table (PD section 1):** correct on every line.
- **Recalibrated 3-gate scorecard (was 5 in spec):** ratified. Spec section A.4 supersedes-text noted; H1 spec body doesn't need amendment for this -- the recalibration is captured in PD review section 1 and this paco_response.
- **mosquitto-snap residual systemd unit `not-found inactive dead`:** harmless, no unit file, will not interfere with apt mosquitto install in Phase C.
- **No new MCP/service restart this phase** -- `feedback_mcp_deferred_restart_verify.md` rule not triggered.

---

## 3. Rulings on PD's 4 asks

### Ask 1 -- Phase A 3/3 PASS confirmation

**RULING:** CONFIRMED. All 3 gates PASS. Captured md5 manifest verified live.

### Ask 2 -- Phase B GO authorization

**RULING:** AUTHORIZED. Proceed per spec section 6 (`tasks/H1_observability.md` lines 129-148). Phase B scope:

1. `sudo apt update && sudo apt install -y docker-compose-plugin`
2. Verify `docker compose version` returns v2.x
3. `sudo usermod -aG docker jes` (PD review noted jes is already in docker group based on docker.txt finding -- re-verify; if already a member, this step is a no-op + document)
4. New shell to refresh group membership; verify `docker ps` works without sudo
5. No service-affecting changes elsewhere (B2b + Garage anchors must remain bit-identical)

**Phase B 4-gate acceptance:**
1. `docker compose version` returns Docker Compose v2.x
2. `id jes` shows `docker` group
3. `docker ps` works without sudo (refreshed shell)
4. B2b + Garage nanosecond anchors preserved

### Ask 3 -- UFW [5] 1883/tcp pre-existing rule strategy

**RULING:** **SKIP the add in Phase C** (PD's recommendation accepted). Reasoning:

- Pre-existing rule is functionally identical to spec mandate (`192.168.1.0/24 -> 1883/tcp ALLOW`)
- Deleting + re-adding creates a transient gap with zero behavioral benefit
- Document in Phase C review: rule [5] verified pre-existing from Day 67 IoT pre-staging, no action required, treat as continuation
- Add a Phase C-specific guard: `sudo ufw status | grep -qE '^\[[ 0-9]+\] 1883/tcp.*ALLOW.*192\.168\.1\.0/24' || sudo ufw allow from 192.168.1.0/24 to any port 1883 proto tcp comment 'H1 Phase C: Mosquitto LAN'`
  This makes Phase C idempotent regardless of pre-existing state.

For port 1884 (LAN authed listener), no pre-existing rule -- normal `ufw allow` applies.

### Ask 4 -- Disposition of observations 5.1 + 5.3 (mariadbd + UFW 80/443)

**RULING:** Bank as live discoveries with refinements + plan. Both are pre-existing scaffolding debt, not H1 blockers. **Do NOT clean up in Phase A or Phase B** -- separate side-action AFTER Phase B Lands. Specifically:

**5.1 mariadbd refined finding:** Paco independent live check confirmed the engine is running but contains ONLY the 4 default schemas (`information_schema`, `mysql`, `performance_schema`, `sys`). NO application data. PID 1738 has been running 4+ days (since `2026-04-23 10:34:07 MDT`). Likely leftover from Day-67-era scaffolding (consistent with `job_pipeline.py`, `agent_bus.py`, `build_index.py`, `query_ai.py` artifacts in `/home/jes`).

**Plan:** After Phase B closes, run a 30-second side-action:
```bash
# Confirm zero app data first
sudo mysql -e 'SHOW DATABASES;'  # expect: only the 4 defaults
# If only defaults, disable + stop
sudo systemctl disable --now mariadb
```
This frees ~9 systemd-tracked tasks + a small RAM footprint and removes a port-3306 surface (even though loopback-only). If CEO wants to keep mariadb for a future scaffolding restart, override with explicit instruction.

**5.3 UFW 80/443 dormant rules:** same pattern as 8080/8084 we cleaned earlier. No HTTP listener on either port. Plan: same side-action timing as 5.1, in same commit:
```bash
sudo ufw delete allow 80/tcp
sudo ufw delete allow 443/tcp
# UFW count drops 5 -> 3
```
If CEO has imminent plans to re-deploy something on 80/443 (a reverse proxy for example), override.

**Banking these as a single Phase B-adjacent side-task** rather than scope creep into Phase A. Keeps Phase A clean (already shipped) and gives CEO a clear veto opportunity before mariadb is disabled.

---

## 4. Phase B directive

Follow `tasks/H1_observability.md` section 6 verbatim. Add the following:

### 4.1 Pre-flight idempotency (do this first)

```bash
echo '=== Pre-state ==='
docker --version
docker compose version 2>&1 | head -2 || echo 'compose plugin NOT installed'
id jes | grep -oE 'docker' && echo 'jes already in docker group' || echo 'jes NOT in docker group'
groups jes | grep -oE 'docker' && echo 'group active in shell' || echo 'group NOT active in shell'
```

This tells us up-front whether either action is a no-op.

### 4.2 Install + group

```bash
sudo apt update
sudo apt install -y docker-compose-plugin
docker compose version  # expect: Docker Compose version v2.x
```

If `id jes` already shows `docker`, skip the usermod + document. If not:
```bash
sudo usermod -aG docker jes
```

### 4.3 Refresh shell + verify

Group membership doesn't refresh in existing shells. Two options:
```bash
# Option A: new SSH session
logout
ssh slimjim
# Option B: re-execute shell with new groups
exec sg docker -c bash
# Verify
groups | grep -oE 'docker'
docker ps
```

Use whichever PD prefers. PD review should document which path was used.

### 4.4 Anchor preservation check

```bash
ssh beast "docker inspect control-postgres-beast control-garage-beast --format '{{.Name}} StartedAt={{.State.StartedAt}} health={{.State.Health.Status}} restarts={{.RestartCount}}'"
```

Must show:
- `control-postgres-beast 2026-04-27T00:13:57.800746541Z healthy 0`
- `control-garage-beast 2026-04-27T05:39:58.168067641Z healthy 0`

### 4.5 Phase B 4-gate acceptance

1. `docker compose version` returns Docker Compose v2.x
2. `id jes` shows `docker` group present
3. `docker ps` works without sudo (in refreshed shell)
4. Both Beast nanosecond anchors bit-identical pre/post Phase B

---

## 5. After Phase B closes

PD writes `paco_review_h1_phase_b_compose_plugin.md` to `/home/jes/control-plane/docs/`. Surface it. Paco confirms gates + writes `paco_response_h1_phase_b_*_phase_c_go.md`.

Then the **side-task** for observations 5.1 + 5.3:
```bash
sudo mysql -e 'SHOW DATABASES;'  # confirm only 4 defaults
sudo systemctl disable --now mariadb
sudo ufw delete allow 80/tcp
sudo ufw delete allow 443/tcp
sudo ufw status numbered  # expect 3 rules now (22, 19999, 1883)
```

This runs as a separate paco_review_h1_side_task_*.md, NOT folded into Phase B's review. Keeps the audit trail clean.

Then Phase C (mosquitto 2.x dual-listener install + close Day 67 YELLOW #5).

---

## 6. Standing rules in effect

- Per-step review docs in `/home/jes/control-plane/docs/` (`feedback_paco_review_doc_per_step.md`)
- B2b + Garage nanosecond anchor preservation -- non-negotiable invariant for the rest of H1
- Spec or no action -- Phase B follows section 6 with the idempotency pre-flight added by this directive (refinement, not deviation)
- Secrets discipline -- not triggered this phase (no credentials touched)
- Canon location -- this paco_response committed to canon by PD as part of the Phase B-related git operations

---

## 7. Open expectations

PD's next deliverables (in order):
1. `paco_review_h1_phase_b_compose_plugin.md` -- Phase B execution + 4 gate scorecard
2. (after my confirmation) `paco_review_h1_side_task_mariadb_ufw_cleanup.md` -- side-task evidence
3. (after my confirmation) `paco_review_h1_phase_c_mosquitto.md` -- Phase C execution

B2b + Garage anchors must continue holding. Each PD review must include them as evidence.

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_a_confirm_phase_b_go.md`

-- Paco
