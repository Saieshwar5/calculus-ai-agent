"""
Pydantic schemas for content generation API.

Handles requests and responses for generating educational content from learning plans.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from datetime import datetime


class ContentGenerationRequest(BaseModel):
    """
    Request schema for content generation.

    Client provides course_id, subject_name, and optionally concept_name
    to generate personalized content.

    If concept_name is provided, content is generated for that specific concept.
    Otherwise, AI determines the next logical topic to teach.
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
    concept_name: Optional[str] = Field(
        None,
        alias="conceptName",
        description="Specific concept name to generate content for (optional)",
        min_length=1
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "courseId": "thermodynamics-2025",
                "subjectName": "Thermodynamics Fundamentals",
                "conceptName": "First Law of Thermodynamics"
            }
        }
    )


class TopicCompletionRequest(BaseModel):
    """
    Request schema for marking a topic as completed.

    Client sends this after user has finished studying a topic.
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
    topic_name: str = Field(
        ...,
        alias="topicName",
        description="Name of the topic that was completed",
        min_length=1
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
                "courseId": "thermodynamics-2025",
                "subjectName": "Thermodynamics Fundamentals",
                "topicName": "First Law of Thermodynamics",
                "contentSnapshot": "Covered energy conservation principles..."
            }
        }
    )


class CompletionStats(BaseModel):
    """Statistics about topic completion progress."""
    total_completed: int = Field(
        ...,
        alias="totalCompleted",
        description="Total number of topics completed"
    )
    subject_name: Optional[str] = Field(
        None,
        alias="subjectName",
        description="Subject name (if filtered by subject)"
    )
    subjects_breakdown: Optional[Dict[str, int]] = Field(
        None,
        alias="subjectsBreakdown",
        description="Per-subject completion counts"
    )

    model_config = ConfigDict(populate_by_name=True)


class TopicCompletionResponse(BaseModel):
    """
    Response schema after marking a topic as completed.

    Returns success status, message, and completion statistics.
    """
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Human-readable message")
    completion_stats: CompletionStats = Field(
        ...,
        alias="completionStats",
        description="Updated completion statistics"
    )
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

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Topic marked as complete",
                "completionStats": {
                    "totalCompleted": 1,
                    "subjectName": "Thermodynamics Fundamentals"
                },
                "topicName": "First Law of Thermodynamics",
                "completedAt": "2025-01-07T12:00:00Z"
            }
        }
    )


class AllTopicsCompletedResponse(BaseModel):
    """
    Response when all topics for a subject have been completed.

    Returns congratulations message and final statistics.
    """
    success: bool = Field(default=True, description="Always true for this response")
    message: str = Field(..., description="Congratulations message")
    all_completed: bool = Field(
        default=True,
        alias="allCompleted",
        description="Indicates all topics are complete"
    )
    completion_stats: CompletionStats = Field(
        ...,
        alias="completionStats",
        description="Final completion statistics"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Congratulations! You've completed all topics in Thermodynamics Fundamentals",
                "allCompleted": True,
                "completionStats": {
                    "totalCompleted": 10,
                    "subjectName": "Thermodynamics Fundamentals"
                }
            }
        }
    )
