"""
Short-term Memory Module.

Handles Redis-based conversation memory for maintaining recent context.
"""

# Imports will be available after module is fully set up
# from app.short_term_memory.manager import MemoryManager, get_memory_manager

__all__ = ["MemoryManager", "get_memory_manager"]

def __getattr__(name):
    if name in ("MemoryManager", "get_memory_manager"):
        from app.short_term_memory.manager import MemoryManager, get_memory_manager
        return {"MemoryManager": MemoryManager, "get_memory_manager": get_memory_manager}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

