from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class QueryRequest(BaseModel):
    """Schema for query request - matches client JSON request"""
    model_config = ConfigDict(
        populate_by_name=True,
    )
    
    query: str = Field(..., min_length=1, description="The query text from the user")


class QueryResponse(BaseModel):
    """Schema for query response"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
    
    id: int
    user_id: str
    query_text: str
    response_text: Optional[str] = None
    used_for_episodic_memory: bool = False
    created_at: datetime
    updated_at: datetime


class QueryCreate(BaseModel):
    """Schema for creating a query in the database"""
    model_config = ConfigDict(
        populate_by_name=True,
    )
    
    user_id: str = Field(..., description="User identifier")
    query_text: str = Field(..., min_length=1, description="The query text from the user")
    response_text: Optional[str] = Field(default=None, description="The response text from the assistant")
    used_for_episodic_memory: bool = Field(default=False, description="Whether this query/response has been used for episodic memory")


class QueryUpdate(BaseModel):
    """Schema for updating a query (e.g., to add response text)"""
    model_config = ConfigDict(
        populate_by_name=True,
    )
    
    response_text: Optional[str] = Field(default=None, description="The response text from the assistant")
    used_for_episodic_memory: Optional[bool] = Field(default=None, description="Whether this query/response has been used for episodic memory")

