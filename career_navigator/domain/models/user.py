from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from career_navigator.domain.models.user_group import UserGroup


class User(BaseModel):
    id: Optional[int] = None
    email: str
    username: Optional[str] = None
    user_group: UserGroup
    password_hash: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    oauth_provider: Optional[str] = None
    oauth_provider_id: Optional[str] = None
    oauth_access_token: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

