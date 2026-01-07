"""
Learning Plan Database Model.

Stores structured learning plans with subjects and concepts in JSONB format.
"""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.my_sql_config import Base


class LearningPlan(Base):
    """
    Stores learning plans created through conversational planning.

    The plan_data JSONB field contains the complete structured plan:
    {
        "title": "Course Title",
        "description": "Course description",
        "subjects": [
            {
                "name": "Subject Name",
                "depth": "beginner|intermediate|advanced",
                "duration": 120,
                "concepts": [
                    {"name": "Concept 1", "depth": 8},
                    {"name": "Concept 2", "depth": 10}
                ]
            }
        ]
    }
    """
    __tablename__ = "learning_plans"

    # Primary key: combination of user_id and course_id
    user_id = Column(String(255), primary_key=True, nullable=False, index=True)
    course_id = Column(String(255), primary_key=True, nullable=False, index=True)

    # Plan metadata
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # Complete plan structure stored as JSONB
    plan_data = Column(JSONB, nullable=False)

    # Status tracking
    status = Column(
        String(50),
        nullable=False,
        default="draft",
        comment="draft|active|completed|archived"
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<LearningPlan(user_id={self.user_id}, course_id={self.course_id}, title={self.title})>"
