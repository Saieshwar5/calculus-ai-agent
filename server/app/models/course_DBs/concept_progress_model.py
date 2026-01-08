"""
Concept Progress Database Model.

Tracks user progress within each concept, including depth achieved and completion status.
"""
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, Index, UniqueConstraint
from sqlalchemy.sql import func
from app.db.my_sql_config import Base


class ConceptProgress(Base):
    """
    Tracks user progress within a specific concept.

    This table aggregates progress for a concept, tracking:
    - How many topics completed
    - Current depth achieved vs target depth
    - Whether concept is complete
    - Summary of learning for future LLM context

    Each concept progress is uniquely identified by
    user_id, course_id, subject_name, and concept_name.
    """
    __tablename__ = "concept_progress"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Composite unique constraint fields
    user_id = Column(String(255), nullable=False, index=True)
    course_id = Column(String(255), nullable=False, index=True)

    # Subject and concept identification
    subject_name = Column(String(500), nullable=False, index=True)
    concept_name = Column(String(500), nullable=False, index=True)

    # Depth tracking
    current_depth = Column(Integer, default=0, nullable=False, comment="Current depth achieved")
    target_depth = Column(Integer, nullable=False, comment="Target depth from learning plan")

    # Topic counting
    topics_completed = Column(Integer, default=0, nullable=False, comment="Number of topics completed")
    last_topic_name = Column(String(500), nullable=True, comment="Most recent completed topic")

    # Completion status
    completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Learning summary for future LLM context (generated when concept complete)
    learning_summary = Column(Text, nullable=True, comment="Summary of what user learned in this concept")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Table constraints and indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'course_id', 'subject_name', 'concept_name',
                        name='uix_user_course_subject_concept'),
        Index('idx_user_course_concept', 'user_id', 'course_id', 'subject_name'),
    )

    def __repr__(self):
        return f"<ConceptProgress(user={self.user_id}, concept={self.concept_name}, depth={self.current_depth}/{self.target_depth}, topics={self.topics_completed}, complete={self.completed})>"

    @property
    def progress_percentage(self) -> int:
        """Calculate progress percentage based on depth."""
        if self.target_depth == 0:
            return 0
        return min(int((self.current_depth / self.target_depth) * 100), 100)

    @property
    def is_complete(self) -> bool:
        """Check if concept is complete based on depth and minimum topics."""
        return self.current_depth >= self.target_depth and self.topics_completed >= 3

    @property
    def depth_remaining(self) -> int:
        """Calculate remaining depth needed."""
        return max(0, self.target_depth - self.current_depth)
