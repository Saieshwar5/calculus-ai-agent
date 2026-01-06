"""
Pydantic schemas for the Learning Context Memory System.

Provides type-safe schemas for:
- Learner profiles and subject configurations
- Learning events and episodes
- Unified context objects for AI agents
"""
from app.context.schemas.learner_profile import (
    LearnerProfile,
    CurrentSkillSet,
    SubjectConfig,
    LearningStrategy,
    Prerequisites,
    Misconception,
    Milestone,
    LearnerSubjectProfileCreate,
    LearnerSubjectProfileUpdate,
    LearnerSubjectProfileResponse,
)
from app.context.schemas.learning_event import (
    LearningEventType,
    LearningEventSubtype,
    LearningEventContext,
    LearningEventCreate,
    LearningEventResponse,
    LearningProgress,
)
from app.context.schemas.context import (
    ShortTermContext,
    LearnerProfileContext,
    SubjectKnowledgeContext,
    LearningHistoryContext,
    UnifiedLearningContext,
    SubjectMessage,
)

__all__ = [
    # Learner profile schemas
    "LearnerProfile",
    "CurrentSkillSet",
    "SubjectConfig",
    "LearningStrategy",
    "Prerequisites",
    "Misconception",
    "Milestone",
    "LearnerSubjectProfileCreate",
    "LearnerSubjectProfileUpdate",
    "LearnerSubjectProfileResponse",
    # Learning event schemas
    "LearningEventType",
    "LearningEventSubtype",
    "LearningEventContext",
    "LearningEventCreate",
    "LearningEventResponse",
    "LearningProgress",
    # Context schemas
    "ShortTermContext",
    "LearnerProfileContext",
    "SubjectKnowledgeContext",
    "LearningHistoryContext",
    "UnifiedLearningContext",
    "SubjectMessage",
]

