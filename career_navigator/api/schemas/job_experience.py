from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel


class JobExperienceCreate(BaseModel):
    user_id: int
    company_name: str
    position: str
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    location: Optional[str] = None
    achievements: Optional[List[str]] = None
    skills_used: Optional[List[str]] = None


class JobExperienceUpdate(BaseModel):
    company_name: Optional[str] = None
    position: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    location: Optional[str] = None
    achievements: Optional[List[str]] = None
    skills_used: Optional[List[str]] = None


class JobExperienceResponse(BaseModel):
    id: int
    user_id: int
    company_name: str
    position: str
    description: Optional[str]
    start_date: date
    end_date: Optional[date]
    is_current: bool
    location: Optional[str]
    achievements: Optional[List[str]]
    skills_used: Optional[List[str]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

