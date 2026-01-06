"""
OpenAI Function Calling Tools for Memory and Web Search.

Production-level memory management with validation and optional async queue.
Includes web search via MCP server for real-time information retrieval.
Flow: Conversation → LLM → function_call → Handler → Result
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

from app.long_term_memory.semantic.service import get_semantic_memory_service
from app.db.crud.memory.episodic import search_episodes_by_context
from app.schemas.pydantic_schemas.memory.episodic import EpisodicMemoryFilters
from app.mcp.client import get_mcp_client

logger = logging.getLogger(__name__)



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


def get_web_search_functions() -> List[Dict[str, Any]]:
    """
    Get OpenAI function definitions for web search operations.
    
    This function first tries to get tools dynamically from the MCP server.
    If the MCP client is not connected, it falls back to a static definition.
    
    Returns:
        List of function definitions in OpenAI format
    """
    # Try to get tools dynamically from MCP server
    mcp_client = get_mcp_client()
    if mcp_client.is_connected:
        openai_tools = mcp_client.get_openai_tools()
        if openai_tools:
            logger.debug(f"Using {len(openai_tools)} tools from MCP server")
            return openai_tools
    
    # Fallback to static definition if MCP not connected
    logger.debug("MCP client not connected, using fallback web_search definition")
    return [
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for current, real-time information. Use this when you need up-to-date information, recent news, current events, facts that may have changed, or any information that requires searching the internet. Returns search results with titles, URLs, and snippets.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query string. Be specific and include relevant keywords for better results."
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of search results to return (1-10). Default is 5.",
                            "minimum": 1,
                            "maximum": 10,
                            "default": 5
                        },
                        "country": {
                            "type": "string",
                            "description": "Country code for localized results (e.g., 'us', 'uk', 'in'). Default is 'us'.",
                            "default": "us"
                        },
                        "language": {
                            "type": "string",
                            "description": "Language code for results (e.g., 'en', 'es', 'fr'). Default is 'en'.",
                            "default": "en"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]


async def handle_web_search(
    query: str,
    max_results: Optional[int] = None,
    country: Optional[str] = None,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handle web_search function call.
    Performs web search via MCP client connected to WebSearchAPI.
    
    Args:
        query: Search query string
        max_results: Maximum number of results (1-10)
        country: Country code for localized results
        language: Language code for results
    
    Returns:
        Result dictionary with search results and success status
    """
    try:
        # Get MCP client
        mcp_client = get_mcp_client()
        
        # Check if connected
        if not mcp_client.is_connected:
            logger.warning("MCP client not connected, attempting to connect...")
            connected = await mcp_client.connect()
            if not connected:
                return {
                    "success": False,
                    "message": "Failed to connect to web search service. MCP server may not be running.",
                    "results": []
                }
        
        # Perform web search via MCP
        result = await mcp_client.web_search(
            query=query,
            max_results=max_results or 5,
            country=country or "us",
            language=language or "en"
        )
        
        # Format results for LLM
        if result.get("success"):
            # Get the full API response
            api_response = result.get("results", {})
            # Also check for extracted_results if available
            extracted_results = result.get("extracted_results", [])
            
            # Format search results for better LLM consumption
            formatted_results = []
            
            # First try extracted_results if available
            if extracted_results and isinstance(extracted_results, list):
                for item in extracted_results:
                    if isinstance(item, dict):
                        formatted_results.append({
                            "title": item.get("title", item.get("name", "")),
                            "url": item.get("url", item.get("link", "")),
                            "snippet": item.get("snippet", item.get("description", item.get("text", ""))),
                        })
            # Then try the standard response structure
            elif isinstance(api_response, dict):
                # Try different possible keys in the API response
                results_list = None
                if "results" in api_response:
                    results_list = api_response["results"]
                elif "organic" in api_response:
                    results_list = api_response["organic"]
                elif "web" in api_response:
                    results_list = api_response["web"]
                elif "data" in api_response:
                    results_list = api_response["data"]
                
                if results_list and isinstance(results_list, list):
                    for item in results_list:
                        if isinstance(item, dict):
                            formatted_results.append({
                                "title": item.get("title", item.get("name", "")),
                                "url": item.get("url", item.get("link", "")),
                                "snippet": item.get("snippet", item.get("description", item.get("text", ""))),
                            })
            elif isinstance(api_response, list):
                # If the response itself is a list
                for item in api_response:
                    if isinstance(item, dict):
                        formatted_results.append({
                            "title": item.get("title", item.get("name", "")),
                            "url": item.get("url", item.get("link", "")),
                            "snippet": item.get("snippet", item.get("description", item.get("text", ""))),
                        })
            
            # Log if we couldn't parse results
            if not formatted_results:
                logger.warning(f"Could not parse web search results. Response structure: {type(api_response)}, keys: {list(api_response.keys()) if isinstance(api_response, dict) else 'N/A'}")
            
            return {
                "success": True,
                "message": f"Found {len(formatted_results)} web search results",
                "query": query,
                "results": formatted_results,
                "count": len(formatted_results)
            }
        else:
            return {
                "success": False,
                "message": result.get("error", "Web search failed"),
                "results": []
            }
        
    except Exception as e:
        logger.error(f"Error in web search: {str(e)}")
        return {
            "success": False,
            "message": f"Error performing web search: {str(e)}",
            "results": []
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
    
    elif function_name == "web_search":
        query = function_args.get("query", "")
        if not query:
            return {
                "success": False,
                "message": "No query parameter provided. Expected 'query' field with the search query."
            }
        if not isinstance(query, str):
            return {
                "success": False,
                "message": f"Invalid query type. Expected string, got {type(query).__name__}"
            }
        
        return await handle_web_search(
            query=query,
            max_results=function_args.get("max_results"),
            country=function_args.get("country"),
            language=function_args.get("language")
        )
    
    else:
        return {
            "success": False,
            "message": f"Unknown function: {function_name}"
        }
