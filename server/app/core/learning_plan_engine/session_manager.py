"""
Learning Plan Session Manager.

Handles storing and retrieving learning plan conversation sessions
using Redis Lists. Each session stores up to 50 messages.
"""
import json
import time
import uuid
from typing import List, Optional, Dict, Any
from redis.asyncio import Redis

from app.db.redis_config import get_redis, MEMORY_TTL_SECONDS


class LearningPlanSessionManager:
    """
    Manages learning plan creation sessions using Redis.

    Stores conversation history as a Redis List with automatic trimming
    to keep only the last 50 messages per session.
    """

    MAX_MESSAGES = 50
    KEY_PREFIX = "learning_plan"
    SESSION_TTL_DAYS = 7
    SESSION_TTL_SECONDS = SESSION_TTL_DAYS * 24 * 60 * 60

    def __init__(self, redis: Optional[Redis] = None):
        """
        Initialize LearningPlanSessionManager.

        Args:
            redis: Optional Redis client. If not provided, will use get_redis().
        """
        self._redis = redis

    async def _get_redis(self) -> Redis:
        """Get Redis client instance."""
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis

    def _get_messages_key(self, user_id: str, plan_id: str) -> str:
        """Generate Redis key for session messages."""
        return f"{self.KEY_PREFIX}:{user_id}:{plan_id}:messages"

    def _get_metadata_key(self, user_id: str, plan_id: str) -> str:
        """Generate Redis key for session metadata."""
        return f"{self.KEY_PREFIX}:{user_id}:{plan_id}:metadata"

    async def create_session(
        self,
        user_id: str,
        plan_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new learning plan session.

        Args:
            user_id: User identifier
            plan_id: Optional plan ID (will generate UUID if not provided)
            metadata: Optional metadata to store with session

        Returns:
            The plan_id for the created session
        """
        try:
            redis = await self._get_redis()

            if plan_id is None:
                plan_id = str(uuid.uuid4())

            # Store session metadata
            metadata_key = self._get_metadata_key(user_id, plan_id)
            session_metadata = {
                "user_id": user_id,
                "plan_id": plan_id,
                "created_at": time.time(),
                "message_count": 0,
                **(metadata or {})
            }

            await redis.set(
                metadata_key,
                json.dumps(session_metadata),
                ex=self.SESSION_TTL_SECONDS
            )

            print(f"✅ Created learning plan session: {user_id}:{plan_id}")
            return plan_id

        except Exception as e:
            print(f"❌ Error creating session: {str(e)}")
            raise

    async def add_message(
        self,
        user_id: str,
        plan_id: str,
        role: str,
        content: str,
        timestamp: Optional[float] = None
    ) -> bool:
        """
        Add a message to the learning plan session.

        Args:
            user_id: User identifier
            plan_id: Plan identifier
            role: Message role ("user" or "assistant" or "system")
            content: Message content
            timestamp: Optional timestamp (defaults to current time)

        Returns:
            True if message was added successfully
        """
        try:
            redis = await self._get_redis()
            messages_key = self._get_messages_key(user_id, plan_id)
            metadata_key = self._get_metadata_key(user_id, plan_id)

            if timestamp is None:
                timestamp = time.time()

            message = {
                "role": role,
                "content": content,
                "timestamp": timestamp
            }

            # Serialize message to JSON
            message_json = json.dumps(message)

            # Add message to the front of the list (LPUSH)
            await redis.lpush(messages_key, message_json)

            # Trim list to keep only last MAX_MESSAGES
            await redis.ltrim(messages_key, 0, self.MAX_MESSAGES - 1)

            # Set or refresh TTL
            await redis.expire(messages_key, self.SESSION_TTL_SECONDS)

            # Update message count in metadata
            metadata_json = await redis.get(metadata_key)
            if metadata_json:
                metadata = json.loads(metadata_json)
                metadata["message_count"] = await redis.llen(messages_key)
                metadata["last_updated"] = timestamp
                await redis.set(
                    metadata_key,
                    json.dumps(metadata),
                    ex=self.SESSION_TTL_SECONDS
                )

            return True
        except Exception as e:
            print(f"❌ Error adding message to session: {str(e)}")
            return False

    async def get_messages(
        self,
        user_id: str,
        plan_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve messages from a learning plan session.

        Args:
            user_id: User identifier
            plan_id: Plan identifier
            limit: Optional limit on number of messages (defaults to MAX_MESSAGES)

        Returns:
            List of message dictionaries, ordered from oldest to newest
        """
        try:
            redis = await self._get_redis()
            messages_key = self._get_messages_key(user_id, plan_id)

            if limit is None:
                limit = self.MAX_MESSAGES

            # Get all messages from the list (LRANGE 0 -1)
            messages_json = await redis.lrange(messages_key, 0, -1)

            if not messages_json:
                return []

            # Parse JSON messages and reverse to get chronological order
            messages = []
            for msg_json in reversed(messages_json):
                try:
                    message = json.loads(msg_json)
                    messages.append(message)
                except json.JSONDecodeError as e:
                    print(f"⚠️ Error parsing message JSON: {str(e)}")
                    continue

            # Return only the requested limit (most recent)
            return messages[-limit:] if limit < len(messages) else messages

        except Exception as e:
            print(f"❌ Error retrieving messages from session: {str(e)}")
            return []

    async def get_session_data(
        self,
        user_id: str,
        plan_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get complete session data including messages and metadata.

        Args:
            user_id: User identifier
            plan_id: Plan identifier

        Returns:
            Dictionary with session data or None if session doesn't exist
        """
        try:
            redis = await self._get_redis()
            metadata_key = self._get_metadata_key(user_id, plan_id)

            # Get metadata
            metadata_json = await redis.get(metadata_key)
            if not metadata_json:
                return None

            metadata = json.loads(metadata_json)

            # Get messages
            messages = await self.get_messages(user_id, plan_id)

            return {
                "metadata": metadata,
                "messages": messages,
                "message_count": len(messages)
            }

        except Exception as e:
            print(f"❌ Error getting session data: {str(e)}")
            return None

    async def clear_session(
        self,
        user_id: str,
        plan_id: str
    ) -> bool:
        """
        Clear a learning plan session (delete all messages and metadata).

        Args:
            user_id: User identifier
            plan_id: Plan identifier

        Returns:
            True if session was cleared successfully
        """
        try:
            redis = await self._get_redis()
            messages_key = self._get_messages_key(user_id, plan_id)
            metadata_key = self._get_metadata_key(user_id, plan_id)

            # Delete both keys
            deleted = await redis.delete(messages_key, metadata_key)

            if deleted > 0:
                print(f"✅ Cleared session: {user_id}:{plan_id}")

            return deleted > 0

        except Exception as e:
            print(f"❌ Error clearing session: {str(e)}")
            return False

    async def session_exists(
        self,
        user_id: str,
        plan_id: str
    ) -> bool:
        """
        Check if a session exists.

        Args:
            user_id: User identifier
            plan_id: Plan identifier

        Returns:
            True if session exists
        """
        try:
            redis = await self._get_redis()
            metadata_key = self._get_metadata_key(user_id, plan_id)

            exists = await redis.exists(metadata_key)
            return exists > 0

        except Exception as e:
            print(f"❌ Error checking session existence: {str(e)}")
            return False

    async def get_message_count(
        self,
        user_id: str,
        plan_id: str
    ) -> int:
        """
        Get the number of messages in a session.

        Args:
            user_id: User identifier
            plan_id: Plan identifier

        Returns:
            Number of messages in session
        """
        try:
            redis = await self._get_redis()
            messages_key = self._get_messages_key(user_id, plan_id)

            count = await redis.llen(messages_key)
            return count

        except Exception as e:
            print(f"❌ Error getting message count: {str(e)}")
            return 0


# Singleton instance
_session_manager: Optional[LearningPlanSessionManager] = None


async def get_session_manager() -> LearningPlanSessionManager:
    """
    Get LearningPlanSessionManager instance (singleton pattern).

    Usage in FastAPI routes:
        from app.core.learning_plan_engine.session_manager import get_session_manager

        @app.post("/learning-plan")
        async def create_plan(
            session_manager: LearningPlanSessionManager = Depends(get_session_manager)
        ):
            ...
    """
    global _session_manager

    if _session_manager is None:
        redis = await get_redis()
        _session_manager = LearningPlanSessionManager(redis=redis)

    return _session_manager
