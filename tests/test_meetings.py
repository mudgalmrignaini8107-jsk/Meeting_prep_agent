# tests/test_meetings.py

from datetime import datetime, timedelta

def test_dashboard_and_calendar_sync(client, test_user):
    """
    Test GET /dashboard. Verifies calendar event sync processes new records in PostgreSQL
    and returns correct workspace summary counts.
    """
    response = client.get("/dashboard")
    assert response.status_code == 200
    
    data = response.json()
    assert "todays_meetings" in data
    assert "upcoming_meetings" in data
    assert "prepared_briefs" in data
    assert "meeting_history_count" in data
    
    # Check that events from mock sync are now populated in DB
    assert data["meeting_history_count"] > 0
    assert len(data["todays_meetings"]) > 0

def test_get_meetings_list(client, test_user):
    """
    Test GET /meetings retrieves the synced calendar meetings.
    """
    # Trigger calendar sync first by calling dashboard
    client.get("/dashboard")
    
    response = client.get("/meetings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "title" in data[0]
    assert "status" in data[0]

def test_prepare_meeting_mock(client, test_user, db_session):
    """
    Test POST /meetings/{id}/prepare. Verifies that the LangGraph workflow triggers
    and generates the structured brief.
    """
    # Sync first
    client.get("/dashboard")
    meetings_resp = client.get("/meetings")
    meeting_id = meetings_resp.json()[0]["id"]
    
    # Prepare
    prep_resp = client.post(f"/meetings/{meeting_id}/prepare")
    assert prep_resp.status_code == 200
    
    brief_data = prep_resp.json()
    assert "meeting_summary" in brief_data
    assert "talking_points" in brief_data
    assert "confidence_score" in brief_data
    assert brief_data["confidence_score"] > 0.0

def test_copilot_start(client, test_user):
    """
    Test POST /copilot/start returns low-latency meeting context.
    """
    client.get("/dashboard")
    meetings_resp = client.get("/meetings")
    meeting_id = meetings_resp.json()[0]["id"]
    
    payload = {"meeting_id": meeting_id}
    response = client.post("/copilot/start", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "talking_points" in data
    assert "questions_to_ask" in data
    assert "quick_context" in data
    assert "live_notes_placeholder" in data

def test_transcript_upload(client, test_user):
    """
    Test POST /transcripts/upload processes transcript, generates summary/actions, and stores them.
    """
    client.get("/dashboard")
    meetings_resp = client.get("/meetings")
    meeting_id = meetings_resp.json()[0]["id"]
    
    payload = {
        "meeting_id": meeting_id,
        "raw_text": "Marcus Vance: We must ensure database isolation locks are Fernet-encrypted. Sarah Chen: Yes, and we will configure Redis to cache meetings."
    }
    response = client.post("/transcripts/upload", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "summary" in data
    assert "email_draft" in data
    assert "action_items" in data
    assert len(data["action_items"]) > 0
    assert "description" in data["action_items"][0]
