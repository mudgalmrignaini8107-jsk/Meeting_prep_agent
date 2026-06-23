# app/models/meeting.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    google_event_id = Column(String, nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    organizer_email = Column(String, nullable=False)
    
    # Status: pending, preparing, prepared, failed
    status = Column(String, default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="meetings")
    attendees = relationship("MeetingAttendee", back_populates="meeting", cascade="all, delete-orphan")
    briefs = relationship("MeetingBrief", back_populates="meeting", cascade="all, delete-orphan")
    transcripts = relationship("MeetingTranscript", back_populates="meeting", cascade="all, delete-orphan")


class MeetingAttendee(Base):
    __tablename__ = "meeting_attendees"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String, nullable=True)
    email = Column(String, index=True, nullable=False)
    domain = Column(String, nullable=True)
    is_external = Column(Boolean, default=True, nullable=False)

    # Relationships
    meeting = relationship("Meeting", back_populates="attendees")
