"""
CRUD operations for LearningPreference model.
All database operations are separated from routing logic.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models.learning_preference_model import LearningPreference
from app.schemas.pydantic_schemas.learning_preference_schema import (
    LearningPreferenceCreate,
    LearningPreferenceUpdate
)


async def get_learning_preference_by_user_id(
    db: AsyncSession,
    user_id: str
) -> Optional[LearningPreference]:
    """
    Get learning preferences by user_id.
    
    Args:
        db: Database session
        user_id: User identifier
    
    Returns:
        LearningPreference object or None if not found
    """
    query = select(LearningPreference).where(LearningPreference.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_learning_preference(
    db: AsyncSession,
    user_id: str,
    preference_data: LearningPreferenceCreate
) -> LearningPreference:
    """
    Create new learning preferences for a user.
    
    Args:
        db: Database session
        user_id: User identifier
        preference_data: Learning preference data to create
    
    Returns:
        Created LearningPreference object
    
    Raises:
        ValueError: If preferences already exist for this user
    """
    # Check if preferences already exist
    existing = await get_learning_preference_by_user_id(db, user_id)
    if existing:
        raise ValueError(f"Learning preferences already exist for user_id: {user_id}")
    
    # Create new learning preferences
    new_preference = LearningPreference(
        user_id=user_id,
        web_search=preference_data.web_search,
        youtube_search=preference_data.youtube_search,
        diagrams_and_flowcharts=preference_data.diagrams_and_flowcharts,
        images_and_illustrations=preference_data.images_and_illustrations,
        charts_and_graphs=preference_data.charts_and_graphs,
        mind_maps=preference_data.mind_maps,
        step_by_step_explanation=preference_data.step_by_step_explanation,
        worked_examples=preference_data.worked_examples,
        practice_problems=preference_data.practice_problems,
        learn_through_stories=preference_data.learn_through_stories,
        explain_with_real_world_examples=preference_data.explain_with_real_world_examples,
        analogies_and_comparisons=preference_data.analogies_and_comparisons,
        fun_and_curious_facts=preference_data.fun_and_curious_facts,
        handling_difficulty=preference_data.handling_difficulty
    )
    
    db.add(new_preference)
    await db.commit()
    await db.refresh(new_preference)
    
    return new_preference


async def update_learning_preference(
    db: AsyncSession,
    user_id: str,
    preference_data: LearningPreferenceUpdate
) -> LearningPreference:
    """
    Update existing learning preferences.
    
    Args:
        db: Database session
        user_id: User identifier
        preference_data: Learning preference data to update (only provided fields)
    
    Returns:
        Updated LearningPreference object
    
    Raises:
        ValueError: If preferences not found
    """
    preference = await get_learning_preference_by_user_id(db, user_id)
    
    if not preference:
        raise ValueError(f"Learning preferences not found for user_id: {user_id}")
    
    # Update only provided fields
    update_data = preference_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preference, field, value)
    
    await db.commit()
    await db.refresh(preference)
    
    return preference


async def create_or_update_learning_preference(
    db: AsyncSession,
    user_id: str,
    preference_data: LearningPreferenceCreate
) -> LearningPreference:
    """
    Create or update learning preferences (upsert operation).
    If preferences exist, update them; otherwise, create new ones.
    
    Args:
        db: Database session
        user_id: User identifier
        preference_data: Learning preference data
    
    Returns:
        Created or updated LearningPreference object
    """
    existing = await get_learning_preference_by_user_id(db, user_id)
    
    if existing:
        # Update existing preferences
        update_data = LearningPreferenceUpdate(**preference_data.model_dump())
        return await update_learning_preference(db, user_id, update_data)
    else:
        # Create new preferences
        return await create_learning_preference(db, user_id, preference_data)


async def delete_learning_preference(
    db: AsyncSession,
    user_id: str
) -> None:
    """
    Delete learning preferences for a user.
    
    Args:
        db: Database session
        user_id: User identifier
    
    Raises:
        ValueError: If preferences not found
    """
    preference = await get_learning_preference_by_user_id(db, user_id)
    
    if not preference:
        raise ValueError(f"Learning preferences not found for user_id: {user_id}")
    
    # Hard delete - permanently remove from database
    from sqlalchemy import delete
    await db.execute(delete(LearningPreference).where(LearningPreference.id == preference.id))
    await db.commit()

