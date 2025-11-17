from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel


class Course(BaseModel):
    id: Optional[int] = None
    user_id: int
    course_name: str
    institution: Optional[str] = None
    provider: Optional[str] = None
    description: Optional[str] = None
    completion_date: Optional[date] = None
    certificate_url: Optional[str] = None
    skills_learned: Optional[List[str]] = None
    duration_hours: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

