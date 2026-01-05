"""
JWT token utilities for creating, verifying, and decoding tokens.
"""
import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-min-32-chars")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password hashing context
# Configure to handle passwords of any length by truncating if needed
# Note: The "(trapped) error reading bcrypt version" warning is harmless
# and can be ignored - passlib handles it gracefully
try:
    pwd_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        bcrypt__ident="2b"  # Use bcrypt version 2b
    )
except Exception as e:
    # Fallback initialization if there's an issue
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Bcrypt has a 72-byte limit, so we pre-hash long passwords with SHA256.
    This allows passwords of any length while maintaining bcrypt security.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
    
    Returns:
        True if password matches, False otherwise
    """
    # If password is longer than 72 bytes, pre-hash with SHA256
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        # Pre-hash with SHA256 to get a fixed 64-character hex string
        plain_password = hashlib.sha256(password_bytes).hexdigest()
    
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Bcrypt has a 72-byte limit, so we pre-hash long passwords with SHA256.
    This allows passwords of any length while maintaining bcrypt security.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    
    Raises:
        ValueError: If password hashing fails
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    # Convert to bytes to check actual byte length
    password_bytes = password.encode('utf-8')
    password_byte_length = len(password_bytes)
    
    # If password exceeds 72 bytes, pre-hash with SHA256
    # This ensures we always pass a password <= 72 bytes to bcrypt
    if password_byte_length > 72:
        # Pre-hash with SHA256 to get a fixed 64-character hex string (always 64 bytes)
        password = hashlib.sha256(password_bytes).hexdigest()
    
    try:
        # Now hash with bcrypt (password is guaranteed to be <= 72 bytes)
        return pwd_context.hash(password)
    except ValueError as e:
        # If passlib still complains, try one more time with SHA256 pre-hash
        if "72 bytes" in str(e).lower() or "too long" in str(e).lower():
            password_bytes = password.encode('utf-8')
            if len(password_bytes) > 72:
                password = hashlib.sha256(password_bytes).hexdigest()
                return pwd_context.hash(password)
        raise ValueError(f"Failed to hash password: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error hashing password: {str(e)}")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token (typically user_id, email, etc.)
        expires_delta: Optional custom expiration time
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    print(f"To encode: {to_encode}")
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    print(f"Encoded JWT: {encoded_jwt}")
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token with longer expiration.
    
    Args:
        data: Data to encode in the token
    
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a JWT token without verification (use with caution).
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except JWTError:
        return None


def get_token_expiration_seconds() -> int:
    """
    Get token expiration time in seconds.
    
    Returns:
        Expiration time in seconds
    """
    return ACCESS_TOKEN_EXPIRE_MINUTES * 60

