"""
Authentication schemas for request and response validation.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


class SignupRequest(BaseModel):
    """Schema for user signup request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, max_length=100, description="User password (min 6 characters)")


class SigninRequest(BaseModel):
    """Schema for user signin request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserData(BaseModel):
    """Schema for user data in response"""
    uuid: str = Field(..., alias="uuid", description="User unique identifier")
    email: str = Field(..., description="User email address")
    userID: Optional[str] = Field(None, alias="userID", description="Alias for uuid for client compatibility")
    
    model_config = ConfigDict(populate_by_name=True)


class AuthResponse(BaseModel):
    """Schema for authentication response"""
    access_token: str = Field(..., description="JWT access token")
    expires_in: Optional[int] = Field(3600, description="Token expiration time in seconds")
    token_type: str = Field("bearer", description="Token type")
    data: UserData = Field(..., description="User data")
    message: Optional[str] = Field(None, description="Optional message")


class MeResponse(BaseModel):
    """Schema for /me endpoint response"""
    data: UserData = Field(..., description="User data")
    message: Optional[str] = Field(None, description="Optional message")


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: Optional[str] = Field(None, description="Refresh token (optional, can use cookie)")


class LogoutResponse(BaseModel):
    """Schema for logout response"""
    message: str = Field(..., description="Logout message")

