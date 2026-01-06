"""
Memory CRUD Operations Module.

Contains database operations for episodic and semantic memory.
"""

from app.db.crud.memory.episodic import (
    create_episodic_memory,
    get_episodic_memory_by_id,
    get_episodic_memories_by_user,
    find_similar_episodes,
    search_episodes_by_context,
    get_recent_episodic_memories,
    get_episodes_by_emotion,
    get_episodes_by_importance,
    delete_episodic_memory,
    get_users_with_unprocessed_episodes,
    get_unprocessed_episodes_for_semantic,
    count_unprocessed_episodes_for_semantic,
    mark_episodes_as_semantic_processed,
)
from app.db.crud.memory.semantic import (
    get_semantic_memory_by_user_id,
    create_semantic_memory,
    update_semantic_memory,
    merge_semantic_memory,
    delete_semantic_memory,
    get_or_create_semantic_memory,
    query_semantic_memory,
)

__all__ = [
    # Episodic memory CRUD
    "create_episodic_memory",
    "get_episodic_memory_by_id",
    "get_episodic_memories_by_user",
    "find_similar_episodes",
    "search_episodes_by_context",
    "get_recent_episodic_memories",
    "get_episodes_by_emotion",
    "get_episodes_by_importance",
    "delete_episodic_memory",
    "get_users_with_unprocessed_episodes",
    "get_unprocessed_episodes_for_semantic",
    "count_unprocessed_episodes_for_semantic",
    "mark_episodes_as_semantic_processed",
    # Semantic memory CRUD
    "get_semantic_memory_by_user_id",
    "create_semantic_memory",
    "update_semantic_memory",
    "merge_semantic_memory",
    "delete_semantic_memory",
    "get_or_create_semantic_memory",
    "query_semantic_memory",
]

