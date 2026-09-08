import re

class PIIDetector:
    def __init__(self):
        self.email_regex = re.compile(r'[a-zA-Z0-9_.+-]+(?:@|%40)[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', flags=re.IGNORECASE)
        self.phone_regex = re.compile(r'\b(?:(?:\+|%2B)(?:1|91)[-.\s%20])?\(?[2-9]\d{2}\)?[-.\s%20]+[2-9]\d{2}[-.\s%20]+\d{4}\b|\b(?:\+|%2B)(?:1|91)[-.\s%20][2-9]\d{9}\b')
        self.name_regex = re.compile(r'(?:\b||-)(?:first_?name|last_?name|fname|lname|name)=([^&#\s]+)', flags=re.IGNORECASE)

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
