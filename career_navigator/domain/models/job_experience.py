from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class JobExperience(BaseModel):
    id: Optional[int] = None
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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

