"""
OpenAI Function Calling Tools for Semantic Memory Management.

Production-level memory management with validation and optional async queue.
Flow: Conversation → LLM → propose_memory → Memory Validator → Memory Queue (optional) → Database
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.services.semantic_memory_service import get_semantic_memory_service
from app.db.crud.episodic_memory_crud import search_episodes_by_context
from app.schemas.pydantic_schemas.episodic_memory_schema import EpisodicMemoryFilters



def get_episodic_memory_functions() -> List[Dict[str, Any]]:
    """
    Get OpenAI function definitions for episodic memory operations.
    
    Returns:
        List of function definitions in OpenAI format
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "search_episodic_memory",
                "description": "Search and recall past incidents/episodes from episodic memory. Use this when the user asks about past events, conversations, or incidents. This performs semantic similarity search to find relevant past episodes based on the query text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query_text": {
                            "type": "string",
                            "description": "Text describing what to search for in past incidents. Use natural language (e.g., 'when I was frustrated with Docker', 'conversations about Python debugging', 'times when I asked about machine learning')"
                        },
                        "similarity_threshold": {
                            "type": "number",
                            "description": "Minimum similarity score (0.0-1.0). Higher values return more relevant results. Default is 0.3.",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "default": 0.3
                        },
                        "date_from": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Filter episodes from this date (ISO 8601 format, e.g., '2024-01-01T00:00:00Z')"
                        },
                        "date_to": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Filter episodes until this date (ISO 8601 format, e.g., '2024-12-31T23:59:59Z')"
                        },
                        "emotion": {
                            "type": "string",
                            "description": "Filter by emotion (e.g., 'frustrated', 'excited', 'confident', 'confused')"
                        },
                        "min_importance": {
                            "type": "integer",
                            "description": "Minimum importance score (1-10). Higher values return more significant episodes.",
                            "minimum": 1,
                            "maximum": 10
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (1-100). Default is 10.",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 10
                        }
                    },
                    "required": ["query_text"]
                }
            }
        }
    ]

async def handle_search_episodic_memory(
    db: AsyncSession,
    user_id: str,
    query_text: str,
    similarity_threshold: Optional[float] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    emotion: Optional[str] = None,
    min_importance: Optional[int] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Handle search_episodic_memory function call.
    Searches for past episodes using semantic similarity.
    
    Args:
        db: Database session
        user_id: User identifier
        query_text: Text to search for
        similarity_threshold: Minimum similarity score (0.0-1.0)
        date_from: Filter episodes from this date (ISO 8601 string)
        date_to: Filter episodes until this date (ISO 8601 string)
        emotion: Filter by emotion
        min_importance: Minimum importance score (1-10)
        limit: Maximum number of results
    
    Returns:
        Result dictionary with episodes and success status
    """
    try:
        # Parse date strings to datetime objects if provided
        date_from_dt = None
        date_to_dt = None
        if date_from:
            try:
                date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            except ValueError:
                return {
                    "success": False,
                    "message": f"Invalid date_from format. Expected ISO 8601 format (e.g., '2024-01-01T00:00:00Z')",
                    "episodes": []
                }
        if date_to:
            try:
                date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            except ValueError:
                return {
                    "success": False,
                    "message": f"Invalid date_to format. Expected ISO 8601 format (e.g., '2024-12-31T23:59:59Z')",
                    "episodes": []
                }
        
        # Build filters object
        filters = None
        if date_from_dt or date_to_dt or emotion or min_importance:
            filters = EpisodicMemoryFilters(
                date_from=date_from_dt,
                date_to=date_to_dt,
                emotion=emotion,
                min_importance=min_importance
            )
        
        # Perform search
        episodes = await search_episodes_by_context(
            db=db,
            query_text=query_text,
            user_id=user_id,
            similarity_threshold=similarity_threshold or 0.3,
            filters=filters,
            limit=limit or 10
        )
        
        # Format episodes for AI (exclude embedding, include all other fields)
        formatted_episodes = []
        for episode in episodes:
            formatted_episode = {
                "id": episode.get("id"),
                "event_description": episode.get("event_description"),
                "context": episode.get("context"),
                "emotion": episode.get("emotion"),
                "importance": episode.get("importance"),
                "event_time": episode.get("event_time").isoformat() if episode.get("event_time") else None,
                "related_query_ids": episode.get("related_query_ids"),
                "additional_metadata": episode.get("additional_metadata"),
                "similarity": episode.get("similarity")
            }
            formatted_episodes.append(formatted_episode)
        
        return {
            "success": True,
            "message": f"Found {len(formatted_episodes)} relevant past episodes",
            "episodes": formatted_episodes,
            "count": len(formatted_episodes)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error searching episodic memory: {str(e)}",
            "episodes": []
        }


# Function Router
async def execute_function_call(
    db: AsyncSession,
    user_id: str,
    function_name: str,
    function_args: Dict[str, Any],
    use_queue: bool = False
) -> Dict[str, Any]:
    """
    Execute a function call based on function name.
    
    Args:
        db: Database session
        user_id: User identifier
        function_name: Name of the function to execute
        function_args: Arguments for the function
        use_queue: Whether to use async queue for propose_memory operations
    
    Returns:
        Result dictionary from the function handler
    """
    
   
    if function_name == "search_episodic_memory":
        query_text = function_args.get("query_text", "")
        if not query_text:
            return {
                "success": False,
                "message": "No query_text parameter provided. Expected 'query_text' field with the search query."
            }
        if not isinstance(query_text, str):
            return {
                "success": False,
                "message": f"Invalid query_text type. Expected string, got {type(query_text).__name__}"
            }
        
        return await handle_search_episodic_memory(
            db=db,
            user_id=user_id,
            query_text=query_text,
            similarity_threshold=function_args.get("similarity_threshold"),
            date_from=function_args.get("date_from"),
            date_to=function_args.get("date_to"),
            emotion=function_args.get("emotion"),
            min_importance=function_args.get("min_importance"),
            limit=function_args.get("limit")
        )
    
    else:
        return {
            "success": False,
            "message": f"Unknown function: {function_name}"
        }
