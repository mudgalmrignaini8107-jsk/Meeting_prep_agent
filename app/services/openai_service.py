# app/services/openai_service.py

import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from loguru import logger
from app.config import settings

class OpenAIService:
    def __init__(self):
        self.client = None
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY is not set. OpenAI operations will run in mock mode.")
            return
        try:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI Client: {e}")
            self.client = None

    def get_embeddings(self, text: str) -> List[float]:
        """
        Generate 1536-dimension embeddings using text-embedding-3-small.
        """
        if not self.client:
            # Return dummy vector for mocks
            return [0.0] * 1536
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI Embedding generation failed: {e}")
            return [0.0] * 1536

    def generate_brief(self, prompt_context: str) -> Dict[str, Any]:
        """
        Send contextual meeting details to gpt-4o and receive a structured briefing.
        """
        if not self.client:
            # Return template mock brief conforming to requested JSON format
            return self._get_mock_brief()

        try:
            system_message = (
                "You are an elite executive preparation assistant. Your task is to compile a highly strategic, "
                "detailed, and concise briefing dossier for an upcoming business meeting. "
                "You must return your response STRICTLY as a JSON object matching the requested schema."
            )
            
            # Request JSON output
            response = self.client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt_context}
                ],
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            return json.loads(result_text)
        except Exception as e:
            logger.error(f"OpenAI GPT-4o brief generation failed: {e}")
            return self._get_mock_brief()

    def generate_post_meeting_brief(self, transcript_text: str) -> Dict[str, Any]:
        """
        Extract summary, action items, assign owners, and write follow-up email drafts.
        """
        if not self.client:
            return self._get_mock_post_brief()

        try:
            system_message = (
                "You are an expert executive meeting scribe. Analyze the provided transcript. "
                "Generate a summary, action items with owners and next steps, and a follow-up email draft. "
                "Respond STRICTLY with a JSON object containing keys: 'summary', 'action_items', and 'email_draft'."
            )
            
            user_prompt = f"Transcript:\n{transcript_text}\n\nExtract and return the structured analysis."
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI transcript processing failed: {e}")
            return self._get_mock_post_brief()

    def _get_mock_brief(self) -> Dict[str, Any]:
        return {
            "meeting_summary": "Sync alignment meeting discussing MVP milestones and system integrations.",
            "attendees": [
                {"name": "Sarah Chen", "email": "sarah@startup.io", "role": "Lead Architect"},
                {"name": "Marcus Vance", "email": "marcus@venturecapital.com", "role": "Managing Partner"}
            ],
            "company_overview": "Startup.io is a SaaS infrastructure company providing real-time data streaming layers.",
            "recent_context": [
                "Completed Series A round ($12M) led by Venture Capital in April 2026.",
                "Friction on API rate limiting discovered during internal dogfooding phase."
            ],
            "talking_points": [
                "Clarify the timeline of the Gmail integration component.",
                "Confirm budget allocation for Pinecone serverless indexing costs."
            ],
            "questions_to_ask": [
                "What is the target load test threshold for the FastAPI endpoints?",
                "Do we require GDPR data residency configs in the EU for the briefs?"
            ],
            "risks": [
                "Google Calendar scopes require full audit, potentially delaying production approval."
            ],
            "opportunities": [
                "Upsell corporate licensing to Venture Capital partners."
            ],
            "recommended_actions": [
                "Share the updated security schema with Marcus ahead of the meeting."
            ],
            "confidence_score": 0.85
        }

    def _get_mock_post_brief(self) -> Dict[str, Any]:
        return {
            "summary": "The team aligned on the database schema and Google OAuth integration endpoints.",
            "action_items": [
                {
                    "description": "Implement password hashing and JWT encoding layers.",
                    "owner_name": "Sarah Chen",
                    "owner_email": "sarah@startup.io"
                },
                {
                    "description": "Provide Google client credentials for test environment.",
                    "owner_name": "Marcus Vance",
                    "owner_email": "marcus@venturecapital.com"
                }
            ],
            "email_draft": "Hi everyone,\n\nThanks for the productive sync today. Here's a summary of the next steps...\n\nBest,\nAI Agent"
        }

# Export singleton instance
openai_service = OpenAIService()
