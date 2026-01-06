"""
Episodic Memory model for AI agents.
Stores events, context, time, and emotions with vector embeddings for semantic search.
Uses pgvector for similarity search and PostgreSQL for structured queries.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Index, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.db.my_sql_config import Base


class EpisodicMemory(Base):
    """
    SQLAlchemy model for episodic memory.
    Stores events with vector embeddings for semantic similarity search.
    Each episode represents a meaningful event from user conversations.
    """
    __tablename__ = "episodic_memory"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(255), index=True, nullable=False, comment="User identifier")
    
    # Event description - what happened
    event_description = Column(Text, nullable=False, comment="Description of the event (e.g., 'User was frustrated debugging Docker')")
    
    # Vector embedding for semantic similarity search
    # Using text-embedding-3-small: 1536 dimensions
    event_embedding = Column(Vector(1536), nullable=True, comment="Vector embedding of event_description + context for semantic search")
    
    # Context information (JSONB for flexibility)
    context = Column(JSONB, nullable=True, default=dict, comment="Conversation context, related topics, concepts")
    
    # Emotion and importance
    emotion = Column(String(50), index=True, nullable=True, comment="Emotion expressed (e.g., 'frustrated', 'confident', 'excited')")
    importance = Column(Integer, index=True, nullable=True, comment="Importance score (1-10), how significant this event is")
    
    # Time information
    event_time = Column(DateTime(timezone=True), index=True, nullable=False, comment="When the event occurred (from conversation timestamp)")
    
    # Related data
    related_query_ids = Column(JSONB, nullable=True, default=list, comment="IDs of related queries/conversations")
    additional_metadata = Column(JSONB, nullable=True, default=dict, comment="Additional flexible data")
    
    # Processing flags for memory synchronization
    used_for_semantic_memory = Column(
        Boolean, 
        default=False, 
        nullable=False, 
        index=True,
        comment="True if this episode has been processed for semantic memory extraction"
    )
    
    # Metadata fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<EpisodicMemory(id={self.id}, user_id={self.user_id}, event_time={self.event_time})>"


# Create indexes for hybrid search performance
# Vector index will be created separately via SQL (HNSW)
# B-tree indexes are created via Column(index=True) above

