# app/api/transcripts.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from loguru import logger

from app.database import get_db
from app.api.deps import get_current_user_context
from app.models.meeting import Meeting
from app.models.transcript import MeetingTranscript, ActionItem
from app.models.audit import AuditLog
from app.schemas.transcript import TranscriptUploadPayload, TranscriptResponse, ActionItemResponse
from app.services.openai_service import openai_service

router = APIRouter(prefix="/transcripts", tags=["Transcripts"])

@router.post("/upload", response_model=TranscriptResponse)
async def upload_transcript(
    payload: TranscriptUploadPayload,
    current_context: tuple = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    """
    Upload a raw meeting transcript.
    Processes the transcript text to generate a meeting summary, individual action items
    with owners, and a drafted follow-up email. Stores results in the SQL database.
    """
    user, workspace_id = current_context
    logger.info(f"User {user.email} uploaded transcript for meeting ID {payload.meeting_id}")
    
    # 1. Verify meeting belongs to active workspace
    meeting = db.query(Meeting).filter(
        Meeting.id == payload.meeting_id,
        Meeting.workspace_id == workspace_id
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found in this workspace."
        )

    # 2. Process transcript using GPT-4o analysis
    analysis = openai_service.generate_post_meeting_brief(payload.raw_text)
    
    summary = analysis.get("summary", "Summary not generated.")
    email_draft = analysis.get("email_draft", "Email draft not generated.")
    items_list = analysis.get("action_items", [])

    # 3. Store transcript details in database
    db_transcript = MeetingTranscript(
        meeting_id=payload.meeting_id,
        raw_text=payload.raw_text,
        processed_summary=summary
    )
    db.add(db_transcript)
    db.commit()
    db.refresh(db_transcript)

    # 4. Store Action Items in database
    response_action_items = []
    for item in items_list:
        desc = item.get("description", "")
        if not desc:
            continue
            
        owner_name = item.get("owner_name")
        owner_email = item.get("owner_email")
        
        db_action = ActionItem(
            transcript_id=db_transcript.id,
            description=desc,
            owner_name=owner_name,
            owner_email=owner_email,
            status="pending"
        )
        db.add(db_action)
        
        response_action_items.append(ActionItemResponse(
            description=desc,
            owner_name=owner_name,
            owner_email=owner_email
        ))
        
    # Log Audit Log
    audit = AuditLog(
        user_id=user.id,
        workspace_id=workspace_id,
        action="upload_transcript",
        details=f"Uploaded and processed transcript for meeting {payload.meeting_id}. Found {len(response_action_items)} action items."
    )
    db.add(audit)
    db.commit()

    return TranscriptResponse(
        summary=summary,
        action_items=response_action_items,
        email_draft=email_draft
    )
