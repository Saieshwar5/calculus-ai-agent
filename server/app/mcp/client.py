"""
MCP Client Service for communicating with MCP servers.

This module provides an async client that connects to MCP servers
and can call tools exposed by those servers.

Features:
- Automatic retry logic for connection and tool calls
- Tool schema conversion to OpenAI function calling format
- Singleton pattern for efficient resource management
"""
import os
import sys
import json
import asyncio
import logging
from typing import Any, Optional, List, Dict
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging
logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1.0  # Base delay in seconds (exponential backoff)


class MCPClientService:
    """
    MCP Client Service that manages connections to MCP servers.
    
    This service handles:
    - Starting MCP server processes
    - Establishing connections via stdio
    - Calling tools on MCP servers
    - Managing connection lifecycle
    - Converting MCP tools to OpenAI format
    - Automatic retry with exponential backoff
    """
    
    def __init__(self):
        """Initialize the MCP client service."""
        self._session: Optional[ClientSession] = None
        self._read_stream = None
        self._write_stream = None
        self._context_manager = None
        self._is_connected = False
        self._available_tools: list[str] = []
        self._tools_cache: List[Dict[str, Any]] = []  # Cache MCP tool definitions
        self._openai_tools_cache: List[Dict[str, Any]] = []  # Cache OpenAI-formatted tools
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected to MCP server."""
        return self._is_connected
    
    @property
    def available_tools(self) -> list[str]:
        """Get list of available tools from connected MCP server."""
        return self._available_tools.copy()
    
    async def connect(self, server_script_path: Optional[str] = None, max_retries: int = MAX_RETRIES) -> bool:
        """
        Connect to the MCP server with automatic retry logic.
        
        Args:
            server_script_path: Path to the MCP server script. 
                              Defaults to web_search_server.py in the same directory.
            max_retries: Maximum number of connection attempts (default: MAX_RETRIES)
        
        Returns:
            True if connection successful, False otherwise
        """
        if self._is_connected:
            logger.warning("Already connected to MCP server")
            return True
        
        # Determine server script path
        if server_script_path is None:
            current_dir = Path(__file__).parent
            server_script_path = str(current_dir / "web_search_server.py")
        
        if not Path(server_script_path).exists():
            logger.error(f"MCP server script not found: {server_script_path}")
            return False
        
        last_error = None
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = RETRY_DELAY_BASE * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {delay:.1f}s delay...")
                    await asyncio.sleep(delay)
                
                logger.info(f"Connecting to MCP server: {server_script_path}")
                
                # Create server parameters for stdio connection
                server_params = StdioServerParameters(
                    command=sys.executable,  # Use the current Python interpreter
                    args=[server_script_path],
                    env={
                        **os.environ,  # Pass current environment variables
                    }
                )
                
                # Start the server and establish connection
                self._context_manager = stdio_client(server_params)
                self._read_stream, self._write_stream = await self._context_manager.__aenter__()
                
                # Create session
                self._session = ClientSession(self._read_stream, self._write_stream)
                await self._session.__aenter__()
                
                # Initialize the session
                await self._session.initialize()
                
                # Get available tools and cache them
                tools_response = await self._session.list_tools()
                self._available_tools = [tool.name for tool in tools_response.tools]
                self._tools_cache = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    }
                    for tool in tools_response.tools
                ]
                # Generate OpenAI-formatted tools cache
                self._openai_tools_cache = self._convert_to_openai_format(self._tools_cache)
                
                self._is_connected = True
                logger.info(f"Connected to MCP server. Available tools: {self._available_tools}")
                
                return True
                
            except Exception as e:
                last_error = e
                logger.warning(f"Connection attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                await self.disconnect()
        
        logger.error(f"Failed to connect to MCP server after {max_retries} attempts. Last error: {str(last_error)}")
        return False
    
    def _convert_to_openai_format(self, mcp_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert MCP tool definitions to OpenAI function calling format.
        
        Args:
            mcp_tools: List of MCP tool definitions
        
        Returns:
            List of tools in OpenAI function calling format
        """
        openai_tools = []
        for tool in mcp_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("inputSchema", {"type": "object", "properties": {}})
                }
            }
            openai_tools.append(openai_tool)
        return openai_tools
    
    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """
        Get tools in OpenAI function calling format.
        
        This method returns cached OpenAI-formatted tools that were
        fetched from the MCP server during connection.
        
        Returns:
            List of tools in OpenAI format, or empty list if not connected
        """
        if not self._is_connected:
            logger.warning("MCP client not connected. Returning empty tools list.")
            return []
        return self._openai_tools_cache.copy()
    
    def get_mcp_tools(self) -> List[Dict[str, Any]]:
        """
        Get raw MCP tool definitions.
        
        Returns:
            List of MCP tool definitions, or empty list if not connected
        """
        if not self._is_connected:
            return []
        return self._tools_cache.copy()
    
    async def disconnect(self):
        """Disconnect from the MCP server and clean up resources."""
        try:
            if self._session:
                try:
                    await self._session.__aexit__(None, None, None)
                except Exception as e:
                    logger.debug(f"Error closing session: {e}")
                self._session = None
            
            if self._context_manager:
                try:
                    await self._context_manager.__aexit__(None, None, None)
                except Exception as e:
                    logger.debug(f"Error closing context manager: {e}")
                self._context_manager = None
            
            self._read_stream = None
            self._write_stream = None
            self._is_connected = False
            self._available_tools = []
            self._tools_cache = []
            self._openai_tools_cache = []
            
            logger.info("Disconnected from MCP server")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")
    
    async def call_tool(
        self, 
        tool_name: str, 
        arguments: dict[str, Any],
        max_retries: int = MAX_RETRIES
    ) -> dict[str, Any]:
        """
        Call a tool on the MCP server with automatic retry logic.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            max_retries: Maximum number of retry attempts (default: MAX_RETRIES)
        
        Returns:
            Result dictionary from the tool
        """
        if not self._is_connected or not self._session:
            logger.error("Not connected to MCP server")
            return {
                "success": False,
                "error": "Not connected to MCP server"
            }
        
        if tool_name not in self._available_tools:
            logger.error(f"Tool '{tool_name}' not available. Available: {self._available_tools}")
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not available",
                "available_tools": self._available_tools
            }
        
        last_error = None
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = RETRY_DELAY_BASE * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info(f"Retry tool call attempt {attempt + 1}/{max_retries} after {delay:.1f}s delay...")
                    await asyncio.sleep(delay)
                
                logger.info(f"Calling MCP tool: {tool_name} with args: {arguments}")
                
                # Call the tool
                result = await self._session.call_tool(tool_name, arguments)
                
                # Parse result content
                if result.content:
                    for content_item in result.content:
                        if hasattr(content_item, 'text'):
                            try:
                                return json.loads(content_item.text)
                            except json.JSONDecodeError:
                                return {
                                    "success": True,
                                    "result": content_item.text
                                }
                
                return {
                    "success": True,
                    "result": str(result)
                }
                
            except Exception as e:
                last_error = e
                logger.warning(f"Tool call attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                
                # Check if connection was lost and try to reconnect
                if not self._is_connected or self._session is None:
                    logger.info("Connection lost, attempting to reconnect...")
                    reconnected = await self.connect()
                    if not reconnected:
                        return {
                            "success": False,
                            "error": "Connection lost and reconnection failed"
                        }
        
        logger.error(f"Failed to call tool {tool_name} after {max_retries} attempts. Last error: {str(last_error)}")
        return {
            "success": False,
            "error": f"Error calling tool after {max_retries} attempts: {str(last_error)}"
        }
    
    async def web_search(
        self,
        query: str,
        max_results: int = 5,
        country: str = "us",
        language: str = "en"
    ) -> dict[str, Any]:
        """
        Convenience method to perform web search.
        
        Args:
            query: Search query string
            max_results: Maximum number of results (1-10)
            country: Country code for localized results
            language: Language code for results
        
        Returns:
            Search results dictionary
        """
        return await self.call_tool("web_search", {
            "query": query,
            "max_results": max_results,
            "country": country,
            "language": language
        })


# Singleton instance
_mcp_client: Optional[MCPClientService] = None


def get_mcp_client() -> MCPClientService:
    """
    Get the singleton MCP client instance.
    
    Returns:
        MCPClientService instance
    """
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClientService()
    return _mcp_client


async def init_mcp_client() -> bool:
    """
    Initialize and connect the MCP client.
    
    Returns:
        True if initialization successful, False otherwise
    """
    client = get_mcp_client()
    return await client.connect()


async def close_mcp_client():
    """Close and clean up the MCP client."""
    global _mcp_client
    if _mcp_client is not None:
        await _mcp_client.disconnect()
        _mcp_client = None

