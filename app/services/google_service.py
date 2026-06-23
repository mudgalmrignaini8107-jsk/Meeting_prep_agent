# app/services/google_service.py

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from loguru import logger

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from app.models.oauth import OAuthConnection
from app.core.security import decrypt_token, encrypt_token
from app.config import settings

def get_google_credentials(db: Session, user_id: int) -> Optional[Credentials]:
    """
    Retrieve and return valid Google credentials for the user.
    If the credentials are expired, refreshes them and saves the new access token.
    """
    oauth_conn = db.query(OAuthConnection).filter(
        OAuthConnection.user_id == user_id,
        OAuthConnection.provider == "google"
    ).first()
    
    if not oauth_conn:
        logger.warning(f"No Google OAuth connection found for user ID: {user_id}")
        return None
        
    try:
        # Decrypt tokens
        access_token = decrypt_token(oauth_conn.access_token)
        refresh_token = decrypt_token(oauth_conn.refresh_token) if oauth_conn.refresh_token else None
        
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=oauth_conn.token_uri,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=oauth_conn.scopes.split(",")
        )
        
        # Check if expired and refresh if necessary
        # We manually refresh if within 5 minutes of expiration, or Google SDK expired property is true
        if not creds.valid or (oauth_conn.expires_at and oauth_conn.expires_at - datetime.utcnow() < timedelta(minutes=5)):
            if refresh_token:
                logger.info(f"Refreshing Google access token for user ID: {user_id}")
                creds.refresh(Request())
                
                # Encrypt and save the new access token
                oauth_conn.access_token = encrypt_token(creds.token)
                if creds.expiry:
                    oauth_conn.expires_at = creds.expiry
                else:
                    oauth_conn.expires_at = datetime.utcnow() + timedelta(hours=1)
                db.commit()
            else:
                logger.warning(f"Google access token for user {user_id} is expired and no refresh token exists.")
                return None
                
        return creds
    except Exception as e:
        logger.error(f"Error restoring Google credentials: {e}")
        return None

async def get_calendar_events(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """
    Sync calendar events from user's primary Google Calendar.
    If no oauth connection is present, returns mock calendar data.
    """
    creds = get_google_credentials(db, user_id)
    if not creds:
        logger.info(f"Serving mock calendar events for user {user_id}")
        return _get_mock_calendar_events()

    try:
        service = build("calendar", "v3", credentials=creds)
        # Fetch events from today onwards
        time_min = datetime.utcnow().isoformat() + "Z"
        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            maxResults=15,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        return events_result.get("items", [])
    except Exception as e:
        logger.error(f"Google Calendar API error: {e}. Falling back to mock calendar.")
        return _get_mock_calendar_events()

async def get_gmail_threads(db: Session, user_id: int, query: str) -> List[Dict[str, Any]]:
    """
    Search and retrieve Gmail threads corresponding to a query.
    If no oauth connection is present, returns mock thread data.
    """
    creds = get_google_credentials(db, user_id)
    if not creds:
        logger.info(f"Serving mock Gmail threads for user {user_id}")
        return _get_mock_gmail_threads()

    try:
        service = build("gmail", "v1", credentials=creds)
        # Call the Gmail API
        results = service.users().threads().list(userId="me", q=query, maxResults=5).execute()
        threads = results.get("threads", [])
        
        thread_details = []
        for t in threads:
            t_detail = service.users().threads().get(userId="me", id=t["id"]).execute()
            messages = t_detail.get("messages", [])
            
            # Extract content from the first and last message
            convo = []
            for msg in messages:
                payload = msg.get("payload", {})
                headers = payload.get("headers", [])
                subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "No Subject")
                sender = next((h["value"] for h in headers if h["name"].lower() == "from"), "Unknown Sender")
                snippet = msg.get("snippet", "")
                
                convo.append({
                    "id": msg["id"],
                    "sender": sender,
                    "subject": subject,
                    "snippet": snippet
                })
                
            thread_details.append({
                "thread_id": t["id"],
                "history_id": t_detail.get("historyId"),
                "messages": convo
            })
            
        return thread_details
    except Exception as e:
        logger.error(f"Gmail API error: {e}. Falling back to mock threads.")
        return _get_mock_gmail_threads()

def _get_mock_calendar_events() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    return [
        {
            "id": "mock_event_1",
            "summary": "Project AURA Architecture Sync",
            "description": "Weekly review of FastAPI database models, oauth connection table locks, and RAG schemas.",
            "start": {"dateTime": (now + timedelta(hours=1)).isoformat() + "Z"},
            "end": {"dateTime": (now + timedelta(hours=2)).isoformat() + "Z"},
            "organizer": {"email": "sarah@startup.io"},
            "attendees": [
                {"email": "sarah@startup.io", "displayName": "Sarah Chen"},
                {"email": "marcus@venturecapital.com", "displayName": "Marcus Vance"}
            ],
            "htmlLink": "https://calendar.google.com/event?id=mock_event_1"
        },
        {
            "id": "mock_event_2",
            "summary": "AI Agent Integration Alignment",
            "description": "Discuss Pinecone indexes and LangGraph state persistence timelines.",
            "start": {"dateTime": (now + timedelta(hours=4)).isoformat() + "Z"},
            "end": {"dateTime": (now + timedelta(hours=5)).isoformat() + "Z"},
            "organizer": {"email": "johndoe@gmail.com"},
            "attendees": [
                {"email": "johndoe@gmail.com", "displayName": "John Doe"},
                {"email": "sarah@startup.io", "displayName": "Sarah Chen"}
            ],
            "htmlLink": "https://calendar.google.com/event?id=mock_event_2"
        },
        {
            "id": "mock_event_3",
            "summary": "Series A Funding Review",
            "description": "Post-closing reviews and milestone audits.",
            "start": {"dateTime": (now + timedelta(days=1)).isoformat() + "Z"},
            "end": {"dateTime": (now + timedelta(days=1, hours=1)).isoformat() + "Z"},
            "organizer": {"email": "marcus@venturecapital.com"},
            "attendees": [
                {"email": "marcus@venturecapital.com", "displayName": "Marcus Vance"},
                {"email": "partner@venturecapital.com", "displayName": "Venture VC"}
            ],
            "htmlLink": "https://calendar.google.com/event?id=mock_event_3"
        }
    ]

def _get_mock_gmail_threads() -> List[Dict[str, Any]]:
    return [
        {
            "thread_id": "thread_gmail_101",
            "messages": [
                {
                    "id": "msg_001",
                    "sender": "Marcus Vance <marcus@venturecapital.com>",
                    "subject": "Re: AURA Architectural Layout",
                    "snippet": "We need to ensure that database credential stores are symmetric Fernet, and GDPR residency is accounted for."
                },
                {
                    "id": "msg_002",
                    "sender": "Sarah Chen <sarah@startup.io>",
                    "subject": "Re: AURA Architectural Layout",
                    "snippet": "Agreed. Adding workspaces isolation guarantees database locks do not leak across users."
                }
            ]
        },
        {
            "thread_id": "thread_gmail_102",
            "messages": [
                {
                    "id": "msg_003",
                    "sender": "Marcus Vance <marcus@venturecapital.com>",
                    "subject": "Pinecone Index Limits",
                    "snippet": "Sarah, please review if the free-tier Pinecone Index supports serverless AWS structures for metadata queries."
                }
            ]
        }
    ]
