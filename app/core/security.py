# app/core/security.py

import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
import bcrypt
from cryptography.fernet import Fernet
from app.config import settings

# Initialize Fernet encryption for OAuth tokens
try:
    # Ensure key is base64 url-safe
    fernet_key = settings.TOKEN_ENCRYPTION_KEY.encode()
    # Test if it's a valid Fernet key
    _ = Fernet(fernet_key)
except Exception:
    # Fallback/Regenerate safe key for local dev if invalid
    # Standard Fernet keys must be 32 base64 urlsafe encoded bytes.
    # We pad or resolve it here.
    safe_key = base64.urlsafe_b64encode(settings.TOKEN_ENCRYPTION_KEY[:32].encode().ljust(32, b'0'))
    fernet_key = safe_key

cipher_suite = Fernet(fernet_key)

# Password Utilities
def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False

# Symmetric OAuth Token Encryption
def encrypt_token(token: str) -> str:
    if not token:
        return ""
    return cipher_suite.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    if not encrypted_token:
        return ""
    return cipher_suite.decrypt(encrypted_token.encode()).decode()

# JWT Token Utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
