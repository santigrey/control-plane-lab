# Atlas v0.1 -- Head of Operations Agent (Full Charter)

**Spec status:** DRAFT v2 (awaiting CEO ratification; v1 superseded)
**Charter:** `CHARTERS_v0.1.md` Charter 5 -- Head of Operations: Atlas
**Predecessor:** `docs/H1_ship_report.md` (commit `f9a4e85`) -- substrate dependencies satisfied
**Author:** Paco (architect) -- to be executed by PD per existing handoff protocol
**Repo:** `github.com/santigrey/atlas` (CEO ratified Day 75)
**Build window target:** 2026-04-30 (Day 75, spec ratification) -> ~2026-06-14 (v0.1 ships)
**Hard date:** Capstone demo recording end of May / early June (per CEO Day 75 ratification)

**v2 corrections from v1 (per CEO Day 75 ratification):**
1. Repo name confirmed: `santigrey/atlas`
2. Demo gate moved from end-of-Cycle-2 to **mid-Cycle-3** (after 3A + 3B close: alert ingestion + restart playbooks land; demo includes live infrastructure response on top of recruiter pipeline)
3. **Architecture corrected to charter-literal all-Beast: Atlas runs its own MCP server on Beast.** v1 had Atlas as MCP-client-only calling out to CK's MCP server. v2 has Atlas hosting its own MCP server (inbound: Paco/Alexandra/CEO call Atlas's MCP server on Beast directly) AND being an MCP client (outbound: for tools Atlas doesn't host, e.g. homelab_ssh_run on CK). This is a multi-MCP-host architecture and stronger portfolio narrative.

---

## 1. Executive scope

Atlas v0.1 ships the **full charter scope** per CEO ratification Day 75: agent runtime on Beast PLUS all three sub-functions (Talent Operations, Infrastructure, Vendor & Admin) per Charter 5. This is the most ambitious build cycle in this engagement. CEO ratified Option C with eyes open on placement-slip risk and aggressive sequencing assumptions.

**What ships when v0.1 is done:**
- Atlas the agent: a multi-node-native AI operations agent with persistent memory, tool execution, and substrate-grade discipline, running on Beast as a self-contained agent (own MCP server + Postgres replica + Garage S3 + embeddings + working memory + tool execution), with inference offloaded to Goliath via Qwen 2.5 72B.
- Talent Operations sub-function: recruiter watcher (inbound email parsing + structured logging), application logger (Postgres-backed funnel state), LinkedIn presence execution (post scheduling + recruiter outreach mechanics), interview scheduling (calendar integration).
- Infrastructure sub-function: Atlas owns operational responses for the homelab Atlas inherits from H1 (alert acknowledgment, restart playbooks, backup verification, security posture monitoring).
- Vendor & Admin sub-function: vendor account state tracking (Anthropic / GitHub / Twilio / ElevenLabs / Per Scholas / Google), calendar awareness, billing visibility, expense logging.

**What v0.1 explicitly DOES NOT ship:**
- Autonomous action on irreversible decisions (always escalates per charter)
- Brand voice / public posting on Sloan's behalf (Brand & Market is CEO-direct)
- Hardware-class decisions, vendor cancellations, recruiter-outreach-with-personal-voice
- Per Scholas capstone code (separate thread; capstone deadline drives demo gate but not Atlas spec scope)

## 2. Substrate dependencies (all satisfied)

| Dependency | Status | Reference |
|------------|--------|-----------|
| B2a Postgres+pgvector on Beast | CLOSED 7/7 gates | Day 72 |
| B2b Logical replication CK->Beast | CLOSED 12/12 gates, nanosecond anchor `2026-04-27T00:13:57.800746541Z` | Day 72 |
| B1 Garage S3 on Beast | CLOSED 8/8 + 6/6 bonus, anchor `2026-04-27T05:39:58.168067641Z` | Day 73 |
| D1 MCP Pydantic limits | VERIFIED | Prior |
| D2 homelab_file_write tool | VERIFIED + used live ~50+ times | Prior |
| H1 Observability | SHIPPED 9 phases / 12 ESCs / 0 substrate disturbances | Day 74 |
| Goliath inference | Llama 3.1 70B + DeepSeek R1 70B + Qwen 2.5 72B operational via Tailscale | Prior |
| MCP server on CK | 12+ tools incl. homelab_file_write (Atlas calls OUT to this for cross-host tooling) | Prior |

**B2b + Garage anchors must remain bit-identical through Atlas v0.1 build.** Hard invariant continues from H1.

## 3. Charter alignment

Per Charter 5 (RATIFIED Day 72):

- **Mission:** Run the business. Keep the infrastructure alive, the talent pipeline moving, and the administrative load off the CEO.
- **Owns:** Infrastructure / Talent operations / Vendor & admin (all 3 sub-functions in v0.1)
- **Decides:** Routine operational responses within agreed playbooks
- **Escalates:** Anything irreversible (deletion, public posting, vendor cancellation), recruiter outreach with personal voice, new vendor adoption, security incidents, hardware-class decisions, anything affecting brand voice
- **Reports to:** COO (Paco)
- **Build location:** Beast (charter-literal per CEO Day 75 Decision A1) -- Postgres replica, Garage object store, embeddings, **own MCP server**, tool execution, working memory; inference offloaded to Goliath
- **Multi-node-native:** First owned agent that lives on multiple homelab nodes; portfolio piece for Applied AI Engineer placement narrative
- **Multi-MCP-host:** Atlas hosts its own MCP server (inbound) AND consumes CK's MCP server (outbound). Demonstrates multi-host MCP architecture, a non-trivial Applied AI Engineer competency.

## 4. Architecture (corrected v2 -- all-Beast, multi-MCP-host)

```
BEAST (Atlas's home, charter-literal):
+----------------------------------------------------------+
| ATLAS PROCESS (Python, systemd-managed)                  |
|   - main loop (task dispatch + handler routing)          |
|   - atlas.db (Postgres pool + replica reader)            |
|   - atlas.storage (Garage S3 client)                     |
|   - atlas.embeddings (TheBeast Ollama embed)             |
|   - atlas.inference (Goliath Ollama RPC)                 |
|   - atlas.tools (Atlas-owned tool implementations)       |
|   - atlas.mcp_client (calls OUT to CK MCP for cross-host)|
|   - atlas.mcp_server (exposes Atlas tools INBOUND)       |
|                                                          |
| ATLAS-OWNED STATE (on Beast):                            |
|   - Postgres atlas schema (tasks/events/memory/etc)      |
|   - Postgres replica reader (alexandra_replica via B2b)  |
|   - Garage buckets: atlas-working-memory, atlas-artifacts|
|     atlas-incoming (atlas owns these)                    |
+----------------------------------------------------------+
         |                              ^
         | inference RPC (HTTP)         | inbound MCP (HTTPS)
         v                              |
GOLIATH (Tailscale 100.112.126.63)   ALL CALLERS:
  Ollama: Qwen 2.5 72B primary       Paco / Alexandra orchestrator / CEO
          DeepSeek R1 70B fallback   call Atlas's MCP server directly
          Llama 3.1 70B fallback     at https://<beast-tailscale>:<port>/mcp

         ^
         | outbound MCP (HTTPS) -- for tools Atlas doesn't host
         |
CISCOKID (existing MCP server)
  Tools: homelab_ssh_run, homelab_file_read, homelab_file_write, etc.
  Atlas authenticates as a privileged client
  ACL applies (Atlas not authorized for unrestricted control-plane writes)
```

**Why two MCP roles?**

- **Server role:** Atlas exposes its own capabilities (atlas_submit_task / atlas_get_status / atlas_log_application / atlas_log_expense / etc.) so callers reach Atlas via a clean protocol. This is the Beast-resident MCP server. **NEW capability built in Cycle 1.**
- **Client role:** Atlas needs to operate on hosts other than Beast (run commands on CK, read SlimJim metrics, etc.). Rather than reinvent that gateway on Beast, Atlas reuses CK's existing MCP server as a client. This is consistent with the principle of one MCP server per role rather than one per host.

This is the charter-literal architecture and stronger portfolio narrative than v1.

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

**Demo gate placement (corrected v2):** mid-Cycle-3, after phases 3A (alert ingestion) and 3B (restart playbooks) close. Rationale per CEO Day 75 ratification: the demo is richer with live infrastructure response (Atlas catches a Prometheus alert, runs a playbook, logs to events) on top of the talent ops workflow from Cycle 2. Demonstrates Atlas as actual operations agent, not just data pipeline. Capstone + placement narrative both benefit.

Demo recording window: May 24-28. Hard backsolve: 3A + 3B close by ~May 22.

## 6. Aggressive sequencing principles

Per Day 75 CEO ratification of folded gates AND parallelization:

### 6.1 Folded gate phases

H1 split phases conservatively (compose skeleton -> compose up -> smoke test as separate phases). Atlas folds where H1 patterns are now banked + safe:
- Skeleton + initial-up + healthcheck poll combine when the underlying stack is well-understood
- UFW rule additions land alongside the service config that requires them, not as separate phases
- Spec amendments fold into the close-out commit of the phase that surfaced them

Folding does NOT compromise gate-level acceptance. Each folded phase still has a numbered scorecard; gates just live in one phase instead of three.

### 6.2 Parallelization across nodes

Where surfaces don't conflict, Atlas runs two tracks in parallel:
- Track A (PD on Beast): runtime build, sub-function service implementations, MCP server build
- Track B (CEO + Paco): external integration setup (Gmail OAuth, LinkedIn API access, vendor account API key generation, Calendar OAuth) -- CEO actions that don't require PD

Coordination: each track captures evidence in its own paco_review section; phase closes when both tracks reach gate.

Parallelization NOT applicable when:
- Both tracks would touch the same compose project / config file / UFW state
- One track's output is a prerequisite for the other (sequential)
- Substrate-anchor-affecting work (always single-track for safety)

### 6.3 Banked H1 patterns reused

- Multi-host preflight matrix (P6 #16) applied to multi-node phases
- Bind-mount UID alignment (P6 #18) applied at every container introduction
- Compose feature mode-compatibility check (P6 #19) at every compose.yaml authoring
- Bridge NAT Path 1 generalization for any Prometheus scrape target hitting same-host bridge NAT
- Standing closure pattern (`feedback_phase_closure_literal_vs_spirit.md`) for literal-PASS + spirit-partial cases
- Bidirectional one-liner handoff protocol throughout

## 7. Timeline back-schedule (corrected v2 for mid-Cycle-3 demo)

Working backward from June 1 conservative capstone target:

```
June 1               <- Conservative capstone deadline (CEO: end of May / early June)
May 24-28            <- Demo recording window (1 week pre-deadline buffer)
                     <- Demo Gate: AFTER 3A+3B close (mid-Cycle 3)
May 18-22            <- Cycle 3 phases 3A (alert ingestion) + 3B (restart playbooks) close
May 14-18            <- Cycle 2 (Talent Ops) closes
May 6-12             <- Cycle 1 (Runtime) closes
2026-04-30 (TODAY)   <- Spec ratification + Cycle 1 begins

May 24-28            <- Demo recording (capstone + placement, record once, edit twice)
May 28-June 4        <- Cycle 3 phases 3C (backup verify) + 3D (security posture) close
June 4-14            <- Cycle 4 (Vendor & Admin) close
June 14-18           <- v0.1 SHIPS
```

**Honest assessment:** Cycle 1 (~2 weeks) is the longest. Cycle 2 (~1 week with parallelization) is gated on external integrations. Cycle 3 phases 3A+3B (~1 week) land before demo gate; 3C+3D continue after. Cycle 4 (~10 days) due to 6 vendor sub-phases. Aggressive but achievable given H1 patterns banked + parallelization + folded gates.

**Placement-slip risk acknowledgment (CEO ratified Day 75):** if Cycles 1, 2, or 3A/3B surface unexpected escalation chains (analogous to Phase G's 3-ESC arc), v0.1 may slip 2-4 weeks beyond June 14-18. CEO accepts this risk as the cost of full-charter scope. Mitigation: demo gate timing chosen to ensure capstone + placement narrative ship before any post-demo slip impacts.

## 8. CYCLE 1 -- RUNTIME (Atlas process on Beast, including own MCP server)

**Cycle scope:** Atlas the agent process running on Beast with full substrate access (Postgres replica + Garage S3 + embeddings + working memory + tool execution + Goliath inference) AND its own MCP server exposing Atlas capabilities. Reports to Paco via the MCP server. Exposed to Alexandra orchestrator on CK as an MCP peer.

**Cycle dependencies:** B2a + B2b + B1 + Goliath inference + MCP gateway on CK (all met).

**Cycle phases:**

### 1A -- Atlas package skeleton on Beast (folded preflight + scaffold)

**Scope:** Project directory at `/home/jes/atlas/` on Beast. Python venv (Python 3.11+), pyproject.toml, src layout. Initial dependencies: psycopg[binary,pool], boto3 (for Garage S3), pydantic, httpx, anthropic SDK (optional for direct Anthropic calls), structlog, mcp (Anthropic MCP Python SDK for both client and server roles). Git init + push to `github.com/santigrey/atlas` (CEO ratified Day 75).

**Preflight (P6 #16 single-host):**
- Python version >= 3.11
- Beast disk free > 20GB on /home
- B2b replica reachable from Beast (`psql -h localhost -U replicator_role -d alexandra_replica -c 'SELECT 1'`)
- Garage S3 endpoint reachable (`curl -s http://localhost:3900/health`)
- Goliath Tailscale reachable (`tailscale ping sloan4`)
- MCP Python SDK installable (verify pip-resolves `mcp` package)

**Acceptance gates:**
1. `/home/jes/atlas/` exists with src/ + tests/ + pyproject.toml
2. Venv activates and `pip install -e .` succeeds
3. `python -m atlas --version` returns version string
4. Git remote configured to `github.com/santigrey/atlas`; first commit pushed
5. Standing anchor: B2b + Garage anchors bit-identical pre/post

### 1B -- Postgres connection layer

**Scope:** `atlas.db` module providing pooled connection to B2b replica + connection to local atlas-owned schema for working memory. Schema migration tool (alembic OR raw SQL with version tracking). Initial schemas:
- `atlas.tasks` (id, status, created_at, owner, payload jsonb, result jsonb)
- `atlas.events` (id, ts, source, kind, payload jsonb)
- `atlas.memory` (id, ts, kind, content text, embedding vector(N matching B2a dim), metadata jsonb)

Replica access: read-only from `alexandra_replica` for cross-agent context.

**Acceptance gates:**
1. Connection pool initializes without errors
2. Migration applies cleanly; 3 tables present in `atlas` schema on Beast Postgres
3. Replica read query succeeds against `alexandra_replica` (logical replication consumer)
4. Standing anchor: B2b + Garage anchors bit-identical

### 1C -- Garage S3 client + working memory ingest

**Scope:** `atlas.storage` module wrapping boto3 against local Garage endpoint. Bucket allocation: `atlas-working-memory` for ephemeral state, `atlas-artifacts` for produced files, `atlas-incoming` for received uploads. Path conventions banked. Per-bucket encryption per banked P5 (defer to v0.2 hardening if cycle pressure).

**Acceptance gates:**
1. boto3 client connects + lists buckets without auth errors
2. 3 buckets created
3. Round-trip put + get + delete on a small test object
4. Standing anchor preserved

### 1D -- Goliath inference RPC

**Scope:** `atlas.inference` module abstracting model selection. Default routing: small/embed -> TheBeast Ollama; large -> Goliath Ollama (Qwen 2.5 72B primary; DeepSeek R1 70B + Llama 3.1 70B available). Per-call model override. Streaming and non-streaming modes. Token usage logged to `atlas.events`.

**Acceptance gates:**
1. Synchronous call to Qwen 2.5 72B on Goliath returns valid completion within timeout
2. Streaming call yields tokens incrementally
3. Token usage row inserted into atlas.events
4. Failover to next model if primary times out (configurable timeout)
5. Standing anchor preserved

### 1E -- Embedding service

**Scope:** `atlas.embeddings` module. Default: TheBeast Ollama embedding model (matching B2a pgvector dimensionality -- CEO confirms exact dim in this phase). API: `embed(text: str | list[str]) -> list[Vector]`. Batch support. Cache layer (LRU in-memory + optional Postgres-backed for hot paths).

**Acceptance gates:**
1. Single text embed returns vector of expected dimension
2. Batch embed returns N vectors for N inputs
3. Cache hit on repeated input (within TTL)
4. Standing anchor preserved

### 1F -- MCP client gateway (outbound to CK)

**Scope:** `atlas.mcp_client` module. Atlas connects to CK MCP server (existing `https://sloan3.tail1216a3.ts.net:8443/mcp`) as a privileged client for cross-host tools. Tool registry pulled at startup; ACL applied (Atlas not authorized for unrestricted writes to /home/jes/control-plane/ at this stage; future cycle expands ACL). Tool calls logged to `atlas.events`.

**Why this is separate from the MCP server in 1G:** the client role is consuming CK's existing infrastructure (read), the server role is exposing Atlas's capabilities (write). Different concerns, different code paths.

**Acceptance gates:**
1. Atlas connects to CK MCP server, retrieves tool list
2. Atlas successfully calls a read-only tool (e.g., `homelab_ssh_run` to ciscokid `whoami`)
3. ACL blocks unauthorized calls (verified by attempting a blocked tool, expecting denial)
4. Tool call event logged with correct schema
5. Standing anchor preserved

### 1G -- Atlas MCP server (NEW capability, inbound on Beast)

**Scope:** `atlas.mcp_server` module. Beast hosts an HTTPS MCP server exposing Atlas's capabilities. Tools registered initially:
- `atlas_submit_task` (caller submits a task; returns task_id)
- `atlas_get_status` (caller queries task status by id)
- `atlas_get_result` (caller retrieves completed task result)
- `atlas_health` (returns Atlas system status)

Transport: HTTPS via Tailscale (Beast's Tailscale name + port TBD). TLS certificate via Tailscale certs (same pattern as CK). UFW LAN-restricted (no public exposure).

Authentication: Bearer token + ACL (matching CK MCP pattern -- one token per privileged client; Paco token, Alexandra token, CEO token differentiated).

**Acceptance gates:**
1. systemd unit for `atlas-mcp-server.service` enabled + starts on boot
2. HTTPS endpoint reachable from CK + Goliath via Tailscale
3. UFW allows MCP port from LAN only (Tailscale subnet); blocks public
4. Tool list returned via JSON-RPC matches the 4 registered tools
5. `atlas_submit_task` accepts a task; `atlas.tasks` row inserted with valid task_id
6. `atlas_get_status` returns correct status for a known task_id
7. ACL test: token without permission rejected (HTTP 403 or MCP equivalent)
8. Standing anchor preserved

### 1H -- Atlas main loop + task dispatch

**Scope:** Atlas runs as long-lived service on Beast (systemd unit `atlas.service` separate from atlas-mcp-server.service; the MCP server is just the inbound interface, the main loop is the worker). Main loop polls `atlas.tasks` for pending work, dispatches to handler (initially: echo handler + LLM-completion handler for testing), updates status, writes result.

**Acceptance gates:**
1. systemd unit `atlas.service` enabled + starts on boot
2. Main loop picks up pending task within polling interval
3. Dispatch routing works: echo task -> echo handler; llm task -> Goliath inference handler
4. Result written to atlas.tasks; status transitions correctly (pending -> running -> done/failed)
5. End-to-end smoke: Paco calls atlas_submit_task via MCP -> Atlas main loop picks up -> handler runs -> result available via atlas_get_result; round-trip < 5s for echo task
6. Standing anchor preserved

### 1I -- Cycle 1 close (ship report fragment + scorecard)

**Scope:** Cycle 1 ship report (subset of v0.1 ship report). Validates Atlas runtime is operational + own MCP server is reachable + Paco can dispatch a task end-to-end through Atlas's MCP server and receive structured result.

**Acceptance gates:**
1. All Cycle 1 phase gates closed
2. End-to-end smoke test: Paco -> Atlas's MCP server (Beast) -> atlas_submit_task -> atlas.tasks -> handler -> Goliath inference -> result back via Atlas's MCP server
3. Cycle 1 anchors documented (Atlas systemd start times for both services, MCP server cert details, Postgres atlas schema row count, Garage atlas-* bucket inventory)
4. Standing anchor: B2b + Garage bit-identical

## 9. CYCLE 2 -- TALENT OPS

**Cycle scope:** Recruiter watcher + application logger + LinkedIn presence execution + interview scheduling. Talent Ops directly supports placement and is the richest demoable workflow from a data-pipeline angle.

**Cycle dependencies:** Cycle 1 closed (Atlas MCP server live + main loop dispatching).

**Parallelization opportunity:** Track A (PD building Atlas-side handlers) + Track B (CEO setting up external integrations: Gmail OAuth, LinkedIn API access tokens, calendar OAuth).

### 2A -- Recruiter watcher

**Scope:** Atlas polls Gmail (OAuth) for inbound recruiter emails. LLM extracts structured data (sender / company / role / message intent / urgency). Stores in `atlas.recruiter_contacts`. Notifies Paco via Atlas's own MCP (callback model) for high-priority items.

**Track B parallel work (CEO):** Gmail OAuth setup, scope `gmail.readonly` initially (write capabilities deferred per safety), refresh token captured.

**Acceptance gates:**
1. Gmail OAuth flow complete; refresh token stored as Atlas-readable secret
2. Polling loop fetches new messages since last seen UID
3. LLM extraction returns structured payload matching schema
4. atlas.recruiter_contacts row inserted with extraction
5. Paco-notification fires for high-priority items only (priority threshold configurable)
6. Standing anchor preserved

### 2B -- Application logger

**Scope:** Postgres-backed funnel state. Atlas-managed schema:
- `atlas.applications` (id, company, role, source, applied_date, current_stage, last_activity_ts, notes)
- `atlas.application_events` (id, application_id, ts, kind, payload jsonb)

Ingest paths: Paco (manual MCP call to Atlas's `atlas_log_application` tool), recruiter watcher (auto-create on confirmed-applied), Browser-Use / future LinkedIn scraping.

**Acceptance gates:**
1. Schema applied
2. Manual application logged via `atlas_log_application` MCP tool (now hosted on Atlas's own MCP server)
3. Auto-creation from recruiter watcher triggered when intent = applied
4. Funnel report query returns counts by stage
5. Standing anchor preserved

### 2C -- LinkedIn presence execution

**Scope:** Post scheduling (Atlas drafts based on CEO-approved templates; CEO ratifies before publish; Atlas-only schedules; publish path is an MCP tool that requires CEO approval gate). Recruiter outreach mechanics: Atlas-prepared message drafts based on template; CEO approves voice + tone before send.

**Charter alignment:** "Recruiter outreach that requires personal voice" escalates per charter, so Atlas drafts but never sends.

**Acceptance gates:**
1. Post drafting from CEO-provided template + dynamic data succeeds
2. Drafted post stored in atlas.scheduled_posts with status `awaiting_ceo_approval`
3. Approval flow: CEO marks approved via Atlas MCP call; Atlas transitions to `scheduled`
4. Publish gate: Atlas does NOT auto-publish; publish requires explicit CEO trigger
5. Standing anchor preserved

### 2D -- Interview scheduling

**Scope:** Calendar OAuth (Google). Atlas reads calendar availability + drafts interview slot proposals based on recruiter constraints. CEO ratifies before send. Atlas adds confirmed interviews to calendar (with CEO approval gate).

**Track B parallel (CEO):** Google Calendar OAuth setup.

**Acceptance gates:**
1. Calendar OAuth complete
2. Atlas reads calendar busy/free slots for next 14 days
3. Slot proposal drafted respecting recruiter window + CEO existing commitments
4. CEO approval flow before slot communicated externally
5. Calendar event creation requires explicit CEO approval (no autonomous calendar mutations)
6. Standing anchor preserved

### 2E -- Cycle 2 close (Talent Ops ship)

**Acceptance gates:**
1. All Cycle 2 phase gates closed
2. End-to-end Talent Ops workflow: inbound recruiter email -> Atlas extract -> Paco notify -> CEO sees structured data -> CEO approves auto-log -> application + recruiter contact persisted
3. Standing anchor: B2b + Garage bit-identical

## 10. CYCLE 3 -- INFRASTRUCTURE (with mid-cycle DEMO GATE)

**Cycle scope:** Atlas owns operational responses for the homelab Atlas inherits from H1. Routine ops only (per charter; irreversible escalates).

**Cycle dependencies:** Cycles 1 + 2 closed; H1 observability stack live.

**Special structure:** Demo Gate sits between 3B and 3C. Phases 3A + 3B close first to enable demoable infrastructure response; demo records; then 3C + 3D land post-demo.

### 3A -- Alert ingestion

**Scope:** Atlas subscribes to Prometheus alerts (Alertmanager not yet deployed -- alternative path: Atlas polls Prometheus alerts API). On alert, Atlas classifies (routine vs escalation) and acts per playbook OR notifies Paco.

**Acceptance gates:**
1. Atlas can read alerts from Prometheus alerts API
2. Classification routing works (test alert -> Atlas decision matches expected)
3. Routine playbook execution: e.g., known-flake alert -> log + ack, no action
4. Escalation alert -> Paco notification via Atlas MCP
5. Standing anchor preserved

### 3B -- Restart playbooks

**Scope:** Per-service restart playbooks (e.g., obs-prometheus crash-loop -> Atlas restarts; mosquitto down -> Atlas restarts; pgvector connection failure -> Atlas notifies Paco for substrate-class concern). Playbooks defined as YAML in `santigrey/atlas` repo (charter-grade approval gate; CEO ratifies playbook before Atlas executes).

**Acceptance gates:**
1. Playbook YAML schema defined + ratified by CEO
2. Atlas executes routine restart per playbook (uses CK MCP `homelab_ssh_run` outbound)
3. Substrate-class issues escalate (not auto-restart)
4. Standing anchor preserved

### [DEMO GATE] -- Capstone + Placement (record once, edit twice)

**Trigger:** 3A + 3B close. Target window: May 24-28.

**Production model:** B1 ratified Day 75 -- single recording session, two cuts post-production. Voice/captioning emphasis differs by audience.

#### Capstone cut requirements (Per Scholas IBM AI Solutions Developer rubric)

Emphasizes:
- AI/ML mechanics: embedding model choice, vector similarity search demonstration, RAG pattern with Atlas's working memory, prompt structure for LLM extraction, model selection logic
- Multi-model architecture: small embeddings on TheBeast, large inference on Goliath, model selection logic
- Agentic patterns: tool use via MCP (both client + server roles), structured output via Pydantic schemas, error handling + retry
- Data pipeline: Gmail polling -> LLM extract -> embedding -> structured persistence
- Bonus: alert ingestion + classification (3A/3B work) demonstrates LLM-driven decision routing

Target runtime: 5-8 minutes

#### Placement cut requirements (Applied AI Engineer / AI Platform Engineer rubric)

Emphasizes:
- Multi-node infrastructure: Atlas on Beast + inference on Goliath + MCP server on CK (Atlas as client) + Atlas's own MCP server on Beast (Atlas as server) + replica via B2b + Garage S3
- **Multi-MCP-host architecture as a portfolio differentiator** (Atlas as both server and client)
- Production discipline: substrate anchor preservation, escalation discipline, standing rule architecture, observability via H1 stack
- End-to-end ownership: spec -> implementation -> tests -> deployment -> monitoring + live alert response
- Engineering judgment: charter alignment, escalation paths, ACL on tools (both directions), secrets discipline
- Bonus: live infrastructure response (Atlas catches alert, runs playbook, escalates substrate concerns)

Target runtime: 5-8 minutes

#### Recording protocol

1. Single live workflow combining: inbound recruiter email -> Atlas full pipeline; AND triggered Prometheus alert -> Atlas response
2. Screen recording captures: terminal showing logs, Postgres rows appearing in real-time, Grafana dashboard showing metric ticks, Atlas systemd journal output, MCP server tool listings
3. CEO narration: live during recording with both audiences in mind; can be re-narrated per cut in post if needed
4. Backup recording: 2nd workflow run for safety (different scenario combinations)
5. Both cuts published before capstone deadline + before LinkedIn portfolio update

#### Demo Gate acceptance

1. Capstone cut delivered to instructor, ratified by CEO as program-quality
2. Placement cut published to LinkedIn / portfolio, ratified by CEO as employer-narrative-quality
3. Both cuts source from same single recording session
4. Standing anchor: B2b + Garage bit-identical pre/post recording sessions

### 3C -- Backup verification (post-demo)

**Scope:** Atlas verifies backups exist + are restorable (read-test only; no restore execution). Logs to atlas.events.

**Acceptance gates:**
1. Backup inventory query returns expected backups (Postgres dumps, Garage object listings, control-plane git remote)
2. Read-test on a recent backup succeeds (download + checksum)
3. Backup-missing alert escalates to Paco
4. Standing anchor preserved

### 3D -- Security posture monitoring (post-demo)

**Scope:** Periodic posture checks (UFW state, container update advisories, certificate expiry, SSH key rotation status). Reports go to Paco; no autonomous action on security posture changes (always escalates).

**Acceptance gates:**
1. Posture check script runs on schedule
2. State changes detected + reported
3. No autonomous action taken on security findings (escalates only)
4. Standing anchor preserved

### 3E -- Cycle 3 close

**Acceptance gates:**
1. All Cycle 3 phase gates closed (3A + 3B + Demo Gate + 3C + 3D)
2. End-to-end test: triggered alert -> Atlas response -> outcome verified
3. Standing anchor: B2b + Garage bit-identical

## 11. CYCLE 4 -- VENDOR & ADMIN

**Cycle scope:** Vendor account state tracking, calendar awareness, billing visibility, expense logging.

**Cycle dependencies:** Cycles 1 + 2 + 3 closed.

### 4A -- Vendor account state

**Scope:** Per-vendor connector reading account state read-only (Anthropic billing usage, GitHub auth scope, Twilio A2P status, ElevenLabs character usage, Per Scholas portal state, Google account quotas). Atlas does NOT mutate vendor state in v0.1; tracking only.

**Acceptance gates:**
1. Per-vendor read-only connector exists (one phase per vendor; sub-phases 4A.1 - 4A.6)
2. State refresh on schedule; latest state in atlas.vendor_state
3. Significant change detection -> Paco notification
4. No auto-mutation of any vendor account
5. Standing anchor preserved

### 4B -- Calendar awareness

**Scope:** Beyond Cycle 2's interview scheduling -- Atlas maintains awareness of CEO's calendar, surfaces conflicts, tracks per-event metadata. Read-only; no autonomous calendar mutations.

**Acceptance gates:**
1. Continuous calendar sync; atlas.calendar_events updated
2. Conflict detection across CEO's day
3. CEO sees consolidated daily view via Atlas MCP tool
4. Standing anchor preserved

### 4C -- Billing visibility

**Scope:** Per-vendor billing fetched + tracked. Atlas surfaces upcoming charges, anomalies (e.g., unexpected usage spike), threshold violations. CEO ratifies vendor cost discipline; Atlas reports.

**Acceptance gates:**
1. Per-vendor billing fetch (sub-phases per vendor)
2. Anomaly detection logic
3. Reports to CEO via Paco
4. No auto-cancellation, no auto-payment changes (always escalates)
5. Standing anchor preserved

### 4D -- Expense logging

**Scope:** CEO logs expenses via Atlas MCP tool; Atlas categorizes + persists; reports generated on demand.

**Acceptance gates:**
1. `atlas_log_expense` MCP tool callable on Atlas's own MCP server
2. Categorization works (CEO-defined categories OR LLM-suggested + ratified)
3. Monthly + per-category reports generated correctly
4. Standing anchor preserved

### 4E -- Cycle 4 close + v0.1 ship

**Acceptance gates:**
1. All Cycle 4 phase gates closed
2. v0.1 ship report (analogous to H1 ship report) covers all 4 cycles
3. Restart safety attestation (Atlas survives Beast reboot cleanly; both atlas.service + atlas-mcp-server.service recover)
4. Standing anchor: B2b + Garage bit-identical pre/post entire v0.1 build
5. Atlas v0.1 declared SHIPPED

## 12. v0.1 ships acceptance

v0.1 is shipped when:

1. All 4 cycles closed with cycle-level acceptance gates passed
2. Demo gate completed (capstone cut + placement cut published)
3. v0.1 ship report published (analogous to H1 ship report; multi-cycle retrospective)
4. Standing anchor: B2b nanosecond invariant + Garage anchor bit-identical through entire v0.1 build (the hardest hard invariant; carries forward from H1)
5. Both Atlas systemd units (`atlas.service` + `atlas-mcp-server.service`) enabled, restart-safe, surviving at least one Beast reboot in production
6. CHARTERS_v0.1.md update: Charter 5 build status updated from "to be built" to "v0.1 SHIPPED on Beast"
7. CHECKLIST.md final v0.1 audit entry
8. SESSION.md + paco_session_anchor.md refreshed for post-v0.1 state
9. v0.2 spec drafting unblocks (sub-function deepening + hardening pass already-queued items + new P5 items)

## 13. Standing rules in effect (all 4 from H1)

1. `feedback_directive_command_syntax_correction_pd_authority.md` (5-guardrail rule + carve-outs + compose-down ESC pre-auth)
2. `feedback_paco_review_doc_per_step.md` (per-step review docs)
3. `feedback_paco_pd_handoff_protocol.md` (handoff protocol + bidirectional one-liner format)
4. `feedback_phase_closure_literal_vs_spirit.md` (closure pattern for literal-PASS + spirit-partial)

P6 lessons banked from H1 (count: 19) carry forward. New P6 lessons banked during Atlas v0.1 build extend the catalog.

B2b nanosecond invariant + Garage anchor bit-identical is the hard substrate invariant. Carries from H1.

## 14. Known unknowns + risks

### 14.1 Risks

- **MCP server hosting on Beast** (1G) is new ground -- CK's MCP server is the only homelab reference. Surface area: TLS via Tailscale certs, UFW rule, systemd unit, ACL token model. Manageable risk; H1's nginx-on-CK pattern is reusable.
- **Cycle 2 external integrations** (Gmail OAuth, LinkedIn API, Google Calendar) may surface escalation chains analogous to Phase G's 3-ESC arc. CEO accepted placement-slip risk Day 75; mitigation = demo gate after 3A+3B.
- **LinkedIn API access** may have non-trivial onboarding (developer app approval, OAuth scopes, rate limits). If blocked, fallback path: Browser-Use automation via Cortez (informational only, not autonomous).
- **Per Scholas portal** likely has no API. Vendor & admin Cycle 4 may need to defer Per Scholas tracking to v0.2 if no scrape-friendly path exists.
- **Goliath inference reliability** under sustained Atlas load not yet stress-tested. Cycle 1 1D phase covers basic call validation; sustained-load testing deferred to Cycle 1 close OR v0.2.
- **Atlas restart safety on Beast** with two systemd units (atlas.service + atlas-mcp-server.service) introduces dependency ordering complexity not exercised in H1. Cycle 1I validates basic case; full restart-safety attestation lands at v0.1 ship gate.

### 14.2 Known unknowns

- Exact embedding dimensionality matching B2a pgvector schema (CEO confirms in Cycle 1B/1E)
- Atlas MCP server port assignment (Cycle 1G; coordinate with existing UFW + Tailscale name allocation on Beast)
- Whether CK's MCP server needs new tool registration to know about Atlas's MCP server (probably not; they're peers, not nested)
- Per-vendor connector implementation details for each of 6 vendors in Cycle 4A (research per sub-phase)
- Optimal alert classification logic for Cycle 3A (refine in execution)

### 14.3 P5 carryovers expected

Atlas v0.1 build will surface new P5 items. Banked into v0.2 hardening pass per existing pattern. Existing v0.2 queue (6 items from H1) carries forward; Atlas v0.1 P5 items extend the queue.

## 15. Spec ratification

This spec (v2) requires explicit CEO ratification before any cycle begins.

Upon ratification:
1. Paco commits this spec to `tasks/atlas_v0_1.md` on origin/main (this turn writes to disk; commit happens after CEO ratifies)
2. Cycle 1A directive lands in handoff_paco_to_pd.md
3. PD pulls origin/main + reads handoff + executes Cycle 1A
4. Bidirectional handoff protocol governs all subsequent communication per existing standing rule
5. Repo `github.com/santigrey/atlas` created (CEO action) before 1A's git push gate

---

**Spec authored:** 2026-04-30 Day 75 by Paco (COO)
**Spec status:** DRAFT v2, awaiting CEO ratification
**File:** `/home/jes/control-plane/tasks/atlas_v0_1.md`

-- Paco
