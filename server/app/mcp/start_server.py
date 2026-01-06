#!/usr/bin/env python3
"""
Standalone MCP Server Startup Script.

This script can be used to run the MCP server independently for testing
or manual operation. The server communicates via stdio.

Usage:
    python -m app.mcp.start_server
    
    Or directly:
    python server/app/mcp/start_server.py

Environment Variables:
    WEBSEARCHAPI_API_KEY: API key for WebSearchAPI.ai (required for web search)

Example Test (from another terminal):
    echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | python -m app.mcp.start_server
"""
import sys
import os

# Add the server directory to the path for imports
server_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

from app.mcp.web_search_server import main

if __name__ == "__main__":
    print("Starting Web Search MCP Server...", file=sys.stderr)
    print("Press Ctrl+C to stop.", file=sys.stderr)
    
    # Check for API key
    api_key = os.getenv("WEBSEARCHAPI_API_KEY", "")
    if api_key:
        print("✅ WEBSEARCHAPI_API_KEY is set", file=sys.stderr)
    else:
        print("⚠️  WEBSEARCHAPI_API_KEY is not set. Web search will not work.", file=sys.stderr)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\nServer stopped.", file=sys.stderr)
    except Exception as e:
        print(f"Error running server: {e}", file=sys.stderr)
        sys.exit(1)

