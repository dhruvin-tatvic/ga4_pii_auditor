import sys
import os

# Add current dir to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from googleapiclient.discovery import build
from app.utils.auth import get_oauth_creds

def list_properties():
    creds = get_oauth_creds()
    # Build the Admin API service
    service = build('analyticsadmin', 'v1beta', credentials=creds)

    print("Fetching accounts...")
    accounts_response = service.accounts().list().execute()
    accounts = accounts_response.get('accounts', [])
    
    if not accounts:
        print("No Google Analytics accounts found.")
        return

    print(f"Found {len(accounts)} accounts. Fetching properties for each...")
    
    for account in accounts:
        account_name = account['name']
        display_name = account['displayName']
        print(f"\nAccount: {display_name} ({account_name})")
        
        try:
            properties_response = service.properties().list(filter=f"parent:{account_name}").execute()
            properties = properties_response.get('properties', [])
            
            for prop in properties:
                prop_name = prop['name']
                prop_display = prop['displayName']
                print(f"  -> Property: {prop_display} (ID: {prop_name.split('/')[1]})")
        except Exception as e:
            print(f"  -> Error fetching properties for this account: {e}")

if __name__ == "__main__":
    list_properties()
