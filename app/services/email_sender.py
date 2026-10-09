import os
import base64
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from googleapiclient.discovery import build
from app.utils.auth import get_email_creds
from app.config import SENDER_EMAIL, SENDER_NAME

class EmailSender:
    def __init__(self):
        self.sender_email = SENDER_EMAIL
        self.sender_name = SENDER_NAME
        creds = get_email_creds()
        self.service = build('gmail', 'v1', credentials=creds)

    def _normalize_emails(self, email_val):
        """Clean and normalize comma- or semicolon-separated email strings/lists into standard RFC 2822 format."""
        if not email_val:
            return ""
        if isinstance(email_val, list):
            items = email_val
        elif isinstance(email_val, str):
            items = email_val.replace(';', ',').split(',')
        else:
            items = [str(email_val)]
        cleaned = [e.strip() for e in items if e and str(e).strip()]
        return ", ".join(cleaned)

    def send_email(self, recipient_email, cc_email, subject, html_content, attachment_path=None):
        try:
            to_recipients = self._normalize_emails(recipient_email)
            cc_recipients = self._normalize_emails(cc_email)

            if not to_recipients:
                raise ValueError("No valid recipient email address provided.")

            msg = MIMEMultipart('mixed')
            msg['Subject'] = subject
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = to_recipients
            if cc_recipients:
                msg['Cc'] = cc_recipients

            # Wrap HTML content in an alternative subpart
            body_container = MIMEMultipart('alternative')
            body_part = MIMEText(html_content, 'html', 'utf-8')
            body_container.attach(body_part)
            msg.attach(body_container)
            
            if attachment_path and os.path.exists(attachment_path):
                filename = os.path.basename(attachment_path)
                content_type, _ = mimetypes.guess_type(attachment_path)
                if not content_type:
                    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                
                maintype, subtype = content_type.split('/', 1)
                mime_base = MIMEBase(maintype, subtype)
                with open(attachment_path, "rb") as attachment:
                    mime_base.set_payload(attachment.read())
                
                encoders.encode_base64(mime_base)
                mime_base.add_header('Content-Disposition', 'attachment', filename=filename)
                mime_base.add_header('Content-Type', f'{content_type}; name="{filename}"')
                msg.attach(mime_base)
            
            encoded_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            
            create_message = {
                'raw': encoded_message
            }
            
            message = (self.service.users().messages().send(userId="me", body=create_message).execute())
            cc_log = f" (CC: {cc_recipients})" if cc_recipients else ""
            print(f"Email sent successfully to {to_recipients}{cc_log}. Message ID: {message['id']}")
            return True
        except Exception as e:
            print(f"Failed to send email to {to_recipients}: {e}")
            raise Exception(f"Email sending failed: {e}")
