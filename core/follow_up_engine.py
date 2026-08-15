from datetime import datetime, timedelta
from sqlalchemy import select
from storage.database import AsyncSessionLocal
from storage.models import Lead, PitchRecord
from core.mailer import Mailer
from litellm import acompletion
from config.settings import settings

class FollowUpEngine:
    def __init__(self, engine: str = "hybrid"):
        self.mailer = Mailer()
        self.engine = engine
        if engine == "local" or engine == "hybrid":
            self.model = "ollama/llama3.1"
        else:
            self.model = "groq/llama-3.1-8b-instant"

    async def run_daily_followups(self):
        print("[FOLLOW-UP] Starting daily follow-up job...")
        async with AsyncSessionLocal() as session:
            # 1. First Follow-up (3 days after initial send)
            three_days_ago = datetime.utcnow() - timedelta(days=3)
            stmt1 = select(Lead, PitchRecord).join(PitchRecord).where(
                Lead.status == "SENT",
                Lead.follow_up_count == 0,
                Lead.last_contacted_at <= three_days_ago
            )
            result1 = await session.execute(stmt1)
            leads_for_fu1 = result1.all()

            # 2. Second Follow-up (7 days after initial send / 4 days after FU1)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            stmt2 = select(Lead, PitchRecord).join(PitchRecord).where(
                Lead.status == "SENT",
                Lead.follow_up_count == 1,
                Lead.last_contacted_at <= seven_days_ago
            )
            result2 = await session.execute(stmt2)
            leads_for_fu2 = result2.all()

            # Process FU1
            for lead, pitch in leads_for_fu1:
                await self._process_followup(session, lead, pitch, follow_up_num=1)

            # Process FU2
            for lead, pitch in leads_for_fu2:
                await self._process_followup(session, lead, pitch, follow_up_num=2)

        print("[FOLLOW-UP] Daily job completed.")

    async def _process_followup(self, session, lead: Lead, original_pitch: PitchRecord, follow_up_num: int):
        if not lead.email:
            return

        prompt = f"""
You are following up with a prospect, {lead.name}, who you emailed {3 if follow_up_num == 1 else 7} days ago.
Your previous email subject was: "{original_pitch.subject_line}".

Task: Write a short, punchy Follow-up #{follow_up_num} email.
Rule 1: Focus purely on showing value. Mention our portfolio: https://tanishch25.github.io/porfolio-/
Rule 2: Maximum 3 sentences.
Rule 3: Keep it extremely casual and professional.
Rule 4: Do not be pushy or mention that they didn't reply.

Return ONLY a valid JSON object in this exact format:
{{
    "subject_line": "Re: {original_pitch.subject_line}",
    "body_text": "The 3 sentence body"
}}
"""
        try:
            resp = await acompletion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_retries=settings.LITELLM_MAX_RETRIES,
                temperature=0.7
            )
            
            content = resp.choices[0].message.content
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                content = content[start:end+1]
                
            import json
            fu_data = json.loads(content)
            
            # Send Email
            success = self.mailer.send_email(
                to_email=lead.email,
                subject=fu_data.get("subject_line", f"Re: {original_pitch.subject_line}"),
                body=fu_data.get("body_text", "")
            )
            
            if success:
                lead.follow_up_count = follow_up_num
                lead.last_contacted_at = datetime.utcnow()
                await session.commit()
                print(f"[FOLLOW-UP] Sent FU#{follow_up_num} to {lead.email}")
            else:
                print(f"[FOLLOW-UP ERROR] Failed to send FU#{follow_up_num} to {lead.email}")

        except Exception as e:
            print(f"[FOLLOW-UP ERROR] LLM or parsing failed for {lead.email}: {e}")
