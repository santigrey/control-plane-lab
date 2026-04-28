# CEO Quick Checklist

**Updated:** 2026-04-28 (Day 73)
**Anchor commit:** TBD
**Canonical:** `/home/jes/control-plane/CEO_CHECKLIST.md` on CiscoKid
**iCloud copy:** `~/iCloud/AI/Santigrey/CEO_CHECKLIST.md`

---

## Status banner

| Layer | State |
|---|---|
| **Substrate (dataplane v1)** | ✅ COMPLETE |
| **Hardware foundation** | 🔧 IN PROGRESS (switch deployed, H1 next) |
| **Atlas (Operations agent)** | ⏸ GATED on hardware completion |
| **B2b nanosecond anchor** | ✅ holding 8+ phases |

---

## DONE this session (Day 72-73)

- B1 Garage S3 substrate -- CLOSED (8/8 gates + 6/6 bonus)
- B2b logical replication -- CLOSED earlier (12/12 gates byte-perfect)
- D2 MCP file_write tool -- VERIFIED EMPIRICALLY (~30+ live calls)
- Cortez audit -- HP OmniBook X Flip, 115 TOPS NPU+GPU. Role: Engineering Edge AI workstation
- Pi3 fleet-confirmed -- Pi 3B 1GB Debian 13. Role TBD: Security DNS Gateway
- Switch acquired + deployed -- Intellinet 560917 at .250, port map established
- SlimJim cleanup -- removed sabnzbd, mosquitto-snap, wire-pod (29k crash loop), cockpit
- H1 observability spec -- DRAFTED at tasks/H1_observability.md
- Org chart -- Security department added (4th)
- P6 lessons -- 11 banked

---

## Pending CEO action

- [ ] Ratify H1 spec -> green-light PD Phase A start
- [ ] (later) Pi3 role confirm: DNS Gateway w/ Pi-hole + Unbound + Tailscale subnet router
- [ ] (Wednesday) MoCA splitter + filter arrive -- separate physical wiring task
- [ ] (future) Router replacement evaluation if VLAN segmentation desired

---

## NOW (waiting on PD)

- H1 SlimJim observability
  - Phase A: baseline + dependency check (Docker Compose v2 plugin install, jes->docker group)
  - Phase B: docker-compose plugin
  - Phase C: mosquitto 2.x apt install + dual-listener config (closes Day 67 YELLOW #5)
  - Phase D: node_exporter on CK/Beast/Goliath/KaliPi
  - Phase E: observability dir tree + compose.yaml + prometheus.yml + Grafana provisioning
  - Phase F: UFW (Prometheus 9090, Grafana 3000, Mosquitto 1884)
  - Phase G: docker compose up + healthcheck poll
  - Phase H: Grafana datasource + dashboards + LAN smoke from CK
  - Phase I: restart safety + ship report (15-gate scorecard)

## NEXT (after H1 ships)

- H2 Cortez integration spec drafting (OpenSSH already ✓, MCP allowed_hosts already ✓ on Tailscale, Tailscale resilience hardening, NPU eval)
- H3 Pi3 DNS Gateway spec drafting (Pi-hole + Unbound + Tailscale subnet router)
- (parallel after H1.B baseline lands)

## DEFERRED to v0.2

- Atlas v0.1 (full agent platform, gated on hardware org complete)
- VLAN segmentation (MR60 router can't route between VLANs)
- JesAir role evaluation (currently mobile thin client)
- SlimJim Wazuh/Suricata IDS (Security dept tooling)
- Per-bucket S3 keys, TLS for S3, lifecycle/versioning, DOCKER-USER hardening
- Family Office charter
- Router replacement (UDM-SE / OPNsense)
- Sub-agent definitions (Mr Robot for Security, etc.)

---

## How to use

- Executive view, updated by Paco at session boundaries.
- Detailed audit lives in CHECKLIST.md.
- Glance before each session.
