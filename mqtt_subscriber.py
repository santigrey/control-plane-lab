#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/jes/control-plane')

import json
import logging
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

logging.basicConfig(
    filename='/tmp/mqtt_subscriber.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
log = logging.getLogger('mqtt_subscriber')

BROKER = '192.168.1.40'
PORT = 1883

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log.info('Connected to MQTT broker')
        client.subscribe('agent/#')
    else:
        log.error(f'MQTT connect failed: rc={rc}')

def on_message(client, userdata, msg):
    topic = msg.topic
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        payload = {'raw': msg.payload.decode()}

    ts = datetime.now(timezone.utc).isoformat()
    truncated = str(payload)[:120]
    log.info(f'{ts} {topic} {truncated}')

    if topic == 'agent/nudge/request':
        try:
            from notifier import send_notification
            message = payload.get('message', '')
            if message:
                send_notification(message)
                log.info(f'Notification sent for nudge: {message[:80]}')
        except Exception as e:
            log.error(f'Nudge notification failed: {e}')

def main():
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
        client_id='ciscokid_subscriber',
    )
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(1, 30)
    client.connect(BROKER, PORT, keepalive=60)
    log.info('Starting MQTT subscriber on ciscokid')
    client.loop_forever()

if __name__ == '__main__':
    main()
