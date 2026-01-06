"""
Pydantic schemas for episodic memory operations.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, List
from datetime import datetime


class EpisodicMemoryCreate(BaseModel):
    """Schema for creating episodic memory (embedding generated automatically)."""
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )
    
    user_id: str = Field(..., description="User identifier")
    event_description: str = Field(..., description="Description of the event")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Conversation context, related topics")
    emotion: Optional[str] = Field(None, description="Emotion expressed (e.g., 'frustrated', 'confident')")
    importance: Optional[int] = Field(None, ge=1, le=10, description="Importance score (1-10)")
    event_time: datetime = Field(..., description="When the event occurred")
    related_query_ids: Optional[List[int]] = Field(default_factory=list, description="IDs of related queries")
    additional_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional flexible data")


class EpisodicMemoryResponse(BaseModel):
    """Schema for episodic memory response (excludes embedding vector)."""
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )
    
    id: int
    user_id: str
    event_description: str
    context: Optional[Dict[str, Any]]
    emotion: Optional[str]
    importance: Optional[int]
    event_time: datetime
    related_query_ids: Optional[List[int]]
    additional_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class EpisodicMemoryFilters(BaseModel):
    """Schema for filtering episodic memories."""
    model_config = ConfigDict(
        populate_by_name=True,
    )
    
    date_from: Optional[datetime] = Field(None, description="Filter episodes from this date")
    date_to: Optional[datetime] = Field(None, description="Filter episodes until this date")
    emotion: Optional[str] = Field(None, description="Filter by emotion")
    min_importance: Optional[int] = Field(None, ge=1, le=10, description="Minimum importance score")
    max_importance: Optional[int] = Field(None, ge=1, le=10, description="Maximum importance score")


class EpisodicMemorySearchRequest(BaseModel):
    """Schema for hybrid search requests."""
    model_config = ConfigDict(
        populate_by_name=True,
    )
    
    query_text: str = Field(..., description="Text to search for semantically similar episodes")
    filters: Optional[EpisodicMemoryFilters] = Field(None, description="Additional filters (date, emotion, importance)")
    similarity_threshold: Optional[float] = Field(0.3, ge=0.0, le=1.0, description="Minimum similarity threshold (0.0-1.0)")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Maximum number of results")


class EpisodicMemoryExtractionRequest(BaseModel):
    """Schema for batch processing requests."""
    model_config = ConfigDict(
        populate_by_name=True,
    )
    
    lookback_days: Optional[int] = Field(7, ge=1, le=30, description="How many days back to analyze conversations")
    min_importance: Optional[int] = Field(3, ge=1, le=10, description="Minimum importance to save episodes")

