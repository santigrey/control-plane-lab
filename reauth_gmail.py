"""
Google OAuth re-auth for Alexandra's Gmail + Calendar access.

SCOPES are imported from google_readers.py (single source of truth).
When adding a new Google tool, add its scope to google_readers.SCOPES --
this script will automatically request it on next re-auth.

Usage (from any device with OpenSSH):
  ssh -L 8899:localhost:8899 jes@192.168.1.10
  cd /home/jes/control-plane
  /home/jes/control-plane/orchestrator/.venv/bin/python reauth_gmail.py

Open the printed URL in your browser, sign in, approve. Script writes
google_token.json and exits.
"""
import json
import os
import sys

# Import authoritative scope list from the module that uses them.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_readers import SCOPES

from google_auth_oauthlib.flow import InstalledAppFlow

CREDS_PATH = "/home/jes/control-plane/google_credentials.json"
TOKEN_PATH = "/home/jes/control-plane/google_token.json"
PORT = 8899

print(f"Requesting scopes from google_readers.SCOPES:")
for s in SCOPES:
    print(f"  - {s}")
print()

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
print(f"\n[OK] Token written to {TOKEN_PATH}")
print(f"[OK] Scopes authorized: {creds.scopes}")
print(f"[OK] Refresh token present: {bool(creds.refresh_token)}")
