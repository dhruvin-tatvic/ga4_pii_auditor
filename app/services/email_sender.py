import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from app.utils.auth import get_oauth_creds
from app.config import SENDER_EMAIL, SENDER_NAME

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
