# app/models/brief.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class MeetingBrief(Base):
    __tablename__ = "meeting_briefs"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    
    # Store complete structured brief JSON mapping the output specification
    brief_json = Column(JSON, nullable=False)
    confidence_score = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    meeting = relationship("Meeting", back_populates="briefs")


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, unique=True, index=True, nullable=False)
    company_name = Column(String, nullable=False)
    overview = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    recent_news = Column(JSON, nullable=True) # List of dictionaries [{title, url, date, source}]
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
