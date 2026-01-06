"""
Pydantic schemas for Unified Learning Context.

Defines the structure for the unified context object that combines
all memory types for AI agents.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

from app.context.schemas.learner_profile import (
    LearnerProfile,
    SubjectConfig,
    LearningStrategy,
    Prerequisites,
    Misconception,
    Milestone,
    DepthLevel,
    LearningStyle,
    ProficiencyLevel,
)
from app.context.schemas.learning_event import (
    LearningEventResponse,
    LearningProgress,
    LearningEmotion,
)


class SubjectMessage(BaseModel):
    """Schema for a message in subject-specific short-term memory."""
    model_config = ConfigDict(populate_by_name=True)
    
    role: Literal["user", "assistant"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: float = Field(..., description="Unix timestamp")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Message metadata (topic_focus, difficulty_level, interaction_type)"
    )


class ShortTermContext(BaseModel):
    """Schema for short-term memory context."""
    model_config = ConfigDict(populate_by_name=True)
    
    recent_messages: List[SubjectMessage] = Field(
        default_factory=list,
        description="Recent conversation messages for this subject"
    )
    message_count: int = Field(default=0, description="Number of messages in memory")
    current_topic_focus: Optional[str] = Field(
        default=None,
        description="Current topic being discussed"
    )
    session_start_time: Optional[float] = Field(
        default=None,
        description="Session start timestamp"
    )
    session_duration_minutes: Optional[float] = Field(
        default=None,
        description="Current session duration in minutes"
    )
    last_interaction_type: Optional[str] = Field(
        default=None,
        description="Type of last interaction (question, explanation, practice)"
    )


class LearnerProfileContext(BaseModel):
    """Schema for learner profile context (simplified for AI consumption)."""
    model_config = ConfigDict(populate_by_name=True)
    
    goal: str = Field(..., description="User's learning goal")
    depth: DepthLevel = Field(..., description="Desired depth level")
    purpose: str = Field(..., description="Learning purpose")
    skill_level: ProficiencyLevel = Field(..., description="Current skill level")
    learning_style: List[LearningStyle] = Field(
        default_factory=list,
        description="Preferred learning styles"
    )
    known_prerequisites: List[str] = Field(
        default_factory=list,
        description="Prerequisites user already knows"
    )
    topics_to_learn: List[str] = Field(
        default_factory=list,
        description="Specific topics user wants to learn"
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="Learning constraints"
    )
    time_commitment: Optional[str] = Field(
        default=None,
        description="Time commitment"
    )
    prior_experience: Optional[str] = Field(
        default=None,
        description="Prior experience description"
    )


class SubjectKnowledgeContext(BaseModel):
    """Schema for subject knowledge context (from predefined templates)."""
    model_config = ConfigDict(populate_by_name=True)
    
    subject_name: str = Field(..., description="Subject name")
    category: str = Field(default="general", description="Subject category")
    strategies: LearningStrategy = Field(..., description="Learning strategies")
    prerequisites: Prerequisites = Field(..., description="Subject prerequisites")
    current_milestone: Optional[Milestone] = Field(
        default=None,
        description="Current milestone user is working on"
    )
    next_milestone: Optional[Milestone] = Field(
        default=None,
        description="Next milestone to achieve"
    )
    relevant_misconceptions: List[Misconception] = Field(
        default_factory=list,
        description="Misconceptions relevant to current topic"
    )
    key_concepts: List[str] = Field(
        default_factory=list,
        description="Key concepts in this subject"
    )
    difficulty_rating: int = Field(default=5, description="Subject difficulty (1-10)")


class LearningHistoryContext(BaseModel):
    """Schema for learning history context (from episodic memory)."""
    model_config = ConfigDict(populate_by_name=True)
    
    # Recent significant events
    recent_breakthroughs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Recent breakthrough moments"
    )
    recent_confusions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Recent confusion moments"
    )
    
    # Topic progress
    mastered_topics: List[str] = Field(
        default_factory=list,
        description="Topics user has mastered"
    )
    struggling_topics: List[str] = Field(
        default_factory=list,
        description="Topics user is struggling with"
    )
    in_progress_topics: List[str] = Field(
        default_factory=list,
        description="Topics currently in progress"
    )
    
    # Learning patterns
    effective_explanations: List[str] = Field(
        default_factory=list,
        description="Explanation types that work well"
    )
    effective_examples: List[str] = Field(
        default_factory=list,
        description="Example types that work well"
    )
    common_question_patterns: List[str] = Field(
        default_factory=list,
        description="Common types of questions user asks"
    )
    
    # Progress metrics
    total_sessions: int = Field(default=0, description="Total learning sessions")
    total_time_minutes: float = Field(default=0, description="Total time spent")
    average_session_minutes: float = Field(default=0, description="Average session duration")
    practice_score_trend: Optional[str] = Field(
        default=None,
        description="Trend in practice scores (improving, stable, declining)"
    )
    
    # Emotional patterns
    dominant_emotion: Optional[LearningEmotion] = Field(
        default=None,
        description="Most common emotion during learning"
    )
    emotional_triggers: Dict[str, str] = Field(
        default_factory=dict,
        description="What triggers certain emotions"
    )
    
    # Last activity
    last_topic: Optional[str] = Field(default=None, description="Last topic studied")
    last_activity_time: Optional[datetime] = Field(
        default=None,
        description="Last activity timestamp"
    )


class UnifiedLearningContext(BaseModel):
    """
    Unified Learning Context - combines all memory types for AI agents.
    
    This is the main context object passed to the learning AI agent,
    providing comprehensive information about the learner and their journey.
    """
    model_config = ConfigDict(populate_by_name=True)
    
    # Identifiers
    user_id: str = Field(..., description="User identifier")
    subject: str = Field(..., description="Subject being learned")
    subject_id: str = Field(..., description="Subject identifier")
    
    # Memory components
    short_term: ShortTermContext = Field(
        default_factory=ShortTermContext,
        description="Short-term conversation context"
    )
    learner_profile: Optional[LearnerProfileContext] = Field(
        default=None,
        description="Learner's profile and preferences"
    )
    subject_knowledge: Optional[SubjectKnowledgeContext] = Field(
        default=None,
        description="Subject-specific learning intelligence"
    )
    learning_history: Optional[LearningHistoryContext] = Field(
        default=None,
        description="Learning history and patterns"
    )
    
    # Context metadata
    context_generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this context was generated"
    )
    context_version: str = Field(
        default="1.0",
        description="Context schema version"
    )
    
    def to_system_prompt(self) -> str:
        """
        Convert the context to a formatted string for system prompt injection.
        
        Returns:
            Formatted context string for AI agent.
        """
        lines = []
        lines.append(f"\n=== LEARNING CONTEXT FOR {self.subject.upper()} ===\n")
        
        # Learner Profile
        if self.learner_profile:
            lines.append("## Learner Profile")
            lines.append(f"- Goal: {self.learner_profile.goal}")
            lines.append(f"- Depth Level: {self.learner_profile.depth.value}")
            lines.append(f"- Purpose: {self.learner_profile.purpose}")
            lines.append(f"- Current Skill Level: {self.learner_profile.skill_level.value}")
            if self.learner_profile.learning_style:
                styles = ", ".join([s.value for s in self.learner_profile.learning_style])
                lines.append(f"- Preferred Learning Styles: {styles}")
            if self.learner_profile.known_prerequisites:
                lines.append(f"- Already Knows: {', '.join(self.learner_profile.known_prerequisites)}")
            if self.learner_profile.topics_to_learn:
                lines.append(f"- Wants to Learn: {', '.join(self.learner_profile.topics_to_learn)}")
            if self.learner_profile.constraints:
                lines.append(f"- Constraints: {', '.join(self.learner_profile.constraints)}")
            lines.append("")
        
        # Subject Knowledge
        if self.subject_knowledge:
            lines.append("## Subject Learning Strategies")
            lines.append(f"- Recommended Approach: {self.subject_knowledge.strategies.recommended_approach}")
            if self.subject_knowledge.strategies.effective_techniques:
                lines.append(f"- Effective Techniques: {', '.join(self.subject_knowledge.strategies.effective_techniques)}")
            if self.subject_knowledge.current_milestone:
                lines.append(f"- Current Milestone: {self.subject_knowledge.current_milestone.name}")
            if self.subject_knowledge.relevant_misconceptions:
                lines.append("- Watch for Misconceptions:")
                for m in self.subject_knowledge.relevant_misconceptions[:3]:
                    lines.append(f"  - {m.topic}: {m.misconception}")
            lines.append("")
        
        # Learning History
        if self.learning_history:
            lines.append("## Learning History")
            if self.learning_history.mastered_topics:
                lines.append(f"- Mastered Topics: {', '.join(self.learning_history.mastered_topics)}")
            if self.learning_history.struggling_topics:
                lines.append(f"- Struggling With: {', '.join(self.learning_history.struggling_topics)}")
            if self.learning_history.effective_explanations:
                lines.append(f"- What Works: {', '.join(self.learning_history.effective_explanations)}")
            if self.learning_history.recent_breakthroughs:
                lines.append(f"- Recent Breakthroughs: {len(self.learning_history.recent_breakthroughs)}")
            lines.append("")
        
        # Short-term Context
        if self.short_term and self.short_term.current_topic_focus:
            lines.append("## Current Session")
            lines.append(f"- Current Topic: {self.short_term.current_topic_focus}")
            if self.short_term.session_duration_minutes:
                lines.append(f"- Session Duration: {self.short_term.session_duration_minutes:.0f} minutes")
            lines.append("")
        
        lines.append("=== END LEARNING CONTEXT ===\n")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for JSON serialization."""
        return self.model_dump(mode="json")

