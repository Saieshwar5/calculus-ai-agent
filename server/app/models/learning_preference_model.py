from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.db.my_sql_config import Base


class LearningPreference(Base):
    """
    SQLAlchemy model for user learning preferences.
    This model represents the learning_preferences table in the database.
    """
    __tablename__ = "learning_preferences"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(255), unique=True, index=True, nullable=False, comment="User identifier")
    
    # Boolean preferences
    web_search = Column(Boolean, default=False, nullable=False)
    youtube_search = Column(Boolean, default=False, nullable=False)
    diagrams_and_flowcharts = Column(Boolean, default=False, nullable=False)
    images_and_illustrations = Column(Boolean, default=False, nullable=False)
    charts_and_graphs = Column(Boolean, default=False, nullable=False)
    mind_maps = Column(Boolean, default=False, nullable=False)
    step_by_step_explanation = Column(Boolean, default=False, nullable=False)
    worked_examples = Column(Boolean, default=False, nullable=False)
    practice_problems = Column(Boolean, default=False, nullable=False)
    learn_through_stories = Column(Boolean, default=False, nullable=False)
    explain_with_real_world_examples = Column(Boolean, default=False, nullable=False)
    analogies_and_comparisons = Column(Boolean, default=False, nullable=False)
    fun_and_curious_facts = Column(Boolean, default=False, nullable=True)
    
    # String preferences
    handling_difficulty = Column(Text, nullable=True, comment="How to handle difficulty")
    
    # Metadata fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<LearningPreference(id={self.id}, user_id={self.user_id})>"


