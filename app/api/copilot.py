# app/api/copilot.py

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user_context
from app.models.meeting import Meeting
from app.models.brief import MeetingBrief

router = APIRouter(prefix="/copilot", tags=["Copilot"])

class CopilotStartPayload(BaseModel):
    meeting_id: int

class CopilotAttendeeInfo(BaseModel):
    name: str
    email: str
    role: str = ""

class CopilotResponse(BaseModel):
    talking_points: List[str]
    attendee_information: List[CopilotAttendeeInfo]
    questions_to_ask: List[str]
    quick_context: str
    live_notes_placeholder: str

@router.post("/start", response_model=CopilotResponse)
async def start_copilot(
    payload: CopilotStartPayload,
    current_context: tuple = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    """
    Initialize Copilot Mode for a live meeting.
    Retrieves critical information optimized for low-latency dashboard overlay rendering.
    """
    user, workspace_id = current_context
    
    # 1. Fetch meeting
    meeting = db.query(Meeting).filter(
        Meeting.id == payload.meeting_id,
        Meeting.workspace_id == workspace_id
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found in this workspace."
        )

    # 2. Retrieve brief if prepared
    brief = db.query(MeetingBrief).filter(MeetingBrief.meeting_id == payload.meeting_id).first()
    
    if brief:
        brief_data = brief.brief_json
        talking_points = brief_data.get("talking_points", [])
        questions_to_ask = brief_data.get("questions_to_ask", [])
        
        # Parse attendees
        attendee_info = []
        for att in brief_data.get("attendees", []):
            attendee_info.append(CopilotAttendeeInfo(
                name=att.get("name", ""),
                email=att.get("email", ""),
                role=att.get("role", "Attendee")
            ))
            
        quick_context = f"{brief_data.get('company_overview', '')} Context summary: {brief_data.get('meeting_summary', '')}"
    else:
        # Fallback if meeting is not prepared yet, return basic details instantly
        talking_points = [f"Initial alignment on: {meeting.title}"]
        questions_to_ask = ["What are the primary targets of today's sync?"]
        
        # Get basic attendees from calendar sync
        attendee_info = []
        for att in meeting.attendees:
            attendee_info.append(CopilotAttendeeInfo(
                name=att.name or "",
                email=att.email,
                role="External Attendee" if att.is_external else "Internal Member"
            ))
            
        quick_context = f"Meeting title: {meeting.title}. Description: {meeting.description or 'No description synced.'}"

    return CopilotResponse(
        talking_points=talking_points,
        attendee_information=attendee_info,
        questions_to_ask=questions_to_ask,
        quick_context=quick_context[:300], # Keep it brief and low-latency
        live_notes_placeholder="Type notes here... AI will automatically generate post-meeting briefs on completion."
    )
