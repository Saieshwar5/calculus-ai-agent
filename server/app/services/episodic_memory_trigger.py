"""
Episodic Memory Trigger Service.
Orchestrates the check and trigger of episodic memory processing based on query count.
"""
import os
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import asyncio

from app.db.my_sql_config import AsyncSessionLocal
from app.db.crud.query_crud import (
    count_unused_query_pairs,
    get_unused_query_pairs,
    mark_queries_as_used
)
from app.services.response_summarizer import get_response_summarizer
from app.services.episodic_memory_extractor import get_episodic_memory_extractor
from app.services.episodic_memory_cache import get_episodic_memory_cache
from app.db.crud.episodic_memory_crud import create_episodic_memory

logger = logging.getLogger(__name__)

# Configuration
EPISODIC_MEMORY_TRIGGER_COUNT = int(os.getenv("EPISODIC_MEMORY_TRIGGER_COUNT", "15"))
MIN_IMPORTANCE = int(os.getenv("EPISODIC_MEMORY_MIN_IMPORTANCE", "3"))


class EpisodicMemoryTrigger:
    """
    Orchestrates the check and trigger of episodic memory processing.
    Triggers when a user has 15+ unused query/response pairs.
    """
    
    def __init__(self):
        """Initialize episodic memory trigger."""
        self.summarizer = get_response_summarizer()
        self.extractor = get_episodic_memory_extractor()
        self.cache = get_episodic_memory_cache()
        self.trigger_count = EPISODIC_MEMORY_TRIGGER_COUNT
        self.min_importance = MIN_IMPORTANCE
    
    async def should_process(
        self,
        db: AsyncSession,
        user_id: str
    ) -> bool:
        """
        Check if we should trigger episodic memory processing for a user.
        
        Args:
            db: Database session
            user_id: User identifier
        
        Returns:
            True if user has >= trigger_count unused query/response pairs
        """
        try:
            count = await count_unused_query_pairs(db, user_id)
            should_trigger = count >= self.trigger_count
            
            if should_trigger:
                logger.info(f"User {user_id} has {count} unused query pairs, triggering processing")
            
            return should_trigger
        except Exception as e:
            logger.error(f"Error checking if should process for user {user_id}: {e}")
            return False
    
    async def check_and_process(
        self,
        db: AsyncSession,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Check if user has enough unused query/response pairs and process if so.
        
        Args:
            db: Database session
            user_id: User identifier
        
        Returns:
            Dictionary with processing results
        """
        try:
            # Check if we should process
            if not await self.should_process(db, user_id):
                return {
                    "success": True,
                    "user_id": user_id,
                    "processed": False,
                    "message": "Not enough unused query/response pairs"
                }
            
            # Get unused query pairs (limit to trigger_count)
            query_pairs = await get_unused_query_pairs(db, user_id, limit=self.trigger_count)
            
            if not query_pairs:
                return {
                    "success": True,
                    "user_id": user_id,
                    "processed": False,
                    "message": "No query pairs found"
                }
            
            logger.info(f"Processing {len(query_pairs)} query pairs for user {user_id}")
            
            # Summarize responses
            summarized_pairs = await self.summarizer.summarize_query_pairs(query_pairs)
            
            # Convert to conversation format
            conversations = self.summarizer.convert_to_conversations(summarized_pairs)
            
            if not conversations:
                return {
                    "success": True,
                    "user_id": user_id,
                    "processed": False,
                    "message": "No conversations after summarization"
                }
            
            # Extract episodes from summarized conversations
            episodes = await self.extractor.extract_episodes_from_conversations(
                conversations=conversations,
                user_id=user_id,
                min_importance=self.min_importance
            )
            
            if not episodes:
                # Mark queries as used even if no episodes extracted
                # (to avoid re-processing the same queries)
                query_ids = [q.id for q in query_pairs]
                await mark_queries_as_used(db, query_ids)
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "processed": True,
                    "episodes_created": 0,
                    "queries_marked": len(query_ids),
                    "message": "No episodes extracted (below importance threshold)"
                }
            
            # Generate embeddings and save episodes
            embeddings = await self.extractor.generate_embeddings_for_episodes(episodes)
            
            created_count = 0
            for episode, embedding in zip(episodes, embeddings):
                if embedding is None:
                    logger.warning(f"Skipping episode without embedding: {episode.event_description[:50]}")
                    continue
                
                try:
                    # Create episode in database
                    created_episode = await create_episodic_memory(
                        db=db,
                        episode_data=episode,
                        embedding=embedding
                    )
                    
                    # Cache recent episode in Redis
                    await self.cache.cache_recent_episode(
                        user_id=user_id,
                        episode={
                            "id": created_episode.id,
                            "user_id": created_episode.user_id,
                            "event_description": created_episode.event_description,
                            "context": created_episode.context,
                            "emotion": created_episode.emotion,
                            "importance": created_episode.importance,
                            "event_time": created_episode.event_time.isoformat(),
                            "related_query_ids": created_episode.related_query_ids,
                            "additional_metadata": created_episode.additional_metadata,
                            "created_at": created_episode.created_at.isoformat(),
                            "updated_at": created_episode.updated_at.isoformat()
                        }
                    )
                    
                    created_count += 1
                    logger.debug(f"Created episode {created_episode.id} for user {user_id}")
                except Exception as e:
                    logger.error(f"Error saving episode: {e}")
                    continue
            
            # Mark queries as used after successful processing
            query_ids = [q.id for q in query_pairs]
            await mark_queries_as_used(db, query_ids)
            
            logger.info(f"Processed {created_count} episodes for user {user_id}, marked {len(query_ids)} queries as used")
            
            return {
                "success": True,
                "user_id": user_id,
                "processed": True,
                "episodes_created": created_count,
                "queries_marked": len(query_ids),
                "message": f"Successfully created {created_count} episodes from {len(query_pairs)} query pairs"
            }
            
        except Exception as e:
            logger.error(f"Error in check_and_process for user {user_id}: {e}")
            return {
                "success": False,
                "user_id": user_id,
                "processed": False,
                "message": f"Error processing: {str(e)}"
            }
    
    async def check_and_process_async(
        self,
        user_id: str
    ) -> None:
        """
        Async wrapper for check_and_process that runs in background.
        Creates its own database session to avoid conflicts with request session.
        Does not block the main request.
        
        Args:
            user_id: User identifier
        """
        try:
            # Create a new database session for this background task
            # This prevents conflicts with the request session which may be closed
            async with AsyncSessionLocal() as db:
                result = await self.check_and_process(db, user_id)
                if result.get("processed"):
                    logger.info(f"Background episodic memory processing completed: {result}")
        except Exception as e:
            logger.error(f"Error in background episodic memory processing: {e}")


# Global trigger instance
_episodic_memory_trigger: Optional[EpisodicMemoryTrigger] = None


def get_episodic_memory_trigger() -> EpisodicMemoryTrigger:
    """
    Get or create global episodic memory trigger instance.
    
    Returns:
        EpisodicMemoryTrigger instance
    """
    global _episodic_memory_trigger
    if _episodic_memory_trigger is None:
        _episodic_memory_trigger = EpisodicMemoryTrigger()
    return _episodic_memory_trigger

