"""
Long-term Memory Module.

Contains episodic memory (events, context, emotions) and semantic memory (facts, preferences).
Both use PostgreSQL with pgvector for semantic search capabilities.
"""

__all__ = ["episodic", "semantic", "shared"]

def __getattr__(name):
    if name == "episodic":
        from app.long_term_memory import episodic
        return episodic
    elif name == "semantic":
        from app.long_term_memory import semantic
        return semantic
    elif name == "shared":
        from app.long_term_memory import shared
        return shared
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

