# paco_request_h1_phase_g_data_dir_perms

**Spec:** H1 -- observability stack first container boot (`tasks/H1_observability.md` Phase G)
**Step:** Phase G -- post-G.2 (compose up), pre-G.3 healthcheck PASS
**Status:** ESCALATION. Phase G Gate 1 (containers Up + healthy + RestartCount=0) FAILING. Bind-mount data-dir permissions mismatch between host (jes:jes 700) and container UIDs (Prometheus=65534/nobody, Grafana=472/grafana). Outside Paco's anticipated failure modes (Bridge NAT G.5).
**Predecessor:** `docs/handoff_paco_to_pd.md` (cleared per protocol; HEAD `701e1d3`)
**Author:** PD
**Date:** 2026-04-29 (Day 74)
**Target host:** SlimJim (`192.168.1.40`)

---

## TL;DR

obs-prometheus enters crash loop on first boot:

```
err="open /prometheus/queries.active: permission denied"
panic: Unable to create mmap-ed active query log
```

Restart count climbing (10 and rising at last capture). obs-grafana stuck in `Status=created` waiting indefinitely on `depends_on: prometheus: condition: service_healthy` cascade.

Root cause: bind-mount `./prom-data:/prometheus` is host-owned `jes:jes` mode 700. Container runs as default UID 65534 (`nobody`), no write permission. Same issue for `./grafana-data:/var/lib/grafana` against UID 472 (`grafana`).

Resolution requires either chown of host directories to match container UIDs, OR `user:` directive in compose.yaml mapping container UID to host owner. Paco ruling needed on path. Recommend `docker compose down` concurrent with this request to stop crash-loop noise.

B2b nanosecond anchor: `2026-04-27T00:13:57.800746541Z` -- holding. Garage anchor: `2026-04-27T05:39:58.168067641Z` -- holding. Substrate undisturbed.

---

## 1. Failure evidence

### 1.1 obs-prometheus state

```
Status=restarting ExitCode=2 Error= Restarts=10
```

### 1.2 obs-prometheus log (panic recurrence)

```
ts=2026-04-29T19:32:06.619Z caller=query_logger.go:114 level=error component=activeQueryTracker
  msg="Error opening query log file" file=/prometheus/queries.active
  err="open /prometheus/queries.active: permission denied"
panic: Unable to create mmap-ed active query log

goroutine 1 [running]:
github.com/prometheus/prometheus/promql.NewActiveQueryTracker({...}, 0x14, {...})
        /app/promql/query_logger.go:146 +0x411
main.main()
        /app/cmd/prometheus/main.go:803 +0x8b6f
```

This stack repeats every ~13s as the container restarts and crashes again.

### 1.3 obs-grafana state

```
Status=created ExitCode=0 Error= Restarts=0
```

Grafana never started. Stuck in `created` because compose `depends_on: prometheus: condition: service_healthy` blocks startup until Prometheus becomes healthy. Prometheus never gets there.

### 1.4 docker compose ps -a

```
NAME             SERVICE      STATUS
obs-grafana      grafana      Created
obs-prometheus   prometheus   Restarting (2) 4 seconds ago
```

---

## 2. Root cause

### 2.1 Host bind-mount ownership

```
drwx------ 2 jes jes 4096 prom-data
drwx------ 2 jes jes 4096 grafana-data
```

Mode 700, owned `jes:jes` (UID 1000:1000).

### 2.2 Container default UIDs

- `prom/prometheus:v2.55.1` runs as `nobody` (UID 65534) by default per image documentation.
- `grafana/grafana:11.3.0` runs as `grafana` (UID 472) by default per image documentation.

### 2.3 compose.yaml -- no `user:` directive on either service

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.55.1@sha256:...
    volumes:
      - ./prom-data:/prometheus
    # NO user: directive

  grafana:
    image: grafana/grafana:11.3.0@sha256:...
    volumes:
      - ./grafana-data:/var/lib/grafana
    # NO user: directive
```

### 2.4 Mismatch

Container UID 65534 (Prometheus) tries to write to host-mounted directory owned by UID 1000 mode 700. Linux DAC permission denial. Prometheus's `NewActiveQueryTracker` panics on mmap creation failure on the first write. `restart: unless-stopped` triggers immediate restart. Loop.

Grafana would face same issue (UID 472 vs host 1000) but never gets to try because of the depends_on health gate.

---

## 3. Why this is not in spec failure modes

Paco's handoff section G.5 anticipates only the Bridge NAT failure (UFW blocking container-to-host scrape path). The data-dir permission mismatch is a different class of failure. Phase E spec built the bind-mount directories but did not document the chown step needed for first compose-up. Likely a spec gap from Phase E config-only build (containers were never started during Phase E so the permission issue was latent until Phase G compose-up).

This is outside the 5-guardrail rule's domain. It's a substantive operational decision about ownership model, not a mechanical pkg-name/syntax/path/ops-propagation correction. Correctly routed to escalation.

---

## 4. Resolution paths

### 4.1 Path A -- chown host directories to container UIDs (PD bias)

```bash
sudo chown -R 65534:65534 /home/jes/observability/prom-data
sudo chown -R 472:472 /home/jes/observability/grafana-data
```

**Pros:**
- No compose.yaml change (no guardrail 4 documentation burden)
- Standard Prometheus + Grafana deployment pattern
- Cleanest separation: host owner is just the bind point, container UID owns the data
- Reversible (chown back to jes:jes)

**Cons:**
- Host-side `jes` user can no longer read/write these dirs without sudo
- Acceptable since data dirs aren't human-edited

### 4.2 Path B -- compose.yaml `user:` directive (PD secondary)

```yaml
prometheus:
  user: "1000:1000"  # jes
grafana:
  user: "1000:1000"  # jes
```

No chown needed (host already 1000:1000).

**Pros:**
- Host owner stays jes:jes
- Single compose.yaml edit, no host filesystem mutation

**Cons:**
- compose.yaml changes require guardrail 4 documentation
- Containers running as non-default UID may have subtle side-effects (image internal user lookups, log path ownership, etc.)
- Less standard pattern for these specific images

### 4.3 Path C -- per-image env var (PUID/PGID)

Not applicable. Official `prom/prometheus` and `grafana/grafana` images do not implement LinuxServer.io PUID/PGID pattern.

### 4.4 Path D -- run containers as root

Anti-pattern. Security regression. NOT recommended.

---

## 5. PD bias

**Path A.** Cleanest, most standard, zero compose.yaml changes, reversible. Path B is acceptable fallback but requires spec amendment + carries non-standard user mapping risk.

---

## 6. Recommended interim action

`docker compose down` to stop the crash loop while waiting for Paco's ruling. obs-prometheus restart count went from 9 to 10 between captures. Each restart produces ~25 lines of panic log. Stopping prevents needless log accumulation and frees the container slots for a clean restart post-fix.

This is a benign reversible operation. Asking for explicit Paco authorization since it changes container state during an active escalation.

---

## 7. PD has NOT done

- chown'd anything (waiting on Paco path ruling)
- Modified compose.yaml (waiting on Paco path ruling)
- Run `docker compose down` (waiting on section 6 authorization)
- Captured Beast anchor post (Phase G G.6 -- defer until containers reach healthy state)

---

## 8. Asks of Paco

1. **Path ruling.** A (chown) vs B (user: directive) vs other?
2. **Authorize `docker compose down`** to stop crash loop while waiting for path ruling?
3. **Spec amendment ack.** This is a Phase E spec gap (data-dir prep didn't include UID alignment). Bank P6 #18 candidate: "First-boot of stateful containers with bind-mount data dirs requires UID alignment between host owner and container default UID -- include in Phase E directory-prep step, not deferred to Phase G compose-up."

---

## 9. State at this pause

### 9.1 What is true now

- obs-prometheus: Restarting (crash-loop), restart count 10 climbing
- obs-grafana: Created (never started, blocked on prometheus health)
- /home/jes/observability/prom-data: drwx------ jes:jes (host)
- /home/jes/observability/grafana-data: drwx------ jes:jes (host)
- compose.yaml: md5 unchanged (Phase E artifact); no user: directives
- mosquitto.service on SlimJim: active+enabled (unaffected)
- agent-bus.service on SlimJim: active+enabled (unaffected)
- node_exporter on SlimJim/Beast/CK/etc: unaffected
- Beast anchors: bit-identical pre/post G.0 + G.1 + G.2 (B2b: 2026-04-27T00:13:57.800746541Z, Garage: 2026-04-27T05:39:58.168067641Z)
- Phase G Gate 1: FAILING

### 9.2 What is unchanged since `701e1d3`

- compose.yaml content
- All grafana provisioning + dashboard files
- prometheus.yml
- grafana-admin.pw
- UFW (still 7 rules; Bridge NAT path not yet evaluated since prometheus never reached scrape stage)
- All other hosts

---

## 10. Cross-references

**Standing rules invoked:**
- 5-guardrail rule: this is OUTSIDE the rule's domain (substantive operational decision, not mechanical correction)
- Spec or no action: PD has not improvised any state changes
- B2b + Garage anchor preservation invariant: holding
- Handoff protocol effective (commit `65e3fd4`)

**Predecessor doc chain (Phase G):**
- `paco_response_h1_phase_f_confirm_phase_g_go.md` (commit `701e1d3`)
- `docs/handoff_paco_to_pd.md` (Day 74, cleared per protocol)
- (this) `paco_request_h1_phase_g_data_dir_perms.md` (PD ESC during Phase G G.2/G.3)

---

## 11. Status

**AWAITING PACO RULING on:**
1. Path A (chown) vs Path B (user: directive) vs other
2. Authorize `docker compose down` to stop crash loop while waiting
3. P6 #18 candidate ack (spec gap: Phase E should have included data-dir UID alignment)

PD paused. Crash loop ongoing (benign, log noise only). Substrate undisturbed. No further changes pending Paco's response.

-- PD
