# app/config.py

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Core Application Settings
    APP_NAME: str = "AI Meeting Prep Agent API"
    DEBUG: bool = False
    
    # Database and Caching
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/meeting_prep"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Authentication & Encryption
    JWT_SECRET_KEY: str = "supersecretjwtkeythatshouldbeoverriddeninproductionenvironments"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    # Must be 32 base64 url-encoded bytes. Generated with cryptography.fernet.Fernet.generate_key()
    TOKEN_ENCRYPTION_KEY: str = "wT-k0X65tS9v8P-1aR6-7c_4Z9u-T1YV8Wv1bX2z3E="
    
    # Google API Credentials
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    
    # LLM Provider
    OPENAI_API_KEY: str = ""
    
    # SerpAPI (for public company news search)
    SERPAPI_API_KEY: str = ""
    
    # Pinecone Vector DB
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "meeting-prep"
    PINECONE_ENVIRONMENT: Optional[str] = None
    PINECONE_HOST: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
