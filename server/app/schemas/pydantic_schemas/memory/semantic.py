"""
Pydantic schemas for semantic memory operations.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional
from datetime import datetime


class SemanticMemoryCreate(BaseModel):
    """Schema for creating semantic memory."""
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",  # Allow extra fields for flexibility
    )
    
    user_id: str = Field(..., description="User identifier")
    memory_data: Dict[str, Any] = Field(default_factory=dict, description="Initial memory data (flexible JSON structure)")


class SemanticMemoryUpdate(BaseModel):
    """Schema for updating semantic memory."""
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )
    
    memory_data: Dict[str, Any] = Field(..., description="Memory data to update (will merge with existing data)")


class SemanticMemoryResponse(BaseModel):
    """Schema for semantic memory response."""
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )
    
    id: int
    user_id: str
    memory_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class SemanticMemoryPartialUpdate(BaseModel):
    """Schema for partial update (merge specific keys)."""
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )
    
    updates: Dict[str, Any] = Field(..., description="Key-value pairs to update in memory_data")

