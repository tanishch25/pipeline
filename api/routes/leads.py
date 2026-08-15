from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import select, delete
from storage.database import AsyncSessionLocal
from storage.models import Lead, AuditResult, PitchRecord
from pydantic import BaseModel
import asyncio

router = APIRouter()

class StatusUpdate(BaseModel):
    status: str

class PitchUpdate(BaseModel):
    body_text: str

@router.get("")
async def get_leads(
    search: str = None,
    niche: str = None,
    status: str = None,
    min_score: float = None,
    max_score: float = None,
    has_ssl: bool = None
):
    async with AsyncSessionLocal() as session:
        stmt = select(Lead, AuditResult, PitchRecord).join(AuditResult, isouter=True).join(PitchRecord, isouter=True)
        
        if search:
            stmt = stmt.where(Lead.name.ilike(f"%{search}%") | Lead.city.ilike(f"%{search}%") | Lead.website_url.ilike(f"%{search}%"))
        if niche:
            niches = niche.split(",")
            stmt = stmt.where(Lead.niche.in_(niches))
        if status:
            statuses = status.split(",")
            stmt = stmt.where(Lead.status.in_(statuses))
        if min_score is not None:
            stmt = stmt.where(AuditResult.final_revamp_score >= min_score)
        if max_score is not None:
            stmt = stmt.where(AuditResult.final_revamp_score <= max_score)
        if has_ssl is not None:
            stmt = stmt.where(AuditResult.has_ssl == has_ssl)
            
        stmt = stmt.order_by(Lead.created_at.desc())
        result = await session.execute(stmt)
        rows = result.all()
        
        # Deduplicate
        unique = {}
        for lead, audit, pitch in rows:
            if lead.id not in unique:
                unique[lead.id] = {
                    "id": lead.id,
                    "name": lead.name,
                    "niche": lead.niche,
                    "city": lead.city,
                    "email": lead.email,
                    "facebook_url": lead.facebook_url,
                    "twitter_url": lead.twitter_url,
                    "instagram_url": lead.instagram_url,
                    "linkedin_url": lead.linkedin_url,
                    "website_url": lead.website_url,
                    "status": lead.status,
                    "audit": {
                        "final_revamp_score": audit.final_revamp_score,
                        "priority_tier": audit.priority_tier,
                        "has_ssl": audit.has_ssl,
                        "load_time_seconds": audit.load_time_seconds,
                        "is_mobile_responsive": audit.is_mobile_responsive,
                        "ai_reasoning": audit.ai_reasoning
                    } if audit else None,
                    "pitch": {
                        "subject_line": pitch.subject_line,
                        "body_text": pitch.body_text
                    } if pitch else None
                }
        return list(unique.values())

@router.patch("/{lead_id}/status")
async def update_status(lead_id: int, payload: StatusUpdate):
    async with AsyncSessionLocal() as session:
        lead = await session.get(Lead, lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        lead.status = payload.status
        await session.commit()
        return {"status": "success", "new_status": lead.status}

@router.patch("/{lead_id}/pitch")
async def update_pitch(lead_id: int, payload: PitchUpdate):
    async with AsyncSessionLocal() as session:
        stmt = select(PitchRecord).where(PitchRecord.lead_id == lead_id)
        result = await session.execute(stmt)
        pitch = result.scalar_one_or_none()
        
        if not pitch:
            raise HTTPException(status_code=404, detail="Pitch not found")
            
        pitch.body_text = payload.body_text
        await session.commit()
        return {"status": "success"}

class SendPitchRequest(BaseModel):
    to_email: str

@router.delete("/{lead_id}")
async def delete_lead(lead_id: int):
    async with AsyncSessionLocal() as session:
        lead = await session.get(Lead, lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Delete related records
        await session.execute(delete(AuditResult).where(AuditResult.lead_id == lead_id))
        await session.execute(delete(PitchRecord).where(PitchRecord.lead_id == lead_id))
        await session.execute(delete(Lead).where(Lead.id == lead_id))
        
        await session.commit()
        return {"status": "success"}

@router.post("/{lead_id}/send")
async def send_pitch(lead_id: int, payload: SendPitchRequest):
    from core.mailer import Mailer
    
    async with AsyncSessionLocal() as session:
        lead = await session.get(Lead, lead_id)
        stmt = select(PitchRecord).where(PitchRecord.lead_id == lead_id)
        result = await session.execute(stmt)
        pitch = result.scalar_one_or_none()
        
        if not lead or not pitch:
            raise HTTPException(status_code=404, detail="Lead or Pitch not found")
            
        mailer = Mailer()
        success = mailer.send_email(
            to_email=payload.to_email,
            subject=pitch.subject_line,
            body=pitch.body_text
        )
        
        if success:
            lead.status = "SENT"
            await session.commit()
            return {"status": "success", "message": "Email sent and status updated"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")

class BulkSendRequest(BaseModel):
    lead_ids: list[int]

@router.post("/bulk-send")
async def bulk_send_pitches(payload: BulkSendRequest):
    from core.mailer import Mailer
    mailer = Mailer()
    results = {"success": 0, "failed": 0, "errors": []}
    
    async with AsyncSessionLocal() as session:
        for lead_id in payload.lead_ids:
            lead = await session.get(Lead, lead_id)
            stmt = select(PitchRecord).where(PitchRecord.lead_id == lead_id)
            pitch_result = await session.execute(stmt)
            pitch = pitch_result.scalar_one_or_none()
            
            if not lead or not pitch or not lead.email:
                results["failed"] += 1
                results["errors"].append(f"Lead {lead_id} missing email or pitch.")
                continue
                
            success = mailer.send_email(
                to_email=lead.email,
                subject=pitch.subject_line,
                body=pitch.body_text
            )
            
            if success:
                lead.status = "SENT"
                results["success"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"SMTP error for lead {lead_id}.")
                
        await session.commit()
    return results

