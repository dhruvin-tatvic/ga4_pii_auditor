import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from app.config import OAUTH_CREDENTIALS_JSON, ACCESS_TOKENS, TOKEN_GMAIL
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv("id") or os.getenv("CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("secret") or os.getenv("CLIENT_SECRET") or os.getenv("GOOGLE_CLIENT_SECRET")
TOKEN_URI = "https://oauth2.googleapis.com/token"

# Fallback to local client_secret.json if CLIENT_ID/CLIENT_SECRET not in env
if (not CLIENT_ID or not CLIENT_SECRET) and os.path.exists("client_secret.json"):
    try:
        with open("client_secret.json", "r") as f:
            cs_data = json.load(f)
            cs = cs_data.get("installed") or cs_data.get("web") or cs_data
            CLIENT_ID = CLIENT_ID or cs.get("client_id")
            CLIENT_SECRET = CLIENT_SECRET or cs.get("client_secret")
    except Exception:
        pass

def get_oauth_creds(access_email=None):
    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET
    
    if OAUTH_CREDENTIALS_JSON:
        try:
            creds_data = json.loads(OAUTH_CREDENTIALS_JSON)
            client_id = client_id or creds_data.get("client_id")
            client_secret = client_secret or creds_data.get("client_secret")
        except Exception:
            pass

    if access_email and ACCESS_TOKENS.get(access_email):
        refresh_token = ACCESS_TOKENS.get(access_email)
        scopes = ["https://www.googleapis.com/auth/analytics.readonly"]
    elif OAUTH_CREDENTIALS_JSON:
        creds_data = json.loads(OAUTH_CREDENTIALS_JSON)
        refresh_token = creds_data.get("refresh_token")
        scopes = creds_data.get("scopes", [
            "https://www.googleapis.com/auth/analytics.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/spreadsheets.readonly"
        ])
    else:
        # Fallback if no OAUTH_CREDENTIALS_JSON is provided
        refresh_token = ACCESS_TOKENS.get("dhruvin@tatvic.com")
        scopes = None

    if not refresh_token:
        raise ValueError("No refresh token available. Ensure ACCESS_TOKENS are set in .env")
            
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
    )
    if not creds.valid:
        creds.refresh(Request())
    return creds

def get_email_creds():
    """Retrieve OAuth credentials specifically authorized for sending emails via Gmail."""
    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET
    
    if OAUTH_CREDENTIALS_JSON:
        try:
            creds_data = json.loads(OAUTH_CREDENTIALS_JSON)
            client_id = client_id or creds_data.get("client_id")
            client_secret = client_secret or creds_data.get("client_secret")
        except Exception:
            pass

    # Priority 1: dedicated TOKEN_GMAIL from .env
    refresh_token = TOKEN_GMAIL
    if not refresh_token and OAUTH_CREDENTIALS_JSON:
        try:
            creds_data = json.loads(OAUTH_CREDENTIALS_JSON)
            refresh_token = creds_data.get("refresh_token")
        except Exception:
            pass
    if not refresh_token:
        refresh_token = ACCESS_TOKENS.get("dhruvin@tatvic.com")

    if not refresh_token:
        raise ValueError("No refresh token available for email sending. Ensure TOKEN_GMAIL is set in .env")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/gmail.send"],
    )
    if not creds.valid:
        creds.refresh(Request())
    return creds
