"""
Pydantic schemas for Learner Subject Profile.

Defines the structure for storing learner goals, skills, preferences,
and subject-specific configurations.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class DepthLevel(str, Enum):
    """Learning depth levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class LearningPurpose(str, Enum):
    """Purpose of learning."""
    CAREER = "career"
    ACADEMIC = "academic"
    HOBBY = "hobby"
    CERTIFICATION = "certification"
    PERSONAL_GROWTH = "personal_growth"


class LearningStyle(str, Enum):
    """Preferred learning styles."""
    VISUAL = "visual"
    READING = "reading"
    PRACTICE = "practice"
    EXAMPLES = "examples"
    INTERACTIVE = "interactive"
    VIDEO = "video"


class ProficiencyLevel(str, Enum):
    """Proficiency level for skills."""
    NONE = "none"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class CurrentSkillSet(BaseModel):
    """Schema for user's current skill set in a subject."""
    model_config = ConfigDict(populate_by_name=True)
    
    prerequisites_known: List[str] = Field(
        default_factory=list,
        description="List of prerequisite topics the user already knows"
    )
    proficiency_level: ProficiencyLevel = Field(
        default=ProficiencyLevel.BEGINNER,
        description="Current proficiency level in the subject"
    )
    prior_experience: Optional[str] = Field(
        default=None,
        description="Description of prior experience with the subject"
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="Topics or areas where the user is strong"
    )
    weaknesses: List[str] = Field(
        default_factory=list,
        description="Topics or areas where the user needs improvement"
    )


class LearnerProfile(BaseModel):
    """
    Schema for learner profile - captures user's learning goals and preferences.
    This is stored per user per subject.
    """
    model_config = ConfigDict(populate_by_name=True)
    
    learning_goal: str = Field(
        ...,
        min_length=1,
        description="User's goal for learning this subject (e.g., 'Master calculus for ML')"
    )
    depth_level: DepthLevel = Field(
        default=DepthLevel.INTERMEDIATE,
        description="How deep the user wants to go"
    )
    purpose: LearningPurpose = Field(
        default=LearningPurpose.PERSONAL_GROWTH,
        description="Why the user is learning this subject"
    )
    current_skill_set: CurrentSkillSet = Field(
        default_factory=CurrentSkillSet,
        description="User's current skills and experience"
    )
    specific_topics_to_learn: List[str] = Field(
        default_factory=list,
        description="Specific topics the user wants to learn"
    )
    time_commitment: Optional[str] = Field(
        default=None,
        description="Time commitment (e.g., '5 hours per week')"
    )
    preferred_learning_style: List[LearningStyle] = Field(
        default_factory=lambda: [LearningStyle.EXAMPLES],
        description="Preferred ways of learning"
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="Learning constraints (e.g., 'limited time', 'needs real-world examples')"
    )
    additional_notes: Optional[str] = Field(
        default=None,
        description="Any additional notes about learning preferences"
    )


# Subject Configuration Schemas

class LearningStrategy(BaseModel):
    """Schema for subject-specific learning strategies."""
    model_config = ConfigDict(populate_by_name=True)
    
    recommended_approach: str = Field(
        ...,
        description="Recommended approach for learning this subject"
    )
    common_sequence: List[str] = Field(
        default_factory=list,
        description="Common learning sequence for topics"
    )
    effective_techniques: List[str] = Field(
        default_factory=list,
        description="Effective learning techniques for this subject"
    )
    tips: List[str] = Field(
        default_factory=list,
        description="Tips for effective learning"
    )


class Prerequisites(BaseModel):
    """Schema for subject prerequisites."""
    model_config = ConfigDict(populate_by_name=True)
    
    required: List[str] = Field(
        default_factory=list,
        description="Required prerequisites before starting"
    )
    recommended: List[str] = Field(
        default_factory=list,
        description="Recommended but not required prerequisites"
    )
    knowledge_graph: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Topic -> prerequisites mapping"
    )


class Misconception(BaseModel):
    """Schema for common misconceptions in a subject."""
    model_config = ConfigDict(populate_by_name=True)
    
    topic: str = Field(..., description="Topic where misconception occurs")
    misconception: str = Field(..., description="The common misconception")
    correction: str = Field(..., description="The correct understanding")
    why_it_matters: Optional[str] = Field(
        default=None,
        description="Why understanding this correctly matters"
    )


class Milestone(BaseModel):
    """Schema for learning milestones."""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(..., description="Unique milestone identifier")
    name: str = Field(..., description="Milestone name")
    description: Optional[str] = Field(default=None, description="Milestone description")
    topics: List[str] = Field(default_factory=list, description="Topics covered in this milestone")
    order: int = Field(default=0, description="Order in the learning path")
    estimated_hours: Optional[float] = Field(default=None, description="Estimated hours to complete")


class SubjectConfig(BaseModel):
    """
    Schema for predefined subject configuration.
    Contains learning intelligence for a specific subject.
    """
    model_config = ConfigDict(populate_by_name=True)
    
    subject_id: str = Field(..., description="Unique subject identifier")
    subject_name: str = Field(..., description="Display name of the subject")
    description: Optional[str] = Field(default=None, description="Subject description")
    category: str = Field(default="general", description="Subject category (math, programming, science)")
    
    learning_strategies: LearningStrategy = Field(
        default_factory=lambda: LearningStrategy(
            recommended_approach="Start with fundamentals and build progressively",
            common_sequence=[],
            effective_techniques=["practice", "examples", "visualization"]
        ),
        description="Learning strategies for this subject"
    )
    prerequisites: Prerequisites = Field(
        default_factory=Prerequisites,
        description="Prerequisites for this subject"
    )
    common_misconceptions: List[Misconception] = Field(
        default_factory=list,
        description="Common misconceptions in this subject"
    )
    milestones: List[Milestone] = Field(
        default_factory=list,
        description="Learning milestones for this subject"
    )
    key_concepts: List[str] = Field(
        default_factory=list,
        description="Key concepts in this subject"
    )
    difficulty_rating: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Overall difficulty rating (1-10)"
    )


# API Request/Response Schemas

class LearnerSubjectProfileCreate(BaseModel):
    """Schema for creating a learner subject profile."""
    model_config = ConfigDict(populate_by_name=True)
    
    user_id: str = Field(..., description="User identifier")
    subject_id: str = Field(..., description="Subject identifier")
    learner_profile: LearnerProfile = Field(..., description="Learner profile data")
    subject_config: Optional[SubjectConfig] = Field(
        default=None,
        description="Optional custom subject config (uses predefined if not provided)"
    )


class LearnerSubjectProfileUpdate(BaseModel):
    """Schema for updating a learner subject profile."""
    model_config = ConfigDict(populate_by_name=True)
    
    learner_profile: Optional[LearnerProfile] = Field(
        default=None,
        description="Updated learner profile"
    )
    subject_config: Optional[SubjectConfig] = Field(
        default=None,
        description="Updated subject config"
    )


class LearnerSubjectProfileResponse(BaseModel):
    """Schema for learner subject profile response."""
    model_config = ConfigDict(populate_by_name=True)
    
    id: int = Field(..., description="Profile ID")
    user_id: str = Field(..., description="User identifier")
    subject_id: str = Field(..., description="Subject identifier")
    learner_profile: LearnerProfile = Field(..., description="Learner profile data")
    subject_config: SubjectConfig = Field(..., description="Subject configuration")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

