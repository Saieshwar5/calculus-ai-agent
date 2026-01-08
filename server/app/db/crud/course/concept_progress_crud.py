"""
CRUD operations for Concept Progress.

Handles database operations for tracking progress within concepts (depth tracking,
completion status, learning summaries).
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, List, Dict
from datetime import datetime

from app.models.course_DBs.concept_progress_model import ConceptProgress


async def get_or_create_concept_progress(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    subject_name: str,
    concept_name: str,
    target_depth: int
) -> ConceptProgress:
    """
    Get existing concept progress or create new one.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier
        subject_name: Subject name from learning plan
        concept_name: Concept name from learning plan
        target_depth: Target depth from learning plan

    Returns:
        ConceptProgress object
    """
    # Try to find existing progress
    result = await db.execute(
        select(ConceptProgress).where(
            ConceptProgress.user_id == user_id,
            ConceptProgress.course_id == course_id,
            ConceptProgress.subject_name == subject_name,
            ConceptProgress.concept_name == concept_name
        )
    )
    progress = result.scalar_one_or_none()

    if progress:
        return progress

    # Create new progress record
    progress = ConceptProgress(
        user_id=user_id,
        course_id=course_id,
        subject_name=subject_name,
        concept_name=concept_name,
        current_depth=0,
        target_depth=target_depth,
        topics_completed=0,
        completed=False,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(progress)
    await db.commit()
    await db.refresh(progress)

    print(f"✅ Created concept progress: {concept_name} (target depth: {target_depth})")
    return progress


async def update_concept_progress(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    subject_name: str,
    concept_name: str,
    depth_increment: int,
    topic_name: str
) -> ConceptProgress:
    """
    Update concept progress after topic completion.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier
        subject_name: Subject name
        concept_name: Concept name
        depth_increment: Depth added by this topic
        topic_name: Name of topic just completed

    Returns:
        Updated ConceptProgress object
    """
    # Get existing progress
    result = await db.execute(
        select(ConceptProgress).where(
            ConceptProgress.user_id == user_id,
            ConceptProgress.course_id == course_id,
            ConceptProgress.subject_name == subject_name,
            ConceptProgress.concept_name == concept_name
        )
    )
    progress = result.scalar_one_or_none()

    if not progress:
        raise ValueError(f"Concept progress not found for {concept_name}")

    # Update progress
    progress.current_depth += depth_increment
    progress.topics_completed += 1
    progress.last_topic_name = topic_name
    progress.updated_at = datetime.now()

    # Check if completed (depth reached + minimum 3 topics)
    if progress.current_depth >= progress.target_depth and progress.topics_completed >= 3:
        progress.completed = True
        progress.completed_at = datetime.now()

    await db.commit()
    await db.refresh(progress)

    print(f"✅ Updated progress: {concept_name} → {progress.current_depth}/{progress.target_depth} (topics: {progress.topics_completed})")
    return progress


async def mark_concept_complete(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    subject_name: str,
    concept_name: str,
    learning_summary: Optional[str] = None
) -> ConceptProgress:
    """
    Mark a concept as completed with optional learning summary.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier
        subject_name: Subject name
        concept_name: Concept name
        learning_summary: Summary of what was learned

    Returns:
        Updated ConceptProgress object
    """
    result = await db.execute(
        select(ConceptProgress).where(
            ConceptProgress.user_id == user_id,
            ConceptProgress.course_id == course_id,
            ConceptProgress.subject_name == subject_name,
            ConceptProgress.concept_name == concept_name
        )
    )
    progress = result.scalar_one_or_none()

    if not progress:
        raise ValueError(f"Concept progress not found for {concept_name}")

    progress.completed = True
    progress.completed_at = datetime.now()
    if learning_summary:
        progress.learning_summary = learning_summary
    progress.updated_at = datetime.now()

    await db.commit()
    await db.refresh(progress)

    print(f"✅ Concept marked complete: {concept_name} ({progress.topics_completed} topics, depth {progress.current_depth}/{progress.target_depth})")
    return progress


async def get_concept_progress(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    subject_name: str,
    concept_name: str
) -> Optional[ConceptProgress]:
    """
    Get concept progress for a specific concept.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier
        subject_name: Subject name
        concept_name: Concept name

    Returns:
        ConceptProgress object or None if not found
    """
    result = await db.execute(
        select(ConceptProgress).where(
            ConceptProgress.user_id == user_id,
            ConceptProgress.course_id == course_id,
            ConceptProgress.subject_name == subject_name,
            ConceptProgress.concept_name == concept_name
        )
    )
    return result.scalar_one_or_none()


async def get_all_concept_progress_for_subject(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    subject_name: str
) -> List[ConceptProgress]:
    """
    Get all concept progress records for a subject.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier
        subject_name: Subject name

    Returns:
        List of ConceptProgress objects
    """
    result = await db.execute(
        select(ConceptProgress).where(
            ConceptProgress.user_id == user_id,
            ConceptProgress.course_id == course_id,
            ConceptProgress.subject_name == subject_name
        ).order_by(ConceptProgress.created_at.asc())
    )
    return list(result.scalars().all())


async def get_all_concept_progress_for_course(
    db: AsyncSession,
    user_id: str,
    course_id: str
) -> List[ConceptProgress]:
    """
    Get all concept progress records for a course.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier

    Returns:
        List of ConceptProgress objects
    """
    result = await db.execute(
        select(ConceptProgress).where(
            ConceptProgress.user_id == user_id,
            ConceptProgress.course_id == course_id
        ).order_by(ConceptProgress.created_at.asc())
    )
    return list(result.scalars().all())


async def get_concept_progress_stats(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    subject_name: Optional[str] = None
) -> Dict:
    """
    Get aggregated stats for concept progress.

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier
        subject_name: Optional filter by subject

    Returns:
        Dictionary with stats
    """
    query = select(ConceptProgress).where(
        ConceptProgress.user_id == user_id,
        ConceptProgress.course_id == course_id
    )

    if subject_name:
        query = query.where(ConceptProgress.subject_name == subject_name)

    result = await db.execute(query)
    all_progress = list(result.scalars().all())

    # Calculate stats
    total_concepts = len(all_progress)
    completed_concepts = sum(1 for p in all_progress if p.completed)
    total_topics = sum(p.topics_completed for p in all_progress)
    total_depth_achieved = sum(p.current_depth for p in all_progress)
    total_target_depth = sum(p.target_depth for p in all_progress)

    stats = {
        "user_id": user_id,
        "course_id": course_id,
        "total_concepts": total_concepts,
        "completed_concepts": completed_concepts,
        "total_topics": total_topics,
        "total_depth_achieved": total_depth_achieved,
        "total_target_depth": total_target_depth,
        "overall_progress_percent": int((total_depth_achieved / total_target_depth * 100)) if total_target_depth > 0 else 0
    }

    if subject_name:
        stats["subject_name"] = subject_name

    return stats


async def delete_concept_progress(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    subject_name: str,
    concept_name: str
) -> bool:
    """
    Delete concept progress (for reset functionality).

    Args:
        db: Database session
        user_id: User identifier
        course_id: Course identifier
        subject_name: Subject name
        concept_name: Concept name

    Returns:
        True if deleted, False if not found
    """
    result = await db.execute(
        select(ConceptProgress).where(
            ConceptProgress.user_id == user_id,
            ConceptProgress.course_id == course_id,
            ConceptProgress.subject_name == subject_name,
            ConceptProgress.concept_name == concept_name
        )
    )
    progress = result.scalar_one_or_none()

    if not progress:
        return False

    await db.delete(progress)
    await db.commit()

    print(f"✅ Deleted concept progress: {concept_name}")
    return True
