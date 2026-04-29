# Paco Session Anchor -- JesAir Resume

**Last updated:** 2026-04-29 / Day 74 (H1 Phase D close)
**Last commit:** Phase D 3/3 PASS close-out (see git log for SHA) -- supersedes `61ff118` Phase C close
**Resume phrase:** "Day 74 close: H1 Phase D 3/3 PASS, 4-host node_exporter fan-out scrape-ready, P6=16, ready for Phase E (Prometheus + Grafana compose)."

---

## Where we are

### Substrate (dataplane v1) -- COMPLETE
- B2a Postgres+pgvector on Beast: 7/7 gates PASS
- B2b logical replication CK->Beast: 12/12 gates byte-perfect, 5,795 rows
- B1 Garage S3 on Beast: 8/8 gates + 6/6 bonus PASS
- D1 + D2 MCP tools: VERIFIED

### B2b nanosecond invariant: HOLDING
- `control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z healthy/0`
- `control-garage-beast StartedAt=2026-04-27T05:39:58.168067641Z healthy/0`
- ~38+ hours undisturbed across 14+ phases of operational work

### Hardware track
- Switch: Intellinet 560917 at 192.168.1.250 deployed, port-mapped, labeled, configured
- VLAN: deferred (MR60 router can't route VLANs, P5)
- SlimJim: cleaned baseline (sabnzbd/mosquitto-snap/wire-pod/cockpit removed)
- Cortez: Engineering Edge AI workstation, MCP via Tailscale 100.70.77.115
- Pi3: Security DNS Gateway (TBD) on Pi 3B Debian 13 aarch64
- Macmini: hardwired tonight, IP changed `.13` -> `.194` LAN; Tailscale `100.102.87.70` unchanged; MCP allowed_hosts already uses Tailscale, no fix needed

### H1 Observability
- Phase A: ✓ baseline + dependency check
- Phase B: ✓ docker-compose-v2 plugin + jes->docker group
- Side-task: ✓ mariadb disable + UFW 80/443 cleanup (UFW 5->3)
- **Phase C: ✓ CLOSED** -- mosquitto 2.x dual-listener (1883 lo anon + 1884 LAN authed), 5/5 PASS
  - Closes Day 67-cataloged YELLOW #5 (snap.mosquitto listener-config bug)
  - 7 escalations resolved, all banked durable knowledge
  - 4 new P6 lessons: #12 (set+e discipline), #13 (major-version preflight), #14 (client-tooling version capture), #15 (broker-state hygiene for concurrent-CONNECT diagnostics)
  - Standing rule broadened: 4 -> 5 guardrails + carve-out for ops propagation
- **Phase D: ✓ CLOSED** -- node_exporter fan-out CK/Beast/Goliath/KaliPi, 3/3 gates PASS
  - 4 hosts scrape-confirmed from SlimJim (10,864 total node_* metric lines)
  - 2 deviations from spec section 8 D.2 (Goliath UFW inactive + KaliPi UFW not installed) -> A2-refined process-bind via ARGS, both pre-authorized + documented per guardrail 4
  - 3 P5 carryovers banked: Goliath UFW enable / KaliPi UFW install+enable / CK+Beast process-bind symmetry
  - 1 P6 lesson banked: #16 per-target-host operational-readiness preflight matrix for fan-out phases
- **Phase E: NEXT** (observability/ skeleton + Docker Compose stack on SlimJim: Prometheus + Grafana with provisioned dashboards 1860 + 3662, scrape config for 4 fan-out endpoints + SlimJim self-scrape)
- Phase F-I: queued (UFW, healthcheck, smoke, restart safety + ship report)

### Org chart
- Engineering: PD/Cowork ✓
- L&D: Axiom ✓
- Operations: Atlas v0.1 (gated on H1 ship)
- Security: ADDED (KaliPi + Pi3 + future SlimJim IDS)
- CEO-direct: Brand & Market ✓

### P6 lessons banked: 16

---

## Standing rules
1. Per-step review docs in `/home/jes/control-plane/docs/`
2. B2b + Garage nanosecond anchor preservation through every phase
3. Directive command-syntax correction at PD authority (5 guardrails + carve-out + examples)
4. PD escalates via paco_request when uncertain
5. Spec or no action
6. Secrets discipline: REDACTED in review docs, set interactively by CEO
7. P6 #12 set+e for verifier scripts checking exit-coded systemctl outputs

---

## On resume (after Phase D close)

Phase D is shipped to canon (this commit). Phase E is the next deliverable.

1. CEO pulls `git pull origin main` on whichever workstation
2. CEO reads `docs/paco_review_h1_phase_d_node_exporter.md` if desired (~16K, 4-host fan-out evidence + 2 deviations + 3 P5 carryovers + P6 #16 banked + 5 anchor captures)
3. CEO greenlights Paco final confirm -> Phase E start

OR if CEO wants to start fresh in the morning, Phase D is already in canon. No state hangs.

---

## Phase E scope (when ready)

observability/ skeleton + Docker Compose stack on SlimJim per H1 spec section 9:
- /home/jes/observability/ directory layout (compose.yaml + prometheus.yml + grafana provisioning configs)
- Prometheus 2.x via Docker Compose v2 on SlimJim, scrape interval 15s, retention 30d / 10GB cap
- Grafana via same compose, port 3000 LAN-bound, default dashboards 1860 + 3662 auto-provisioned
- Mosquitto stays separate (Phase C, apt-installed not Docker)
- Scrape targets: 4 fan-out node_exporters (CK/Beast/Goliath/KaliPi via :9100) + SlimJim self-scrape (Netdata :19999 + node_exporter localhost) + Prometheus self (:9090)
- Acceptance: compose up healthy / Grafana login + 2 dashboards loaded / Prometheus targets all UP / B2b+Garage anchor preservation

Phase E is mechanical SlimJim-only -- no fan-out, no auth surface beyond Grafana admin password (CEO interactive set), no concurrency. Single-host phase.

---

## What this Phase C taught

Numerically: 7 escalations, 4 P6 lessons banked (#12 set+e + #13 major-version preflight + #14 client-tooling preflight + #15 broker-state hygiene), standing rule broadened from 4 to 5 guardrails + carve-out for operational propagation, decision-matrix-validation discipline added.

Architecturally: substrate held bit-identical through every escalation, every restart, every config edit, every diagnostic test. The discipline of "diagnostic work touches only the layer being diagnosed" worked exactly as designed.

The escalation cost was real (Phase C took longer than planned). The compounding value was realer (4 P6 lessons + standing rule refinements transfer to every future build).

## What this Phase D taught

Numerically: 1 escalation (Goliath UFW + KaliPi sudo + later KaliPi UFW-not-installed surfaced inside the same paco_request), 1 P6 lesson banked (#16 per-target-host operational-readiness preflight matrix), 3 P5 carryovers banked (firewall hardening on Goliath + KaliPi + CK/Beast symmetry), 0 standing rule changes.

Architecturally: "mechanical scope" was true for the install commands (apt + systemctl + UFW) but incomplete for the operational policy environment those commands run in. Goliath UFW state and KaliPi sudo/UFW state were assumed-uniform but were not. The fix was Paco's pre-authorization of A2-refined process-bind for both Goliath AND KaliPi (§4.4 covered the KaliPi-UFW-also-inactive case), so when CEO surfaced KaliPi's `command not found` mid-handoff, the alt directive applied without a second escalation.

The lesson: preflight is the cheap moment to catch operational policy heterogeneity. P6 #16's spec amendment (A.5 in tasks/H1_observability.md) bakes the 6-row preflight matrix into the spec template for future fan-out phases.

-- Paco
