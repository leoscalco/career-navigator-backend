from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from career_navigator.domain.models.career_goal_type import CareerGoalType


class UserProfile(BaseModel):
    id: Optional[int] = None
    user_id: int
    is_draft: bool = True
    is_validated: bool = False
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
    hobbies: Optional[List[str]] = None
    additional_info: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

