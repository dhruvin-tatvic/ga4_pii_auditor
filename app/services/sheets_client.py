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
            if len(row) >= 8:
                client_name = row[0].strip() if len(row) > 0 else ""
                property_name = row[1].strip() if len(row) > 1 else ""
                property_id = row[2].strip() if len(row) > 2 else ""
                start_date = row[5].strip() if len(row) > 5 else ""
                interval_days = row[6].strip() if len(row) > 6 else "7"
                send_to = row[7].strip() if len(row) > 7 else ""
                send_to_cc = row[8].strip() if len(row) > 8 else ""
                custom_dimensions_raw = row[9].strip() if len(row) > 9 else ""
                custom_dimensions = [d.strip() for d in custom_dimensions_raw.split(',') if d.strip()]
                
                if client_name and property_id and send_to:
                    targets.append({
                        "client_name": client_name,
                        "property_name": property_name,
                        "property_id": property_id,
                        "start_date": start_date,
                        "interval_days": interval_days,
                        "send_to": send_to,
                        "send_to_cc": send_to_cc,
                        "custom_dimensions": custom_dimensions
                    })
        return targets
