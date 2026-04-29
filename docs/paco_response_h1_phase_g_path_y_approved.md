# Paco -> PD ruling -- H1 Phase G ESC #2 (Path Y approved + P6 #18 broadened)

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-29 (Day 74)
**Predecessor:** `docs/paco_request_h1_phase_g_secret_perms.md` (PD ESC #2 -- secret file scope)
**Status:** **APPROVED** -- Path Y (compose long-syntax) -- P6 #18 broadened to all bind-mount classes -- mixed-ownership subdirs banked as P5

---

## TL;DR

Four rulings on PD's four asks:

1. **Path Y APPROVED** (compose long-syntax secret). Operator ergonomics + B-substrate pattern consistency + declarative documentation all favor Y over X.
2. **P6 #18 BROADENED** to cover all bind-mount-UID-alignment cases (volumes + secrets + configs), with default-approach guidance per mount type. Count stays at 18; the rule text expands.
3. **Phase G close-out scope confirmed**: compose.yaml change documented per guardrail 4 (pre/post md5 + explicit diff + docker compose config re-pass), spec amendment lands at Phase E.1 (chown step from ESC #1) + Section 9 E.2 (long-syntax pattern from ESC #2), all in single Phase G close-out commit.
4. **Mixed-ownership grafana-data subdirs banked as P5** (not Phase G chmod step). Decisive test is whether grafana startup succeeds with Path Y; pre-fixing what we don't know is broken expands scope unnecessarily.

---

## 1. Path Y ruling -- APPROVED

PD's bias correct. Three reasons over Path X:

### 1.1 Operator ergonomics is real

This isn't a write-once secret. CEO will rotate the Grafana admin password at some point -- quarterly hardening pass, suspected compromise, routine refresh. Path X forces `sudo` on every rotation; Path Y lets CEO `vi` the file with normal credentials. The cumulative cost of Path X is non-trivial across the system's lifetime.

### 1.2 Pattern consistency for B-substrate

Postgres admin password (B2a/B2b), Garage S3 keys (B1), future Atlas secrets -- all will be docker secrets at some point. Setting the precedent now with long-syntax + explicit `uid`/`gid`/`mode` means every future secret declaration follows the same template. Path X scales worse: every new secret needs its own host-side chown convention.

### 1.3 Declarative documentation

Path Y makes the runtime mapping intent visible in `compose.yaml` itself. Reading the file tells you "this secret is meant for UID 472 mode 0400." Path X leaves that intent implicit in host filesystem state -- you'd have to `stat` to discover it.

### 1.4 Trade-off

One compose.yaml edit + guardrail 4 documentation in close-out review. Small one-time cost.

## 2. P6 #18 broadened scope

### 2.1 Revised rule text (replaces Phase G ESC #1 banking)

> **P6 #18 -- All bind-mounts (volumes AND secrets) that inherit host filesystem ownership require UID alignment between host owner and container default UID before first compose-up.**
>
> This applies to:
> - **`volumes:` directives** (data dirs, config dirs, plugin dirs) -- resolution: chown host directory to container's default UID, OR specify `user:` directive in compose.yaml
> - **`secrets:` short-syntax directives** (file mode inherited from host) -- resolution: switch to long-syntax with explicit `uid`/`gid`/`mode` fields, OR chown host file to container's default UID
> - **`configs:` short-syntax directives** (same mechanism) -- same resolution pattern
>
> **Default approach by mount type:**
> - **Data directories** -> chown host dir to image-default UID (host owner is just the bind point, container fully owns the data)
> - **Secret/config files** -> long-syntax with explicit `uid`/`gid`/`mode` (host file stays human-editable for credential rotation; compose declares container-side mapping intent)
>
> Required spec preflight: capture image-default UID at spec-author time alongside every bind-mount declaration. For unfamiliar images: `docker run --rm --entrypoint id <image>`.
>
> Common UIDs banked: prom/prometheus 65534, grafana/grafana 472, postgres 999, dxflrs/garage 0, nginx 101, redis 999.
>
> Banked from H1 Phase G ESC #1+#2 Day 74. ESC #1 surfaced data-dir scope (Phase E created prom-data + grafana-data chmod 700 jes:jes; Prometheus runs as 65534, Grafana as 472). ESC #2 surfaced secret-file scope (Phase E created grafana-admin.pw 600 jes:jes; Grafana container UID 472 cannot read host-UID-1000 file via short-syntax bind-mount). Fix at directive-write-time is per-mount UID declaration; fix at deploy-time costs N escalation roundtrips for N mounts.

### 2.2 P6 lessons banked count

**18** (unchanged). The broadening updates #18's text scope, not the count. ESC #2 confirmed the broader pattern; not a separate lesson.

### 2.3 Spec amendment scope

`tasks/H1_observability.md` gets two amendments in Phase G close-out:

**Phase E.1 (directory creation)**: append chown step per ESC #1 ruling (already authorized, lands in Phase G close-out)

```bash
sudo chown -R 65534:65534 /home/jes/observability/prom-data
sudo chown -R 472:472 /home/jes/observability/grafana-data
```

**Section 9 E.2 (compose.yaml secrets block)**: replace short-syntax with long-syntax

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

Both cross-reference broadened P6 #18.

## 3. Phase G close-out review scope confirmation

Path Y's compose.yaml edit is broader than Path A's directive (which was filesystem-only). Document delta in review's deviations section per guardrail 4. Three things land in the close-out review:

1. **Path Y compose.yaml edit evidence**:
   - Pre/post md5 (current `db89319cad27c091ab1675f7035d7aa3` -> new value captured post-edit)
   - Explicit diff showing short-syntax -> long-syntax block (4 new lines: `source` / `target` / `uid` / `gid` / `mode`)
   - `docker compose config` re-pass post-edit, with grep confirmation that long-syntax resolved correctly (mode 0400 expressed as 256 decimal in resolved output)

2. **Spec amendments to `tasks/H1_observability.md`**:
   - Phase E.1 chown step (ESC #1)
   - Section 9 E.2 secrets long-syntax block (ESC #2)
   - Both cross-reference P6 #18

3. **Single Phase G close-out commit folds**:
   - paco_review_h1_phase_g_compose_up.md
   - tasks/H1_observability.md amendments (E.1 + 9 E.2)
   - SESSION.md Day 74 Phase G close section
   - paco_session_anchor.md (Phase G CLOSED, Phase H NEXT, P6 = 18 broadened)
   - CHECKLIST.md audit entry
   - observability/ files on SlimJim disk modified (compose.yaml new md5, grafana-admin.pw unchanged) but NOT in commit -- per standing rule, observability/ is operational config, lives on SlimJim filesystem only

## 4. Mixed-ownership grafana-data subdirs -- P5 carryover

### 4.1 Why P5 not Phase G chmod

PD observed `dashboards/` as `root:root` and `plugins/` as `472:root` from grafana's failed-start attempts. Three reasons to bank as P5, not fix in Phase G:

**1. Transient artifacts of failed-start state.** Once Path Y is applied and grafana starts cleanly, grafana itself will create + manage the directories it needs at UID 472. Current mixed ownership is residue from incomplete startup, not steady-state.

**2. Out of scope for ESC #2.** The escalation is "secret file unreadable." Adding chmod step for observed-side-effect-from-failed-attempt expands scope and complicates Phase G review. Tight scope per ESC.

**3. Likely self-resolves.** Grafana's entrypoint runs as root momentarily before dropping to UID 472. It creates `dashboards/` and `plugins/` during root phase. After Path Y allows successful startup, observe whether grafana actually needs to write to them; if it does and fails, fresh ESC. If startup completes cleanly, mixed ownership is benign cosmetic.

### 4.2 P5 banking

> **P5 carryover banked Day 74 Phase G ESC #2**: Investigate grafana-data subdir ownership post-Path-Y stable startup. Phase G ESC #2 captured `grafana-data/dashboards` as `root:root` and `grafana-data/plugins` as `472:root` from grafana's failed-start attempts (entrypoint runs as root briefly, creates dirs, drops to UID 472). If grafana writes successfully despite the mixed ownership, accept as upstream behavior + document. If startup or runtime operations fail on these, surface as fresh ESC. Defer to v0.2 hardening or post-Phase-H stable state.

Don't pre-fix what we don't know is broken. Decisive test is whether grafana startup succeeds with Path Y applied.

## 5. Path Y execution

### 5.1 Procedure (PD self-auth under this ruling)

```bash
cd /home/jes/observability

# Capture pre-state
md5sum compose.yaml  # current: db89319cad27c091ab1675f7035d7aa3
cp compose.yaml /tmp/compose.yaml.pre-pathy-bak

# Apply long-syntax via direct file edit (sed not safe for multi-line YAML structure changes)
# Replace this block in compose.yaml under services.grafana:
#     secrets:
#       - grafana_admin_pw
# With:
#     secrets:
#       - source: grafana_admin_pw
#         target: grafana_admin_pw
#         uid: "472"
#         gid: "472"
#         mode: 0400

# Validate post-edit
docker compose config > /tmp/compose.config.post-pathy.yaml 2>&1
echo "compose config exit=$?"  # expect 0
grep -B1 -A5 'grafana_admin_pw' /tmp/compose.config.post-pathy.yaml | head -30
# expect long-syntax block resolved with uid: '472', gid: '472', mode: 256 (compose normalizes 0400 to decimal)

# Capture post-state
md5sum compose.yaml  # should differ from pre

# Re-launch stack
docker compose up -d

# Healthcheck poll cap 120s (G.3 pattern)
for i in $(seq 1 24); do
  PROM=$(docker inspect obs-prometheus --format '{{.State.Health.Status}}' 2>/dev/null || echo missing)
  GRAF=$(docker inspect obs-grafana --format '{{.State.Health.Status}}' 2>/dev/null || echo missing)
  echo "poll $i: prometheus=$PROM grafana=$GRAF"
  [ "$PROM" = healthy ] && [ "$GRAF" = healthy ] && break
  sleep 5
done

docker compose ps
docker inspect obs-prometheus obs-grafana --format '{{.Name}} StartedAt={{.State.StartedAt}} health={{.State.Health.Status}} restarts={{.RestartCount}}'
```

Expected: both containers Up healthy with RestartCount=0.

If grafana still fails, STOP and file paco_request with new symptom. Do NOT improvise.

### 5.2 Then resume Phase G

Continue from G.4 (scrape target verification) through G.6 (Beast anchor post-capture) per the original handoff. Bridge NAT decision (G.5) still pending runtime check.

## 6. Order of operations from here

```
1. PD: confirm stack down (docker compose ps -a shows 0 running)
2. PD: cp compose.yaml /tmp/compose.yaml.pre-pathy-bak (rollback artifact)
3. PD: capture pre md5 of compose.yaml
4. PD: edit compose.yaml grafana service secrets block (short-syntax -> long-syntax)
5. PD: docker compose config validates (exit 0)
6. PD: capture post md5 of compose.yaml
7. PD: docker compose up -d
8. PD: healthcheck poll (cap 120s) -- expect both healthy
9. PD: resume G.4 (scrape target verification)
10. PD: G.5 bridge NAT decision (Path 1 if SlimJim self-scrape fails)
11. PD: G.6 Beast anchor post-capture (must be bit-identical)
12. PD: write paco_review_h1_phase_g_compose_up.md including:
    - Path A chown evidence (ESC #1 resolution, prior turn)
    - Path Y compose.yaml edit evidence (ESC #2 resolution, this turn)
    - 5-gate scorecard
    - Container start times + health
    - Prometheus targets table
    - Bridge NAT decision + evidence
    - Beast anchor pre/post diff
    - P6 #18 broadened banking + spec amendment cross-references
    - P5 carryover banked (mixed-ownership grafana-data subdirs)
13. PD: Phase G close-out commit (single git push):
    - paco_review_h1_phase_g_compose_up.md
    - tasks/H1_observability.md amendments (E.1 chown + 9 E.2 long-syntax)
    - SESSION.md Day 74 Phase G close section
    - paco_session_anchor.md (Phase G CLOSED, Phase H NEXT, P6 = 18 broadened)
    - CHECKLIST.md audit entry
14. PD: write notification to /home/jes/control-plane/docs/handoff_pd_to_paco.md
15. PD: git commit + push
16. CEO triggers Paco with one-line: "Paco, PD finished, check handoff."
```

## 7. Standing rules in effect

- 5-guardrail rule + carve-out (this ESC correctly routed -- substantive secret-mapping decision, not mechanical)
- B2b + Garage nanosecond anchor preservation (still holding through both Phase G ESCs)
- Per-step review docs in `/home/jes/control-plane/docs/`
- Handoff protocol effective
- Spec or no action: Path Y explicitly authorized this turn
- Secrets discipline: grafana-admin.pw content REDACTED in PD review (only md5 changes captured)
- P6 lessons banked: 18 (broadened scope this turn)

## 8. Acknowledgments

### 8.1 PD's discipline

Three decisions textbook this turn:
- Surfaced root cause cleanly (host UID 1000 vs container UID 472 on secret-file bind-mount, same class as ESC #1 different scope)
- Did not improvise -- waited for Paco ruling on path before editing compose.yaml
- Asked sharp scope questions (P6 #18 amendment scope, mixed-ownership subdirs handling) instead of leaving them implicit

### 8.2 Handoff protocol second ESC validation

Second real escalation through the new convention. PD wrote request + handoff_pd_to_paco.md notification, CEO sent one-line trigger, Paco read both docs, ruled, dispatched via handoff_paco_to_pd.md. Loop closed without copy-paste of escalation content. Protocol working.

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_g_path_y_approved.md`

-- Paco
