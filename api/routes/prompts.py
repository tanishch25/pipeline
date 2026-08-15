from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from litellm import acompletion
from storage.database import AsyncSessionLocal
from storage.models import Lead, AuditResult
from sqlalchemy import select
from config.settings import settings
import json

router = APIRouter()

class PromptTestRequest(BaseModel):
    lead_id: int
    system_prompt: str
    user_template: str
    temperature: float = 0.7

@router.get("/config")
async def get_prompts_config():
    import os
    prompts_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "prompts.json")
    if os.path.exists(prompts_path):
        with open(prompts_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

@router.post("/config")
async def save_prompts_config(config: dict):
    import os
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config")
    os.makedirs(config_dir, exist_ok=True)
    prompts_path = os.path.join(config_dir, "prompts.json")
    with open(prompts_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    return {"status": "success"}

@router.post("/test-pitch")
async def test_pitch(req: PromptTestRequest):
    async with AsyncSessionLocal() as session:
        stmt = select(Lead, AuditResult).outerjoin(AuditResult).where(Lead.id == req.lead_id)
        result = await session.execute(stmt)
        row = result.first()
        
        if not row:
            raise HTTPException(status_code=404, detail="Lead not found")
            
        lead, audit = row
        
        flaws = []
        if audit:
            if not audit.has_ssl: flaws.append("Missing SSL certificate")
            if not audit.is_mobile_responsive: flaws.append("Not mobile responsive")
            if audit.load_time_seconds > 4: flaws.append(f"Slow load time ({audit.load_time_seconds}s)")
        else:
            flaws = ["generic performance issues", "lack of mobile optimization"]
        
        # Inject variables into template safely
        prompt = req.user_template.replace("{company_name}", lead.name)
        prompt = prompt.replace("{niche}", lead.niche)
        prompt = prompt.replace("{flaw_1}", flaws[0] if len(flaws) > 0 else "general performance issues")
        prompt = prompt.replace("{flaw_2}", flaws[1] if len(flaws) > 1 else "design outdatedness")
        
        try:
            response = await acompletion(
                model=settings.DEFAULT_LLM_MODEL,
                messages=[
                    {"role": "system", "content": req.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=req.temperature,
                api_key=settings.GEMINI_API_KEY
            )
            pitch = response.choices[0].message.content
            word_count = len(pitch.split())
            
            # Simple tone check
            banned_words = ["synergy", "leverage", "paradigm", "innovative", "leading provider", "guarantee"]
            flags = [w for w in banned_words if w in pitch.lower()]
            
            return {
                "pitch": pitch,
                "word_count": word_count,
                "flags": flags
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

class PitchSaveRequest(BaseModel):
    lead_id: int
    subject_line: str
    body_text: str

@router.post("/save-pitch")
async def save_pitch(req: PitchSaveRequest):
    from storage.models import PitchRecord
    from sqlalchemy.dialects.sqlite import insert
    
    async with AsyncSessionLocal() as session:
        # Check if pitch already exists and update or create
        stmt = select(PitchRecord).where(PitchRecord.lead_id == req.lead_id)
        result = await session.execute(stmt)
        pitch = result.scalar_one_or_none()
        
        if pitch:
            pitch.subject_line = req.subject_line
            pitch.body_text = req.body_text
        else:
            pitch = PitchRecord(
                lead_id=req.lead_id,
                subject_line=req.subject_line,
                body_text=req.body_text
            )
            session.add(pitch)
            
        # Update lead status to pitched
        lead = await session.get(Lead, req.lead_id)
        if lead:
            lead.status = "PITCH READY"
            
        await session.commit()
        return {"status": "success", "message": "Pitch saved to CRM"}
