"""
MCP Server for Web Search using WebSearchAPI.

This server implements the Model Context Protocol (MCP) and provides
web search capabilities through WebSearchAPI.ai.

Run this server as a standalone process that communicates via stdio.
"""
import os
import json
import asyncio
import logging
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSearchAPI configuration
WEBSEARCHAPI_URL = "https://api.websearchapi.ai/ai-search"
WEBSEARCHAPI_API_KEY = os.getenv("WEBSEARCHAPI_API_KEY", "")

# Create MCP server instance
server = Server("web-search-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    List all available tools provided by this MCP server.
    
    Returns:
        List of Tool objects describing available tools
    """
    return [
        Tool(
            name="web_search",
            description="Search the web for current information using WebSearchAPI. Use this when you need to find up-to-date information, news, facts, or any web content. Returns search results with titles, URLs, and snippets.",
            inputSchema={
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
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle tool calls from MCP clients.
    
    Args:
        name: Name of the tool to call
        arguments: Tool arguments
    
    Returns:
        List of TextContent with tool results
    """
    if name == "web_search":
        return await handle_web_search(arguments)
    else:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"Unknown tool: {name}",
                "available_tools": ["web_search"]
            })
        )]


async def handle_web_search(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute web search using WebSearchAPI.
    
    Args:
        arguments: Search parameters including query, max_results, country, language
    
    Returns:
        List of TextContent with search results
    """
    query = arguments.get("query", "")
    max_results = arguments.get("max_results", 5)
    country = arguments.get("country", "us")
    language = arguments.get("language", "en")
    
    if not query:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "Query is required for web search"
            })
        )]
    
    if not WEBSEARCHAPI_API_KEY:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "WEBSEARCHAPI_API_KEY environment variable is not set"
            })
        )]
    
    try:
        # Prepare request to WebSearchAPI
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {WEBSEARCHAPI_API_KEY}"
        }
        
        payload = {
            "query": query,
            "maxResults": max_results,
            "includeContent": False,
            "country": country,
            "language": language
        }
        
        logger.info(f"Performing web search for: {query}")
        
        # Make async HTTP request
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                WEBSEARCHAPI_URL,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                results = response.json()
                
                # Debug: Log the actual response structure (first 1000 chars)
                response_str = json.dumps(results, indent=2)
                logger.info(f"WebSearchAPI raw response (first 1000 chars): {response_str[:1000]}")
                logger.info(f"WebSearchAPI response type: {type(results)}, keys: {list(results.keys()) if isinstance(results, dict) else 'N/A'}")
                
                # Extract results from API response
                # WebSearchAPI may return results in different keys: "results", "organic", "web", etc.
                search_results = []
                if isinstance(results, dict):
                    # Try common response keys
                    if "results" in results:
                        search_results = results["results"]
                        logger.info(f"Found results in 'results' key: {len(search_results) if isinstance(search_results, list) else 'not a list'}")
                    elif "organic" in results:
                        search_results = results["organic"]
                        logger.info(f"Found results in 'organic' key: {len(search_results) if isinstance(search_results, list) else 'not a list'}")
                    elif "web" in results:
                        search_results = results["web"]
                        logger.info(f"Found results in 'web' key: {len(search_results) if isinstance(search_results, list) else 'not a list'}")
                    elif "data" in results:
                        search_results = results["data"]
                        logger.info(f"Found results in 'data' key: {len(search_results) if isinstance(search_results, list) else 'not a list'}")
                    else:
                        # If no standard key, log all keys for debugging
                        logger.warning(f"Unexpected API response structure. Available keys: {list(results.keys())}")
                        # Check if any key contains a list
                        for key, value in results.items():
                            if isinstance(value, list):
                                logger.info(f"Found list in key '{key}' with {len(value)} items")
                                search_results = value
                                break
                
                # Format results for LLM consumption
                formatted_results = {
                    "success": True,
                    "query": query,
                    "results": results,  # Keep full response for debugging
                    "extracted_results": search_results,
                    "count": len(search_results) if isinstance(search_results, list) else 0
                }
                
                logger.info(f"Web search completed successfully for: {query}, found {formatted_results['count']} results")
                
                return [TextContent(
                    type="text",
                    text=json.dumps(formatted_results, indent=2)
                )]
            else:
                error_text = response.text
                logger.error(f"WebSearchAPI error: {response.status_code} - {error_text}")
                
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": f"WebSearchAPI returned status {response.status_code}",
                        "details": error_text
                    })
                )]
                
    except httpx.TimeoutException:
        logger.error("WebSearchAPI request timed out")
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "Web search request timed out"
            })
        )]
    except httpx.RequestError as e:
        logger.error(f"WebSearchAPI request error: {str(e)}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": f"Web search request failed: {str(e)}"
            })
        )]
    except Exception as e:
        logger.error(f"Unexpected error during web search: {str(e)}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            })
        )]


async def run_server():
    """Run the MCP server with stdio transport."""
    logger.info("Starting Web Search MCP Server...")
    
    if not WEBSEARCHAPI_API_KEY:
        logger.warning("WEBSEARCHAPI_API_KEY is not set. Web search will not work.")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """Entry point for running the MCP server."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()

