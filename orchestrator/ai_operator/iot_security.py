"""IoT Security — Command Tier Enforcement & Audit Logging

Project Ascension IoT Security Protocol implementation.
Enforces 3-tier command system between Alexandra's tool calls and HA execution.
All IoT commands are audit-logged to PostgreSQL (append-only).

Tier 1: Autonomous — execute immediately (lights, thermostat, sensors)
Tier 2: Notify + delay — Telegram alert, 15s cancel window (arm/disarm, motion detect)
Tier 3: Approval required — Telegram prompt, wait for explicit approval (unlock, disable cameras, ACL changes)
"""
import os
import json
import time
import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import psycopg2
import requests
from dotenv import dotenv_values

log = logging.getLogger('iot_security')

# --- Configuration ---
_env = dotenv_values('/home/jes/control-plane/.env')

TELEGRAM_BOT_TOKEN = _env.get('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = _env.get('TELEGRAM_CHAT_ID') or os.getenv('TELEGRAM_CHAT_ID', '')
AUTHORIZED_TELEGRAM_IDS = [int(_env.get('TELEGRAM_CHAT_ID', '0'))]  # Sloan only

# Database config for audit log (uses alexandra_user — append-only)
AUDIT_DB_HOST = '127.0.0.1'
AUDIT_DB_PORT = 5432
AUDIT_DB_NAME = 'controlplane'
AUDIT_DB_USER = 'alexandra_user'
AUDIT_DB_PASS = 'ax_audit_r3ad0nly!'

# Camera access state (can be toggled by kill switch)
_camera_access_enabled = True
_camera_lock = threading.Lock()

# Tier 2 cancel state
_pending_cancel = {}
_cancel_lock = threading.Lock()


# --- Tier Classification ---
TIER_MAP = {
    # Tier 1 — Autonomous
    ('light', 'turn_on'): 1,
    ('light', 'turn_off'): 1,
    ('light', 'toggle'): 1,
    ('switch', 'turn_on'): 1,
    ('switch', 'turn_off'): 1,
    ('switch', 'toggle'): 1,
    ('climate', 'set_temperature'): 1,
    ('climate', 'set_hvac_mode'): 1,
    ('media_player', 'media_play'): 1,
    ('media_player', 'media_pause'): 1,
    ('media_player', 'media_next'): 1,
    ('media_player', 'volume_set'): 1,
    ('media_player', 'select_source'): 1,
    ('sensor', 'read'): 1,
    ('binary_sensor', 'read'): 1,
    ('siren', 'turn_off'): 1,

    # Tier 2 — Notify + 15s delay
    ('alarm_control_panel', 'arm_away'): 2,
    ('alarm_control_panel', 'disarm'): 3,  # security-critical
    ('alarm', 'arm_away'): 2,
    ('alarm', 'disarm'): 3,  # alias for alarm_control_panel
    ('camera', 'turn_on'): 2,
    ('camera', 'turn_off'): 2,
    ('camera', 'enable_motion'): 2,
    ('camera', 'disable_motion'): 2,
    ('camera', 'snapshot'): 2,
    ('siren', 'turn_on'): 3,  # can be weaponized
    ('lock', 'lock'): 2,

    # Tier 3 — Explicit approval
    ('lock', 'unlock'): 3,
}

# Actions that are always Tier 3 regardless of domain
TIER3_ACTIONS = {
    'disable_all_cameras',
    'export_feed',
    'modify_automation',
    'change_acl',
    'change_credentials',
}


def classify_tier(entity_id: str, action: str) -> int:
    """Classify an IoT command into Tier 1, 2, or 3."""
    if action in TIER3_ACTIONS:
        return 3

    domain = entity_id.split('.')[0] if '.' in entity_id else 'unknown'
    tier = TIER_MAP.get((domain, action))

    if tier is not None:
        return tier

    # Unknown command fallback — Tier 3 (protocol rule)
    log.warning(f'Unknown command tier: domain={domain} action={action} -> Tier 3')
    return 3


# --- Audit Logging ---

def _audit_db_connect():
    return psycopg2.connect(
        host=AUDIT_DB_HOST, port=AUDIT_DB_PORT,
        dbname=AUDIT_DB_NAME, user=AUDIT_DB_USER, password=AUDIT_DB_PASS
    )


def log_iot_command(
    command: str,
    parameters: dict,
    tier: int,
    approval_method: str,
    source: str = 'orchestrator',
    telegram_user_id: Optional[int] = None,
    executed: bool = False,
    notes: str = ''
):
    """Append-only log of every IoT command to PostgreSQL."""
    try:
        conn = _audit_db_connect()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO iot_audit_log
               (command, parameters, tier, approval_method, source,
                telegram_user_id, executed, notes)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (command, json.dumps(parameters, default=str), tier,
             approval_method, source, telegram_user_id, executed, notes)
        )
        conn.commit()
        cur.close()
        conn.close()
        log.info(f'Audit: tier={tier} method={approval_method} cmd={command} executed={executed}')
    except Exception as e:
        log.error(f'Audit log write failed: {e}')


def log_security_event(event_type: str, detail: dict, source: str = 'iot_security'):
    """Log a security event."""
    try:
        conn = _audit_db_connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO iot_security_events (event_type, detail, source) VALUES (%s, %s, %s)",
            (event_type, json.dumps(detail, default=str), source)
        )
        conn.commit()
        cur.close()
        conn.close()
        log.warning(f'Security event: {event_type}')
    except Exception as e:
        log.error(f'Security event log failed: {e}')


# --- Telegram Integration ---

def _send_telegram(message: str) -> bool:
    """Send a Telegram message to Sloan."""
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
        resp = requests.post(url, json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown',
        }, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        log.error(f'Telegram send failed: {e}')
        return False


def _check_telegram_cancel(command_id: str, timeout: float = 15.0) -> bool:
    """Check if a cancel was received during the delay window."""
    with _cancel_lock:
        _pending_cancel[command_id] = False

    time.sleep(timeout)

    with _cancel_lock:
        cancelled = _pending_cancel.pop(command_id, False)
    return cancelled


def receive_cancel(command_id: str):
    """Called by Telegram bot when CANCEL reply received."""
    with _cancel_lock:
        if command_id in _pending_cancel:
            _pending_cancel[command_id] = True
            log.info(f'Cancel received for command {command_id}')


# --- Camera Kill Switch ---

def camera_blackout():
    """Immediately disable all camera access for Alexandra."""
    global _camera_access_enabled
    with _camera_lock:
        _camera_access_enabled = False
    log_security_event('CAMERA_BLACKOUT_ACTIVATED', {
        'activated_at': datetime.now(timezone.utc).isoformat()
    })
    _send_telegram('CAMERA BLACKOUT ACTIVATED\nAll camera access disabled for Alexandra.')
    log.warning('Camera blackout activated')


def camera_restore():
    """Re-enable camera access for Alexandra."""
    global _camera_access_enabled
    with _camera_lock:
        _camera_access_enabled = True
    log_security_event('CAMERA_ACCESS_RESTORED', {
        'restored_at': datetime.now(timezone.utc).isoformat()
    })
    _send_telegram('Camera access restored for Alexandra.')
    log.info('Camera access restored')


def is_camera_access_enabled() -> bool:
    with _camera_lock:
        return _camera_access_enabled


# --- Tier Enforcement ---

def enforce_tier(entity_id: str, action: str, extras: dict = None,
                 source: str = 'orchestrator') -> Tuple[bool, str]:
    """Enforce command tier before execution.

    Returns (allow, reason):
      - Tier 1: (True, 'tier1_auto')
      - Tier 2: blocks 15s, then (True, 'tier2_executed') or (False, 'cancelled')
      - Tier 3: (False, 'approval_required') — must go through approval gate
    """
    params = {'entity_id': entity_id, 'action': action, 'extras': extras or {}}
    tier = classify_tier(entity_id, action)
    domain = entity_id.split('.')[0] if '.' in entity_id else 'unknown'

    # Camera blackout check
    if domain == 'camera' and not is_camera_access_enabled():
        log_iot_command(
            f'{action}:{entity_id}', params, tier, 'blocked_blackout',
            source=source, executed=False, notes='Camera blackout active'
        )
        return False, 'Camera access is currently disabled (blackout mode).'

    if tier == 1:
        log_iot_command(
            f'{action}:{entity_id}', params, tier, 'auto',
            source=source, executed=True
        )
        return True, 'tier1_auto'

    elif tier == 2:
        cmd_id = f't2_{entity_id}_{action}_{int(time.time())}'
        friendly = entity_id
        if extras and isinstance(extras, dict):
            friendly = extras.get('friendly_name', entity_id)
        _send_telegram(
            f'Tier 2 Command\n'
            f'Alexandra executing: {action} on {friendly}\n'
            f'Reply CANCEL within 15 seconds to stop.'
        )

        cancelled = _check_telegram_cancel(cmd_id, timeout=15.0)

        if cancelled:
            log_iot_command(
                f'{action}:{entity_id}', params, tier, 'cancelled',
                source=source, executed=False, notes='Cancelled during delay'
            )
            return False, 'Command cancelled by user during 15-second window.'

        log_iot_command(
            f'{action}:{entity_id}', params, tier, 'notify',
            source=source, executed=True
        )
        return True, 'tier2_notify_executed'

    elif tier == 3:
        log_iot_command(
            f'{action}:{entity_id}', params, tier, 'pending_approval',
            source=source, executed=False,
            notes='Awaiting explicit Telegram approval via approval gate'
        )
        _send_telegram(
            f'TIER 3 APPROVAL REQUIRED\n'
            f'Command: {action} on {entity_id}\n'
            f'Reply /approve or /deny'
        )
        return False, 'approval_required'

    return False, 'unknown_tier'


def verify_telegram_sender(user_id: int) -> bool:
    """Verify a Telegram user is authorized for IoT approvals."""
    if user_id not in AUTHORIZED_TELEGRAM_IDS:
        log_security_event('UNAUTHORIZED_IOT_APPROVAL_ATTEMPT', {
            'user_id': user_id,
            'authorized_ids': AUTHORIZED_TELEGRAM_IDS,
        })
        return False
    return True
