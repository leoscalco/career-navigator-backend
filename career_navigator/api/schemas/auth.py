"""
Authentication schemas for request/response models.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str
    username: Optional[str] = None


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Access token response."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str


class OAuthProvider(BaseModel):
    """OAuth provider information."""
    provider: str  # 'google', 'github', 'linkedin', etc.
    redirect_uri: str


class OAuthCallback(BaseModel):
    """OAuth callback request."""
    code: str
    state: Optional[str] = None

