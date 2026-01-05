"""
CRUD operations for Query model.
All database operations are separated from routing logic.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List

from app.models.query_model import Query
from app.schemas.pydantic_schemas.query_schema import QueryCreate, QueryUpdate


async def create_query(
    db: AsyncSession,
    query_data: QueryCreate
) -> Query:
    """
    Create a new query.
    
    Args:
        db: Database session
        query_data: Query data to create
    
    Returns:
        Created Query object
    
    Raises:
        ValueError: If query data is invalid
    """
    try:
        query = Query(
            user_id=query_data.user_id,
            query_text=query_data.query_text,
            response_text=query_data.response_text,
            used_for_episodic_memory=query_data.used_for_episodic_memory
        )
        
        db.add(query)
        await db.commit()
        await db.refresh(query)
        
        return query
    except Exception as e:
        await db.rollback()
        raise ValueError(f"Error creating query: {str(e)}")


async def get_query_by_id(
    db: AsyncSession,
    query_id: int
) -> Optional[Query]:
    """
    Get a query by ID.
    
    Args:
        db: Database session
        query_id: Query ID
    
    Returns:
        Query object or None if not found
    """
    query = select(Query).where(Query.id == query_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def update_query(
    db: AsyncSession,
    query_id: int,
    query_update: QueryUpdate
) -> Optional[Query]:
    """
    Update a query (typically to add response text).
    
    Args:
        db: Database session
        query_id: Query ID
        query_update: Query update data
    
    Returns:
        Updated Query object or None if not found
    """
    query = await get_query_by_id(db, query_id)
    if not query:
        return None
    
    try:
        if query_update.response_text is not None:
            query.response_text = query_update.response_text
        if query_update.used_for_episodic_memory is not None:
            query.used_for_episodic_memory = query_update.used_for_episodic_memory
        
        await db.commit()
        await db.refresh(query)
        
        return query
    except Exception as e:
        await db.rollback()
        raise ValueError(f"Error updating query: {str(e)}")


async def get_queries_by_user_id(
    db: AsyncSession,
    user_id: str,
    limit: int = 100
) -> list[Query]:
    """
    Get queries for a specific user.
    
    Args:
        db: Database session
        user_id: User identifier
        limit: Maximum number of queries to return
    
    Returns:
        List of Query objects
    """
    query = (
        select(Query)
        .where(Query.user_id == user_id)
        .order_by(Query.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_unused_query_pairs(
    db: AsyncSession,
    user_id: str,
    limit: int = 15
) -> List[Query]:
    """
    Get query/response pairs that have not been used for episodic memory.
    Returns pairs where both query_text and response_text are present.
    
    Args:
        db: Database session
        user_id: User identifier
        limit: Maximum number of pairs to return (default: 15)
    
    Returns:
        List of Query objects (oldest first)
    """
    query = (
        select(Query)
        .where(
            and_(
                Query.user_id == user_id,
                Query.used_for_episodic_memory == False,
                Query.query_text.isnot(None),
                Query.query_text != "",
                Query.response_text.isnot(None),
                Query.response_text != ""
            )
        )
        .order_by(Query.created_at.asc())  # Oldest first
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def count_unused_query_pairs(
    db: AsyncSession,
    user_id: str
) -> int:
    """
    Count how many unused query/response pairs exist for a user.
    Only counts pairs where both query_text and response_text are present.
    
    Args:
        db: Database session
        user_id: User identifier
    
    Returns:
        Number of unused query/response pairs
    """
    query = (
        select(func.count(Query.id))
        .where(
            and_(
                Query.user_id == user_id,
                Query.used_for_episodic_memory == False,
                Query.query_text.isnot(None),
                Query.query_text != "",
                Query.response_text.isnot(None),
                Query.response_text != ""
            )
        )
    )
    result = await db.execute(query)
    return result.scalar() or 0


async def mark_queries_as_used(
    db: AsyncSession,
    query_ids: List[int]
) -> bool:
    """
    Mark multiple queries as used for episodic memory.
    
    Args:
        db: Database session
        query_ids: List of query IDs to mark as used
    
    Returns:
        True if successful, False otherwise
    """
    if not query_ids:
        return True
    
    try:
        for query_id in query_ids:
            query_obj = await get_query_by_id(db, query_id)
            if query_obj:
                query_obj.used_for_episodic_memory = True
        
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        raise ValueError(f"Error marking queries as used: {str(e)}")

