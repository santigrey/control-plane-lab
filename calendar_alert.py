#!/usr/bin/env python3
import json
import time
import logging
import os
from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('calendar_alert')

ENV = dotenv_values('/home/jes/control-plane/.env')
TELEGRAM_TOKEN = ENV.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = ENV.get('TELEGRAM_CHAT_ID', '')
ALERT_AHEAD_MINUTES = 30
POLL_INTERVAL = 300
NOTIFIED_FILE = '/tmp/calendar_alert_notified.json'

def load_notified():
    try:
        with open(NOTIFIED_FILE) as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_notified(notified):
    try:
        with open(NOTIFIED_FILE, 'w') as f:
            json.dump(list(notified), f)
    except Exception:
        pass

def send_telegram(msg):
    import urllib.request
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = json.dumps({'chat_id': TELEGRAM_CHAT_ID, 'text': msg, 'parse_mode': 'HTML'}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 200
    except Exception as e:
        log.error(f'Telegram error: {e}')
        return False

def get_calendar_events():
    import sys
    sys.path.insert(0, '/home/jes/control-plane')
    try:
        from google_readers import get_todays_calendar
        return get_todays_calendar()
    except Exception as e:
        log.error(f'Calendar error: {e}')
        return []

def make_alert_key(event, window_label):
    return f"{event.get('summary','?')}_{event.get('start','')}_{window_label}"

def run():
    log.info('Calendar alert service started')
    notified = load_notified()
    while True:
        try:
            events = get_calendar_events()
            now = datetime.now(timezone.utc)
            for event in events:
                summary = event.get('summary', 'Meeting')
                start_str = event.get('start', '')
                if not start_str:
                    continue
                try:
                    if start_str.endswith('Z'):
                        start_str = start_str[:-1] + '+00:00'
                    start_dt = datetime.fromisoformat(start_str)
                    if start_dt.tzinfo is None:
                        import pytz
                        denver = pytz.timezone('America/Denver')
                        start_dt = denver.localize(start_dt)
                    start_dt = start_dt.astimezone(timezone.utc)
                except Exception as e:
                    log.warning(f'Could not parse start time {start_str}: {e}')
                    continue
                minutes_until = (start_dt - now).total_seconds() / 60
                if 0 < minutes_until <= ALERT_AHEAD_MINUTES:
                    key = make_alert_key(event, '30min')
                    if key not in notified:
                        mins = int(minutes_until)
                        msg = f'<b>Heads up, James</b>\n\n{summary} starts in {mins} minute{"s" if mins != 1 else ""}.'
                        if send_telegram(msg):
                            log.info(f'Alert sent: {summary} in {mins}min')
                            notified.add(key)
                            save_notified(notified)
                            notified_copy = set(k for k in notified if any(e.get('start','') in k for e in events))
                            notified = notified_copy | {key}
                            save_notified(notified)
                        else:
                            log.error(f'Failed to send alert for {summary}')
            old_date = (now - timedelta(hours=24)).strftime('%Y-%m-%d')
            notified = {k for k in notified if old_date not in k}
            save_notified(notified)
        except Exception as e:
            log.error(f'Poll error: {e}')
        time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    run()
