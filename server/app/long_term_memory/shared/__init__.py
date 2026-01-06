"""
Shared Utilities for Long-term Memory.

Contains common services used by both episodic and semantic memory modules.
"""

__all__ = [
    "EmbeddingService",
    "get_embedding_service",
    "MemoryValidator",
    "MemoryQueue",
    "get_memory_queue",
    "ResponseSummarizer",
    "get_response_summarizer",
]

def __getattr__(name):
    if name in ("EmbeddingService", "get_embedding_service"):
        from app.long_term_memory.shared.embedding import EmbeddingService, get_embedding_service
        return {"EmbeddingService": EmbeddingService, "get_embedding_service": get_embedding_service}[name]
    elif name == "MemoryValidator":
        from app.long_term_memory.shared.validator import MemoryValidator
        return MemoryValidator
    elif name in ("MemoryQueue", "get_memory_queue"):
        from app.long_term_memory.shared.queue import MemoryQueue, get_memory_queue
        return {"MemoryQueue": MemoryQueue, "get_memory_queue": get_memory_queue}[name]
    elif name in ("ResponseSummarizer", "get_response_summarizer"):
        from app.long_term_memory.shared.summarizer import ResponseSummarizer, get_response_summarizer
        return {"ResponseSummarizer": ResponseSummarizer, "get_response_summarizer": get_response_summarizer}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

