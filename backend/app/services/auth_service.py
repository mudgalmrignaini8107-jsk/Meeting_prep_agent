# app/services/auth_service.py

import httpx
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from loguru import logger

from app.models.user import User, Workspace
from app.models.oauth import OAuthConnection
from app.models.audit import AuditLog
from app.schemas.user import UserCreate
from app.schemas.auth import LoginPayload
from app.core.security import (
    get_password_hash,
    verify_password,
    encrypt_token,
    create_access_token
)
from app.config import settings

async def authenticate_user(db: Session, payload: LoginPayload) -> Tuple[User, int]:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user's primary/first workspace
    workspace = db.query(Workspace).filter(Workspace.owner_id == user.id).first()
    if not workspace:
        # Fallback to create workspace if somehow missing
        workspace = Workspace(name="Default Workspace", owner_id=user.id)
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
        
    return user, workspace.id

async def register_user(db: Session, payload: UserCreate) -> Tuple[User, int]:
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(payload.password)
    user = User(email=payload.email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create default workspace
    workspace = Workspace(name=f"{payload.email.split('@')[0]}'s Workspace", owner_id=user.id)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    
    # Log Audit Log
    audit = AuditLog(
        user_id=user.id,
        workspace_id=workspace.id,
        action="user_register",
        details=f"User {user.email} registered. Workspace created: {workspace.name}."
    )
    db.add(audit)
    db.commit()
    
    return user, workspace.id

async def exchange_google_code(db: Session, code: str, workspace_id: Optional[int] = None) -> Tuple[str, int]:
    # 1. Exchange auth code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=token_data)
        if response.status_code != 200:
            logger.error(f"Google Token Exchange Failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to authenticate with Google: {response.json().get('error_description', 'Token exchange failed')}"
            )
        
        tokens = response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        expires_in = tokens.get("expires_in", 3600)
        scopes = tokens.get("scope", "")
        
        # 2. Get User Profile from Google info endpoint
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        info_response = await client.get(user_info_url, headers=headers)
        
        if info_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to retrieve Google user profile details."
            )
            
        profile = info_response.json()
        email = profile.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google OAuth profile did not return a valid email address."
            )
            
        # 3. Handle user persistence (Login or Register)
        user = db.query(User).filter(User.email == email).first()
        is_new = False
        if not user:
            # Register user automatically
            is_new = True
            random_pw = get_password_hash(datetime.utcnow().isoformat()) # random password hash
            user = User(email=email, hashed_password=random_pw)
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Create default workspace
            workspace = Workspace(name=f"{email.split('@')[0]}'s Workspace", owner_id=user.id)
            db.add(workspace)
            db.commit()
            db.refresh(workspace)
            active_workspace_id = workspace.id
        else:
            # Retrieve active workspace ID
            if workspace_id:
                ws = db.query(Workspace).filter(Workspace.id == workspace_id, Workspace.owner_id == user.id).first()
                active_workspace_id = ws.id if ws else db.query(Workspace).filter(Workspace.owner_id == user.id).first().id
            else:
                active_workspace_id = db.query(Workspace).filter(Workspace.owner_id == user.id).first().id
        
        # 4. Encrypt and save Google OAuth Connection details
        encrypted_access = encrypt_token(access_token)
        encrypted_refresh = encrypt_token(refresh_token) if refresh_token else None
        
        # Check for existing google oauth connection
        oauth_conn = db.query(OAuthConnection).filter(
            OAuthConnection.user_id == user.id,
            OAuthConnection.provider == "google"
        ).first()
        
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        if oauth_conn:
            oauth_conn.access_token = encrypted_access
            if encrypted_refresh:
                oauth_conn.refresh_token = encrypted_refresh
            oauth_conn.scopes = scopes
            oauth_conn.expires_at = expires_at
        else:
            oauth_conn = OAuthConnection(
                user_id=user.id,
                provider="google",
                access_token=encrypted_access,
                refresh_token=encrypted_refresh,
                token_uri=token_url,
                scopes=scopes,
                expires_at=expires_at
            )
            db.add(oauth_conn)
            
        db.commit()
        
        # Log Audit Log
        audit_action = "oauth_connect_register" if is_new else "oauth_connect_login"
        audit = AuditLog(
            user_id=user.id,
            workspace_id=active_workspace_id,
            action=audit_action,
            details=f"User {user.email} authenticated via Google OAuth."
        )
        db.add(audit)
        db.commit()
        
        # 5. Generate and return JWT session token
        jwt_payload = {
            "sub": str(user.id),
            "email": user.email,
            "workspace_id": active_workspace_id
        }
        jwt_token = create_access_token(jwt_payload)
        
        return jwt_token, active_workspace_id
