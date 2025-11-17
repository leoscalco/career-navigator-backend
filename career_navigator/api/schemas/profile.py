from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from career_navigator.domain.models.career_goal_type import CareerGoalType


class ProfileCreate(BaseModel):
    user_id: int
    career_goals: Optional[str] = None
    career_goal_type: CareerGoalType = CareerGoalType.CONTINUE_PATH  # Default to continue path
    short_term_goals: Optional[str] = None
    long_term_goals: Optional[str] = None
    job_search_locations: Optional[List[str]] = None  # Where user is searching for jobs
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
    career_goal_type: Optional[CareerGoalType] = None
    short_term_goals: Optional[str] = None
    long_term_goals: Optional[str] = None
    job_search_locations: Optional[List[str]] = None
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
    is_draft: bool
    is_validated: bool
    career_goals: Optional[str]
    career_goal_type: CareerGoalType
    short_term_goals: Optional[str]
    long_term_goals: Optional[str]
    job_search_locations: Optional[List[str]]
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
    hobbies: Optional[List[str]]
    additional_info: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

