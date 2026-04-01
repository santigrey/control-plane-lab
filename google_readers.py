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

def _load_credentials():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    with open(TOKEN_FILE) as f:
        token_data = json.load(f)
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
        events.append({
            'summary': item.get('summary', '(no title)'),
            'start': start.get('dateTime') or start.get('date', ''),
            'end': end.get('dateTime') or end.get('date', ''),
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
