# Santigrey Data Map

**Updated:** 2026-04-27 (Day 72/73)
**Purpose:** Where every piece of data lives, why it lives there, and how it moves.
**Canonical:** `/home/jes/control-plane/DATA_MAP.md` on CiscoKid
**iCloud copy:** `~/iCloud/AI/Santigrey/DATA_MAP.md` (read-only convenience)

---

## Topology at a glance

```
                          INTERNET / TAILSCALE MESH
                                    │
                                    ▼
   ┌──────────────────────────────────────────────────────┐
   │  CISCOKID 192.168.1.10 — control plane / public gateway       │
   │  └─ Postgres PRIMARY (port 5432)        → schema: agent_os    │
   │  └─ nginx :443 / :8443 (Tailscale TLS)                       │
   │  └─ MCP server :8001 (homelab tools)                         │
   │  └─ Orchestrator API + dashboard                             │
   └──────────────────────────────────────────────────────┘
             │ logical replication (B2b, async, lag=0)
             ▼
   ┌─────────────────────────────────────────────────────┐
   │  BEAST 192.168.1.152 — workhorse: data, agents, accel         │
   │  └─ Postgres REPLICA (port 5432, localhost-only)             │
   │  └─ pgvector embeddings (Atlas RAG memory)                   │
   │  └─ Garage S3 :3900 LAN, :3903 admin localhost               │
   │     └─ buckets: atlas-state, backups, artifacts              │
   │  └─ Ollama small/embed models (Tesla T4)                     │
   │  └─ LoRA fine-tuning rig                                     │
   └──────────────────────────────────────────────────────┘

   ┌──────────────────────────┐    ┌────────────────────────────┐
   │  GOLIATH 192.168.1.20  │    │  SLIMJIM 192.168.1.40       │
   │  Large-model inference │    │  Edge / IoT / Observability │
   │  70B/72B/405B Ollama   │    │  Mosquitto MQTT :1883       │
   │  via Tailscale         │    │  (Prometheus+Grafana TBD)   │
   └──────────────────────────┘    └────────────────────────────┘
```

---

## Storage tiers

| Tier | Where | Access | What lives here | Why here |
|---|---|---|---|---|
| **Relational primary** | CiscoKid Postgres `192.168.1.10:5432` | LAN-restricted (UFW [18] from Beast only) | Tasks, runs, messages, memory metadata, audit, agent state | Single source of truth; CiscoKid is control plane |
| **Relational replica** | Beast Postgres `127.0.0.1:5432` | Localhost only on Beast | Read-only mirror of primary (B2b logical replication) | Local reads for Atlas; no CK round-trip |
| **Vector** | Beast pgvector (in replica DB) | Localhost on Beast | Document embeddings, chunk vectors | Co-located with replica = sub-ms retrieval |
| **Object (large)** | Beast Garage S3 `192.168.1.152:3900` | LAN (UFW [15] from 192.168.1.0/24) | `atlas-state` (agent state blobs), `backups` (PG dumps, DR), `artifacts` (portfolio assets) | Decoupled blob store, lifecycle-policy-ready |
| **Edge/event** | SlimJim Mosquitto `192.168.1.40:1883` | LAN | IoT events, sensor data, MQTT pub/sub | Pub/sub fits ephemeral event flow |
| **Config** | Filesystem per-node (`/home/jes/<service>/`) | SSH on the node | Compose files, service configs | Local to deployment |
| **Secrets** | Filesystem chmod 600 per-node | Owner-only on the node | API keys, S3 creds, DB passwords, RPC tokens | Never in git, never in env-printable form |
| **Code/specs** | CiscoKid `/home/jes/control-plane/` + GitHub `origin/main` | Git | All specs, checklists, charters, audit trail, /docs review chain | Canonical project state |

---

## Per-data-type details

| Data type | Lives at | Read by | Written by | Replicated? | Backed up? |
|---|---|---|---|---|---|
| Agent tasks (queue) | CK Postgres | Atlas (Beast replica) | Orchestrator, CEO | ✅ → Beast | Garage `backups` (planned) |
| Agent runs (history) | CK Postgres | Atlas, dashboard | Atlas worker | ✅ → Beast | Garage `backups` (planned) |
| Audit log | CK Postgres | CEO, Paco | All agents | ✅ → Beast | Garage `backups` (planned) |
| Embeddings (vectors) | Beast pgvector | Atlas RAG layer | Atlas embedder | ❌ (rebuildable from source docs) | Source docs in `atlas-state` |
| Memory documents (source) | Beast Garage `atlas-state` | Atlas RAG, CEO | Atlas ingester, CEO uploads | ❌ | Yes (multi-copy planned v0.2) |
| Portfolio artifacts | Beast Garage `artifacts` | CEO, public demo | CEO, Engineering | ❌ | Yes (planned) |
| DB dumps | Beast Garage `backups` | CEO, recovery scripts | Cron job (planned) | ❌ | This IS the backup |
| MCP tool calls | CK Postgres audit table | CEO, Paco | MCP server | ✅ → Beast | Via PG dumps |
| IoT events | SlimJim MQTT (ephemeral) | IoT command engine | Sensors, Schlage, etc. | ❌ (ephemeral) | Critical events copied to PG |
| Secrets / API keys | Filesystem chmod 600 + 1Password | Service at boot | CEO via 1Password | ❌ (security) | 1Password (CEO master) |

---

## Read/write paths (concrete examples)

### Atlas answers a question (RAG)
```
user → Telegram bot (CK)
     → Atlas (Beast)
     → embed query (Beast Ollama nomic-embed-text)
     → pgvector lookup (Beast PG replica)
     → fetch source chunks from `atlas-state` if needed (Beast Garage)
     → prompt + context to Goliath 72B (Ollama via Tailscale)
     → reply back to Telegram
```

### Backup of Postgres
```
CK cron (planned) → pg_dump
                 → pipe through aws-cli to s3://backups/pg/...
                 → timestamped object in Garage
```

### CEO uploads a document for Atlas memory
```
CEO upload → dashboard / API
           → PUT to s3://atlas-state/docs/{uuid}
           → trigger embed job
           → chunked + embedded
           → vectors INSERT to Beast pgvector (replicated metadata back to CK)
```

---

## Failure modes (what's lost if X dies)

| Failure | Impact | Recovery |
|---|---|---|
| **CiscoKid dies** | Loses orchestrator + dashboard + MCP. Beast replica still readable for Atlas. No NEW writes possible until CK back. | Restore CK from snapshot; replication catches up automatically. |
| **Beast dies** | Atlas offline. Garage offline. CK still serves dashboard + accepts writes. | Restore Beast; subscription resyncs from CK; Garage data restored from `backups` bucket if disk lost. |
| **Goliath dies** | Large-model inference offline. Atlas falls back to Beast small models or fails the request. | Reboot Goliath. No data loss (no state stored). |
| **SlimJim dies** | IoT command engine offline. Observability gone (once H1 ships). | Reboot. No data loss (MQTT ephemeral). |
| **Disk failure on Beast** | Postgres replica + Garage data lost. | Recreate from CK primary (replication) + restore Garage from latest backup tarball. |
| **CK + Beast both die** | Worst case. Recover from off-site backup (P5: not yet implemented). | Currently no off-site DR; planned for v0.2. |

---

## What still needs doing (data-layer P5 carryovers)

- Per-bucket S3 keys (split root key into `atlas-svc`, `backups-svc`, `artifacts-svc`)
- TLS for S3 API (currently HTTP; OK on LAN, plan for Tailscale-served TLS)
- Object lifecycle policies (auto-expire old artifacts; retention windows on backups)
- Versioning on `backups` bucket (point-in-time PG recovery)
- Off-site DR target (currently on-prem only)
- DOCKER-USER iptables chain hardening (carryover from B2b/B1)

---

## How to use this file

- This is the **data topology reference**. Stable; updated only when storage architecture changes.
- Companion to `CEO_CHECKLIST.md` (which tracks current work).
- Quick lookup: "where is X stored?" → storage tiers table.
- Quick lookup: "what happens if X dies?" → failure modes table.

---

## Dev workstations & specialty nodes (added 2026-04-27)

These consume the dataplane but do not store it:

| Node | Where | Role | Capability |
|---|---|---|---|
| **Cortez** | TS `100.70.77.115` | Engineering Edge AI workstation | Intel Core Ultra 7 258V (Lunar Lake) + Intel AI Boost NPU + Arc 140V GPU = 115 TOPS combined; 32GB RAM; for on-device LLM, OpenVINO, NPU-accelerated Whisper/TTS, mobile dev |
| **JesAir** | LAN `192.168.1.155` / TS `100.86.193.45` | Engineering thin/mobile client | MacBook Air, daily mobile, Tailscale active |
| **Mac mini** | LAN `192.168.1.13` / TS `100.102.87.70` | MCP host + Claude Desktop / Cowork | macOS, primary always-on Apple bridge |
| **KaliPi** | LAN `192.168.1.254` / TS `100.66.90.76` | Security pentest lab | Existing red-team toolkit |
| **Pi3** | LAN `192.168.1.139` / TS `100.71.159.102` | Security DNS Gateway (TBD) | Pi 3 Model B Rev 1.2, 1GB, Debian 13 aarch64; future Pi-hole + Unbound + Tailscale subnet router |

## Tailscale fabric

All homelab nodes are members of tailnet `tail1216a3.ts.net`. Tailscale provides:
- Secure remote access (mesh VPN, no port forwarding)
- Magic-DNS hostnames (e.g., `cortez`, `pi3`, `sloan4`)
- Tailscale TLS certs for nginx (`/etc/ssl/tailscale/` on CiscoKid)
- Direct LAN routing when on same subnet (no relay overhead)

**MCP control fabric** (CiscoKid `homelab-mcp.service` PID 3631249) uses Tailscale IPs for hosts when LAN unreliable (Cortez post-audit) or LAN IPs when reliable (Beast/CK/SlimJim/KaliPi/Pi3).

---

## Day 73 update (2026-04-28)

### Switch added
Intellinet 560917 at `192.168.1.250` -- **24-port managed gigabit + 2 SFP**. All fleet wired through it. Port map authoritative in CHECKLIST.md Day 73 audit entry. VLAN segmentation **deferred** (MR60 satellite cannot route VLANs).

### Cortez network reachability change
LAN `192.168.1.240` is dead -- Cortez wakes onto Tailscale only. MCP allowed_hosts now uses Tailscale `100.70.77.115`. Substrate-data does not flow through Cortez (Engineering workstation, not data-plane).

### SlimJim baseline post-cleanup
Only :22 (SSH) + :19999 (Netdata) listening. Reserved for H1 deployment: :9090 (Prometheus), :3000 (Grafana), :1883 + :1884 (Mosquitto), :9100 (node_exporter). UFW = 5 rules.

### MQTT broker status
Day 67 YELLOW #5 (snap.mosquitto listener config) -- snap version REMOVED Day 73. Apt mosquitto 2.x install gated to H1 Phase C with **dual-listener config** (1883 loopback-anon for legacy `mqtt-subscriber.service` on CK + 1884 LAN-authed per Day 67 IoT security spec). Closure status: **gated, no longer blocked**.

### IoT command path (informational)
Future data flow once H1 + IoT integration ship:
```
IoT device  ->  Mosquitto :1884 LAN authed (SlimJim)
             ->  mqtt-subscriber.service on CK
             ->  Postgres audit (B2b replicated to Beast)
             ->  Tier 2/3 approval gate (Telegram)
             ->  Schlage / camera / sensor command engine
```
