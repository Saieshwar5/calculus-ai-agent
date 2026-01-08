"""
CRUD operations for Topic Completions.

Handles database operations for tracking completed topics in learning plans.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from typing import Optional, List, Dict
from datetime import datetime

from app.models.course_DBs.topic_completion_model import TopicCompletion


async def create_topic_completion(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    subject_name: str,
    concept_name: str,
    topic_name: str,
    depth_increment: int = 1,
    content_snapshot: Optional[str] = None,
    full_content: Optional[str] = None
) -> TopicCompletion:
    """
    Create a topic completion record.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier
        subject_name: Subject name from learning plan
        concept_name: Concept name from learning plan
        topic_name: Topic name that was completed
        depth_increment: How much depth this topic adds (1-3)
        content_snapshot: Optional brief snapshot of content delivered
        full_content: Optional full educational content for navigation history

    Returns:
        Created TopicCompletion object

    Raises:
        ValueError: If topic completion already exists
    """
    # Check if already completed
    existing = await is_topic_completed(db, user_id, course_id, subject_name, concept_name, topic_name)
    if existing:
        raise ValueError(f"Topic '{topic_name}' already marked as completed for this concept")

    topic_completion = TopicCompletion(
        user_id=user_id,
        course_id=course_id,
        subject_name=subject_name,
        concept_name=concept_name,
        topic_name=topic_name,
        depth_increment=depth_increment,
        completed=True,
        completed_at=datetime.now(),
        content_snapshot=content_snapshot,
        full_content=full_content,
        created_at=datetime.now()
    )

    db.add(topic_completion)
    await db.commit()
    await db.refresh(topic_completion)

    print(f"✅ Topic completed: {subject_name} → {concept_name} → {topic_name} (depth +{depth_increment})")
    return topic_completion


async def get_completed_topics(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    subject_name: Optional[str] = None,
    concept_name: Optional[str] = None
) -> List[str]:
    """
    Get list of completed topic names.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier
        subject_name: Optional filter by subject name
        concept_name: Optional filter by concept name

    Returns:
        List of completed topic names
    """
    query = select(TopicCompletion.topic_name).where(
        TopicCompletion.user_id == user_id,
        TopicCompletion.course_id == course_id,
        TopicCompletion.completed == True
    )

    if subject_name:
        query = query.where(TopicCompletion.subject_name == subject_name)

    if concept_name:
        query = query.where(TopicCompletion.concept_name == concept_name)

    query = query.order_by(TopicCompletion.completed_at.asc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_completed_topic_objects(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    subject_name: Optional[str] = None,
    concept_name: Optional[str] = None
) -> List[TopicCompletion]:
    """
    Get list of completed topic objects (full records).

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier
        subject_name: Optional filter by subject name
        concept_name: Optional filter by concept name

    Returns:
        List of TopicCompletion objects
    """
    query = select(TopicCompletion).where(
        TopicCompletion.user_id == user_id,
        TopicCompletion.course_id == course_id,
        TopicCompletion.completed == True
    )

    if subject_name:
        query = query.where(TopicCompletion.subject_name == subject_name)

    if concept_name:
        query = query.where(TopicCompletion.concept_name == concept_name)

    query = query.order_by(TopicCompletion.completed_at.asc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def is_topic_completed(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    subject_name: str,
    concept_name: str,
    topic_name: str
) -> bool:
    """
    Check if a specific topic has been completed.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier
        subject_name: Subject name
        concept_name: Concept name
        topic_name: Topic name

    Returns:
        True if topic is completed, False otherwise
    """
    result = await db.execute(
        select(TopicCompletion).where(
            TopicCompletion.user_id == user_id,
            TopicCompletion.course_id == course_id,
            TopicCompletion.subject_name == subject_name,
            TopicCompletion.concept_name == concept_name,
            TopicCompletion.topic_name == topic_name,
            TopicCompletion.completed == True
        )
    )
    return result.scalar_one_or_none() is not None


async def get_completion_stats(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    subject_name: Optional[str] = None
) -> Dict:
    """
    Get completion statistics for a course or subject.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier
        subject_name: Optional filter by subject name

    Returns:
        Dictionary with completion statistics
    """
    # Base query for counting
    count_query = select(func.count(TopicCompletion.id)).where(
        TopicCompletion.user_id == user_id,
        TopicCompletion.course_id == course_id,
        TopicCompletion.completed == True
    )

    if subject_name:
        count_query = count_query.where(TopicCompletion.subject_name == subject_name)

    result = await db.execute(count_query)
    total_completed = result.scalar_one()

    # Get subjects breakdown if no specific subject
    stats = {
        "user_id": user_id,
        "course_id": course_id,
        "total_completed": total_completed
    }

    if subject_name:
        stats["subject_name"] = subject_name
    else:
        # Get per-subject breakdown
        subjects_query = (
            select(
                TopicCompletion.subject_name,
                func.count(TopicCompletion.id).label("count")
            )
            .where(
                TopicCompletion.user_id == user_id,
                TopicCompletion.course_id == course_id,
                TopicCompletion.completed == True
            )
            .group_by(TopicCompletion.subject_name)
        )

        result = await db.execute(subjects_query)
        subjects_breakdown = {row[0]: row[1] for row in result.all()}
        stats["subjects_breakdown"] = subjects_breakdown

    return stats


async def get_topic_history_with_content(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    subject_name: str,
    concept_name: str
) -> List[TopicCompletion]:
    """
    Get all completed topics with full content for navigation, ordered by completion time.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier
        subject_name: Subject name
        concept_name: Concept name

    Returns:
        List of TopicCompletion objects with full content, ordered by completed_at ascending
    """
    query = select(TopicCompletion).where(
        TopicCompletion.user_id == user_id,
        TopicCompletion.course_id == course_id,
        TopicCompletion.subject_name == subject_name,
        TopicCompletion.concept_name == concept_name,
        TopicCompletion.completed == True
    ).order_by(TopicCompletion.completed_at.asc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def delete_topic_completion(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    subject_name: str,
    concept_name: str,
    topic_name: str
) -> bool:
    """
    Delete a topic completion record (allow un-completing).

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier
        subject_name: Subject name
        concept_name: Concept name
        topic_name: Topic name

    Returns:
        True if deleted, False if not found
    """
    stmt = delete(TopicCompletion).where(
        TopicCompletion.user_id == user_id,
        TopicCompletion.course_id == course_id,
        TopicCompletion.subject_name == subject_name,
        TopicCompletion.concept_name == concept_name,
        TopicCompletion.topic_name == topic_name
    )

    result = await db.execute(stmt)
    await db.commit()

    deleted = result.rowcount > 0
    if deleted:
        print(f"✅ Deleted topic completion: {subject_name} → {concept_name} → {topic_name}")
    return deleted


async def delete_all_completions_for_course(
    db: AsyncSession,
    user_id: str,
    course_id: str
) -> int:
    """
    Delete all topic completions for a course (useful when resetting progress).

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier

    Returns:
        Number of records deleted
    """
    stmt = delete(TopicCompletion).where(
        TopicCompletion.user_id == user_id,
        TopicCompletion.course_id == course_id
    )

    result = await db.execute(stmt)
    await db.commit()

    count = result.rowcount
    if count > 0:
        print(f"✅ Deleted {count} topic completions for course {course_id}")
    return count
