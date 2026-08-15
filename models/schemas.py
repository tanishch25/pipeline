from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field
from enum import Enum

class NicheType(str, Enum):
    GYM = "gym"
    RESTAURANT = "restaurant"
    UTILITY = "utility"
    OTHER = "other"

class PriorityTier(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    DISQUALIFIED = "DISQUALIFIED"

class LeadRecord(BaseModel):
    name: str
    niche: NicheType
    city: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    facebook_url: Optional[str] = None
    twitter_url: Optional[str] = None
    instagram_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None
    gmaps_rating: Optional[float] = None
    review_count: Optional[int] = None

class TechnicalAuditMetrics(BaseModel):
    has_ssl: bool
    load_time_seconds: float
    is_mobile_responsive: bool
    detected_tech_stack: List[str] = Field(default_factory=list)
    meta_description_present: bool
    h1_count: int
    has_broken_ctas: bool

class VectorScore(BaseModel):
    score: float = Field(..., ge=0.0, le=10.0)
    reasoning: str

class LLMAuditResult(BaseModel):
    design_modernity: VectorScore
    mobile_ux: VectorScore
    cta_clarity: VectorScore
    booking_ordering_integration: VectorScore
    page_speed_and_assets: VectorScore
    seo_and_schema: VectorScore
    social_proof_trust: VectorScore

class ScoringResult(BaseModel):
    raw_technical_score: float
    llm_deficiency_score: float
    final_revamp_score: float
    priority_tier: PriorityTier
    ai_reasoning: str = ""
    defects: List[str] = Field(default_factory=list)

class PitchPayload(BaseModel):
    subject_line: str
    body_text: str
    identified_flaws: List[str]
    compliment: str
    target_email: Optional[str] = None
