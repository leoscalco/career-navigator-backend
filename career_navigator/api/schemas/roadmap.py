from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class RoadmapTaskResponse(BaseModel):
    id: int
    user_id: int
    product_id: Optional[int] = None
    plan_type: str
    period: str
    task_type: str
    task_content: str
    task_index: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MarkTaskRequest(BaseModel):
    plan_type: str  # '1y', '3y', '5y'
    period: str  # 'Q1', 'Q2', etc.
    task_type: str  # 'projects', 'networking', etc.
    task_index: int  # Index in the array


class MarkTaskResponse(BaseModel):
    success: bool
    task: RoadmapTaskResponse
    message: str

