# app/api/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserRead
from app.schemas.auth import LoginPayload, GoogleAuthPayload, Token
from app.services import auth_service
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Standard user registration endpoint. Creates a user and sets up their default workspace.
    """
    user, _ = await auth_service.register_user(db, payload)
    return user

@router.post("/login", response_model=Token)
async def login(payload: LoginPayload, db: Session = Depends(get_db)):
    """
    Standard username/password login endpoint. Returns a JWT session token.
    """
    user, workspace_id = await auth_service.authenticate_user(db, payload)
    
    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "workspace_id": workspace_id
    }
    access_token = create_access_token(token_payload)
    return Token(access_token=access_token, workspace_id=workspace_id)

@router.post("/google", response_model=Token)
async def google_auth(payload: GoogleAuthPayload, db: Session = Depends(get_db)):
    """
    Google OAuth login/connection endpoint. Exchanges authorization code for Google access/refresh tokens,
    saves the encrypted oauth credentials, and returns a session JWT token.
    """
    jwt_token, workspace_id = await auth_service.exchange_google_code(
        db, 
        code=payload.code,
        workspace_id=payload.workspace_id
    )
    return Token(access_token=jwt_token, workspace_id=workspace_id)
