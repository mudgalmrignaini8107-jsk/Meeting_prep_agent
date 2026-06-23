# app/api/dashboard.py

from datetime import datetime, date, time
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from loguru import logger

from app.database import get_db
from app.api.deps import get_current_user_context
from app.models.user import User, Workspace
from app.models.meeting import Meeting, MeetingAttendee
from app.models.brief import MeetingBrief
from app.models.oauth import OAuthConnection
from app.schemas.meeting import DashboardRead, MeetingRead, BriefSummaryRead, IntegrationRead
from app.services.google_service import get_calendar_events

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("", response_model=DashboardRead)
async def get_dashboard_data(
    current_context: tuple = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    """
    Retrieves aggregated dashboard data: today's meetings, upcoming meetings,
    recently prepared briefs, connected OAuth integrations, and meeting history.
    Triggers calendar sync in the background for live accounts.
    """
    user, workspace_id = current_context
    logger.info(f"Retrieving dashboard for user {user.email} in workspace {workspace_id}")

    # 1. Sync Calendar Events from Google in real-time (and save new events to DB)
    try:
        events = await get_calendar_events(db, user_id=user.id)
        for event in events:
            # Check if event is already synced
            existing = db.query(Meeting).filter(
                Meeting.google_event_id == event.get("id"),
                Meeting.workspace_id == workspace_id
            ).first()
            
            if not existing:
                # Parse start/end times
                start_str = event["start"].get("dateTime") or event["start"].get("date")
                end_str = event["end"].get("dateTime") or event["end"].get("date")
                
                # Format to python datetime
                start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                end_time = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                
                # Create Meeting
                new_meeting = Meeting(
                    google_event_id=event.get("id"),
                    workspace_id=workspace_id,
                    title=event.get("summary", "Untitled Meeting"),
                    description=event.get("description", ""),
                    start_time=start_time.replace(tzinfo=None),
                    end_time=end_time.replace(tzinfo=None),
                    organizer_email=event.get("organizer", {}).get("email", user.email),
                    status="pending"
                )
                db.add(new_meeting)
                db.commit()
                db.refresh(new_meeting)
                
                # Save Attendees
                for att in event.get("attendees", []):
                    email = att.get("email")
                    if not email:
                        continue
                    
                    is_external = not email.endswith(user.email.split("@")[-1])
                    new_att = MeetingAttendee(
                        meeting_id=new_meeting.id,
                        name=att.get("displayName", ""),
                        email=email,
                        domain=email.split("@")[-1],
                        is_external=is_external
                    )
                    db.add(new_att)
                db.commit()
    except Exception as e:
        logger.error(f"Error syncing calendar events during dashboard retrieve: {e}")

    # 2. Query today's meetings from DB
    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)
    
    todays_db_meetings = db.query(Meeting).filter(
        Meeting.workspace_id == workspace_id,
        Meeting.start_time >= today_start,
        Meeting.start_time <= today_end
    ).order_by(Meeting.start_time.asc()).all()

    # 3. Query upcoming meetings (starting after today)
    upcoming_db_meetings = db.query(Meeting).filter(
        Meeting.workspace_id == workspace_id,
        Meeting.start_time > today_end
    ).order_by(Meeting.start_time.asc()).limit(10).all()

    # 4. Query prepared briefs summaries
    prepared_briefs = []
    briefs = db.query(MeetingBrief).join(Meeting).filter(
        Meeting.workspace_id == workspace_id
    ).order_by(MeetingBrief.created_at.desc()).limit(5).all()
    
    for b in briefs:
        prepared_briefs.append(BriefSummaryRead(
            meeting_id=b.meeting_id,
            title=b.meeting.title,
            confidence_score=b.confidence_score,
            created_at=b.created_at
        ))

    # 5. Connected Integrations (OAuth)
    integrations = []
    conns = db.query(OAuthConnection).filter(OAuthConnection.user_id == user.id).all()
    for c in conns:
        integrations.append(IntegrationRead(
            provider=c.provider,
            connected_at=c.created_at,
            scopes=c.scopes.split(",")
        ))

    # 6. Meeting history count (all meetings)
    history_count = db.query(Meeting).filter(
        Meeting.workspace_id == workspace_id
    ).count()

    return DashboardRead(
        todays_meetings=[MeetingRead.from_orm(m) for m in todays_db_meetings],
        upcoming_meetings=[MeetingRead.from_orm(m) for m in upcoming_db_meetings],
        prepared_briefs=prepared_briefs,
        connected_integrations=integrations,
        meeting_history_count=history_count
    )
