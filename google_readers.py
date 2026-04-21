import json
import os
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)
import socket as _socket
_orig_getaddrinfo = _socket.getaddrinfo
def _ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, _socket.AF_INET, type, proto, flags)
_socket.getaddrinfo = _ipv4_getaddrinfo

from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_FILE = os.path.join(BASE_DIR, 'google_credentials.json')
TOKEN_FILE = os.path.join(BASE_DIR, 'google_token.json')

# AUTHORITATIVE SCOPE LIST -- single source of truth for Alexandra's Google access.
# reauth_gmail.py imports this. Add new scopes here when adding new Google tools.
# Day 65 lesson: scope drift between this file and reauth script caused silent
# HTTP 403s. Never hardcode scopes elsewhere -- import from here.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]

class ScopeMismatchError(RuntimeError):
    pass

def _assert_token_scopes(token_data):
    """Raise ScopeMismatchError if token is missing any required SCOPE.
    Fails loud at credential load so smoke test catches scope drift nightly."""
    have = set((token_data.get('scope') or '').split())
    need = set(SCOPES)
    missing = need - have
    if missing:
        raise ScopeMismatchError(
            f"Token is missing required scopes: {sorted(missing)}. "
            f"Run reauth_gmail.py to refresh."
        )

def _load_credentials():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    with open(TOKEN_FILE) as f:
        token_data = json.load(f)
    _assert_token_scopes(token_data)
    with open(CREDS_FILE) as f:
        creds_data = json.load(f)
    app = creds_data.get('installed') or creds_data.get('web')
    creds = Credentials(
        token=token_data.get('access_token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri=app['token_uri'],
        client_id=app['client_id'],
        client_secret=app['client_secret'],
        scopes=token_data.get('scope', '').split(),
    )
    if creds.expired or not creds.valid:
        creds.refresh(Request())
        token_data['access_token'] = creds.token
        if creds.refresh_token:
            token_data['refresh_token'] = creds.refresh_token
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)
    return creds

def get_recent_emails(max_results=10):
    from googleapiclient.discovery import build
    creds = _load_credentials()
    service = build('gmail', 'v1', credentials=creds)
    after = int((datetime.now(timezone.utc) - timedelta(hours=24)).timestamp())
    result = service.users().messages().list(
        userId='me', q=f'after:{after}', maxResults=max_results
    ).execute()
    messages = result.get('messages', [])
    emails = []
    for msg in messages:
        detail = service.users().messages().get(
            userId='me', id=msg['id'], format='metadata',
            metadataHeaders=['From', 'Subject', 'Date']
        ).execute()
        headers = {h['name']: h['value'] for h in detail.get('payload', {}).get('headers', [])}
        emails.append({
            'id': msg['id'],
            'from': headers.get('From', ''),
            'subject': headers.get('Subject', '(no subject)'),
            'snippet': detail.get('snippet', ''),
            'date': headers.get('Date', ''),
        })
    return emails

def get_todays_calendar(calendar_id='primary'):
    from googleapiclient.discovery import build
    creds = _load_credentials()
    service = build('calendar', 'v3', credentials=creds)
    local_now = datetime.now().astimezone()
    tz = local_now.tzinfo
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).astimezone(tz)
    today_end = today_start + timedelta(days=1)
    result = service.events().list(
        calendarId=calendar_id,
        timeMin=today_start.isoformat(),
        timeMax=today_end.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = []
    for item in result.get('items', []):
        start = item.get('start', {})
        end = item.get('end', {})
        start_str = start.get('dateTime') or start.get('date', '')
        day_name = ''
        try:
            day_name = datetime.fromisoformat(start_str).strftime('%A')
        except Exception:
            pass
        events.append({
            'summary': item.get('summary', '(no title)'),
            'start': start_str,
            'day_of_week': day_name,
            'end': end.get('dateTime') or end.get('date', ''),
            'location': item.get('location', ''),
        })
    return events


def get_upcoming_calendar(days=14, calendar_id='primary'):
    """Get calendar events for the next N days (default 7)."""
    from googleapiclient.discovery import build
    creds = _load_credentials()
    service = build('calendar', 'v3', credentials=creds)
    local_now = datetime.now().astimezone()
    tz = local_now.tzinfo
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).astimezone(tz)
    end = start + timedelta(days=days)
    result = service.events().list(
        calendarId=calendar_id,
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = []
    for item in result.get('items', []):
        s = item.get('start', {})
        e = item.get('end', {})
        start_str = s.get('dateTime') or s.get('date', '')
        day_name = ''
        try:
            day_name = datetime.fromisoformat(start_str).strftime('%A')
        except Exception:
            pass
        events.append({
            'summary': item.get('summary', '(no title)'),
            'start': start_str,
            'day_of_week': day_name,
            'end': e.get('dateTime') or e.get('date', ''),
            'location': item.get('location', ''),
        })
    return events

def create_calendar_event(summary, start_time, end_time, description='', location='', timezone='America/Denver', recurrence=None):
    """Create a Google Calendar event.
    
    Args:
        summary: Event title
        start_time: ISO format datetime string (e.g. '2026-03-31T18:00:00')
        end_time: ISO format datetime string (e.g. '2026-03-31T19:00:00')
        description: Optional event description
        location: Optional location
        timezone: Timezone string, defaults to America/Denver
        recurrence: Optional RFC5545 recurrence rule string (e.g. 'RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR;UNTIL=20260627T000000Z')
    
    Returns:
        dict with event id, summary, start, end, and htmlLink
    """
    from googleapiclient.discovery import build
    creds = _load_credentials()
    service = build('calendar', 'v3', credentials=creds)
    event = {
        'summary': summary,
        'start': {'dateTime': start_time, 'timeZone': timezone},
        'end': {'dateTime': end_time, 'timeZone': timezone},
    }
    if description:
        event['description'] = description
    if location:
        event['location'] = location
    if recurrence:
        event['recurrence'] = [recurrence] if isinstance(recurrence, str) else recurrence
    result = service.events().insert(calendarId='primary', body=event).execute()
    return {
        'id': result.get('id', ''),
        'summary': result.get('summary', ''),
        'start': result.get('start', {}).get('dateTime', ''),
        'end': result.get('end', {}).get('dateTime', ''),
        'link': result.get('htmlLink', ''),
    }


def send_email(to, subject, body, attachment_path=None):
    """Send an email via Gmail API.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Plain-text email body
        attachment_path: Optional file path (jailed to /home/jes/control-plane/)

    Returns:
        dict with id, threadId, and labelIds of the sent message
    """
    import base64
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    from googleapiclient.discovery import build

    creds = _load_credentials()
    service = build('gmail', 'v1', credentials=creds)

    if attachment_path:
        msg = MIMEMultipart()
        msg.attach(MIMEText(body, 'plain'))
        jail = '/home/jes/control-plane'
        resolved = os.path.realpath(attachment_path)
        if not resolved.startswith(jail):
            raise ValueError(f'Attachment path outside jail: {resolved}')
        if not os.path.isfile(resolved):
            raise FileNotFoundError(f'Attachment not found: {resolved}')
        with open(resolved, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(resolved)}"')
        msg.attach(part)
    else:
        msg = MIMEText(body, 'plain')

    msg['to'] = to
    msg['subject'] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    sent = service.users().messages().send(
        userId='me', body={'raw': raw}
    ).execute()
    return {
        'id': sent.get('id', ''),
        'threadId': sent.get('threadId', ''),
        'labelIds': sent.get('labelIds', []),
    }
