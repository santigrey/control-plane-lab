#!/usr/bin/env python3
"""Event-driven priority interrupt system for Alexandra."""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone, timedelta

import psycopg2
import requests

sys.path.insert(0, '/home/jes/control-plane')

from dotenv import dotenv_values
from google_readers import get_recent_emails, get_todays_calendar
from recruiter_watcher import is_real_recruiter

LOG_FILE = '/tmp/event_engine.log'
NOTIFIED_FILE = '/home/jes/control-plane/event_engine_notified.json'
ENV_FILE = '/home/jes/control-plane/.env'
POLL_INTERVAL = 60

INTERVIEW_KW = ['interview', 'schedule', 'phone screen', 'technical assessment']
STATUS_KW = ['application', 'status', 'next steps', 'offer', 'unfortunately']

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)


def get_db():
    return psycopg2.connect(
        host='127.0.0.1', port=5432, dbname='controlplane',
        user='admin', password=os.getenv('CONTROLPLANE_DB_PASS', 'adminpass'))


def load_notified():
    if os.path.exists(NOTIFIED_FILE):
        try:
            with open(NOTIFIED_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {'emails': [], 'calendar': [], 'tasks': []}


def save_notified(notified):
    with open(NOTIFIED_FILE, 'w') as f:
        json.dump(notified, f)


def send_telegram(token, chat_id, text):
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    resp = requests.post(url, json={'chat_id': chat_id, 'text': text}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def score_email(sender, subject):
    subj = subject.lower()
    if any(kw in subj for kw in INTERVIEW_KW):
        return 10, 'interview_invitation'
    if is_real_recruiter(sender, subject):
        return 9, 'recruiter_reply'
    if 'offer' in subj:
        return 10, 'offer_update'
    if any(kw in subj for kw in ['unfortunately', 'not moving forward', 'regret']):
        return 7, 'rejection_update'
    if any(kw in subj for kw in STATUS_KW):
        return 6, 'application_status'
    return 0, None


def check_gmail(notified):
    events = []
    try:
        emails = get_recent_emails(max_results=10)
    except Exception as e:
        log.error(f'Gmail fetch failed: {e}')
        return events
    for email in emails:
        eid = email.get('id', '')
        if not eid or eid in notified.get('emails', []):
            continue
        sender = email.get('from', '')
        subject = email.get('subject', '')
        score, etype = score_email(sender, subject)
        if score > 0:
            events.append({
                'id': f'email_{eid}', 'source': 'gmail',
                'priority': score, 'type': etype,
                'title': f'{etype}: {subject}',
                'detail': f'From: {sender}\n{email.get("snippet", "")[:200]}',
            })
            notified.setdefault('emails', []).append(eid)
    return events


def check_calendar(notified):
    events = []
    try:
        cal_events = get_todays_calendar()
    except Exception as e:
        log.error(f'Calendar fetch failed: {e}')
        return events
    now = datetime.now().astimezone()
    window = now + timedelta(minutes=15)
    for ev in cal_events:
        start_str = ev.get('start', '')
        if not start_str or 'T' not in start_str:
            continue
        try:
            start_dt = datetime.fromisoformat(start_str)
        except Exception:
            continue
        summary = ev.get('summary', '(no title)')
        cal_id = f'cal_{summary}_{start_str}'
        if cal_id in notified.get('calendar', []):
            continue
        if now <= start_dt <= window:
            events.append({
                'id': cal_id, 'source': 'calendar',
                'priority': 8, 'type': 'calendar_soon',
                'title': f'Starting in {int((start_dt - now).total_seconds() / 60)}min: {summary}',
                'detail': f'{start_str} — {ev.get("location", "")}',
            })
            notified.setdefault('calendar', []).append(cal_id)
    return events


def check_tasks(notified, last_check):
    events = []
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute(
            "SELECT id, title, status, result FROM agent_tasks "
            "WHERE updated_at >= %s AND status IN ('completed','failed')",
            (last_check,))
        for row in cur.fetchall():
            tid = str(row[0])
            if tid in notified.get('tasks', []):
                continue
            status = row[2]
            priority = 6 if status == 'failed' else 5
            events.append({
                'id': f'task_{tid}', 'source': 'task_queue',
                'priority': priority, 'type': f'task_{status}',
                'title': f'Task {status}: {row[1]}',
                'detail': str(row[3] or '')[:300],
            })
            notified.setdefault('tasks', []).append(tid)
        cur.execute(
            "SELECT id, title FROM agent_tasks "
            "WHERE created_at >= %s AND assigned_to = 'alexandra'",
            (last_check,))
        for row in cur.fetchall():
            tid = str(row[0])
            key = f'new_{tid}'
            if key in notified.get('tasks', []):
                continue
            events.append({
                'id': key, 'source': 'task_queue',
                'priority': 3, 'type': 'new_alexandra_task',
                'title': f'New task for Alexandra: {row[1]}',
                'detail': '',
            })
            notified.setdefault('tasks', []).append(key)
        cur.close(); conn.close()
    except Exception as e:
        log.error(f'Task check failed: {e}')
    return events


def insert_pending_event(source, priority, title, detail):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO pending_events (source, priority, title, detail) "
            "VALUES (%s, %s, %s, %s)",
            (source, priority, title, detail))
        conn.commit(); cur.close(); conn.close()
    except Exception as e:
        log.error(f'Failed to insert pending event: {e}')


def dispatch(event, token, chat_id):
    p = event['priority']
    title = event['title']
    detail = event.get('detail', '')
    if p >= 7:
        emoji = {10: '\U0001f6a8', 9: '\U0001f4e7', 8: '\U0001f4c5', 7: '\u26a0\ufe0f'}.get(p, '\U0001f514')
        msg = f'{emoji} [{event["source"].upper()}] P{p}\n{title}\n{detail}'.strip()
        try:
            send_telegram(token, chat_id, msg)
            log.info(f'Telegram sent P{p}: {title}')
        except Exception as e:
            log.error(f'Telegram failed for P{p} {title}: {e}')
    elif p >= 4:
        insert_pending_event(event['source'], p, title, detail)
        log.info(f'Pending event P{p}: {title}')
    else:
        log.info(f'Logged P{p}: {title}')


def poll(last_check):
    env = dotenv_values(ENV_FILE)
    token = env.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = env.get('TELEGRAM_CHAT_ID', '')
    if not token or not chat_id:
        log.error('TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing')
        return

    notified = load_notified()
    all_events = []
    all_events.extend(check_gmail(notified))
    all_events.extend(check_calendar(notified))
    all_events.extend(check_tasks(notified, last_check))
    save_notified(notified)

    all_events.sort(key=lambda e: e['priority'], reverse=True)
    for event in all_events:
        dispatch(event, token, chat_id)
    log.info(f'Poll done: {len(all_events)} events processed')


def main():
    log.info('event_engine starting')
    last_check = datetime.now(timezone.utc) - timedelta(minutes=2)
    while True:
        try:
            poll(last_check)
        except Exception as e:
            log.error(f'Unhandled error in poll: {e}')
        last_check = datetime.now(timezone.utc)
        log.info(f'Sleeping {POLL_INTERVAL}s')
        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()
