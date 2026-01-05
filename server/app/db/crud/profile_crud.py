"""
CRUD operations for Profile model.
All database operations are separated from routing logic.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sql_func
from typing import Optional, List, Tuple

from app.models.profile_model import Profile
from app.schemas.pydantic_schemas.profile_schema import ProfileCreate, ProfileUpdate


async def get_profile_by_user_id(
    db: AsyncSession,
    user_id: str,
    include_inactive: bool = False
) -> Optional[Profile]:
    """
    Get a profile by user_id.
    
    Args:
        db: Database session
        user_id: User identifier
        include_inactive: If True, includes inactive profiles
    
    Returns:
        Profile object or None if not found
    """
    query = select(Profile).where(Profile.user_id == user_id)
    
    if not include_inactive:
        query = query.where(Profile.is_active == True)
    
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_profile(
    db: AsyncSession,
    user_id: str,
    profile_data: ProfileCreate
) -> Profile:
    """
    Create a new profile.
    
    Args:
        db: Database session
        user_id: User identifier
        profile_data: Profile data to create
    
    Returns:
        Created Profile object
    
    Raises:
        ValueError: If profile already exists
    """
    # Check if profile already exists
    existing = await get_profile_by_user_id(db, user_id, include_inactive=True)
    if existing:
        raise ValueError(f"Profile already exists for user_id: {user_id}")
    
    # Create new profile
    new_profile = Profile(
        user_id=user_id,
        username=profile_data.username,
        date_of_birth=profile_data.date_of_birth,
        country=profile_data.country,
        education=profile_data.education,
        mother_tongue=profile_data.mother_tongue,
        gender=profile_data.gender,
        learning_pace=profile_data.learning_pace
    )
    
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    
    return new_profile


async def update_profile(
    db: AsyncSession,
    user_id: str,
    profile_data: ProfileUpdate,
    include_inactive: bool = False
) -> Profile:
    """
    Update an existing profile.
    
    Args:
        db: Database session
        user_id: User identifier
        profile_data: Profile data to update (only provided fields)
        include_inactive: If True, can update inactive profiles
    
    Returns:
        Updated Profile object
    
    Raises:
        ValueError: If profile not found
    """
    profile = await get_profile_by_user_id(db, user_id, include_inactive=include_inactive)
    
    if not profile:
        raise ValueError(f"Profile not found for user_id: {user_id}")
    
    # Update only provided fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    await db.commit()
    await db.refresh(profile)
    
    return profile


async def delete_profile(
    db: AsyncSession,
    user_id: str,
    hard_delete: bool = False
) -> None:
    """
    Delete a profile (soft delete by default).
    
    Args:
        db: Database session
        user_id: User identifier
        hard_delete: If True, permanently deletes from database
    
    Raises:
        ValueError: If profile not found
    """
    profile = await get_profile_by_user_id(db, user_id, include_inactive=True)
    
    if not profile:
        raise ValueError(f"Profile not found for user_id: {user_id}")
    
    if hard_delete:
        # Hard delete - permanently remove from database
        from sqlalchemy import delete
        await db.execute(delete(Profile).where(Profile.id == profile.id))
    else:
        # Soft delete
        profile.is_active = False
    
    await db.commit()


async def activate_profile(
    db: AsyncSession,
    user_id: str
) -> Profile:
    """
    Activate a profile (set is_active to True).
    
    Args:
        db: Database session
        user_id: User identifier
    
    Returns:
        Activated Profile object
    
    Raises:
        ValueError: If profile not found
    """
    profile = await get_profile_by_user_id(db, user_id, include_inactive=True)
    
    if not profile:
        raise ValueError(f"Profile not found for user_id: {user_id}")
    
    profile.is_active = True
    await db.commit()
    await db.refresh(profile)
    
    return profile


async def list_profiles(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    is_active: Optional[bool] = None
) -> Tuple[List[Profile], int]:
    """
    Get list of profiles with pagination.
    
    Args:
        db: Database session
        page: Page number (1-indexed)
        page_size: Number of items per page
        is_active: Filter by active status (None = all)
    
    Returns:
        Tuple of (list of profiles, total count)
    """
    # Build query
    query = select(Profile)
    
    if is_active is not None:
        query = query.where(Profile.is_active == is_active)
    
    # Get total count
    count_query = select(sql_func.count()).select_from(Profile)
    if is_active is not None:
        count_query = count_query.where(Profile.is_active == is_active)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(Profile.created_at.desc()).offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    profiles = result.scalars().all()
    
    return profiles, total

