"""
Episodic Memory Processor for batch processing.
Processes user conversations to extract and save episodic memories.
Now uses query-count-based triggering instead of time-based.
"""
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.services.episodic_memory_extractor import get_episodic_memory_extractor
from app.services.episodic_memory_cache import get_episodic_memory_cache
from app.services.response_summarizer import get_response_summarizer
from app.db.crud.episodic_memory_crud import create_episodic_memory
from app.db.crud.query_crud import (
    get_queries_by_user_id,
    get_unused_query_pairs,
    count_unused_query_pairs,
    mark_queries_as_used
)
from app.models.query_model import Query
from app.services.memory_manager import MemoryManager
from app.schemas.pydantic_schemas.episodic_memory_schema import EpisodicMemoryExtractionRequest

logger = logging.getLogger(__name__)

# Configuration
LOOKBACK_DAYS = int(os.getenv("EPISODIC_MEMORY_LOOKBACK_DAYS", "7"))
MIN_IMPORTANCE = int(os.getenv("EPISODIC_MEMORY_MIN_IMPORTANCE", "3"))
EPISODIC_MEMORY_TRIGGER_COUNT = int(os.getenv("EPISODIC_MEMORY_TRIGGER_COUNT", "15"))


class EpisodicMemoryProcessor:
    """
    Processes user conversations to extract and save episodic memories.
    Supports both query-count-based triggering and legacy time-based processing.
    """
    
    def __init__(self):
        """Initialize episodic memory processor."""
        self.extractor = get_episodic_memory_extractor()
        self.cache = get_episodic_memory_cache()
        self.summarizer = get_response_summarizer()
        self.trigger_count = EPISODIC_MEMORY_TRIGGER_COUNT
    
    async def process_user_episodes(
        self,
        db: AsyncSession,
        user_id: str,
        memory_manager: Optional[MemoryManager] = None,
        lookback_days: Optional[int] = None,
        min_importance: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process episodes for a single user.
        
        Args:
            db: Database session
            user_id: User identifier
            memory_manager: Optional memory manager for Redis conversations
            lookback_days: How many days back to analyze (default: from env or 7)
            min_importance: Minimum importance to save (default: from env or 3)
        
        Returns:
            Dictionary with processing results
        """
        lookback = lookback_days or LOOKBACK_DAYS
        min_imp = min_importance or MIN_IMPORTANCE
        
        try:
            logger.info(f"Processing episodic memories for user {user_id} (lookback: {lookback} days)")
            
            # Get conversations from multiple sources
            conversations = await self._get_user_conversations(
                db=db,
                user_id=user_id,
                memory_manager=memory_manager,
                lookback_days=lookback
            )
            
            if not conversations:
                logger.info(f"No conversations found for user {user_id}")
                return {
                    "success": True,
                    "user_id": user_id,
                    "episodes_created": 0,
                    "message": "No conversations to process"
                }
            
            # Extract episodes from conversations
            episodes = await self.extractor.extract_episodes_from_conversations(
                conversations=conversations,
                user_id=user_id,
                min_importance=min_imp
            )
            
            if not episodes:
                logger.info(f"No episodes extracted for user {user_id}")
                return {
                    "success": True,
                    "user_id": user_id,
                    "episodes_created": 0,
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
            
            logger.info(f"Processed {created_count} episodes for user {user_id}")
            return {
                "success": True,
                "user_id": user_id,
                "episodes_created": created_count,
                "conversations_analyzed": len(conversations),
                "message": f"Successfully created {created_count} episodes"
            }
        except Exception as e:
            logger.error(f"Error processing episodes for user {user_id}: {e}")
            return {
                "success": False,
                "user_id": user_id,
                "episodes_created": 0,
                "message": f"Error processing: {str(e)}"
            }
    
    async def process_unused_queries(
        self,
        db: AsyncSession,
        user_id: str,
        min_importance: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process unused query/response pairs for a user.
        This is the query-count-based approach (triggered after 15 unused pairs).
        
        Args:
            db: Database session
            user_id: User identifier
            min_importance: Minimum importance to save (default: from env or 3)
        
        Returns:
            Dictionary with processing results
        """
        min_imp = min_importance or MIN_IMPORTANCE
        
        try:
            # Check if we have enough unused pairs
            count = await count_unused_query_pairs(db, user_id)
            
            if count < self.trigger_count:
                logger.info(f"User {user_id} has {count} unused pairs, need {self.trigger_count}")
                return {
                    "success": True,
                    "user_id": user_id,
                    "episodes_created": 0,
                    "message": f"Not enough unused pairs ({count}/{self.trigger_count})"
                }
            
            # Get unused query pairs
            query_pairs = await get_unused_query_pairs(db, user_id, limit=self.trigger_count)
            
            if not query_pairs:
                return {
                    "success": True,
                    "user_id": user_id,
                    "episodes_created": 0,
                    "message": "No unused query pairs found"
                }
            
            logger.info(f"Processing {len(query_pairs)} unused query pairs for user {user_id}")
            
            # Summarize responses before extraction
            summarized_pairs = await self.summarizer.summarize_query_pairs(query_pairs)
            
            # Convert to conversation format
            conversations = self.summarizer.convert_to_conversations(summarized_pairs)
            
            if not conversations:
                # Mark as used even if no conversations (to avoid re-processing)
                query_ids = [q.id for q in query_pairs]
                await mark_queries_as_used(db, query_ids)
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "episodes_created": 0,
                    "queries_marked": len(query_ids),
                    "message": "No conversations after summarization"
                }
            
            # Extract episodes from summarized conversations
            episodes = await self.extractor.extract_episodes_from_conversations(
                conversations=conversations,
                user_id=user_id,
                min_importance=min_imp
            )
            
            query_ids = [q.id for q in query_pairs]
            
            if not episodes:
                # Mark as used even if no episodes extracted
                await mark_queries_as_used(db, query_ids)
                
                return {
                    "success": True,
                    "user_id": user_id,
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
            await mark_queries_as_used(db, query_ids)
            
            logger.info(f"Processed {created_count} episodes from {len(query_pairs)} query pairs for user {user_id}")
            return {
                "success": True,
                "user_id": user_id,
                "episodes_created": created_count,
                "queries_processed": len(query_pairs),
                "queries_marked": len(query_ids),
                "message": f"Successfully created {created_count} episodes from {len(query_pairs)} query pairs"
            }
            
        except Exception as e:
            logger.error(f"Error processing unused queries for user {user_id}: {e}")
            return {
                "success": False,
                "user_id": user_id,
                "episodes_created": 0,
                "message": f"Error processing: {str(e)}"
            }
    
    async def _get_user_conversations(
        self,
        db: AsyncSession,
        user_id: str,
        memory_manager: Optional[MemoryManager],
        lookback_days: int
    ) -> List[Dict[str, Any]]:
        """
        Get user conversations from multiple sources (Redis and PostgreSQL).
        
        Args:
            db: Database session
            user_id: User identifier
            memory_manager: Optional memory manager for Redis
            lookback_days: How many days back to look
        
        Returns:
            List of conversation dictionaries
        """
        conversations = []
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        
        # Get conversations from Redis (short-term memory)
        if memory_manager:
            try:
                recent_messages = await memory_manager.get_recent_messages(user_id, limit=20)
                for msg in recent_messages:
                    conversations.append({
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat() if hasattr(msg.timestamp, 'isoformat') else str(msg.timestamp)
                    })
            except Exception as e:
                logger.warning(f"Error getting Redis conversations: {e}")
        
        # Get conversations from PostgreSQL (Query table)
        try:
            query = select(Query).where(
                Query.user_id == user_id,
                Query.created_at >= cutoff_date
            ).order_by(Query.created_at.desc())
            
            result = await db.execute(query)
            queries = result.scalars().all()
            
            for query_obj in queries:
                if query_obj.query_text:
                    conversations.append({
                        "role": "user",
                        "content": query_obj.query_text,
                        "timestamp": query_obj.created_at.isoformat()
                    })
                if query_obj.response_text:
                    conversations.append({
                        "role": "assistant",
                        "content": query_obj.response_text,
                        "timestamp": query_obj.updated_at.isoformat()
                    })
        except Exception as e:
            logger.warning(f"Error getting PostgreSQL conversations: {e}")
        
        # Sort by timestamp
        conversations.sort(key=lambda x: x.get("timestamp", ""))
        
        return conversations
    
    async def process_all_users(
        self,
        db: AsyncSession,
        memory_manager: Optional[MemoryManager] = None,
        lookback_days: Optional[int] = None,
        min_importance: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process episodes for all active users.
        
        Args:
            db: Database session
            memory_manager: Optional memory manager
            lookback_days: How many days back to analyze
            min_importance: Minimum importance to save
        
        Returns:
            Dictionary with processing results
        """
        try:
            # Get all unique user IDs from Query table
            query = select(Query.user_id).distinct()
            result = await db.execute(query)
            user_ids = [row[0] for row in result.all()]
            
            logger.info(f"Processing episodic memories for {len(user_ids)} users")
            
            results = []
            for user_id in user_ids:
                result = await self.process_user_episodes(
                    db=db,
                    user_id=user_id,
                    memory_manager=memory_manager,
                    lookback_days=lookback_days,
                    min_importance=min_importance
                )
                results.append(result)
            
            total_created = sum(r.get("episodes_created", 0) for r in results)
            
            return {
                "success": True,
                "users_processed": len(user_ids),
                "total_episodes_created": total_created,
                "results": results
            }
        except Exception as e:
            logger.error(f"Error processing all users: {e}")
            return {
                "success": False,
                "message": f"Error processing all users: {str(e)}"
            }


# Global processor instance
_episodic_memory_processor: Optional[EpisodicMemoryProcessor] = None


def get_episodic_memory_processor() -> EpisodicMemoryProcessor:
    """
    Get or create global episodic memory processor instance.
    
    Returns:
        EpisodicMemoryProcessor instance
    """
    global _episodic_memory_processor
    if _episodic_memory_processor is None:
        _episodic_memory_processor = EpisodicMemoryProcessor()
    return _episodic_memory_processor

