import os
import psycopg2
import requests
import json
import logging
from datetime import date
from google_readers import get_recent_emails, get_todays_calendar

logging.basicConfig(
    filename='/tmp/daily_brief.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
log = logging.getLogger(__name__)

JOB_LOG = '/home/jes/control-plane/job_search_log.json'

def search_new_jobs():
    """Fetch remote AI/MLOps jobs from Remotive, return up to 3 not previously seen."""
    if os.path.exists(JOB_LOG):
        with open(JOB_LOG) as f:
            seen = set(json.load(f).get('seen_urls', []))
    else:
        seen = set()

    new_jobs = []
    for query in ['AI Platform Engineer', 'Applied AI Engineer', 'MLOps Engineer']:
        if len(new_jobs) >= 3:
            break
        try:
            resp = requests.get(
                'https://remotive.com/api/remote-jobs',
                params={'search': query, 'limit': 10},
                timeout=15
            )
            resp.raise_for_status()
            for job in resp.json().get('jobs', []):
                url = job.get('url', '')
                if url and url not in seen:
                    new_jobs.append({
                        'title': job.get('title', ''),
                        'company': job.get('company_name', ''),
                        'url': url,
                    })
                    seen.add(url)
                    if len(new_jobs) >= 3:
                        break
        except Exception as e:
            log.warning(f'Job search failed for "{query}": {e}')

    with open(JOB_LOG, 'w') as f:
        json.dump({'seen_urls': list(seen)}, f)

    return new_jobs

def main():
    log.info('Starting daily brief generation')
    conn = psycopg2.connect(
        host='192.168.1.10', port=5432,
        dbname='controlplane', user='admin', password=os.getenv('POSTGRES_PASSWORD', 'adminpass')
    )
    cur = conn.cursor()
    cur.execute('SELECT category, key, value FROM user_profile ORDER BY category, key')
    rows = cur.fetchall()
    profile = '\n'.join(f'{r[0]}.{r[1]}: {r[2]}' for r in rows)
    log.info(f'Loaded {len(rows)} profile entries')
    cur.execute("""
        SELECT title, status, created_at FROM agent_tasks
        WHERE status IN ('pending_approval','approved','running')
        ORDER BY created_at DESC
    """)
    task_rows = cur.fetchall()
    tasks = '\n'.join(f'- [{r[1]}] {r[0]}' for r in task_rows) if task_rows else '(no pending tasks)'
    log.info('Fetching emails and calendar')
    try:
        emails = get_recent_emails(10)
        log.info(f'Fetched {len(emails)} emails')
    except Exception as e:
        log.warning(f'Email fetch failed: {e}')
        emails = []
    try:
        events = get_todays_calendar()
        log.info(f'Fetched {len(events)} calendar events')
    except Exception as e:
        log.warning(f'Calendar fetch failed: {e}')
        events = []
    if emails:
        email_summary = '\n'.join(
            f'- From: {m["from"]} | Subject: {m["subject"]} | {m["snippet"][:80]}'
            for m in emails
        )
    else:
        email_summary = '(no emails in last 24h)'
    if events:
        event_list = '\n'.join(
            f'- {e["summary"]} [{e["start"]} - {e["end"]}]' +
            (f' @ {e["location"]}' if e['location'] else '')
            for e in events
        )
    else:
        event_list = '(no events today)'
    try:
        import psycopg2 as _pg
        _jconn = _pg.connect(host='192.168.1.10', port=5432, dbname='controlplane', user='admin', password=os.getenv('POSTGRES_PASSWORD', 'adminpass'))
        _jcur = _jconn.cursor()
        _jcur.execute('SELECT status, COUNT(*) FROM job_applications GROUP BY status ORDER BY COUNT(*) DESC')
        _jrows = _jcur.fetchall()
        _jcur.execute("SELECT company, role, status FROM job_applications WHERE status='applied' ORDER BY last_updated DESC LIMIT 5")
        _active = _jcur.fetchall()
        _jconn.close()
        job_stats = 'Counts: ' + ', '.join(f'{r[1]} {r[0]}' for r in _jrows)
        if _active:
            job_stats += '\nActive: ' + ', '.join(f'{r[0]} ({r[2]})' for r in _active)
    except Exception as _je:
        job_stats = '(job pipeline unavailable)'

    prompt = (
        'You are Alexandra, a personal AI companion. Based on the context below, '
        'generate a concise morning brief covering: 1) what to focus on today, '
        '2) pending tasks needing attention, 3) important emails needing action, '
        '4) today\'s meetings and events, 5) one proactive suggestion.\n\n'
        f'USER PROFILE:\n{profile}\n\n'
        f'PENDING TASKS:\n{tasks}\n\n'
        f'EMAILS (last 24h):\n{email_summary}\n\n'
        f'CALENDAR (today):\n{event_list}\n\n'
        f'JOB PIPELINE:\n{job_stats}\n\n'
        'Keep the brief under 250 words. Be direct and actionable.'
    )
    log.info('Sending prompt to agent')
    resp = requests.post('http://192.168.1.10:8000/chat', json={'message': prompt, 'session_id': 'daily_brief'}, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    brief = data.get('response') or json.dumps(data)
    log.info(f'Got response ({len(brief)} chars)')
    try:
        new_jobs = search_new_jobs()
        log.info(f'Found {len(new_jobs)} new job matches')
        if new_jobs:
            job_lines = '\n'.join(
                f'- {j["title"]} @ {j["company"]} — {j["url"]}'
                for j in new_jobs
            )
            brief += f'\n\nNEW JOB MATCHES:\n{job_lines}'
    except Exception as e:
        log.warning(f'Job search section failed: {e}')
    today = date.today().isoformat()
    cur.execute("""
        INSERT INTO agent_tasks (created_by, assigned_to, status, title, result)
        VALUES (%s, %s, %s, %s, %s)
    """, ('alexandra', 'sloan', 'completed',
           f'Daily Brief - {today}', json.dumps({'brief': brief})))
    conn.commit()
    cur.close()
    conn.close()
    print(brief)
    try:
        from dotenv import dotenv_values as _dv
        import urllib.request as _ur
        _env = _dv('/home/jes/control-plane/.env')
        _tok = _env.get('TELEGRAM_BOT_TOKEN', '')
        _cid = _env.get('TELEGRAM_CHAT_ID', '')
        if _tok and _cid:
            _turl = f'https://api.telegram.org/bot{_tok}/sendMessage'
            _tmsg = json.dumps({'chat_id': _cid, 'text': f'Good morning James.\n\n{brief[:3000]}', 'parse_mode': 'HTML'}).encode()
            _treq = _ur.Request(_turl, data=_tmsg, headers={'Content-Type': 'application/json'})
            with _ur.urlopen(_treq, timeout=10) as _tr:
                log.info(f'Telegram brief sent: {_tr.status}')
    except Exception as _te:
        log.warning(f'Telegram brief failed: {_te}')

    try:
        import sys as _sys
        _sys.path.insert(0, '/home/jes/control-plane')
        from notifier import send_notification
        summary = ('Alexandra: ' + brief)[:160]
        send_notification(summary, subject='Alexandra Daily Brief')
        log.info('SMS notification sent')
    except Exception as _e:
        log.warning(f'SMS notification failed: {_e}')
    log.info('Daily brief complete')

if __name__ == '__main__':
    main()
