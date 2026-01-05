from pydantic import BaseModel, Field, ConfigDict, AliasChoices
from typing import Optional
from datetime import datetime


class ProfileCreate(BaseModel):
    """Schema for creating a new profile - accepts camelCase from frontend"""
    model_config = ConfigDict(
        populate_by_name=True,  # Allow both alias and field name
    )
    
    username: str = Field(..., min_length=1, max_length=255, description="username")
    
    # Accept both camelCase and snake_case from frontend
    date_of_birth: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Date of birth",
        validation_alias=AliasChoices("dateOfBirth", "date_of_birth")
    )
    
    country: Optional[str] = Field(default=None, max_length=100, description="Country")
    education: Optional[str] = Field(default=None, max_length=255, description="Education level")
    
    mother_tongue: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Mother tongue",
        validation_alias=AliasChoices("motherTongue", "mother_tongue")
    )
    
    gender: Optional[str] = Field(default=None, max_length=50, description="Gender")
    
    learning_pace: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Learning pace",
        validation_alias=AliasChoices("learningPace", "learning_pace")
    )


class ProfileUpdate(BaseModel):
    """Schema for updating an existing profile - accepts camelCase from frontend"""
    model_config = ConfigDict(populate_by_name=True)
    
    username: Optional[str] = Field(default=None, min_length=1, max_length=255)
    
    date_of_birth: Optional[str] = Field(
        default=None,
        max_length=50,
        validation_alias=AliasChoices("dateOfBirth", "date_of_birth")
    )
    
    country: Optional[str] = Field(default=None, max_length=100)
    education: Optional[str] = Field(default=None, max_length=255)
    
    mother_tongue: Optional[str] = Field(
        default=None,
        max_length=100,
        validation_alias=AliasChoices("motherTongue", "mother_tongue")
    )
    
    gender: Optional[str] = Field(default=None, max_length=50)
    
    learning_pace: Optional[str] = Field(
        default=None,
        max_length=50,
        validation_alias=AliasChoices("learningPace", "learning_pace")
    )


class ProfileResponse(BaseModel):
    """Schema for profile response"""
    model_config = ConfigDict(
        from_attributes=True,  # For SQLAlchemy model conversion
        populate_by_name=True,  # Allow both alias and field name
    )
    
    id: int
    user_id: str
    username: str
    date_of_birth: Optional[str] = Field(None, alias="dateOfBirth")
    country: Optional[str]
    education: Optional[str]
    mother_tongue: Optional[str] = Field(None, alias="motherTongue")
    gender: Optional[str]
    learning_pace: Optional[str] = Field(None, alias="learningPace")
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProfileListResponse(BaseModel):
    """Schema for list of profiles"""
    profiles: list[ProfileResponse]
    total: int
    page: int
    page_size: int