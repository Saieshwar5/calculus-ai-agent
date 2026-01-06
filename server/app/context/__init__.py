"""
Context Management System for Learning Agent Platform.

Provides subject-based memory management for learning AI agents:

1. Short-term Memory (Redis) - Conversation history per user per subject
2. Semantic Memory (PostgreSQL) - Learner profiles and subject configurations
3. Episodic Memory (PostgreSQL) - Learning events and progress tracking

Each memory type supports CRUD operations organized by user_id and subject.
"""

# Short-term Memory (Redis)
from app.context.short_term import (
    SubjectShortTermMemory,
    get_subject_memory_manager,
)

# Semantic Memory (PostgreSQL) - Learner Profiles
from app.context.semantic import (
    LearnerProfileManager,
    get_learner_profile_manager,
)
from app.models.learning_context_DB import LearnerSubjectProfile

# Episodic Memory (PostgreSQL) - Learning Events
from app.context.episodic import (
    LearningEpisodicMemory,
    get_learning_episodic_memory,
)
from app.models.learning_context_DB import LearningEpisode

# Context Builder
from app.context.builder import (
    ContextBuilder,
    build_learning_context,
)

# Schemas
from app.context.schemas import (
    # Learner profile schemas
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
    # Learning event schemas
    LearningEventType,
    LearningEventSubtype,
    LearningEventContext,
    LearningEventCreate,
    LearningEventResponse,
    LearningProgress,
    # Context schemas
    ShortTermContext,
    LearnerProfileContext,
    SubjectKnowledgeContext,
    LearningHistoryContext,
    UnifiedLearningContext,
    SubjectMessage,
)

# Templates
from app.context.templates import (
    SubjectTemplateManager,
    get_template_manager,
    get_or_create_template,
    create_dynamic_template,
)

__all__ = [
    # Short-term Memory
    "SubjectShortTermMemory",
    "get_subject_memory_manager",
    # Semantic Memory
    "LearnerSubjectProfile",
    "LearnerProfileManager",
    "get_learner_profile_manager",
    # Episodic Memory
    "LearningEpisode",
    "LearningEpisodicMemory",
    "get_learning_episodic_memory",
    # Context Builder
    "ContextBuilder",
    "build_learning_context",
    # Schemas
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
    "LearningEventType",
    "LearningEventSubtype",
    "LearningEventContext",
    "LearningEventCreate",
    "LearningEventResponse",
    "LearningProgress",
    "ShortTermContext",
    "LearnerProfileContext",
    "SubjectKnowledgeContext",
    "LearningHistoryContext",
    "UnifiedLearningContext",
    "SubjectMessage",
    # Templates
    "SubjectTemplateManager",
    "get_template_manager",
    "get_or_create_template",
    "create_dynamic_template",
]
