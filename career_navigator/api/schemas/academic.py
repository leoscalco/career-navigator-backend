from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class AcademicRecordCreate(BaseModel):
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


class AcademicRecordUpdate(BaseModel):
    institution_name: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gpa: Optional[float] = None
    honors: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None


class AcademicRecordResponse(BaseModel):
    id: int
    user_id: int
    institution_name: str
    degree: Optional[str]
    field_of_study: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    gpa: Optional[float]
    honors: Optional[str]
    description: Optional[str]
    location: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

