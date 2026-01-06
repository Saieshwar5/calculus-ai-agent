"""
Pydantic schemas for short-term memory operations.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, List, Optional
from datetime import datetime


class Message(BaseModel):
    """Schema for a single message in short-term memory."""
    model_config = ConfigDict(
        populate_by_name=True,
    )
    
    role: Literal["user", "assistant"] = Field(..., description="Role of the message sender")
    content: str = Field(..., min_length=1, description="Message content")
    timestamp: float = Field(..., description="Unix timestamp of the message")


class MemoryResponse(BaseModel):
    """Schema for memory API responses."""
    model_config = ConfigDict(
        populate_by_name=True,
    )
    
    user_id: str = Field(..., description="User identifier")
    messages: List[Message] = Field(default_factory=list, description="List of recent messages")
    count: int = Field(..., description="Number of messages in memory")
    max_messages: int = Field(default=20, description="Maximum number of messages stored")


class MemoryClearResponse(BaseModel):
    """Schema for memory clear operation response."""
    model_config = ConfigDict(
        populate_by_name=True,
    )
    
    user_id: str = Field(..., description="User identifier")
    cleared: bool = Field(..., description="Whether memory was cleared successfully")
    message: str = Field(..., description="Response message")

