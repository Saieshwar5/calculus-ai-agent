"""
Memory Schemas Module.

Contains Pydantic schemas for episodic, semantic, and short-term memory operations.
"""

from app.schemas.pydantic_schemas.memory.episodic import (
    EpisodicMemoryCreate,
    EpisodicMemoryResponse,
    EpisodicMemoryFilters,
    EpisodicMemorySearchRequest,
    EpisodicMemoryExtractionRequest,
)
from app.schemas.pydantic_schemas.memory.semantic import (
    SemanticMemoryCreate,
    SemanticMemoryUpdate,
    SemanticMemoryResponse,
    SemanticMemoryPartialUpdate,
)
from app.schemas.pydantic_schemas.memory.short_term import (
    Message,
    MemoryResponse,
    MemoryClearResponse,
)

__all__ = [
    # Episodic memory
    "EpisodicMemoryCreate",
    "EpisodicMemoryResponse",
    "EpisodicMemoryFilters",
    "EpisodicMemorySearchRequest",
    "EpisodicMemoryExtractionRequest",
    # Semantic memory
    "SemanticMemoryCreate",
    "SemanticMemoryUpdate",
    "SemanticMemoryResponse",
    "SemanticMemoryPartialUpdate",
    # Short-term memory
    "Message",
    "MemoryResponse",
    "MemoryClearResponse",
]

