"""
Run this once interactively to add gmail.send scope to google_token.json.
Usage: python3 /home/jes/control-plane/reauth_gmail.py
It will print a URL -- open it in a browser, authorize, paste the code back.
"""
from google_auth_oauthlib.flow import InstalledAppFlow
import json

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]
CREDS_PATH = "/home/jes/control-plane/google_credentials.json"
TOKEN_PATH = "/home/jes/control-plane/google_token.json"

flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
creds = flow.run_console()  # prints URL, prompts for paste-back code

token_data = {
    "access_token": creds.token,
    "refresh_token": creds.refresh_token,
    "token_type": "Bearer",
    "scope": " ".join(SCOPES),
    "expires_in": 3600,
}
with open(TOKEN_PATH, "w") as f:
    json.dump(token_data, f, indent=2)
print(f"Token written to {TOKEN_PATH}")
print("Scopes:", creds.scopes)
