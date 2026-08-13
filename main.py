import os
import re
import json
import base64
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
from jinja2 import Environment, FileSystemLoader
from google.cloud import secretmanager

load_dotenv()

# --- CONFIGURATION ---
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SHEET_RANGE = os.getenv("SHEET_RANGE", "Sheet1!A2:J")

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = os.getenv("SENDER_NAME", "GA4 Compliance Monitor")

GCP_PROJECT = os.getenv("GCP_PROJECT")
OAUTH_CREDENTIALS_JSON = os.getenv("OAUTH_CREDENTIALS_JSON")

if not OAUTH_CREDENTIALS_JSON and GCP_PROJECT:
    try:
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

def get_oauth_creds():
    creds_data = json.loads(OAUTH_CREDENTIALS_JSON)
    creds = Credentials(
        token=creds_data.get("token"),
        refresh_token=creds_data["refresh_token"],
        token_uri=creds_data["token_uri"],
        client_id=creds_data["client_id"],
        client_secret=creds_data["client_secret"],
        scopes=creds_data["scopes"],
    )
    if not creds.valid:
        creds.refresh(Request())
    return creds

# --- PII DETECTOR ---
class PIIDetector:
    def __init__(self):
        self.email_regex = re.compile(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)')
        self.phone_regex = re.compile(r'(\+?\d{1,3}?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})')

    def scan_value(self, value):
        if not value or not isinstance(value, str):
            return []
        found_pii = []
        for email in self.email_regex.findall(value):
            found_pii.append({"type": "Email Address", "matched_string": email})
        for phone in self.phone_regex.findall(value):
            digit_count = len(re.sub(r'\D', '', phone))
            if 10 <= digit_count <= 15:
                found_pii.append({"type": "Phone Number", "matched_string": phone})
        return found_pii

    def scan_row(self, row_data, dimensions):
        leaks = []
        for dimension in dimensions:
            value = row_data.get(dimension, "")
            detected = self.scan_value(value)
            for item in detected:
                leaks.append({
                    "dimension": dimension,
                    "flagged_value": value,
                    "type": item["type"]
                })
        return leaks

# --- SHEETS CLIENT ---
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

# --- GA4 CLIENT ---
class GA4Client:
    def __init__(self):
        creds = get_oauth_creds()
        self.client = BetaAnalyticsDataClient(credentials=creds)
        self.pii_detector = PIIDetector()

    def audit_property(self, property_id, start_date, end_date, dimensions):
        property_path = f"properties/{property_id}"
        api_dimensions = [Dimension(name=dim) for dim in dimensions]
        metrics = [Metric(name="activeUsers")]
        request = RunReportRequest(
            property=property_path,
            dimensions=api_dimensions,
            metrics=metrics,
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        )
        try:
            response = self.client.run_report(request)
        except Exception as e:
            print(f"Error querying GA4 property {property_id}: {e}")
            return []

        all_leaks = []
        seen_leaks = set()
        for row in response.rows:
            row_data = {}
            for i, dim_val in enumerate(row.dimension_values):
                row_data[dimensions[i]] = dim_val.value
            leaks = self.pii_detector.scan_row(row_data, dimensions)
            for leak in leaks:
                leak_sig = (leak["dimension"], leak["flagged_value"], leak["type"])
                if leak_sig not in seen_leaks:
                    seen_leaks.add(leak_sig)
                    all_leaks.append(leak)
        return all_leaks

# --- REPORT GENERATOR ---
class ReportGenerator:
    def __init__(self):
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def generate_report(self, client_name, property_id, start_date, end_date, leaks):
        template_data = {
            "client_name": client_name,
            "property_id": property_id,
            "start_date": start_date,
            "end_date": end_date,
            "leaks": leaks
        }
        if not leaks:
            template = self.env.get_template('clean_report.html')
        else:
            template = self.env.get_template('urgent_report.html')
        return template.render(template_data)

# --- EMAIL SENDER ---
class EmailSender:
    def __init__(self):
        self.sender_email = SENDER_EMAIL
        self.sender_name = SENDER_NAME
        creds = get_oauth_creds()
        self.service = build('gmail', 'v1', credentials=creds)

    def send_email(self, recipient_email, cc_email, subject, html_content):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.sender_name} <{self.sender_email}>"
        msg['To'] = recipient_email
        if cc_email:
            msg['Cc'] = cc_email
        part = MIMEText(html_content, 'html')
        msg.attach(part)
        
        encoded_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        
        create_message = {
            'raw': encoded_message
        }
        
        try:
            message = (self.service.users().messages().send(userId="me", body=create_message).execute())
            print(f"Email sent successfully to {recipient_email} (CC: {cc_email}). Message ID: {message['id']}")
            return True
        except Exception as e:
            print(f"Failed to send email to {recipient_email}: {e}")
            return False

# --- ORCHESTRATOR ---
def parse_date(date_str, format_str="%Y-%m-%d"):
    try:
        return datetime.datetime.strptime(date_str, format_str).date()
    except (ValueError, TypeError):
        return None

def run_audit(request):
    print("Starting GA4 PII Audit...")
    try:
        validate_config()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return f"Configuration Error: {e}", 500

    try:
        sheets_client = SheetsClient()
        ga4_client = GA4Client()
        report_generator = ReportGenerator()
        email_sender = EmailSender()
    except Exception as e:
        print(f"Initialization Error: {e}")
        return f"Initialization Error: {e}", 500

    print("Fetching audit targets from Google Sheets...")
    try:
        targets = sheets_client.get_audit_targets()
    except Exception as e:
        print(f"Failed to fetch targets: {e}")
        return f"Failed to fetch targets: {e}", 500
        
    print(f"Found {len(targets)} properties to audit.")
    
    for target in targets:
        client_name = target["client_name"]
        property_id = target["property_id"]
        recipient_email = target["send_to"]
        cc_email = target.get("send_to_cc", "")
        custom_dimensions = target.get("custom_dimensions", [])
        
        dimensions_to_scan = list(set(BASE_DIMENSIONS + custom_dimensions))
        
        interval = target.get("interval_days", "7")
        try:
            interval_days = int(interval)
        except ValueError:
            interval_days = 7
            
        start_date_str_sheet = target.get("start_date", "")
        parsed_start_date = parse_date(start_date_str_sheet)
        
        if parsed_start_date:
            end_date = parsed_start_date + datetime.timedelta(days=interval_days)
            start_date_query = parsed_start_date.strftime("%Y-%m-%d")
            end_date_query = end_date.strftime("%Y-%m-%d")
            display_start = parsed_start_date.strftime("%d-%m-%Y")
            display_end = end_date.strftime("%d-%m-%Y")
        else:
            end_date_obj = datetime.date.today()
            start_date_obj = end_date_obj - datetime.timedelta(days=interval_days)
            start_date_query = f"{interval_days}daysAgo"
            end_date_query = "today"
            display_start = start_date_obj.strftime("%d-%m-%Y")
            display_end = end_date_obj.strftime("%d-%m-%Y")

        print(f"\nAuditing Property: {client_name} (ID: {property_id})")
        print(f"  -> Target Dates: {display_start} to {display_end}")
        print(f"  -> Scanning Dimensions: {', '.join(dimensions_to_scan)}")
        
        leaks = ga4_client.audit_property(property_id, start_date=start_date_query, end_date=end_date_query, dimensions=dimensions_to_scan)
        
        if leaks:
            print(f"  -> URGENT: Found {len(leaks)} PII leaks!")
            subject = f"[URGENT] GA4 PII Leak Detected - {client_name}"
        else:
            print("  -> ALL CLEAR: No PII detected.")
            subject = f"[ALL CLEAR] GA4 PII Audit - {client_name}"
            
        html_report = report_generator.generate_report(
            client_name=client_name,
            property_id=property_id,
            start_date=display_start,
            end_date=display_end,
            leaks=leaks
        )
        
        print(f"  -> Sending report to {recipient_email}...")
        email_sender.send_email(recipient_email, cc_email, subject, html_report)

    print("\nAudit completed successfully.")
    return "Audit completed successfully.", 200

if __name__ == "__main__":
    run_audit(None)
