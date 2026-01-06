"""
CRUD operations for EpisodicMemory model.
Handles hybrid search: vector similarity + SQL filtering.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text, update, cast
from sqlalchemy.dialects.postgresql import array
from pgvector.sqlalchemy import Vector
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from app.models.memory.episodic import EpisodicMemory
from app.schemas.pydantic_schemas.memory.episodic import (
    EpisodicMemoryCreate,
    EpisodicMemoryFilters
)
from app.long_term_memory.shared.embedding import get_embedding_service

logger = logging.getLogger(__name__)


async def create_episodic_memory(
    db: AsyncSession,
    episode_data: EpisodicMemoryCreate,
    embedding: Optional[List[float]] = None
) -> EpisodicMemory:
    """
    Create new episodic memory record.
    If embedding is not provided, generates it automatically.
    
    Args:
        db: Database session
        episode_data: Episode data to create
        embedding: Optional pre-generated embedding
    
    Returns:
        Created EpisodicMemory object
    """
    try:
        # Generate embedding if not provided
        if embedding is None:
            embedding_service = get_embedding_service()
            embedding = await embedding_service.generate_episode_embedding(
                event_description=episode_data.event_description,
                context=episode_data.context
            )
        
        episodic_memory = EpisodicMemory(
            user_id=episode_data.user_id,
            event_description=episode_data.event_description,
            event_embedding=embedding,
            context=episode_data.context,
            emotion=episode_data.emotion,
            importance=episode_data.importance,
            event_time=episode_data.event_time,
            related_query_ids=episode_data.related_query_ids,
            additional_metadata=episode_data.additional_metadata
        )
        
        db.add(episodic_memory)
        await db.commit()
        await db.refresh(episodic_memory)
        
        logger.info(f"Created episodic memory {episodic_memory.id} for user {episode_data.user_id}")
        return episodic_memory
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating episodic memory: {e}")
        raise ValueError(f"Error creating episodic memory: {str(e)}")


async def get_episodic_memory_by_id(
    db: AsyncSession,
    episode_id: int
) -> Optional[EpisodicMemory]:
    """
    Get episodic memory by ID.
    
    Args:
        db: Database session
        episode_id: Episode ID
    
    Returns:
        EpisodicMemory object or None if not found
    """
    query = select(EpisodicMemory).where(EpisodicMemory.id == episode_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_episodic_memories_by_user(
    db: AsyncSession,
    user_id: str,
    filters: Optional[EpisodicMemoryFilters] = None,
    limit: Optional[int] = None,
    offset: int = 0
) -> List[EpisodicMemory]:
    """
    Get episodic memories for a user with optional filters.
    Pure SQL filtering (no vector search).
    
    Args:
        db: Database session
        user_id: User identifier
        filters: Optional filters (date, emotion, importance)
        limit: Optional limit on results
        offset: Offset for pagination
    
    Returns:
        List of EpisodicMemory objects
    """
    query = select(EpisodicMemory).where(EpisodicMemory.user_id == user_id)
    
    # Apply filters
    if filters:
        if filters.date_from:
            query = query.where(EpisodicMemory.event_time >= filters.date_from)
        if filters.date_to:
            query = query.where(EpisodicMemory.event_time <= filters.date_to)
        if filters.emotion:
            query = query.where(EpisodicMemory.emotion == filters.emotion)
        if filters.min_importance:
            query = query.where(EpisodicMemory.importance >= filters.min_importance)
        if filters.max_importance:
            query = query.where(EpisodicMemory.importance <= filters.max_importance)
    
    # Order by event_time (most recent first)
    query = query.order_by(EpisodicMemory.event_time.desc())
    
    # Apply pagination
    if limit:
        query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def find_similar_episodes(
    db: AsyncSession,
    query_embedding: List[float],
    user_id: str,
    similarity_threshold: float = 0.3,
    filters: Optional[EpisodicMemoryFilters] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Hybrid search: Find similar episodes using vector similarity + SQL filters.
    
    Args:
        db: Database session
        query_embedding: Query embedding vector
        user_id: User identifier
        similarity_threshold: Minimum similarity (0.0-1.0)
        filters: Optional SQL filters (date, emotion, importance)
        limit: Maximum number of results
    
    Returns:
        List of dictionaries with episode data and similarity score
    """
    try:
        # Build base query with vector similarity
        # Using cosine distance: 1 - cosine_similarity
        # Lower distance = higher similarity
        # We want similarity >= threshold, so distance <= (1 - threshold)
        max_distance = 1.0 - similarity_threshold
        
        # Cast the query embedding array to pgvector Vector type
        # This is required because cosine_distance expects (vector, vector) not (vector, double precision[])
        query_vector = cast(array(query_embedding), Vector(1536))
        
        # pgvector cosine distance query
        # Using 1 - (embedding <=> query_embedding) for similarity
        query = select(
            EpisodicMemory,
            (1 - func.cosine_distance(EpisodicMemory.event_embedding, query_vector)).label('similarity')
        ).where(
            and_(
                EpisodicMemory.user_id == user_id,
                EpisodicMemory.event_embedding.isnot(None),
                # Vector similarity filter
                func.cosine_distance(EpisodicMemory.event_embedding, query_vector) <= max_distance
            )
        )
        
        # Apply SQL filters
        if filters:
            if filters.date_from:
                query = query.where(EpisodicMemory.event_time >= filters.date_from)
            if filters.date_to:
                query = query.where(EpisodicMemory.event_time <= filters.date_to)
            if filters.emotion:
                query = query.where(EpisodicMemory.emotion == filters.emotion)
            if filters.min_importance:
                query = query.where(EpisodicMemory.importance >= filters.min_importance)
            if filters.max_importance:
                query = query.where(EpisodicMemory.importance <= filters.max_importance)
        
        # Order by similarity (descending)
        query = query.order_by(text('similarity DESC'))
        query = query.limit(limit)
        
        result = await db.execute(query)
        rows = result.all()
        
        # Format results with similarity scores
        episodes = []
        for row in rows:
            episode = row[0]
            similarity = float(row[1])
            episodes.append({
                "id": episode.id,
                "user_id": episode.user_id,
                "event_description": episode.event_description,
                "context": episode.context,
                "emotion": episode.emotion,
                "importance": episode.importance,
                "event_time": episode.event_time,
                "related_query_ids": episode.related_query_ids,
                "additional_metadata": episode.additional_metadata,
                "created_at": episode.created_at,
                "updated_at": episode.updated_at,
                "similarity": similarity
            })
        
        logger.debug(f"Found {len(episodes)} similar episodes for user {user_id}")
        return episodes
    except Exception as e:
        logger.error(f"Error finding similar episodes: {e}")
        raise


async def search_episodes_by_context(
    db: AsyncSession,
    query_text: str,
    user_id: str,
    similarity_threshold: float = 0.3,
    filters: Optional[EpisodicMemoryFilters] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    High-level function: Search episodes by context text (generates embedding automatically).
    
    Args:
        db: Database session
        query_text: Text to search for
        user_id: User identifier
        similarity_threshold: Minimum similarity threshold
        filters: Optional SQL filters
        limit: Maximum number of results
    
    Returns:
        List of episodes with similarity scores
    """
    # Generate embedding for query text
    embedding_service = get_embedding_service()
    query_embedding = await embedding_service.generate_embedding(query_text)
    
    # Use vector similarity search
    return await find_similar_episodes(
        db=db,
        query_embedding=query_embedding,
        user_id=user_id,
        similarity_threshold=similarity_threshold,
        filters=filters,
        limit=limit
    )


async def get_recent_episodic_memories(
    db: AsyncSession,
    user_id: str,
    days: int = 7,
    limit: Optional[int] = None
) -> List[EpisodicMemory]:
    """
    Get recent episodic memories (last N days).
    
    Args:
        db: Database session
        user_id: User identifier
        days: Number of days to look back
        limit: Optional limit on results
    
    Returns:
        List of EpisodicMemory objects
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = select(EpisodicMemory).where(
        and_(
            EpisodicMemory.user_id == user_id,
            EpisodicMemory.event_time >= cutoff_date
        )
    ).order_by(EpisodicMemory.event_time.desc())
    
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_episodes_by_emotion(
    db: AsyncSession,
    user_id: str,
    emotion: str,
    limit: Optional[int] = None
) -> List[EpisodicMemory]:
    """
    Get episodes by emotion type.
    
    Args:
        db: Database session
        user_id: User identifier
        emotion: Emotion to filter by
        limit: Optional limit on results
    
    Returns:
        List of EpisodicMemory objects
    """
    query = select(EpisodicMemory).where(
        and_(
            EpisodicMemory.user_id == user_id,
            EpisodicMemory.emotion == emotion
        )
    ).order_by(EpisodicMemory.event_time.desc())
    
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_episodes_by_importance(
    db: AsyncSession,
    user_id: str,
    min_importance: int,
    limit: Optional[int] = None
) -> List[EpisodicMemory]:
    """
    Get episodes by importance threshold.
    
    Args:
        db: Database session
        user_id: User identifier
        min_importance: Minimum importance score
        limit: Optional limit on results
    
    Returns:
        List of EpisodicMemory objects
    """
    query = select(EpisodicMemory).where(
        and_(
            EpisodicMemory.user_id == user_id,
            EpisodicMemory.importance >= min_importance
        )
    ).order_by(EpisodicMemory.importance.desc(), EpisodicMemory.event_time.desc())
    
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def delete_episodic_memory(
    db: AsyncSession,
    episode_id: int
) -> bool:
    """
    Delete episodic memory by ID.
    
    Args:
        db: Database session
        episode_id: Episode ID to delete
    
    Returns:
        True if deleted, False if not found
    """
    episodic_memory = await get_episodic_memory_by_id(db, episode_id)
    
    if not episodic_memory:
        return False
    
    try:
        await db.delete(episodic_memory)
        await db.commit()
        logger.info(f"Deleted episodic memory {episode_id}")
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting episodic memory: {e}")
        raise ValueError(f"Error deleting episodic memory: {str(e)}")


# ============================================================================
# Semantic Memory Sync Functions
# ============================================================================

async def get_users_with_unprocessed_episodes(
    db: AsyncSession
) -> List[str]:
    """
    Get distinct user IDs that have episodic memories not yet processed for semantic memory.
    
    Args:
        db: Database session
    
    Returns:
        List of user IDs with unprocessed episodes
    """
    query = select(EpisodicMemory.user_id).where(
        EpisodicMemory.used_for_semantic_memory == False
    ).distinct()
    
    result = await db.execute(query)
    return [row[0] for row in result.all()]


async def get_unprocessed_episodes_for_semantic(
    db: AsyncSession,
    user_id: str,
    limit: Optional[int] = None
) -> List[EpisodicMemory]:
    """
    Get episodic memories for a user that have not been processed for semantic memory.
    
    Args:
        db: Database session
        user_id: User identifier
        limit: Optional limit on results
    
    Returns:
        List of unprocessed EpisodicMemory objects
    """
    query = select(EpisodicMemory).where(
        and_(
            EpisodicMemory.user_id == user_id,
            EpisodicMemory.used_for_semantic_memory == False
        )
    ).order_by(EpisodicMemory.event_time.asc())  # Process oldest first
    
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def count_unprocessed_episodes_for_semantic(
    db: AsyncSession,
    user_id: str
) -> int:
    """
    Count episodic memories for a user that have not been processed for semantic memory.
    
    Args:
        db: Database session
        user_id: User identifier
    
    Returns:
        Count of unprocessed episodes
    """
    query = select(func.count(EpisodicMemory.id)).where(
        and_(
            EpisodicMemory.user_id == user_id,
            EpisodicMemory.used_for_semantic_memory == False
        )
    )
    
    result = await db.execute(query)
    return result.scalar_one()


async def mark_episodes_as_semantic_processed(
    db: AsyncSession,
    episode_ids: List[int]
) -> int:
    """
    Mark multiple episodes as having been processed for semantic memory.
    
    Args:
        db: Database session
        episode_ids: List of episode IDs to mark as processed
    
    Returns:
        Number of episodes updated
    """
    if not episode_ids:
        return 0
    
    try:
        stmt = (
            update(EpisodicMemory)
            .where(EpisodicMemory.id.in_(episode_ids))
            .values(
                used_for_semantic_memory=True,
                updated_at=func.now()
            )
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        updated_count = result.rowcount
        logger.info(f"Marked {updated_count} episodes as processed for semantic memory")
        return updated_count
    except Exception as e:
        await db.rollback()
        logger.error(f"Error marking episodes as semantic processed: {e}")
        raise ValueError(f"Error marking episodes as semantic processed: {str(e)}")

