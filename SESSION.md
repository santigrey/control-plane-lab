# SESSION.md — Project Ascension

## Last Updated
2026-03-31 (Day 48)

## Completed This Session (Day 48)
- Wake word VAD pipeline fixed end-to-end:
  - Added speaking lock (wakeSpeaking flag) to prevent TTS feedback loops
  - Raised VAD threshold to 0.045
  - Set language="en" in Whisper to reduce hallucinations
  - Added query fragment cleanup (strips partial words from wake word split)
  - Replaced run_agent() in voice_wake_detect with full tool loop (parse_tool_call + TOOLS.run, max 5 iterations, fallback to run_agent)
  - Added 'hey alexander' and 'alexander' to WAKE_VARIANTS (Whisper misheard variant)
- Wake word confirmed working: "Hey Alexandra, what time is it" returns live tool data
- Identified Alexandra cannot create calendar events (read-only) — queued for Day 49

## Current Platform Status
- Orchestrator: UP (CiscoKid:8000)
- Ollama: UP (TheBeast:192.168.1.152:11434) — LAN bound
- pgvector: UP — 507+ memory rows
- MCP server: UP (CiscoKid:8001)
- Alexandra /ask: RESPONDING
- Alexandra /chat: RESPONDING (tool loop with parse_tool_call + TOOLS.run)
- Alexandra wake word: WORKING (voice_wake_detect with full tool loop)
- Dashboard: LIVE (HTTPS via nginx reverse proxy)
- Telegram bot: LIVE (voice in/out, ElevenLabs TTS)
- Recruiter watcher: LIVE (Gmail polling every 15 min)

## Known Issues
- Wake word response latency (audio capture → ffmpeg → Whisper → Anthropic → tool loop → TTS)
- Alexandra has read-only calendar access — needs create_calendar_event tool with Google Calendar API write scope
- Anthropic rate limits impacting Max plan during peak hours (known platform issue as of 2026-03-31)
- Second consecutive identical /chat query can return stale/hallucinated response

## Next Steps (Day 49)
1. Add Google Calendar write tool to Alexandra (create_calendar_event)
2. Optimize wake word latency pipeline
3. Phase 2 — Agent network: shared task queue + message bus on CiscoKid/pgvector
4. MQTT broker on SlimJim (open to LAN)

## Resume Anchor
"Paco — read SESSION.md. Day 49. Wake word is working. Next: Google Calendar write tool for Alexandra, then agent network Phase 2."
