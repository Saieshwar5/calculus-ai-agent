"""
Semantic Memory Service with Validation and Queue.
Production-level service that validates memory before saving and optionally queues operations.
"""
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.long_term_memory.shared.validator import MemoryValidator
from app.long_term_memory.shared.queue import get_memory_queue
from app.db.crud.memory.semantic import (
    get_semantic_memory_by_user_id,
    create_semantic_memory,
    update_semantic_memory,
    merge_semantic_memory,
    delete_semantic_memory,
    get_or_create_semantic_memory,
    query_semantic_memory
)
from app.schemas.pydantic_schemas.memory.semantic import (
    SemanticMemoryCreate,
    SemanticMemoryUpdate
)
from app.db.my_sql_config import AsyncSessionLocal

logger = logging.getLogger(__name__)


class SemanticMemoryService:
    """
    Production-level semantic memory service with validation and optional async queue.
    """
    
    def __init__(self, use_queue: bool = False):
        """
        Initialize semantic memory service.
        
        Args:
            use_queue: Whether to use async queue for operations (default: False for immediate processing)
        """
        self.validator = MemoryValidator()
        self.use_queue = use_queue
        self.queue = get_memory_queue() if use_queue else None
    
    async def propose_memory(
        self,
        db: AsyncSession,
        user_id: str,
        data: Dict[str, Any],
        use_queue: Optional[bool] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Propose memory data for saving (with validation).
        This is the entry point for AI agents to save memory.
        
        Flow: Conversation → LLM → propose_memory → Validator → Queue (optional) → Database
        
        Args:
            db: Database session
            user_id: User identifier
            data: Memory data to save
            use_queue: Override default queue setting
        
        Returns:
            Tuple of (success, message, saved_data)
        """
        # Step 1: Validate memory data
        is_valid, error_message, cleaned_data = self.validator.validate_memory_data(data)
        
        if not is_valid:
            logger.warning(f"Memory validation failed for user {user_id}: {error_message}")
            return False, f"Validation failed: {error_message}", None
        
        # Step 2: Decide on sync vs async processing
        should_queue = use_queue if use_queue is not None else self.use_queue
        
        if should_queue:
            # Queue for async processing
            success = await self.queue.enqueue(
                operation="merge",
                user_id=user_id,
                data=cleaned_data,
                handler=self._async_merge_handler()
            )
            
            if success:
                return True, "Memory data queued for processing", cleaned_data
            else:
                # Fallback to sync if queue is full
                logger.warning(f"Queue full, falling back to sync processing for user {user_id}")
                return await self._save_memory_sync(db, user_id, cleaned_data)
        else:
            # Immediate sync processing
            return await self._save_memory_sync(db, user_id, cleaned_data)
    
    async def _save_memory_sync(
        self,
        db: AsyncSession,
        user_id: str,
        cleaned_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Save memory synchronously (immediate).
        
        Args:
            db: Database session
            user_id: User identifier
            cleaned_data: Validated and cleaned data
        
        Returns:
            Tuple of (success, message, saved_data)
        """
        try:
            # Get or create memory
            memory = await get_or_create_semantic_memory(db, user_id, {})
            
            # Merge the new data
            updated_memory = await merge_semantic_memory(db, user_id, cleaned_data)
            
            if updated_memory:
                logger.info(f"Successfully saved semantic memory for user {user_id}")
                return True, f"Successfully saved semantic memory. Updated keys: {list(cleaned_data.keys())}", updated_memory.memory_data
            else:
                return False, "Failed to save semantic memory", None
        except Exception as e:
            logger.error(f"Error saving semantic memory for user {user_id}: {e}")
            return False, f"Error saving semantic memory: {str(e)}", None
    
    def _async_merge_handler(self):
        """
        Create async handler for queue processing.
        Creates its own database session since the original session may be closed.
        
        Returns:
            Async handler function
        """
        async def handler(user_id: str, data: Dict[str, Any]):
            # Create a new database session for async processing
            async with AsyncSessionLocal() as db:
                try:
                    # Get or create memory first
                    await get_or_create_semantic_memory(db, user_id, {})
                    # Then merge
                    result = await merge_semantic_memory(db, user_id, data)
                    return result
                except Exception as e:
                    logger.error(f"Error in async merge handler for user {user_id}: {e}")
                    raise
        
        return handler
    
    async def create_memory(
        self,
        db: AsyncSession,
        user_id: str,
        data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Create new semantic memory record.
        
        Args:
            db: Database session
            user_id: User identifier
            data: Initial memory data
        
        Returns:
            Tuple of (success, message, saved_data)
        """
        # Validate
        is_valid, error_message, cleaned_data = self.validator.validate_memory_data(data)
        
        if not is_valid:
            return False, f"Validation failed: {error_message}", None
        
        try:
            memory_create = SemanticMemoryCreate(
                user_id=user_id,
                memory_data=cleaned_data
            )
            
            memory = await create_semantic_memory(db, memory_create)
            
            if memory:
                logger.info(f"Successfully created semantic memory for user {user_id}")
                return True, "Successfully created semantic memory", memory.memory_data
            else:
                return False, "Failed to create semantic memory", None
        except ValueError as e:
            # Memory already exists
            return False, str(e), None
        except Exception as e:
            logger.error(f"Error creating semantic memory for user {user_id}: {e}")
            return False, f"Error creating semantic memory: {str(e)}", None
    
    async def update_memory(
        self,
        db: AsyncSession,
        user_id: str,
        data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Update entire semantic memory (replaces all data).
        
        Args:
            db: Database session
            user_id: User identifier
            data: New memory data (replaces existing)
        
        Returns:
            Tuple of (success, message, saved_data)
        """
        # Validate
        is_valid, error_message, cleaned_data = self.validator.validate_memory_data(data)
        
        if not is_valid:
            return False, f"Validation failed: {error_message}", None
        
        try:
            memory_update = SemanticMemoryUpdate(
                memory_data=cleaned_data
            )
            
            updated_memory = await update_semantic_memory(db, user_id, memory_update)
            
            if updated_memory:
                logger.info(f"Successfully updated semantic memory for user {user_id}")
                return True, "Successfully updated semantic memory", updated_memory.memory_data
            else:
                return False, "Semantic memory not found", None
        except Exception as e:
            logger.error(f"Error updating semantic memory for user {user_id}: {e}")
            return False, f"Error updating semantic memory: {str(e)}", None
    
    async def delete_memory(
        self,
        db: AsyncSession,
        user_id: str
    ) -> Tuple[bool, str]:
        """
        Delete semantic memory for a user.
        
        Args:
            db: Database session
            user_id: User identifier
        
        Returns:
            Tuple of (success, message)
        """
        try:
            deleted = await delete_semantic_memory(db, user_id)
            
            if deleted:
                logger.info(f"Successfully deleted semantic memory for user {user_id}")
                return True, "Successfully deleted semantic memory"
            else:
                return False, "Semantic memory not found"
        except Exception as e:
            logger.error(f"Error deleting semantic memory for user {user_id}: {e}")
            return False, f"Error deleting semantic memory: {str(e)}"
    
    async def get_memory(
        self,
        db: AsyncSession,
        user_id: str,
        keys: Optional[list] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get semantic memory for a user.
        
        Args:
            db: Database session
            user_id: User identifier
            keys: Optional list of specific keys to retrieve
        
        Returns:
            Tuple of (success, message, data)
        """
        try:
            memory = await get_semantic_memory_by_user_id(db, user_id)
            
            if not memory or not memory.memory_data:
                return True, "No semantic memory found for user", {}
            
            memory_data = memory.memory_data
            
            # Filter by keys if requested
            if keys and len(keys) > 0:
                filtered_data = {key: memory_data.get(key) for key in keys if key in memory_data}
                return True, f"Retrieved semantic memory for keys: {keys}", filtered_data
            else:
                return True, "Retrieved all semantic memory data", memory_data
        except Exception as e:
            logger.error(f"Error retrieving semantic memory for user {user_id}: {e}")
            return False, f"Error retrieving semantic memory: {str(e)}", None
    
    async def query_memory_path(
        self,
        db: AsyncSession,
        user_id: str,
        path: str
    ) -> Tuple[bool, str, Optional[Any]]:
        """
        Query a specific path in semantic memory.
        
        Args:
            db: Database session
            user_id: User identifier
            path: JSON path to query
        
        Returns:
            Tuple of (success, message, value)
        """
        try:
            value = await query_semantic_memory(db, user_id, path)
            
            if value is None:
                return True, f"No value found at path: {path}", None
            else:
                return True, f"Retrieved value from path: {path}", value
        except Exception as e:
            logger.error(f"Error querying semantic memory path for user {user_id}: {e}")
            return False, f"Error querying semantic memory path: {str(e)}", None


# Global service instance
_semantic_memory_service: Optional[SemanticMemoryService] = None


def get_semantic_memory_service(use_queue: bool = False) -> SemanticMemoryService:
    """
    Get or create semantic memory service instance.
    
    Args:
        use_queue: Whether to use async queue
    
    Returns:
        SemanticMemoryService instance
    """
    global _semantic_memory_service
    if _semantic_memory_service is None or _semantic_memory_service.use_queue != use_queue:
        _semantic_memory_service = SemanticMemoryService(use_queue=use_queue)
    return _semantic_memory_service

