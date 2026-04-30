# H1 -- SlimJim Observability + MQTT Broker Close -- Ship Report

**Spec:** `tasks/H1_observability.md`
**Status:** **SHIPPED** -- 9 phases (A-I) all closed. Phase I close-out commit pending alongside this report.
**Build window:** 2026-04-26 (Day 71) -> 2026-04-30 (Day 74), ~52 hours of operational time across 19+ phases of work.
**Authoring:** Paco (architect / spec) + PD (executor / build) + CEO (ratification + browser tests).

---

## 1. Executive summary

H1 ships an end-to-end observability stack on SlimJim (`192.168.1.40`) plus the MQTT broker close-out that resolved the Day 67 YELLOW #5 carryover. The stack is Prometheus 2.55.1 + Grafana 11.3.0 in Docker Compose, scraping 5 node_exporter targets across the homelab (CK + Beast + Goliath + KaliPi + SlimJim self) plus the Netdata target on SlimJim, plus Prometheus self. CEO can browse Grafana dashboards on the LAN with provisioned datasource + 2 dashboards (Node Exporter Full rendering live data; Prometheus 2.0 Overview shipped broken under known-limitation pattern, P5 carryover). MQTT broker on dual listeners (loopback anon + LAN authed) for Alexandra agent_bus + future IoT integrations.

B2b nanosecond invariant + Garage substrate anchor on Beast held bit-identical through the entire build (`2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z`), validating the substrate-preservation discipline at scale: 19+ phases / ~52 hours / 12 ESCs / 3 compose down-up cycles / 4 chowns / 9 UFW additions / 1 SlimJim reboot. Atlas v0.1 unblocked.

---

## 2. Phase-by-phase scorecard

| Phase | Scope | Result | Gates | ESCs | Anchor commit |
|-------|-------|--------|-------|------|---------------|
| A | Baseline + UFW orphan cleanup | CLOSED | 3/3 | 0 | `f0abbdf` |
| B | docker compose v2 plugin + docker group | CLOSED | 4/4 | 0 (1 inline standing-rule introduction) | `c4ca14e` |
| C side-task | UFW delete syntax broadening | CLOSED | 3/3 | 1 (UFW delete syntax) | `2f839c7` |
| C | mosquitto 2.x dual-listener + Day 67 YELLOW #5 closure | CLOSED | 5/5 | 5 (per_listener / reload / gate5-concurrency / gate5-followup-matrix-collision / hypothesis-F) | `61ff118` |
| D | node_exporter fan-out CK/Beast/Goliath/KaliPi | CLOSED | 3/3 | 1 (Goliath + KaliPi divergent paths) | `1c35322` |
| E | observability/ skeleton + compose + provisioning | CLOSED | 4/4 | 0 (Grafana env var caught + folded into Phase F) | `172176f` |
| E corrections + F | Grafana env var Option A + UFW for SlimJim | CLOSED | 3/3 | 0 | `94f8277` |
| G | compose up + healthcheck + Bridge NAT | CLOSED structural | 5/5 (Gates 3+4 deferred to H per spec) | 3 (data-dir UID / secret-file UID / Path Y runtime-ignored) + Path 1 generalization | `c3813c6` |
| H | Grafana smoke + CEO browser tests | CLOSED literal | 4/4 | 1 (literal-PASS spirit-partial -> first standing-closure-pattern application) | `e791c08` |
| I | restart safety + ship report | CLOSED | 7/7 | 0 | (this commit) |

**Total:** 9 phases shipped + 1 side-task. **12 ESCs** across the build, all resolved cleanly. **0 substrate disturbances.**

---

## 3. Substrate invariant attestation

B2b nanosecond anchor (Postgres logical replication CK->Beast established Day 71) + Garage S3 anchor on Beast held **bit-identical** across the entire H1 build:

```
control-postgres-beast StartedAt = 2026-04-27T00:13:57.800746541Z health=healthy restarts=0
control-garage-beast   StartedAt = 2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

Verified at every phase boundary + after every state-changing operation. ~52 hours of substrate stability through:
- 12 ESCs
- 3 compose down/up cycles (Phase G)
- 4 chown operations on SlimJim filesystem
- 9 UFW rule additions across SlimJim
- 1 SlimJim full reboot (Phase I)
- 4 standing rule memory file additions
- 4 spec amendments
- 4 corrections from PD self-discovery

The discipline scaled. "Spec or no action" + per-phase anchor pre/post diffs + bidirectional one-liner handoffs together produced a build cycle where the foundation never moved.

---

## 4. Container final state

```
NAME             IMAGE (digest-pinned)                                                                              STATUS
obs-prometheus   prom/prometheus:v2.55.1@sha256:2659f4c2ebb718e7695cb9b25ffa7d6be64db013daba13e05c875451cf51b0d3   Up healthy, restart=unless-stopped
obs-grafana      grafana/grafana:11.3.0@sha256:a0f881232a6fb71a0554a47d0fe2203b6888fe77f4cefb7ea62bed7eb54e13c3    Up, restart=unless-stopped
```

**Bind mounts (post-Phase-G chown alignment):**
- `./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro`
- `./prom-data:/prometheus` (host owner: 65534:65534 nobody:nogroup)
- `./grafana/provisioning:/etc/grafana/provisioning:ro`
- `./grafana/dashboards:/var/lib/grafana/dashboards:ro`
- `./grafana-data:/var/lib/grafana` (host owner: 472:472)

**Secrets:**
- `./grafana-admin.pw` -> `/run/secrets/grafana_admin_pw` (host owner: 472:472, mode 600, content set by CEO interactively)

**Ports:** `192.168.1.40:9090->9090/tcp` (Prometheus) + `192.168.1.40:3000->3000/tcp` (Grafana)

**Healthcheck:** Prometheus has `wget -q --spider http://localhost:9090/-/healthy` interval=30s. Grafana has no healthcheck by spec design.

**Restart safety:** verified Phase I -- both containers came back up + reached healthy without manual intervention after SlimJim full reboot. obs-prometheus reached healthy ~30s post-Docker-daemon-up; obs-grafana running ~30s post-recovery.

---

## 5. Network state at H1 ship

### 5.1 SlimJim UFW (9 rules)

```
[ 1] 22/tcp                ALLOW IN 192.168.1.0/24
[ 2] 19999/tcp             ALLOW IN 192.168.1.0/24
[ 3] 1883/tcp              ALLOW IN 192.168.1.0/24    # H1 Phase C: Mosquitto LAN
[ 4] 1884/tcp              ALLOW IN 192.168.1.0/24    # H1 Phase C: Mosquitto LAN authed
[ 5] 9100/tcp              ALLOW IN 127.0.0.1         # H1 Phase E.4: node_exporter local scrape
[ 6] 9090/tcp              ALLOW IN 192.168.1.0/24    # H1 Phase F: Prometheus LAN
[ 7] 3000/tcp              ALLOW IN 192.168.1.0/24    # H1 Phase F: Grafana LAN
[ 8] 9100/tcp              ALLOW IN 172.18.0.0/16     # H1 Phase G: Prom container scrape via bridge NAT
[ 9] 19999/tcp             ALLOW IN 172.18.0.0/16     # H1 Phase G: Prom container scrape via bridge NAT (netdata)
```

### 5.2 Bridge subnet

`observability_default` Docker bridge: **172.18.0.0/16** (stable through Phase G + Phase I reboot).

### 5.3 Per-target node_exporter UFW state

| Host | IP | UFW rule | Mechanism |
|------|-----|---------|-----------|
| CK | 192.168.1.10 | UFW [25] H1 source-filter | apt prometheus-node-exporter 1.3.1, listener `*:9100` |
| Beast | 192.168.1.152 | UFW [16] H1 source-filter | apt prometheus-node-exporter 1.3.1, listener `*:9100` |
| Goliath | 192.168.1.20 | (UFW inactive on Goliath -- P5) | process-bind via /etc/default ARGS, listener `192.168.1.20:9100` |
| KaliPi | 192.168.1.254 | (UFW not installed on Kali -- P5) | process-bind via /etc/default ARGS, listener `192.168.1.254:9100` |
| SlimJim | 192.168.1.40 | UFW [5] from 127.0.0.1 + [8] from 172.18.0.0/16 | apt prometheus-node-exporter 1.7.0, listener `*:9100` |

Deviations on Goliath + KaliPi documented at Phase D close per guardrail 4 of the broadened standing rule.

---

## 6. Provisioned dashboards inventory

Located at `/home/jes/observability/grafana/dashboards/`, mounted into container at `/var/lib/grafana/dashboards/`, provisioned via `/etc/grafana/provisioning/dashboards/dashboard.yml`.

| Dashboard | Source ID | Size | Status at ship |
|-----------|-----------|------|----------------|
| Node Exporter Full | Grafana 1860 | 468,600 bytes | **WORKING** -- live data, all panels render, Grafana 11 compatible |
| Prometheus 2.0 Overview | Grafana 3662 | 85,625 bytes | **KNOWN BROKEN** -- panels show N/A, deprecated singlestat removed in Grafana 11.x; P5 carryover for v0.2 replacement |

The broken dashboard is visible (operator can see N/A, not silently failing) and bounded (other dashboard works, Prometheus has its own /targets UI). Closed under the standing closure pattern (`feedback_phase_closure_literal_vs_spirit.md`) -- 5 conditions verified satisfied.

---

## 7. Prometheus scrape targets final state (7/7 UP)

| job | scrapeUrl | Status |
|-----|-----------|--------|
| prometheus | http://localhost:9090/metrics | UP (self) |
| node | http://192.168.1.10:9100/metrics | UP (CK) |
| node | http://192.168.1.20:9100/metrics | UP (Goliath) |
| node | http://192.168.1.40:9100/metrics | UP (SlimJim self via bridge NAT [8]) |
| node | http://192.168.1.152:9100/metrics | UP (Beast) |
| node | http://192.168.1.254:9100/metrics | UP (KaliPi) |
| netdata | http://192.168.1.40:19999/api/v1/allmetrics?format=prometheus | UP (via bridge NAT [9]) |

Verified pre-reboot + post-reboot in Phase I.

---

## 8. Escalation chain summary (12 ESCs across the build)

| Phase | ESC | Topic | Resolution | Anchor |
|-------|-----|-------|------------|--------|
| C side-task | 1 | UFW delete syntax mismatch (bare port vs source-constrained rules) | Match-syntax delete approved + standing rule broadened to all command-syntax corrections (4 guardrails) | `d2da918` |
| C | 2 | mosquitto 2.0 per_listener_settings semantic change | `per_listener_settings true` prepended to santigrey.conf + 5th guardrail banked (auth/security boundary) | `f43a23d` |
| C | 3 | mosquitto reload after CEO password set | Reload approved + guardrail 5 carve-out for operational propagation banked | `8c4c8c7` |
| C | 4 | Gate 5 concurrent-CONNECT pattern (sub-bg + pub-fg from CK) | Diagnostic paths a + b approved, CK upgrade pre-authorized contingent on Beast result | `1603016` |
| C | 5 | Gate 5 followup (CONNECT-stage rejection pattern surfaced) | Beast third-host test approved | `93164d5`, corrected `465f5d1` |
| C | 6 | Beast PASS + version-parity invalidates pre-auth CK upgrade | Path B (escalate first, no upgrade) + P6 #14 banked | `4c5623c` |
| C | 7 | Hypothesis F (CK-host-specific environmental state) | F.1 (broker restart) authorized + F.4/F.2 fallbacks pre-auth; F.1 confirmed root cause | `c9e1192` |
| D | 1 | Goliath UFW inactive + KaliPi UFW not installed | A2-refined process-bind via /etc/default ARGS; deviations documented per guardrail 4 | `6266ba1` |
| E | 1 | Grafana env var single vs double underscore | Option A approved (correct in spec + on-disk + amend); P6 #17 banked | `dcd41ef` |
| G | 1 | data-dir UID mismatch (Prometheus crash loop) | Path A (chown to container UIDs) | `9aef8d1` |
| G | 2 | secret-file UID mismatch (Grafana crash loop, post-Path-A) | Path Y (compose long-syntax) attempted | `9d59cc4` |
| G | 3 | Path Y runtime-ignored (compose v2 standalone discards swarm fields) | Path X-only (revert + chown grafana-admin.pw) + P6 #19 banked + compose-down ESC carve-out banked | `e85b256` |
| G | (extension) | Bridge NAT extension for netdata 19999 | Path 1 generalized for any bridge-NAT scrape target | `3aac8b9` |
| H | 1 | Dashboard 3662 fails under Grafana 11 (literal-PASS spirit-partial) | Path A (close + P5) + new standing closure pattern banked as 4th memory file | `0326903` |

Every ESC banked durable knowledge. Compounding value remained net-positive throughout.

---

## 9. P6 lessons banked catalog (19 entries)

| # | Originated | Lesson summary |
|---|-----------|----------------|
| 1-11 | Pre-H1 | (B-substrate phase lessons, see prior ship reports) |
| 12 | Phase C (Day 73) | `set +e` discipline for verifier scripts checking exit-coded systemctl outputs (`is-active`, `is-enabled`); `&&` short-circuits on inactive states |
| 13 | Phase C (Day 73) | mosquitto 2.x major-version preflight before package install (snap broken from 1.x; apt is the supported install vector); spec text for software with major-version behavior changes must include version-feature check |
| 14 | Phase C ESC #6 (Day 73) | Spec preflight must capture client-side tooling version on each consuming host; even when version comparison ultimately disproves the hypothesis, preflight catches matrix-collision bugs before triggering no-op actions |
| 15 | Phase C ESC #7 (Day 73) | Broker-state hygiene for concurrent-CONNECT diagnostics; mosquitto restart should be first-line discriminator when single-connection tests pass but concurrent-pattern tests fail from one source |
| 16 | Phase D (Day 74) | Per-target-host operational-readiness preflight matrix for fan-out phases (firewall state / sudo policy / package availability / port collision / arch / OS family) |
| 17 | Phase E corrections (Day 74) | Spec text referencing upstream-product env var conventions must be cross-checked against current upstream docs at directive-author time (single vs double underscore class; silent-fail at runtime, not parse error) |
| 18 | Phase G ESC #1+#3 (Day 74) | First-boot of stateful containers with bind-mount data + secret resources requires UID alignment between host owner and container default UID; Phase E spec must include explicit chown directives |
| 19 | Phase G ESC #3 (Day 74) | Compose v2 secrets long-syntax fields `uid`/`gid`/`mode` are swarm-mode-only; standalone compose accepts the YAML syntactically but discards runtime values with a warning (not detected by `docker compose config` validation); for non-swarm deployments, secret-file UID alignment must be done at host filesystem level |

---

## 10. Standing rule memory files (4 entries)

| File | Banked | Originating phase | Purpose |
|------|--------|-------------------|---------|
| `feedback_directive_command_syntax_correction_pd_authority.md` | Day 73 (Phase B), broadened Day 73 (Phase C side-task), 5th guardrail Day 73 (Phase C ESC #2), carve-out Day 73 (Phase C ESC #4), section 2A Day 74 (Phase G ESC #3) | C side-task / C ESC #2 / C ESC #4 / G ESC #3 | 5-guardrail rule for PD self-correction of directive command syntax + 2 carve-outs (operational propagation of CEO state changes, compose-down during active ESC) |
| `feedback_paco_review_doc_per_step.md` | Day 73 | Phase C side-task | Per-step review docs in `docs/` for novel/blocking issues |
| `feedback_paco_pd_handoff_protocol.md` | Day 74 | Phase F + Phase G ESC #3 | Bidirectional handoff protocol with one-liner format spec on both `handoff_paco_to_pd.md` and `handoff_pd_to_paco.md` |
| `feedback_phase_closure_literal_vs_spirit.md` | Day 74 | Phase H ESC #1 | Closure pattern for literal-PASS + spirit-partial cases; 5-condition default-Path-A rule with required documentation elements |

---

## 11. Spec amendments folded into H1

All amendments to `tasks/H1_observability.md`:

- **Phase A.5** (Day 74 Phase D close): Per-target-host preflight matrix template (P6 #16)
- **Phase A.6** (Day 74 Phase E corrections): Upstream-product env var convention preflight (P6 #17)
- **Phase E.1** (Day 74 Phase G close): Filesystem-prep step for chown of bind-mount data dirs + secret file (P6 #18 broadened)
- **Phase E.6** (Day 74 Phase H close): One-line note documenting dashboard 3662 known-broken under Grafana 11.x (P5 carryover)
- **Phase G** (Day 74 Phase G close): Bridge NAT note before G.1 acceptance gates documenting Path 1 generalization for any container-to-host scrape target
- **Section 9 E.2 Grafana env var** (Day 74 Phase E corrections): `GF_SECURITY_ADMIN_PASSWORD_FILE` -> `GF_SECURITY_ADMIN_PASSWORD__FILE` (single -> double underscore for Grafana 11.x file-provider convention)

Final spec md5 at H1 ship: `ae4fa85e1811d816346dbdaa37ef3cc9` (28,362 bytes / 619 lines).

---

## 12. v0.2 hardening pass queue (5 items grouped)

All P5 carryovers from H1 Phases D + G + H, grouped for one cohesive hardening pass:

1. **Goliath UFW enable** (Phase D) -- enable UFW + allow SSH 22 first / then 9100 source-filter
2. **KaliPi UFW install + enable** (Phase D) -- larger lift since Kali rolling doesn't ship UFW; install + enable + SSH preservation + 9100 rule
3. **grafana-data subdirs ownership cleanup** (Phase G) -- `dashboards` root:root + `plugins` 472:root from ESC #2/#3 cycle; chmod -R 472:472 to normalize
4. **Grafana admin password rotation helper script** (Phase G) -- wrap the 4-step rotation flow (chown + chmod + restart) in a single helper at `/home/jes/observability/scripts/rotate-grafana-admin.sh`
5. **Dashboard 3662 replacement** (Phase H) -- 3 candidates evaluated: Grafana 15489 / Grafana 3681 / hand-rolled minimal; validate against Grafana 11 in sandbox before swapping

Plus **post-H1 P5 finding** from Phase I: CK -> slimjim hostname DNS resolution broken (`Temporary failure in name resolution` from CK while SlimJim is up). Likely `/etc/hosts` or systemd-resolved cache; investigate at v0.2 hardening time.

One grouped pass at v0.2 hardening time addresses all 6.

---

## 13. Operational runbooks established

### 13.1 compose-down during active ESC (PD self-auth)

From `feedback_directive_command_syntax_correction_pd_authority.md` section 2A. When Compose stack is in active failure mode + 4 conditions hold (failure observable+ongoing / canonical mechanism / bounded retry / no config-state mutation), PD self-issues `docker compose down` without inline auth.

### 13.2 Path 1 Bridge NAT for any container-to-host scrape

From `paco_response_h1_phase_g_path_1_extension.md`. PD self-applies UFW `allow from <bridge-subnet> to any port <port>` for any Prometheus scrape target failing with bridge-NAT context-deadline-exceeded; documented per guardrail 4.

### 13.3 Grafana admin password rotation (current procedure, v0.2 will wrap in script)

```bash
sudo bash -c "printf '%s' '<new-password>' > /home/jes/observability/grafana-admin.pw"
sudo chown 472:472 /home/jes/observability/grafana-admin.pw
sudo chmod 600 /home/jes/observability/grafana-admin.pw
cd /home/jes/observability && docker compose restart grafana
```

### 13.4 Phase closure under literal-PASS + spirit-partial

From `feedback_phase_closure_literal_vs_spirit.md`. Default Path A (close + P5) when 5 conditions hold; required documentation elements (Known limitations / P5 by reference / inline-fix rationale / spec amendment).

---

## 14. Restart safety attestation (Phase I Half A)

SlimJim full systemctl reboot performed Day 74 at 12:27:08 UTC. Recovery evidence:

- **OS boot:** 40.6s total (4.3s kernel + 36.3s userspace) per `systemd-analyze`
- **Network layer:** ICMP responsive at ~12:29:00 UTC (~110s post-reboot)
- **TCP/22:** open at the same window
- **SSH/sshd:** ready by ~12:30:00 UTC (~180s post-reboot)
- **Containers:** both came back via `restart: unless-stopped` policy without manual intervention; obs-prometheus reached `healthy` ~30s post-Docker-daemon-up; new StartedAt `2026-04-30T00:28:42`
- **Prometheus targets:** 7/7 UP within ~60s of containers reaching healthy
- **UFW:** all 9 rules persisted byte-for-byte (rules + comments + bridge NAT entries [8] + [9] all intact)
- **systemd:** mosquitto + prometheus-node-exporter + docker all came back active+enabled
- **Bridge subnet:** stable at 172.18.0.0/16 (didn't change across reboot)
- **Beast anchors:** bit-identical pre/post (SlimJim reboot independent of Beast Docker)

**Verdict:** Restart safety verified. Stack is operationally durable.

---

## 15. Substrate state at H1 ship

```
control-postgres-beast StartedAt = 2026-04-27T00:13:57.800746541Z health=healthy restarts=0
control-garage-beast   StartedAt = 2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

Both on Beast (`192.168.1.152`). Bit-identical to Day 71 establishment. Untouched through all of H1.

**Atlas v0.1 substrate dependencies:** all SATISFIED.
- B2a Postgres + pgvector on Beast: CLOSED
- B2b logical replication CK->Beast: CLOSED
- B1 Garage S3 on Beast: CLOSED
- D1 MCP Pydantic limits: VERIFIED
- D2 homelab_file_write tool: VERIFIED
- H1 observability stack: SHIPPED (this report)

Atlas v0.1 is unblocked.

---

## 16. Known limitations at ship

Per the standing closure pattern, explicit acknowledgment of the H1 deliverable's known broken-state:

**Dashboard 3662 ("Prometheus 2.0 Overview")** is provisioned and visible in Grafana's Dashboards menu but renders all panels N/A when opened. Operator sees clearly-broken dashboard, not silent failure. Other observability surfaces unaffected.

- **Why it ships broken:** Grafana 4-5 era (~2018) dashboard, deprecated `singlestat` panel removed in Grafana 11.x, auto-migration insufficient. Phase E preflight gap (selected by community popularity without Grafana 11 compat validation).
- **Operational impact:** minimal. Node Exporter Full is the primary observability surface. Prometheus self-monitoring available via Prometheus's own UI at `http://192.168.1.40:9090/targets` and `/graph`.
- **P5 disposition:** v0.2 hardening pass with 3 candidate replacements identified (15489 / 3681 / hand-rolled minimal).

---

## 17. Forward state

**Atlas v0.1 unblocked.** All H1 + B-substrate dependencies satisfied. Paco drafts the spec next; PD executes.

**v0.2 hardening pass queued** with 6 grouped P5 items (Goliath UFW + KaliPi UFW + grafana-data subdirs + admin pw rotation script + dashboard 3662 replacement + CK->slimjim DNS).

**H2 (Cortez integration)** + **H3 (Pi3 DNS Gateway)** specs not yet drafted; gated on Atlas v0.1 substrate-prep priority.

**H4 (VLAN segmentation)** deferred -- router-replacement-gated (MR60 satellite cannot route VLANs).

**Standing rules + protocols** banked through H1 are now durable infrastructure for future phases:
- 5-guardrail rule + 2 carve-outs (operational propagation, compose-down ESC)
- Per-step review docs
- Bidirectional one-liner handoff protocol
- Phase closure pattern for literal-PASS + spirit-partial
- P6 lesson catalog at 19 entries with phase-by-phase originating context

**Substrate:** B2b nanosecond invariant + Garage anchor on Beast -- both untouched, bit-identical, ready to anchor Atlas v0.1 work.

H1 SHIPPED.

-- PD, on behalf of Paco (architect) + CEO (ratification + browser tests)
