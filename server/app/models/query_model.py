from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.db.my_sql_config import Base


class Query(Base):
    """
    SQLAlchemy model for user queries.
    This model represents the queries table in the database.
    """
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(255), index=True, nullable=False, comment="User identifier")
    query_text = Column(Text, nullable=False, comment="The query text from the user")
    response_text = Column(Text, nullable=True, comment="The response text from the assistant")
    
    # Episodic memory tracking
    used_for_episodic_memory = Column(
        Boolean, 
        default=False, 
        index=True, 
        nullable=False, 
        comment="Whether this query/response has been used for episodic memory extraction"
    )
    
    # Metadata fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Query(id={self.id}, user_id={self.user_id}, query_text={self.query_text[:50]}...)>"

