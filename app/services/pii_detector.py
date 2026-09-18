import re
from urllib.parse import unquote


class PIIDetector:
    def __init__(self):

        # ---------------------------------------------------------
        # EMAIL
        # ---------------------------------------------------------
        self.email_regex = re.compile(
            r'\b[A-Za-z0-9](?:[A-Za-z0-9._%+-]{0,63})[A-Za-z0-9]'
            r'(?:@|%40)'
            r'[A-Za-z0-9]'
            r'(?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?'
            r'(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?){0,8}'
            r'\.(?!png\b|jpg\b|jpeg\b|svg\b|webp\b|gif\b)'
            r'[A-Za-z]{2,24}\b',
            flags=re.IGNORECASE
        )

        # ---------------------------------------------------------
        # PHONE
        # ---------------------------------------------------------
        self.phone_regex = re.compile(
            r'\b(?:mobile|mobileno|mobilenumber|mobile_number|'
            r'phone|phone_number|mobile_no|phone_no)'
            r'\b\s*[:=]\s*[\'"]?\d{10}[\'"]?',
            flags=re.IGNORECASE
        )

        # ---------------------------------------------------------
        # NAME
        # ---------------------------------------------------------
        self.name_regex = re.compile(
            r'\b(?:name|child_name|childname|full_name|fullname|'
            r'first_name|firstname|last_name|lastname|'
            r'customer_name|customername|user_name|username|'
            r'contact_name|contactname)'
            r'\b\s*[:=]\s*[-_/\'"]*'
            r'[A-Za-z]+(?:[-_.\' +]+[A-Za-z]+){0,3}',
            flags=re.IGNORECASE
        )

    def scan_value(self, value):
        try:
            if not value or not isinstance(value, str):
                return []

            # Ignore redacted values
            if "redact" in value.lower():
                return []

            found_pii = []

            # -----------------------------------------------------
            # Scan original value
            # -----------------------------------------------------
            values_to_scan = [value]

            # -----------------------------------------------------
            # Also scan URL-decoded value
            # This handles encoded JSON/query parameters.
            # -----------------------------------------------------
            decoded_value = unquote(value)

            if decoded_value != value:
                values_to_scan.append(decoded_value)

            # -----------------------------------------------------
            # EMAIL
            # -----------------------------------------------------
            for scan_text in values_to_scan:
                for m in self.email_regex.finditer(scan_text):

                    item = {
                        "type": "Email Address",
                        "matched_string": m.group(0)
                    }

                    if item not in found_pii:
                        found_pii.append(item)

            # -----------------------------------------------------
            # PHONE
            # -----------------------------------------------------
            for scan_text in values_to_scan:
                for m in self.phone_regex.finditer(scan_text):

                    item = {
                        "type": "Phone Number",
                        "matched_string": m.group(0)
                    }

                    if item not in found_pii:
                        found_pii.append(item)

            # -----------------------------------------------------
            # NAME
            # -----------------------------------------------------
            for scan_text in values_to_scan:
                for m in self.name_regex.finditer(scan_text):

                    item = {
                        "type": "Name",
                        "matched_string": m.group(0)
                    }

                    if item not in found_pii:
                        found_pii.append(item)

            return found_pii

        except Exception as e:
            raise Exception(f"PII scan error: {e}")

    def scan_row(self, row_data, dimensions):
        try:
            leaks = []

            for dimension in dimensions:

                value = row_data.get(dimension, "")

                detected = self.scan_value(value)

                if not detected:
                    continue

                # -------------------------------------------------
                # Combine all PII types for this value
                # -------------------------------------------------
                pii_types = []
                matched_values = []

                for item in detected:

                    if item["type"] not in pii_types:
                        pii_types.append(item["type"])

                    if item["matched_string"] not in matched_values:
                        matched_values.append(item["matched_string"])

                leaks.append({
                    "dimension": dimension,
                    "flagged_value": value,
                    "type": ", ".join(pii_types),
                    "matched_values": ", ".join(matched_values)
                })

            return leaks

        except Exception as e:
            raise Exception(f"Row scan error: {e}")