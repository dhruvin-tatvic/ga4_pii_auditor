from googleapiclient.discovery import build
from app.utils.auth import get_oauth_creds
from app.config import GOOGLE_SHEET_ID, SHEET_RANGE

class SheetsClient:
    def __init__(self):
        creds = get_oauth_creds()
        self.service = build('sheets', 'v4', credentials=creds)

    def get_audit_targets(self):
        sheet = self.service.spreadsheets()
        result = sheet.values().get(spreadsheetId=GOOGLE_SHEET_ID, range=SHEET_RANGE).execute()
        values = result.get('values', [])
        targets = []
        for row in values:
            if len(row) >= 1:
                client_name = row[0].strip() if len(row) > 0 else ""
                property_name = row[1].strip() if len(row) > 1 else ""
                property_id = row[2].strip() if len(row) > 2 else ""
                property_access = row[3].strip() if len(row) > 3 else None
                start_date = row[4].strip() if len(row) > 4 else ""
                end_date = row[5].strip() if len(row) > 5 else ""
                send_to = row[6].strip() if len(row) > 6 else ""
                send_to_cc = row[7].strip() if len(row) > 7 else ""
                
                if client_name and property_id and send_to:
                    targets.append({
                        "client_name": client_name,
                        "property_name": property_name,
                        "property_id": property_id,
                        "property_access": property_access,
                        "start_date": start_date,
                        "end_date": end_date,
                        "send_to": send_to,
                        "send_to_cc": send_to_cc,
                        "custom_dimensions": [] # Not in the new sheet structure, default empty
                    })
        return targets
