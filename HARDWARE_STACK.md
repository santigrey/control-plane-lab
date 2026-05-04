# Santigrey Hardware Stack -- Full Topology

**Version:** 1.0 (companion to PROJECT_ASCENSION_INSTRUCTIONS.md v2.3)
**Source canon:** `/home/jes/control-plane/CAPACITY_v1.1.md` + `/home/jes/control-plane/DATA_MAP.md`
**Purpose:** Every node, its scope, role, routing. Authoritative source is CAPACITY + DATA_MAP. Update when hardware changes.

---

## Design Principles

1. **No new hardware.** Use what's owned. Buy nothing unless an actual capability gap emerges.
2. **Goliath is sacred.** Specialized inference, not general compute. Idle GPU between requests is correct.
3. **Beast is the unsung workhorse.** 256GB RAM, 32 cores, 4.4TB. Most-utilized box.
4. **CiscoKid is control plane + public gateway.** Receives traffic, dispatches work, owns truth.
5. **Mac mini is Apple-bound + CEO daily-driver.** Scope locked; new infra work goes to Linux nodes unless Apple-only.
6. **Scope drives workflow.** New work is routed by node scope, not absorbed by whatever is available.

---

## TIER 1 -- Compute Platform (Alexandra's substrate)

### CISCOKID -- Control Plane & Public Gateway
- **Hardware:** Cisco UCS C240 M4 SFF, Xeon E5-2680 v3 (24c/48t), 64GB RAM, ~4TB disk
- **OS:** Ubuntu 22.04
- **LAN:** 192.168.1.10
- **Tailscale:** sloan3.tail1216a3.ts.net
- **Theme:** Receives traffic, dispatches work, owns truth.

**Services (active):**
- `nginx` -- reverse proxy, Tailscale TLS at `/etc/ssl/tailscale/`
  - `:443` -> `127.0.0.1:8000` (orchestrator dashboard + API)
  - `:8443` -> `127.0.0.1:8001/mcp` (MCP server)
  - `:80` -> 301 to `:443`
- `orchestrator.service` -- FastAPI app, port 8000
  - Endpoints: `/chat`, `/chat/private`, `/agent`, `/ask`, `/voice/*`, `/vision/*`, `/dashboard/*`, `/healthz`, `/readyz`, `/notify`, `/tasks/*`
  - System prompts: `get_alexandra_system_prompt()` (work), `get_private_mode_system_prompt()` (private-work), `get_system_prompt()` (love-mode legacy for `/ask`)
  - Persona handler: `_chat_persona_handler()` (only callable via `/chat/private?intimate=1`)
- `homelab-mcp.service` -- MCP server, port 8001 (homelab tools: SSH, file read/write, message queue, Postgres queries, Atlas tools)
- `control-postgres` (Docker) -- Postgres 16 + pgvector PRIMARY, port 5432 LAN
  - DB: `controlplane`
  - Schemas: `public` (replicated to Beast), `mercury` (Beast-replicated)
- `mercury-scanner.service` -- Mercury sub-agent (Kalshi paper-trading bot)
- `git` primary node -- credential store configured, GitHub PAT chmod 600

**Why it's here:**
- Public-gateway role requires single ingress with TLS
- Postgres primary co-located with orchestrator = sub-ms write latency
- MCP server fronted by nginx for unified TLS

### BEAST -- Workhorse: Data, Agents, Acceleration
- **Hardware:** Dell PowerEdge R640, Xeon Silver 4110 (8c/16t × 2 = 32 threads), 256GB RAM, ~4.4TB disk, NVIDIA Tesla T4 (16GB)
- **OS:** Ubuntu 22.04
- **LAN:** 192.168.1.152
- **Theme:** The box that does five jobs at once because it can.

**Services (active):**
- `control-postgres-beast` (Docker) -- Postgres REPLICA, port 5432 localhost-only
  - DB: `controlplane` (mirror of CK primary via B2b logical replication)
  - Beast-local schema: `atlas` (NOT replicated; Beast-only writes)
- `control-garage-beast` (Docker) -- Garage S3-compatible object store
  - LAN port: 3900
  - Localhost admin: 3903
  - Buckets: `atlas-state`, `backups`, `artifacts`
- `atlas-mcp.service` -- Atlas MCP tools server (10 tools live; tasks/runs/messages/memory ops)
- `atlas-agent.service` -- Atlas agent loop runtime (Phases 1-7 closed; Phase 8+ pending)
- `ollama` -- Tesla T4 inference for embeddings + small models
  - Models: `mxbai-embed-large` (1024-dim), `nomic-embed-text`, `llama3.1:8b`, others
  - URL: `http://192.168.1.152:11434` (env var `OLLAMA_URL`)
- LoRA fine-tuning rig (POC complete Day 62; Llama 3.1 8B + SQuAD)

**Why it's here:**
- Most RAM and cores in fleet -> multi-service host without contention
- Tesla T4 -> embeddings without round-tripping to Goliath
- Storage capacity -> Garage S3 + Postgres replica + LoRA training data
- Atlas agent loop runs here (not Goliath) because operations work is general compute, not GPU-bound

**Critical routing note:** Atlas reads from Beast replica (sub-ms local). Atlas writes go through CK primary, replicated back. Agent-native schemas (`atlas.*`) are Beast-local; never replicated.

### GOLIATH -- Specialized Large-Model Inference
- **Hardware:** NVIDIA DGX Spark (GB10 Grace Blackwell), 128GB unified memory
- **OS:** DGX OS (ARM64)
- **LAN:** 192.168.1.20
- **Tailscale:** 100.112.126.63 (sloan4)
- **Theme:** Ready when called, doesn't multitask.

**Services (active):**
- `ollama` -- large-model inference
  - Models: `qwen2.5:72b` (Alexandra's primary brain), `llama3.1:70b`, `deepseek-r1:70b`
  - URL: `http://192.168.1.20:11434` (env var `OLLAMA_URL_LARGE`)
- LoRA fine-tuning rig for 70B+ models (NeMo AutoModel + LoRA + SQuAD POC complete Day 62)

**Routing rules (orchestrator):**
- `OLLAMA_URL_LARGE` is the dispatch target for: `qwen2.5:72b`, `llama3.1:70b`, `deepseek-r1:70b`, anything matching `:70b` / `:72b` / `:405b` suffix
- `LARGE_MODELS` env var allowlist + suffix match in `get_ollama_url_for_model()` (commit `bf3682c`)
- Persona handler hardcoded to `OLLAMA_URL_LARGE` + qwen2.5:72b (no Claude fallback by design)

**Why it's here:**
- 128GB unified memory -> 70B+ models fit comfortably
- ARM64 + DGX OS optimized for large-model inference
- Idle between requests is correct -- purpose-built specialty

### SLIMJIM -- Edge / IoT / Observability / Future Security
- **Hardware:** Dell PowerEdge R340, Xeon E-2176G (6c/12t @ 3.7GHz), 32GB RAM, ~271GB disk
- **OS:** Ubuntu 24.04
- **LAN:** 192.168.1.40
- **Theme:** Lives at the edge, watches everything else.

**Services (active):**
- Mosquitto MQTT broker -- port 1883 (loopback-anon legacy) + planned 1884 (LAN-authed)
- Netdata -- port 19999 (per-node metrics)
- Prometheus + Grafana -- planned (H1 Phase C)

**Services (planned):**
- Mr Robot home: Wazuh manager + Suricata (defense-in-depth; security NOT co-located with Atlas on Beast)
- IoT command actuation tier (Schlage, relays)

**Why it's here:**
- Lightweight always-on edge node, separate from data plane
- Defense-in-depth principle: security agent ISOLATED from operations agent
- IoT edge actuation should be physically/logically separated from data tier

---

## TIER 2 -- Apple-Bound Infrastructure

### MAC MINI -- Claude Desktop / Cowork Host + CEO Daily Driver
- **Hardware:** Mac mini M4
- **OS:** macOS
- **LAN:** 192.168.1.13 (and 192.168.1.194 per Day 78 reachability cycle)
- **Tailscale:** 100.102.87.70

**Services (active):**
- Claude Desktop (with Cowork enabled) -- principal Cowork/Claude consumer hub for PD execution
- AgentOS Refresh LaunchAgent (`com.sloan.agentos.refresh`) -- 900s cron, AppleScript
- Tailscale macOS client
- OpenSSH server (inbound from CEO + Paco)
- AI_Agent_OS repo at `~/AI_Agent_OS` -- 4.6MB dev workspace
- iCloud Drive `/Users/jes/Library/Mobile Documents/com~apple~CloudDocs/AI` -- 272MB / 7,709 files canon hub

**Future Apple-bound roles (conditional on actual build):**
- iMessage / SMS bridge
- HomeKit bridge
- AppleScript automation expansion
- Apple Notes / Reminders sync
- Apple Mail integration
- Shortcuts.app workflows

**Explicitly NOT on Mac mini:**
- MCP server termination (lives on CK)
- Any Linux-portable workload
- Any service that doesn't require macOS / Apple ID / Apple-only frameworks

**Daily-driver concern:** Mac mini is also CEO's primary workstation. Legitimate but separate from infrastructure scope.

---

## TIER 3 -- Clients, Security, Edge

### KALIPI -- Security & Pentest Lab
- **Hardware:** Raspberry Pi 5 Model B (Cortex-A76), 8GB RAM
- **OS:** Kali Linux (rolling)
- **LAN:** 192.168.1.254
- **Tailscale:** 100.66.90.76
- **Role:** On-demand pentest toolbox (nmap, sqlmap, hydra, nikto). Dispatched via SSH for active scans by future Mr Robot. NOT an always-on Mr Robot service node.

### PI3 -- Security DNS Gateway (TBD)
- **Hardware:** Raspberry Pi 3 Model B Rev 1.2, 1GB
- **OS:** Debian 13 aarch64
- **LAN:** 192.168.1.139
- **Tailscale:** 100.71.159.102
- **Role (pending):** Pi-hole + Unbound + Tailscale subnet router. Standing direction: DNS Gateway. Patched + verified Day 80; role assignment pending.

### CORTEZ -- Engineering Edge AI Workstation
- **Hardware:** HP OmniBook X Flip -- Intel Core Ultra 7 258V (Lunar Lake) + Intel AI Boost NPU + Arc 140V GPU = ~115 TOPS combined, 32GB RAM
- **OS:** Windows
- **LAN:** dead post-Day-69 (wakes onto Tailscale only)
- **Tailscale:** 100.70.77.115
- **Role:** Engineering thin/edge AI client. On-device LLM, OpenVINO, NPU-accelerated Whisper/TTS, mobile dev. Capable of more than thin-client; flagged for upgraded role review.

### JESAIR -- Engineering Thin/Mobile Client
- **Hardware:** MacBook Air, Apple Silicon
- **LAN:** 192.168.1.155
- **Tailscale:** 100.86.193.45
- **Role:** Daily mobile, secondary git node. Capable of more than thin-client; flagged for upgraded role review.

### IPAD PRO -- Primary Mobile UI to Alexandra
### IPHONE PRO 17 -- On-the-go Voice / Telegram Interface

---

## NETWORK FABRIC

### LAN
- Subnet: `192.168.1.0/24`
- Switch: Intellinet 560917 24-port managed gigabit + 2 SFP at `192.168.1.250`
- Router: Netgear CAX80 (gateway)
- MoCA bridge: Trendnet TMO-313C2K connecting CAX80 to office (Day 73; verified 900Mbps, SNR 41-42dB)
- Office: Mac mini on Intellinet switch via MoCA-B

### Tailscale Mesh
- Tailnet: `tail1216a3.ts.net`
- All homelab nodes are members
- Provides: secure remote access, magic-DNS hostnames, Tailscale TLS certs (CK), direct LAN routing on same subnet

### MCP Control Fabric
- CiscoKid `homelab-mcp.service` is the central MCP gateway
- Uses Tailscale IPs when LAN unreliable (Cortez post-Day 69)
- Uses LAN IPs when reliable (Beast / CK / SlimJim / KaliPi / Pi3)
- All clients connect via `mcp-remote` -> `https://sloan3.tail1216a3.ts.net:8443/mcp`

---

## DATA ROUTING (Full Stack)

### Alexandra answers a question (work-mode `/chat`)
```
User -> Telegram bot OR dashboard browser
     -> nginx :443 (CK)
     -> orchestrator :8000 (CK) /chat endpoint
     -> load chat_history from CK primary Postgres
     -> embed query (mxbai-embed-large via Beast Ollama)
     -> pgvector lookup in CK primary memory table
     -> POST /api/chat to Goliath qwen2.5:72b (OLLAMA_URL_LARGE)
     -> tool calls executed via orchestrator tool runtime
     -> response -> guard filter -> user
     -> save turn to chat_history (CK primary; replicates to Beast)
```

### Alexandra answers a question (companion-mode `/chat/private?intimate=1`)
```
User -> dashboard browser (lock closed)
     -> nginx :443 (CK)
     -> orchestrator :8000 (CK) /chat/private endpoint with intimate=1
     -> _chat_persona_handler()
     -> load chat_history for sid `private:<id>` from CK primary
     -> POST /api/chat to Goliath qwen2.5:72b with PERSONA_CORE prompt
     -> response -> user (NO Claude fallback by design; persona endpoint returns 503 if Goliath down)
```

### Atlas executes a scheduled job
```
Atlas agent loop on Beast
     -> reads atlas.tasks via Beast LOCAL schema (not replicated)
     -> executes work (call MCP tools, run jobs, dispatch)
     -> writes to atlas.runs / atlas.events on Beast LOCAL
     -> if cross-domain write needed (e.g. agent_tasks update): hits CK primary via DATABASE_URL -> replicates back
```

### CEO uploads document for Alexandra memory
```
CEO upload -> dashboard / API
     -> orchestrator (CK)
     -> PUT to s3://atlas-state/docs/{uuid} via Beast Garage
     -> trigger embed job (Atlas)
     -> chunked + embedded via Beast Ollama mxbai-embed-large
     -> vectors INSERT to CK primary memory table
     -> metadata replicates back to Beast for local Atlas RAG retrieval
```

### Mercury places paper trade
```
mercury-scanner.service on CK
     -> reads market data via Kalshi API
     -> trade decision via local model (CK)
     -> writes trade row to mercury.trades (CK primary; replicates to Beast)
     -> emits Telegram alert via orchestrator -> Twilio API
     -> Tier-2 dashboard surface via Alexandra
```

---

## STORAGE TIERS

| Tier | Where | Access | What lives here |
|---|---|---|---|
| **Relational primary** | CK Postgres `192.168.1.10:5432` | LAN (UFW from Beast) | Tasks, runs, messages, memory metadata, audit, agent state |
| **Relational replica** | Beast Postgres `127.0.0.1:5432` | Localhost only | Read-only mirror of primary |
| **Vector** | Beast pgvector (in replica DB) | Localhost on Beast | Document embeddings, chunk vectors |
| **Object** | Beast Garage S3 `192.168.1.152:3900` | LAN (UFW from .0/24) | `atlas-state`, `backups`, `artifacts` |
| **Edge/event** | SlimJim Mosquitto `192.168.1.40:1883` | LAN | IoT events, sensor data |
| **Config** | Per-node filesystem | SSH | Compose files, service configs |
| **Secrets** | Per-node filesystem chmod 600 | Owner-only | API keys, S3 creds, DB passwords, RPC tokens |
| **Code/specs** | CK `/home/jes/control-plane/` + GitHub `origin/main` | Git | All specs, checklists, charters, audit |
| **iCloud canon** | Mac mini `/Users/jes/Library/Mobile Documents/com~apple~CloudDocs/AI/` | macOS + iCloud | 272MB accumulated context (notes, prompts, course materials) |

---

## FAILURE MODES

| Failure | Impact | Recovery |
|---|---|---|
| **CK dies** | Loses orchestrator + dashboard + MCP. Beast replica still readable. No new writes. | Restore CK from snapshot; replication catches up. |
| **Beast dies** | Atlas offline. Garage offline. CK still serves dashboard + accepts writes. | Restore Beast; subscription resyncs from CK; Garage from `backups` bucket. |
| **Goliath dies** | Large-model inference offline. Alexandra falls back to Sonnet (work) or returns 503 (persona). | Reboot. No data loss. |
| **SlimJim dies** | IoT command engine offline. Observability gone (post H1). | Reboot. No data loss (MQTT ephemeral). |
| **Disk failure on Beast** | Postgres replica + Garage data lost. | Recreate from CK primary (replication) + restore Garage from latest backup tarball. |
| **CK + Beast both die** | Worst case. Recover from off-site backup (P5 not yet implemented). | Currently no off-site DR; planned for v0.2. |

---

## GROWTH ARCHITECTURE

The hardware stack is designed to grow without restructure:

1. **Tier 1 nodes are stable.** CK / Beast / Goliath / SlimJim. Adding new Tier 1 requires CAPACITY amendment.
2. **Tier 3 nodes are flexible.** Cortez, JesAir, Pi3 can be promoted to specialty roles (DNS Gateway, edge AI, etc.) without restructure.
3. **No new hardware is the default.** ConnectX-7 ports on Goliath are reserved for future second-GX10 stack expansion path.
4. **Off-site DR is the next major addition** (planned v0.2; not yet built).

When new hardware arrives: write a CAPACITY amendment first. Then update HARDWARE_STACK.md from CAPACITY. Code changes follow.
