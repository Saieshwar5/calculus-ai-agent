"""
Pydantic schemas for learning progress and next-topic API.

Handles requests and responses for progressive concept-based learning.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List
from datetime import datetime


class NextTopicRequest(BaseModel):
    """
    Request schema for getting the next topic in a concept.

    Client provides course_id, subject_name, and concept_name.
    Server determines whether to generate next topic or signal concept completion.
    """
    model_config = ConfigDict(populate_by_name=True)

    course_id: str = Field(
        ...,
        alias="courseId",
        description="The learning plan/course identifier",
        min_length=1
    )
    subject_name: str = Field(
        ...,
        alias="subjectName",
        description="Subject name from the learning plan",
        min_length=1
    )
    concept_name: str = Field(
        ...,
        alias="conceptName",
        description="Concept name from the learning plan",
        min_length=1
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "courseId": "calculus-101",
                "subjectName": "Differential Calculus",
                "conceptName": "Limits"
            }
        }
    )


class ConceptProgressInfo(BaseModel):
    """Progress information for a concept."""
    concept_name: str = Field(..., alias="conceptName")
    current_depth: int = Field(..., alias="currentDepth")
    target_depth: int = Field(..., alias="targetDepth")
    topics_completed: int = Field(..., alias="topicsCompleted")
    progress_percent: int = Field(..., alias="progressPercent")
    last_topic_name: Optional[str] = Field(None, alias="lastTopicName")
    completed: bool = Field(default=False)

    model_config = ConfigDict(populate_by_name=True)


class NextConceptSuggestion(BaseModel):
    """Suggestion for the next concept to learn."""
    concept_name: str = Field(..., alias="conceptName")
    target_depth: int = Field(..., alias="targetDepth")
    description: Optional[str] = None
    estimated_topics: Optional[str] = Field(None, alias="estimatedTopics")

    model_config = ConfigDict(populate_by_name=True)


class ConceptCompleteResponse(BaseModel):
    """
    Response when a concept is completed.

    Returns completion message, progress stats, learning summary,
    and suggestion for next concept.
    """
    status: str = Field(default="concept_complete")
    success: bool = Field(default=True)
    message: str = Field(..., description="Congratulations message")

    progress: ConceptProgressInfo = Field(..., description="Final progress for completed concept")

    learning_summary: Optional[str] = Field(
        None,
        alias="learningSummary",
        description="Summary of what was learned in this concept"
    )

    next_concept: Optional[NextConceptSuggestion] = Field(
        None,
        alias="nextConcept",
        description="Suggested next concept"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "status": "concept_complete",
                "success": True,
                "message": "🎉 Congratulations! You've mastered Limits!",
                "progress": {
                    "conceptName": "Limits",
                    "currentDepth": 8,
                    "targetDepth": 7,
                    "topicsCompleted": 5,
                    "progressPercent": 114,
                    "completed": True
                },
                "learningSummary": "Completed 5 topics in Limits...",
                "nextConcept": {
                    "conceptName": "Continuity",
                    "targetDepth": 6,
                    "description": "Build on limits to understand continuous functions"
                }
            }
        }
    )


class TopicCompletionRequest(BaseModel):
    """
    Enhanced request schema for marking a topic as completed.

    Now includes concept_name and depth_increment.
    """
    model_config = ConfigDict(populate_by_name=True)

    course_id: str = Field(
        ...,
        alias="courseId",
        description="The learning plan/course identifier",
        min_length=1
    )
    subject_name: str = Field(
        ...,
        alias="subjectName",
        description="Subject name from the learning plan",
        min_length=1
    )
    concept_name: str = Field(
        ...,
        alias="conceptName",
        description="Concept name from the learning plan",
        min_length=1
    )
    topic_name: str = Field(
        ...,
        alias="topicName",
        description="Name of the topic that was completed",
        min_length=1
    )
    depth_increment: int = Field(
        ...,
        alias="depthIncrement",
        description="Depth added by this topic (1-3)",
        ge=1,
        le=3
    )
    content_snapshot: Optional[str] = Field(
        None,
        alias="contentSnapshot",
        description="Optional brief summary of content delivered"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "courseId": "calculus-101",
                "subjectName": "Differential Calculus",
                "conceptName": "Limits",
                "topicName": "Introduction to Limits",
                "depthIncrement": 1,
                "contentSnapshot": "Covered basic limit definition..."
            }
        }
    )


class TopicCompletionResponse(BaseModel):
    """
    Enhanced response after marking a topic as completed.

    Now includes concept progress information.
    """
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Human-readable message")

    topic_name: str = Field(
        ...,
        alias="topicName",
        description="Name of the completed topic"
    )

    completed_at: datetime = Field(
        ...,
        alias="completedAt",
        description="When the topic was marked complete"
    )

    concept_progress: ConceptProgressInfo = Field(
        ...,
        alias="conceptProgress",
        description="Updated concept progress"
    )

    next_action: str = Field(
        ...,
        alias="nextAction",
        description="What user should do next: 'continue_learning' or 'concept_complete'"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Topic 'Introduction to Limits' marked as complete",
                "topicName": "Introduction to Limits",
                "completedAt": "2025-01-08T10:35:00Z",
                "conceptProgress": {
                    "conceptName": "Limits",
                    "currentDepth": 1,
                    "targetDepth": 7,
                    "topicsCompleted": 1,
                    "progressPercent": 14,
                    "completed": False
                },
                "nextAction": "continue_learning"
            }
        }
    )
