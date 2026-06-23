# app/schemas/transcript.py

from typing import List, Optional
from pydantic import BaseModel

class TranscriptUploadPayload(BaseModel):
    meeting_id: int
    raw_text: str

class ActionItemResponse(BaseModel):
    description: str
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None

class TranscriptResponse(BaseModel):
    summary: str
    action_items: List[ActionItemResponse] = []
    email_draft: str
