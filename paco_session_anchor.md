# Paco Session Anchor

**Last updated:** 2026-04-29 evening (Day 74 evening)
**Anchor commit:** TBD (this Phase G close-out commit)
**Resume Phrase:** "Day 74 close: H1 Phase G structural 5/5 PASS, 3-ESC arc + 2 standing rules, P6=19, ready for Phase H."

---

## Current state (as of Phase G close)

### Substrate (dataplane v1) -- ALL HOLDING
- **B2a** Postgres+pgvector on Beast -- CLOSED (7/7 gates)
- **B2b** logical replication CK->Beast -- CLOSED (12/12 gates)
- **B1**  Garage S3 on Beast -- CLOSED (8/8 gates + 6/6 bonus)
- **D1** MCP Pydantic limits -- VERIFIED
- **D2** homelab_file_write tool -- VERIFIED
- **B2b nanosecond anchor**: `2026-04-27T00:13:57.800746541Z` -- holding through 18+ phases (~52 hours)
- **Garage anchor**: `2026-04-27T05:39:58.168067641Z` -- holding through 18+ phases

### H1 progression
- **Phase A** (baseline + UFW orphans) -- CLOSED (3/3)
- **Phase B** (compose v2 + docker group) -- CLOSED (4/4)
- **Phase C side-task** (UFW delete syntax) -- CLOSED (3/3)
- **Phase C** (mosquitto 2.x dual-listener) -- CLOSED (5/5, 7-ESC arc)
- **Phase D** (node_exporter fan-out CK/Beast/Goliath/KaliPi) -- CLOSED (3/3)
- **Phase E** (observability/ skeleton + compose + provisioning) -- CLOSED (4/4)
- **Phase F** (UFW for SlimJim 9090+3000) -- CLOSED (3/3)
- **Phase G** (compose up + healthcheck) -- **STRUCTURAL CLOSED 5/5** (Gates 3+4 by design land at Phase H CEO browser tests)
  - 3 ESCs resolved: Path A (data-dir UID), Path X-only (secret-file UID, Path Y revoked), Path 1 + extension (Bridge NAT for 9100 + 19999)
  - obs-prometheus + obs-grafana: running healthy, Restarts=0
  - Prometheus targets: 7/7 UP
  - UFW: 9 rules (was 7 pre-Phase-G)

### Phase G observability stack final state on SlimJim

- compose.yaml: md5 `db89319cad27c091ab1675f7035d7aa3` (Phase F state, short-syntax secrets per Path X-only ruling)
- grafana-admin.pw: 600 472:472 11 bytes
- prom-data: 700 65534:65534
- grafana-data: 700 472:472
- obs-prometheus: prom/prometheus:v2.55.1 (sha256:2659f4c2...) StartedAt `2026-04-29T21:27:50.229362232Z` health=healthy
- obs-grafana: grafana/grafana:11.3.0 (sha256:a0f88123...) StartedAt `2026-04-29T21:27:56.139191606Z`

### P6 lessons banked: 19
- #1-#11 prior sessions
- #12 Day 73 evening: `set +e` discipline for verifier scripts on exit-coded systemctl outputs
- #13 Day 73 evening: mosquitto 2.x major-version preflight (snap broken from 1.x, apt is supported install vector)
- #14 Phase C close-out: preflight client-tooling version capture catches matrix-collision bugs
- #15 Phase C close-out: broker-state hygiene for concurrent-CONNECT diagnostics (mosquitto restart as first-line discriminator)
- #16 Phase D close-out: per-target-host operational-readiness preflight matrix for fan-out phases
- #17 Phase E corrections: spec text referencing upstream-product env var conventions must be cross-checked at directive-author time (single vs double underscore class)
- **#18** Phase G ESC #1+#3: first-boot of stateful containers with bind-mount data + secret resources requires UID alignment between host owner and container default UID
- **#19** Phase G ESC #3: compose v2 secrets long-syntax `uid`/`gid`/`mode` are swarm-mode-only; standalone compose discards values with warning

### Standing rules updates (Phase G)

- **compose-down during active ESC pre-authorized** (banked at commit `e85b256`, section 2A of `feedback_directive_command_syntax_correction_pd_authority.md` this commit)
- **Path 1 generalization** (banked at commit `3aac8b9`, documented in spec section 11 Phase G this commit)
- **Bidirectional one-liner format spec** for both handoff files (banked at commit `e85b256`, `docs/feedback_paco_pd_handoff_protocol.md` updated)

### Open specs / phases
- **H1 Phase H** (Grafana smoke + LAN smoke from CK + CEO browser Gate 3+4) -- ready, gated on Paco confirm + GO
- **H1 Phase I** (restart safety + ship report) -- gated post-H
- **H2 Cortez integration** -- not drafted (gated post-H1)
- **H3 Pi3 DNS Gateway** -- not drafted (gated post-H1)
- **H4 VLAN** -- DEFERRED (router-replacement-gated)
- **Atlas v0.1** -- not drafted (gated post-hardware-org-complete)

### P5 carryovers
- Phase D's 3 P5s (Goliath UFW enable, KaliPi UFW install + enable, CK + Beast process-bind symmetry)
- Phase G new P5: Grafana admin password rotation helper script (defer to v0.2)
- Phase G new P5: mixed-ownership grafana-data subdirs from ESC #2/#3 cycle (`dashboards` root:root, `plugins` 472:root) -- benign, post-Phase-H stable-state cleanup
- `docs/paco_response_h1_phase_c_hypothesis_f_test.md` -- still untracked (not PD-authored, surfaced previously, low-priority)

### Org chart
- COO: Paco ✓
- Engineering: PD/Cowork ✓ + Cortez/JesAir/Macmini
- L&D: Axiom ✓
- Operations: Atlas v0.1 (TBD, gated on H1 ship)
- Security: KaliPi + Pi3 + future SlimJim IDS (no agent head)
- CEO-direct: Brand & Market ✓

---

## On resume

1. **Paco confirms Phase G** (independent verification of structural 5-gate from fresh shell against `paco_review_h1_phase_g_compose_up.md`).
2. **Phase H GO authorization** (Grafana web smoke + LAN smoke from CK + CEO browser Gate 3 + Gate 4).
3. PD executes Phase H per spec section 12.
4. Phase H close-out commit (single fold pattern).
5. Phase I (restart safety + ship report).

---

## Notes for Paco

- 3-ESC arc closed cleanly via spec-or-no-action discipline + bidirectional one-liner protocol effectiveness.
- compose-down inline auth pattern from ESC #1/#2/#3 banked as standing rule (carve-out 2A).
- Path Y authorization revocation (commit `e85b256`) was a healthy correction -- spec said long-syntax was the answer, runtime proved otherwise. Discipline held: PD didn't try Path X without ratification despite obvious mechanical pressure.
- Path 1 generalization (commit `3aac8b9`) eliminated need for ESC #4 on netdata; PD self-auth applies for any future bridge-NAT scrape target.
- B2b + Garage nanosecond invariants holding through 18+ phases / ~52 hours / 3 compose down-up cycles / compose.yaml edit + revert / 2 chowns / 2 UFW additions. Discipline scaled.
- One untracked `paco_response_h1_phase_c_hypothesis_f_test.md` orphan persists; PD did not author. Surface for Paco review at convenience.
