"""
CRUD operations for User model.
All database operations for user authentication.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models.user_model import User
from app.utils.jwt_utils import get_password_hash, verify_password


async def get_user_by_email(
    db: AsyncSession,
    email: str,
    include_inactive: bool = False
) -> Optional[User]:
    """
    Get a user by email.
    
    Args:
        db: Database session
        email: User email address
        include_inactive: If True, includes inactive users
    
    Returns:
        User object or None if not found
    """
    query = select(User).where(User.email == email)
    
    if not include_inactive:
        query = query.where(User.is_active == True)
    
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_user_by_uuid(
    db: AsyncSession,
    uuid: str,
    include_inactive: bool = False
) -> Optional[User]:
    """
    Get a user by UUID.
    
    Args:
        db: Database session
        uuid: User UUID
        include_inactive: If True, includes inactive users
    
    Returns:
        User object or None if not found
    """
    query = select(User).where(User.uuid == uuid)
    
    if not include_inactive:
        query = query.where(User.is_active == True)
    
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    email: str,
    password: str
) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session
        email: User email address
        password: Plain text password (will be hashed)
    
    Returns:
        Created User object
    
    Raises:
        ValueError: If user with email already exists
    """
    # Check if user already exists
    existing = await get_user_by_email(db, email, include_inactive=True)
    if existing:
        raise ValueError(f"User with email {email} already exists")
    
    # Hash password
    hashed_password = get_password_hash(password)

    print(f"Hashed password: {hashed_password}")
    
    # Create new user
    new_user = User(
        email=email,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str
) -> Optional[User]:
    """
    Authenticate a user by email and password.
    
    Args:
        db: Database session
        email: User email address
        password: Plain text password
    
    Returns:
        User object if authentication successful, None otherwise
    """
    user = await get_user_by_email(db, email, include_inactive=False)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


async def update_last_login(
    db: AsyncSession,
    user: User
) -> None:
    """
    Update user's last login timestamp.
    
    Args:
        db: Database session
        user: User object to update
    """
    from datetime import datetime
    user.last_login = datetime.utcnow()
    await db.commit()
    await db.refresh(user)


async def deactivate_user(
    db: AsyncSession,
    uuid: str
) -> User:
    """
    Deactivate a user account (soft delete).
    
    Args:
        db: Database session
        uuid: User UUID
    
    Returns:
        Deactivated User object
    
    Raises:
        ValueError: If user not found
    """
    user = await get_user_by_uuid(db, uuid, include_inactive=True)
    
    if not user:
        raise ValueError(f"User not found with uuid: {uuid}")
    
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    
    return user

