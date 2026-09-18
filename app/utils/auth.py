import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from app.config import OAUTH_CREDENTIALS_JSON, ACCESS_TOKENS
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv("id")
CLIENT_SECRET = os.getenv("secret")
TOKEN_URI = "https://oauth2.googleapis.com/token"

def get_oauth_creds(access_email=None):
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
        scopes = [
            "https://www.googleapis.com/auth/analytics.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/spreadsheets.readonly"
        ]

    if not refresh_token:
        raise ValueError("No refresh token available. Ensure ACCESS_TOKENS are set in .env")
            
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=scopes,
    )
    if not creds.valid:
        creds.refresh(Request())
    return creds
