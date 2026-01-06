"""
Pydantic schemas for Learning Events (Episodic Memory).

Defines the structure for tracking learning events like breakthroughs,
confusion moments, progress, and interactions.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class LearningEventType(str, Enum):
    """Main categories of learning events."""
    UNDERSTANDING = "understanding"  # Breakthroughs, confusion, mastery
    PROGRESS = "progress"            # Topic completion, time spent, difficulty
    INTERACTION = "interaction"       # Questions, explanations, examples, practice


class LearningEventSubtype(str, Enum):
    """Specific types of learning events."""
    # Understanding events
    BREAKTHROUGH = "breakthrough"     # User finally understood something
    CONFUSION = "confusion"           # User is confused about something
    MASTERY = "mastery"               # User has mastered a topic
    AHA_MOMENT = "aha_moment"         # Sudden understanding
    
    # Progress events
    TOPIC_STARTED = "topic_started"   # Started learning a new topic
    TOPIC_COMPLETE = "topic_complete" # Completed a topic
    MILESTONE_REACHED = "milestone_reached"  # Reached a learning milestone
    TIME_SPENT = "time_spent"         # Significant time spent on topic
    DIFFICULTY_FACED = "difficulty_faced"  # Encountered difficulty
    
    # Interaction events
    QUESTION_ASKED = "question_asked"     # User asked a question
    EXPLANATION_GIVEN = "explanation_given"  # AI gave an explanation
    EXAMPLE_USED = "example_used"         # An example was used effectively
    PRACTICE_DONE = "practice_done"       # User did practice problems
    FEEDBACK_RECEIVED = "feedback_received"  # User received feedback


class LearningEmotion(str, Enum):
    """Emotions during learning."""
    EXCITED = "excited"
    CONFIDENT = "confident"
    CURIOUS = "curious"
    NEUTRAL = "neutral"
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"
    OVERWHELMED = "overwhelmed"
    MOTIVATED = "motivated"
    SATISFIED = "satisfied"


class LearningEventContext(BaseModel):
    """Context information for a learning event."""
    model_config = ConfigDict(populate_by_name=True)
    
    topic: str = Field(..., description="The topic being learned")
    subtopic: Optional[str] = Field(default=None, description="Specific subtopic")
    trigger: Optional[str] = Field(
        default=None,
        description="What triggered this event (e.g., 'visual diagram', 'practice problem')"
    )
    related_topics: List[str] = Field(
        default_factory=list,
        description="Related topics involved"
    )
    difficulty_rating: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
        description="Difficulty rating (1-10)"
    )
    time_spent_minutes: Optional[float] = Field(
        default=None,
        description="Time spent on this topic/event in minutes"
    )
    explanation_type: Optional[str] = Field(
        default=None,
        description="Type of explanation used (visual, step-by-step, analogy, etc.)"
    )
    example_description: Optional[str] = Field(
        default=None,
        description="Description of example that was effective"
    )
    question_text: Optional[str] = Field(
        default=None,
        description="The question that was asked"
    )
    practice_type: Optional[str] = Field(
        default=None,
        description="Type of practice (problem-solving, quiz, coding, etc.)"
    )
    practice_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Score on practice (0-100)"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes about the event"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional flexible metadata"
    )


class LearningEventCreate(BaseModel):
    """Schema for creating a learning event."""
    model_config = ConfigDict(populate_by_name=True)
    
    user_id: str = Field(..., description="User identifier")
    subject_id: str = Field(..., description="Subject identifier")
    event_type: LearningEventType = Field(..., description="Type of learning event")
    event_subtype: LearningEventSubtype = Field(..., description="Specific subtype of event")
    event_description: str = Field(
        ...,
        min_length=1,
        description="Description of what happened"
    )
    context: LearningEventContext = Field(..., description="Event context")
    emotion: Optional[LearningEmotion] = Field(
        default=LearningEmotion.NEUTRAL,
        description="Emotion during the event"
    )
    importance: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Importance score (1-10)"
    )
    event_time: Optional[datetime] = Field(
        default=None,
        description="When the event occurred (defaults to now)"
    )


class LearningEventResponse(BaseModel):
    """Schema for learning event response."""
    model_config = ConfigDict(populate_by_name=True)
    
    id: int = Field(..., description="Event ID")
    user_id: str = Field(..., description="User identifier")
    subject_id: str = Field(..., description="Subject identifier")
    event_type: LearningEventType = Field(..., description="Type of learning event")
    event_subtype: LearningEventSubtype = Field(..., description="Specific subtype")
    event_description: str = Field(..., description="Event description")
    context: LearningEventContext = Field(..., description="Event context")
    emotion: Optional[LearningEmotion] = Field(default=None, description="Emotion")
    importance: int = Field(..., description="Importance score")
    event_time: datetime = Field(..., description="When the event occurred")
    created_at: datetime = Field(..., description="Creation timestamp")


class LearningProgress(BaseModel):
    """Schema for aggregated learning progress."""
    model_config = ConfigDict(populate_by_name=True)
    
    user_id: str = Field(..., description="User identifier")
    subject_id: str = Field(..., description="Subject identifier")
    
    # Topic progress
    topics_started: List[str] = Field(default_factory=list, description="Topics started")
    topics_completed: List[str] = Field(default_factory=list, description="Topics completed")
    topics_mastered: List[str] = Field(default_factory=list, description="Topics mastered")
    struggling_topics: List[str] = Field(default_factory=list, description="Topics user is struggling with")
    
    # Milestone progress
    milestones_reached: List[str] = Field(default_factory=list, description="Milestones reached")
    current_milestone: Optional[str] = Field(default=None, description="Current milestone")
    
    # Time tracking
    total_time_spent_minutes: float = Field(default=0, description="Total time spent learning")
    average_session_minutes: float = Field(default=0, description="Average session duration")
    
    # Understanding metrics
    breakthrough_count: int = Field(default=0, description="Number of breakthroughs")
    confusion_count: int = Field(default=0, description="Number of confusion moments")
    
    # Interaction metrics
    questions_asked: int = Field(default=0, description="Number of questions asked")
    practice_sessions: int = Field(default=0, description="Number of practice sessions")
    average_practice_score: Optional[float] = Field(default=None, description="Average practice score")
    
    # Effective learning patterns
    effective_explanations: List[str] = Field(
        default_factory=list,
        description="Types of explanations that work well"
    )
    effective_examples: List[str] = Field(
        default_factory=list,
        description="Types of examples that work well"
    )
    
    # Overall assessment
    estimated_proficiency: Optional[str] = Field(
        default=None,
        description="Estimated current proficiency level"
    )
    last_activity: Optional[datetime] = Field(
        default=None,
        description="Last learning activity timestamp"
    )

