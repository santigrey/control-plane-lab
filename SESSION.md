# SESSION.md — Project Ascension

## Last Updated
2026-04-01 (Day 50)

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

## Next Steps (Day 51+)
1. Demo video of Alexandra for LinkedIn/portfolio
2. Automate CC task runner
3. Dashboard file/folder upload UI
4. Continue Alexandra features toward Jarvis-level
5. Per Scholas coursework assistance (AI-assisted coding strategy)
6. Weekly application cadence (3-5 targeted apps)

## Resume Anchor
"Paco - read SESSION.md. Day 51. MCP on Mac mini. Telegram photo pipeline live. Drive API enabled. Course materials downloaded. Lirio applied. LinkedIn updated. Next: demo video, coursework support, keep building Alexandra."
