from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ProfileCreate(BaseModel):
    user_id: int
    career_goals: Optional[str] = None
    short_term_goals: Optional[str] = None
    long_term_goals: Optional[str] = None
    cv_content: Optional[str] = None
    linkedin_profile_url: Optional[str] = None
    linkedin_profile_data: Optional[Dict[str, Any]] = None
    life_profile: Optional[str] = None
    age: Optional[int] = None
    birth_country: Optional[str] = None
    birth_city: Optional[str] = None
    current_location: Optional[str] = None
    desired_job_locations: Optional[List[str]] = None
    languages: Optional[List[Dict[str, str]]] = None
    culture: Optional[str] = None


class ProfileUpdate(BaseModel):
    career_goals: Optional[str] = None
    short_term_goals: Optional[str] = None
    long_term_goals: Optional[str] = None
    cv_content: Optional[str] = None
    linkedin_profile_url: Optional[str] = None
    linkedin_profile_data: Optional[Dict[str, Any]] = None
    life_profile: Optional[str] = None
    age: Optional[int] = None
    birth_country: Optional[str] = None
    birth_city: Optional[str] = None
    current_location: Optional[str] = None
    desired_job_locations: Optional[List[str]] = None
    languages: Optional[List[Dict[str, str]]] = None
    culture: Optional[str] = None


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    career_goals: Optional[str]
    short_term_goals: Optional[str]
    long_term_goals: Optional[str]
    cv_content: Optional[str]
    linkedin_profile_url: Optional[str]
    linkedin_profile_data: Optional[Dict[str, Any]]
    life_profile: Optional[str]
    age: Optional[int]
    birth_country: Optional[str]
    birth_city: Optional[str]
    current_location: Optional[str]
    desired_job_locations: Optional[List[str]]
    languages: Optional[List[Dict[str, str]]]
    culture: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

