import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import settings

class Mailer:
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASS

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        if not self.user or not self.password:
            print("[WARN] SMTP credentials not set. Simulating email send.")
            print(f"To: {to_email}\nSubject: {subject}\nBody:\n{body}")
            return True

        msg = MIMEMultipart()
        msg['From'] = self.user
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to send email to {to_email}: {e}")
            return False
