# SESSION.md — April 5, 2026 ~12:45 PM MST

## RESUME POINT
IoT Security Protocol (Option C) FULLY DEPLOYED, AUDITED, DOCUMENTED. All 8 verification checks passing. Security protocol doc created (IoT_Security_Protocol.docx). Next: Schlage lock HA integration.

## Completed This Session (April 5)

### IoT Security Protocol — DEPLOYED + AUDITED

#### Tier Enforcement (iot_security.py)
- 3-tier classification: T1 auto, T2 notify+15s, T3 approval required
- Unknown commands default Tier 3 (fail-safe)
- Camera blackout kill switch, append-only PostgreSQL audit
- UPDATED: siren.turn_on moved to Tier 3 (weaponization risk)
- UPDATED: alarm_control_panel.disarm moved to Tier 3 (security-critical)
- ADDED: alarm domain aliases for alarm_control_panel

#### Approval Gate (approval_gate.py) — RUNNING
- Separate process (prompt injection defense)
- MQTT on home/security/request/#, HTTP API 127.0.0.1:8002
- FIXED: paho-mqtt v2 callback API (no more deprecation warning)
- systemd: approval-gate.service (enabled, running)

#### Telegram Bot (telegram_bot.py) — PATCHED
- Smart routing: req_* -> gate, others -> orchestrator
- Commands: /approve /deny /blackout /cameras_on /gate
- systemd: alexandra-telegram.service (restarted, running)

#### Infrastructure
- PostgreSQL: iot_audit_log + iot_security_events (append-only verified)
- UFW: per-device IoT blocks (11 devices), default deny incoming
- Cron: hourly snapshot retention (manual 60m, motion 24h)
- ADDED: mosquitto-clients installed for CLI MQTT debugging

#### Audit Results (8/8 PASS)
1. Services: orchestrator, alexandra-telegram, approval-gate — all active
2. Approval Gate API: /healthz OK, 0 pending, blackout off
3. MQTT Broker: connected rc=0
4. Tier Classification: all domains verified correct
5. PostgreSQL: append-only enforced (DELETE blocked)
6. File Integrity: all 4 core files present, backups in place
7. Cron Jobs: snapshot retention installed
8. Telegram Bot: imports clean, GATE_API_BASE set

#### Documentation
- IoT_Security_Protocol.docx created (6 pages)
- Covers: exec summary, threat model, tiers, architecture, devices, commands, network, audit, retention, emergency procedures

## Pending (next session)
1. Schlage lock HA integration (on network at 192.168.1.174, UFW blocked, not in HA)
2. HA Overview UI cleanup — organize by room
3. WiZ bulb room assignments + rename
4. Bedroom + den Apple TVs -> HA
5. Git commit all security changes

## System State: ALL HEALTHY
Services: orchestrator + alexandra-telegram + approval-gate
Security: iot_security + approval_gate + audit_logging
Alexandra: home_status + home_control + home_cameras
