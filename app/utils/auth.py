import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from app.config import OAUTH_CREDENTIALS_JSON

def get_oauth_creds(access_email=None):
    creds_data = json.loads(OAUTH_CREDENTIALS_JSON)
    refresh_token = creds_data["refresh_token"]
    scopes = creds_data["scopes"]
    
    if access_email:
        from app.config import ACCESS_TOKENS
        token = ACCESS_TOKENS.get(access_email)
        if token:
            refresh_token = token
            # Restrict scopes for alternate tokens to avoid 'invalid_scope' errors
            scopes = ["https://www.googleapis.com/auth/analytics.readonly"]
            
    creds = Credentials(
        token=creds_data.get("token"),
        refresh_token=refresh_token,
        token_uri=creds_data["token_uri"],
        client_id=creds_data["client_id"],
        client_secret=creds_data["client_secret"],
        scopes=scopes,
    )
    if not creds.valid:
        creds.refresh(Request())
    return creds
