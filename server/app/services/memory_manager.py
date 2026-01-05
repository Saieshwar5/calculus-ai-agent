"""
Memory Manager Service for Short-term Memory Management.

Handles storing and retrieving recent conversation history (last 20 messages)
per user using Redis Lists.
"""
import json
import time
from typing import List, Optional
from redis.asyncio import Redis

from app.db.redis_config import get_redis, MEMORY_TTL_SECONDS
from app.schemas.pydantic_schemas.memory_schema import Message


class MemoryManager:
    """
    Manages short-term memory for AI agents using Redis.
    
    Stores conversation history as a Redis List with automatic trimming
    to keep only the last 20 messages per user.
    """
    
    MAX_MESSAGES = 20
    KEY_PREFIX = "short_term_memory"
    
    def __init__(self, redis: Optional[Redis] = None):
        """
        Initialize MemoryManager.
        
        Args:
            redis: Optional Redis client. If not provided, will use get_redis().
        """
        self._redis = redis
    
    async def _get_redis(self) -> Redis:
        """Get Redis client instance."""
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis
    
    def _get_key(self, user_id: str) -> str:
        """Generate Redis key for user's memory."""
        return f"{self.KEY_PREFIX}:{user_id}"
    
    async def add_message(
        self,
        user_id: str,
        role: str,
        content: str,
        timestamp: Optional[float] = None
    ) -> bool:
        """
        Add a message to user's short-term memory.
        
        Args:
            user_id: User identifier
            role: Message role ("user" or "assistant")
            content: Message content
            timestamp: Optional timestamp (defaults to current time)
        
        Returns:
            True if message was added successfully
        """
        try:
            redis = await self._get_redis()
            key = self._get_key(user_id)
            
            if timestamp is None:
                timestamp = time.time()
            
            message = Message(
                role=role,
                content=content,
                timestamp=timestamp
            )
            
            # Serialize message to JSON
            message_json = message.model_dump_json()
            
            # Add message to the front of the list (LPUSH)
            await redis.lpush(key, message_json)
            
            # Trim list to keep only last MAX_MESSAGES
            await redis.ltrim(key, 0, self.MAX_MESSAGES - 1)
            
            # Set or refresh TTL
            await redis.expire(key, MEMORY_TTL_SECONDS)
            
            return True
        except Exception as e:
            print(f"Error adding message to memory: {str(e)}")
            return False
    
    async def get_recent_messages(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """
        Retrieve recent messages from user's short-term memory.
        
        Args:
            user_id: User identifier
            limit: Optional limit on number of messages (defaults to MAX_MESSAGES)
        
        Returns:
            List of Message objects, ordered from oldest to newest
        """
        try:
            redis = await self._get_redis()
            key = self._get_key(user_id)
            
            if limit is None:
                limit = self.MAX_MESSAGES
            
            # Get all messages from the list (LRANGE 0 -1)
            messages_json = await redis.lrange(key, 0, -1)
            
            if not messages_json:
                return []
            
            # Parse JSON messages and reverse to get chronological order
            # (Redis List stores newest first due to LPUSH)
            messages = []
            for msg_json in reversed(messages_json):
                try:
                    msg_dict = json.loads(msg_json)
                    message = Message(**msg_dict)
                    messages.append(message)
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Error parsing message JSON: {str(e)}")
                    continue
            
            # Return only the requested limit (most recent)
            return messages[-limit:] if limit < len(messages) else messages
            
        except Exception as e:
            print(f"Error retrieving messages from memory: {str(e)}")
            return []
    
    async def clear_memory(self, user_id: str) -> bool:
        """
        Clear all messages from user's short-term memory.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if memory was cleared successfully
        """
        try:
            redis = await self._get_redis()
            key = self._get_key(user_id)
            
            deleted = await redis.delete(key)
            return deleted > 0
            
        except Exception as e:
            print(f"Error clearing memory: {str(e)}")
            return False
    
    async def get_message_count(self, user_id: str) -> int:
        """
        Get the number of messages stored for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            Number of messages in memory
        """
        try:
            redis = await self._get_redis()
            key = self._get_key(user_id)
            
            count = await redis.llen(key)
            return count
            
        except Exception as e:
            print(f"Error getting message count: {str(e)}")
            return 0
    
    async def get_memory_info(self, user_id: str) -> dict:
        """
        Get information about user's memory.
        
        Args:
            user_id: User identifier
        
        Returns:
            Dictionary with memory information
        """
        try:
            redis = await self._get_redis()
            key = self._get_key(user_id)
            
            count = await redis.llen(key)
            ttl = await redis.ttl(key)
            
            return {
                "user_id": user_id,
                "message_count": count,
                "max_messages": self.MAX_MESSAGES,
                "ttl_seconds": ttl if ttl > 0 else None,
            }
            
        except Exception as e:
            print(f"Error getting memory info: {str(e)}")
            return {
                "user_id": user_id,
                "message_count": 0,
                "max_messages": self.MAX_MESSAGES,
                "ttl_seconds": None,
            }


# Singleton instance (optional, can also use dependency injection)
_memory_manager: Optional[MemoryManager] = None


async def get_memory_manager() -> MemoryManager:
    """
    Get MemoryManager instance (singleton pattern).
    
    Usage in FastAPI routes:
        from app.services.memory_manager import get_memory_manager
        @app.get("/items")
        async def read_items(memory: MemoryManager = Depends(get_memory_manager)):
            ...
    """
    global _memory_manager
    
    if _memory_manager is None:
        redis = await get_redis()
        _memory_manager = MemoryManager(redis=redis)
    
    return _memory_manager

