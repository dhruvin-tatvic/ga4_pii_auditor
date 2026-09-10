import re

with open("app/services/orchestrator.py", "r") as f:
    content = f.read()

manager_class = """class GA4ClientManager:
    def __init__(self):
        self.clients = {}
    
    def get_client(self, access_email):
        if not access_email:
            access_email = "default"
        if access_email not in self.clients:
            self.clients[access_email] = GA4Client(access_email if access_email != "default" else None)
        return self.clients[access_email]

"""

# Insert GA4ClientManager after the imports and parse_date
content = content.replace("def _process_targets_in_chunks(", manager_class + "def _process_targets_in_chunks(")

# In _process_targets_in_chunks, replace ga4_client with ga4_client_manager
content = content.replace("def _process_targets_in_chunks(targets, ga4_client, report_generator, email_sender, excel_generator):", 
                          "def _process_targets_in_chunks(targets, ga4_client_manager, report_generator, email_sender, excel_generator):")

# Inside the loop in _process_targets_in_chunks:
# Extract property_access
# ga4_client = ga4_client_manager.get_client(property_access)
loop_insertion = """            property_id = target["property_id"]
            property_access = target.get("property_access", None)
            ga4_client = ga4_client_manager.get_client(property_access)
            recipient_email = target["send_to"]"""
content = content.replace('            property_id = target["property_id"]\n            recipient_email = target["send_to"]', loop_insertion)

# In run_audit:
content = content.replace("ga4_client = GA4Client()", "ga4_client_manager = GA4ClientManager()")
content = content.replace("_process_targets_in_chunks(targets, ga4_client, report_generator", "_process_targets_in_chunks(targets, ga4_client_manager, report_generator")

# In run_single_audit:
content = content.replace("ga4_client = GA4Client()", "ga4_client_manager = GA4ClientManager()")
single_audit_insertion = """    property_id = payload.get("property_id")
    property_access = payload.get("property_access", None)
    ga4_client = ga4_client_manager.get_client(property_access)
    recipient_email = payload.get("send_to")"""
content = content.replace('    property_id = payload.get("property_id")\n    recipient_email = payload.get("send_to")', single_audit_insertion)

# In run_mass_audit:
# Wait, I didn't verify if I need to replace ga4_client in run_mass_audit, but the ga4_client = GA4Client() replacement covers it.
content = content.replace("_process_targets_in_chunks(targets, ga4_client, report_generator", "_process_targets_in_chunks(targets, ga4_client_manager, report_generator")

with open("app/services/orchestrator.py", "w") as f:
    f.write(content)
