import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os

with open("oauth_credentials.json", "r") as f:
    creds_data = json.load(f)

creds = Credentials(
    token=creds_data.get("token"),
    refresh_token=creds_data["refresh_token"],
    token_uri=creds_data["token_uri"],
    client_id=creds_data["client_id"],
    client_secret=creds_data["client_secret"],
    scopes=creds_data["scopes"],
)

print(f"Valid before refresh: {creds.valid}")
try:
    creds.refresh(Request())
    print(f"Valid after refresh: {creds.valid}")
    print(f"Has token: {bool(creds.token)}")
except Exception as e:
    print(f"Error during refresh: {e}")
