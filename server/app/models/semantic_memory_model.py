"""
Semantic Memory model for AI agents.
Stores flexible JSON data per user, similar to MongoDB but in PostgreSQL.
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.my_sql_config import Base


class SemanticMemory(Base):
    """
    SQLAlchemy model for semantic memory.
    Each user has one record that can store flexible JSON data.
    Uses PostgreSQL JSONB type for efficient storage and querying.
    """
    __tablename__ = "semantic_memory"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(255), unique=True, index=True, nullable=False, comment="User identifier")
    
    # JSONB field for flexible semantic memory data
    # AI agents can store any structure here (facts, preferences, events, etc.)
    memory_data = Column(JSONB, nullable=False, default=dict, comment="Flexible JSON data for semantic memory")
    
    # Metadata fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<SemanticMemory(id={self.id}, user_id={self.user_id})>"

