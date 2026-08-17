import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SHEET_RANGE = os.getenv("SHEET_RANGE", "Sheet1!A2:J")

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = os.getenv("SENDER_NAME", "GA4 Compliance Monitor")

GCP_PROJECT = os.getenv("GCP_PROJECT")
OAUTH_CREDENTIALS_JSON = os.getenv("OAUTH_CREDENTIALS_JSON")

if not OAUTH_CREDENTIALS_JSON and GCP_PROJECT:
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{GCP_PROJECT}/secrets/OAUTH_CREDENTIALS/versions/latest"
        response = client.access_secret_version(request={"name": name})
        OAUTH_CREDENTIALS_JSON = response.payload.data.decode("UTF-8")
        print("Loaded OAuth credentials from Secret Manager.")
    except Exception as e:
        print(f"Error fetching OAuth credentials from Secret Manager: {e}")

if not OAUTH_CREDENTIALS_JSON and os.path.exists("oauth_credentials.json"):
    with open("oauth_credentials.json", "r") as f:
        OAUTH_CREDENTIALS_JSON = f.read()
    print("Loaded OAuth credentials from local file.")

BASE_DIMENSIONS = [dim.strip() for dim in os.getenv("BASE_DIMENSIONS", "page_location,page_referrer").split(",") if dim.strip()]

def validate_config():
    missing = []
    if not GOOGLE_SHEET_ID: missing.append("GOOGLE_SHEET_ID")
    if not SENDER_EMAIL: missing.append("SENDER_EMAIL")
    if not OAUTH_CREDENTIALS_JSON: missing.append("OAUTH_CREDENTIALS_JSON (or local oauth_credentials.json file)")
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
