# Paco Session Anchor -- JesAir Resume

**Last updated:** 2026-04-29 / Day 74 (H1 Phase E close)
**Last commit:** Phase E 4/4 PASS close-out (see git log for SHA) -- supersedes Phase D close-out
**Resume phrase:** "Day 74 close: H1 Phase E 4/4 PASS structural, observability/ skeleton landed (config-only, containers DOWN until Phase G), 1 spec discrepancy flagged for Paco ruling (Grafana env var single-vs-double underscore), P6=16, ready for Phase F (UFW for SlimJim)."

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
- **Phase E: ✓ CLOSED** -- observability/ skeleton + compose.yaml + prometheus.yml + grafana provisioning, 4/4 gates PASS structural
  - 6 config files written + 1 placeholder grafana-admin.pw chmod 600 (CEO writes content pre-Phase-G)
  - Both Docker images pulled + digest-pinned in compose.yaml: prom/prometheus@sha256:2659f4c2... + grafana/grafana@sha256:a0f88123...
  - 5th node_exporter installed on SlimJim itself, UFW rule [5] for 9100 from 127.0.0.1 (spec literal)
  - 1 spec discrepancy flagged: Grafana env var `GF_SECURITY_ADMIN_PASSWORD_FILE` (single _) vs canonical Grafana 11.x `__FILE` (double _); PD self-caught under guardrail 5 + reverted to spec literal; awaiting Paco ruling at review
  - 1 Phase G concern carry-forward: Prom container bridge-NAT source IP vs UFW [5] from 127.0.0.1 may not match at runtime; will surface at Phase G smoke if real
- **Phase F: NEXT** (UFW for SlimJim per spec section 10 -- 9090/tcp + 3000/tcp LAN-allow for human access)
- Phase G-I: queued (compose up + healthcheck, Grafana smoke + LAN smoke, restart safety + ship report)

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

## Phase F scope (when ready)

UFW for SlimJim per H1 spec section 10:
- ufw allow 9090/tcp from 192.168.1.0/24 (Prometheus web UI human access)
- ufw allow 3000/tcp from 192.168.1.0/24 (Grafana web UI human access)
- May or may not need extra rules for Prom-container scrape paths -- TBD when reading spec section 10 + addressing Phase G concern (Prom container bridge-NAT vs node_exporter on SlimJim itself)
- Acceptance: UFW count goes 5 -> 7 (or higher if Phase G concern needs resolving here); B2b + Garage anchor preservation

Phase F is mechanical SlimJim-only -- straight UFW rule additions. No auth surface change beyond LAN-allow scope. No concurrency.

---

## What this Phase C taught

Numerically: 7 escalations, 4 P6 lessons banked (#12 set+e + #13 major-version preflight + #14 client-tooling preflight + #15 broker-state hygiene), standing rule broadened from 4 to 5 guardrails + carve-out for operational propagation, decision-matrix-validation discipline added.

Architecturally: substrate held bit-identical through every escalation, every restart, every config edit, every diagnostic test. The discipline of "diagnostic work touches only the layer being diagnosed" worked exactly as designed.

The escalation cost was real (Phase C took longer than planned). The compounding value was realer (4 P6 lessons + standing rule refinements transfer to every future build).

## What this Phase D taught

Numerically: 1 escalation (Goliath UFW + KaliPi sudo + later KaliPi UFW-not-installed surfaced inside the same paco_request), 1 P6 lesson banked (#16 per-target-host operational-readiness preflight matrix), 3 P5 carryovers banked (firewall hardening on Goliath + KaliPi + CK/Beast symmetry), 0 standing rule changes.

Architecturally: "mechanical scope" was true for the install commands (apt + systemctl + UFW) but incomplete for the operational policy environment those commands run in. Goliath UFW state and KaliPi sudo/UFW state were assumed-uniform but were not. The fix was Paco's pre-authorization of A2-refined process-bind for both Goliath AND KaliPi (§4.4 covered the KaliPi-UFW-also-inactive case), so when CEO surfaced KaliPi's `command not found` mid-handoff, the alt directive applied without a second escalation.

The lesson: preflight is the cheap moment to catch operational policy heterogeneity. P6 #16's spec amendment (A.5 in tasks/H1_observability.md) bakes the 6-row preflight matrix into the spec template for future fan-out phases.

## What this Phase E taught

Numerically: 0 escalations, 0 new P6 lessons, 0 new P5 carryovers, 0 standing rule changes -- but 1 spec discrepancy surfaced + 1 Phase G concern banked (both for Paco review-time ruling).

Architecturally: the 5-guardrail rule (with carve-out) worked at minimum-friction scale this phase. PD reflexively typed the canonical Grafana 11.x `__FILE` env var convention on first compose.yaml write -- caught it within seconds as an auth-surface correction (Grafana admin password mechanism), reverted to spec literal `_FILE` (single underscore) before any other operation, and flagged for Paco ruling in the review. No paco_request roundtrip needed; the discipline showed up in the typo-correction caught and reverted in real time. This is what guardrail 5 looks like in steady-state operation: not just for big config changes (Phase C per_listener_settings), but for every auth-related line PD types.

Second observation: the spec section 9 prometheus.yml + UFW config implies Prom-container-on-SlimJim scrapes node-exporter-on-SlimJim via 192.168.1.40:9100 with UFW filter from 127.0.0.1. Linux local routing optimizes same-host LAN-IP scrapes via lo, so host-process curl works. But container scrapes go through Docker bridge NAT, source IP becomes bridge gateway (172.17.0.1), UFW filter from 127.0.0.1 won't match. This is a Phase G concern banked at Phase E time -- the architectural detail surfaces during config writes, before runtime, where it's cheap to address.

The lesson: config-only phases ARE worth doing carefully; they surface runtime concerns at write-time when fixing is cheap.

-- Paco
