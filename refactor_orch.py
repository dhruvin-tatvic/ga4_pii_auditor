import re

with open("app/services/orchestrator.py", "r") as f:
    content = f.read()

# Define the new helper function
helper_func = """
def _process_targets_in_chunks(targets, ga4_client, report_generator, email_sender, excel_generator):
    CHUNK_SIZE = 5
    CHUNK_DELAY = 10  # Seconds to wait between chunks
    ITEM_DELAY = 2    # Seconds to wait between individual audits

    for i in range(0, len(targets), CHUNK_SIZE):
        chunk = targets[i:i + CHUNK_SIZE]
        print(f"\\n--- Processing Chunk {i//CHUNK_SIZE + 1} ({len(chunk)} properties) ---")
        for target in chunk:
            client_name = target["client_name"]
            property_id = target["property_id"]
            recipient_email = target["send_to"]
            cc_email = target.get("send_to_cc", "")
            custom_dimensions = target.get("custom_dimensions", [])
        
            dynamic_custom_dims = ga4_client.get_all_custom_dimensions(property_id)
            dimensions_to_scan = list(set(BASE_DIMENSIONS + custom_dimensions + dynamic_custom_dims))
        
            start_date_str = target.get("start_date", "")
            end_date_str = target.get("end_date", "")
            interval = target.get("interval_days", "7")
            
            parsed_start_date = parse_date(start_date_str)
            parsed_end_date = parse_date(end_date_str)
            
            try:
                interval_days = int(interval)
            except ValueError:
                interval_days = 7
        
            if parsed_start_date and parsed_end_date:
                start_date_query = parsed_start_date.strftime("%Y-%m-%d")
                end_date_query = parsed_end_date.strftime("%Y-%m-%d")
                display_start = parsed_start_date.strftime("%d-%m-%Y")
                display_end = parsed_end_date.strftime("%d-%m-%Y")
            elif parsed_start_date:
                end_date = parsed_start_date + datetime.timedelta(days=interval_days)
                start_date_query = parsed_start_date.strftime("%Y-%m-%d")
                end_date_query = end_date.strftime("%Y-%m-%d")
                display_start = parsed_start_date.strftime("%d-%m-%Y")
                display_end = end_date.strftime("%d-%m-%Y")
            else:
                end_date_obj = datetime.date.today()
                start_date_obj = end_date_obj - datetime.timedelta(days=7)
                start_date_query = "7daysAgo"
                end_date_query = "today"
                display_start = start_date_obj.strftime("%d-%m-%Y")
                display_end = end_date_obj.strftime("%d-%m-%Y")

            print(f"\\nAuditing Property: {client_name} (ID: {property_id})")
            print(f"  -> Target Dates: {display_start} to {display_end}")
            print(f"  -> Scanning Dimensions: {', '.join(dimensions_to_scan)}")
        
            try:
                leaks = ga4_client.audit_property(property_id, start_date=start_date_query, end_date=end_date_query, dimensions=dimensions_to_scan)
            
                attachment_path = None
                if leaks:
                    print(f"  -> URGENT: Found {len(leaks)} PII leaks!")
                    subject = f"[URGENT] GA4 PII Leak Detected - {client_name}"
                    attachment_path = excel_generator.generate_excel_report(client_name, property_id, display_start, display_end, leaks)
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
                email_sender.send_email(recipient_email, cc_email, subject, html_report, attachment_path=attachment_path)
                
                if attachment_path and os.path.exists(attachment_path):
                    os.remove(attachment_path)
            except Exception as e:
                print(f"  -> ERROR: Failed to audit property {property_id}: {e}")
                print(f"  -> Skipping email for {client_name} due to error.")

            time.sleep(ITEM_DELAY)
        if i + CHUNK_SIZE < len(targets):
            print(f"Waiting {CHUNK_DELAY} seconds before processing the next chunk to avoid rate limits...")
            time.sleep(CHUNK_DELAY)
"""

mass_audit_func = """
def run_mass_audit(payload):
    print("Starting Mass GA4 PII Audit...")
    try:
        validate_config()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        if "GOOGLE_SHEET_ID" not in str(e):
            return f"Configuration Error: {e}", 500

    try:
        ga4_client = GA4Client()
        report_generator = ReportGenerator()
        email_sender = EmailSender()
        excel_generator = ExcelGenerator()
    except Exception as e:
        print(f"Initialization Error: {e}")
        return f"Initialization Error: {e}", 500

    targets = payload.get("targets", [])
    if not targets:
        return "No targets provided for mass audit.", 400

    print(f"Found {len(targets)} properties to audit in payload.")
    
    _process_targets_in_chunks(targets, ga4_client, report_generator, email_sender, excel_generator)

    print("\\nMass Audit completed successfully.")
    return "Mass Audit completed successfully.", 200
"""

# Regex to find the chunk loop inside run_audit()
# The loop starts with `CHUNK_SIZE = 5` and ends with `print("\nAudit completed successfully.")`
loop_regex = re.compile(r'    CHUNK_SIZE = 5.*?    print\("\\nAudit completed successfully\."\)', re.DOTALL)

# Replace the loop with a call to _process_targets_in_chunks
replacement = """    _process_targets_in_chunks(targets, ga4_client, report_generator, email_sender, excel_generator)

    print("\\nAudit completed successfully.")"""

content = loop_regex.sub(replacement, content)

# Insert the helper function after `def parse_date`
parts = content.split('def run_audit():')
new_content = parts[0] + helper_func + '\ndef run_audit():' + parts[1] + '\n' + mass_audit_func

with open("app/services/orchestrator.py", "w") as f:
    f.write(new_content)
