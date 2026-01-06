"""
Redis Cache Layer for Episodic Memory.
Caches recent episodes for fast access and similarity search results.
"""
import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from redis.asyncio import Redis
import logging

from app.db.redis_config import get_redis
from app.schemas.pydantic_schemas.memory.episodic import EpisodicMemoryResponse

logger = logging.getLogger(__name__)

# Cache TTL configuration
CACHE_TTL_HOURS = int(os.getenv("EPISODIC_MEMORY_CACHE_TTL_HOURS", "48"))
CACHE_SEARCH_TTL_MINUTES = int(os.getenv("EPISODIC_MEMORY_CACHE_SEARCH_TTL_MINUTES", "5"))
CACHE_TTL_SECONDS = CACHE_TTL_HOURS * 60 * 60
CACHE_SEARCH_TTL_SECONDS = CACHE_SEARCH_TTL_MINUTES * 60


class EpisodicMemoryCache:
    """
    Redis cache for episodic memory.
    Caches recent episodes and similarity search results.
    """
    
    KEY_PREFIX_EPISODES = "episodic_memory:episodes"
    KEY_PREFIX_RECENT = "episodic_memory:recent"
    KEY_PREFIX_SEARCH = "episodic_memory:search"
    
    def __init__(self, redis: Optional[Redis] = None):
        """
        Initialize episodic memory cache.
        
        Args:
            redis: Optional Redis client. If not provided, will use get_redis().
        """
        self._redis = redis
    
    async def _get_redis(self) -> Redis:
        """Get Redis client instance."""
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis
    
    def _get_episode_key(self, user_id: str, episode_id: int) -> str:
        """Generate Redis key for a specific episode."""
        return f"{self.KEY_PREFIX_EPISODES}:{user_id}:{episode_id}"
    
    def _get_recent_key(self, user_id: str) -> str:
        """Generate Redis key for recent episodes list."""
        return f"{self.KEY_PREFIX_RECENT}:{user_id}"
    
    def _get_search_key(self, user_id: str, query_hash: str) -> str:
        """Generate Redis key for search results."""
        return f"{self.KEY_PREFIX_SEARCH}:{user_id}:{query_hash}"
    
    async def cache_recent_episode(
        self,
        user_id: str,
        episode: Dict[str, Any]
    ) -> bool:
        """
        Cache a recent episode in Redis.
        
        Args:
            user_id: User identifier
            episode: Episode data (dict or EpisodicMemoryResponse)
        
        Returns:
            True if cached successfully
        """
        try:
            redis = await self._get_redis()
            
            # Convert episode to dict if needed
            if isinstance(episode, EpisodicMemoryResponse):
                episode_dict = episode.model_dump()
            else:
                episode_dict = episode
            
            episode_id = episode_dict.get("id")
            if not episode_id:
                logger.warning("Episode missing id, cannot cache")
                return False
            
            # Cache individual episode
            episode_key = self._get_episode_key(user_id, episode_id)
            await redis.setex(
                episode_key,
                CACHE_TTL_SECONDS,
                json.dumps(episode_dict, default=str)
            )
            
            # Add to recent episodes list (sorted set by event_time)
            recent_key = self._get_recent_key(user_id)
            event_time = episode_dict.get("event_time")
            if event_time:
                # Convert datetime to timestamp for sorting
                if isinstance(event_time, str):
                    event_time = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
                timestamp = event_time.timestamp() if isinstance(event_time, datetime) else float(event_time)
                
                await redis.zadd(
                    recent_key,
                    {str(episode_id): timestamp}
                )
                await redis.expire(recent_key, CACHE_TTL_SECONDS)
            
            logger.debug(f"Cached episode {episode_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error caching episode: {e}")
            return False
    
    async def get_cached_episodes(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent episodes from cache.
        
        Args:
            user_id: User identifier
            limit: Optional limit on number of episodes
        
        Returns:
            List of episode dictionaries
        """
        try:
            redis = await self._get_redis()
            recent_key = self._get_recent_key(user_id)
            
            # Get recent episode IDs (sorted by time, descending)
            if limit:
                episode_ids = await redis.zrevrange(recent_key, 0, limit - 1)
            else:
                episode_ids = await redis.zrevrange(recent_key, 0, -1)
            
            if not episode_ids:
                return []
            
            # Fetch individual episodes
            episodes = []
            for episode_id_str in episode_ids:
                episode_key = self._get_episode_key(user_id, int(episode_id_str))
                episode_json = await redis.get(episode_key)
                
                if episode_json:
                    try:
                        episode_dict = json.loads(episode_json)
                        episodes.append(episode_dict)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse cached episode {episode_id_str}")
                        continue
            
            logger.debug(f"Retrieved {len(episodes)} cached episodes for user {user_id}")
            return episodes
        except Exception as e:
            logger.error(f"Error retrieving cached episodes: {e}")
            return []
    
    async def get_cached_similar(
        self,
        user_id: str,
        query_hash: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached similarity search results.
        
        Args:
            user_id: User identifier
            query_hash: Hash of the search query (for cache key)
        
        Returns:
            Cached search results or None if not found
        """
        try:
            redis = await self._get_redis()
            search_key = self._get_search_key(user_id, query_hash)
            
            cached_json = await redis.get(search_key)
            if cached_json:
                results = json.loads(cached_json)
                logger.debug(f"Retrieved cached search results for user {user_id}")
                return results
            
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached search results: {e}")
            return None
    
    async def cache_similar_results(
        self,
        user_id: str,
        query_hash: str,
        results: List[Dict[str, Any]]
    ) -> bool:
        """
        Cache similarity search results.
        
        Args:
            user_id: User identifier
            query_hash: Hash of the search query
            results: Search results to cache
        
        Returns:
            True if cached successfully
        """
        try:
            redis = await self._get_redis()
            search_key = self._get_search_key(user_id, query_hash)
            
            await redis.setex(
                search_key,
                CACHE_SEARCH_TTL_SECONDS,
                json.dumps(results, default=str)
            )
            
            logger.debug(f"Cached search results for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error caching search results: {e}")
            return False
    
    async def invalidate_user_cache(self, user_id: str) -> bool:
        """
        Invalidate all cache entries for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if invalidated successfully
        """
        try:
            redis = await self._get_redis()
            
            # Get all keys for this user
            pattern_episodes = f"{self.KEY_PREFIX_EPISODES}:{user_id}:*"
            pattern_recent = f"{self.KEY_PREFIX_RECENT}:{user_id}"
            pattern_search = f"{self.KEY_PREFIX_SEARCH}:{user_id}:*"
            
            # Delete keys
            async for key in redis.scan_iter(match=pattern_episodes):
                await redis.delete(key)
            
            await redis.delete(pattern_recent)
            
            async for key in redis.scan_iter(match=pattern_search):
                await redis.delete(key)
            
            logger.info(f"Invalidated cache for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False


# Global cache instance
_episodic_memory_cache: Optional[EpisodicMemoryCache] = None


def get_episodic_memory_cache() -> EpisodicMemoryCache:
    """
    Get or create global episodic memory cache instance.
    
    Returns:
        EpisodicMemoryCache instance
    """
    global _episodic_memory_cache
    if _episodic_memory_cache is None:
        _episodic_memory_cache = EpisodicMemoryCache()
    return _episodic_memory_cache

