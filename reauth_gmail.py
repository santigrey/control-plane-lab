"""
Google OAuth re-auth script (Day 64 rebuild).
Restores tokens for gmail.send, gmail.readonly, calendar.readonly.

Usage from your LAPTOP (Mac mini), not from CiscoKid directly:
  ssh -L 8765:localhost:8765 jes@ciscokid
  cd /home/jes/control-plane
  /home/jes/control-plane/orchestrator/.venv/bin/python reauth_gmail.py

The script will print a URL. Open it in your Mac mini browser.
Google will redirect to http://localhost:8765/... which SSH tunnels to CiscoKid.
The script captures the token, writes google_token.json, and exits.
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
PORT = 8899

flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
print(f"Starting local OAuth server on port {PORT}...")
print("Open the URL below in your browser (the one with the SSH tunnel).")
creds = flow.run_local_server(port=PORT, open_browser=False)

token_data = {
    "access_token": creds.token,
    "refresh_token": creds.refresh_token,
    "token_type": "Bearer",
    "scope": " ".join(SCOPES),
    "expires_in": 3600,
}
with open(TOKEN_PATH, "w") as f:
    json.dump(token_data, f, indent=2)
print(f"\n✓ Token written to {TOKEN_PATH}")
print(f"✓ Scopes authorized: {creds.scopes}")
print(f"✓ Refresh token present: {bool(creds.refresh_token)}")
