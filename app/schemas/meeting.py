# app/schemas/meeting.py

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr

class MeetingAttendeeRead(BaseModel):
    name: Optional[str]
    email: EmailStr
    domain: Optional[str]
    is_external: bool

    class Config:
        from_attributes = True


class MeetingRead(BaseModel):
    id: int
    google_event_id: Optional[str]
    workspace_id: int
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    organizer_email: str
    status: str
    created_at: datetime
    attendees: List[MeetingAttendeeRead] = []

    class Config:
        from_attributes = True


class BriefSummaryRead(BaseModel):
    meeting_id: int
    title: str
    confidence_score: float
    created_at: datetime


class IntegrationRead(BaseModel):
    provider: str
    connected_at: datetime
    scopes: List[str]


class DashboardRead(BaseModel):
    todays_meetings: List[MeetingRead]
    upcoming_meetings: List[MeetingRead]
    prepared_briefs: List[BriefSummaryRead]
    connected_integrations: List[IntegrationRead]
    meeting_history_count: int
