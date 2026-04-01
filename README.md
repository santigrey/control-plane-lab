# Project Ascension — Distributed AI Platform & Autonomous Agent System

A production-grade AI platform running across a three-node bare-metal cluster. Built as a personal AI companion (Alexandra) with autonomous task execution, voice interaction, and tool-based reasoning.

This is not a demo or proof of concept. Every component described here is running in production on real infrastructure.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                          │
│                  CiscoKid (Ubuntu Server)                       │
│                                                                 │
│  FastAPI Orchestrator (:8000)    MCP Server (:8001)            │
│  ├── 14-tool registry            ├── 12 registered tools       │
│  ├── Multi-step agent loop       ├── SSH execution             │
│  ├── parse_tool_call + TOOLS.run ├── Vector memory search      │
│  ├── Chat endpoint (/chat)       ├── Task lifecycle mgmt       │
│  ├── Wake word endpoint          └── Inter-agent messaging     │
│  └── Vision endpoint (/vision)                                 │
│                                                                 │
│  PostgreSQL + pgvector (Docker)                                │
│  ├── Semantic memory (798+ embeddings)                         │
│  ├── Agent task queue (agent_tasks)                            │
│  ├── Chat history                                              │
│  ├── User profile                                              │
│  └── Inter-agent messages                                      │
├─────────────────────────────────────────────────────────────────┤
│                     INFERENCE LAYER                             │
│                 TheBeast (Ubuntu Server)                        │
│                                                                 │
│  Ollama (Tesla T4 GPU)                                         │
│  ├── mxbai-embed-large (embeddings)                            │
│  └── Local model inference                                     │
├─────────────────────────────────────────────────────────────────┤
│                     OPERATOR LAYER                              │
│                   Mac mini M4 (macOS)                           │
│                                                                 │
│  Claude Desktop + MCP Bridge                                   │
│  ├── homelab-mcp tool access                                   │
│  └── Always-on connectivity to orchestrator                    │
└─────────────────────────────────────────────────────────────────┘
```

## What It Does

**Multi-Step Agent Tool Loop** — The orchestrator receives a user query, calls Claude with tool definitions, parses structured JSON tool calls, executes them via a 14-tool registry, feeds results back, and loops up to 5 iterations before returning a conversational response.

**Agent Task Pipeline** — Agents create tasks in a PostgreSQL queue. A real-time dashboard surfaces pending tasks with approve/reject controls. Execution agents poll for approved work, run it, and write structured results back to the database. Human-in-the-loop approval gates ensure control over autonomous execution.

**Voice Interface** — Browser-based wake word detection captures audio, converts via ffmpeg, transcribes with Whisper (faster-whisper-tiny, CPU), runs a fast Haiku-powered tool loop, and responds via ElevenLabs TTS.

**Telegram Bot** — Text, voice, and photo input. Photos are processed through Claude Vision to extract content, then routed through the chat tool loop for action. Send a photo of an appointment and get it added to Google Calendar.

**Google Calendar + Gmail Integration** — Full read/write Calendar API access. Creates events, handles recurring schedules, surfaces daily agendas. Gmail API polls every 15 minutes for recruiter messages via a systemd service.

**Semantic Memory** — Cross-session memory using pgvector and mxbai-embed-large embeddings. The agent retrieves contextually relevant past interactions at inference time via cosine similarity search. 798+ embeddings stored and growing.

**MCP Server** — 12 registered tools exposed via Model Context Protocol, enabling external Claude agents to interact with the platform: SSH into nodes, search vector memory, create and manage tasks, send messages between agents, read user profile data.

**Real-Time Dashboard** — HTTPS dashboard with status badges (API, Postgres, Ollama, Agent Queue), chat interface, webcam vision greeting, agent task lifecycle panel with approve/reject controls, daily brief, and activity log.

## Stack

| Component | Technology |
|-----------|------------|
| Orchestrator | Python, FastAPI |
| LLM | Claude API (Sonnet 4 for chat, Haiku 4.5 for wake word) |
| Database | PostgreSQL 16 + pgvector (Docker) |
| Embeddings | Ollama + mxbai-embed-large on Tesla T4 |
| Voice | Whisper (faster-whisper-tiny), ElevenLabs TTS |
| Vision | Claude Vision API |
| Messaging | Telegram Bot API |
| Calendar/Email | Google Calendar API, Gmail API |
| Inter-Agent | Model Context Protocol (MCP) |
| Infrastructure | Ubuntu Server, macOS, Tailscale mesh, systemd, nginx |

## Services Running

| Service | Type | Schedule |
|---------|------|---------|
| `orchestrator` | systemd | Always on |
| `alexandra-telegram` | systemd | Always on |
| `recruiter-watcher` | systemd | Gmail poll every 15 min |
| `daily_brief.py` | cron | 7:00 AM daily |
| `evening_nudge.py` | cron | 6:00 PM daily |

## Key Files

```
orchestrator/app.py                          # FastAPI orchestrator, tool loop, endpoints
orchestrator/ai_operator/tools/registry.py   # 14-tool registry
orchestrator/ai_operator/dashboard/dashboard.py  # Real-time dashboard
mcp_server.py                                # MCP server (12 tools)
mcp_stdio.py                                 # MCP stdio bridge for Claude Desktop
telegram_bot.py                              # Telegram bot (text, voice, photo)
voice.py                                     # Whisper STT + ElevenLabs TTS
google_readers.py                            # Google Calendar + Gmail API
recruiter_watcher.py                         # Gmail recruiter polling service
daily_brief.py                               # Morning briefing generator
evening_nudge.py                             # Evening summary
notifier.py                                  # Email + SMS notification layer
```

## Database Schema

9 tables in PostgreSQL:

- `memory` — pgvector semantic memory (798+ rows, 1024-dim embeddings)
- `agent_tasks` — Task queue with approval workflow
- `messages` — Inter-agent message bus
- `chat_history` — Conversation persistence
- `user_profile` — Structured user context
- `job_applications` — Job search pipeline tracking
- `tasks` — Legacy task queue
- `worker_heartbeats` — Service health tracking
- `patch_applies` — Change tracking

## Development

Active daily development since February 2026. Built by James Sloan as part of Project Ascension — a transition from senior infrastructure engineering to AI platform engineering.
