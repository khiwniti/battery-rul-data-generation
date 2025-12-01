"""
Authentication Schemas
Pydantic models for authentication requests/responses
"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class LoginRequest(BaseModel):
    """Login request"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class LoginResponse(BaseModel):
    """Login response with tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token expiration in seconds")
    user: "UserInfo"


class UserInfo(BaseModel):
    """User information returned in login response"""
    user_id: str
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)


class CreateUserRequest(BaseModel):
    """Create new user request (admin only)"""
    user_id: str = Field(..., min_length=3, max_length=50, description="Unique user ID")
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., description="User role: admin, engineer, viewer")


class UpdateUserRequest(BaseModel):
    """Update user request (admin only)"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = Field(None, description="User role: admin, engineer, viewer")
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response"""
    user_id: str
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """List of users"""
    users: list[UserResponse]
    total: int


# Rebuild models to resolve forward references
LoginResponse.model_rebuild()
