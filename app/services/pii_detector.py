import re


class PIIDetector:
    def __init__(self):
        # Email:
        # Detects standard emails as well as emails embedded inside URLs/query parameters.
        # Supports both @ and %40.
        self.email_regex = re.compile(
            r'\b[A-Za-z0-9][A-Za-z0-9._%+-]*?(?:@|%40)'
            r'[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\b',
            flags=re.IGNORECASE
        )

        # Phone:
        # Detects exactly 10-digit Indian mobile numbers when preceded by:
        # mobile, mobilenumber, mobile_number, phone, phone_number
        #
        # Examples:
        # mobile=9876543210
        # mobile_number:9876543210
        # phone_number="9876543210"
        # Also works inside URLs.
        self.phone_regex = re.compile(
            r'\b(?:mobile|mobilenumber|mobile_number|phone|phone_number)'
            r'\b\s*[:=]?\s*[\'"]?\d{10}[\'"]?',
            flags=re.IGNORECASE
        )

        # Name:
        # Detects a name when it follows an explicit name identifier.
        #
        # Examples:
        # name=JohnSmith
        # full_name=John_Smith
        # firstname=Rahul
        # last_name=Sharma
        # name=John-Smith
        # Works inside URLs as well.
        self.name_regex = re.compile(
            r'\b(?:name|full_name|fullname|first_name|firstname|last_name|lastname|'
            r'customer_name|customername|user_name|username|contact_name|contactname)'
            r'\b\s*[:=]?\s*[-_/\'"]*'
            r'[A-Za-z]+(?:[-_.\' ]+[A-Za-z]+){1,3}\b',
            flags=re.IGNORECASE
        )

    def scan_value(self, value):
        try:
            if not value or not isinstance(value, str):
                return []

            # Ignore any value containing "redact" (case-insensitive).
            # Example:
            # redact@gmail.com
            # ?email=redact@gmail.com
            # ?name=redact_JohnSmith
            # ?phone_number=redact9876543210
            if "redact" in value.lower():
                return []

            found_pii = []

            # Email detection
            for m in self.email_regex.finditer(value):
                found_pii.append({
                    "type": "Email Address",
                    "matched_string": m.group(0)
                })

            # Phone detection
            for m in self.phone_regex.finditer(value):
                found_pii.append({
                    "type": "Phone Number",
                    "matched_string": m.group(0)
                })

            # Name detection
            for m in self.name_regex.finditer(value):
                found_pii.append({
                    "type": "Name",
                    "matched_string": m.group(0)
                })

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