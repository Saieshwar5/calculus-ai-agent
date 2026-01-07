"""
Topic Completion Database Model.

Tracks which topics have been completed for each user's learning plan to prevent repetition.
"""
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, Index, UniqueConstraint
from sqlalchemy.sql import func
from app.db.my_sql_config import Base


class TopicCompletion(Base):
    """
    Tracks completed topics for learning plans.

    This table prevents repetition by recording which topics have been covered
    for each user's learning plan subject. Each topic is uniquely identified by
    the combination of user_id, course_id, subject_name, and topic_name.
    """
    __tablename__ = "topic_completions"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Composite unique constraint fields
    user_id = Column(String(255), nullable=False, index=True)
    course_id = Column(String(255), nullable=False, index=True)

    # Subject and topic identification
    subject_name = Column(String(500), nullable=False, index=True)
    topic_name = Column(String(500), nullable=False)

    # Completion tracking
    completed = Column(Boolean, default=True, nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Optional metadata - brief snapshot of content delivered
    content_snapshot = Column(Text, nullable=True, comment="Brief snapshot of content delivered")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Table constraints and indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'course_id', 'subject_name', 'topic_name',
                        name='uix_user_course_subject_topic'),
        Index('idx_user_course_completions', 'user_id', 'course_id'),
    )

    def __repr__(self):
        return f"<TopicCompletion(user_id={self.user_id}, course_id={self.course_id}, subject={self.subject_name}, topic={self.topic_name})>"
