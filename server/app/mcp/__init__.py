"""
MCP (Model Context Protocol) Module.

Contains MCP server and client implementations for tool integrations.
The MCP server provides tools that can be called by LLM clients.
"""

__all__ = ["web_search_server", "client"]

def __getattr__(name):
    if name == "web_search_server":
        from app.mcp import web_search_server
        return web_search_server
    elif name == "client":
        from app.mcp import client
        return client
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

