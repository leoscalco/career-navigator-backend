from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel


class CourseCreate(BaseModel):
    user_id: int
    course_name: str
    institution: Optional[str] = None
    provider: Optional[str] = None
    description: Optional[str] = None
    completion_date: Optional[date] = None
    certificate_url: Optional[str] = None
    skills_learned: Optional[List[str]] = None
    duration_hours: Optional[float] = None


class CourseUpdate(BaseModel):
    course_name: Optional[str] = None
    institution: Optional[str] = None
    provider: Optional[str] = None
    description: Optional[str] = None
    completion_date: Optional[date] = None
    certificate_url: Optional[str] = None
    skills_learned: Optional[List[str]] = None
    duration_hours: Optional[float] = None


class CourseResponse(BaseModel):
    id: int
    user_id: int
    course_name: str
    institution: Optional[str]
    provider: Optional[str]
    description: Optional[str]
    completion_date: Optional[date]
    certificate_url: Optional[str]
    skills_learned: Optional[List[str]]
    duration_hours: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

