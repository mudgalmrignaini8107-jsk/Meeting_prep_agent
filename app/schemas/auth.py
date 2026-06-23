# app/schemas/auth.py

from typing import Optional
from pydantic import BaseModel, EmailStr

class LoginPayload(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthPayload(BaseModel):
    # Standard authorization code returned by Google OAuth callback to exchange for tokens
    code: str
    # Workspace to bind this connection or login to (optional, defaults to creating/selecting primary)
    workspace_id: Optional[int] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    workspace_id: int

class TokenData(BaseModel):
    user_id: int
    email: str
    workspace_id: int
