"""
Course Semantic Memory Database Model.

Stores extracted semantic information from learning plan conversations.
"""
from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.my_sql_config import Base


class CourseSemanticMemory(Base):
    """
    Stores semantic memory extracted from learning plan conversations.

    This memory contains key insights about the learner that will be used
    throughout the course generation and content creation process.

    The memory_data JSONB field contains:
    {
        "prior_knowledge": {
            "level": "beginner|some_knowledge|intermediate|advanced",
            "specific_topics": ["topic1", "topic2"],
            "experience_summary": "Text description of their background"
        },
        "learning_motivation": {
            "primary_goal": "Why they want to learn",
            "specific_objectives": ["objective1", "objective2"],
            "use_case": "What they want to build/achieve"
        },
        "learning_preferences": {
            "depth_preference": "beginner|intermediate|advanced",
            "depth_level": 7,  # 1-10 scale
            "time_commitment": "hours per week or timeline",
            "learning_style": "hands-on|theoretical|balanced"
        },
        "context": {
            "professional_context": "Work/career related info",
            "personal_interests": ["interest1", "interest2"],
            "constraints": ["time", "resources", etc.]
        }
    }
    """
    __tablename__ = "course_semantic_memory"

    # Primary key: combination of user_id and course_id
    user_id = Column(String(255), primary_key=True, nullable=False, index=True)
    course_id = Column(String(255), primary_key=True, nullable=False, index=True)

    # Semantic memory data stored as JSONB
    memory_data = Column(JSONB, nullable=False)

    # Quick access fields (extracted from memory_data for easier querying)
    knowledge_level = Column(
        String(50),
        nullable=True,
        comment="beginner|some_knowledge|intermediate|advanced"
    )
    depth_preference = Column(
        String(50),
        nullable=True,
        comment="beginner|intermediate|advanced"
    )
    depth_level = Column(Integer, nullable=True, comment="1-10 scale")

    # Conversation summary
    conversation_summary = Column(Text, nullable=True, comment="Brief summary of the planning conversation")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<CourseSemanticMemory(user_id={self.user_id}, course_id={self.course_id}, level={self.knowledge_level})>"
