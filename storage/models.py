from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from storage.database import Base
from models.schemas import NicheType, PriorityTier

class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    niche = Column(String)  # Stored as string from NicheType Enum
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    facebook_url = Column(String, nullable=True)
    twitter_url = Column(String, nullable=True)
    instagram_url = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    gmaps_rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)
    
    status = Column(String, default="DISCOVERED") # DISCOVERED, AUDITED, SCORED, PITCHED, SENT, REPLIED, CALL_BOOKED, WON, LOST
    
    last_contacted_at = Column(DateTime, nullable=True)
    follow_up_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    audit = relationship("AuditResult", back_populates="lead", uselist=False)
    pitch = relationship("PitchRecord", back_populates="lead", uselist=False)

class AuditResult(Base):
    __tablename__ = "audit_results"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    
    # Technical
    has_ssl = Column(Boolean, default=False)
    load_time_seconds = Column(Float, default=0.0)
    is_mobile_responsive = Column(Boolean, default=False)
    
    # Scores
    final_revamp_score = Column(Float, default=0.0)
    priority_tier = Column(String) # Stored as string from PriorityTier Enum
    ai_reasoning = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    lead = relationship("Lead", back_populates="audit")

class PitchRecord(Base):
    __tablename__ = "pitch_records"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    
    subject_line = Column(String)
    body_text = Column(String)
    target_email = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    lead = relationship("Lead", back_populates="pitch")
