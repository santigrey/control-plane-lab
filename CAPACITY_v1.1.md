# Santigrey Enterprises -- Hardware Org Chart

**Version:** 1.1 (RATIFIED 2026-04-26 by CEO)
**Drafted:** 2026-04-26 AM, by Paco (COO)
**Supersedes:** CAPACITY_v1.0.md (2026-04-25 PM, retained as `CAPACITY_v1.0.md.superseded.<timestamp>`)
**Companion to:** CHARTERS_v0.1.md, CHECKLIST.md

## What changed from v1.0

Three corrections, all surfaced from live verification on 2026-04-26 AM:

1. **Removed phantom MCP migration.** v1.0 said "MCP server endpoint MOVES HERE [to CiscoKid] from Mac mini" and "Mac mini sheds MCP termination." Wrong. CiscoKid was already running `homelab-mcp.service` (PID 2286677) with nginx on `:8443/mcp` proxying to `127.0.0.1:8001`. Mac mini terminated nothing. There was no migration to do.

2. **Removed fictional iMessage and HomeKit bridges.** v1.0 listed both as either existing or new Mac mini roles. Verified absent from process list, LaunchAgents, and binaries. Reclassified as future, conditional roles.

3. **Tightened Mac mini scope language.** v1.0 used broad "Apple-bridged specialty" phrasing. v1.1 says exactly what Mac mini is: a Claude Desktop / Cowork host plus a daily-driver workstation, with future Apple-bound roles only when actually built.

The principle now governing the chart: **scope drives workflow, not the reverse.** Every node has a primary scope. Workflow is a consumer of scope. New work is routed by scope; nodes do not absorb work just because they happen to be available.

## Design Principles (unchanged from v1.0)

1. **No new hardware.** Use what is owned. Buy nothing this quarter unless an actual capability gap emerges.
2. **Goliath is sacred.** Specialized inference, not general compute. Idle GPU between requests is correct.
3. **Beast is the unsung workhorse.** 252 GB RAM, 32 cores, 4.4 TB disk, free. She becomes the most-utilized box.
4. **CiscoKid stays as control plane and public gateway.** Already does this. No change needed.
5. **Mac mini is Apple-bound infrastructure only.** Plus the CEO's daily-driver workstation, which is a separate concern outside the org chart.

## The Hardware Org Chart

### TIER 1 -- Compute Platform (Alexandra's substrate)

**CISCOKID -> Control Plane & Public Gateway** (no migration -- already in place)
- Orchestrator API
- MCP server endpoint (`homelab-mcp.service`, port 8001, nginx-fronted at `:8443/mcp`)
- nginx reverse proxy + Tailscale TLS
- Postgres PRIMARY
- Dashboard, Telegram bot
- Theme: receives traffic, dispatches work, owns truth.

**BEAST -> Workhorse: Data, Agents, Acceleration**
- ATLAS lives here (charter revision -- moved from Goliath in v1.0)
- Postgres REPLICA (new) + WAL archive
- MinIO S3-compatible object store (new) -- backups, artifacts
- Embedding & small-model Ollama (existing, expanded)
- Fine-tuning rig for LoRA on small models (existing POC)
- DR snapshot target for CiscoKid
- Theme: the box that does five jobs at once because it can.

**GOLIATH -> Specialized Large-Model Inference**
- Qwen 2.5 72B primary
- Llama 3.1 70B, DeepSeek R1 70B
- Future: fine-tuning runs on 70B models when needed
- ConnectX-7 ports RESERVED for future second-GX10 stack
- Theme: ready when called, doesn't multitask.

**SLIMJIM -> Edge / IoT / Observability**
- Mosquitto MQTT broker (existing)
- Prometheus + Grafana (new) -- pulls metrics from all nodes
- IoT actuation tier (Schlage, relays, future)
- Wazuh/Suricata security monitoring (deferred -- needs careful tuning)
- Theme: lives at the edge, watches everything else.

### TIER 2 -- Apple-Bound Infrastructure

**MAC MINI -> Claude Desktop / Cowork Host + Future Apple Bridges**

Verified current footprint (2026-04-26 AM probe):
- **Claude Desktop** running with Cowork enabled -- principal Cowork/Claude consumer hub
- **AgentOS Refresh** LaunchAgent (`com.sloan.agentos.refresh`) -- 900s cron, AppleScript, pokes Claude Desktop scheduled tasks
- **Tailscale macOS client** -- mesh participation (required to be macOS-side)
- **OpenSSH server** -- inbound jes@macmini for CEO + Paco
- **AI_Agent_OS repo** at `~/AI_Agent_OS` -- 4.6 MB dev workspace, NOT running as a daemon
- Consumer apps (separate concern, not infrastructure): Slack, Zoom, OBSBOT, Perplexity, OpenAI Atlas

Future Apple-bound roles, conditional on actually being built:
- iMessage / SMS bridge (does not exist today)
- HomeKit bridge (does not exist today)
- AppleScript automation expansion
- Apple Notes / Reminders sync
- Apple Mail integration
- Shortcuts.app workflows

Explicitly NOT on Mac mini:
- MCP server termination (lives on CiscoKid -- always has)
- Any Linux-portable workload
- Any service that doesn't require macOS, Apple ID, or Apple-only frameworks

Theme: things only a Mac can do.

**Note on the daily-driver concern.** Mac mini is also the CEO's primary daily-driver workstation. This is a legitimate but separate use of the same physical machine. The infrastructure scope above is what Santigrey runs on Mac mini; "Sloan uses Mac mini" is about which apps the CEO happens to launch and is not part of the org chart. Don't conflate them.

### TIER 3 -- Clients, Security, Edge

- **KaliPi** -> Security & Pentest Lab (unchanged)
- **JesAir** -> Currently mobile dev thin client. **TO BE EVALUATED** -- CEO flagged for upgraded role review (Apple Silicon, capable of more than thin-client duty).
- **Cortez** -> Currently Windows admin thin client. **TO BE EVALUATED** -- has NPU per CEO flag; possible AI-equipped upgrade. Tailscale resilience issue still open from Day 69.
- **Pi3** -> Registered (192.168.1.139, user sloanzj) but unprobed and unassigned. **TO BE EVALUATED** -- needs role assignment.
- **iPad Pro** -> Primary mobile UI to Alexandra
- **iPhone Pro 17** -> On-the-go voice / Telegram interface

## Charter Revision Carrying Forward From v1.0

**Atlas lives on Beast, not Goliath.** Reason: Atlas's job is running operations -- monitoring, scheduling, recruiter watching, application logging, vendor admin. That is general compute with frequent multitasking. Beast's 252 GB / 32 cores / 4.4 TB lets Atlas run alongside the data tier and the embedding server without contention. Goliath is a single-purpose accelerator and stays focused. Atlas calls out to Goliath when she needs 70B reasoning. Cleaner separation.

**Action on ratification:** update CHARTERS_v0.1.md Charter 5 Build status to read Beast as Atlas's home.

## What This Fixes (mapped to CEO-stated pain points)

| Pain | Fix |
|---|---|
| Beast underutilized | Becomes the busiest box in the fleet. Atlas + DB replica + MinIO + small-model Ollama + LoRA. |
| Goliath not yet earning her cost | Stays specialized; ConnectX-7 reserved for future expansion path; idle GPU is a feature. |
| SlimJim orphaned | Owns observability stack and security monitoring on top of MQTT. |
| Mac mini SPOF + arch mismatch | Scope locked to Apple-bound only. Future roles explicitly conditional. Daily-driver concern factored out of org chart. |
| CiscoKid concentration risk | Data tier replicated to Beast. CiscoKid stays as gateway; if Beast dies, CiscoKid keeps serving. If CiscoKid dies, Beast's replica can be promoted. |

## Migration Sequence (low-to-high risk)

1. ~~Move MCP termination Mac mini -> CiscoKid.~~ **REMOVED -- already in place.**
2. **Beast gets Postgres replica** -- read-only WAL streaming from CiscoKid. No service interruption. (CHECKLIST item B2)
3. **Beast gets MinIO** -- new object store, becomes backup target. (CHECKLIST item B1)
4. **SlimJim gets observability stack** -- Prometheus + Grafana + node_exporter on every node. (CHECKLIST P3)
5. **Build Atlas on Beast** -- first owned agent. Calls Goliath for big-model reasoning. (CHECKLIST P3)
6. **SlimJim gets Wazuh/Suricata** (deferred -- needs careful tuning).

## What This Recommendation Does NOT Include

- Buying a second GX10. ConnectX-7 ports reserved for the future; immediate stack works without it.
- Replacing the Tesla T4 in Beast. Adequate for embeddings and small-model serving.
- Off-site DR target. Beast as on-prem replica is sufficient for a personal venture.
- Building iMessage or HomeKit bridges proactively. Build them only if and when an actual workflow demands them.

**End of v1.1.** Awaiting CEO ratification.
