# core/auth.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a plain password"""
    truncated = password[:72]
    return pwd_context.hash(truncated)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    truncated = plain_password[:72]
    return pwd_context.verify(truncated, hashed_password)
