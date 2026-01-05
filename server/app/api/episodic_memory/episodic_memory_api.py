"""
Episodic Memory API routes.
Handles episodic memory extraction, retrieval, and search endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime
import hashlib
import logging

from app.db.my_sql_config import get_db
from app.services.memory_manager import MemoryManager, get_memory_manager
from app.services.episodic_memory_processor import get_episodic_memory_processor
from app.services.episodic_memory_cache import get_episodic_memory_cache
from app.services.embedding_service import get_embedding_service
from app.db.crud.episodic_memory_crud import (
    get_episodic_memories_by_user,
    get_recent_episodic_memories,
    search_episodes_by_context,
    delete_episodic_memory,
    get_episodic_memory_by_id
)
from app.schemas.pydantic_schemas.episodic_memory_schema import (
    EpisodicMemoryResponse,
    EpisodicMemorySearchRequest,
    EpisodicMemoryFilters,
    EpisodicMemoryExtractionRequest
)

logger = logging.getLogger(__name__)

episodic_memory_router = APIRouter(tags=["Episodic Memory"])


@episodic_memory_router.post("/extract/{user_id}", response_model=dict)
async def extract_episodic_memory(
    user_id: str = Path(..., description="User identifier"),
    request: Optional[EpisodicMemoryExtractionRequest] = None,
    db: AsyncSession = Depends(get_db),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """
    Manually trigger episodic memory extraction for a user.
    
    Args:
        user_id: User identifier
        request: Optional extraction request with parameters
        db: Database session
        memory_manager: Memory manager instance
    
    Returns:
        Processing results
    """
    try:
        processor = get_episodic_memory_processor()
        
        result = await processor.process_user_episodes(
            db=db,
            user_id=user_id,
            memory_manager=memory_manager,
            lookback_days=request.lookback_days if request else None,
            min_importance=request.min_importance if request else None
        )
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("message", "Extraction failed"))
    except Exception as e:
        logger.error(f"Error extracting episodic memory: {e}")
        raise HTTPException(status_code=500, detail=f"Error extracting episodic memory: {str(e)}")


@episodic_memory_router.get("/{user_id}", response_model=List[EpisodicMemoryResponse])
async def get_episodic_memories(
    user_id: str = Path(..., description="User identifier"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    emotion: Optional[str] = Query(None, description="Filter by emotion"),
    min_importance: Optional[int] = Query(None, ge=1, le=10, description="Minimum importance"),
    max_importance: Optional[int] = Query(None, ge=1, le=10, description="Maximum importance"),
    limit: Optional[int] = Query(10, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get episodic memories for a user with optional filters.
    Uses pure SQL filtering (no vector search).
    
    Args:
        user_id: User identifier
        date_from: Filter episodes from this date
        date_to: Filter episodes until this date
        emotion: Filter by emotion
        min_importance: Minimum importance score
        max_importance: Maximum importance score
        limit: Maximum number of results
        offset: Offset for pagination
        db: Database session
    
    Returns:
        List of episodic memories
    """
    try:
        filters = None
        if any([date_from, date_to, emotion, min_importance, max_importance]):
            filters = EpisodicMemoryFilters(
                date_from=date_from,
                date_to=date_to,
                emotion=emotion,
                min_importance=min_importance,
                max_importance=max_importance
            )
        
        episodes = await get_episodic_memories_by_user(
            db=db,
            user_id=user_id,
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        return [EpisodicMemoryResponse.model_validate(ep) for ep in episodes]
    except Exception as e:
        logger.error(f"Error getting episodic memories: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting episodic memories: {str(e)}")


@episodic_memory_router.post("/{user_id}/search", response_model=List[dict])
async def search_episodic_memories(
    user_id: str = Path(..., description="User identifier"),
    request: EpisodicMemorySearchRequest = ...,
    db: AsyncSession = Depends(get_db)
):
    """
    Hybrid search: Find similar episodic memories using vector similarity + SQL filters.
    
    Args:
        user_id: User identifier
        request: Search request with query text and filters
        db: Database session
    
    Returns:
        List of episodes with similarity scores
    """
    try:
        cache = get_episodic_memory_cache()
        
        # Create cache key from query
        cache_key = hashlib.md5(
            f"{user_id}:{request.query_text}:{request.similarity_threshold}:{request.filters}".encode()
        ).hexdigest()
        
        # Try cache first
        cached_results = await cache.get_cached_similar(user_id, cache_key)
        if cached_results:
            logger.debug(f"Returning cached search results for user {user_id}")
            return cached_results
        
        # Perform hybrid search
        results = await search_episodes_by_context(
            db=db,
            query_text=request.query_text,
            user_id=user_id,
            similarity_threshold=request.similarity_threshold or 0.3,
            filters=request.filters,
            limit=request.limit or 10
        )
        
        # Cache results
        await cache.cache_similar_results(user_id, cache_key, results)
        
        return results
    except Exception as e:
        logger.error(f"Error searching episodic memories: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching episodic memories: {str(e)}")


@episodic_memory_router.get("/{user_id}/recent", response_model=List[EpisodicMemoryResponse])
async def get_recent_episodic_memories(
    user_id: str = Path(..., description="User identifier"),
    days: int = Query(2, ge=1, le=7, description="Number of days to look back"),
    limit: Optional[int] = Query(10, ge=1, le=100, description="Maximum results"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent episodic memories (from cache if available, otherwise from database).
    
    Args:
        user_id: User identifier
        days: Number of days to look back
        limit: Maximum number of results
        db: Database session
    
    Returns:
        List of recent episodic memories
    """
    try:
        cache = get_episodic_memory_cache()
        
        # Try cache first
        cached_episodes = await cache.get_cached_episodes(user_id, limit=limit)
        
        if cached_episodes and len(cached_episodes) >= limit:
            logger.debug(f"Returning {len(cached_episodes)} cached episodes for user {user_id}")
            return [EpisodicMemoryResponse.model_validate(ep) for ep in cached_episodes[:limit]]
        
        # Fallback to database
        episodes = await get_recent_episodic_memories(
            db=db,
            user_id=user_id,
            days=days,
            limit=limit
        )
        
        # Cache results
        for episode in episodes:
            await cache.cache_recent_episode(
                user_id=user_id,
                episode={
                    "id": episode.id,
                    "user_id": episode.user_id,
                    "event_description": episode.event_description,
                    "context": episode.context,
                    "emotion": episode.emotion,
                    "importance": episode.importance,
                    "event_time": episode.event_time.isoformat(),
                    "related_query_ids": episode.related_query_ids,
                    "additional_metadata": episode.additional_metadata,
                    "created_at": episode.created_at.isoformat(),
                    "updated_at": episode.updated_at.isoformat()
                }
            )
        
        return [EpisodicMemoryResponse.model_validate(ep) for ep in episodes]
    except Exception as e:
        logger.error(f"Error getting recent episodic memories: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting recent episodic memories: {str(e)}")


@episodic_memory_router.delete("/{episode_id}", response_model=dict)
async def delete_episodic_memory(
    episode_id: int = Path(..., description="Episode ID to delete"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a specific episodic memory.
    
    Args:
        episode_id: Episode ID to delete
        db: Database session
    
    Returns:
        Success message
    """
    try:
        # Get episode to get user_id for cache invalidation
        episode = await get_episodic_memory_by_id(db, episode_id)
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")
        
        # Delete from database
        from app.db.crud.episodic_memory_crud import delete_episodic_memory as crud_delete_episodic_memory
        deleted = await crud_delete_episodic_memory(db, episode_id)
        
        if deleted:
            # Invalidate cache
            cache = get_episodic_memory_cache()
            await cache.invalidate_user_cache(episode.user_id)
            
            return {"success": True, "message": f"Episode {episode_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Episode not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting episodic memory: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting episodic memory: {str(e)}")

