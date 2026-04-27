# CEO Quick Checklist

**Updated:** 2026-04-27 (Day 72/73)
**Anchor commit:** `7ca7563` on `origin/main`
**Canonical:** `/home/jes/control-plane/CEO_CHECKLIST.md` on CiscoKid
**iCloud copy:** `~/iCloud/AI/Santigrey/CEO_CHECKLIST.md` (read-only convenience)

---

## Status banner

| Layer | State |
|---|---|
| **Substrate (dataplane)** | ✅ COMPLETE v1 |
| **Hardware foundation** | 🔧 IN PROGRESS |
| **Atlas (Operations agent)** | ⏸ GATED on hardware |
| **May 2026 placement target** | 🎯 ~4-6 weeks runway |

---

## ✅ DONE — substrate phase

- [x] **B2a** — Postgres 16 + pgvector on Beast (7/7 gates)
- [x] **B2b** — Logical replication CiscoKid → Beast (12/12 gates, 5,795 rows byte-perfect)
- [x] **B1**  — Garage v2.1.0 S3 substrate on Beast (8/8 gates + 6/6 bonus)
- [x] **D1**  — MCP Pydantic limits lifted (verified)
- [x] **D2**  — `homelab_file_write` tool (verified live this session)
- [x] Charters v0.1 ratified, Capacity v1.1 ratified
- [x] 11 P6 lessons banked

---

## 🔧 NOW — hardware completion

### Pending CEO action (today)
- [ ] **Order managed switch** — 24-port, my ruling: UniFi USW-Pro-24-PoE ($799) or USW-Pro-24 non-PoE ($379)
- [ ] **Ratify Security department** — adding 4th dept under COO; KaliPi + Pi3 + (future) SlimJim IDS
- [ ] **Confirm Pi3 role** — DNS Gateway (Pi-hole + Unbound + DoT)

### Specs to draft (Paco, parallel-while-you-shop)
- [ ] **H1** — SlimJim observability (Prometheus + Grafana + node_exporter fleet-wide)
- [ ] **Charter 7** — Security department formal
- [ ] **Side-commit** — D2 verification close + CHECKLIST stamp catchup (cosmetic)

### Specs to execute (PD, gated on H1 baseline)
- [ ] **H1.A→D** — Observability deploy + dashboards
- [ ] **H2** — Cortez integration (OpenSSH, MCP allowed_hosts, Tailscale resilience, NPU eval)
- [ ] **H3** — Pi3 → DNS Gateway (Pi-hole + Unbound + Tailscale subnet router)
- [ ] **H4** — VLAN segmentation (post-switch-arrival)

---

## ▶ NEXT — Atlas v0.1

Unblocks when hardware completes. Architecture already planned (Option 3 ratified):
- 9 phases A-I
- Multi-step agent with task queue, MCP fan-out, vector memory, scheduling, 3-tier approval gates
- ~15-gate scorecard
- Capstone alignment handled separately by CEO

---

## ⏸ DEFERRED to v0.2

- JesAir role evaluation (thin-client → secondary?)
- SlimJim Wazuh/Suricata IDS/IPS (per Capacity_v1.1)
- Per-bucket S3 keys, TLS for S3, lifecycle/versioning, DOCKER-USER hardening
- Sub-agent definitions (Mr Robot for Security, etc.)
- Family Office charter
- Brand & Market quarterly plan

---

## How to use this file

- This is the **executive view**. Updated by Paco at session boundaries.
- Detailed audit trail lives at `CHECKLIST.md` (long-form, every step).
- This is the deliverable to glance at before each working session.
- Decisions awaiting CEO are in the **Pending CEO action** block above.

**Two questions to ask Paco any time:** (1) what's done, (2) what's next.
This file answers both in 30 seconds.

---

## Recent: 2026-04-27 hardware audit

**Cortez** (online, audited): HP OmniBook X Flip Laptop, Intel Core Ultra 7 258V (Lunar Lake), **AI Boost NPU + Arc 140V GPU = 115 TOPS combined**, 32GB RAM, 1.7TB free, OpenSSH ✓ + Tailscale ✓. **Role ratified: Engineering — Edge AI workstation.** MCP allowed_hosts updated to Tailscale `100.70.77.115` (LAN .240 was dead).

**Pi3** (online, fleet-confirmed): Raspberry Pi 3 Model B Rev 1.2, Debian 13 trixie aarch64, 1GB RAM, 50GB free SD. **Sufficient for: Pi-hole + Unbound + Tailscale subnet router (DNS Gateway role).** Not viable for VPN exit node (100Mbps NIC). MCP via LAN `192.168.1.139` confirmed; Tailscale `100.71.159.102` available as backup path.

**D2** (`homelab_file_write` MCP tool): empirically verified — ~30 successful live calls this session. D2 line 23 PASS, status now fully closed.

**Atlas org chart amendment:** Cortez is Engineering, NOT Security. Security dept owns KaliPi (pentest) + Pi3 (DNS Gateway) + future SlimJim IDS. Engineering owns Cortez + JesAir + Mac mini + dev access to Beast/Goliath.
