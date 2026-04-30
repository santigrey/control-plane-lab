# Atlas v0.1 -- Head of Operations Agent (Full Charter)

**Spec status:** RATIFIED v3 (v2 superseded; Verified live header added per Day 75 CEO discipline RFC)
**Charter:** `CHARTERS_v0.1.md` Charter 5 -- Head of Operations: Atlas
**Predecessor:** `docs/H1_ship_report.md` (commit `f9a4e85`) -- substrate dependencies satisfied
**Author:** Paco (architect) -- to be executed by PD per existing handoff protocol
**Repo:** `github.com/santigrey/atlas` (CEO ratified Day 75)
**Build window target:** 2026-04-30 (Day 75, spec ratification) -> ~2026-06-14 (v0.1 ships)
**Hard date:** Capstone demo recording end of May / early June (per CEO Day 75 ratification)

**v3 corrections from v2 (per CEO Day 75 discipline RFC):**
1. Master "Verified live" section added at the top -- mandatory per `feedback_paco_pre_directive_verification.md` (5th standing rule)
2. Real Postgres state propagated through Cycles 1B + 1E + 1H + 4D: `admin/controlplane/adminpass` (NOT fictional `replicator_role/alexandra_replica`); atlas-owned tables live in `atlas` schema within `controlplane` database (not separate database)
3. Real Garage state propagated through Cycle 1C: existing buckets `atlas-state`, `backups`, `artifacts` (NOT `atlas-working-memory/atlas-artifacts/atlas-incoming` -- those don't exist; B1 ship pre-allocated different names)
4. Garage health URL: `http://127.0.0.1:3903/health` (admin endpoint), NOT `:3900/health` (S3 listener)
5. Goliath inference: LAN `192.168.1.20:11434` (Tailscale Path B per Cycle 1A ESC ruling)
6. Embedding model: `mxbai-embed-large:latest` on TheBeast (192.168.1.152:11434), dimension 1024
7. Section 13 standing rules count: 4 -> 5 (added `feedback_paco_pre_directive_verification.md`)
8. P6 lessons: 19 -> 20 (added P6 #20 deployed-state-name verification)

**v2 corrections from v1 (per CEO Day 75 ratification, retained in v3):**
1. Repo name confirmed: `santigrey/atlas`
2. Demo gate moved from end-of-Cycle-2 to **mid-Cycle-3** (after 3A + 3B close)
3. Architecture corrected to charter-literal all-Beast: Atlas runs its own MCP server on Beast (multi-MCP-host)

---

## 0. Verified live (2026-04-30 Day 75)

**Master verification block per `feedback_paco_pre_directive_verification.md`.** All deployed-state names referenced in this spec trace back to a row in this table. Verifications run from `beast` SSH alias (host `192.168.1.152`).

| Category | Command | Output |
|----------|---------|--------|
| Beast Postgres roles | `docker exec control-postgres-beast psql -U admin -d controlplane -c "SELECT rolname FROM pg_roles WHERE rolname NOT LIKE 'pg_%'"` | `admin` only |
| Beast Postgres databases | `docker exec control-postgres-beast psql -U admin -d postgres -c "SELECT datname FROM pg_database"` | `controlplane`, `postgres`, `template0`, `template1` |
| Beast Postgres pgvector | `SELECT extname, extversion FROM pg_extension WHERE extname='vector'` | `vector 0.8.2` |
| Beast Postgres tables in public | `\dt public.*` | 12 tables incl `tasks`, `agent_tasks`, `messages`, `memory`, `job_applications`, `chat_history`, `pending_events`, `iot_audit_log`, `iot_security_events`, `user_profile` |
| B2b subscription | `SELECT * FROM pg_subscription` | `controlplane_sub` enabled, conninfo `host=192.168.1.10 port=5432 dbname=controlplane user=admin password=adminpass` |
| Beast Garage listeners | `ss -tlnp` filtering 390x | `127.0.0.1:3903` admin, `192.168.1.152:3900` S3 LAN |
| Beast Garage health | `curl http://127.0.0.1:3903/health` | "Garage is fully operational" |
| Beast Garage existing buckets | `docker exec control-garage-beast /garage bucket list` | `atlas-state`, `backups`, `artifacts` (created during B1 ship Day 73) |
| Goliath Ollama (LAN) | `curl http://192.168.1.20:11434/api/tags` | models: `qwen2.5:72b`, `deepseek-r1:70b`, `llama3.1:70b` |
| TheBeast Ollama (local) | `curl http://192.168.1.152:11434/api/tags` | models: `qwen2.5:14b`, `mxbai-embed-large:latest`, `llama3.1:8b` |
| TheBeast embedding dim | `POST /api/embeddings model=mxbai-embed-large:latest` | dim=1024 |
| Beast Docker substrate anchors | `docker inspect control-postgres-beast control-garage-beast` | postgres `2026-04-27T00:13:57.800746541Z` healthy/0; garage `2026-04-27T05:39:58.168067641Z` healthy/0 |
| Beast git creds | `cat ~/.git-credentials` (sanitized) | HTTPS PAT for github.com configured |
| Beast git config | `git config --global user.email/user.name` | `sloanz_j@icloud.com / James Sloan` |
| santigrey/atlas repo | `gh repo view santigrey/atlas` (from CK) | empty, public, no default branch yet, ready for first push |

**Verification host:** Beast SSH alias (`192.168.1.152`), CK SSH alias (`192.168.1.10`)
**Verification timestamp:** 2026-04-30 Day 75, late afternoon UTC

**Discoveries from this verification that drove v3 corrections:**
- B2b uses `admin` role + `controlplane` database + `adminpass` password. The fictional `replicator_role` + `alexandra_replica` Atlas v1/v2 referenced do not exist.
- Garage already has 3 buckets pre-allocated from B1 ship (`atlas-state`, `backups`, `artifacts`) -- v1/v2 spec's `atlas-working-memory/atlas-artifacts/atlas-incoming` would have been a naming collision and the third name `incoming` is missing entirely.
- `controlplane` database has 12 existing tables in `public` schema; Atlas owned tables go in separate `atlas` schema to avoid namespace collision.
- Embedding model is `mxbai-embed-large` at dim 1024 -- this is the dimensionality Atlas pgvector schema must match.
- Goliath Ollama works fine on LAN -- Tailscale not needed for v0.1.

These discoveries are why P6 #20 was banked and why this Verified live section is now mandatory for every Paco-authored directive.

---

## 1. Executive scope

Atlas v0.1 ships the **full charter scope** per CEO ratification Day 75: agent runtime on Beast PLUS all three sub-functions (Talent Operations, Infrastructure, Vendor & Admin) per Charter 5. This is the most ambitious build cycle in this engagement. CEO ratified Option C with eyes open on placement-slip risk and aggressive sequencing assumptions.

**What ships when v0.1 is done:**
- Atlas the agent: a multi-node-native AI operations agent with persistent memory, tool execution, and substrate-grade discipline, running on Beast as a self-contained agent (own MCP server + Postgres atlas schema in controlplane DB + Garage S3 buckets + embeddings + working memory + tool execution), with inference offloaded to Goliath via Qwen 2.5 72B.
- Talent Operations sub-function: recruiter watcher, application logger, LinkedIn presence execution, interview scheduling.
- Infrastructure sub-function: Atlas owns operational responses for the homelab Atlas inherits from H1.
- Vendor & Admin sub-function: vendor account state tracking, calendar awareness, billing visibility, expense logging.

**What v0.1 explicitly DOES NOT ship:**
- Autonomous action on irreversible decisions (always escalates per charter)
- Brand voice / public posting on Sloan's behalf (Brand & Market is CEO-direct)
- Hardware-class decisions, vendor cancellations, recruiter-outreach-with-personal-voice
- Per Scholas capstone code (separate thread; capstone deadline drives demo gate but not Atlas spec scope)

## 2. Substrate dependencies (all satisfied per Section 0)

| Dependency | Status | Reference |
|------------|--------|-----------|
| B2a Postgres+pgvector on Beast | CLOSED 7/7 gates; pgvector 0.8.2 | Day 72 |
| B2b Logical replication CK->Beast | CLOSED 12/12; subscription `controlplane_sub` enabled; nanosecond anchor `2026-04-27T00:13:57.800746541Z` | Day 72 |
| B1 Garage S3 on Beast | CLOSED 8/8 + 6/6 bonus; 3 buckets `atlas-state/backups/artifacts`; anchor `2026-04-27T05:39:58.168067641Z` | Day 73 |
| D1 MCP Pydantic limits | VERIFIED | Prior |
| D2 homelab_file_write tool | VERIFIED + used live ~50+ times | Prior |
| H1 Observability | SHIPPED 9 phases / 12 ESCs / 0 substrate disturbances | Day 74 |
| Goliath inference (LAN 192.168.1.20:11434) | Llama 3.1 70B + DeepSeek R1 70B + Qwen 2.5 72B operational | Verified live this turn |
| TheBeast embeddings (LAN 192.168.1.152:11434) | mxbai-embed-large:latest, dim=1024 | Verified live this turn |
| MCP server on CK | 12+ tools incl. homelab_file_write | Prior |

**B2b + Garage anchors must remain bit-identical through Atlas v0.1 build.** Hard invariant continues from H1.

## 3. Charter alignment

Per Charter 5 (RATIFIED Day 72):

- **Mission:** Run the business. Keep the infrastructure alive, the talent pipeline moving, and the administrative load off the CEO.
- **Owns:** Infrastructure / Talent operations / Vendor & admin (all 3 sub-functions in v0.1)
- **Decides:** Routine operational responses within agreed playbooks
- **Escalates:** Anything irreversible (deletion, public posting, vendor cancellation), recruiter outreach with personal voice, new vendor adoption, security incidents, hardware-class decisions, anything affecting brand voice
- **Reports to:** COO (Paco)
- **Build location:** Beast (charter-literal per CEO Day 75 Decision A1) -- atlas schema in controlplane DB, Garage object store with existing pre-allocated buckets, embeddings via local TheBeast Ollama, **own MCP server**, tool execution, working memory; large-model inference offloaded to Goliath via LAN
- **Multi-node-native:** First owned agent that lives on multiple homelab nodes; portfolio piece for Applied AI Engineer placement narrative
- **Multi-MCP-host:** Atlas hosts its own MCP server (inbound) AND consumes CK's MCP server (outbound). Demonstrates multi-host MCP architecture, a non-trivial Applied AI Engineer competency.

## 4. Architecture (corrected v3 -- all-Beast, multi-MCP-host, real names)

```
BEAST (Atlas's home, charter-literal, 192.168.1.152):
+----------------------------------------------------------+
| ATLAS PROCESS (Python 3.11+ via deadsnakes, systemd)     |
|   - main loop (task dispatch + handler routing)          |
|   - atlas.db (Postgres pool to controlplane DB)          |
|   - atlas.storage (Garage S3 client to existing buckets) |
|   - atlas.embeddings (TheBeast Ollama @ localhost:11434) |
|   - atlas.inference (Goliath Ollama @ 192.168.1.20:11434)|
|   - atlas.tools (Atlas-owned tool implementations)       |
|   - atlas.mcp_client (calls OUT to CK MCP for cross-host)|
|   - atlas.mcp_server (exposes Atlas tools INBOUND)       |
|                                                          |
| ATLAS-OWNED STATE (on Beast):                            |
|   - Postgres `atlas` schema in controlplane DB           |
|     (separate from existing public.* tables)             |
|   - Postgres replica reader (controlplane DB itself is   |
|     the replicated DB via subscription `controlplane_sub`)|
|   - Garage existing buckets: atlas-state (primary),      |
|     backups (cross-cycle), artifacts (produced files)    |
+----------------------------------------------------------+
         |                              ^
         | inference RPC (HTTP)         | inbound MCP (HTTPS)
         v                              |
GOLIATH (LAN 192.168.1.20)           ALL CALLERS:
  Ollama: Qwen 2.5 72B primary       Paco / Alexandra orchestrator / CEO
          DeepSeek R1 70B fallback   call Atlas's MCP server directly
          Llama 3.1 70B fallback     at https://<beast-host>:<port>/mcp

         ^
         | outbound MCP (HTTPS) -- for tools Atlas doesn't host
         |
CISCOKID (existing MCP server, 192.168.1.10)
  Endpoint: https://sloan3.tail1216a3.ts.net:8443/mcp
  Tools: homelab_ssh_run, homelab_file_read, homelab_file_write, etc.
  Atlas authenticates as a privileged client
  ACL applies (Atlas not authorized for unrestricted control-plane writes)
```

**Why two MCP roles:**

- **Server role:** Atlas exposes its own capabilities (atlas_submit_task / atlas_get_status / atlas_log_application / atlas_log_expense / etc.) so callers reach Atlas via a clean protocol. This is the Beast-resident MCP server. **NEW capability built in Cycle 1.**
- **Client role:** Atlas needs to operate on hosts other than Beast (run commands on CK, read SlimJim metrics, etc.). Rather than reinvent that gateway on Beast, Atlas reuses CK's existing MCP server as a client.

## 5. Cycle ordering + demo gate

```
CYCLE 1: RUNTIME           (Atlas process on Beast, charter-literal, includes own MCP server)
   |
   v
CYCLE 2: TALENT OPS        (recruiter watcher + app logger + LinkedIn + interview scheduling)
   |
   v
CYCLE 3 starts:            (alert ingestion + restart playbooks first)
   |
   v
[DEMO GATE -- mid-Cycle-3] (record once, edit twice -- after 3A+3B close)
   |
   v
CYCLE 3 continues:         (backup verify + security posture)
   |
   v
CYCLE 4: VENDOR & ADMIN    (account state tracking + calendar + billing + expenses)
   |
   v
v0.1 SHIPS
```

**Demo gate placement:** mid-Cycle-3, after phases 3A (alert ingestion) and 3B (restart playbooks) close. Demo recording window: May 24-28. Hard backsolve: 3A + 3B close by ~May 22.

## 6. Aggressive sequencing principles

Per Day 75 CEO ratification of folded gates AND parallelization:

### 6.1 Folded gate phases

H1 split phases conservatively. Atlas folds where H1 patterns are now banked + safe:
- Skeleton + initial-up + healthcheck poll combine when stack is well-understood
- UFW rule additions land alongside the service config that requires them
- Spec amendments fold into close-out commit of the phase that surfaced them

### 6.2 Parallelization across nodes

Where surfaces don't conflict:
- Track A (PD on Beast): runtime build, sub-function service implementations, MCP server build
- Track B (CEO + Paco): external integration setup (Gmail OAuth, LinkedIn API, vendor API keys, Calendar OAuth)

NOT applicable when: same compose project / config / UFW state, sequential dependency, or substrate-anchor-affecting work.

### 6.3 Banked H1 patterns reused

- Multi-host preflight matrix (P6 #16)
- Bind-mount UID alignment (P6 #18)
- Compose feature mode-compatibility check (P6 #19)
- Bridge NAT Path 1 generalization
- Standing closure pattern for literal-PASS + spirit-partial cases
- Bidirectional one-liner handoff protocol
- **NEW: Pre-directive verification discipline (P6 #20 + 5th memory file)**

## 7. Timeline back-schedule

```
June 1               <- Conservative capstone deadline (CEO: end of May / early June)
May 24-28            <- Demo recording window
May 18-22            <- Cycle 3 phases 3A + 3B close
May 14-18            <- Cycle 2 (Talent Ops) closes
May 6-12             <- Cycle 1 (Runtime) closes
2026-04-30 (TODAY)   <- Spec ratified v3 + Cycle 1A in flight

May 28-June 4        <- Cycle 3 phases 3C + 3D close
June 4-14            <- Cycle 4 (Vendor & Admin) close
June 14-18           <- v0.1 SHIPS
```

**Placement-slip risk acknowledgment (CEO Day 75):** if cycles surface unexpected escalation chains, v0.1 may slip 2-4 weeks. CEO accepts this risk. Mitigation: demo gate timing chosen so capstone + placement narrative ship before any post-demo slip.

## 8. CYCLE 1 -- RUNTIME (Atlas process on Beast, with own MCP server)

**Cycle scope:** Atlas the agent process running on Beast with full substrate access. Reports to Paco via the MCP server. Exposed to Alexandra orchestrator on CK as an MCP peer.

**Cycle dependencies:** All substrate dependencies satisfied per Section 0 + Section 2.

### 1A -- Atlas package skeleton on Beast (folded preflight + scaffold)

**Status:** IN FLIGHT (PD executing per resolved preflight ESC at commit `7d29c6c`)

**Scope:** Project directory at `/home/jes/atlas/` on Beast. Python 3.11+ via deadsnakes PPA, pyproject.toml, src layout. Initial dependencies: psycopg[binary,pool], boto3, pydantic, httpx, structlog, mcp. Git push to `github.com/santigrey/atlas`.

**Preflight (P6 #16, corrected per ESC #1 ruling Day 75):**
- Python 3.11+ via deadsnakes PPA (Path A; Beast jammy default 3.10 insufficient)
- Beast disk free > 20GB (verified live, 4.0T free)
- Postgres reachable via `~/.pgpass` for `admin/controlplane/adminpass` at `127.0.0.1:5432` (NOT fictional replicator_role/alexandra_replica)
- Garage health at `http://127.0.0.1:3903/health` (admin endpoint, NOT S3 listener `:3900`)
- Goliath LAN reachable at `http://192.168.1.20:11434/api/tags` (Tailscale Path B; LAN sufficient for v0.1)
- mcp Python SDK installable (1.27.0 verified)

**Acceptance gates:** per ESC ruling. Cycle 1A close-out fold includes: paco_review + spec amendments E.1 (real names) + P6 #20 banking + 2 new P5 carryovers (rotate adminpass, Beast Tailscale enrollment if needed).

### 1B -- Postgres connection layer

**Scope:** `atlas.db` module providing pooled connection to local Postgres on Beast. Connection target: `controlplane` database via `admin` user (same DB used by B2b subscription; atlas-owned tables live in a separate `atlas` schema to avoid collision with existing 12 tables in `public`). Schema migration tool (alembic OR raw SQL). Initial schemas in `atlas` namespace:

- `atlas.tasks` (id, status, created_at, owner, payload jsonb, result jsonb)
- `atlas.events` (id, ts, source, kind, payload jsonb)
- `atlas.memory` (id, ts, kind, content text, embedding vector(1024) for mxbai-embed-large compat, metadata jsonb)

**Replica access:** the `controlplane` database itself is the B2b replica via subscription `controlplane_sub`. Atlas reads cross-agent context from existing `public.*` tables (12 tables: agent_tasks, chat_history, iot_audit_log, iot_security_events, job_applications, memory, messages, pending_events, tasks, user_profile + 2 retired) directly. Read-only by convention; writes only to `atlas.*`.

**Acceptance gates:**
1. Connection pool initializes against `controlplane` DB without errors
2. Migration applies cleanly; 3 tables present in `atlas` schema (verify via `\dt atlas.*`)
3. Cross-schema read query succeeds: `SELECT count(*) FROM public.agent_tasks` returns N rows
4. Embedding column dimension is 1024 (matches mxbai-embed-large)
5. Standing anchor: B2b + Garage anchors bit-identical

### 1C -- Garage S3 client + existing bucket adoption

**Scope:** `atlas.storage` module wrapping boto3 against local Garage endpoint (admin `127.0.0.1:3903`, S3 LAN `192.168.1.152:3900`). **Bucket adoption (NOT creation):** B1 ship pre-allocated 3 buckets that Atlas adopts:

- `atlas-state` -- Atlas's primary state bucket (working memory, ephemeral state)
- `backups` -- shared backup destination (Atlas writes backup artifacts here)
- `artifacts` -- shared produced-file destination (Atlas writes report outputs here)

If an additional bucket is needed for incoming uploads (Cycle 2 recruiter email attachments etc.), Atlas creates `atlas-incoming` in this phase via Garage admin API (one-line addition; not a new architectural decision).

**Path conventions:** keys prefixed by Atlas function (`tasks/<task_id>/...`, `memory/<kind>/<id>`, `events/<ts>/...`). Documented in atlas-config.

**Per-bucket encryption** deferred to v0.2 hardening per banked P5.

**Acceptance gates:**
1. boto3 client connects to S3 endpoint without auth errors
2. Lists 3 existing buckets correctly (verifies adoption, not creation)
3. Creates `atlas-incoming` bucket if Cycle 2 needs it (otherwise defers)
4. Round-trip put + get + delete on a small test object in `atlas-state`
5. Standing anchor preserved

### 1D -- Goliath inference RPC

**Scope:** `atlas.inference` module abstracting model selection. Default routing:
- Small/embed -> TheBeast Ollama at `http://localhost:11434` (Atlas runs on TheBeast, embed is local-loopback; verified models: qwen2.5:14b, mxbai-embed-large, llama3.1:8b)
- Large -> Goliath Ollama at `http://192.168.1.20:11434` (verified models: qwen2.5:72b primary, deepseek-r1:70b, llama3.1:70b)

Per-call model override. Streaming and non-streaming modes. Token usage logged to `atlas.events`.

**Acceptance gates:**
1. Synchronous call to `qwen2.5:72b` on Goliath returns valid completion
2. Streaming call yields tokens incrementally
3. Token usage row inserted into `atlas.events`
4. Failover to next model if primary times out
5. Standing anchor preserved

### 1E -- Embedding service

**Scope:** `atlas.embeddings` module. Default model: `mxbai-embed-large:latest` on TheBeast Ollama (localhost since Atlas runs on TheBeast). Dimension 1024 (verified live). API: `embed(text: str | list[str]) -> list[list[float]]`. Batch support. LRU cache.

**Acceptance gates:**
1. Single text embed returns vector of dimension 1024
2. Batch embed returns N vectors for N inputs
3. Cache hit on repeated input within TTL
4. atlas.memory embedding column accepts the vectors (dim match)
5. Standing anchor preserved

### 1F -- MCP client gateway (outbound to CK)

**Scope:** `atlas.mcp_client` module connecting to CK MCP server `https://sloan3.tail1216a3.ts.net:8443/mcp` as privileged client. Tool registry pulled at startup; ACL applied (Atlas not authorized for unrestricted writes to /home/jes/control-plane/). Tool calls logged to `atlas.events`.

**Acceptance gates:**
1. Atlas connects to CK MCP server, retrieves tool list
2. Successfully calls a read-only tool (e.g., `homelab_ssh_run` to ciscokid `whoami`)
3. ACL blocks unauthorized calls (verified via attempted blocked tool)
4. Tool call event logged with correct schema
5. Standing anchor preserved

### 1G -- Atlas MCP server (NEW capability, inbound on Beast)

**Scope:** `atlas.mcp_server` module. Beast hosts an HTTPS MCP server exposing Atlas's capabilities. Tools registered initially:
- `atlas_submit_task` (returns task_id)
- `atlas_get_status` (queries by id)
- `atlas_get_result` (retrieves completed result)
- `atlas_health` (returns Atlas system status)

**Transport:** HTTPS via Beast hostname. TLS strategy TBD in this phase (options: Tailscale certs if Beast enrolled, OR self-signed for LAN-only initial, OR Let's Encrypt if Beast becomes routable). PD surfaces TLS path choice via paco_request before implementation.

**UFW:** LAN-restricted (no public exposure).

**Authentication:** Bearer token + ACL (matching CK MCP pattern).

**Acceptance gates:**
1. systemd unit `atlas-mcp-server.service` enabled + starts on boot
2. HTTPS endpoint reachable from CK + Goliath via LAN
3. UFW allows MCP port from LAN only; blocks public
4. Tool list returned via JSON-RPC matches the 4 registered tools
5. `atlas_submit_task` accepts task; `atlas.tasks` row inserted with task_id
6. `atlas_get_status` returns correct status for known task_id
7. ACL test: token without permission rejected
8. Standing anchor preserved

### 1H -- Atlas main loop + task dispatch

**Scope:** Atlas runs as long-lived service on Beast (systemd unit `atlas.service` separate from atlas-mcp-server.service). Main loop polls `atlas.tasks` for pending work, dispatches to handler.

**Acceptance gates:**
1. systemd unit `atlas.service` enabled + starts on boot
2. Main loop picks up pending task within polling interval
3. Dispatch routing works: echo task -> echo handler; llm task -> Goliath inference handler
4. Result written to `atlas.tasks`; status transitions correctly
5. End-to-end smoke: Paco -> atlas_submit_task -> atlas.tasks -> handler -> result via atlas_get_result; round-trip < 5s for echo task
6. Standing anchor preserved

### 1I -- Cycle 1 close (ship report fragment + scorecard)

**Scope:** Cycle 1 ship report (subset of v0.1 ship report). Validates Atlas runtime is operational + own MCP server is reachable + Paco can dispatch a task end-to-end.

**Acceptance gates:**
1. All Cycle 1 phase gates closed
2. End-to-end smoke test passes
3. Cycle 1 anchors documented (Atlas systemd start times for both services, MCP server cert details, atlas schema row count, Garage atlas-* bucket inventory)
4. Standing anchor: B2b + Garage bit-identical

## 9. CYCLE 2 -- TALENT OPS

**Cycle scope:** Recruiter watcher + application logger + LinkedIn presence execution + interview scheduling.

**Cycle dependencies:** Cycle 1 closed.

### 2A -- Recruiter watcher

**Scope:** Atlas polls Gmail (OAuth) for inbound recruiter emails. LLM extracts structured data. Stores in `atlas.recruiter_contacts`. Notifies Paco via Atlas's own MCP for high-priority items.

**Track B parallel (CEO):** Gmail OAuth setup, scope `gmail.readonly` initially.

**Acceptance gates:** OAuth complete; polling fetches new messages; LLM extraction returns structured payload; row inserted; high-priority notification fires; standing anchor preserved.

### 2B -- Application logger

**Scope:** Postgres-backed funnel state in `atlas` schema:
- `atlas.applications`
- `atlas.application_events`

Ingest paths: Paco (manual `atlas_log_application` MCP), recruiter watcher (auto on confirmed-applied), Browser-Use/future LinkedIn.

**Note:** existing `public.job_applications` table from prior orchestrator work remains untouched. Atlas's own funnel lives in `atlas.applications` to avoid altering replicated B2b state. Cross-reference query if needed for migration in future cycle.

**Acceptance gates:** schema applied; manual logging via MCP; auto-creation from recruiter watcher; funnel report; anchor preserved.

### 2C -- LinkedIn presence execution

**Scope:** Post drafting (CEO templates); CEO ratifies before publish. Recruiter outreach drafts; CEO approves voice. Atlas drafts but never sends (charter-aligned).

**Acceptance gates:** drafting succeeds; stored in `atlas.scheduled_posts` with `awaiting_ceo_approval`; approval flow; no auto-publish; anchor preserved.

### 2D -- Interview scheduling

**Scope:** Calendar OAuth (Google). Atlas reads availability + drafts slot proposals. CEO ratifies before send. Atlas adds confirmed events with CEO approval.

**Acceptance gates:** OAuth complete; calendar read; slot proposal respects window; CEO approval flow; no autonomous mutations; anchor preserved.

### 2E -- Cycle 2 close (Talent Ops ship)

**Acceptance gates:** all Cycle 2 phase gates closed; end-to-end Talent Ops workflow verified; anchor bit-identical.

## 10. CYCLE 3 -- INFRASTRUCTURE (with mid-cycle DEMO GATE)

**Cycle scope:** Atlas owns operational responses for the homelab. Routine ops only.

**Cycle dependencies:** Cycles 1 + 2 closed; H1 observability stack live.

### 3A -- Alert ingestion

**Scope:** Atlas polls Prometheus alerts API on SlimJim (`http://192.168.1.40:9090/api/v1/alerts`). Classifies alerts (routine vs escalation). Acts per playbook OR notifies Paco.

**Acceptance gates:** read alerts; classification routing; routine playbook execution; escalation notification; anchor preserved.

### 3B -- Restart playbooks

**Scope:** Per-service restart playbooks defined as YAML in `santigrey/atlas` repo. CEO ratifies playbook before execution. Atlas uses CK MCP `homelab_ssh_run` outbound for cross-host restarts.

**Acceptance gates:** YAML schema ratified by CEO; routine restart per playbook; substrate-class issues escalate; anchor preserved.

### [DEMO GATE] -- Capstone + Placement (record once, edit twice)

**Trigger:** 3A + 3B close. Target window: May 24-28.

**Production model:** B1 -- single recording, two cuts post-production.

#### Capstone cut (Per Scholas IBM AI Solutions Developer rubric)

Emphasizes: AI/ML mechanics (mxbai-embed-large 1024-dim vector search, RAG with Atlas's working memory in atlas-state bucket, Pydantic schema-driven LLM extraction), multi-model architecture (small embed local + large inference Goliath), agentic patterns (MCP both client + server roles), data pipeline (Gmail -> LLM extract -> embed -> structured persist), bonus alert ingestion + classification.

Target runtime: 5-8 minutes

#### Placement cut (Applied AI Engineer / AI Platform Engineer rubric)

Emphasizes: multi-node infrastructure (Beast + Goliath + CK + replica + Garage), **multi-MCP-host architecture as portfolio differentiator**, production discipline (5 standing rules, anchor preservation, escalation discipline including this very spec's own evolution), end-to-end ownership, engineering judgment (charter alignment, escalation paths, ACL, secrets, P6 #20 verification discipline), bonus live infrastructure response.

Target runtime: 5-8 minutes

#### Recording protocol

1. Single live workflow combining recruiter email pipeline + triggered Prometheus alert
2. Screen recording: terminal logs, Postgres rows in real-time, Grafana ticks, Atlas systemd journal, MCP tool listings
3. CEO narration live with both audiences in mind
4. Backup recording (different scenario)
5. Both cuts published before capstone deadline

#### Demo Gate acceptance

1. Capstone cut delivered + CEO-ratified as program-quality
2. Placement cut published + CEO-ratified as employer-narrative-quality
3. Both source from same recording
4. Standing anchor pre/post recording sessions bit-identical

### 3C -- Backup verification (post-demo)

**Scope:** Atlas verifies backups (Postgres dumps, Garage objects in `backups` bucket, control-plane git remote). Read-test only. Logs to atlas.events.

**Acceptance gates:** inventory query; read-test on recent backup; backup-missing escalates; anchor preserved.

### 3D -- Security posture monitoring (post-demo)

**Scope:** Periodic posture checks (UFW state, container update advisories, certificate expiry, SSH key rotation). Reports go to Paco; no autonomous action.

**Acceptance gates:** posture script runs on schedule; state changes detected + reported; no autonomous action on findings; anchor preserved.

### 3E -- Cycle 3 close

**Acceptance gates:** all Cycle 3 phases closed (3A + 3B + Demo Gate + 3C + 3D); end-to-end alert response verified; anchor bit-identical.

## 11. CYCLE 4 -- VENDOR & ADMIN

**Cycle scope:** Vendor account state tracking, calendar awareness, billing visibility, expense logging.

**Cycle dependencies:** Cycles 1 + 2 + 3 closed.

### 4A -- Vendor account state (sub-phases per vendor)

Per-vendor read-only connector: Anthropic billing usage, GitHub auth scope, Twilio A2P status, ElevenLabs character usage, Per Scholas portal state (research scrape-friendly path), Google account quotas. Atlas does NOT mutate vendor state in v0.1.

**Acceptance gates:** per-vendor connector exists (sub-phases 4A.1 - 4A.6); state refresh; change detection -> Paco notification; no auto-mutation; anchor preserved.

### 4B -- Calendar awareness

Beyond Cycle 2's interview scheduling: Atlas maintains continuous awareness, surfaces conflicts. Read-only.

**Acceptance gates:** continuous sync; conflict detection; consolidated daily view via MCP; anchor preserved.

### 4C -- Billing visibility

Per-vendor billing fetched + tracked. Atlas surfaces upcoming charges, anomalies, threshold violations.

**Acceptance gates:** per-vendor fetch; anomaly detection; reports to CEO via Paco; no auto-cancellation/payment; anchor preserved.

### 4D -- Expense logging

CEO logs expenses via `atlas_log_expense` MCP tool on Atlas's own MCP server. Atlas categorizes + persists in `atlas.expenses`. Reports on demand.

**Acceptance gates:** MCP tool callable; categorization works; reports correct; anchor preserved.

### 4E -- Cycle 4 close + v0.1 ship

**Acceptance gates:** all Cycle 4 closed; v0.1 ship report covers all 4 cycles; restart safety attestation (both atlas.service + atlas-mcp-server.service recover after Beast reboot); standing anchor: B2b + Garage bit-identical pre/post entire build; v0.1 declared SHIPPED.

## 12. v0.1 ships acceptance

v0.1 is shipped when:

1. All 4 cycles closed with cycle-level acceptance gates passed
2. Demo gate completed (capstone cut + placement cut published)
3. v0.1 ship report published (multi-cycle retrospective)
4. Standing anchor: B2b nanosecond invariant + Garage anchor bit-identical through entire build
5. Both Atlas systemd units enabled, restart-safe, surviving at least one Beast reboot
6. CHARTERS_v0.1.md update: Charter 5 status -> "v0.1 SHIPPED on Beast"
7. CHECKLIST.md final v0.1 audit entry
8. SESSION.md + paco_session_anchor.md refreshed
9. v0.2 spec drafting unblocks

## 13. Standing rules in effect (5 memory files)

1. `feedback_directive_command_syntax_correction_pd_authority.md` (5-guardrail rule + carve-outs + compose-down ESC pre-auth)
2. `feedback_paco_review_doc_per_step.md` (per-step review docs)
3. `feedback_paco_pd_handoff_protocol.md` (handoff protocol + bidirectional one-liner format)
4. `feedback_phase_closure_literal_vs_spirit.md` (closure pattern for literal-PASS + spirit-partial)
5. **`feedback_paco_pre_directive_verification.md` (NEW Day 75 -- mandatory "Verified live" header on every directive that references deployed state; three-layer rule -- mechanical gate, system prompt reminder, adversarial self-check)**

P6 lessons banked: 20 (added P6 #20 Day 75 -- deployed-state-name verification at directive-author time).

B2b nanosecond invariant + Garage anchor bit-identical is the hard substrate invariant. Carries from H1.

## 14. Known unknowns + risks

### 14.1 Risks

- **MCP server hosting on Beast** (1G) is new ground -- TLS strategy TBD; surfaces in Cycle 1G via paco_request before implementation
- **Cycle 2 external integrations** (Gmail, LinkedIn, Calendar OAuth) may surface escalation chains; CEO accepted placement-slip risk; demo gate after 3A+3B mitigates
- **LinkedIn API access** non-trivial onboarding; fallback Browser-Use via Cortez (informational only)
- **Per Scholas portal** likely no API; Cycle 4A may defer to v0.2 if no scrape path
- **Goliath inference reliability** under sustained load not stress-tested; Cycle 1D covers basic, sustained load deferred
- **Atlas restart safety** with two systemd units introduces dependency ordering not exercised in H1; Cycle 1I validates basic, full attestation at v0.1 ship

### 14.2 Known unknowns

- TLS strategy for Atlas MCP server on Beast (Cycle 1G; PD + Paco surface options)
- Atlas MCP server port assignment (Cycle 1G; coordinate UFW)
- Whether `atlas-incoming` bucket needs creation in Cycle 1C or defers to Cycle 2
- Per-vendor connector implementation per of 6 vendors (Cycle 4A research per sub-phase)
- Optimal alert classification logic (Cycle 3A refine in execution)

### 14.3 P5 carryovers (current count: 8)

From H1 (6):
1. Goliath UFW enable (Phase D)
2. KaliPi UFW install + enable (Phase D)
3. grafana-data subdirs ownership cleanup (Phase G)
4. Grafana admin password rotation helper script (Phase G)
5. Dashboard 3662 replacement (Phase H)
6. CK -> SlimJim hostname resolution post-reboot timing fix (Phase I)

From Atlas Cycle 1A ESC (2):
7. Rotate B2b admin password from default `adminpass`; create Atlas-specific limited-scope role
8. Beast Tailscale enrollment if cross-network reachability needed in v0.2+

Atlas v0.1 build will surface additional P5 items; banked into v0.2 hardening pass per existing pattern.

## 15. Spec ratification

v3 ratified by Day 75 CEO discipline RFC approval. Ratification path:

1. v1 drafted by Paco; surfaced for ratification
2. v2 drafted with 3 CEO corrections (repo / demo gate / architecture)
3. v2 committed `9176634`; Cycle 1A dispatched
4. Cycle 1A preflight ESC surfaced 3 deployed-state spec errors + 1 URL error -> P6 #20 banked
5. CEO discipline RFC approved -> 5th memory file banked + system prompt enhancement drafted + retroactive Verified live headers (this v3)
6. v3 commits with full Verified live section + corrected names propagated

---

**Spec authored:** 2026-04-30 Day 75 by Paco (COO)
**Spec status:** RATIFIED v3 (Verified live header active + real names propagated)
**File:** `/home/jes/control-plane/tasks/atlas_v0_1.md`

-- Paco
