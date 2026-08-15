import asyncio
from storage.database import AsyncSessionLocal
from storage.models import Lead, AuditResult, PitchRecord
from sqlalchemy import select
from core.pitcher import PitchGenerator
from models.schemas import LeadRecord

async def force_generate():
    pitcher = PitchGenerator()
    async with AsyncSessionLocal() as session:
        stmt = select(Lead, AuditResult).join(AuditResult).where(AuditResult.final_revamp_score >= 50.0)
        result = await session.execute(stmt)
        rows = result.all()
        
        for db_lead, audit in rows:
            print(f"Generating for {db_lead.name} (Score: {audit.final_revamp_score})...")
            # Create schema LeadRecord
            lead = LeadRecord(
                name=db_lead.name,
                niche=db_lead.niche,
                website_url=db_lead.website_url,
                city=db_lead.city,
                phone=db_lead.phone,
                email=db_lead.email
            )
            
            # defects
            defects = [audit.ai_reasoning] if audit.ai_reasoning else ["Low score detected on mobile"]
            
            pitch = await pitcher.generate(lead, defects)
            print("Generated:", pitch.subject_line)
            
            # Save
            new_pitch = PitchRecord(
                lead_id=db_lead.id,
                subject_line=pitch.subject_line,
                body_text=pitch.body_text
            )
            session.add(new_pitch)
            db_lead.status = "PITCH READY"
            
        await session.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(force_generate())
