import re

class PIIDetector:
    def __init__(self):
        self.email_regex = re.compile(r'\b[A-Za-z0-9][A-Za-z0-9._%+-]*?(?:@|%40)[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\b',flags=re.IGNORECASE)

        self.phone_regex = re.compile(r'(?<!\d)(?:(?:\+|%2B)(?:91|1)[-.\s%20]?)?(?:[6-9]\d{9})(?!\d)',flags=re.IGNORECASE)

        self.name_regex = re.compile(r'(?:^|[?&])(?:first_?name|last_?name|fname|lname|full_?name|customer_?name|user_?name)=([^&#\s]+)',flags=re.IGNORECASE)

    def scan_value(self, value):
        try:
            if not value or not isinstance(value, str):
                return []
            found_pii = []
            
            for m in self.email_regex.finditer(value):
                found_pii.append({"type": "Email Address", "matched_string": m.group(0)})
                
            for m in self.phone_regex.finditer(value):
                found_pii.append({"type": "Phone Number", "matched_string": m.group(0)})
                
            for m in self.name_regex.finditer(value):
                found_pii.append({"type": "Name", "matched_string": m.group(0)})
                
            return found_pii
        except Exception as e:
            raise Exception(f"PII scan error: {e}")

    def scan_row(self, row_data, dimensions):
        try:
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
        except Exception as e:
            raise Exception(f"Row scan error: {e}")
