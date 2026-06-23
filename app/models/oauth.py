# app/models/oauth.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class OAuthConnection(Base):
    __tablename__ = "oauth_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String, default="google", nullable=False)
    
    # Store tokens encrypted as strings
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    
    token_uri = Column(String, nullable=False)
    scopes = Column(String, nullable=False)  # Comma separated list
    expires_at = Column(DateTime, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="oauth_connections")
