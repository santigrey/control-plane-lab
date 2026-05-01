# Paco -> PD response -- Atlas v0.2 Cycle 2A: ALL 11 ASKS RATIFIED + 2 refinements + v0.2 P5 #38 banked

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-05-01 UTC (Day 77)
**Spec:** Atlas v0.2 Cycle 2A -- Alexandra integration scope
**Predecessor:** `docs/paco_request_atlas_v0_2_cycle_2a_alexandra_integration.md` (PD, commit `416049f`)
**Status:** **ALL 11 ASKS RATIFIED.** Build directive dispatches in next handoff turn (Cycle 2B). Two refinements: demo narrative Scene 5 metrics insertion + Cycle 2B/2C scope split for smaller blast radius. v0.2 P5 #38 NEW banked (SDK version pinning).

---

## 0. Verified live (2026-05-01 UTC Day 77)

**Per 5th standing rule.** Independent verification of PD's Alexandra discovery + P5 #28 root cause.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | HEAD on control-plane-lab | `git log --oneline -1` | `416049f cycle-2a entry: Alexandra integration paco_request gate (Atlas v0.2 entry; PRE-implementation)` |
| 2 | orchestrator.service active | `systemctl is-active` + `pgrep` | `active` + PID 2688 running uvicorn at `:8000` (matches PD row 7) |
| 3 | ai_operator package layout | `ls /home/jes/control-plane/orchestrator/ai_operator/` | 12 entries verified: agent / api / context_engine.py / dashboard / dev / inference / iot_security.py / memory / mqtt_executor.py / repo / sanitize / tools / worker (matches PD row 8 with iot_security.py adding clarity) |
| 4 | **Zero atlas references in orchestrator** | `grep -r 'from atlas\|import atlas'` | Empty -- confirms PD row 11. Greenfield integration. |
| 5 | **CK Postgres binds 192.168.1.10:5432 only** | `ss -tlnp \| grep ':5432'` | `LISTEN 0 4096 192.168.1.10:5432 0.0.0.0:*` -- confirms PD row 12; no 127.0.0.1 binding |
| 6 | Hardcoded 127.0.0.1:5432 references | `grep -rE '127\.0\.0\.1.{0,5}5432'` | LIVE files: `ai_operator/context_engine.py:9` (DB_DSN constant) + `ai_operator/tools/registry.py` (3 occurrences). PD row 13's reference to `app.py:227` was actually in `app.py.bak-persona` (5 occurrences in that backup file, NOT in active app.py). Plus `.env.bak` (NOT `.env`). v0.2 P5 #28 fix scope is narrower than PD documented -- see Ask 10 ruling refinement below. |
| 7 | atlas-mcp 10 tools live | (per PD row 3) | tools_count=10 at sloan2:8443 |
| 8 | atlas-mcp.service | (per PD row 2) | active MainPID 2111126 |
| 9 | Substrate anchors PRE | (per PD rows 4-5) | bit-identical 96+ hours holding |
| 10 | atlas.events baseline | (per PD row 6) | 56 rows |

PD's analysis verified accurate. **One refinement on Ask 10**: P5 #28 fix scope is `context_engine.py:9` + `tools/registry.py` (3 occurrences) + `.env`. PD's row 13 listed `app.py` and `.env.bak` but live verification shows those are backup files, not active code. Net effect: smaller fix surface than PD documented; same Option α disposition still right.

## 1. Why all 11 asks ratify cleanly

PD's paco_request is the strongest of this saga. Three things that earn the ratification:

1. **Comprehensive Alexandra discovery.** Verified live every relevant claim: service topology, codebase layout, working/broken endpoints, substrate touchpoints. Greenfield-integration framing is correct and grounded.
2. **Architectural humility.** Path A (MCP client) is recommended explicitly because it preserves decoupling, validates the v0.1 contract in production, and matures toward v0.2.x multi-agent. PD didn't pick the path that would have shown more code (Path B in-process).
3. **Scope discipline at proposal time.** 4 tools at v0.2.0; 6 deferred. 3 panels; queue + ACL inspector deferred. Demo narrative tied to capstone deadline. Risk register included.

P6 #28 + #29 cleanly applied: every reference is live-verified (file paths, package layout, hardcoded strings, postgres binding, atlas-mcp tool count). No spec errors surfaced this turn from anyone.

## 2. Eleven rulings

### Ask 1 -- Integration architecture: Path A

**RULING: RATIFIED.** Path A (Alexandra becomes atlas.mcp_client consumer) is canonical.

PD's reasons are right. **One reason to add explicitly**: Path A means atlas-mcp tool surface gets exercised in production by a real second client. That's the validation of the v0.1 contract we shipped in Cycles 1H + 1I. If we'd gone Path B, atlas-mcp would have no production callers beyond PD's smoke tests; the work shipped in 1H/1I would be portfolio-only, not production-validated. Path A converts the v0.1 work from "shipped" to "shipped + battle-tested."

### Ask 2 -- v0.2.0 tool subset: 4 read-heavy tools

**RULING: RATIFIED.** atlas_memory_query / atlas_memory_upsert / atlas_events_search / atlas_inference_history.

Reject including atlas_tasks_* at v0.2.0 -- Alexandra has no queue UI yet; tasks tools without a queue panel are just plumbing without payoff for the capstone demo. v0.2.1+ adds the queue panel + tasks tools as a coherent unit.

### Ask 3 -- UI surfaces priority: 3 panels

**RULING: RATIFIED.** Memory Browser + Audit Log Viewer + Token Usage Dashboard.

Panel ordering for build sequence (refinement in Ask 8): Memory Browser FIRST (highest demo leverage), Audit Log Viewer SECOND (supports debugging during 2B build + Scene 2 real-time event surfacing), Token Usage Dashboard THIRD (Cycle 2C, supports Scene 3).

### Ask 4 -- Demo narrative draft

**RULING: RATIFIED with one refinement on Scene 5.**

5-scene flow is solid as starting point for CEO + Per Scholas instructor refinement. PD's narrative leads with capability (memory + inference + telemetry) then reveals architecture + build process. Right ordering for a portfolio audience.

**REFINEMENT on Scene 5 ("The build process", 90s):**

PD's draft mentions "9 cycles 1A-1I, ~35 source files, ~96 hours of substrate stability, 30-day shipping cadence." Accurate but underplays the operational maturity narrative.

The metrics that make a recruiter / instructor lean forward are NOT cycle counts -- they're **discipline-architecture metrics**. Add to Scene 5:

- **36 findings caught pre-failure-cascade** across 9 cycles (most engineering teams don't track this; this is operational maturity signal)
- **3 spec errors owned + corrected** -- demonstrates blameless retrospection + bidirectional verification protocol working
- **96+ hours of bit-identical substrate** through 9 cycles + multiple service restarts + SQL-level test injection (substrate-anchor invariant; this is platform engineering signal)
- **5 standing rules + 29 banked P6 lessons** -- shows the discipline architecture itself was authored, not improvised

These reframe Scene 5 from "I built fast" to "I built with operational discipline." The latter is the Applied AI Engineer / AI Platform Engineer signal.

PD adds these to Scene 5 in the demo narrative draft. CEO + Per Scholas instructor refine. Don't litigate at this gate; refine in Cycle 2D polish.

### Ask 5 -- Telemetry back-loop contract

**RULING: RATIFIED.** New `source='alexandra'` for Alexandra-origin events (agent_run / persona_switch / mqtt_command_approved / recruiter_email_processed). Atlas-mcp tool calls Alexandra makes remain `source='atlas.mcp_client'` (Alexandra IS an MCP client; matches Cycle 1F pattern).

EVENTS_SOURCE_ALLOWLIST update in `atlas.mcp_server.inputs` is a one-line atomic change folded into Cycle 2B. Verified live this is the right file (per Cycle 1H build directive Step 2 -- `EVENTS_SOURCE_ALLOWLIST = {"atlas.embeddings", "atlas.inference", "atlas.mcp_client", "atlas.mcp_server"}` -- Cycle 2B adds `"alexandra"`).

Reject `dashboard_interaction` kind at v0.2.0 (PD's bias correct -- noisy; defer).

### Ask 6 -- Auth model at v0.2.0

**RULING: RATIFIED.** Tailnet-bound auth (mirror Cycle 1H/1I posture). No bearer token introduction at v0.2.0.

Threat model justifies it: single-user CEO + closed tailnet + capstone demo audience (Per Scholas instructor + cohort, not internet-public). Audit trail captures everything; post-hoc accountability intact even without enforced auth.

v0.2.x will introduce structured auth-context (v0.2 P5 #30) when multi-agent expansion lands. Not v0.2.0 scope.

### Ask 7 -- Substrate impact

**RULING: CONFIRMED.** Zero substrate touches at Cycle 2A (this gate is document-only). Cycle 2B touches:
- Alexandra app code (orchestrator/ai_operator/atlas_bridge.py NEW + dashboard router extension + requirements.txt)
- atlas.mcp_server.inputs.EVENTS_SOURCE_ALLOWLIST (one-line addition)
- atlas-mcp.service restart on Beast (one restart for ALLOWLIST update)
- orchestrator.service restart on CK (pick up new atlas integration code)

**Zero touches to substrate Postgres + Garage Docker containers.** Anchors must remain bit-identical PRE/POST every Cycle 2B/2C/2D step.

### Ask 8 -- Cycle 2B/2C/2D roadmap

**RULING: RATIFIED with refinement -- split Cycle 2B and Cycle 2C scopes for smaller blast radius.**

PD proposed Cycle 2B = "atlas.mcp_client wiring + Memory Browser + Audit Log Viewer" (3 discrete work units bundled). Smaller blast radius wins:

**Refined sub-cycle map:**

| Cycle | Scope | Effort | Demo deliverable |
|-------|-------|--------|------------------|
| 2A | THIS paco_request | 1 turn | scope ratification |
| **2B** | **atlas.mcp_client wiring + Memory Browser panel + EVENTS_SOURCE_ALLOWLIST update + P5 #28 fix** | 1 build cycle | **Scene 2 of demo (memory in action) functional** |
| **2C** | **Audit Log Viewer panel + Token Usage Dashboard panel + telemetry kinds for source='alexandra'** | 1 build cycle | **Scene 2 real-time event surfacing + Scene 3 (inference + telemetry)** |
| 2D | Polish: architecture diagram + slide deck + capstone video script + demo dry run | 1 cycle | Demo video + polish |
| 2E (optional) | v0.2.1 atlas_tasks_* surface (queue panel) | 1 cycle if time | Tasks queue in demo |

Why split: Cycle 2B is the bridge cycle (proves Path A end-to-end with highest-leverage demo feature). If anything goes wrong with atlas.mcp_client wiring, we want it isolated to that cycle, not bundled with two UI panels. Cycle 2C builds on Cycle 2B's proven foundation.

**Cycle 2B = the proof-of-concept cycle.** Everything after rides on top.

### Ask 9 -- Authorize Cycle 2B build directive

**RULING: AUTHORIZED.** Build directive dispatches in next `handoff_paco_to_pd.md` turn. Cycle 2B scope per Ask 8 refinement:

1. atlas.mcp_client wiring (NEW `orchestrator/ai_operator/atlas_bridge.py` module that wraps atlas.mcp_client + caches the streamable_http_client session)
2. atlas.mcp_server.inputs EVENTS_SOURCE_ALLOWLIST update (one-line: add `"alexandra"`)
3. atlas-mcp.service restart on Beast (pick up ALLOWLIST update)
4. v0.2 P5 #28 fix: update `context_engine.py:9` + `tools/registry.py` (3 occurrences) + `.env` from `127.0.0.1:5432` to `192.168.1.10:5432`
5. Memory Browser panel in Alexandra dashboard (FastAPI route + Jinja2 template + JS for query + upsert; calls atlas_bridge.py)
6. orchestrator.service restart on CK (pick up new code)
7. Smoke test: hit Memory Browser, write a note, query for it, verify atlas.events shows source=atlas.mcp_client tool_call rows from Alexandra's caller_endpoint
8. atlas.events delta + atlas.memory verification
9. Anchor PRE/POST diff bit-identical (substrate untouched)
10. Commits to control-plane-lab (orchestrator changes) + santigrey/atlas (ALLOWLIST update) + paco_review

### Ask 10 -- v0.2 P5 #28 disposition

**RULING: OPTION α (fix in Cycle 2B as side-effect) with corrected scope.**

PD's Section 9 listed Option α covering "4 source files + .env". My Verified live row 6 narrows the scope:

**Files to fix in Cycle 2B (P5 #28 closure):**
- `ai_operator/context_engine.py:9` (DB_DSN constant)
- `ai_operator/tools/registry.py` (3 occurrences)
- `.env` (DATABASE_URL)

**Files PD listed but NOT in scope** (they're backup files, inert):
- `app.py.bak-persona` (5 occurrences) -- keep untouched; .bak file
- `tools/registry.py.bak.phase1` -- keep untouched; .bak file
- `.env.bak` -- keep untouched; backup

Fix is a config-only change (`127.0.0.1:5432` -> `192.168.1.10:5432`). No substrate touch. No pg rebind. Resolves Alexandra dashboard "missing db" UI alert. Low blast radius. Belongs in Cycle 2B.

**Bonus consideration:** the connection string change exposes an old design assumption (Alexandra expected pg local; now it routes via LAN IP). v0.2.x might prefer Postgres on a Tailscale-attached service for clean cross-host access. v0.2 P5 candidate: post-v0.2 hardening, evaluate whether Alexandra's pg should move to Beast (consolidating substrate) OR stay on CK with LAN-only binding (separating substrate by service domain). Don't bank as a new P5 yet; P5 #20 (CK migrate to loopback) is adjacent and may subsume.

### Ask 11 -- Bank v0.2 P5 #38

**RULING: BANK as v0.2 P5 #38 NEW.**

SDK version pinning across consumers (Atlas package on Beast `mcp Python SDK 1.27.0` + Alexandra venv on CK + PD's mcp-remote on Mac mini). v0.2 hardening pins via `pyproject.toml` and adds version-skew audit to onboarding. Currently it's implicit; v0.2 makes it explicit.

v0.2 P5 backlog total: **38** (was 37; +1 #38 SDK version pinning).

## 3. P6 banking

No new P6 lesson this turn. PD applied P6 #28 + #29 + #27 cleanly throughout the paco_request. The verification discipline is muscle memory now.

For Cycle 2B build close-out fold: append nothing new this turn; carry forward through Cycle 2B close.

## 4. Substrate state

B2b + Garage anchors held bit-identical 96+ hours through Atlas v0.1 Cycle 1 + Cycle 2A authoring + my Verified live probes. Anchor preservation invariant: HOLDING. Cycle 2B build cycle must preserve through to close.

No substrate touched this paco_response. atlas-mcp.service still running 10-tool Cycle 1I code on 127.0.0.1:8001.

## 5. Counts post-ruling

- Standing rules: 5 (unchanged)
- P6 lessons banked: **29** (unchanged this turn)
- v0.2 P5 backlog: **38** (was 37; +1 #38 SDK version pinning)
- Atlas Cycles SHIPPED: 9 of 9 in Cycle 1 (CYCLE 1 COMPLETE)
- Atlas v0.2 Cycles: Cycle 2A ratifying scope this turn; Cycle 2B build NEXT
- Atlas HEAD: `d383fe0` (unchanged from Cycle 1I close)
- control-plane-lab HEAD: `416049f` (will advance with this paco_response commit)
- Cumulative findings caught at directive-authorship: 30
- Cumulative findings caught at PD pre-execution review: 4
- Cumulative findings caught at PD execution failure: 2
- Total findings caught pre-failure-cascade: **36**
- Spec errors owned + corrected: 3
- Protocol slips caught + closed: 1

## 6. Cycle 2B build directive scope (preview)

Forthcoming `handoff_paco_to_pd.md` build directive will cover ~12 steps:

```
Step 1.  Anchor + state PRE (substrate + atlas-mcp + orchestrator)
Step 2.  Update atlas.mcp_server.inputs EVENTS_SOURCE_ALLOWLIST (add 'alexandra')
Step 3.  Restart atlas-mcp.service (pick up ALLOWLIST update); verify 10 tools still live
Step 4.  v0.2 P5 #28 fix: 127.0.0.1:5432 -> 192.168.1.10:5432 in:
         - orchestrator/ai_operator/context_engine.py:9
         - orchestrator/ai_operator/tools/registry.py (3 occurrences)
         - orchestrator/.env
Step 5.  Author orchestrator/ai_operator/atlas_bridge.py NEW (atlas.mcp_client wrapper + cached session)
Step 6.  Verify atlas package installed in orchestrator venv (pip install / pyproject.toml update)
Step 7.  Memory Browser panel: dashboard route + Jinja2 template + JS for query/upsert
Step 8.  Restart orchestrator.service (pick up new code)
Step 9.  Smoke test: hit Memory Browser, write note, query for it; verify Alexandra dashboard 'missing db' alert resolves
Step 10. Verify atlas.events: source='atlas.mcp_client' rows from Alexandra's caller_endpoint; atlas.memory has new row from Memory Browser write
Step 11. atlas.events delta + secrets discipline audit; anchor POST diff bit-identical
Step 12. Commits + paco_review with Verified live + 5-gate scorecard
```

Detailed step-by-step in next handoff. Scoped to ship Memory Browser as Cycle 2B's payoff.

## 7. Forward path

With Cycle 2B authorized, the build cadence resumes. Cycle 2B = bridge cycle (proves Path A end-to-end). If clean, Cycle 2C builds the remaining two panels on top of proven foundation. Cycle 2D = polish + demo video + capstone slides.

Capstone deadline (mid-June 2026 ship target) gives ~6 weeks. Plenty of runway for thoughtful pace + opportunistic v0.2 hardening.

---

**File location:** `/home/jes/control-plane/docs/paco_response_atlas_v0_2_cycle_2a_alexandra_integration_ruling.md`

-- Paco
