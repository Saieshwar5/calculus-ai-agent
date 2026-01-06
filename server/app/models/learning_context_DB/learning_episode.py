"""
Learning Episode Model.

Stores learning events for episodic memory in the learning context system.
Tracks meaningful learning moments like breakthroughs, confusion, progress, and interactions.

Event Types:
- understanding: breakthroughs, confusion, mastery, aha moments
- progress: topic started/completed, milestones, time spent, difficulty faced
- interaction: questions asked, explanations given, examples used, practice done
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.my_sql_config import Base


class LearningEpisode(Base):
    """
    SQLAlchemy model for learning episodes (events).
    
    Stores learning events with optional vector embeddings for semantic search.
    Each episode represents a meaningful learning moment that can be used to
    personalize future interactions.
    
    Key Format: id (auto-increment), indexed by (user_id, subject_id, event_type)
    """
    __tablename__ = "learning_episodes"
    
    id = Column(
        Integer, 
        primary_key=True, 
        index=True, 
        autoincrement=True
    )
    
    user_id = Column(
        String(255), 
        index=True, 
        nullable=False, 
        comment="User identifier"
    )
    
    subject_id = Column(
        String(255), 
        index=True, 
        nullable=False, 
        comment="Subject identifier (normalized)"
    )
    
    # Event Classification
    # event_type: "understanding" | "progress" | "interaction"
    event_type = Column(
        String(50), 
        index=True, 
        nullable=False, 
        comment="Event type (understanding/progress/interaction)"
    )
    
    # event_subtype examples:
    # - understanding: breakthrough, confusion, mastery, aha_moment
    # - progress: topic_started, topic_complete, milestone_reached, time_spent, difficulty_faced
    # - interaction: question_asked, explanation_given, example_used, practice_done
    event_subtype = Column(
        String(50), 
        index=True, 
        nullable=False, 
        comment="Event subtype (breakthrough/confusion/mastery/question_asked/etc)"
    )
    
    # Event Description - What happened
    event_description = Column(
        Text, 
        nullable=False, 
        comment="Description of what happened (e.g., 'User understood recursion after tree example')"
    )
    
    # Context - Detailed information about the event
    # Structure:
    # {
    #   "topic": "recursion",
    #   "subtopic": "tree traversal",
    #   "trigger": "visual tree diagram",
    #   "related_topics": ["functions", "data structures"],
    #   "difficulty_rating": 7,
    #   "time_spent_minutes": 30,
    #   "explanation_type": "visual",
    #   "example_description": "Binary tree traversal animation",
    #   "question_text": "How does recursion work?",
    #   "practice_type": "coding exercise",
    #   "practice_score": 85,
    #   "notes": "Additional notes"
    # }
    context = Column(
        JSONB, 
        nullable=False, 
        default=dict, 
        comment="Event context (topic, trigger, related topics, scores, etc.)"
    )
    
    # Emotion during the event
    # Values: excited, confident, curious, neutral, confused, frustrated, overwhelmed, motivated, satisfied
    emotion = Column(
        String(50), 
        index=True, 
        nullable=True, 
        comment="Emotion during the event (excited/confused/frustrated/etc)"
    )
    
    # Importance score (1-10) - How significant this event is
    # Higher importance = more likely to be included in context
    importance = Column(
        Integer, 
        index=True, 
        default=5, 
        comment="Importance score (1-10), higher = more significant"
    )
    
    # When the event occurred
    event_time = Column(
        DateTime(timezone=True), 
        index=True, 
        nullable=False, 
        comment="When the event occurred"
    )
    
    # Optional vector embedding for semantic similarity search
    # Uses OpenAI text-embedding-3-small: 1536 dimensions
    # Can be used to find similar learning experiences
    event_embedding = Column(
        Vector(1536), 
        nullable=True, 
        comment="Vector embedding for semantic search (optional)"
    )
    
    # Metadata
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        comment="When this record was created"
    )
    
    # Indexes for efficient querying
    __table_args__ = (
        # Composite index for common query patterns
        Index('ix_episode_user_subject', 'user_id', 'subject_id'),
        Index('ix_episode_user_subject_type', 'user_id', 'subject_id', 'event_type'),
        Index('ix_episode_user_subject_subtype', 'user_id', 'subject_id', 'event_subtype'),
        Index('ix_episode_user_time', 'user_id', 'event_time'),
        Index('ix_episode_importance', 'user_id', 'subject_id', 'importance'),
    )
    
    def __repr__(self):
        return f"<LearningEpisode(id={self.id}, user_id={self.user_id}, subject_id={self.subject_id}, type={self.event_type}/{self.event_subtype})>"
    
    def get_topic(self) -> str:
        """Get the topic from context."""
        return self.context.get("topic", "")
    
    def get_trigger(self) -> str:
        """Get what triggered this event."""
        return self.context.get("trigger", "")
    
    def get_difficulty_rating(self) -> int:
        """Get the difficulty rating (1-10)."""
        return self.context.get("difficulty_rating", 5)
    
    def get_time_spent_minutes(self) -> float:
        """Get time spent in minutes."""
        return self.context.get("time_spent_minutes", 0)
    
    def get_practice_score(self) -> float:
        """Get practice score (0-100)."""
        return self.context.get("practice_score")
    
    def is_breakthrough(self) -> bool:
        """Check if this is a breakthrough event."""
        return self.event_subtype == "breakthrough"
    
    def is_confusion(self) -> bool:
        """Check if this is a confusion event."""
        return self.event_subtype == "confusion"
    
    def is_high_importance(self) -> bool:
        """Check if this is a high importance event (7+)."""
        return self.importance >= 7

