# app/api/meetings.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from loguru import logger

from app.database import get_db
from app.api.deps import get_current_user_context
from app.models.meeting import Meeting
from app.schemas.meeting import MeetingRead
from app.schemas.brief import BriefRead
from app.services.agent_service import execute_meeting_preparation

router = APIRouter(prefix="/meetings", tags=["Meetings"])

@router.get("", response_model=List[MeetingRead])
async def get_meetings(
    current_context: tuple = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    """
    Retrieve all meetings associated with the user's active workspace.
    """
    user, workspace_id = current_context
    meetings = db.query(Meeting).filter(
        Meeting.workspace_id == workspace_id
    ).order_by(Meeting.start_time.asc()).all()
    return meetings

@router.get("/{id}", response_model=MeetingRead)
async def get_meeting_details(
    id: int,
    current_context: tuple = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    """
    Get full details for a specific meeting in the user's active workspace.
    """
    user, workspace_id = current_context
    meeting = db.query(Meeting).filter(
        Meeting.id == id,
        Meeting.workspace_id == workspace_id
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting ID {id} not found in this workspace."
        )
    return meeting

@router.post("/{id}/prepare", response_model=BriefRead)
async def prepare_meeting(
    id: int,
    current_context: tuple = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    """
    Triggers the LangGraph agent preparation workflow. Compiles Calendar, Gmail, and Web News contexts,
    updates index configurations, generates the briefing via GPT-4o, and returns the briefing JSON.
    """
    user, workspace_id = current_context
    logger.info(f"User {user.email} triggered preparation for meeting ID {id}")
    
    # Verify meeting exists in this workspace
    meeting = db.query(Meeting).filter(
        Meeting.id == id,
        Meeting.workspace_id == workspace_id
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting ID {id} not found in this workspace."
        )
        
    # Execute the LangGraph workflow service
    brief_json = await execute_meeting_preparation(
        db=db,
        meeting_id=id,
        user_id=user.id,
        workspace_id=workspace_id
    )
    
    return brief_json
