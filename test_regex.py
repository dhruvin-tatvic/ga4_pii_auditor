import re

email_regex = r'[a-zA-Z0-9_.+-]+(?:@|%40)[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
phone_regex = r'\b(?:(?:\+|%2B)(?:1|91)[-.\s%20])?\(?[2-9]\d{2}\)?[-.\s%20]+[2-9]\d{2}[-.\s%20]+\d{4}\b|\b(?:\+|%2B)(?:1|91)[-.\s%20][2-9]\d{9}\b'
name_regex = r'(?:\b||-)(?:first_?name|last_?name|fname|lname|name)=([^&#\s]+)'

try:
    re.compile(email_regex)
    re.compile(phone_regex)
    re.compile(name_regex)
    print("Regexes compiled successfully in Python.")
except Exception as e:
    print(f"Error compiling regex: {e}")
