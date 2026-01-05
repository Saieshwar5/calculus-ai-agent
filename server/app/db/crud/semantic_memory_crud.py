"""
CRUD operations for SemanticMemory model.
Handles flexible JSON data storage and updates, similar to MongoDB.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
from sqlalchemy.dialects.postgresql import JSONB

from app.models.semantic_memory_model import SemanticMemory
from app.schemas.pydantic_schemas.semantic_memory_schema import (
    SemanticMemoryCreate,
    SemanticMemoryUpdate,
    SemanticMemoryPartialUpdate
)


async def get_semantic_memory_by_user_id(
    db: AsyncSession,
    user_id: str
) -> Optional[SemanticMemory]:
    """
    Get semantic memory for a user.
    
    Args:
        db: Database session
        user_id: User identifier
    
    Returns:
        SemanticMemory object or None if not found
    """
    query = select(SemanticMemory).where(SemanticMemory.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_semantic_memory(
    db: AsyncSession,
    memory_data: SemanticMemoryCreate
) -> SemanticMemory:
    """
    Create semantic memory for a user.
    
    Args:
        db: Database session
        memory_data: Semantic memory data to create
    
    Returns:
        Created SemanticMemory object
    
    Raises:
        ValueError: If memory already exists for user
    """
    # Check if memory already exists
    existing = await get_semantic_memory_by_user_id(db, memory_data.user_id)
    if existing:
        raise ValueError(f"Semantic memory already exists for user {memory_data.user_id}")
    
    try:
        semantic_memory = SemanticMemory(
            user_id=memory_data.user_id,
            memory_data=memory_data.memory_data
        )
        
        db.add(semantic_memory)
        await db.commit()
        await db.refresh(semantic_memory)
        
        return semantic_memory
    except Exception as e:
        await db.rollback()
        raise ValueError(f"Error creating semantic memory: {str(e)}")


async def update_semantic_memory(
    db: AsyncSession,
    user_id: str,
    memory_update: SemanticMemoryUpdate
) -> Optional[SemanticMemory]:
    """
    Update semantic memory for a user (replaces entire memory_data).
    
    Args:
        db: Database session
        user_id: User identifier
        memory_update: New memory data
    
    Returns:
        Updated SemanticMemory object or None if not found
    """
    semantic_memory = await get_semantic_memory_by_user_id(db, user_id)
    
    if not semantic_memory:
        return None
    
    try:
        semantic_memory.memory_data = memory_update.memory_data
        await db.commit()
        await db.refresh(semantic_memory)
        
        return semantic_memory
    except Exception as e:
        await db.rollback()
        raise ValueError(f"Error updating semantic memory: {str(e)}")


async def merge_semantic_memory(
    db: AsyncSession,
    user_id: str,
    updates: Dict[str, Any]
) -> Optional[SemanticMemory]:
    """
    Merge updates into existing semantic memory (partial update).
    Similar to MongoDB's update with $set operator.
    
    Args:
        db: Database session
        user_id: User identifier
        updates: Dictionary of key-value pairs to merge into memory_data
    
    Returns:
        Updated SemanticMemory object or None if not found
    """
    semantic_memory = await get_semantic_memory_by_user_id(db, user_id)
    
    if not semantic_memory:
        return None
    
    try:
        # Merge updates into existing memory_data
        current_data = semantic_memory.memory_data or {}
        current_data.update(updates)
        semantic_memory.memory_data = current_data
        
        await db.commit()
        await db.refresh(semantic_memory)
        
        return semantic_memory
    except Exception as e:
        await db.rollback()
        raise ValueError(f"Error merging semantic memory: {str(e)}")


async def delete_semantic_memory(
    db: AsyncSession,
    user_id: str
) -> bool:
    """
    Delete semantic memory for a user.
    
    Args:
        db: Database session
        user_id: User identifier
    
    Returns:
        True if deleted, False if not found
    """
    semantic_memory = await get_semantic_memory_by_user_id(db, user_id)
    
    if not semantic_memory:
        return False
    
    try:
        await db.delete(semantic_memory)
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        raise ValueError(f"Error deleting semantic memory: {str(e)}")


async def get_or_create_semantic_memory(
    db: AsyncSession,
    user_id: str,
    initial_data: Optional[Dict[str, Any]] = None
) -> SemanticMemory:
    """
    Get semantic memory for a user, or create it if it doesn't exist.
    
    Args:
        db: Database session
        user_id: User identifier
        initial_data: Initial data if creating new memory
    
    Returns:
        SemanticMemory object
    """
    semantic_memory = await get_semantic_memory_by_user_id(db, user_id)
    
    if semantic_memory:
        return semantic_memory
    
    # Create new memory
    memory_create = SemanticMemoryCreate(
        user_id=user_id,
        memory_data=initial_data or {}
    )
    
    return await create_semantic_memory(db, memory_create)


async def query_semantic_memory(
    db: AsyncSession,
    user_id: str,
    json_path: str
) -> Optional[Any]:
    """
    Query a specific path in the semantic memory JSON data.
    Uses PostgreSQL JSONB path queries.
    
    Args:
        db: Database session
        user_id: User identifier
        json_path: JSON path (e.g., "location", "education.degree")
    
    Returns:
        Value at the path or None if not found
    """
    semantic_memory = await get_semantic_memory_by_user_id(db, user_id)
    
    if not semantic_memory or not semantic_memory.memory_data:
        return None
    
    # Navigate the JSON path
    data = semantic_memory.memory_data
    path_parts = json_path.split(".")
    
    try:
        for part in path_parts:
            if isinstance(data, dict):
                data = data.get(part)
            else:
                return None
            if data is None:
                return None
        return data
    except (KeyError, TypeError, AttributeError):
        return None

