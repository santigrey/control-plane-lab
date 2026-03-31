import json
import logging
from datetime import datetime, timezone

log = logging.getLogger('mqtt_publisher')

BROKER = '192.168.1.40'
PORT = 1883

def publish(topic: str, payload: dict):
    try:
        import paho.mqtt.publish as publish_mqtt
        publish_mqtt.single(
            topic,
            payload=json.dumps(payload, default=str),
            hostname=BROKER,
            port=PORT,
            client_id='ciscokid_orchestrator',
            keepalive=10
        )
        log.info(f'Published to {topic}: {str(payload)[:80]}')
        return True
    except Exception as e:
        log.warning(f'MQTT publish failed {topic}: {e}')
        return False

def task_created(title: str, assigned_to: str = 'paco'):
    return publish('agent/tasks/new', {
        'title': title,
        'assigned_to': assigned_to,
        'ts': datetime.now(timezone.utc).isoformat()
    })

def job_update(company: str, status: str, role: str = ''):
    return publish('agent/events/job_update', {
        'company': company,
        'status': status,
        'role': role,
        'ts': datetime.now(timezone.utc).isoformat()
    })

def system_event(event: str, detail: str = ''):
    return publish('agent/events/system', {
        'event': event,
        'detail': detail,
        'ts': datetime.now(timezone.utc).isoformat()
    })

def nudge(message: str):
    return publish('agent/nudge/request', {
        'message': message,
        'ts': datetime.now(timezone.utc).isoformat()
    })
