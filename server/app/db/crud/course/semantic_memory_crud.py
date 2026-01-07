"""
CRUD operations for Course Semantic Memory.

Handles database operations for storing and retrieving semantic memory
extracted from learning plan conversations.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import Optional, List
from datetime import datetime

from app.models.course_DBs.semantic_memory_model import CourseSemanticMemory
from app.schemas.pydantic_schemas.learning_plan_schema import (
    CourseSemanticMemoryCreate,
    CourseSemanticMemoryResponse,
    SemanticMemoryData
)


async def create_semantic_memory(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    memory_data: SemanticMemoryData,
    conversation_summary: Optional[str] = None
) -> CourseSemanticMemory:
    """
    Create semantic memory for a course.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier
        memory_data: SemanticMemoryData object
        conversation_summary: Optional summary of the conversation

    Returns:
        Created CourseSemanticMemory object
    """
    # Convert Pydantic model to dict for JSONB storage
    memory_dict = memory_data.model_dump()

    # Extract quick access fields
    knowledge_level = memory_data.prior_knowledge.level
    depth_preference = memory_data.learning_preferences.depth_preference
    depth_level = memory_data.learning_preferences.depth_level

    semantic_memory = CourseSemanticMemory(
        user_id=user_id,
        course_id=course_id,
        memory_data=memory_dict,
        knowledge_level=knowledge_level,
        depth_preference=depth_preference,
        depth_level=depth_level,
        conversation_summary=conversation_summary,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(semantic_memory)
    await db.commit()
    await db.refresh(semantic_memory)

    print(f"✅ Created semantic memory: {user_id}:{course_id}")
    print(f"   Level: {knowledge_level}, Depth: {depth_preference} ({depth_level}/10)")
    return semantic_memory


async def get_semantic_memory(
    db: AsyncSession,
    user_id: str,
    course_id: str
) -> Optional[CourseSemanticMemory]:
    """
    Retrieve semantic memory by user_id and course_id.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier

    Returns:
        CourseSemanticMemory object or None if not found
    """
    result = await db.execute(
        select(CourseSemanticMemory).where(
            CourseSemanticMemory.user_id == user_id,
            CourseSemanticMemory.course_id == course_id
        )
    )
    return result.scalar_one_or_none()


async def update_semantic_memory(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    memory_data: Optional[SemanticMemoryData] = None,
    conversation_summary: Optional[str] = None
) -> Optional[CourseSemanticMemory]:
    """
    Update semantic memory.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier
        memory_data: Optional updated SemanticMemoryData
        conversation_summary: Optional updated summary

    Returns:
        Updated CourseSemanticMemory object or None if not found
    """
    update_dict = {"updated_at": datetime.now()}

    if memory_data:
        memory_dict = memory_data.model_dump()
        update_dict["memory_data"] = memory_dict
        update_dict["knowledge_level"] = memory_data.prior_knowledge.level
        update_dict["depth_preference"] = memory_data.learning_preferences.depth_preference
        update_dict["depth_level"] = memory_data.learning_preferences.depth_level

    if conversation_summary is not None:
        update_dict["conversation_summary"] = conversation_summary

    stmt = (
        update(CourseSemanticMemory)
        .where(
            CourseSemanticMemory.user_id == user_id,
            CourseSemanticMemory.course_id == course_id
        )
        .values(**update_dict)
    )

    await db.execute(stmt)
    await db.commit()

    # Fetch and return updated memory
    return await get_semantic_memory(db, user_id, course_id)


async def delete_semantic_memory(
    db: AsyncSession,
    user_id: str,
    course_id: str
) -> bool:
    """
    Delete semantic memory.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier

    Returns:
        True if deleted, False if not found
    """
    stmt = delete(CourseSemanticMemory).where(
        CourseSemanticMemory.user_id == user_id,
        CourseSemanticMemory.course_id == course_id
    )

    result = await db.execute(stmt)
    await db.commit()

    deleted = result.rowcount > 0
    if deleted:
        print(f"✅ Deleted semantic memory: {user_id}:{course_id}")
    return deleted


async def get_user_semantic_memories(
    db: AsyncSession,
    user_id: str
) -> List[CourseSemanticMemory]:
    """
    Get all semantic memories for a user.

    Args:
        db: Database session
        user_id: User identifier

    Returns:
        List of CourseSemanticMemory objects
    """
    query = (
        select(CourseSemanticMemory)
        .where(CourseSemanticMemory.user_id == user_id)
        .order_by(CourseSemanticMemory.created_at.desc())
    )

    result = await db.execute(query)
    return list(result.scalars().all())


def semantic_memory_to_response(
    memory: CourseSemanticMemory
) -> CourseSemanticMemoryResponse:
    """
    Convert CourseSemanticMemory ORM model to Pydantic response.

    Args:
        memory: CourseSemanticMemory ORM object

    Returns:
        CourseSemanticMemoryResponse object
    """
    # Reconstruct SemanticMemoryData from dict
    memory_data = SemanticMemoryData(**memory.memory_data)

    return CourseSemanticMemoryResponse(
        user_id=memory.user_id,
        course_id=memory.course_id,
        memory_data=memory_data,
        knowledge_level=memory.knowledge_level,
        depth_preference=memory.depth_preference,
        depth_level=memory.depth_level,
        conversation_summary=memory.conversation_summary,
        created_at=memory.created_at,
        updated_at=memory.updated_at
    )
