"""
Topic Completion Database Model.

Tracks which topics have been completed for each user's learning plan to prevent repetition
and measure depth progression within concepts.
"""
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, Index, UniqueConstraint
from sqlalchemy.sql import func
from app.db.my_sql_config import Base


class TopicCompletion(Base):
    """
    Tracks completed topics for learning plans with depth progression.

    This table prevents repetition by recording which topics have been covered
    for each user's learning plan concept. Each topic is uniquely identified by
    the combination of user_id, course_id, subject_name, concept_name, and topic_name.

    Tracks depth_increment to measure progressive learning within a concept.
    """
    __tablename__ = "topic_completions"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Composite unique constraint fields
    user_id = Column(String(255), nullable=False, index=True)
    course_id = Column(String(255), nullable=False, index=True)

    # Subject, concept, and topic identification
    subject_name = Column(String(500), nullable=False, index=True)
    concept_name = Column(String(500), nullable=False, index=True, comment="Concept from learning plan")
    topic_name = Column(String(500), nullable=False)

    # Completion tracking
    completed = Column(Boolean, default=True, nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Depth tracking - how much depth this topic added
    depth_increment = Column(Integer, default=1, nullable=False, comment="Depth points added by this topic (1-3)")

    # Optional metadata - brief snapshot of content delivered
    content_snapshot = Column(Text, nullable=True, comment="Brief snapshot of content delivered")

    # Full content for navigation history
    full_content = Column(Text, nullable=True, comment="Full educational content delivered")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Table constraints and indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'course_id', 'subject_name', 'concept_name', 'topic_name',
                        name='uix_user_course_subject_concept_topic'),
        Index('idx_user_course_completions', 'user_id', 'course_id'),
        Index('idx_concept_completions', 'user_id', 'course_id', 'subject_name', 'concept_name'),
    )

    def __repr__(self):
        return f"<TopicCompletion(user_id={self.user_id}, course={self.course_id}, subject={self.subject_name}, concept={self.concept_name}, topic={self.topic_name}, depth+={self.depth_increment})>"
