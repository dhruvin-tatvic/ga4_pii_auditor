from googleapiclient.discovery import build
from app.utils.auth import get_oauth_creds
from app.config import GOOGLE_SHEET_ID, SHEET_RANGE


class SheetsClient:
    def __init__(self):
        creds = get_oauth_creds()
        self.service = build('sheets', 'v4', credentials=creds)

    def _read_sheet_values(self):
        sheet = self.service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=SHEET_RANGE,
        ).execute()
        return result.get('values', [])

    def get_client_list(self):
        clients = []
        for row in self._read_sheet_values():
            if len(row) < 4:
                continue

            client_name = row[0].strip() if row[0].strip() else ""
            property_id = row[2].strip() if len(row) > 2 and row[2].strip() else ""
            property_access = row[3].strip() if len(row) > 3 and row[3].strip() else ""
            send_to = row[6].strip() if len(row) > 6 and row[6].strip() else ""
            send_to_cc = row[7].strip() if len(row) > 7 and row[7].strip() else ""

            if client_name and property_id and send_to:
                clients.append({
                    "client_name": client_name,
                    "property_id": property_id,
                    "property_access": property_access,
                    "send_to": send_to,
                    "send_to_cc": send_to_cc,
                })

        return clients

    def get_audit_targets(self):
        targets = []
        for row in self._read_sheet_values():
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
                        "custom_dimensions": []
                    })
        return targets
