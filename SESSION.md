# SESSION.md — Project Ascension

## Last Updated
2026-04-02 (Day 52)

## Completed Day 52 — April 2, 2026

**P1 — Security (complete)**
- CiscoKid: UFW enabled (default deny, LAN-only 22/80/443/8000/8001, deny 5432)
- CiscoKid: PostgreSQL rebound to 127.0.0.1 via compose.yaml (Docker bypasses UFW iptables). Committed 261dc8f.
- CiscoKid: .env audit clean — gitignored, not tracked, no hardcoded secrets
- TheBeast: OLLAMA_HOST=0.0.0.0 + UFW LAN-only on 11434/22 (UFW is the access control layer)
- fail2ban running on CiscoKid, TheBeast, SlimJim — sshd jail active on all
- Orchestrator health post-hardening: api=ok, postgres=ok, ollama=ok

**P2 — Kernel Updates (complete)**
- SlimJim: 6.8.0-106 -> 6.8.0-107, clean boot, zero failed units
- TheBeast: 5.15.0-173 -> 5.15.0-174, Ollama active post-reboot, Tesla T4 healthy
- CiscoKid: 5.15.0-173 -> 5.15.0-174, all services recovered, UFW intact, PostgreSQL on 127.0.0.1
- Note: Ubuntu holds kernels back from apt upgrade — dist-upgrade required

**P3 — Housekeeping (complete)**
- CiscoKid: removed 2 dead Docker containers (thirsty_noyce, heuristic_wozniak)
- Mac mini: cleared 8.8GB from ~/Library/Caches
- JesAir: CiscoKid SSH key authorized — CiscoKid can now SSH to JesAir directly
- KaliPi: Tailscale 1.96.4 installed and authenticated — now in mesh
- Mac mini: Tailscale launched and authenticated — now in mesh

**TheBeast Amber Light**
- Dell EMC PowerEdge amber health LED — likely RAID controller BBU draining
- Machine fully operational: Ollama active, Tesla T4 healthy 57-64C
- Do NOT touch hardware — previous CMOS swap caused full OS loss and rebuild
- Action: monitor only, investigate via iDRAC non-destructively next session

**MCP Bridge — RESOLVED via mcp-remote**
- mcp_stdio.py blocking read loop stalls on long SSH commands (60s+), hanging bridge
- Workaround used: fire-and-forget nohup + polling pattern
- Permanent fix needed: SSH ControlMaster or async rewrite — Day 53 priority

**Services Post-Day-52**
- All 7 systemd services active and healthy post-reboot
- pgvector: 907 memory rows | Ollama: 2 models | PostgreSQL: 127.0.0.1:5432 only
- UFW: active on CiscoKid and TheBeast | fail2ban: CiscoKid + TheBeast + SlimJim
## Completed Day 51 — April 2, 2026

### Completed
- Built task_runner.py on CiscoKid (/home/jes/control-plane/task_runner.py) — clean CC task execution via list/get/complete/fail subcommands
- Logged 4 new job applications (Prologis, HPE, Ascendion, Conscious Minds) — total now 62
- **JARVIS UPGRADE — 3 major systems built and deployed:**
  1. **Event Engine** (Phase 1) — event_engine.py (248 lines). Systemd service. Polls Gmail/calendar/tasks every 60s. Priority scoring 1-10. P7+ = Telegram interrupt. P4-6 = pending_events table.
  2. **Tool Chain Engine** (Phase 2) — tools/chains.py + registry upgrade. 3 chain templates. plan_and_execute tool. MAX_STEPS 5→10. Multi-step autonomous execution.
  3. **Live Context Engine** (Phase 3) — context_engine.py (147 lines). Real-time: time/energy/class/events/timeline/interaction. Injected into system prompts.
- All 3 systems verified live — Alexandra adapts to time of day, chains 5 tools, Event Engine tracks tasks
- 7 systemd services active: orchestrator, alexandra-telegram, recruiter-watcher, calendar-alert, homelab-mcp, mqtt-subscriber, event-engine

### Services
- event-engine.service: NEW, active, 60s poll interval
- All other services: active and healthy

## Completed Day 50
- Wake word fixed: Haiku model string corrected (20241022 -> 20251001)
- Error logging added to voice_wake_detect (no more silent failures)
- MCP bridge migrated from JesAir to Mac mini (permanent, always-on)
- Telegram photo handler: photos processed via Claude Vision, routed through /chat tool loop
- Vision endpoint upgraded: accepts prompt parameter for non-webcam use cases (Form import fix)
- Google Drive API enabled and OAuth re-authorized with drive.readonly scope
- Course materials downloaded from professor's shared folder to CiscoKid
- Lirio application submitted + tailored resume/cover letter emailed to Patrick Hunt
- Applications CSV backfilled: 58 total entries from 12/20/2025 through 4/1/2026
- LinkedIn profile updated: headline, About section, Open to Work roles, Featured
- GitHub README created for control-plane-lab (121 lines, architecture diagram, full capability breakdown)
- Profile data updated in PostgreSQL (salary target, target companies, LinkedIn, Per Scholas, timeline)
- Twilio toll-free verification submitted (pending review)
- Course structure mapped: Module 933 (6 lessons, assignments, deadlines)

## Completed Day 49
- Calendar write tool (OAuth re-auth, create_calendar_event, Per Scholas schedule)
- parse_tool_call fix (handles JSON + trailing text)
- Date injection in system prompt
- Wake word switched to Haiku (~7s response)
- Agent task pipeline operational (Paco > approve > CC executes > DB)
- Dashboard upgraded: task lifecycle panel, queue badge, approve/reject
- Ollama restarted on TheBeast
- CiscoKid set as primary git node

## Current Platform Status
- Orchestrator: UP (CiscoKid:8000)
- Ollama: UP (TheBeast:192.168.1.152:11434)
- pgvector: UP (798+ memory rows)
- MCP server: UP (CiscoKid:8001)
- MCP bridge: Mac mini (always-on, migrated from JesAir Day 50)
- Alexandra /chat: RESPONDING (Sonnet tool loop, 14 tools)
- Alexandra wake word: WORKING (Haiku tool loop, ~7s)
- Alexandra calendar: READ + WRITE
- Alexandra Telegram: TEXT + VOICE + PHOTO (vision pipeline)
- Alexandra Google Drive: READ (drive.readonly scope)
- Dashboard: LIVE (task lifecycle, queue badge, approve/reject)
- Recruiter watcher: LIVE (Gmail poll every 15 min)
- Git: CiscoKid primary, JesAir secondary

## Per Scholas Course
- Course: UCI 3097 AI Solutions Developer (2026-CAX-142)
- Instructor: Alexandros Karales (akarales@perscholas.org)
- Schedule: M/W/F 6-9 PM ET, March 30 - June 26 2026 (13 weeks)
- Current: Module 933 - Intro to AI and Tools for Software Engineering
- Course materials downloaded to /home/jes/control-plane/course_materials/
- Canvas: perscholas.instructure.com/courses/3227

## Known Issues
- Wake word latency ~7s
- Twilio toll-free verification pending (1-3 business days)
- Task queue works for research tasks but not code-edit tasks (CC needs direct file access)
- Anthropic rate limits on Max plan during peak hours

## Next Steps (Day 53+)
1. Fix MCP bridge - SSH ControlMaster or async rewrite to prevent long-command hangs
2. TheBeast amber light - investigate via iDRAC/omreport non-destructively
3. Mac mini Chrome mic fix - switch to OBSBOT Tiny SE for wake word
4. Per Scholas homework - Lesson 933.2 Google Cloud Skills Boost Intro to GenAI
5. Demo video of Alexandra for LinkedIn/portfolio
6. Dashboard file/folder upload UI
7. Event acknowledgment flow, chain template expansion, context engine tuning


## Resume Anchor
"Paco - read SESSION.md. Day 52. Full homelab hardened: UFW on CiscoKid+TheBeast, PostgreSQL localhost-only, fail2ban on all Linux nodes, all kernels updated (174/107), P3 housekeeping complete. MCP bridge long-command hang is known issue - fix is Day 53 priority. TheBeast amber LED - monitor only, no hardware changes. Alexandra stack fully operational post-reboot. 907 pgvector rows. 62 applications tracked."
## Day 52 Addendum
- mcp-remote installed as permanent MCP bridge replacement
- claude_desktop_config.json: npx mcp-remote http://192.168.1.10:8001/mcp
- No SSH tunnel. HTTP only. Auto-reconnects on reboot. Bridge stable.
- TheBeast amber light resolved: inlet temp threshold raised 33C to 37C via iDRAC9 (192.168.1.237)
- CiscoKid iDRAC: 192.168.1.35
- Standing Paco rule: search community solutions before declaring a blocker

## Day 52 Evening Addendum
- Twilio local number provisioned: +1 720 902 7314 (Denver local, replaces failed toll-free)
- TWILIO_FROM_NUMBER updated in .env, orchestrator restarted
- A2P 10DLC brand + campaign submitted for carrier approval
  - Brand: James Sloan (Sole Proprietor, $4.50 one-time + $2/month)
  - Messaging service: Alexandra
  - Campaign: Mixed / personal assistant notifications
  - Status: Under review, ETA 24-48 hours
- Applications CSV: Oracle AI Engineer + Lirio marked rejected (7 total rejections)
- Note: bulk sed error wiped applied statuses, restored 45 rows via python script
