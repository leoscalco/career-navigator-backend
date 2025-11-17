from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class AcademicRecord(BaseModel):
    id: Optional[int] = None
    user_id: int
    institution_name: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gpa: Optional[float] = None
    honors: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

