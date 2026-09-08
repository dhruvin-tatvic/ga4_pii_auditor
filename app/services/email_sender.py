import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from googleapiclient.discovery import build
from app.utils.auth import get_oauth_creds
from app.config import SENDER_EMAIL, SENDER_NAME

class EmailSender:
    def __init__(self):
        self.sender_email = SENDER_EMAIL
        self.sender_name = SENDER_NAME
        creds = get_oauth_creds()
        self.service = build('gmail', 'v1', credentials=creds)

    def send_email(self, recipient_email, cc_email, subject, html_content, attachment_path=None):
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = recipient_email
            if cc_email:
                msg['Cc'] = cc_email
            part = MIMEText(html_content, 'html')
            msg.attach(part)
            
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as attachment:
                    mime_base = MIMEBase('application', 'octet-stream')
                    mime_base.set_payload(attachment.read())
                
                encoders.encode_base64(mime_base)
                filename = os.path.basename(attachment_path)
                mime_base.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{filename}"'
                )
                msg.attach(mime_base)
            
            encoded_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            
            create_message = {
                'raw': encoded_message
            }
            
            message = (self.service.users().messages().send(userId="me", body=create_message).execute())
            print(f"Email sent successfully to {recipient_email} (CC: {cc_email}). Message ID: {message['id']}")
            return True
        except Exception as e:
            print(f"Failed to send email to {recipient_email}: {e}")
            raise Exception(f"Email sending failed: {e}")
