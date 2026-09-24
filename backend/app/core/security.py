import hashlib
import hmac
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from app.core.config import settings

def get_password_hash(password: str) -> str:
    # Use PBKDF2 with SHA-256 for secure, robust password hashing
    salt = "edusupport_fixed_salt_2026".encode('utf-8')
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return pwd_hash.hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    candidate_hash = get_password_hash(plain_password)
    return hmac.compare_digest(candidate_hash, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
