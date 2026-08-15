from fastapi import APIRouter
from sqlalchemy import select, func
from storage.database import AsyncSessionLocal
from storage.models import Lead, AuditResult, PitchRecord

router = APIRouter()

@router.get("/summary")
async def get_analytics_summary():
    async with AsyncSessionLocal() as session:
        # Funnel
        discovered = await session.scalar(select(func.count(Lead.id))) or 0
        high_priority = await session.scalar(select(func.count(AuditResult.id)).where(AuditResult.priority_tier == "HIGH")) or 0
        pitched = await session.scalar(select(func.count(PitchRecord.id))) or 0
        won = await session.scalar(select(func.count(Lead.id)).where(Lead.status == "WON")) or 0
        replied = await session.scalar(select(func.count(Lead.id)).where(Lead.status == "REPLIED")) or 0
        
        # Follow-ups sent (sum of follow_up_count)
        follow_ups_sent = await session.scalar(select(func.sum(Lead.follow_up_count))) or 0
        
        # Scores
        scores_stmt = select(AuditResult.final_revamp_score)
        scores_result = await session.execute(scores_stmt)
        scores = [s[0] for s in scores_result.all()]
        
        # Niches
        niches_stmt = select(Lead.niche, func.count(Lead.id)).group_by(Lead.niche)
        niches_result = await session.execute(niches_stmt)
        niches = [{"name": row[0], "count": row[1]} for row in niches_result.all()]
        
        # Stages
        stages_stmt = select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
        stages_result = await session.execute(stages_stmt)
        stage_counts = {row[0]: row[1] for row in stages_result.all()}
        
        funnel_order = ["DISCOVERED", "AUDITED", "SCORED", "PITCH READY", "SENT", "REPLIED", "CALL_BOOKED", "WON", "LOST"]
        funnel_data = [{"stage": stage, "count": stage_counts.get(stage, 0)} for stage in funnel_order]
        
        return {
            "funnel": {
                "discovered": discovered,
                "high_priority": high_priority,
                "pitched": pitched,
                "replied": replied,
                "follow_ups_sent": follow_ups_sent,
                "won": won,
                "conversion_rate": round((won / pitched * 100) if pitched > 0 else 0, 1),
                "reply_rate": round((replied / pitched * 100) if pitched > 0 else 0, 1)
            },
            "scores": scores,
            "niches": niches,
            "stages": funnel_data
        }
