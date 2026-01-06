"""
Episodic Memory Module.

Handles storage and retrieval of episodic memories (events, context, time, emotions).
Uses pgvector for semantic similarity search.
"""

__all__ = [
    "EpisodicMemoryCache",
    "get_episodic_memory_cache",
    "EpisodicMemoryExtractor",
    "get_episodic_memory_extractor",
    "EpisodicMemoryProcessor",
    "get_episodic_memory_processor",
    "EpisodicMemoryTrigger",
    "get_episodic_memory_trigger",
]

def __getattr__(name):
    if name in ("EpisodicMemoryCache", "get_episodic_memory_cache"):
        from app.long_term_memory.episodic.cache import EpisodicMemoryCache, get_episodic_memory_cache
        return {"EpisodicMemoryCache": EpisodicMemoryCache, "get_episodic_memory_cache": get_episodic_memory_cache}[name]
    elif name in ("EpisodicMemoryExtractor", "get_episodic_memory_extractor"):
        from app.long_term_memory.episodic.extractor import EpisodicMemoryExtractor, get_episodic_memory_extractor
        return {"EpisodicMemoryExtractor": EpisodicMemoryExtractor, "get_episodic_memory_extractor": get_episodic_memory_extractor}[name]
    elif name in ("EpisodicMemoryProcessor", "get_episodic_memory_processor"):
        from app.long_term_memory.episodic.processor import EpisodicMemoryProcessor, get_episodic_memory_processor
        return {"EpisodicMemoryProcessor": EpisodicMemoryProcessor, "get_episodic_memory_processor": get_episodic_memory_processor}[name]
    elif name in ("EpisodicMemoryTrigger", "get_episodic_memory_trigger"):
        from app.long_term_memory.episodic.trigger import EpisodicMemoryTrigger, get_episodic_memory_trigger
        return {"EpisodicMemoryTrigger": EpisodicMemoryTrigger, "get_episodic_memory_trigger": get_episodic_memory_trigger}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

