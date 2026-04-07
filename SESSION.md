# SESSION.md — April 7, 2026 ~12:00 AM MST

## RESUME POINT
Alexandra Phase 1 fixes deployed: device manifest, conversation context, camera schema, Ollama fallback killed. Camera snapshot returns stale Blink thumbnail (need force-refresh via camera.snapshot service). GX10 arrives April 9. Sloan in NM this week for property work.

## Completed This Session (April 6-7, P2)

### Alexandra Phase 1 — Core Fixes DEPLOYED
- Device manifest injection: build_device_manifest() queries HA at prompt-build time, injects entity_id/friendly_name/state table into system prompt. Alexandra now maps "blueroom lamps" -> switch.tall_switch + switch.short_switch on first call. No more guessing.
- Conversation context injection: build_conversation_context() pulls last 5 user messages with timestamps, injects time-since-last-chat and recent topics. Eliminates cold-start amnesia.
- Camera tool schema fix: home_cameras now requires entity_id, lists all 7 cameras in description. LLM passes correct args on first call.
- Camera handler rewrite: status action queries HA states API (works). Snapshot action fetches camera_proxy with cache-buster timestamp, saves to /tmp/cam_*.jpg.
- Camera system prompt fix: Updated tool description from "Get status of all cameras" to list all entity_ids and require entity_id arg.
- Killed silent Ollama fallback: /chat no longer falls through to 8B local model on API failure. Returns clear error message, logs traceback. No more split personality.
- Telegram bot photo delivery: bot checks response for image_path, sends as reply_photo with caption.
- Pydantic fix: ChatResponse.image_path is Optional[str].

### Known Bug — Camera Snapshot Stale Image
- Blink cameras don't stream continuously — they cache last motion thumbnail
- HA camera_proxy returns whatever Blink has cached (often hours old)
- Fix: call HA camera.snapshot service to force fresh capture before fetching proxy
- Tapo cameras (BlueRoom, Den) may work better since they have RTSP streams

### Previous Session Work (preserved)
- WireGuard VPN fully deployed (CiscoKid server, laptop + Pi peers, DuckDNS, port forward)
- Scheduled briefings fixed then disabled (Cowork tasks unreliable for this)
- Alexandra vs JARVIS status report generated
- MQTT Tier 3 approval flow wired and tested
- IoT security protocol deployed and audited

## Key Configs
### Alexandra System Prompt Injections (orchestrator/app.py)
- build_conversation_context() — last 5 user messages + time gap
- build_device_manifest() — live HA device table
- build_live_context() — weather/time/stocks (existing)
- profile_context — user profile from DB (existing)

### WireGuard
- Server: /etc/wireguard/wg0.conf (CiscoKid)
- DuckDNS: ascension-vpn.duckdns.org, 5min cron
- Router: UDP 51820 -> 192.168.1.10

## Incoming Hardware
- ASUS Ascent GX10 (NVIDIA GB10, 128GB LPDDR5x) — arrives April 9

## Pending (Next Session)
1. Camera snapshot force-refresh — call camera.snapshot service before proxy fetch
2. Test Tapo camera snapshots (BlueRoom/Den) — RTSP may give live frames
3. Alexandra Phase 2 — memory search improvements, proactive briefings via systemd timer
4. Pi VPN client setup — deploy pi-client.conf, test tunnel before NM trip
5. NM camera integration — add to HA via Pi tunnel over Starlink
6. GX10 integration — DGX OS, vLLM endpoint, orchestrator routing
7. Schlage lock HA — 192.168.1.174, UFW blocked
8. HA Overview UI — organize by room
9. WiZ bulb room assignments + rename
10. Bedroom + den Apple TVs -> HA
11. Investigate 192.168.1.15 — unknown Android/Samsung device

## System State: ALL HEALTHY
Services: orchestrator + alexandra-telegram + approval-gate
Security: iot_security + approval_gate + audit_logging + mqtt_executor
MQTT: broker (slimjim) + executor + gate subscriber
VPN: wireguard (ciscokid) + duckdns + router port forward
Alexandra: device manifest + conversation context + camera status (snapshot stale)
