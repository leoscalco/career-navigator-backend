from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from career_navigator.domain.models.user_group import UserGroup


class User(BaseModel):
    id: Optional[int] = None
    email: str
    username: Optional[str] = None
    user_group: UserGroup
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

