# Paco -> PD ruling -- Atlas v0.1 Cycle 1A preflight ESC (4 rulings + P6 #20 banked)

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-30 (Day 75)
**Predecessor:** `docs/paco_request_atlas_v0_1_cycle_1a_preflight_fail.md`
**Status:** **APPROVED** -- Path A (Python deadsnakes) / Path A (PG creds .pgpass) / Garage URL spec fix / Path B (Tailscale skip) -- P6 #20 banked

---

## TL;DR

Four rulings + Paco self-acknowledgment + P6 #20 banked:

1. **Python -> Path A APPROVED.** deadsnakes PPA install of python3.11. Path D (relax to 3.10) tempting but rejected: blocks PEP 695 generics + asyncio.TaskGroup + except* patterns we'll likely use across 4 cycles.
2. **PG creds -> Path A APPROVED + corrected credentials.** `~/.pgpass` on Beast with the **actual** connection string. **CRITICAL CORRECTION:** the spec named fictional `replicator_role` + `alexandra_replica` -- the real B2b setup is `user=admin / dbname=controlplane / password=adminpass` (verified live this turn via `pg_subscription`). Spec amendment lands in Phase G close-out.
3. **Garage URL spec fix APPROVED.** `localhost:3900/health` -> `127.0.0.1:3903/health`. PD's catch correct.
4. **Tailscale -> Path B APPROVED.** Skip Tailscale; use LAN `192.168.1.20` for Goliath. Both nodes are on the same LAN; Tailscale is over-spec for v0.1. Defer enrollment to v0.2 if cross-network use case emerges.

**P6 #20 banked:** spec content referencing actual deployed-state names (database names, role names, URLs, ports, hostnames) must be verified against running infrastructure at directive-author time, not transcribed from memory. This is the third class of Paco-side spec error in the H1+Atlas track (P6 #17 env var conventions, P6 #19 compose mode-compatibility, now #20 deployed-state-name verification).

---

## 0. Paco-side acknowledgment (third spec error in H1+Atlas track)

This is my third spec-authoring failure caught by PD's discipline cycle in 24-72 hours:

- **P6 #17** (yesterday Phase E): Grafana env var `_FILE` vs `__FILE` -- transcribed from memory
- **P6 #19** (yesterday Phase G): compose long-syntax `uid/gid/mode` swarm-only -- assumed without verifying mode-compat
- **P6 #20** (today Cycle 1A preflight): Atlas spec named fictional database `alexandra_replica` + role `replicator_role` + wrong Garage URL `:3900` -- transcribed from memory + reasonable-sounding-names rather than verifying actual B2b deployed state

**Pattern:** I'm authoring directive content from a mental model of "what the system probably looks like" rather than verifying against running infrastructure at directive-author time. Each instance is caught by PD's runtime discipline at the right moment, but the recurring pattern is a Paco-side process gap.

**Going forward:** for every Atlas cycle directive I author, I will verify deployed-state names (DB / role / bucket / port / URL / hostname) against running infrastructure BEFORE writing the directive, NOT after PD's preflight catches the gap. This adds ~5 minutes of verification per phase and saves N escalation roundtrips. The pattern is self-imposed; banking as P6 #20 makes it durable.

PD's instinct to flag rather than improvise was textbook. The 5-guardrail rule's effectiveness is measured at this typo / fictional-name level catch, not just at the major-incident level.

---

## 1. Python ruling -- Path A APPROVED (deadsnakes PPA + python3.11)

Deadsnakes is the standard, well-trusted PPA for newer Python on jammy hosts. Adds one apt source. Pattern reusable for any future Beast Python tooling. Stable across systemd-managed services (vs pyenv shims which can fragment across kernel updates).

### 1.1 Why not Path D (relax to 3.10)

Tempting in isolation but constrains 4 future cycles. Specifically:
- PEP 695 generic syntax (3.12+) for cleaner Pydantic v2 + protocol typing
- `asyncio.TaskGroup` (3.11+) for cleaner concurrent task handling in Atlas main loop
- `except*` exception groups (3.11+) for cleaner error aggregation in tool execution
- Several `mcp` Python SDK patterns assume 3.11+ idioms

The cost of staying on 3.10 compounds. We'd write less idiomatic code and fight Python version gates throughout.

### 1.2 Procedure (PD self-auth this ruling)

```bash
# Add deadsnakes PPA + install python3.11 packages
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils

# Verify
python3.11 --version  # expect: Python 3.11.<latest>
python3.11 -m venv --help | head -3  # expect: usage banner (venv module loadable)
```

No system-default Python change. Beast's `python3` -> 3.10 stays the same. Atlas just uses `python3.11` explicitly via the venv.

### 1.3 Spec amendment

No amendment needed. Spec already says ">= 3.11"; this just fulfills it.

---

## 2. PG creds ruling -- Path A APPROVED + corrected credentials

### 2.1 Critical correction: actual B2b connection string

Verified live this turn against running Beast Postgres + `pg_subscription` table:

```
Database:    controlplane          (NOT alexandra_replica)
User:        admin                  (NOT replicator_role)
Password:    adminpass              (default; matches pg_subscription evidence)
Host:        127.0.0.1
Port:        5432
Subscription: controlplane_sub      (CK -> Beast logical replication)
```

The Atlas spec's `replicator_role` + `alexandra_replica` were fictional names from my memory model. They don't exist on Beast. Real names captured above.

### 2.2 Procedure (PD self-auth this ruling)

```bash
# Create .pgpass on Beast for jes user
cat > ~/.pgpass <<'PGPASS_EOF'
127.0.0.1:5432:controlplane:admin:adminpass
localhost:5432:controlplane:admin:adminpass
PGPASS_EOF
chmod 600 ~/.pgpass
ls -la ~/.pgpass  # expect: -rw------- 1 jes jes ... .pgpass

# Verify libpq picks it up
psql -h localhost -U admin -d controlplane -c 'SELECT 1;' 2>&1 | head -5
# expect: 1 row returned without password prompt
```

### 2.3 Spec amendment scope

`tasks/atlas_v0_1.md` Cycle 1A preflight + Cycle 1B Postgres connection layer + Section 7 schema text all need amendment to reference real names:

```
Replica access: read-only from `controlplane` database via `admin` user (same admin uses logical replication subscription `controlplane_sub` per B2b ship state). [NOT alexandra_replica / replicator_role]

atlas-owned schema lives in the same `controlplane` database under namespace `atlas` (not a separate database).
```

Lands in Cycle 1A close-out commit alongside the Garage URL fix.

### 2.4 Security / discipline note

`adminpass` is a default password from B2b establishment. Per H1's standing rule on secrets discipline, this is a known P5 carryover for v0.2 hardening: rotate to a strong password + per-role separation (Atlas-specific role with limited scope vs admin-everything). Banking as P5:

> **P5 carryover banked Day 75 Atlas Cycle 1A**: rotate B2b Postgres `admin` password from default `adminpass` to strong value; create Atlas-specific role with limited scope (read on B2b replicated tables + write on `atlas` namespace only); update `.pgpass` + Atlas runtime config; update CK primary's pg_hba.conf if subscription auth needs the new password. Defer to v0.2 hardening pass with the other 6 P5 items.

This lands in v0.2 queue, not Cycle 1A scope.

---

## 3. Garage URL spec fix APPROVED

PD's catch correct. Garage on Beast has two listeners:
- `:3900` -- S3 protocol on LAN (rejects unauthenticated `/health` with XML AccessDenied)
- `:3903` -- admin/health on localhost (returns text "Garage is fully operational")

Spec amendment (one-line):

```
# Cycle 1A preflight, change:
echo '=== Garage S3 reachable ===' && curl -s --max-time 4 http://localhost:3900/health
# To:
echo '=== Garage health endpoint ===' && curl -s --max-time 4 http://127.0.0.1:3903/health
# Expected: "Garage is fully operational"
```

Lands in Cycle 1A close-out commit.

---

## 4. Tailscale ruling -- Path B APPROVED (skip, use LAN)

PD's bias correct. Both Beast (`192.168.1.152`) and Goliath (`192.168.1.20`) are on the same LAN. Tailscale is over-spec for Atlas v0.1 since:
- Cycle 1D inference RPC: Beast -> `http://192.168.1.20:11434` (Ollama) works LAN-only
- Cycle 2-4: all stay on-LAN for Beast-Goliath communication
- Cross-network use cases (e.g., Atlas reachable from outside the homelab) are v0.2+ scope

Defer Tailscale enrollment on Beast to v0.2 if a cross-network use case emerges.

### 4.1 Spec amendment

Replace Tailscale preflight check with LAN reachability check:

```
# Cycle 1A preflight, change:
echo '=== Goliath Tailscale reachable ===' && tailscale ping -c 2 sloan4 2>&1 | head -5
# To:
echo '=== Goliath LAN reachable ===' && curl -s --max-time 4 http://192.168.1.20:11434/api/tags 2>&1 | head -3
# Expected: JSON listing of Ollama models on Goliath
```

Verifies the actual capability Atlas needs (Ollama HTTP reachability), not the underlying network path.

Lands in Cycle 1A close-out commit.

### 4.2 P5 carryover banked

> **P5 carryover banked Day 75**: Beast Tailscale enrollment if cross-network reachability becomes needed in v0.2+. Defer until use case surfaces.

---

## 5. P6 #20 BANKED (new methodology lesson)

### 5.1 Banked rule

> **P6 #20 -- Spec content referencing actual deployed-state names (database names, role names, bucket names, URLs, ports, hostnames, file paths) must be verified against running infrastructure at directive-author time, not transcribed from memory or reasonable-sounding-names.**
>
> Required preflight pattern when authoring spec directives:
> - For database/role names: query running Postgres via `\dn`, `\du`, `pg_subscription`, `pg_database` to capture actual names
> - For URLs/ports: read the actual compose.yaml + `ss -tlnp` on the host to capture the real listener bindings (admin port vs API port distinction matters)
> - For bucket/object names: query the actual S3 service or storage backend
> - For Tailscale names + IPs: verify against `tailscale status` on the actual host
> - For file paths and credential locations: verify against the actual filesystem state
>
> Cost at directive-author time: ~5 minutes of verification per phase. Cost at deploy-time when fictional names ship: minimum one paco_request roundtrip per fictional name; in worst case, multiple cascading ESCs as PD discovers more divergences.
>
> Banked from Atlas v0.1 Cycle 1A preflight Day 75: spec authored `replicator_role` + `alexandra_replica` + Garage `:3900/health` -- all three were memory-model fictional. Real names captured live from `pg_subscription` and `ss -tlnp` during ESC ruling.
>
> Pattern context: this is the third spec-authoring class of Paco-side error in the H1+Atlas track (P6 #17 env var conventions, P6 #19 compose mode-compatibility, P6 #20 deployed-state-name verification). All three share the underlying cause: directive content authored from a mental model rather than from verified runtime state. P6 #20 bank formalizes the discipline against this class.

### 5.2 P6 lessons banked count

**20** (was 19).

### 5.3 Companion Paco-side process commitment

For every Atlas cycle directive I author from this point forward, I will:
1. SSH to relevant nodes via homelab_ssh_run + verify actual state before writing directive
2. Reference real names (verified live) in directive text
3. Quote the verification command in the spec for posterity ("verified live YYYY-MM-DD via `<command>`")
4. Cross-reference P6 #20 in the spec section that uses verified names

This adds ~5 minutes per directive but eliminates the recurring spec-author error class.

---

## 6. Order of operations from here

```
1. PD: install python3.11 via deadsnakes (Path A)
2. PD: create ~/.pgpass on Beast with corrected credentials (admin / controlplane)
3. PD: re-run preflight Steps 1.1 + 1.3 + 1.4 + 1.5 with corrected URLs/creds
   - Python: python3.11 --version returns 3.11.x
   - psql with .pgpass: SELECT 1 returns 1 without password prompt
   - Garage: curl http://127.0.0.1:3903/health returns "Garage is fully operational"
   - Goliath LAN: curl http://192.168.1.20:11434/api/tags returns JSON model list
   - mcp Python SDK: 1.27.0 confirmed (already verified)
4. PD: resume Cycle 1A from Step 2 (project scaffold) -- scaffold uses python3.11 explicitly
5. PD: continues Steps 3 (pip install) / 4 (git push) / 5 (Beast anchor)
6. PD: writes paco_review_atlas_v0_1_cycle_1a_skeleton.md including:
   - 5-gate scorecard with all gates PASS
   - Preflight failures + Path resolutions documented per guardrail 4
   - Real B2b credentials referenced (admin / controlplane), NOT fictional names
   - Garage URL corrected
   - Tailscale path B applied
   - Beast anchor pre/post bit-identical
7. PD: Cycle 1A close-out commit folds:
   - paco_review_atlas_v0_1_cycle_1a_skeleton.md
   - tasks/atlas_v0_1.md amendments:
     - Cycle 1A preflight: real DB/role names + corrected Garage URL + Tailscale -> LAN check
     - Cycle 1B Postgres connection layer text: replace fictional names with real ones
     - P6 lessons section update: 19 -> 20 (add #20 deployed-state-name verification)
   - SESSION.md Day 75 Cycle 1A close section append
   - paco_session_anchor.md (Cycle 1A CLOSED, Cycle 1B NEXT, P6 = 20)
   - CHECKLIST.md audit entry
8. PD: writes notification to handoff_pd_to_paco.md per bidirectional format spec
9. CEO: "Paco, PD finished, check handoff."
```

## 7. Standing rules in effect

- 5-guardrail rule + carve-outs (PD's no-improvise was correct discipline)
- Compose-down ESC pre-auth (not applicable this turn -- no service stops)
- B2b + Garage anchor preservation (still holding bit-identical 19+ phases)
- Per-step review docs in `/home/jes/control-plane/docs/`
- Handoff protocol with bidirectional one-liner format
- Phase closure pattern (literal-PASS + spirit-partial)
- Spec or no action: 4 paths explicitly authorized this turn
- Secrets discipline: adminpass is a known weak default; P5 carryover banked for v0.2 hardening
- P6 lessons banked: 20 (added #20 this turn)

## 8. Acknowledgments

### 8.1 PD's discipline

Three decisions textbook:
1. Surfaced 4 root causes cleanly (3 real + 1 spec-author error) with full evidence
2. Did NOT improvise any fixes -- substrate untouched, no scaffold work, no `~/.pgpass` creation, no PPA add
3. Asked the meta-question implicitly by showing me my own spec-author error -- forced banking of P6 #20 rather than one-off ruling

### 8.2 Handoff protocol once again validated

Fourth real ESC through the convention. CEO sent one-line trigger; Paco read everything from disk; ruling dispatched via handoff_paco_to_pd.md. Loop closed cleanly. Pattern stable across 4 escalations now.

---

**File location:** `/home/jes/control-plane/docs/paco_response_atlas_v0_1_cycle_1a_preflight_resolved.md`

-- Paco
