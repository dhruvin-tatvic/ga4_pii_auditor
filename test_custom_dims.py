import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from googleapiclient.discovery import build
from app.utils.auth import get_oauth_creds

def test_fetch_custom_dims():
    creds = get_oauth_creds()
    # Build the Admin API service
    service = build('analyticsadmin', 'v1beta', credentials=creds)
    # Using testing property ID 360918272
    try:
        response = service.properties().customDimensions().list(parent="properties/360918272").execute()
        print("Custom Dimensions Response:")
        print(response)
    except Exception as e:
        print(f"Error fetching custom dimensions: {e}")

if __name__ == "__main__":
    test_fetch_custom_dims()
