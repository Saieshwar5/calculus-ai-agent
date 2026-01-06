"""
Learner Subject Profile Model.

Stores learner profiles and subject configurations per user per subject.
This is the semantic memory component of the learning context system.

Each record contains:
- User's learning goals, skills, and preferences for a subject
- Subject-specific learning strategies, prerequisites, and milestones
"""
from sqlalchemy import Column, Integer, String, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.db.my_sql_config import Base


class LearnerSubjectProfile(Base):
    """
    SQLAlchemy model for learner subject profiles.
    
    Stores:
    - learner_profile: User's goals, skills, preferences, constraints
    - subject_config: Learning strategies, prerequisites, milestones, misconceptions
    
    Key Format: (user_id, subject_id) - unique per user per subject
    """
    __tablename__ = "learner_subject_profiles"
    
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
        comment="Subject identifier (normalized, e.g., 'machine_learning')"
    )
    
    # Learner Profile - User's learning information for this subject
    # Structure:
    # {
    #   "learning_goal": "Master Python for data science",
    #   "depth_level": "intermediate",
    #   "purpose": "career",
    #   "current_skill_set": {
    #     "prerequisites_known": ["basic programming"],
    #     "proficiency_level": "beginner",
    #     "prior_experience": "Some JavaScript experience"
    #   },
    #   "specific_topics_to_learn": ["pandas", "numpy", "matplotlib"],
    #   "time_commitment": "10 hours per week",
    #   "preferred_learning_style": ["examples", "practice"],
    #   "constraints": ["limited time", "need practical examples"],
    #   "milestones_reached": ["m1", "m2"],
    #   "current_topic": "data manipulation"
    # }
    learner_profile = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Learner profile (goals, skills, preferences, progress)"
    )
    
    # Subject Configuration - Learning strategies and structure for this subject
    # Structure:
    # {
    #   "subject_id": "python",
    #   "subject_name": "Python Programming",
    #   "category": "programming",
    #   "learning_strategies": {
    #     "recommended_approach": "Start with basics, practice with projects",
    #     "common_sequence": ["syntax", "functions", "classes", "modules"],
    #     "effective_techniques": ["coding exercises", "project-based learning"]
    #   },
    #   "prerequisites": {
    #     "required": [],
    #     "recommended": ["basic computer skills"],
    #     "knowledge_graph": {"functions": ["variables", "control flow"]}
    #   },
    #   "common_misconceptions": [
    #     {"topic": "variables", "misconception": "...", "correction": "..."}
    #   ],
    #   "milestones": [
    #     {"id": "m1", "name": "Python Basics", "topics": ["syntax", "variables"]}
    #   ],
    #   "key_concepts": ["variables", "functions", "classes"]
    # }
    subject_config = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Subject configuration (strategies, prerequisites, milestones)"
    )
    
    # Metadata
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        comment="When this profile was created"
    )
    
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False,
        comment="When this profile was last updated"
    )
    
    # Constraints
    __table_args__ = (
        # Ensure unique combination of user_id and subject_id
        UniqueConstraint('user_id', 'subject_id', name='uq_user_subject_profile'),
        # Index for fast lookups by user
        Index('ix_learner_profile_user_subject', 'user_id', 'subject_id'),
    )
    
    def __repr__(self):
        return f"<LearnerSubjectProfile(id={self.id}, user_id={self.user_id}, subject_id={self.subject_id})>"
    
    def get_learning_goal(self) -> str:
        """Get the user's learning goal for this subject."""
        return self.learner_profile.get("learning_goal", "")
    
    def get_depth_level(self) -> str:
        """Get the desired depth level."""
        return self.learner_profile.get("depth_level", "intermediate")
    
    def get_milestones_reached(self) -> list:
        """Get list of milestone IDs the user has reached."""
        return self.learner_profile.get("milestones_reached", [])
    
    def get_current_topic(self) -> str:
        """Get the current topic the user is learning."""
        return self.learner_profile.get("current_topic", "")
    
    def get_subject_name(self) -> str:
        """Get the display name of the subject."""
        return self.subject_config.get("subject_name", self.subject_id.replace("_", " ").title())

