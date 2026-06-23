# app/schemas/brief.py

from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class BriefAttendee(BaseModel):
    name: str
    email: str
    role: Optional[str] = None
    interest: Optional[str] = None

class BriefRead(BaseModel):
    meeting_summary: str
    attendees: List[BriefAttendee] = []
    company_overview: str
    recent_context: List[str] = []
    talking_points: List[str] = []
    questions_to_ask: List[str] = []
    risks: List[str] = []
    opportunities: List[str] = []
    recommended_actions: List[str] = []
    confidence_score: float
