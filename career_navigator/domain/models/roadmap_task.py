from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class RoadmapTask(BaseModel):
    id: Optional[int] = None
    user_id: int
    product_id: Optional[int] = None
    plan_type: str  # '1y', '3y', '5y'
    period: str  # 'Q1', 'Q2', etc. or 'Year 1', etc. or 'Foundation', etc.
    task_type: str  # 'projects', 'networking', 'strategies', 'tips', 'milestones', 'goals', 'courses'
    task_content: str
    task_index: int
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

