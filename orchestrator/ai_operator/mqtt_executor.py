"""MQTT Executor — Executes approved Tier 3 IoT commands.

Subscribes to home/security/execute/# and calls Home Assistant API
when the approval gate publishes an approved command.

Runs as a background thread inside the orchestrator process.
"""
import os
import json
import logging
import threading
import time

import paho.mqtt.client as mqtt
import requests
from dotenv import dotenv_values

log = logging.getLogger('mqtt_executor')

_env = dotenv_values('/home/jes/control-plane/.env')

MQTT_BROKER = '192.168.1.40'
MQTT_PORT = 1883
MQTT_USER = _env.get('MQTT_USER') or os.getenv('MQTT_USER', 'alexandra')
MQTT_PASS = _env.get('MQTT_PASS') or os.getenv('MQTT_PASS', '')

HA_URL = _env.get('HA_URL', 'http://localhost:8123')
HA_TOKEN = _env.get('HA_TOKEN') or os.getenv('HA_TOKEN', '')

TELEGRAM_BOT_TOKEN = _env.get('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = _env.get('TELEGRAM_CHAT_ID') or os.getenv('TELEGRAM_CHAT_ID', '')

# --- Service map (mirrors registry.py) ---
SERVICE_MAP = {
    'turn_on': '{dom}/turn_on', 'turn_off': '{dom}/turn_off', 'toggle': '{dom}/toggle',
    'set_temperature': 'climate/set_temperature', 'set_hvac_mode': 'climate/set_hvac_mode',
    'media_play': 'media_player/media_play', 'media_pause': 'media_player/media_pause',
    'media_next': 'media_player/media_next_track', 'volume_set': 'media_player/volume_set',
    'arm_away': 'alarm_control_panel/alarm_arm_away', 'disarm': 'alarm_control_panel/alarm_disarm',
    'select_source': 'media_player/select_source',
    'unlock': 'lock/unlock', 'lock': 'lock/lock',
}


def _ha_request(method, path, json_body=None):
    headers = {'Authorization': f'Bearer {HA_TOKEN}', 'Content-Type': 'application/json'}
    if method == 'GET':
        resp = requests.get(f'{HA_URL}{path}', headers=headers, timeout=10)
    else:
        resp = requests.post(f'{HA_URL}{path}', headers=headers, json=json_body or {}, timeout=10)
    resp.raise_for_status()
    return resp.json() if resp.text else {'ok': True}


def _send_telegram(message):
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
        requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}, timeout=10)
    except Exception as e:
        log.error(f'Telegram send failed: {e}')


def _execute_command(payload):
    """Execute an approved Tier 3 command against Home Assistant."""
    entity_id = payload.get('entity_id', '')
    action = payload.get('action', '')
    extras = payload.get('extras', {})
    request_id = payload.get('request_id', 'unknown')
    dom = entity_id.split('.')[0] if '.' in entity_id else 'unknown'

    svc_template = SERVICE_MAP.get(action)
    if not svc_template:
        log.error(f'Unknown action in execute: {action}')
        _send_telegram(f'Execute FAILED: unknown action `{action}` for `{entity_id}`')
        return

    svc = svc_template.format(dom=dom)
    body = {'entity_id': entity_id}
    if isinstance(extras, dict):
        body.update(extras)

    try:
        _ha_request('POST', f'/api/services/{svc}', body)
        # WiZ delay
        if dom == 'light' and 'wiz' in entity_id.lower():
            time.sleep(1.2)
        new_state = _ha_request('GET', f'/api/states/{entity_id}')
        state = new_state.get('state', 'unknown')
        friendly = new_state.get('attributes', {}).get('friendly_name', entity_id)
        log.info(f'EXECUTED {request_id}: {action} on {entity_id} -> {state}')
        _send_telegram(f'EXECUTED: `{action}` on `{friendly}`\nState: `{state}`\nRequest: `{request_id}`')
    except Exception as e:
        log.error(f'Execute failed for {request_id}: {e}')
        _send_telegram(f'Execute FAILED for `{request_id}`: {e}')


# --- MQTT Callbacks ---

def _on_connect(client, userdata, flags, reason_code, properties):
    if not reason_code.is_failure:
        log.info('MQTT executor connected to broker')
        client.subscribe('home/security/execute/#', qos=1)
        log.info('Subscribed to home/security/execute/#')
    else:
        log.error(f'MQTT executor connect failed: {reason_code}')


def _on_message(client, userdata, msg):
    topic = msg.topic
    log.info(f'Execute message on {topic}')
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        log.error(f'Bad MQTT payload on {topic}: {e}')
        return
    # Execute in a thread to not block the MQTT loop
    threading.Thread(target=_execute_command, args=(payload,), daemon=True).start()


def _on_disconnect(client, userdata, flags, reason_code, properties):
    log.warning(f'MQTT executor disconnected: {reason_code}')


_client = None
_started = False


def start():
    """Start the MQTT executor in a background thread. Safe to call multiple times."""
    global _client, _started
    if _started:
        return
    _started = True

    _client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id='mqtt_executor',
        protocol=mqtt.MQTTv311,
    )
    _client.username_pw_set(MQTT_USER, MQTT_PASS)
    _client.on_connect = _on_connect
    _client.on_message = _on_message
    _client.on_disconnect = _on_disconnect

    try:
        _client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        _client.loop_start()
        log.info('MQTT executor background thread started')
    except Exception as e:
        log.error(f'MQTT executor failed to connect: {e}')
        _started = False
