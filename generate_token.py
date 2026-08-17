import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/analytics.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

def main():
    flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
    creds = flow.run_local_server(port=0)
    
    with open('oauth_credentials.json', 'w') as f:
        f.write(creds.to_json())
    print("Successfully generated oauth_credentials.json")

if __name__ == '__main__':
    main()
