"""
Subject-based Short-term Memory Manager.

Manages conversation history per user per subject in Redis.
This allows the AI agent to maintain separate context for different
learning topics the user is studying.

Redis Key Format: learning:stm:{user_id}:{subject_id}
"""
import json
import time
import logging
from typing import List, Optional, Dict, Any
from redis.asyncio import Redis

from app.db.redis_config import get_redis, MEMORY_TTL_SECONDS
from app.context.schemas.context import SubjectMessage

logger = logging.getLogger(__name__)


class SubjectShortTermMemory:
    """
    Manages short-term memory for learning AI agents per user per subject.
    
    Features:
    - Separate conversation history per subject
    - Automatic trimming to keep memory bounded
    - TTL to expire inactive conversations
    - Message metadata for topic tracking
    - List all active subjects for a user
    """
    
    MAX_MESSAGES = 30
    KEY_PREFIX = "learning:stm"
    SUBJECT_INDEX_PREFIX = "learning:subjects"
    
    def __init__(self, redis: Optional[Redis] = None, max_messages: int = 30):
        """
        Initialize SubjectShortTermMemory.
        
        Args:
            redis: Optional Redis client. If not provided, will use get_redis().
            max_messages: Maximum messages to keep per subject (default: 30)
        """
        self._redis = redis
        self.MAX_MESSAGES = max_messages
    
    async def _get_redis(self) -> Redis:
        """Get Redis client instance."""
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis
    
    def _normalize_subject(self, subject: str) -> str:
        """
        Normalize subject name to a consistent format.
        
        Args:
            subject: Subject name (e.g., "Machine Learning", "calculus")
        
        Returns:
            Normalized subject ID (e.g., "machine_learning", "calculus")
        """
        return subject.lower().strip().replace(" ", "_").replace("-", "_")
    
    def _get_key(self, user_id: str, subject: str) -> str:
        """
        Generate Redis key for user's subject-specific memory.
        
        Args:
            user_id: User identifier
            subject: Learning subject/topic
        
        Returns:
            Redis key string
        """
        normalized_subject = self._normalize_subject(subject)
        return f"{self.KEY_PREFIX}:{user_id}:{normalized_subject}"
    
    def _get_subject_index_key(self, user_id: str) -> str:
        """
        Generate Redis key for user's subject index.
        
        Args:
            user_id: User identifier
        
        Returns:
            Redis key for subject index set
        """
        return f"{self.SUBJECT_INDEX_PREFIX}:{user_id}"
    
    async def add_message(
        self,
        user_id: str,
        subject: str,
        role: str,
        content: str,
        timestamp: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a message to user's subject-specific short-term memory.
        
        Args:
            user_id: User identifier
            subject: Learning subject/topic (e.g., "Python", "Calculus")
            role: Message role ("user" or "assistant")
            content: Message content
            timestamp: Optional timestamp (defaults to current time)
            metadata: Optional metadata (topic_focus, difficulty_level, interaction_type)
        
        Returns:
            True if message was added successfully
        """
        try:
            redis = await self._get_redis()
            key = self._get_key(user_id, subject)
            subject_index_key = self._get_subject_index_key(user_id)
            
            if timestamp is None:
                timestamp = time.time()
            
            # Create message
            message = SubjectMessage(
                role=role,
                content=content,
                timestamp=timestamp,
                metadata=metadata or {}
            )
            
            # Serialize message to JSON
            message_json = message.model_dump_json()
            
            # Add message to the front of the list (LPUSH)
            await redis.lpush(key, message_json)
            
            # Trim list to keep only last MAX_MESSAGES
            await redis.ltrim(key, 0, self.MAX_MESSAGES - 1)
            
            # Set or refresh TTL
            await redis.expire(key, MEMORY_TTL_SECONDS)
            
            # Add subject to user's subject index
            normalized_subject = self._normalize_subject(subject)
            await redis.sadd(subject_index_key, normalized_subject)
            await redis.expire(subject_index_key, MEMORY_TTL_SECONDS)
            
            logger.debug(f"Added message for user {user_id} in subject {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding message to subject memory: {str(e)}")
            return False
    
    async def get_recent_messages(
        self,
        user_id: str,
        subject: str,
        limit: Optional[int] = None
    ) -> List[SubjectMessage]:
        """
        Retrieve recent messages from user's subject-specific short-term memory.
        
        Args:
            user_id: User identifier
            subject: Learning subject/topic
            limit: Optional limit on number of messages (defaults to MAX_MESSAGES)
        
        Returns:
            List of SubjectMessage objects, ordered from oldest to newest
        """
        try:
            redis = await self._get_redis()
            key = self._get_key(user_id, subject)
            
            if limit is None:
                limit = self.MAX_MESSAGES
            
            # Get messages from the list
            messages_json = await redis.lrange(key, 0, limit - 1)
            
            if not messages_json:
                return []
            
            # Parse JSON messages and reverse to get chronological order
            # (Redis List stores newest first due to LPUSH)
            messages = []
            for msg_json in reversed(messages_json):
                try:
                    msg_dict = json.loads(msg_json)
                    message = SubjectMessage(**msg_dict)
                    messages.append(message)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Error parsing message JSON: {str(e)}")
                    continue
            
            return messages
            
        except Exception as e:
            logger.error(f"Error retrieving messages from subject memory: {str(e)}")
            return []
    
    async def get_conversation_for_ai(
        self,
        user_id: str,
        subject: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Get conversation formatted for AI API calls.
        
        Args:
            user_id: User identifier
            subject: Learning subject/topic
            limit: Optional limit on messages
        
        Returns:
            List of dicts with 'role' and 'content' keys
        """
        messages = await self.get_recent_messages(user_id, subject, limit)
        return [{"role": msg.role, "content": msg.content} for msg in messages]
    
    async def clear_memory(self, user_id: str, subject: str) -> bool:
        """
        Clear all messages from user's subject-specific short-term memory.
        
        Args:
            user_id: User identifier
            subject: Learning subject/topic
        
        Returns:
            True if memory was cleared successfully
        """
        try:
            redis = await self._get_redis()
            key = self._get_key(user_id, subject)
            subject_index_key = self._get_subject_index_key(user_id)
            
            deleted = await redis.delete(key)
            
            # Remove from subject index
            normalized_subject = self._normalize_subject(subject)
            await redis.srem(subject_index_key, normalized_subject)
            
            logger.info(f"Cleared memory for user {user_id} in subject {subject}")
            return deleted > 0
            
        except Exception as e:
            logger.error(f"Error clearing subject memory: {str(e)}")
            return False
    
    async def get_active_subjects(self, user_id: str) -> List[str]:
        """
        Get list of all subjects that have active memory for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            List of subject names (normalized format)
        """
        try:
            redis = await self._get_redis()
            subject_index_key = self._get_subject_index_key(user_id)
            
            # Get all subjects from the set
            subjects = await redis.smembers(subject_index_key)
            
            return list(subjects) if subjects else []
            
        except Exception as e:
            logger.error(f"Error getting active subjects: {str(e)}")
            return []
    
    async def get_message_count(self, user_id: str, subject: str) -> int:
        """
        Get the number of messages stored for a user-subject pair.
        
        Args:
            user_id: User identifier
            subject: Learning subject/topic
        
        Returns:
            Number of messages in memory
        """
        try:
            redis = await self._get_redis()
            key = self._get_key(user_id, subject)
            
            count = await redis.llen(key)
            return count
            
        except Exception as e:
            logger.error(f"Error getting message count: {str(e)}")
            return 0
    
    async def get_memory_info(self, user_id: str, subject: str) -> Dict[str, Any]:
        """
        Get information about user's subject-specific memory.
        
        Args:
            user_id: User identifier
            subject: Learning subject/topic
        
        Returns:
            Dictionary with memory information
        """
        try:
            redis = await self._get_redis()
            key = self._get_key(user_id, subject)
            
            count = await redis.llen(key)
            ttl = await redis.ttl(key)
            
            # Get first and last message timestamps
            messages = await self.get_recent_messages(user_id, subject, limit=1)
            last_message_time = messages[-1].timestamp if messages else None
            
            # Get first message (oldest)
            all_messages = await self.get_recent_messages(user_id, subject)
            first_message_time = all_messages[0].timestamp if all_messages else None
            
            # Calculate session duration
            session_duration = None
            if first_message_time and last_message_time:
                session_duration = (last_message_time - first_message_time) / 60  # minutes
            
            return {
                "user_id": user_id,
                "subject": subject,
                "message_count": count,
                "max_messages": self.MAX_MESSAGES,
                "ttl_seconds": ttl if ttl > 0 else None,
                "session_start": first_message_time,
                "last_activity": last_message_time,
                "session_duration_minutes": session_duration,
            }
            
        except Exception as e:
            logger.error(f"Error getting memory info: {str(e)}")
            return {
                "user_id": user_id,
                "subject": subject,
                "message_count": 0,
                "max_messages": self.MAX_MESSAGES,
                "ttl_seconds": None,
                "session_start": None,
                "last_activity": None,
                "session_duration_minutes": None,
            }
    
    async def get_current_topic_focus(self, user_id: str, subject: str) -> Optional[str]:
        """
        Get the current topic focus from recent messages.
        
        Args:
            user_id: User identifier
            subject: Learning subject/topic
        
        Returns:
            Current topic focus or None
        """
        try:
            # Get most recent messages
            messages = await self.get_recent_messages(user_id, subject, limit=5)
            
            # Look for topic_focus in metadata (newest first)
            for msg in reversed(messages):
                if msg.metadata and "topic_focus" in msg.metadata:
                    return msg.metadata["topic_focus"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting current topic focus: {str(e)}")
            return None
    
    async def update_message_metadata(
        self,
        user_id: str,
        subject: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Update metadata on the most recent message.
        
        Args:
            user_id: User identifier
            subject: Learning subject/topic
            metadata: Metadata to merge with existing
        
        Returns:
            True if updated successfully
        """
        try:
            redis = await self._get_redis()
            key = self._get_key(user_id, subject)
            
            # Get the most recent message
            messages_json = await redis.lrange(key, 0, 0)
            if not messages_json:
                return False
            
            # Parse and update
            msg_dict = json.loads(messages_json[0])
            msg_dict["metadata"] = {**msg_dict.get("metadata", {}), **metadata}
            
            # Replace the message
            await redis.lset(key, 0, json.dumps(msg_dict))
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating message metadata: {str(e)}")
            return False
    
    async def clear_all_user_memory(self, user_id: str) -> int:
        """
        Clear all subject memories for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            Number of subjects cleared
        """
        try:
            redis = await self._get_redis()
            
            # Get all subjects
            subjects = await self.get_active_subjects(user_id)
            
            # Delete each subject's memory
            cleared = 0
            for subject in subjects:
                if await self.clear_memory(user_id, subject):
                    cleared += 1
            
            # Delete the subject index
            subject_index_key = self._get_subject_index_key(user_id)
            await redis.delete(subject_index_key)
            
            logger.info(f"Cleared all memory for user {user_id}: {cleared} subjects")
            return cleared
            
        except Exception as e:
            logger.error(f"Error clearing all user memory: {str(e)}")
            return 0


# Singleton instance
_subject_memory_manager: Optional[SubjectShortTermMemory] = None


async def get_subject_memory_manager() -> SubjectShortTermMemory:
    """
    Get the singleton SubjectShortTermMemory instance.
    
    Returns:
        SubjectShortTermMemory instance
    """
    global _subject_memory_manager
    
    if _subject_memory_manager is None:
        redis = await get_redis()
        _subject_memory_manager = SubjectShortTermMemory(redis=redis)
    
    return _subject_memory_manager

