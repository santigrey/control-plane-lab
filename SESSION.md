# SESSION.md — Project Ascension

## Last Updated
2026-04-01 (Day 49, late session)

## Completed Day 49
- Google Calendar write access: re-authorized OAuth with full calendar scope, added create_calendar_event to google_readers.py, registered tool in registry.py, Per Scholas recurring class schedule created end-to-end
- Fixed parse_tool_call to extract JSON when Claude appends conversational text after tool JSON
- Injected today's date into system prompt so Alexandra resolves relative dates correctly
- Wake word switched to Haiku for latency (~7s response vs Sonnet)
- Agent task pipeline operational end-to-end (Paco proposes > dashboard approve > CC executes > DB updated)
- CC autonomously cleared 6 approved tasks (job research x5 + full homelab health audit)
- Dashboard upgraded: task lifecycle panel (pending/in-progress/completed/rejected sections with count badges), queue badge in top bar, approve/reject buttons
- Dashboard JS hotfix: onclick quote escaping (\' -> &#39; HTML entities)
- Ollama restarted on TheBeast (systemd active but port not listening)
- 3 clean git pushes from CiscoKid
- Removed debug line (chat_debug.log) from app.py
- Added anti-hallucination guardrail for state-changing tool calls in system prompt

## Completed Day 48
- Wake word VAD pipeline fixed end-to-end (speaking lock, threshold 0.045, language="en", fragment cleanup)
- Replaced run_agent() in voice_wake_detect with full tool loop (parse_tool_call + TOOLS.run)
- Added 'hey alexander' variant to WAKE_VARIANTS
- CiscoKid set as primary git node with credential store

## Hot Lead
Lirio Sr AI Development Platform Engineer — REMOTE USA, $165-185k. Requires MCP + Claude Code + agent orchestration + HIPAA. Direct match with Project Ascension work. Apply ASAP.

## Current Platform Status
- Orchestrator: UP (CiscoKid:8000)
- Ollama: UP (TheBeast:192.168.1.152:11434)
- pgvector: UP
- MCP server: UP (CiscoKid:8001)
- Alexandra /chat: RESPONDING (tool loop with parse_tool_call + TOOLS.run)
- Alexandra wake word: WORKING (Haiku, full tool loop)
- Alexandra calendar: READ + WRITE (create_calendar_event tool live)
- Dashboard: LIVE (HTTPS, task lifecycle panel, queue badge)
- Telegram bot: LIVE (voice in/out, ElevenLabs TTS)
- Recruiter watcher: LIVE (Gmail polling every 15 min)
- Agent task pipeline: OPERATIONAL (Paco > approve > CC > DB)
- Git: CiscoKid primary, JesAir secondary

## Known Issues
- Wake word response latency (~7s with Haiku, was ~12s with Sonnet)
- Second consecutive identical /chat query can return stale response
- Anthropic rate limits on Max plan during peak hours

## Next Steps (Day 50)
1. Apply to Lirio (priority)
2. Automate CC task runner (cron or webhook trigger)
3. MQTT broker on SlimJim (open to LAN)
4. Continue wake word latency optimization

## Resume Anchor
"Paco — read SESSION.md. Day 50. Agent task pipeline operational. Dashboard upgraded. Calendar write live. Priority: Lirio application."
