import datetime
from app.config import validate_config, BASE_DIMENSIONS
from app.services.sheets_client import SheetsClient
from app.services.ga4_client import GA4Client
from app.services.report_generator import ReportGenerator
from app.services.email_sender import EmailSender

def parse_date(date_str, format_str="%Y-%m-%d"):
    try:
        return datetime.datetime.strptime(date_str, format_str).date()
    except (ValueError, TypeError):
        return None

def run_audit():
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
