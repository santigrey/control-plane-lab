# SESSION.md — April 6, 2026 ~1:30 AM MST

## RESUME POINT
WireGuard VPN fully deployed. Scheduled briefings fixed (Cowork tasks + legacy cron disabled). Alexandra vs JARVIS status report generated. GX10 arriving April 9. Sloan heading to NM for property work. Next: Pi VPN client setup, NM camera integration, GX10 stack integration on return.

## Completed This Session (April 5-6)

### Scheduled Briefing Fix — DEPLOYED + VERIFIED (Late Night, P2)
- Diagnosed why evening briefing never arrived via Telegram
- Root cause: Cowork scheduled tasks were using homelab_send_message (agent-to-agent IPC) instead of Telegram Bot API
- Fix: Updated both morning-briefing and evening-debrief task prompts to use homelab_ssh_run with curl to Telegram Bot API
- Delivery command: source .env && curl Telegram sendMessage endpoint
- Live test: sent test message to Telegram, confirmed delivery
- Also discovered legacy cron jobs (daily_brief.py 7AM UTC, evening_nudge.py 6PM UTC) were competing
- Legacy cron sent raw prompt text as email via notifier.py — no substance
- Disabled both legacy cron entries with comments explaining Cowork replacement
- Kept sync_app_count.py and snapshot retention crons active

### Alexandra vs JARVIS Status Report — GENERATED (Late Night, P2)
- Comprehensive status report: system state, 27 tool handlers, gap analysis vs JARVIS
- 5-phase roadmap: Local Brain → Expanded Senses → Proactive Intelligence → Ambient Interface → Advanced Autonomy
- Capability at ~30%, architecture at ~70% of JARVIS equivalent
- GX10 identified as key inflection point unlocking next 3 phases
- Saved to workspace + iCloud AI/Notes folder

### WireGuard VPN — FULLY DEPLOYED (Late Night, P2)
- WireGuard server on CiscoKid: wg0 at 10.10.0.1/24, listening UDP 51820
- Enabled at boot via systemctl (wg-quick@wg0), UFW 51820/udp open
- IP forwarding + NAT masquerade active (VPN clients reach full LAN)
- Two peers: laptop (10.10.0.2) and Pi (10.10.0.3)
- Netgear CAX80 port forward: UDP 51820 -> 192.168.1.10
- DuckDNS: ascension-vpn.duckdns.org, auto-updates every 5min via cron
- Script: /etc/wireguard/duckdns-update.sh, logs: /var/log/duckdns.log
- Client configs use hostname not hardcoded IP
- Laptop client installed on Sloan's Mac
- Pi client ready at /etc/wireguard/pi-client.conf

### VPN Address Map
- 10.10.0.1 — CiscoKid (server)
- 10.10.0.2 — Sloan laptop
- 10.10.0.3 — NM Raspberry Pi (not yet deployed)

### Network Recon
- 192.168.1.15: unknown Android device (hostname android-167dfab7c868dd27, MAC 08:8F:C3 Samsung OUI). All top ports closed. Sloan investigating.

### MQTT Tier 3 Approval Flow — WIRED + TESTED (Earlier, P2)
- iot_security.py: Tier 3 publishes to home/security/request/{action} via MQTT
- approval_gate.py: receives MQTT, sends Telegram prompt
- mqtt_executor.py (NEW): subscribes to home/security/execute/#, calls HA API
- Fixed approval_gate.py msg.topicc typo + SlimJim MQTT ACL
- E2E tested: unlock -> MQTT -> gate -> pending -> deny path verified

### Telegram Bot Timeout Fix — DEPLOYED
- registry.py: 1.2s sleep now WiZ-only
- telegram_bot.py: /chat timeouts 60s -> 180s

### IoT Security Protocol — DEPLOYED + AUDITED (Morning, P1)
- 3-tier classification, 8/8 audit checks passing
- Docs: IoT_Security_Protocol.docx + docs/alexandra_iot_security_protocol.md

## Key Configs
### WireGuard
- Server: /etc/wireguard/wg0.conf (CiscoKid)
- Laptop client: /etc/wireguard/laptop-client.conf (CiscoKid backup)
- Pi client: /etc/wireguard/pi-client.conf (CiscoKid)
- DuckDNS script: /etc/wireguard/duckdns-update.sh
- DuckDNS cron: */5 * * * * (root crontab, CiscoKid)
- Router: UDP 51820 -> 192.168.1.10 (Netgear CAX80)

### Scheduled Tasks
- Morning briefing: Cowork scheduled task, 7:00 AM MT daily
- Evening debrief: Cowork scheduled task, 10:00 PM MT daily
- Both use homelab_ssh_run + curl to Telegram Bot API
- Legacy cron jobs (daily_brief.py, evening_nudge.py): DISABLED

## Incoming Hardware
- ASUS Ascent GX10 (NVIDIA GB10, 128GB unified LPDDR5x, 2TB NVMe)
- Arrives: April 9, 2026
- Plan: primary local inference tier via vLLM

## Pending (Next Session)
1. Pi VPN client setup — deploy pi-client.conf, test tunnel
2. NM camera integration — add to HA via Pi tunnel over Starlink
3. GX10 integration — DGX OS, vLLM endpoint, orchestrator routing
4. Schlage lock HA — 192.168.1.174, UFW blocked
5. HA Overview UI — organize by room
6. WiZ bulb room assignments + rename
7. Bedroom + den Apple TVs -> HA
8. Investigate 192.168.1.15 — unknown Android/Samsung device
9. Update iCloud resume prompt with WireGuard additions

## System State: ALL HEALTHY
Services: orchestrator + alexandra-telegram + approval-gate
Security: iot_security + approval_gate + audit_logging + mqtt_executor
MQTT: broker (slimjim) + executor + gate subscriber
VPN: wireguard (ciscokid) + duckdns + router port forward
Briefings: morning 7AM MT + evening 10PM MT via Cowork scheduled tasks
Alexandra: home_status + home_control + home_cameras (via enforce_tier)
