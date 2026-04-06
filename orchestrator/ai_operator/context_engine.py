"""Live Context Engine - dynamic situational awareness for Alexandra."""

import os
from datetime import datetime, date, timedelta

import psycopg2
import pytz

DB_DSN = f"postgresql://admin:{os.getenv('CONTROLPLANE_DB_PASS', 'adminpass')}@127.0.0.1:5432/controlplane"
DENVER = pytz.timezone('America/Denver')


def _get_conn():
    return psycopg2.connect(DB_DSN)


def _time_awareness():
    now = datetime.now(DENVER)
    hour = now.hour
    if 5 <= hour < 12:
        period, energy = 'morning', 'peak energy'
    elif 12 <= hour < 17:
        period, energy = 'afternoon', 'steady'
    elif 17 <= hour < 21:
        period, energy = 'evening', 'winding down'
    else:
        period, energy = 'night', 'low energy, should consider rest'

    dow = now.strftime('%A')
    time_str = now.strftime('%A %B %-d, %Y at %-I:%M %p %Z')

    # Per Scholas: M/W/F 6-9 PM ET = 4-7 PM MT
    class_days = {0, 2, 4}  # Mon, Wed, Fri
    is_class_day = now.weekday() in class_days
    class_note = ''
    if is_class_day:
        class_start = now.replace(hour=16, minute=0, second=0)
        class_end = now.replace(hour=19, minute=0, second=0)
        if class_start - timedelta(hours=2) <= now <= class_end:
            class_note = 'Class in session or starting soon (4-7 PM MT)'
        elif now > class_end and now.hour < 23:
            class_note = 'Post-class evening'
            energy = 'post-class, likely tired'
    if not class_note:
        next_class = 'M/W/F 4-7 PM MT'
        class_note = f'No class right now (schedule: {next_class})'

    return time_str, period, dow, energy, class_note


def _active_work_state():
    pending_events = []
    pending_tasks = []
    app_count = 0
    try:
        conn = _get_conn(); cur = conn.cursor()
        cur.execute("SELECT source, priority, title FROM pending_events WHERE acknowledged=FALSE ORDER BY priority DESC LIMIT 5")
        pending_events = [{'source': r[0], 'priority': r[1], 'title': r[2]} for r in cur.fetchall()]
        cur.execute("SELECT title, status FROM agent_tasks WHERE status IN ('pending_approval','approved') ORDER BY created_at DESC LIMIT 5")
        pending_tasks = [{'title': r[0], 'status': r[1]} for r in cur.fetchall()]
        cur.execute("SELECT value FROM user_profile WHERE category='context' AND key='application_count'")
        _ac_row = cur.fetchone()
        app_count = int(_ac_row[0]) if _ac_row else 0
        cur.close(); conn.close()
    except Exception:
        pass
    return pending_events, pending_tasks, app_count


def _project_timeline():
    try:
        conn = _get_conn(); cur = conn.cursor()
        cur.execute("SELECT value FROM user_profile WHERE category='context' AND key='project_start_date'")
        row = cur.fetchone()
        cur.close(); conn.close()
        if row:
            start = datetime.strptime(row[0], '%Y-%m-%d').date()
            day_num = (date.today() - start).days + 1
            return f'Day {day_num} of Project Ascension (started {start.strftime("%b %d")}, target: May 2026)'
    except Exception:
        pass
    return 'Project Ascension (timeline unavailable)'


def _recent_interaction():
    try:
        conn = _get_conn(); cur = conn.cursor()
        cur.execute("SELECT created_at FROM chat_history ORDER BY created_at DESC LIMIT 1")
        row = cur.fetchone()
        cur.close(); conn.close()
        if row:
            last = row[0]
            now = datetime.now(pytz.utc)
            if last.tzinfo is None:
                last = pytz.utc.localize(last)
            delta = now - last
            mins = int(delta.total_seconds() / 60)
            if mins < 5:
                return 'Just chatted'
            elif mins < 60:
                return f'{mins} minutes ago'
            else:
                hours = mins // 60
                if hours >= 8:
                    return f'{hours}h ago (been away several hours, likely just returning)'
                elif hours >= 4:
                    return f'{hours}h ago (been away for a while)'
                else:
                    return f'{hours}h ago'
    except Exception:
        pass
    return 'unknown'


def build_live_context() -> str:
    time_str, period, dow, energy, class_note = _time_awareness()
    pending_events, pending_tasks, app_count = _active_work_state()
    timeline = _project_timeline()
    last_interaction = _recent_interaction()

    lines = [
        '---',
        'LIVE CONTEXT (auto-generated, do not recite verbatim):',
        f'Time: {time_str} ({period})',
        f'Energy: {energy}',
        f'Project: {timeline}',
        f'Applications: {app_count} total',
    ]

    if pending_tasks:
        task_strs = [f'{t["title"]} [{t["status"]}]' for t in pending_tasks]
        lines.append(f'Pending tasks: {len(pending_tasks)} ({", ".join(task_strs[:3])})')
    else:
        lines.append('Pending tasks: none')

    if pending_events:
        ev_strs = [f'P{e["priority"]}: {e["title"]}' for e in pending_events]
        lines.append(f'Unread events: {len(pending_events)} ({", ".join(ev_strs[:3])})')
    else:
        lines.append('Unread events: none')

    lines.append(f'Last interaction: {last_interaction}')
    lines.append(f'Class: {class_note}')
    lines.append('')
    lines.append('Use this context to adapt your tone and suggestions. Late night = be concise, suggest rest if appropriate. Morning = energetic, proactive. During class hours = do not suggest heavy tasks.')
    lines.append('---')

    return '\n'.join(lines)
