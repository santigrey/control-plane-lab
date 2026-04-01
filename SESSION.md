# SESSION.md — Project Ascension

## Last Updated
2026-04-01 (Day 49)

## Completed This Session (Day 49)
- Google Calendar write access: re-authorized OAuth with full calendar scope (was readonly)
- Added create_calendar_event function to google_readers.py
- Registered create_calendar_event tool in registry.py with handler
- Updated system prompt with create_calendar_event tool description
- Fixed parse_tool_call to extract JSON when Claude appends conversational text after tool JSON
- Injected today's date into system prompt so Alexandra resolves relative dates correctly
- Tested end-to-end: Alexandra created Per Scholas recurring class schedule via voice command
- CiscoKid confirmed as primary git node (set up Day 48)

## Completed Day 48
- Wake word VAD pipeline fixed end-to-end (speaking lock, threshold 0.045, language="en", fragment cleanup)
- Replaced run_agent() in voice_wake_detect with full tool loop (parse_tool_call + TOOLS.run)
- Added 'hey alexander' variant to WAKE_VARIANTS
- CiscoKid set as primary git node with credential store

## Current Platform Status
- Orchestrator: UP (CiscoKid:8000)
- Ollama: UP (TheBeast:192.168.1.152:11434)
- pgvector: UP
- MCP server: UP (CiscoKid:8001)
- Alexandra /chat: RESPONDING (tool loop with parse_tool_call + TOOLS.run)
- Alexandra wake word: WORKING (full tool loop)
- Alexandra calendar: READ + WRITE (create_calendar_event tool live)
- Dashboard: LIVE (HTTPS via nginx reverse proxy)
- Telegram bot: LIVE (voice in/out, ElevenLabs TTS)
- Recruiter watcher: LIVE (Gmail polling every 15 min)
- Git: CiscoKid primary, JesAir secondary

## Known Issues
- Wake word response latency (audio > ffmpeg > Whisper > Anthropic > tool loop > TTS)
- Second consecutive identical /chat query can return stale/hallucinated response
- Anthropic rate limits impacting Max plan during peak hours (known platform issue)

## Next Steps (Day 50)
1. Optimize wake word latency pipeline
2. Phase 2 - Agent network: shared task queue + message bus on CiscoKid/pgvector
3. MQTT broker on SlimJim (open to LAN)

## Resume Anchor
"Paco - read SESSION.md. Day 50. Calendar write tool is live. Next: wake word latency optimization, then agent network Phase 2."
