"""
Authentication and authorization helper functions.
"""
from fastapi import HTTPException, Header
from typing import Optional


async def get_user_id(x_user_id: Optional[str] = Header(None, alias="X-User-ID")) -> str:
    """
    Extract user_id from request header.
    
    Args:
        x_user_id: User ID from X-User-ID header
    
    Returns:
        User ID string (stripped of leading/trailing whitespace)
    
    Raises:
        HTTPException: If user ID is not provided or is only whitespace
    
    Note:
        In production, this should be replaced with proper authentication
        (JWT tokens, OAuth, etc.)
    """
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(
            status_code=401,
            detail="User ID is required in X-User-ID header"
        )

    print(f"User ID: {x_user_id.strip()}")
    return x_user_id.strip()


async def check_admin(x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")) -> bool:
    """
    Check if request is from admin.
    
    Args:
        x_admin_token: Admin token from X-Admin-Token header
    
    Returns:
        True if admin token is valid
    
    Raises:
        HTTPException: If admin token is invalid or missing
    
    Note:
        In production, this should be replaced with proper authentication
        (JWT with role claims, OAuth scopes, etc.)
    """
    # TODO: Move to environment variables
    admin_token = "admin_secret_token"
    
    # Check if token is None, empty, or only whitespace
    if not x_admin_token or not x_admin_token.strip():
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    # Require exact match (no whitespace normalization for security)
    # Tokens with leading/trailing whitespace should be rejected
    if x_admin_token != admin_token:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return True

