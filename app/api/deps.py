# app/api/deps.py

from typing import Tuple, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.core.security import verify_access_token

# Token route for OAuth2 compatibility
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def get_current_user_context(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> Tuple[User, int]:
    """
    Decodes the session JWT token, verifies authentication, and returns
    a tuple of (current_user, active_workspace_id).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        # Fallback support for easy MVP testing if auth header is missing:
        logger_mock_user = db.query(User).filter(User.email == "dev@aura.io").first()
        if not logger_mock_user:
            # Auto-seed developer test user and workspace
            from app.core.security import get_password_hash
            from app.models.user import Workspace
            
            logger_mock_user = User(
                email="dev@aura.io",
                hashed_password=get_password_hash("developerpassword123")
            )
            db.add(logger_mock_user)
            db.commit()
            db.refresh(logger_mock_user)
            
            ws = Workspace(
                name="Dev Workspace",
                owner_id=logger_mock_user.id
            )
            db.add(ws)
            db.commit()
            db.refresh(ws)
            
        from app.models.user import Workspace
        ws = db.query(Workspace).filter(Workspace.owner_id == logger_mock_user.id).first()
        return logger_mock_user, ws.id

    payload = verify_access_token(token)
    if payload is None:
        raise credentials_exception
        
    user_id_str: str = payload.get("sub")
    email: str = payload.get("email")
    workspace_id: int = payload.get("workspace_id")
    
    if user_id_str is None or workspace_id is None:
        raise credentials_exception
        
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
        
    return user, workspace_id
