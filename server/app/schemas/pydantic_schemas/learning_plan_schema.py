"""
Pydantic schemas for learning plan creation and management.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Concept(BaseModel):
    """Individual concept within a subject."""
    name: str = Field(..., description="Name of the concept")
    depth: int = Field(default=5, description="Depth level (1-10, where 10 is most advanced)")


class Subject(BaseModel):
    """Subject within a learning plan."""
    name: str = Field(..., description="Name of the subject")
    depth: str = Field(..., description="Learning depth: beginner, intermediate, or advanced")
    duration: int = Field(..., description="Estimated duration in minutes")
    concepts: Optional[List[Concept]] = Field(default_factory=list, description="List of concepts to cover")


class LearningPlanResponse(BaseModel):
    """Final learning plan response structure matching client interface."""
    plan_id: str = Field(..., alias="planId", description="Unique identifier for the plan")
    title: str = Field(..., description="Title of the learning plan")
    description: str = Field(..., description="Description of what will be learned")
    created_at: datetime = Field(default_factory=datetime.now, alias="createdAt", description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, alias="updatedAt", description="Last update timestamp")
    subjects: List[Subject] = Field(..., description="List of subjects in the plan")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "planId": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Full Stack Web Development",
                "description": "Learn modern web development from basics to advanced",
                "createdAt": "2025-01-07T00:00:00Z",
                "updatedAt": "2025-01-07T00:00:00Z",
                "subjects": [
                    {
                        "name": "HTML & CSS",
                        "depth": "beginner",
                        "duration": 120,
                        "concepts": [
                            {"name": "HTML Structure"},
                            {"name": "CSS Styling"}
                        ]
                    }
                ]
            }
        }


class LearningPlanMessage(BaseModel):
    """Individual message in a learning plan session."""
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    timestamp: float = Field(..., description="Unix timestamp of message")


class LearningPlanSession(BaseModel):
    """Learning plan session data."""
    user_id: str = Field(..., alias="userId", description="User identifier")
    plan_id: str = Field(..., alias="planId", description="Plan identifier")
    messages: List[LearningPlanMessage] = Field(default_factory=list, description="Conversation messages")
    message_count: int = Field(default=0, alias="messageCount", description="Number of messages in session")
    created_at: Optional[float] = Field(None, alias="createdAt", description="Session creation timestamp")
    last_updated: Optional[float] = Field(None, alias="lastUpdated", description="Last update timestamp")

    class Config:
        populate_by_name = True


class LearningPlanQueryRequest(BaseModel):
    """Request body for learning plan query."""
    query: str = Field(..., min_length=1, description="User's query or response")
    plan_id: Optional[str] = Field(None, alias="planId", description="Existing plan ID (optional, will create new if not provided)")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "query": "I want to learn web development",
                "planId": None
            }
        }


class SessionInfoResponse(BaseModel):
    """Response for session information."""
    user_id: str = Field(..., alias="userId", description="User identifier")
    plan_id: str = Field(..., alias="planId", description="Plan identifier")
    message_count: int = Field(..., alias="messageCount", description="Number of messages")
    messages: List[LearningPlanMessage] = Field(..., description="Session messages")
    metadata: Optional[dict] = Field(None, description="Session metadata")

    class Config:
        populate_by_name = True


class SessionClearResponse(BaseModel):
    """Response for session clear operation."""
    user_id: str = Field(..., alias="userId", description="User identifier")
    plan_id: str = Field(..., alias="planId", description="Plan identifier")
    cleared: bool = Field(..., description="Whether session was cleared")
    message: str = Field(..., description="Status message")

    class Config:
        populate_by_name = True


# === Semantic Memory Schemas ===

class PriorKnowledge(BaseModel):
    """User's prior knowledge about the subject."""
    level: str = Field(..., description="beginner|some_knowledge|intermediate|advanced")
    specific_topics: List[str] = Field(default_factory=list, description="Specific topics they know")
    experience_summary: str = Field(default="", description="Summary of their background")


class LearningMotivation(BaseModel):
    """Why the user wants to learn."""
    primary_goal: str = Field(..., description="Main reason for learning")
    specific_objectives: List[str] = Field(default_factory=list, description="Specific things they want to achieve")
    use_case: str = Field(default="", description="What they want to build or accomplish")


class LearningPreferences(BaseModel):
    """User's learning preferences and constraints."""
    depth_preference: str = Field(..., description="beginner|intermediate|advanced")
    depth_level: int = Field(default=5, description="1-10 scale for content depth")
    time_commitment: str = Field(default="", description="Available time per week or timeline")
    learning_style: str = Field(default="balanced", description="hands-on|theoretical|balanced")


class LearningContext(BaseModel):
    """Additional context about the learner."""
    professional_context: str = Field(default="", description="Work or career related information")
    personal_interests: List[str] = Field(default_factory=list, description="Related interests")
    constraints: List[str] = Field(default_factory=list, description="Time, resource, or other constraints")


class SemanticMemoryData(BaseModel):
    """Complete semantic memory structure."""
    prior_knowledge: PriorKnowledge
    learning_motivation: LearningMotivation
    learning_preferences: LearningPreferences
    context: LearningContext


class CourseSemanticMemoryCreate(BaseModel):
    """Request to create semantic memory."""
    user_id: str = Field(..., alias="userId")
    course_id: str = Field(..., alias="courseId")
    memory_data: SemanticMemoryData = Field(..., alias="memoryData")
    conversation_summary: Optional[str] = Field(None, alias="conversationSummary")

    class Config:
        populate_by_name = True


class CourseSemanticMemoryResponse(BaseModel):
    """Response with semantic memory data."""
    user_id: str = Field(..., alias="userId")
    course_id: str = Field(..., alias="courseId")
    memory_data: SemanticMemoryData = Field(..., alias="memoryData")
    knowledge_level: Optional[str] = Field(None, alias="knowledgeLevel")
    depth_preference: Optional[str] = Field(None, alias="depthPreference")
    depth_level: Optional[int] = Field(None, alias="depthLevel")
    conversation_summary: Optional[str] = Field(None, alias="conversationSummary")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    class Config:
        populate_by_name = True


class LearningPlanCreate(BaseModel):
    """Request to create/save a learning plan."""
    user_id: str = Field(..., alias="userId")
    course_id: str = Field(..., alias="courseId")
    title: str
    description: str
    plan_data: dict = Field(..., alias="planData", description="Complete plan structure as dict")
    status: str = Field(default="draft", description="draft|active|completed|archived")

    class Config:
        populate_by_name = True


class LearningPlanDBResponse(BaseModel):
    """Response with saved learning plan."""
    user_id: str = Field(..., alias="userId")
    course_id: str = Field(..., alias="courseId")
    title: str
    description: Optional[str]
    plan_data: dict = Field(..., alias="planData")
    status: str
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    class Config:
        populate_by_name = True
