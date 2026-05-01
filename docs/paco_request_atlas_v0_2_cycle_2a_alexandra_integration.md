# Paco Request -- Atlas v0.2 Cycle 2A -- Alexandra integration scope ratification

**Filed by:** PD
**Date:** 2026-05-01 UTC (Day 77)
**Predecessor:** `docs/handoff_paco_to_pd.md` at HEAD `bbc10e2` (Cycle 2A entry directive) + `docs/paco_response_atlas_v0_1_cycle_1i_close_confirm.md` (Atlas v0.1 Cycle 1 ratified COMPLETE)
**Status:** PRE-implementation. Awaiting Paco rulings on integration architecture + tool subset + UI surfaces + demo narrative + telemetry contract + auth model + sub-cycle roadmap. NO code lands this turn.

---

## Section 0 -- Verified live block (5th standing rule)

14 verifications run live; all evidence below from this session.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | Atlas git HEAD | git on Beast | `d383fe0` (Cycle 1I close) clean tree |
| 2 | atlas-mcp.service | systemctl on Beast | active, MainPID 2111126 |
| 3 | atlas-mcp 10 tools live | Beast SDK -> sloan2 :8443/mcp | tools_count=10; names match Cycle 1I close |
| 4 | B2b anchor PRE | docker inspect on Beast | `2026-04-27T00:13:57.800746541Z` healthy r=0 |
| 5 | Garage anchor PRE | docker inspect on Beast | `2026-04-27T05:39:58.168067641Z` healthy r=0 |
| 6 | atlas.events baseline | psql on Beast | 56 rows (embeddings=12, inference=14, mcp_client=6, mcp_server=24) |
| 7 | Alexandra location | systemctl + find on CK | orchestrator.service running uvicorn at `/home/jes/control-plane/orchestrator/app.py` :8000 PID 2688 |
| 8 | Alexandra package | ls + cat on CK | `ai_operator.*` -- 12 subpackages: agent / inference / memory / tools / dashboard / api / worker / repo / sanitize / dev / persona / mqtt_executor |
| 9 | Supporting services | systemctl on CK | 5 active: alexandra-telegram, calendar-alert, event-engine, mqtt-subscriber, recruiter-watcher |
| 10 | Dashboard endpoint | curl on CK | https://sloan3.tail1216a3.ts.net/dashboard -> http_code=200 time=0.010s |
| 11 | Alexandra-Atlas references | grep on CK | **ZERO** -- `from atlas` / `import atlas` not present in orchestrator code -- greenfield integration |
| 12 | CK Postgres locality (v0.2 P5 #28 root cause) | ss on CK | `LISTEN 192.168.1.10:5432` (LAN IP only; no 127.0.0.1 binding) |
| 13 | Alexandra hardcoded pg references | grep on CK | 4 source files + `.env` DATABASE_URL all hardcode `127.0.0.1:5432` -- fail because of #12 |
| 14 | CK has its own postgres container | docker ps on CK | `control-postgres pgvector/pgvector:pg16` (separate from Beast `control-postgres-beast`) |
| 15 | v0.2 P5 #22 (Tailscale auth key residual) | CEO confirmation prior session | RESOLVED via 1-day expiration (no manual revocation) |

---

## Section 1 -- TL;DR

Alexandra is the orchestrator FastAPI/uvicorn app at `/home/jes/control-plane/orchestrator/` on CK :8000, fronted by nginx at `https://sloan3.tail1216a3.ts.net/dashboard`. Built around the `ai_operator.*` package (agent + inference + pgvector memory + homegrown tool registry + dashboard). Has ZERO atlas references currently -- Cycle 2A is greenfield integration.

Atlas v0.1 ships 10 tools on `https://sloan2.tail1216a3.ts.net:8443/mcp`. Substrate held bit-identical for ~96+ hours.

PD recommendation: **Path A** (Alexandra adds `atlas.mcp_client` import + becomes an MCP client of atlas-mcp). v0.2.0 tool subset = 4 read-heavy tools (memory_query / memory_upsert / events_search / inference_history). Tasks tools deferred to v0.2.1+. UI surfaces: memory browser + audit log viewer + token usage dashboard. Telemetry back-loop: new `source='alexandra'` for Alexandra-origin events. Auth: tailnet-bound at v0.2.0. Sub-cycles: 2B build (wire client + memory browser), 2C build (audit + token dashboards), 2D polish + demo. Capstone deadline (June 2026) drives narrative-first prioritization.

v0.2 P5 #28 (broken `127.0.0.1:5432` connection) root cause located but TANGENTIAL to integration scope -- can be fixed opportunistically without blocking Cycle 2B build.

---

## Section 2 -- Alexandra current architecture (informational)

### Service topology

- **`orchestrator.service`** -- FastAPI/uvicorn at `/home/jes/control-plane/orchestrator/app.py` :8000 (PID 2688). Main API surface. Includes `/dashboard` route via `ai_operator.dashboard.dashboard.router`.
- **`alexandra-telegram.service`** -- Telegram bot front-end
- **`calendar-alert.service`** -- calendar alert worker
- **`event-engine.service`** -- event engine worker
- **`mqtt-subscriber.service`** -- MQTT subscriber for Tier 3 IoT
- **`recruiter-watcher.service`** -- recruiter email watcher

### Codebase

- Path: `/home/jes/control-plane/orchestrator/` (SAME git repo as control-plane-lab)
- Entry: `app.py` (FastAPI, ~227+ lines visible in head; multiple .bak files indicate active iteration)
- Package: `ai_operator/` with 12 subpackages
- Existing memory layer: `ai_operator/memory/db.py` uses psycopg + pgvector + dict_row (NOT atlas.db)
- Existing tool registry: `ai_operator/tools/registry.py` -- homegrown, NOT MCP-based
- Inference: `ai_operator/inference/ollama.py` -- direct Ollama calls (qwen2.5:72b at Goliath 192.168.1.20:11434)
- Persona system: Alexandra/Companion two-posture per product vision
- Context engine: `ai_operator/context_engine.py` builds live context (currently broken pg connection per v0.2 P5 #28)
- MQTT executor: `ai_operator/mqtt_executor.py` -- starts on app boot for Tier 3 IoT command approval gate

### What's working

- Dashboard endpoint returns 200 in 10ms (verified live row 10)
- Goliath inference (qwen2.5:72b) wired and warming on startup (per `app.py:warmup_private_brain`)
- Anthropic API integration (per dashboard alert state)
- Tier 3 IoT MQTT executor running (per service status)
- Telegram + calendar + event engine + recruiter watcher all active

### What's broken (v0.2 P5 #28)

- `ai_operator/context_engine.py:9` hardcodes `postgresql://admin:adminpass@127.0.0.1:5432/controlplane`
- `ai_operator/tools/registry.py` lines 598, 637, 1066 hardcode the same
- `app.py:227` hardcodes the same
- `.env` `DATABASE_URL=postgresql://admin:adminpass@127.0.0.1:5432/controlplane`
- CK Postgres binds `192.168.1.10:5432` only (no 127.0.0.1) -- connections fail
- Fix options: (a) rebind pg to also LISTEN on 127.0.0.1 (substrate change) OR (b) update Alexandra connection strings to `192.168.1.10:5432` (config change) OR (c) Docker compose level binding

### Substrate touchpoints

- Alexandra Postgres = `control-postgres` container on CK (pgvector/pgvector:pg16) -- DIFFERENT from Beast `control-postgres-beast` substrate anchor
- Beast substrate (postgres + garage) is what atlas.* schemas live on; Alexandra has NO direct substrate touchpoint at v0.2.0 scope

---

## Section 3 -- Integration architecture options

### Path A -- Alexandra becomes an MCP client (PD RECOMMENDED)

Alexandra adds `atlas.mcp_client` as a Python dependency. Calls atlas-mcp via streamable_http_client over Tailscale. Mirrors PD's existing client pattern.

**Pros:**
- Zero coupling between Alexandra and Atlas at the Python import level (other than the client SDK)
- Atlas-mcp tool surface is the integration contract -- stable since Cycle 1H/1I ratification
- Server-side ACL is the authoritative authorization boundary; Alexandra inherits this discipline
- Atlas can evolve internal implementation without breaking Alexandra (MCP contract holds)
- Existing Atlas tooling (10 tools) becomes immediately usable
- Alexandra's existing memory + tools + context engine remain untouched at v0.2.0

**Cons:**
- Network-hop latency for every atlas tool call (Alexandra :8000 -> atlas-mcp tailnet -> nginx -> uvicorn :8001 -> psycopg). Likely <50ms intra-tailnet but adds RTT
- Two MCP transports in play (mcp_client SDK 1.27.0 must be installed in Alexandra venv too)
- Failure mode: if atlas-mcp.service down, atlas tool calls fail (Alexandra must handle gracefully)

### Path B -- Alexandra imports atlas package directly

Alexandra adds `atlas` as Python dep (sibling to `ai_operator`). Calls atlas.db.Database, atlas.embeddings.EmbeddingClient directly in-process.

**Pros:**
- Zero network-hop latency
- No MCP-transport overhead
- Direct error handling (raised exceptions, not MCP error responses)

**Cons:**
- Couples Alexandra to atlas package internals; refactoring atlas breaks Alexandra
- Atlas package exists ON BEAST not CK -- requires either (a) installing atlas on CK OR (b) running Alexandra on Beast (architectural change). Beast already runs atlas-mcp; running orchestrator there too breaks separation of concerns and changes substrate map
- Bypasses server-side ACL; Alexandra has direct DB access (privilege escalation risk; doesn't mature toward multi-agent v0.2.x)
- Doesn't validate atlas-mcp's tool surface contract; v0.2 atlas-mcp client traffic remains PD-only
- Doesn't exercise the MCP transport in production (defers debt)

### Path C -- Hybrid (some MCP, some in-process)

E.g., memory operations via MCP (durable, ACL'd); inference operations in-process (Goliath URL is shared infra).

**Pros:**
- Optimization knob for latency-sensitive paths

**Cons:**
- Complexity tax: two integration patterns, two failure modes, two test surfaces
- Inconsistent: caller-endpoint and audit trail differ between paths
- v0.2.0 doesn't have established latency requirements that justify hybrid splits

### PD Recommendation: Path A

Reasons:
1. Alexandra is a brand-new Atlas consumer; MCP transport contract is the right boundary
2. Server-side ACL discipline carries forward (matters for v0.2.x multi-agent expansion)
3. Atlas package internals stay invisible to Alexandra -- decoupling reduces refactor risk
4. Network-hop latency is a non-issue at v0.2.0 (single CEO + Alexandra; not high-throughput)
5. Validates atlas-mcp tool surface contract in production (the work shipped for Cycles 1H/1I gets exercised)
6. v0.2.x evolution path is clean: add new atlas-mcp tools -> Alexandra picks them up via list_tools (or explicit wiring); no Alexandra refactor

---

## Section 4 -- Tool subset for v0.2.0

Atlas-mcp ships 10 tools. PD proposes 4 land at v0.2.0; 6 deferred to v0.2.1+:

### v0.2.0 (4 tools, read-heavy)

| Tool | Why now |
|---|---|
| `atlas_memory_query` | CEO memory recall is the highest-leverage demo feature; semantic similarity over CEO notes is the "intelligence" payoff |
| `atlas_memory_upsert` | Symmetric write path for memory; CEO can take notes through Alexandra and they land in atlas.memory |
| `atlas_events_search` | Audit / introspection; surfaces what Alexandra has been doing across atlas |
| `atlas_inference_history` | Token usage stats + cost / activity visibility; capstone-friendly metric |

### v0.2.1+ (6 tools deferred)

| Tool | Defer reason |
|---|---|
| `atlas_tasks_create` | Alexandra has no task queue UI yet; v0.2.1 builds a queue panel first |
| `atlas_tasks_list` | Same |
| `atlas_tasks_get` | Same |
| `atlas_tasks_claim` | Worker semantics not v0.2.0 scope |
| `atlas_tasks_complete` | Same |
| `atlas_tasks_fail` | Same |

**Rationale:** memory + events + inference cover the demo narrative (Section 6). Tasks add a second loop (queue work, observe completion) that's a separate v0.2.x story.

---

## Section 5 -- UI surfaces

PD proposes 3 new dashboard panels for v0.2.0, all wired to the 4-tool subset:

### Panel 1: Memory Browser

- Search box -> `atlas_memory_query` (top_k=10 default)
- Result list with kind / content snippet / distance / metadata
- "Save note" form -> `atlas_memory_upsert`
- Sidebar shows recent memories (last 20 by created_at) -- backed by `atlas_memory_query` with empty query OR a separate fetch

### Panel 2: Audit Log Viewer

- Filterable timeline backed by `atlas_events_search`
- Filters: source (allowlist dropdown: atlas.embeddings / atlas.inference / atlas.mcp_client / atlas.mcp_server / alexandra), kind, ts range
- Row expand shows full payload jsonb
- Useful for debugging Alexandra's atlas integration during demo

### Panel 3: Token Usage Dashboard

- Backed by `atlas_inference_history` (default ts_after=now-7d)
- Aggregate metrics: total tokens by model, total ms by model, avg tokens/req
- Time-series chart: tokens/hour over last 7 days
- Lightweight; uses existing inference telemetry from Cycle 1D

### Defer to v0.2.1+

- Task queue panel (depends on tasks tools)
- Per-tool ACL inspector (depends on visibility into ACL_DENY_PATTERNS_SERVER -- v0.1 patterns are empty so panel would be empty too)

### Implementation notes

- Alexandra's existing dashboard router pattern from `ai_operator/dashboard/dashboard.py` likely templates Jinja2 + serves HTML/CSS/JS. New panels probably follow the same shape.
- Each panel calls Alexandra's FastAPI :8000 -> Alexandra calls atlas-mcp via Path A -> renders results.
- v0.2.0 keeps existing dashboard panels intact (Anthropic API status, postgres status, nginx status). Atlas panels are additive, not replacement.

---

## Section 6 -- Demo narrative (capstone)

PD proposed flow (Sloan + Per Scholas instructor will refine):

### Scene 1: "The system before me" (60s)

- Camera on dashboard at sloan3 :443/dashboard
- Show all green status (Anthropic / postgres / nginx / Goliath warm)
- Show Memory Browser empty state
- Voice-over: "This is Alexandra. She's the Head of Operations for my homelab. Built on Atlas, an Anthropic-style agent platform I've been shipping over the past 30 days."

### Scene 2: "Memory in action" (90s)

- Type a CEO note: "Met with X today, discussed Y"
- Submit -> hits `atlas_memory_upsert` -> server embeds via mxbai-embed-large -> writes atlas.memory
- Audit log panel updates in real-time showing `tool_call atlas_memory_upsert ms=...`
- Type a query: "what did I discuss with X"
- Hits `atlas_memory_query` -> server embeds query -> nearest-neighbors search
- Result shows the note from above with similarity score
- Voice-over: "Semantic memory. Local. Private. mxbai-embed-large at 1024 dimensions, pgvector backend, all running on my Tesla T4."

### Scene 3: "Inference + telemetry" (60s)

- Trigger an Alexandra agent action that uses Goliath inference (e.g., persona conversation)
- Switch to Token Usage Dashboard
- See the latest inference event with eval_count, eval_duration_ms, model name
- Voice-over: "Every inference is logged. Tokens, durations, models. I know exactly what compute I'm consuming and which models are doing the work."

### Scene 4: "The architecture" (60s)

- Cut to architecture diagram showing: Alexandra orchestrator (CK) -- atlas.mcp_client -- Tailscale tailnet -- nginx Beast -- uvicorn -- atlas-mcp loopback -- Postgres + Garage substrate
- Voice-over: "Tailnet for transport. nginx fronts a strict-loopback uvicorn. Substrate runs in Docker on bare metal. Substrate-anchor invariant holds bit-identical from build to demo. The whole thing is observable and recoverable."

### Scene 5: "The build process" (90s)

- Slide deck: 9 cycles 1A-1I, ~35 source files, ~96 hours of substrate stability, 30-day shipping cadence
- Reference Per Scholas program; emphasize disciplined cycle structure (paco_request gates -> build directives -> review -> close confirmation)
- Voice-over: "This is what 30 days of focused systems engineering looks like when you treat AI work as platform engineering."

### Defer to v0.2.x or live demo

- Tier 3 IoT (Schlage lock approval gate) -- compelling but moves the demo away from agent/data narrative
- Multi-agent demo (Atlas + future agents) -- requires v0.2.x feature work
- Capstone written component -- separate workstream

### What this drives

- Memory browser is the centerpiece (Scene 2) -> Cycle 2B's first build target
- Audit log viewer enables Scene 2's real-time event surfacing -> ships in Cycle 2B too
- Token dashboard supports Scene 3 -> Cycle 2C
- Architecture diagram + slide deck = Cycle 2D polish

---

## Section 7 -- Telemetry back-loop

Proposal: introduce **`source='alexandra'`** for Alexandra-origin events.

### Source allowlist update

Current atlas.events sources: atlas.embeddings, atlas.inference, atlas.mcp_client, atlas.mcp_server. Add `alexandra` to the allowlist.

This means updating `atlas.mcp_server.inputs.EVENTS_SOURCE_ALLOWLIST` -- a one-line change in v0.2.x. Tangential to Cycle 2A scope but flagged here for ratification.

### Where Alexandra writes

- **Atlas-mcp tool calls** Alexandra makes -> `source='atlas.mcp_client'` (Alexandra IS an MCP client per Path A; matches Cycle 1F pattern)
- **Alexandra-internal events** (agent runs, persona switches, dashboard interactions, MQTT triggers) -> `source='alexandra'`. Scoped to Alexandra's own observability needs; doesn't pollute the atlas-mcp event space.

### Kinds (proposed)

- `agent_run` -- Alexandra agent invocation
- `persona_switch` -- two-posture transitions
- `dashboard_interaction` -- UI navigation events (optional; may be too noisy)
- `mqtt_command_approved` -- Tier 3 IoT approval gate trigger
- `recruiter_email_processed` -- recruiter watcher events

PD bias: keep kinds list minimal at v0.2.0; expand opportunistically.

### Secrets discipline carries forward

No arg VALUES persisted. Same posture as Cycle 1H/1I: tool_name + arg_keys + status + duration_ms + caller_endpoint. Alexandra adopts identical discipline.

---

## Section 8 -- Auth model at v0.2.0

PD proposal: **tailnet membership + caller_endpoint = authentication boundary** (mirror Cycle 1H/1I).

### v0.2.0 trust model

- Anyone on the tailnet who reaches sloan3 :443 (Alexandra dashboard) is trusted
- Anyone on the tailnet who reaches sloan2 :8443 (atlas-mcp) is trusted
- Currently: Sloan is the only human on the tailnet; Mac mini Claude Desktop is the only other client
- caller_endpoint (X-Real-IP) is captured for audit, NOT for authorization

### v0.2.0 ACL state

- Server-side `ACL_DENY_PATTERNS_SERVER` remains empty (v0.1 posture)
- Pydantic Field validators enforce per-tool allow-list constraints declaratively
- No bearer token / OAuth / single-user CEO auth at v0.2.0

### Defer to v0.2.x

- Bearer token / API key for inbound MCP -- v0.2.x P5 (when multi-agent v0.2.x lands)
- CEO-vs-Companion permission split -- requires persona-aware ACL middleware
- Per-tool rate limiting -- v0.2 P5 (already banked)
- Session token for dashboard cookie auth -- v0.2.x; Alexandra dashboard is currently un-authenticated (relies on tailnet membership)

### Why this is OK at v0.2.0

- Threat model: single user (Sloan) + closed tailnet + capstone demo audience (Per Scholas instructor + cohort)
- No public exposure (sloan2/sloan3 .ts.net are tailnet-only)
- Audit trail captures everything via atlas.events; even if auth isn't enforced, post-hoc accountability is intact
- Capstone demo doesn't require auth UX; introducing it adds complexity without value at this stage

---

## Section 9 -- Substrate impact + scope boundary

### What Cycle 2A touches

- **NOTHING** at the substrate / service layer. This is a paco_request gate; document only.

### What Cycle 2B (build) WILL touch

- Alexandra's `requirements.txt` / `pyproject.toml` -- adds `atlas` package as dep (or sibling install)
- Alexandra's `app.py` or new `ai_operator/atlas_bridge.py` -- adds atlas.mcp_client wiring
- Alexandra's dashboard router -- adds 3 new panels (Memory Browser + Audit + Token Usage)
- Possibly `EVENTS_SOURCE_ALLOWLIST` in atlas.mcp_server.inputs -- adds `'alexandra'`
- orchestrator.service may need restart to pick up new code (application-layer; substrate untouched)

### What Cycle 2A does NOT touch

- atlas-mcp.service on Beast (10 tools stay live; no schema changes)
- nginx config on Beast (Cycle 1G config carries forward)
- nginx config on CK (alexandra vhost unchanged)
- substrate Postgres + Garage Docker containers (anchors must remain bit-identical)
- mcp_server.py on CK (homelab-mcp; unrelated)
- v0.2 P5 #28 (broken pg connection) -- fix is OPPORTUNISTIC; not required for Path A integration since Alexandra's atlas integration goes over network, not local pg

### v0.2 P5 #28 disposition

Fix is independent of Cycle 2A scope. Two options:
- **Option α:** fix in Cycle 2B as a side-effect of touching Alexandra (update connection strings to `192.168.1.10:5432` -- pure config change; no substrate touch)
- **Option β:** defer to a dedicated v0.2 P5 cycle

PD bias: Option α (small, in-flight, reduces tech-debt; compatible with anchor preservation since it's connection string config, not pg rebind)

---

## Section 10 -- Timeline / sub-cycle roadmap

### Capstone timeline anchor

- Per Scholas program ends June 26, 2026
- Capstone presentation typically last 1-2 weeks of program
- v0.2.0 ship target: **mid-June 2026** (~6 weeks from today)
- Demo video shoot: ~1 week before presentation
- Demo polish lane runs separate from build lane

### Sub-cycle proposal

| Cycle | Scope | Effort estimate |
|---|---|---|
| 2A | THIS paco_request | 1 turn |
| 2B | Build: atlas.mcp_client wiring in Alexandra + Memory Browser panel + Audit Log Viewer panel + `source='alexandra'` allowlist update | 1-2 build cycles |
| 2C | Build: Token Usage Dashboard panel + telemetry kinds for `agent_run` / `mqtt_command_approved` + smoke / observability tests | 1 build cycle |
| 2D | Polish: architecture diagram + slide deck + capstone video script + demo dry run | 1 cycle |
| 2E (optional) | v0.2.1 atlas_tasks_* surface (queue panel) | 1 cycle if time permits |

### Parallel workstreams

- v0.2 P5 hardening pass: opportunistic; not gating any Cycle 2B-D work
- v0.2 P5 #28 broken pg connection: PD recommends Option α (fix in Cycle 2B as side-effect)
- Per Scholas coursework: M/W/F 6-9 PM ET; build cycle calendar respects class days

### Risk register

- **R1**: atlas.mcp_client SDK version skew between Beast atlas venv (1.27.0) and Alexandra venv (TBD on CK) -- mitigation: pin via pyproject.toml during Cycle 2B
- **R2**: orchestrator.service restart during Cycle 2B may briefly drop dashboard availability -- mitigation: restart during low-use window; rollback path is `git revert` + restart
- **R3**: capstone demo video record/edit time may be longer than 1 cycle -- mitigation: rough cut by Cycle 2D mid-point; final polish opportunistic
- **R4**: Per Scholas coursework demands may compress build time -- mitigation: keep cycle scopes small; prefer 2 small cycles over 1 large

---

## Section 11 -- Asks for Paco

1. **Ratify integration architecture** -- Path A (PD-recommended) / Path B / Path C / amend?
2. **Ratify v0.2.0 tool subset** -- 4 tools (memory_query / memory_upsert / events_search / inference_history)? Or different subset?
3. **Ratify UI surfaces priority** -- 3 panels (Memory Browser + Audit Log Viewer + Token Usage Dashboard)? Or different priority?
4. **Ratify demo narrative draft** -- Section 6 5-scene flow as starting point for CEO + Per Scholas instructor refinement?
5. **Ratify telemetry back-loop contract** -- new `source='alexandra'` + add to EVENTS_SOURCE_ALLOWLIST in atlas.mcp_server.inputs (Cycle 2B atomic change)?
6. **Ratify auth model at v0.2.0** -- tailnet-bound (mirror Cycle 1H/1I) without bearer token introduction at this stage?
7. **Confirm substrate impact** -- zero substrate touches at Cycle 2A; Cycle 2B touches Alexandra app code + EVENTS_SOURCE_ALLOWLIST only; Postgres/Garage anchors invariant?
8. **Confirm Cycle 2B/2C/2D roadmap** -- 4 sub-cycles plus optional 2E? Effort estimates reasonable?
9. **Authorize Cycle 2B build directive next handoff** -- with Path A + 4-tool subset + 2 panels (Memory Browser + Audit Log Viewer) as Cycle 2B scope?
10. **Disposition on v0.2 P5 #28** -- Option α (fix in Cycle 2B) or Option β (defer)?
11. **Bank any new v0.2 P5 candidates surfaced** -- e.g., atlas-mcp client SDK version pinning across consumers (Atlas package + Alexandra venv) as v0.2 P5 #38?
