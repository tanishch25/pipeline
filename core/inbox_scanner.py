import imaplib
import email
from email.header import decode_header
from sqlalchemy import select
from storage.database import AsyncSessionLocal
from storage.models import Lead
from config.settings import settings

class InboxScanner:
    def __init__(self):
        self.host = getattr(settings, 'IMAP_HOST', 'imap.gmail.com')
        self.port = getattr(settings, 'IMAP_PORT', 993)
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASS

    async def scan_for_replies(self):
        if not self.user or not self.password:
            print("[WARN] IMAP credentials not set. Cannot sync inbox.")
            return

        try:
            # Connect to IMAP
            mail = imaplib.IMAP4_SSL(self.host, self.port)
            mail.login(self.user, self.password)
            mail.select("inbox")

            # Search for all emails from the last few days
            status, messages = mail.search(None, 'ALL')
            if status != 'OK':
                print("[ERROR] Failed to search inbox.")
                return

            email_ids = messages[0].split()
            reply_emails = set()

            # For performance, only check recent emails or read headers
            # Here we just check the sender email address
            for e_id in email_ids[-50:]:  # Check last 50 emails
                res, msg_data = mail.fetch(e_id, '(RFC822.SIZE BODY[HEADER.FIELDS (FROM)])')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        from_ = msg.get("From")
                        if from_:
                            # Extract email address between < >
                            import re
                            match = re.search(r'<(.+?)>', from_)
                            sender_email = match.group(1) if match else from_
                            reply_emails.add(sender_email.lower().strip())
                            
            mail.logout()

            # Update DB
            if reply_emails:
                async with AsyncSessionLocal() as session:
                    stmt = select(Lead).where(
                        Lead.email.in_(list(reply_emails)),
                        Lead.status.in_(["SENT", "PITCH READY", "PITCHED"])
                    )
                    result = await session.execute(stmt)
                    leads = result.scalars().all()
                    
                    for lead in leads:
                        lead.status = "REPLIED"
                        print(f"[SYNC] Marked lead {lead.name} ({lead.email}) as REPLIED.")
                        
                    await session.commit()
                    
            print(f"[SYNC] Inbox sync complete. Checked last 50 emails.")

        except Exception as e:
            print(f"[ERROR] Inbox scan failed: {e}")
