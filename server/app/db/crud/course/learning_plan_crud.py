"""
CRUD operations for Learning Plans.

Handles database operations for storing and retrieving learning plans.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import Optional, List
from datetime import datetime

from app.models.course_DBs.learning_plan_model import LearningPlan
from app.schemas.pydantic_schemas.learning_plan_schema import (
    LearningPlanCreate,
    LearningPlanDBResponse
)


async def create_learning_plan(
    db: AsyncSession,
    plan_data: LearningPlanCreate
) -> LearningPlan:
    """
    Create a new learning plan in the database.

    Args:
        db: Database session
        plan_data: Learning plan data to create

    Returns:
        Created LearningPlan object
    """
    learning_plan = LearningPlan(
        user_id=plan_data.user_id,
        course_id=plan_data.course_id,
        title=plan_data.title,
        description=plan_data.description,
        plan_data=plan_data.plan_data,
        status=plan_data.status,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(learning_plan)
    await db.commit()
    await db.refresh(learning_plan)

    print(f"✅ Created learning plan: {plan_data.user_id}:{plan_data.course_id}")
    return learning_plan


async def get_learning_plan(
    db: AsyncSession,
    user_id: str,
    course_id: str
) -> Optional[LearningPlan]:
    """
    Retrieve a learning plan by user_id and course_id.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier

    Returns:
        LearningPlan object or None if not found
    """
    result = await db.execute(
        select(LearningPlan).where(
            LearningPlan.user_id == user_id,
            LearningPlan.course_id == course_id
        )
    )
    return result.scalar_one_or_none()


async def update_learning_plan(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    update_data: dict
) -> Optional[LearningPlan]:
    """
    Update an existing learning plan.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier
        update_data: Dictionary of fields to update

    Returns:
        Updated LearningPlan object or None if not found
    """
    # Add updated_at timestamp
    update_data["updated_at"] = datetime.now()

    stmt = (
        update(LearningPlan)
        .where(
            LearningPlan.user_id == user_id,
            LearningPlan.course_id == course_id
        )
        .values(**update_data)
    )

    await db.execute(stmt)
    await db.commit()

    # Fetch and return updated plan
    return await get_learning_plan(db, user_id, course_id)


async def delete_learning_plan(
    db: AsyncSession,
    user_id: str,
    course_id: str
) -> bool:
    """
    Delete a learning plan.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier

    Returns:
        True if deleted, False if not found
    """
    stmt = delete(LearningPlan).where(
        LearningPlan.user_id == user_id,
        LearningPlan.course_id == course_id
    )

    result = await db.execute(stmt)
    await db.commit()

    deleted = result.rowcount > 0
    if deleted:
        print(f"✅ Deleted learning plan: {user_id}:{course_id}")
    return deleted


async def get_user_learning_plans(
    db: AsyncSession,
    user_id: str,
    status: Optional[str] = None
) -> List[LearningPlan]:
    """
    Get all learning plans for a user.

    Args:
        db: Database session
        user_id: User identifier
        status: Optional status filter (draft|active|completed|archived)

    Returns:
        List of LearningPlan objects
    """
    query = select(LearningPlan).where(LearningPlan.user_id == user_id)

    if status:
        query = query.where(LearningPlan.status == status)

    # Order by most recent first
    query = query.order_by(LearningPlan.created_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


def learning_plan_to_response(plan: LearningPlan) -> LearningPlanDBResponse:
    """
    Convert LearningPlan ORM model to Pydantic response.

    Args:
        plan: LearningPlan ORM object

    Returns:
        LearningPlanDBResponse object
    """
    return LearningPlanDBResponse(
        user_id=plan.user_id,
        course_id=plan.course_id,
        title=plan.title,
        description=plan.description,
        plan_data=plan.plan_data,
        status=plan.status,
        created_at=plan.created_at,
        updated_at=plan.updated_at
    )
