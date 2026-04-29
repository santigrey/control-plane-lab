# Paco -> PD ruling -- H1 Phase G data-dir UID mismatch (Path A approved + P6 #18 banked)

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-29 (Day 74)
**Predecessor:** `docs/paco_request_h1_phase_g_data_dir_perms.md` (PD ESC during Phase G G.2/G.3)
**Status:** **APPROVED** -- Path A (chown) -- `docker compose down` ratified -- P6 #18 banked

---

## TL;DR

Three rulings:

1. **`docker compose down` ratified.** CEO authorized inline; that was the right call. Bank as guardrail 5 carve-out instance: stopping an actively crash-looping service during an escalation is operational propagation, not state modification.
2. **Path A APPROVED** (chown host dirs to container UIDs). PD's bias correct. Standard pattern for prom/prometheus + grafana/grafana official images. No compose.yaml edit. Reversible.
3. **P6 #18 BANKED.** Bind-mount data directories require UID alignment between host owner and container default UID before first compose-up. Phase E spec gap caught here; spec amendment lands in Phase G close-out.

---

## 1. `docker compose down` ratification

CEO authorized the down command inline. That was correct.

Stopping a crash-looping container is operational hygiene -- not a state change to the deployment, not a config edit, not auth surface impact. The container is in a broken state by definition; stopping it is the digital equivalent of pulling power on a malfunctioning device. Fits guardrail 5 carve-out as "operational propagation of CEO-authorized state changes" -- CEO observed the failure and authorized the stop; PD propagated.

Banking observation: future similar cases (PD escalates an active failure with crash-loop or runaway-resource symptoms; CEO authorizes stop inline; PD propagates) are pre-authorized under guardrail 5 carve-out IF (a) the failure is observable + ongoing, (b) the stop command is the canonical mechanism (`docker compose down`, `systemctl stop`, `kill -TERM <pid>`), (c) failure mode is bounded to "stays stopped, retry available." Document in review per guardrail 4.

## 2. Path A ruling -- APPROVED

PD's bias is correct. Three reasons over Path B:

### 2.1 Standard pattern

Both `prom/prometheus` and `grafana/grafana` official images expect to own their data dir at their image-default UID. Running them under host UID 1000 via `user:` works for Prometheus but produces subtle issues for Grafana -- the Grafana image runs `chown -R grafana:grafana` on certain paths at startup; forcing UID 1000 leaves file ownership inconsistent and may cause plugin/provisioning side-effects. Running each image as its expected UID is the deployment pattern documented in upstream Docker run examples.

### 2.2 No compose.yaml edit

Keeps the spec-deployed compose.yaml byte-identical. No guardrail 4 documentation overhead. The spec amendment for P6 #18 lands in `tasks/H1_observability.md` Phase E.1 (directory creation), not in compose.yaml.

### 2.3 Reversible

If we ever switch patterns (e.g. moving to a non-bind-mount volume model in v0.2), single chown back. Path B's `user:` directive locks in non-standard UID mapping that's harder to undo.

## 3. Path A execution

### 3.1 Procedure (PD self-auth under this ruling)

```bash
# Confirm stack is down
cd /home/jes/observability
docker compose ps
# Expected: 0 containers running, or both Stopped

# Apply chown to match container default UIDs
sudo chown -R 65534:65534 /home/jes/observability/prom-data
sudo chown -R 472:472 /home/jes/observability/grafana-data

# Verify
stat -c '%a %u:%g %U:%G %n' /home/jes/observability/prom-data /home/jes/observability/grafana-data
# Expected: 700 65534:65534 nobody:nogroup ./prom-data
#           700 472:472 (no-name):(no-name) ./grafana-data    # UIDs without /etc/passwd entries on host show numeric

# Re-launch stack
docker compose up -d

# Healthcheck poll (cap 120s) -- same pattern as G.3
for i in $(seq 1 24); do
  PROM_HEALTH=$(docker inspect obs-prometheus --format '{{.State.Health.Status}}' 2>/dev/null || echo missing)
  GRAF_HEALTH=$(docker inspect obs-grafana --format '{{.State.Health.Status}}' 2>/dev/null || echo missing)
  echo "poll $i: prometheus=$PROM_HEALTH grafana=$GRAF_HEALTH"
  [ "$PROM_HEALTH" = healthy ] && [ "$GRAF_HEALTH" = healthy ] && break
  sleep 5
done

docker compose ps
docker inspect obs-prometheus obs-grafana --format '{{.Name}} StartedAt={{.State.StartedAt}} health={{.State.Health.Status}} restarts={{.RestartCount}}'
```

Expected: both containers Up healthy with RestartCount=0.

### 3.2 Then resume Phase G

Continue from G.4 (scrape target verification) through G.6 (Beast anchor post-capture) per the original handoff. Bridge NAT decision (G.5) still pending runtime check after Prometheus reaches scrape stage.

## 4. P6 #18 BANKED

### 4.1 Banked rule

> **Bind-mount data directories require UID alignment between host owner and container default UID before first compose-up.**
>
> When a spec phase creates bind-mount directories for stateful containers (Prometheus, Grafana, Postgres, Garage, etc.), the directory-prep step must include either (a) chown to the container's default UID, or (b) a `user:` directive in compose.yaml mapping container UID to host owner. Default approach: (a) chown to image-default UID, since most upstream images expect to own their data dir.
>
> Required spec preflight: capture image-default UID at spec-author time alongside the bind-mount declaration. For unfamiliar images, run `docker run --rm --entrypoint id <image>` to capture the default UID before spec writes the bind-mount.
>
> Default UIDs for common images banked here:
> - `prom/prometheus`: 65534 (nobody)
> - `grafana/grafana`: 472 (grafana)
> - `postgres`, `pgvector/pgvector`: 999 (postgres)
> - `dxflrs/garage`: 0 (root, scratch image)
> - `nginx`: 101 (nginx)
> - `redis`: 999 (redis)
>
> Banked from H1 Phase G Day 74: Phase E built `prom-data` + `grafana-data` chmod 700 jes:jes (UID 1000); Phase G compose-up panicked at first write because Prometheus runs as UID 65534 and Grafana runs as UID 472. The fix at directive-write-time is one chown line per data dir during the directory-prep step; the fix at deploy-time cost one escalation roundtrip + crash-loop log noise.

### 4.2 P6 lessons banked count

**18** (was 17). Lands in Phase G close-out commit alongside the spec amendment.

### 4.3 H1 spec amendment scheduled

`tasks/H1_observability.md` Phase E.1 (directory tree creation) gets a new bullet appended:

> After creating bind-mount data directories, chown each to its container's default UID per P6 #18 (Phase E close-out 2026-04-29):
> ```bash
> sudo chown -R 65534:65534 /home/jes/observability/prom-data
> sudo chown -R 472:472 /home/jes/observability/grafana-data
> ```

Fold into Phase G close-out commit, NOT separate.

## 5. Order of operations from here

```
1. PD: confirm stack down (docker compose ps -a shows 0 running)
2. PD: apply Path A chown -- /home/jes/observability/prom-data -> 65534:65534
                              /home/jes/observability/grafana-data -> 472:472
3. PD: docker compose up -d
4. PD: healthcheck poll (G.3 pattern, cap 120s)
5. PD: resume Phase G G.4 (scrape target verification)
6. PD: G.5 bridge NAT decision (Path 1 if SlimJim self-scrape fails, or note not-needed if Linux local routing optimized)
7. PD: G.6 Beast anchor post-capture (must be bit-identical)
8. PD: write paco_review_h1_phase_g_compose_up.md including:
   - Path A chown evidence
   - 5-gate scorecard
   - Bridge NAT decision + evidence
   - Beast anchor pre/post diff
   - P6 #18 banking + spec amendment cross-reference
9. PD: Phase G close-out commit folds:
   - paco_review_h1_phase_g_compose_up.md
   - tasks/H1_observability.md Phase E.1 amendment for chown step
   - SESSION.md (P6 = 18)
   - paco_session_anchor.md (P6 = 18, Phase G CLOSED, Phase H NEXT)
   - CHECKLIST.md audit entry
10. PD: write notification to /home/jes/control-plane/docs/handoff_pd_to_paco.md
11. PD: git commit + push
12. CEO triggers Paco with one-line: "Paco, PD finished, check handoff."
```

## 6. Standing rules in effect

- 5-guardrail rule + carve-out (this case correctly routed to escalation -- substantive ownership-model decision, not mechanical correction)
- B2b + Garage nanosecond anchor preservation (still holding through Phase G failure + recovery)
- Per-step review docs in `/home/jes/control-plane/docs/`
- Handoff protocol effective (PD wrote handoff_pd_to_paco.md correctly; CEO sent the one-line trigger; this paco_response is dispatched via handoff_paco_to_pd.md)
- Spec or no action: Path A explicitly authorized this turn
- Secrets discipline: no creds touched
- P6 lessons banked: 18 (added #18 this turn)

## 7. Acknowledgments

### 7.1 PD's discipline

Three decisions this turn were textbook:
- Surfaced root cause cleanly (host UID 1000 vs container UID 65534/472, mode 700 DAC denial)
- Did not improvise -- waited for Paco ruling on path before chown'ing or editing compose.yaml
- Asked for explicit authorization on `docker compose down` despite CEO inline approval (correct: PD's protocol requires Paco ratification of stop-actions during active escalations)

### 7.2 Handoff protocol working as designed

First real escalation through the new handoff convention. PD wrote the request to /docs/, notified via handoff_pd_to_paco.md, CEO sent the one-line trigger, Paco read both docs and is responding via handoff_paco_to_pd.md. Loop closed without copy-paste of the escalation content. Protocol validated.

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_g_path_a_approved.md`

-- Paco
