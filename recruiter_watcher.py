#!/usr/bin/env python3
"""Proactive recruiter email watcher for Alexandra."""

import json
import logging
import os
import re
import sys
import time

import requests

sys.path.insert(0, '/home/jes/control-plane')

from dotenv import dotenv_values
from google_readers import get_recent_emails

LOG_FILE = '/tmp/recruiter_watcher.log'
NOTIFIED_FILE = '/home/jes/control-plane/notified_emails.json'
ENV_FILE = '/home/jes/control-plane/.env'
POLL_INTERVAL = 15 * 60  # 15 minutes

# Automated job board / ATS domains — never real human outreach
BLACKLIST_DOMAINS = {
    'jobleads.com', 'jobright.ai', 'adzuna.com', 'indeed.com', 'linkedin.com',
    'glassdoor.com', 'ziprecruiter.com', 'monster.com', 'careerbuilder.com',
    'dice.com', 'simplyhired.com', 'gohiretalent.info', 'jobscan.co',
    'jobvite.com', 'greenhouse.io', 'lever.co', 'workday.com',
    'myworkdayjobs.com', 'smartrecruiters.com', 'icims.com',
}

# Local-part prefixes that indicate automated/system senders
AUTOMATED_PREFIXES = (
    'noreply', 'no-reply', 'mailer', 'support', 'alert',
    'jobs', 'career', 'hiring',
)

# Subjects that indicate real human outreach
RECRUITER_SUBJECT_KEYWORDS = [
    'opportunity', 'role', 'position', 'opening', 'hiring', 'interview',
    'recruiter', 'talent', 'your background', 'your experience',
    'your profile', 'connect', 'reach out', 'interested in you',
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)


def parse_sender(from_field):
    """Return (name, email_address) from a From header like 'Jane Doe <jane@co.com>'."""
    m = re.match(r'^(.*?)\s*<([^>]+)>', from_field.strip())
    if m:
        return m.group(1).strip().strip('"'), m.group(2).strip().lower()
    # bare address
    addr = from_field.strip().lower()
    return '', addr


def is_real_recruiter(sender_from, subject):
    """
    Returns True only if the email passes all three gates:
      1. Sender domain is NOT in the blacklist
      2. Sender local-part does NOT start with an automated prefix
      3. Subject matches at least one recruiter keyword
    """
    name, addr = parse_sender(sender_from)

    # Gate 1: blacklisted domain
    if '@' in addr:
        domain = addr.split('@', 1)[1]
        # check exact domain and parent domain (e.g. mail.greenhouse.io)
        parts = domain.split('.')
        for i in range(len(parts) - 1):
            if '.'.join(parts[i:]) in BLACKLIST_DOMAINS:
                log.debug(f'Blacklisted domain: {domain}')
                return False

    # Gate 2: automated sender local-part
    local = addr.split('@')[0] if '@' in addr else addr
    if any(local.startswith(p) for p in AUTOMATED_PREFIXES):
        log.debug(f'Automated sender prefix: {local}')
        return False

    # Gate 3: subject must contain a real-outreach signal
    subj_lower = subject.lower()
    if not any(kw in subj_lower for kw in RECRUITER_SUBJECT_KEYWORDS):
        log.debug(f'Subject lacks recruiter keywords: {subject}')
        return False

    return True


def load_notified():
    if os.path.exists(NOTIFIED_FILE):
        try:
            with open(NOTIFIED_FILE) as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def save_notified(notified):
    with open(NOTIFIED_FILE, 'w') as f:
        json.dump(list(notified), f)


def send_telegram(token, chat_id, text):
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    resp = requests.post(url, json={'chat_id': chat_id, 'text': text}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def poll():
    env = dotenv_values(ENV_FILE)
    token = env.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = env.get('TELEGRAM_CHAT_ID', '')

    if not token or not chat_id:
        log.error('TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing from .env — cannot send notifications')
        return

    notified = load_notified()

    try:
        emails = get_recent_emails(max_results=20)
    except Exception as e:
        log.error(f'Failed to fetch emails: {e}')
        return

    log.info(f'Fetched {len(emails)} emails, {len(notified)} already notified')

    new_count = 0
    for email in emails:
        eid = email.get('id', '')
        if not eid:
            log.warning(f'Email missing id, skipping: {email.get("subject")}')
            continue
        if eid in notified:
            continue

        sender = email.get('from', 'unknown')
        subject = email.get('subject', '(no subject)')

        if not is_real_recruiter(sender, subject):
            log.debug(f'Filtered out: [{subject}] from {sender}')
            continue

        snippet = email.get('snippet', '')
        msg = (
            f"\U0001f4e7 New recruiter email from {sender}\n"
            f"Subject: {subject}\n"
            f"{snippet[:150]}\n\n"
            f"Reply to Alexandra: /brief"
        )

        try:
            send_telegram(token, chat_id, msg)
            notified.add(eid)
            save_notified(notified)
            log.info(f'Notified: [{subject}] from {sender}')
            try:
                import sys as _sys2; _sys2.path.insert(0,'/home/jes/control-plane')
                from mqtt_publisher import publish as _mqtt_pub2
                _mqtt_pub2('agent/events/job_update', {
                    'company': sender,
                    'status': 'recruiter_contact',
                    'role': subject[:100],
                })
            except Exception as _me2:
                log.warning(f'MQTT publish failed: {_me2}')
            new_count += 1
        except Exception as e:
            log.error(f'Telegram send failed for [{subject}]: {e}')

    log.info(f'Poll complete. {new_count} new notifications sent.')


def main():
    log.info('recruiter_watcher starting')
    while True:
        try:
            poll()
        except Exception as e:
            log.error(f'Unhandled error in poll: {e}')
        log.info(f'Sleeping {POLL_INTERVAL}s until next poll')
        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()
