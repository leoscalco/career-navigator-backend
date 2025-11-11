from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from career_navigator.domain.models.user_group import UserGroup


class UserCreate(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    user_group: UserGroup


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    user_group: Optional[UserGroup] = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: Optional[str]
    user_group: UserGroup
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

