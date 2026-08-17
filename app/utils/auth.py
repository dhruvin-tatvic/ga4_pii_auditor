import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from app.config import OAUTH_CREDENTIALS_JSON

def get_oauth_creds():
    creds_data = json.loads(OAUTH_CREDENTIALS_JSON)
    creds = Credentials(
        token=creds_data.get("token"),
        refresh_token=creds_data["refresh_token"],
        token_uri=creds_data["token_uri"],
        client_id=creds_data["client_id"],
        client_secret=creds_data["client_secret"],
        scopes=creds_data["scopes"],
    )
    if not creds.valid:
        creds.refresh(Request())
    return creds
