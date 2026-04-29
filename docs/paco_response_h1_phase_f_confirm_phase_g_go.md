# Paco -> PD response -- H1 Phase F CONFIRMED 3/3 PASS, Phase G GO

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-29 (Day 74)
**Spec:** `tasks/H1_observability.md` section 11 (Phase G)
**Predecessor:** `docs/paco_review_h1_phase_f_ufw.md` (commit `94f8277`)
**Status:** **CONFIRMED 3/3 PASS** -- Phase G GO authorized + handoff protocol now in effect

---

## TL;DR

Three confirmations + Phase G GO:

1. **Phase F 3/3 PASS CONFIRMED.** Independent Paco verification: UFW = 7 rules with rules 1-5 byte-identical pre/post + rules 6+7 carrying H1 Phase F comments. compose.yaml md5 `db89319cad27c091ab1675f7035d7aa3` (Correction 2 applied) + double-underscore `GF_SECURITY_ADMIN_PASSWORD__FILE` confirmed live. B2b + Garage anchors bit-identical (19+ phases, ~50 hours).
2. **Correction 1 + Correction 2 confirmed applied** correctly per Option A authorization at Phase E review time.
3. **P6 #17 spec amendment landed** in tasks/H1_observability.md section A.6 per PD review section 4.

**Phase G GO authorized** with two prerequisites: (a) CEO writes grafana-admin.pw content; (b) handoff protocol now in effect for all PD task dispatches.

## 1. Independent Phase F verification (Paco's side)

```
Gate 1 (UFW count 5 -> 7):
  Pre:  5 rules ([1] 22/tcp, [2] 19999/tcp, [3] 1883 H1 Phase C, [4] 1884 H1 Phase C, [5] 9100 from 127.0.0.1 H1 E.4)
  Post: 7 rules (above + [6] 9090 from 192.168.1.0/24 H1 Phase F: Prometheus LAN, [7] 3000 from 192.168.1.0/24 H1 Phase F: Grafana LAN)
  Live ufw status numbered shows: 7 rules confirmed
  -> PASS

Gate 2 (no existing rules modified):
  Rules [1]-[5] byte-identical pre/post (PD review section 1.1 vs 1.3)
  -> PASS

Gate 3 (both new rules carry H1 Phase F comments):
  [6] 9090/tcp ALLOW IN 192.168.1.0/24    # H1 Phase F: Prometheus LAN
  [7] 3000/tcp ALLOW IN 192.168.1.0/24    # H1 Phase F: Grafana LAN
  -> PASS

Correction 2 verification (live this turn):
  /home/jes/observability/compose.yaml md5 = db89319cad27c091ab1675f7035d7aa3 (matches PD post-correction)
  grep GF_SECURITY_ADMIN_PASSWORD shows: GF_SECURITY_ADMIN_PASSWORD__FILE: /run/secrets/grafana_admin_pw
  Double underscore confirmed -- Phase G smoke test will read CEO password correctly
  -> PASS

B2b + Garage anchors (live):
  /control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z healthy 0
  /control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z healthy 0
  -> BIT-IDENTICAL through Phase F (19+ phases preserved, ~50 hours)
```

All gates PASS. Phase F is CONFIRMED.

## 2. Acknowledgments

### 2.1 Phase F discipline

Phase F was the cleanest H1 phase to date: 2 UFW additions + 2 corrections folded into single commit, zero escalations, byte-perfect against directive. Mechanical scope as predicted; no surprises.

### 2.2 P6 #17 spec amendment landed

Section A.6 added to `tasks/H1_observability.md` per PD review section 4. Spec md5 `71aaf1ef` -> `a81e24c8` (600 -> 608 lines, +8). The preflight rule for upstream-product env var conventions is now banked into the spec template forward.

### 2.3 Discipline observation

PD's full broadened-standing-rule cycle demonstrated end-to-end this phase: typo-level reflex (`__FILE`) -> guardrail 5 self-catch -> revert to spec literal -> escalate at review with 3 options -> Paco ratifies Option A -> Correction applied + spec amended in close-out commit -> runtime validation deferred to Phase G. The single-character bug would have shipped silent-fail to admin/admin without the discipline catch. Banked observation: 5-guardrail rule effectiveness measurable at typo-level.

## 3. Phase G directive

Per spec section 11. Phase G is the FIRST container boot of the new observability stack.

### 3.1 Two prerequisites

**Prerequisite 1 (CEO action)**: write grafana-admin.pw content. CEO action only; PD never sees the literal value.

```bash
ssh slimjim
printf '%s' '<chosen-password>' | sudo tee /home/jes/observability/grafana-admin.pw > /dev/null
sudo chown jes:jes /home/jes/observability/grafana-admin.pw
sudo chmod 600 /home/jes/observability/grafana-admin.pw
stat -c '%a %U:%G %s' /home/jes/observability/grafana-admin.pw  # confirm 600 jes:jes <non-zero size>
exit
```

Use `printf '%s'` instead of `echo -n` to guarantee no trailing newline (echo's `-n` flag is not POSIX-portable; printf is). Trailing newline would cause Grafana login failure on first attempt.

**Prerequisite 2 (handoff protocol)**: starting Phase G, all PD task dispatches use the handoff protocol per `feedback_paco_pd_handoff_protocol.md`. This Phase G directive is the first task to fire via the new pattern.

### 3.2 Phase G scope

```bash
cd /home/jes/observability
docker compose pull   # validates digests match cache, no-op if cached
docker compose up -d  # starts both containers

# Healthcheck poll (cap ~120s)
for i in $(seq 1 24); do
  PROM_HEALTH=$(docker inspect obs-prometheus --format '{{.State.Health.Status}}' 2>/dev/null || echo missing)
  GRAF_HEALTH=$(docker inspect obs-grafana --format '{{.State.Health.Status}}' 2>/dev/null || echo missing)
  echo "poll $i: prometheus=$PROM_HEALTH grafana=$GRAF_HEALTH"
  [ "$PROM_HEALTH" = healthy ] && [ "$GRAF_HEALTH" = healthy ] && break
  sleep 5
done

# Capture container state
docker compose ps
docker inspect obs-prometheus obs-grafana --format '{{.Name}} StartedAt={{.State.StartedAt}} health={{.State.Health.Status}} restarts={{.RestartCount}}'
```

### 3.3 Bridge NAT decision (Phase G runtime)

Flagged at Phase E close, unchanged this phase. When Prometheus container scrapes `192.168.1.40:9100`, source IP is the bridge gateway (likely `172.17.0.1` or compose project's bridge subnet), NOT `127.0.0.1`. UFW rule [5] (`from 127.0.0.1`) won't match.

**Three resolution paths** (decided at Phase G runtime when behavior observable):

- **Path 1**: Add UFW rule `from <bridge-subnet>` for port 9100. Capture compose project's bridge subnet via `docker network inspect observability_default --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}'`. Single new UFW rule.
- **Path 2**: Switch Prometheus container to `network_mode: host`. Container shares host's network namespace; source IP for scrape becomes 127.0.0.1 (matches existing UFW [5]). compose.yaml edit; no UFW change.
- **Path 3**: invalid (eliminated at Phase E close).

**Diagnostic at Phase G**: check Prometheus targets page or query `up{instance="192.168.1.40:9100"}` after compose-up. If UP=0 with connection-refused, bridge NAT issue confirmed; pick Path 1 or Path 2. If UP=1, Linux local routing optimized via lo and the issue didn't manifest.

### 3.4 Phase G acceptance gates (5 gates per spec section 11)

1. Both containers (`obs-prometheus`, `obs-grafana`) Up + healthy
2. All 7 scrape targets returning UP in Prometheus (curl `http://192.168.1.40:9090/api/v1/targets` from SlimJim)
3. Grafana login works with admin + CEO password (CEO browser test from LAN)
4. Both dashboards loaded + rendering data (CEO browser test)
5. Bridge NAT resolution applied if needed (Path 1 / Path 2 / not needed) with documentation per guardrail 4

Plus standing gate: B2b + Garage anchors bit-identical pre/post.

### 3.5 Single-host preflight (G.0) per P6 #16

```bash
# SlimJim preflight before compose up
stat -c '%a %U:%G %s' /home/jes/observability/grafana-admin.pw  # expect 600 jes:jes >0 bytes
ls -la /home/jes/observability/                                  # expect tree intact
docker images --digests | grep -E 'prom/prometheus|grafana/grafana'  # expect 2 images cached with digests
sudo ss -tlnp | grep -E ':(9090|3000)\b'                         # expect EMPTY (no collision)
free -h                                                           # expect >2G available
df -h /home /var/lib/docker                                       # expect >10G free for compose volumes
systemctl is-active mosquitto prometheus-node-exporter            # expect active active
sudo ufw status numbered | head -10                               # expect 7 rules per Phase F close
```

## 4. Order of operations

```
1. CEO: write grafana-admin.pw content (prerequisite 1, action only by CEO)
2. Paco: write task to /home/jes/control-plane/docs/handoff_paco_to_pd.md (this turn)
3. CEO: send one-line trigger to PD: "Read docs/handoff_paco_to_pd.md and execute."
4. PD: read handoff_paco_to_pd.md, clear it, execute Phase G:
   4a. G.0 single-host preflight
   4b. docker compose up -d + healthcheck poll
   4c. capture container state + scrape target health
   4d. Bridge NAT decision (Path 1 or Path 2 if needed, documented per guardrail 4)
   4e. Beast anchor preservation pre/post
   4f. write paco_review_h1_phase_g_compose_up.md to /home/jes/control-plane/docs/
   4g. write notification to /home/jes/control-plane/docs/handoff_pd_to_paco.md
5. CEO: "Paco, PD finished, check handoff."
6. Paco: read handoff_pd_to_paco.md + clear it + read paco_review + verify + Phase H GO
7. Phase H (Grafana smoke + LAN access test) -- handoff protocol continues
```

## 5. Standing rules in effect

- 5-guardrail rule + carve-out (Phase F demonstrated full cycle including Correction 1+2 application)
- B2b + Garage nanosecond anchor preservation through 19+ phases
- Per-step review docs in `/home/jes/control-plane/docs/`
- **Handoff protocol effective starting Phase G** (`feedback_paco_pd_handoff_protocol.md`, banked Day 74)
- Spec or no action: Phase G follows spec section 11 with bridge-NAT decision authorized at runtime
- Secrets discipline: grafana-admin.pw content set by CEO interactively, REDACTED in PD review
- P6 lessons banked: 17

## 6. Phase progress summary

```
H1: A -> B -> side-task -> C -> D -> E -> F -> G -> H -> I
    OK   OK   OK           OK   OK   OK   OK   GO   .    .

Phase F close summary:
  - 2 UFW additions (5 -> 7 rules)
  - 2 corrections folded (spec amendment + on-disk compose.yaml)
  - 1 P6 lesson banked (#17 upstream-env-var-cross-check)
  - PD's Phase G NAT concern pending runtime resolution
  - Anchors bit-identical, ~50 hours preservation

Phase G next:
  - First container boot of observability stack
  - 5-gate acceptance + standing anchor gate
  - Bridge NAT path decision at runtime
  - Handoff protocol effective

Phase H + I after:
  - Grafana smoke + LAN access
  - Restart safety + 15-gate ship report
  - H1 ships -> Atlas v0.1 spec drafting unblocks
```

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_f_confirm_phase_g_go.md`

-- Paco
