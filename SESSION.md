# SESSION.md — April 5, 2026 ~4:30 PM MST

## RESUME POINT
IoT Security Protocol FULLY DEPLOYED + AUDITED + DOCUMENTED. Security protocol doc saved to docs/alexandra_iot_security_protocol.md (gitignored). Cowork safeguard files verified (live in Cowork session memory only). Next: Telegram bot timeout fix (WiZ-only delay + 180s timeout), then MQTT Tier 3 approval wiring.

## Completed This Session (April 5)

### IoT Security Protocol — DEPLOYED + AUDITED (Morning, P1)

#### Tier Enforcement (iot_security.py)
- 3-tier classification: T1 auto, T2 notify+15s, T3 approval required
- Unknown commands default Tier 3 (fail-safe)
- Camera blackout kill switch, append-only PostgreSQL audit
- siren.turn_on → Tier 3 (weaponization risk)
- alarm_control_panel.disarm → Tier 3 (security-critical)
- alarm domain aliases for alarm_control_panel

#### Approval Gate (approval_gate.py) — RUNNING
- Separate process (prompt injection defense)
- MQTT on home/security/request/#, HTTP API 127.0.0.1:8002
- paho-mqtt v2 callback API (no deprecation warning)
- systemd: approval-gate.service (enabled, running)

#### Telegram Bot (telegram_bot.py) — PATCHED
- Smart routing: req_* -> gate, others -> orchestrator
- Commands: /approve /deny /blackout /cameras_on /gate
- systemd: alexandra-telegram.service (restarted, running)

#### Infrastructure
- PostgreSQL: iot_audit_log + iot_security_events (append-only verified)
- UFW: per-device IoT blocks (11 devices), default deny incoming
- Cron: hourly snapshot retention (manual 60m, motion 24h)
- mosquitto-clients installed for CLI MQTT debugging

#### Audit Results (8/8 PASS)
1. Services: orchestrator, alexandra-telegram, approval-gate — all active
2. Approval Gate API: /healthz OK, 0 pending, blackout off
3. MQTT Broker: connected rc=0
4. Tier Classification: all domains verified correct
5. PostgreSQL: append-only enforced (DELETE blocked)
6. File Integrity: all 4 core files present, backups in place
7. Cron Jobs: snapshot retention installed
8. Telegram Bot: imports clean, GATE_API_BASE set

### Reconciliation Follow-Up (Afternoon, P2)

#### 1. IoT Security Protocol Doc — SAVED + GITIGNORED
- Source: P1-authored 448-line comprehensive security protocol
- Saved to: /home/jes/control-plane/docs/alexandra_iot_security_protocol.md
- Transfer: base64 chunked (15 chunks x 1800 bytes) via homelab MCP
- Verified: 448 lines, correct header and footer
- Added docs/alexandra_iot_security_protocol.md to .gitignore
- Classification: INTERNAL — source of truth for all IoT security decisions

#### 2. Cowork Safeguard Files — VERIFIED
- Files P1 referenced live in Cowork session memory only
- They do NOT persist on CiscoKid filesystem (expected)
- IoT security protocol doc is the authoritative on-disk reference

#### 3. SESSION.md Update — THIS FILE
- Full state capture from both P1 and P2 work today

### Documentation
- IoT_Security_Protocol.docx (6 pages, morning session)
- docs/alexandra_iot_security_protocol.md (448 lines, INTERNAL, gitignored)

## Approved But Not Yet Implemented

### Telegram Bot Timeout Fix (APPROVED by Sloan)
In registry.py, make 1.2s delay WiZ-only:
```python
_ha_request("POST", f"/api/services/{svc}", body)
if dom == 'light' and 'wiz' in eid.lower():
    time.sleep(1.2)
new_state = _ha_request('GET', f'/api/states/{eid}')
```
In telegram_bot.py, increase request timeout to 180s.
Reason: 1.2s delay runs for ALL devices (8x sequential = ~10s). Only WiZ needs it.

## Pending (Next Session)
1. **Telegram bot timeout fix** — implement approved WiZ-only delay + 180s timeout
2. **Anthropic API auto-reload** — currently disabled, $23.90 balance; needs Sloan go-ahead
3. **MQTT Tier 3 approval flow** — wire enforce_tier() T3 through MQTT to approval_gate.py; remove camera hard block when live
4. **Scheduled task briefs** — morning/evening stopped (API credit outage); confirm self-healing
5. **Schlage lock HA integration** — on network at 192.168.1.174, UFW blocked, not in HA
6. **HA Overview UI cleanup** — organize by room
7. **WiZ bulb room assignments** + rename
8. **Bedroom + den Apple TVs** -> HA
9. **Git commit security changes** — .gitignore update + any pending changes

## System State: ALL HEALTHY
Services: orchestrator + alexandra-telegram + approval-gate
Security: iot_security + approval_gate + audit_logging
Alexandra: home_status + home_control + home_cameras
Docs: alexandra_iot_security_protocol.md (on disk, gitignored)
