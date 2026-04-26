# Santigrey Enterprises -- Master Checklist

**Owner:** Paco (COO)
**Source of truth:** This file. All other docs feed it; it feeds none.
**Location:** Primary on CiscoKid `/home/jes/control-plane/CHECKLIST.md` + GitHub origin/main (canonical via git push). iCloud `/AI/Santigrey/CHECKLIST.md` is a CEO-convenience read-only copy, no longer Paco-managed (canon-flip 2026-04-26 Day 72).
**Last updated:** 2026-04-26 evening (Day 72) -- B2a closed; CAPACITY_v1.1 + CHARTERS_v0.1 + iCloud canon-flip ratified; B2b ratified, queued for PD
**Update rule:** Paco updates after every closed task or every CEO direction change. Status legend: `[ ]` open, `[~]` in progress, `[x]` done, `[!]` blocked, `[-]` deferred.

---

## P0 -- URGENT (external deadline)

- [ ] **Capstone lane decision** for Per Scholas instructor meeting Monday 2026-04-27. Three lanes documented (Path A: Alexandra-derived RAG slice / Path B: rubric-suggested project / Path C: both as instructor options). CEO has all day Sunday + most of Monday before meeting. **Owner: CEO.**

## P1 -- ACTIVE WORK (this session)

- [x] D1 -- Lift four Pydantic input limits in `mcp_server.py` (PD shipped; Paco gate PASS). Code commit `3cb303c`, session commits `b43966e` + `1d9cbe8`.
- [x] **CAPACITY_v1.1** -- DRAFT shipped 2026-04-26 AM, RATIFIED 2026-04-26 PM (Day 72) by CEO. Three v1.0 errors corrected (phantom MCP migration removed, fictional iMessage/HomeKit bridges reclassified as future-conditional, Mac mini scope tightened). 133 lines.
- [x] **Mac mini scope lock** -- RATIFIED by CEO 2026-04-26. Principle locked: scope drives workflow, not reverse. Mac mini = Apple-bound infrastructure only + remains CEO daily-driver workstation (separate concern outside org chart). Footprint verified: Claude Desktop / Cowork host, AgentOS Refresh, Tailscale, OpenSSH. No iMessage/HomeKit bridges, no MCP termination.

## P2 -- DATA PLANE SEQUENCE (post-D1)

- [x] **D2** -- add `homelab_file_write` MCP tool. SHIPPED 2026-04-26 (code commit `faa0d6a`, session commit `8e602a7`). All 6 gate tests PASS: atomic write+read roundtrip (unicode + smart quotes + newlines), mkdir_parents on path with space, create-mode collision rejected, file_mode 0644 + 0600 verified, binary=True 32 bytes 0x00-0x1f byte-perfect (sha256 630dcd29...10dd canonical). PD `str_strip_whitespace` omission ratified (correctness over consistency).
- [ ] **D3** -- add `homelab_file_transfer` MCP tool (host-to-host). **Owner: Paco spec, PD execute.**
- [ ] **D4** -- streaming output support (move off `subprocess.run capture_output=True`). **Owner: Paco spec, PD execute.**
- [x] **A** -- discipline shift: rsync/HTTP/native replication for bulk; MCP for control only. RATIFIED by CEO 2026-04-26 as Rule 1 in `docs/STANDING_RULES.md` (3989 bytes, hash 141f04c087c78d2d8b1e02ffa8305cac, 68 lines). Standing rule now effective; all six plan-level decisions verified and approved as-is.
- [ ] **B1** -- MinIO on Beast (S3-compatible object store). **Owner: Paco spec, PD execute.**
- [x] **B2a** -- install PostgreSQL on Beast (Docker pgvector/pgvector:pg16, greenfield). SHIPPED 2026-04-26 by PD (ship report at `/home/jes/postgres-beast/B2a_ship_report.md` on Beast, md5 b9d862fcebbe78317a0081d052121294). Paco independent gate PASS 7/7 from fresh shell. PG 16.13 + pgvector 0.8.2 healthy on 127.0.0.1:5432. Two Paco-authorized deviations documented (Compose v5.1.3 plugin bootstrap; health-poll replacing sleep 15). **Owner: Paco spec, PD execute. CLOSED.**
- [~] **B2b** -- logical replication CiscoKid -> Beast (WAL change + port rebind + pg_hba + UFW + schema bootstrap + publication + subscription + slot). RATIFIED 2026-04-26 by CEO (all 4 picks Option 1: pg_hba bind-mount, accept ~5-30s downtime, admin/adminpass, pg_dump+scp). Spec at `tasks/B2b_logical_replication.md` (19341 bytes / 356 lines, hash via md5sum). 12 acceptance gates. Queued for PD via Cowork; per-phase paco_review docs to follow. **Owner: Paco spec, PD execute. Awaiting PD Phase A capture.**
- [-] **C** -- cable up idle high-speed ports. Defer until 1 GbE actually saturates.
- [-] **E** -- replace MCP-over-SSH with MCP-over-HTTP-API. Defer one quarter.

## P3 -- HARDWARE ORG REDISTRIBUTION (CAPACITY_v1.1 ratified; redistribution unblocked)

- [ ] **SlimJim** -- add Prometheus + Grafana, deploy node_exporter on every node. **Owner: Paco spec, PD execute.**
- [ ] **Beast** -- becomes Atlas's home (charter revision from CAPACITY_v1.0). Build deferred until B1+B2 land. **Owner: Paco spec, PD execute.**
- [-] **SlimJim** -- Wazuh/Suricata security monitoring. Deferred (needs careful tuning).
- [ ] **Pi3** -- assign role. Currently registered (192.168.1.139, sloanzj) but unprobed and unassigned. **Owner: CEO direction needed.**
- [ ] **JesAir** -- evaluate beyond thin client (Apple Silicon, capable of more). **Owner: CEO direction needed.**
- [ ] **Cortez** -- evaluate beyond thin client (NPU-equipped per CEO flag). **Owner: CEO direction needed.**
- [ ] **Cortez** -- Tailscale resilience hardening (Day 69 carryover; auto-restart + boot-start + DERP keepalive). **Owner: PD execute when Cortez online.**

## P4 -- ORG CHARTERS

- [x] **CHARTERS_v0.1.md ratification** -- six role charters + Alexandra platform charter. RATIFIED 2026-04-26 Day 72 by CEO. Atlas-on-Beast revision applied at ratification per CAPACITY_v1.1 (Atlas builds on Beast for Postgres replica + MinIO + embeddings + tool execution; inference offloaded to Goliath Qwen 2.5 72B over LAN). Pulled from iCloud to CiscoKid as part of iCloud canon-flip; now canonical at `/home/jes/control-plane/CHARTERS_v0.1.md` on CiscoKid + GitHub. 11074 bytes, 7 charters + Platform charter + Ratification audit section.
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

- [ ] Codify into anchor: spec template for live-service tasks must answer (1) "is restart safe right now?", (2) "what does the health check actually mean?", AND (3) "where does the PD-to-Paco report land and how is it shared (file path, naming convention, transmission mechanism)?" -- D1 surfaced (1)+(2); D2 surfaced (3) (CEO had to prompt PD for the report after ship). **Owner: Paco.**
- [ ] Codify rule: **no claim about state without source verification first.** Already in anchor; needs reinforcement after Day 70 + Day 72 AM corrections. **Owner: Paco.**
- [ ] Codify into spec template: deferred-restart pattern MUST bundle verification into the same nohup subshell, writing to `/tmp/<task>_verify.out`. PD surfaced this from D2 -- avoids the cgroup-death race that otherwise requires fishing verification out of a follow-up MCP call (which itself fails because the channel just bounced). **Owner: Paco.**

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
- [x] **2026-04-26 Day 72** -- D2 spec drafted (213 lines, hash 137cabe0c04165817029e0d6a49e96a1). CEO-approved D-A-B-C-E sequence within data plane: D2 first (highest leverage), then A discipline rule, then B2 (Atlas hard prereq), then D3, B1, D4, then Atlas. Spec queued for PD. Saved to iCloud + CiscoKid as DRAFT.
- [x] **2026-04-26 Day 72** -- D2 SHIPPED by PD (code commit `faa0d6a`, session commit `8e602a7`). Paco gate PASS (all 6 tests). PD methodology contributions: (a) bundled-verification deferred-restart pattern, now standard; (b) `str_strip_whitespace` omission ratified for content fidelity. Three methodology lessons captured into P6.
- [x] **2026-04-26 Day 72** -- A drafted as Rule 1 in new canon doc `docs/STANDING_RULES.md` (3989 bytes, 68 lines, hash 141f04c087c78d2d8b1e02ffa8305cac). MCP-fabric-is-control-not-bulk principle codified with explicit in/out scope, transport routing rules, and violation handling. Awaiting CEO ratification.
- [x] **2026-04-26 Day 72** -- A RATIFIED by CEO as-is (no rework). All six plan-level decisions verified retroactively (3 already-flagged + 3 surfaced for measure: new doc choice, storage location pattern, 1MB tool-output threshold). Rule 1 (MCP fabric is for control, not bulk data) effective immediately. P2 data plane advances to B2 next.
- [x] **2026-04-26 Day 72** -- B2 shallow probe complete (commit `a23caf1`, 113-line investigation report). Q3 resolved -> split into B2a + B2b. Q4-Q7 ratified by CEO with Paco picks: Q4=C (public+agent_os, exclude mercury), Q5=A (Docker pgvector/pgvector:pg16), Q6=A (LAN rebind + layered ACLs), Q7=C (bundle WAL change into B2b). B2a spec drafted (6186 bytes, greenfield Postgres on Beast, no CiscoKid dependency at install time). Awaiting CEO ratification.
- [x] **2026-04-26 Day 72** -- B2a spec RATIFIED by CEO as-is (no rework). Cowork prompt provided; queued for PD execution. Awaiting ship report at `/home/jes/postgres-beast/B2a_ship_report.md` on Beast.
- [x] **2026-04-26 Day 72** -- B2a SHIPPED by PD (ship report md5 `b9d862fcebbe78317a0081d052121294`, 220 lines, on Beast at `/home/jes/postgres-beast/B2a_ship_report.md`). All 7 acceptance gates PASS. Paco independent verification gate from fresh shell: 7/7 PASS, file integrity preserved (compose.yaml `a9a7404d...`, init SQL `899c6932...`), container ID `61acfaf455d8...` running image SHA `8ed3192326bb...`. Two Paco-authorized deviations documented in ship report: (1) Compose v5.1.3 plugin bootstrap (Beast docker.io lacks v2 plugin; sha256 verified against Docker upstream); (2) Spec Step 6 `sleep 15` replaced with health-poll loop (P6 lesson: container-up steps should poll until healthy with explicit timeout cap, not sleep for guessed duration). PG 16.13 + pgvector 0.8.2 running on Beast at 127.0.0.1:5432, controlplane DB owned by admin (Superuser+Replication=t), pgdata 48.21MB. Three P6 methodology lessons captured. B2a CLOSED. B2b (logical replication CiscoKid->Beast) drafting unblocks; Atlas-on-Beast (P3) hard prereq satisfied. Task pipeline `6d5102a5-93e8-4972-846f-9acbabe2b795` ready for CEO mark-done. Doc chain: 10 B2a docs total (2 paco_request, 4 paco_review, 4 paco_response in `/docs/`; ship report on Beast).
- [x] **2026-04-26 Day 72** -- CAPACITY_v1.1 RATIFIED by CEO as-is. Hardware org chart canon-locked. P3 hardware redistribution unblocks (SlimJim Prometheus+Grafana, Beast=Atlas home, Pi3/JesAir/Cortez role evaluations).
- [x] **2026-04-26 Day 72** -- iCloud canon-flip RATIFIED by CEO. Standing convention now: CiscoKid + GitHub origin/main are canonical for all Paco-managed artifacts (CHECKLIST, STANDING_RULES, CAPACITY, CHARTERS, /tasks specs, /docs correspondence). iCloud `/AI/Santigrey/` becomes a CEO-convenience read-only copy not maintained by Paco. Macmini SSH pipe is no longer treated as data-sync infrastructure (Rule 1 corollary). Stale iCloud copies will be allowed to drift; CEO can manually pull from GitHub when desired. CHECKLIST + STANDING_RULES Location/Mirror lines updated. Memory edit pending.
- [x] **2026-04-26 Day 72** -- CHARTERS_v0.1 RATIFIED by CEO with Atlas-on-Beast revision applied (per CAPACITY_v1.1 ratification: Atlas home = Beast, inference = Goliath). Pulled from iCloud one final time as part of canon-flip transition; now canonical on CiscoKid + GitHub. Build status revision: Atlas to be built on Beast (Postgres replica + MinIO + embeddings + tool execution), inference offloaded to Goliath (Qwen 2.5 72B over LAN), depends on B2b + B1 landing first. Six P4 deferred items remain (Family Office charter, sub-agent definitions, inter-dept SOPs, Atlas build spec, shared-state architecture, Brand & Market quarterly plan).
- [x] **2026-04-26 Day 72** -- B2b spec drafted (19341 bytes / ~440 lines, hash via md5sum). Logical replication CiscoKid (publisher PG 16.11) -> Beast (subscriber PG 16.13) for `public` + `agent_os` schemas; `mercury` deliberately excluded per Q4=C. Q1-Q7 picks integrated into spec. Four NEW structural picks flagged: (1) pg_hba.conf bind-mount approach Option B preferred (config-as-code, mirrors B2a init/), (2) Service ordering Option A preferred (accept ~5-30s downtime, dependents auto-reconnect per Day 48 hardening), (3) Subscription password Option A preferred (admin/adminpass; replicator-role separation deferred to P5 credentials inventory), (4) Schema bootstrap transport Option A preferred (pg_dump --schema-only + scp + psql; standard idiom; Rule 1 compliant). 12-item acceptance gate, full rollback procedure, downtime safety analysis. Awaiting CEO ratification.
- [x] **2026-04-26 Day 72** -- B2b RATIFIED by CEO (Option 1, all four picks as Paco recommended): (1) pg_hba.conf via bind-mount (Option B, config-as-code), (2) accept ~5-30s CiscoKid Postgres downtime during Phase E (Option A; dependents auto-reconnect per Day 48), (3) subscription password admin/adminpass matching publisher (Option A; replicator-role separation deferred to P5), (4) schema bootstrap via pg_dump --schema-only + scp + psql (Option A; standard idiom, Rule 1 compliant). Spec status DRAFT -> RATIFIED. Queued for PD via Cowork prompt with `docs/paco_response_b2b_ratification_phase_a_go.md` as routing handle. PD begins Phase A (CiscoKid pre-change capture + conf/ directory creation + backup compose.yaml + pg_hba.conf.original capture).

---

## How to use this checklist

- **Every Paco session opens with a checklist read.** SESSION.md is history; CHECKLIST.md is current state.
- **Every closed task moves to the audit trail with a date.**
- **Every new commitment lands at the right priority tier with an explicit owner.**
- **No work happens that isn't on this list.** If it should happen, add it. If it shouldn't, don't.

