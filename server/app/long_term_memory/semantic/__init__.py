"""
Semantic Memory Module.

Handles storage and retrieval of semantic memories (facts, preferences, user profile data).
Updated from episodic memories via scheduled processing.
"""

__all__ = [
    "SemanticMemoryService",
    "get_semantic_memory_service",
    "SemanticMemoryExtractor",
    "get_semantic_memory_extractor",
    "SemanticMemoryScheduler",
    "get_semantic_memory_scheduler",
    "start_semantic_memory_scheduler",
    "stop_semantic_memory_scheduler",
]

def __getattr__(name):
    if name in ("SemanticMemoryService", "get_semantic_memory_service"):
        from app.long_term_memory.semantic.service import SemanticMemoryService, get_semantic_memory_service
        return {"SemanticMemoryService": SemanticMemoryService, "get_semantic_memory_service": get_semantic_memory_service}[name]
    elif name in ("SemanticMemoryExtractor", "get_semantic_memory_extractor"):
        from app.long_term_memory.semantic.extractor import SemanticMemoryExtractor, get_semantic_memory_extractor
        return {"SemanticMemoryExtractor": SemanticMemoryExtractor, "get_semantic_memory_extractor": get_semantic_memory_extractor}[name]
    elif name in ("SemanticMemoryScheduler", "get_semantic_memory_scheduler", "start_semantic_memory_scheduler", "stop_semantic_memory_scheduler"):
        from app.long_term_memory.semantic.scheduler import (
            SemanticMemoryScheduler, get_semantic_memory_scheduler, 
            start_semantic_memory_scheduler, stop_semantic_memory_scheduler
        )
        exports = {
            "SemanticMemoryScheduler": SemanticMemoryScheduler,
            "get_semantic_memory_scheduler": get_semantic_memory_scheduler,
            "start_semantic_memory_scheduler": start_semantic_memory_scheduler,
            "stop_semantic_memory_scheduler": stop_semantic_memory_scheduler,
        }
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

