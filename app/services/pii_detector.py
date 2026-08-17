import re

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
