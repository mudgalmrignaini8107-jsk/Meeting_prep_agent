# app/api/briefs.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.deps import get_current_user_context
from app.models.meeting import Meeting
from app.models.brief import MeetingBrief
from app.schemas.brief import BriefRead

router = APIRouter(prefix="/briefs", tags=["Briefs"])

@router.get("/{id}", response_model=BriefRead)
async def get_brief(
    id: int, # Meeting ID
    current_context: tuple = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    """
    Get the prepared briefing dossier for a meeting ID.
    """
    user, workspace_id = current_context
    
    # Verify meeting belongs to user's workspace
    meeting = db.query(Meeting).filter(
        Meeting.id == id,
        Meeting.workspace_id == workspace_id
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found in this workspace."
        )
        
    brief = db.query(MeetingBrief).filter(MeetingBrief.meeting_id == id).first()
    if not brief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No preparation brief exists for this meeting yet. Please call /meetings/{id}/prepare first."
        )
        
    return brief.brief_json
