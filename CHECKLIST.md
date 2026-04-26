# Santigrey Enterprises -- Master Checklist

**Owner:** Paco (COO)
**Source of truth:** This file. All other docs feed it; it feeds none.
**Location:** iCloud `/AI/Santigrey/CHECKLIST.md` (primary), mirrored to CiscoKid `/home/jes/control-plane/CHECKLIST.md`
**Last updated:** 2026-04-26 late-morning (Day 72)
**Update rule:** Paco updates after every closed task or every CEO direction change. Status legend: `[ ]` open, `[~]` in progress, `[x]` done, `[!]` blocked, `[-]` deferred.

---

## P0 -- URGENT (external deadline)

- [ ] **Capstone lane decision** for Per Scholas instructor meeting Monday 2026-04-27. Three lanes documented (Path A: Alexandra-derived RAG slice / Path B: rubric-suggested project / Path C: both as instructor options). CEO has all day Sunday + most of Monday before meeting. **Owner: CEO.**

## P1 -- ACTIVE WORK (this session)

- [x] D1 -- Lift four Pydantic input limits in `mcp_server.py` (PD shipped; Paco gate PASS). Code commit `3cb303c`, session commits `b43966e` + `1d9cbe8`.
- [x] **CAPACITY_v1.1** -- DRAFT shipped 2026-04-26 AM. Three v1.0 errors corrected (phantom MCP migration removed, fictional iMessage/HomeKit bridges reclassified as future-conditional, Mac mini scope tightened). 133 lines, hash 1de8a2cc0f01cd7b32e3170bf2ab4e82. Awaiting CEO ratification.
- [x] **Mac mini scope lock** -- RATIFIED by CEO 2026-04-26. Principle locked: scope drives workflow, not reverse. Mac mini = Apple-bound infrastructure only + remains CEO daily-driver workstation (separate concern outside org chart). Footprint verified: Claude Desktop / Cowork host, AgentOS Refresh, Tailscale, OpenSSH. No iMessage/HomeKit bridges, no MCP termination.

## P2 -- DATA PLANE SEQUENCE (post-D1)

- [ ] **D2** -- add `homelab_file_write` MCP tool. Eliminates chunked-cat workaround. Spec not yet drafted. **Owner: Paco spec, PD execute.**
- [ ] **D3** -- add `homelab_file_transfer` MCP tool (host-to-host). **Owner: Paco spec, PD execute.**
- [ ] **D4** -- streaming output support (move off `subprocess.run capture_output=True`). **Owner: Paco spec, PD execute.**
- [ ] **A** -- discipline shift: rsync/HTTP/native replication for bulk; MCP for control only. No code change, just standing rule. **Owner: Paco enforce, PD honor.**
- [ ] **B1** -- MinIO on Beast (S3-compatible object store). **Owner: Paco spec, PD execute.**
- [ ] **B2** -- Postgres logical replication CiscoKid -> Beast. **Owner: Paco spec, PD execute.**
- [-] **C** -- cable up idle high-speed ports. Defer until 1 GbE actually saturates.
- [-] **E** -- replace MCP-over-SSH with MCP-over-HTTP-API. Defer one quarter.

## P3 -- HARDWARE ORG REDISTRIBUTION (after CAPACITY_v1.1 ratifies)

- [ ] **SlimJim** -- add Prometheus + Grafana, deploy node_exporter on every node. **Owner: Paco spec, PD execute.**
- [ ] **Beast** -- becomes Atlas's home (charter revision from CAPACITY_v1.0). Build deferred until B1+B2 land. **Owner: Paco spec, PD execute.**
- [-] **SlimJim** -- Wazuh/Suricata security monitoring. Deferred (needs careful tuning).
- [ ] **Pi3** -- assign role. Currently registered (192.168.1.139, sloanzj) but unprobed and unassigned. **Owner: CEO direction needed.**
- [ ] **JesAir** -- evaluate beyond thin client (Apple Silicon, capable of more). **Owner: CEO direction needed.**
- [ ] **Cortez** -- evaluate beyond thin client (NPU-equipped per CEO flag). **Owner: CEO direction needed.**
- [ ] **Cortez** -- Tailscale resilience hardening (Day 69 carryover; auto-restart + boot-start + DERP keepalive). **Owner: PD execute when Cortez online.**

## P4 -- ORG CHARTERS

- [ ] **CHARTERS_v0.1.md ratification** -- six role charters + Alexandra platform charter. Atlas-on-Beast revision must land in canon. **Owner: CEO ratify.**
- [ ] **PD title communication** -- announce Head of Engineering scope to PD. Deferred until charter ratification. **Owner: CEO + Paco.**
- [ ] **Family Office charter** -- explicitly drafted or explicitly kept informal. **Owner: CEO direction.**
- [ ] **Sub-agent definitions** inside each department (Mr Robot, Mercury, future agents). **Owner: Paco draft.**
- [ ] **Inter-department SOPs** -- how Engineering hands work to Operations, etc. **Owner: Paco draft.**
- [ ] **Brand & Market quarterly plan** -- separate strategy document. **Owner: CEO + Paco.**

## P5 -- DAY 69 CARRYOVERS (still pending)

- [ ] phase-4-sanitizer rebase + step 6/12 resume. **Owner: PD.**
- [ ] Methodology doc "verify what depends on a credential." **Owner: Paco draft.**
- [ ] Credentials inventory doc. **Owner: Paco draft.**
- [ ] Calendar reminder 2026-05-24 -- drop `_retired_` tables. **Owner: CEO add to calendar.**
- [ ] Cortez `cortez_AI_Operator` PAT (regenerated, unused) -- delete on GitHub at convenience. **Owner: CEO.**

## P6 -- METHODOLOGY (Paco self-improvement)

- [ ] Codify into anchor: spec template for live-service tasks must answer "is restart safe right now?" and "what does the health check actually mean?" -- D1 surfaced both gaps. **Owner: Paco.**
- [ ] Codify rule: **no claim about state without source verification first.** Already in anchor; needs reinforcement after Day 70 + Day 72 AM corrections. **Owner: Paco.**

---

## Closed (audit trail)

- [x] **2026-04-25 Day 70 AM** -- Org chart locked v0.4 (3 departments + 2 CEO-direct + Alexandra platform).
- [x] **2026-04-25 Day 70 AM** -- CHARTERS_v0.1.md drafted (164 lines, 7 charters).
- [x] **2026-04-25 Day 70 PM** -- Hardware audit completed across all reachable nodes.
- [x] **2026-04-25 Day 70 PM** -- MCP fabric diagnosed (control plane only, no data plane). Five-path fix sequence chosen: D -> A -> B -> C(maybe) -> E(deferred).
- [x] **2026-04-25 Day 70 PM** -- CAPACITY_v1.0.md drafted (104 lines, DRAFT). Superseded by v1.1 once corrections apply.
- [x] **2026-04-25 Day 70 PM** -- D1 task spec drafted, CEO-approved, queued for PD.
- [x] **2026-04-26 Day 71** -- D1 SHIPPED by PD (commit `3cb303c`). Paco verification gate PASS.
- [x] **2026-04-26 Day 72 AM** -- Mac mini footprint verified. MCP migration confirmed phantom (already on CiscoKid). Three v1.0 errors identified for v1.1 correction.
- [x] **2026-04-26 Day 72** -- CAPACITY_v1.1.md drafted (133 lines, hash 1de8a2cc0f01cd7b32e3170bf2ab4e82). Three v1.0 errors corrected. Saved to iCloud + mirrored to CiscoKid. v1.0 retained as superseded backup.
- [x] **2026-04-26 Day 72** -- Mac mini scope ratified. Principle locked: scope drives workflow, not reverse.

---

## How to use this checklist

- **Every Paco session opens with a checklist read.** SESSION.md is history; CHECKLIST.md is current state.
- **Every closed task moves to the audit trail with a date.**
- **Every new commitment lands at the right priority tier with an explicit owner.**
- **No work happens that isn't on this list.** If it should happen, add it. If it shouldn't, don't.

