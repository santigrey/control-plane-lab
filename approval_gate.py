"""Approval Gate Service — Tier 3 IoT Command Approval

Project Ascension IoT Security Protocol — Section 5.

Runs as a SEPARATE process from the orchestrator on CiscoKid.
This isolation is the key security property: if the orchestrator is
compromised via prompt injection, the attacker cannot bypass Tier 3
approval because this process owns the approval logic independently.

Architecture:
  - MQTT listener: subscribes to home/security/request/#
  - HTTP API on port 8002 (localhost only): receives /approve, /deny,
    /blackout, /cameras_on from telegram_bot.py
  - On approval: publishes to home/security/execute/{command}
  - All actions logged to PostgreSQL audit tables
  - Zero extra dependencies beyond paho-mqtt, psycopg2, requests (already installed)

Why HTTP instead of its own Telegram polling:
  Only one process can long-poll a Telegram bot token. telegram_bot.py
  already does this. The gate exposes a tiny HTTP API that telegram_bot.py
  calls when it receives gate-related commands.
"""
import os
import json
import logging
import threading
import time
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Optional
from urllib.parse import urlparse

import paho.mqtt.client as mqtt
import paho.mqtt.publish as mqtt_publish
import psycopg2
import requests as http_requests
from dotenv import dotenv_values

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('/tmp/approval_gate.log'),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger('approval_gate')

# --- Configuration ---
_env = dotenv_values('/home/jes/control-plane/.env')

TELEGRAM_BOT_TOKEN = _env.get('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = _env.get('TELEGRAM_CHAT_ID') or os.getenv('TELEGRAM_CHAT_ID', '')
AUTHORIZED_TELEGRAM_IDS = [int(TELEGRAM_CHAT_ID)] if TELEGRAM_CHAT_ID else []

MQTT_BROKER = '192.168.1.40'
MQTT_PORT = 1883
MQTT_USER = _env.get('MQTT_USER') or os.getenv('MQTT_USER', 'alexandra')
MQTT_PASS = _env.get('MQTT_PASS') or os.getenv('MQTT_PASS', '')

GATE_HTTP_PORT = 8002

DB_HOST = '127.0.0.1'
DB_PORT = 5432
DB_NAME = 'controlplane'
DB_USER = 'alexandra_user'
DB_PASS = _env.get('AUDIT_DB_PASS') or 'ax_audit_r3ad0nly!'

# --- State ---
pending_approvals: Dict[str, dict] = {}
_lock = threading.Lock()

_camera_blackout = False
_camera_lock = threading.Lock()


# --- Database ---

def _db_connect():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )


def _log_audit(command, parameters, tier, approval_method, source='approval_gate',
               telegram_user_id=None, executed=False, notes=''):
    try:
        conn = _db_connect()
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
    except Exception as e:
        log.error(f'Audit log write failed: {e}')


def _log_security_event(event_type, detail, source='approval_gate'):
    try:
        conn = _db_connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO iot_security_events (event_type, detail, source) VALUES (%s, %s, %s)",
            (event_type, json.dumps(detail, default=str), source)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        log.error(f'Security event log failed: {e}')


# --- Telegram Helper ---

def _send_telegram(message: str) -> Optional[int]:
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
        resp = http_requests.post(url, json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown',
        }, timeout=10)
        if resp.status_code == 200:
            return resp.json().get('result', {}).get('message_id')
    except Exception as e:
        log.error(f'Telegram send error: {e}')
    return None


# --- MQTT Callbacks ---

def _on_connect(client, userdata, flags, reason_code, properties):
    if not reason_code.is_failure:
        log.info('Connected to MQTT broker')
        client.subscribe('home/security/request/#', qos=1)
        log.info('Subscribed to home/security/request/#')
    else:
        log.error(f'MQTT connect failed: {reason_code}')


def _on_message(client, userdata, msg):
    """Handle incoming Tier 3 approval requests from the orchestrator."""
    topic = msg.topic
    log.info(f'Received request on {topic}')

    try:
        payload = json.loads(msg.payload.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        log.error(f'Bad MQTT payload on {topic}: {e}')
        return

    parts = topic.split('/')
    command = parts[-1] if len(parts) > 3 else 'unknown'

    entity_id = payload.get('entity_id', 'unknown')
    action = payload.get('action', command)
    extras = payload.get('extras', {})
    request_id = payload.get('request_id', f'req_{int(time.time())}')
    friendly = extras.get('friendly_name', entity_id)

    # Camera blackout check
    domain = entity_id.split('.')[0] if '.' in entity_id else 'unknown'
    with _camera_lock:
        if domain == 'camera' and _camera_blackout:
            _log_audit(
                f'{action}:{entity_id}', payload, 3, 'blocked_blackout',
                executed=False, notes='Camera blackout active — gate rejected'
            )
            log.warning(f'Blocked camera command during blackout: {action}:{entity_id}')
            return

    # Send Telegram approval prompt
    msg_text = (
        '*TIER 3 APPROVAL REQUIRED*\n\n'
        f'Command: `{action}`\n'
        f'Device: `{friendly}`\n'
        f'Entity: `{entity_id}`\n'
        f'Request ID: `{request_id}`\n\n'
        f'Reply `/approve {request_id}` to execute\n'
        f'Reply `/deny {request_id}` to reject'
    )
    _send_telegram(msg_text)

    with _lock:
        pending_approvals[request_id] = {
            'command': command,
            'action': action,
            'entity_id': entity_id,
            'params': payload,
            'extras': extras,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

    _log_audit(
        f'{action}:{entity_id}', payload, 3, 'pending_approval',
        executed=False, notes=f'Telegram prompt sent, request_id={request_id}'
    )
    log.info(f'Tier 3 pending: {request_id} — {action} on {entity_id}')


# --- HTTP API Handler ---

class GateHandler(BaseHTTPRequestHandler):
    """Tiny HTTP API for the approval gate. Localhost only."""

    def _read_json(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    def _respond(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _verify_caller(self, data):
        user_id = data.get('user_id')
        if not user_id:
            return None, 'Missing user_id'
        user_id = int(user_id)
        if user_id not in AUTHORIZED_TELEGRAM_IDS:
            _log_security_event('UNAUTHORIZED_GATE_COMMAND', {
                'user_id': user_id, 'path': self.path,
            })
            return None, 'Unauthorized'
        return user_id, None

    def do_GET(self):
        path = urlparse(self.path).path

        if path == '/healthz':
            with _lock:
                pc = len(pending_approvals)
            with _camera_lock:
                bo = _camera_blackout
            self._respond(200, {
                'status': 'ok', 'service': 'approval_gate',
                'pending_approvals': pc, 'camera_blackout': bo,
            })

        elif path == '/pending':
            with _lock:
                result = {
                    rid: {'action': r['action'], 'entity_id': r['entity_id'],
                          'timestamp': r['timestamp']}
                    for rid, r in pending_approvals.items()
                }
            self._respond(200, {'pending': result, 'count': len(result)})

        else:
            self._respond(404, {'error': 'not found'})

    def do_POST(self):
        path = urlparse(self.path).path
        data = self._read_json()

        if path == '/approve':
            self._handle_approve(data)
        elif path == '/deny':
            self._handle_deny(data)
        elif path == '/blackout':
            self._handle_blackout(data)
        elif path == '/cameras_on':
            self._handle_cameras_on(data)
        else:
            self._respond(404, {'error': 'not found'})

    def _handle_approve(self, data):
        user_id, err = self._verify_caller(data)
        if err:
            code = 400 if err == 'Missing user_id' else 403
            self._respond(code, {'error': err})
            return

        request_id = data.get('request_id')
        if not request_id:
            self._respond(400, {'error': 'Missing request_id'})
            return

        with _lock:
            req = pending_approvals.pop(request_id, None)
        if req is None:
            self._respond(404, {'error': f'No pending request: {request_id}'})
            return

        entity_id = req['entity_id']
        action = req['action']
        params = req['params']
        execute_topic = f'home/security/execute/{req["command"]}'

        try:
            mqtt_publish.single(
                execute_topic, payload=json.dumps(params),
                hostname=MQTT_BROKER, port=MQTT_PORT,
                auth={'username': MQTT_USER, 'password': MQTT_PASS}, qos=1,
            )
            log.info(f'APPROVED: Published to {execute_topic}')
            _log_audit(
                f'{action}:{entity_id}', params, 3, 'approved',
                telegram_user_id=user_id, executed=True,
                notes=f'Approved by Telegram user {user_id}'
            )
            self._respond(200, {
                'status': 'approved', 'request_id': request_id,
                'action': action, 'entity_id': entity_id,
            })
        except Exception as e:
            log.error(f'Failed to publish approved command: {e}')
            _log_audit(
                f'{action}:{entity_id}', params, 3, 'approved_but_failed',
                telegram_user_id=user_id, executed=False,
                notes=f'MQTT publish failed: {e}'
            )
            self._respond(500, {'error': f'Publish failed: {e}'})

    def _handle_deny(self, data):
        user_id, err = self._verify_caller(data)
        if err:
            code = 400 if err == 'Missing user_id' else 403
            self._respond(code, {'error': err})
            return

        request_id = data.get('request_id')
        if not request_id:
            self._respond(400, {'error': 'Missing request_id'})
            return

        with _lock:
            req = pending_approvals.pop(request_id, None)
        if req is None:
            self._respond(404, {'error': f'No pending request: {request_id}'})
            return

        entity_id = req['entity_id']
        action = req['action']
        params = req['params']

        _log_audit(
            f'{action}:{entity_id}', params, 3, 'denied',
            telegram_user_id=user_id, executed=False,
            notes=f'Denied by Telegram user {user_id}'
        )
        log.info(f'DENIED: {request_id} — {action} on {entity_id}')
        self._respond(200, {
            'status': 'denied', 'request_id': request_id,
            'action': action, 'entity_id': entity_id,
        })

    def _handle_blackout(self, data):
        global _camera_blackout
        user_id, err = self._verify_caller(data)
        if err:
            code = 400 if err == 'Missing user_id' else 403
            self._respond(code, {'error': err})
            return

        with _camera_lock:
            _camera_blackout = True

        _log_security_event('CAMERA_BLACKOUT_ACTIVATED', {
            'activated_by': user_id,
            'activated_at': datetime.now(timezone.utc).isoformat(),
            'source': 'telegram_command',
        })
        _send_telegram(
            '*CAMERA BLACKOUT ACTIVATED*\n'
            'All camera access disabled for Alexandra.\n'
            'Send `/cameras_on` to restore.'
        )
        log.warning(f'Camera blackout activated by user {user_id}')
        self._respond(200, {'status': 'blackout_active', 'camera_blackout': True})

    def _handle_cameras_on(self, data):
        global _camera_blackout
        user_id, err = self._verify_caller(data)
        if err:
            code = 400 if err == 'Missing user_id' else 403
            self._respond(code, {'error': err})
            return

        with _camera_lock:
            _camera_blackout = False

        _log_security_event('CAMERA_ACCESS_RESTORED', {
            'restored_by': user_id,
            'restored_at': datetime.now(timezone.utc).isoformat(),
            'source': 'telegram_command',
        })
        _send_telegram('Camera access restored for Alexandra.')
        log.info(f'Camera access restored by user {user_id}')
        self._respond(200, {'status': 'cameras_on', 'camera_blackout': False})

    def log_message(self, format, *args):
        """Override to use our logger instead of stderr."""
        log.debug(f'HTTP: {args[0]}')


# --- Main ---

def main():
    log.info('=== Approval Gate Service Starting ===')
    log.info(f'MQTT broker: {MQTT_BROKER}:{MQTT_PORT}')
    log.info(f'HTTP API: 127.0.0.1:{GATE_HTTP_PORT}')
    log.info(f'Authorized Telegram IDs: {AUTHORIZED_TELEGRAM_IDS}')

    # MQTT client
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id='approval_gate', protocol=mqtt.MQTTv311)
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = _on_connect
    client.on_message = _on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    except Exception as e:
        log.error(f'Failed to connect to MQTT broker: {e}')
        raise

    client.loop_start()
    log.info('MQTT loop started')

    # HTTP server (blocks main thread)
    server = HTTPServer(('127.0.0.1', GATE_HTTP_PORT), GateHandler)
    log.info(f'HTTP API listening on 127.0.0.1:{GATE_HTTP_PORT}')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info('Shutting down...')
    finally:
        server.server_close()
        client.loop_stop()
        client.disconnect()
        log.info('Approval Gate Service stopped')


if __name__ == '__main__':
    main()
