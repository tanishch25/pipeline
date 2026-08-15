from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from storage.models import Lead, AuditResult, PitchRecord
from models.schemas import LeadRecord, ScoringResult, PitchPayload

class AnalyticsTracker:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def add_lead(self, lead_data: LeadRecord) -> Lead:
        db_lead = Lead(
            name=lead_data.name,
            niche=lead_data.niche.value,
            city=lead_data.city,
            country=lead_data.country,
            phone=lead_data.phone,
            email=lead_data.email,
            website_url=lead_data.website_url
        )
        self.session.add(db_lead)
        await self.session.commit()
        await self.session.refresh(db_lead)
        return db_lead
        
    async def update_status(self, lead_id: int, status: str):
        lead = await self.session.get(Lead, lead_id)
        if lead:
            lead.status = status
            await self.session.commit()
            
    async def save_audit(self, lead_id: int, score_data: ScoringResult, has_ssl: bool, load_time: float, is_mobile: bool):
        audit = AuditResult(
            lead_id=lead_id,
            has_ssl=has_ssl,
            load_time_seconds=load_time,
            is_mobile_responsive=is_mobile,
            final_revamp_score=score_data.final_revamp_score,
            priority_tier=score_data.priority_tier.value,
            ai_reasoning=score_data.ai_reasoning
        )
        self.session.add(audit)
        await self.session.commit()
        
    async def save_pitch(self, lead_id: int, pitch: PitchPayload):
        db_pitch = PitchRecord(
            lead_id=lead_id,
            subject_line=pitch.subject_line,
            body_text=pitch.body_text
        )
        self.session.add(db_pitch)
        await self.session.commit()

    async def get_funnel_stats(self):
        # Discovered
        discovered = await self.session.scalar(select(func.count(Lead.id)))
        
        # Scored (High Priority)
        high_priority = await self.session.scalar(
            select(func.count(AuditResult.id)).where(AuditResult.priority_tier == "HIGH")
        )
        
        # Pitched
        pitched = await self.session.scalar(select(func.count(PitchRecord.id)))
        
        return {
            "Total Discovered": discovered or 0,
            "High Priority Leads": high_priority or 0,
            "Pitches Generated": pitched or 0
        }
