import os
import base64
from datetime import datetime
from email.mime.text import MIMEText

_ENV_PATH = "/home/jes/control-plane/.env"
_CREDS_PATH = "/home/jes/control-plane/google_credentials.json"
_TOKEN_PATH = "/home/jes/control-plane/google_token.json"
_LOG_PATH = "/tmp/notifier.log"
_GMAIL_FROM = "james.3sloan@gmail.com"
_GMAIL_TO = "james.3sloan@gmail.com"


def _log(level, msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(_LOG_PATH, "a") as f:
            f.write(f"{ts} [{level}] {msg}\n")
    except Exception:
        pass


def _load_env(path=_ENV_PATH):
    env = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return env


def send_sms(message):
    try:
        env = _load_env()
        account_sid = os.getenv("TWILIO_ACCOUNT_SID") or env.get("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN") or env.get("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_FROM_NUMBER") or env.get("TWILIO_FROM_NUMBER")
        to_number = os.getenv("TWILIO_TO_NUMBER") or env.get("TWILIO_TO_NUMBER")
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        msg = client.messages.create(body=message, from_=from_number, to=to_number)
        _log("INFO", f"SMS sent sid={msg.sid} to={to_number} body={message!r}")
        return True
    except Exception as e:
        _log("ERROR", f"SMS failed: {e}")
        return False


def send_email(subject, body):
    try:
        import json
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        with open(_TOKEN_PATH) as f:
            token_data = json.load(f)
        with open(_CREDS_PATH) as f:
            creds_data = json.load(f).get("installed", {})

        creds = Credentials(
            token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=creds_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=creds_data.get("client_id"),
            client_secret=creds_data.get("client_secret"),
            scopes=["https://www.googleapis.com/auth/gmail.send"],
        )
        if not creds.valid:
            creds.refresh(Request())
            token_data["access_token"] = creds.token
            with open(_TOKEN_PATH, "w") as f:
                json.dump(token_data, f)

        service = build("gmail", "v1", credentials=creds)
        mime_msg = MIMEText(body)
        mime_msg["to"] = _GMAIL_TO
        mime_msg["from"] = _GMAIL_FROM
        mime_msg["subject"] = subject
        raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()
        result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        _log("INFO", f"Email sent id={result.get('id')} subject={subject!r}")
        return True
    except Exception as e:
        _log("ERROR", f"Email failed: {e}")
        return False


def send_notification(message, subject=None):
    sms_ok = send_sms(message)
    email_ok = send_email(subject or "Alexandra Notification", message)
    return {"sms": sms_ok, "email": email_ok}
