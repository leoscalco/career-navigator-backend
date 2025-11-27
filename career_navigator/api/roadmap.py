from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from career_navigator.infrastructure.database.session import get_db
from career_navigator.infrastructure.repositories.roadmap_task_repository import SQLAlchemyRoadmapTaskRepository
from career_navigator.infrastructure.repositories.product_repository import SQLAlchemyProductRepository
from career_navigator.infrastructure.database.models import ProductType
from career_navigator.api.schemas.roadmap import RoadmapTaskResponse, MarkTaskRequest, MarkTaskResponse
from career_navigator.api.auth import get_current_user
from career_navigator.domain.models.user import User as DomainUser
from datetime import datetime

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


def get_roadmap_task_repository(db: Session = Depends(get_db)) -> SQLAlchemyRoadmapTaskRepository:
    return SQLAlchemyRoadmapTaskRepository(db)


@router.get("/tasks/{user_id}", response_model=List[RoadmapTaskResponse])
def get_user_roadmap_tasks(
    user_id: int,
    plan_type: str = None,
    current_user: DomainUser = Depends(get_current_user),
    repository: SQLAlchemyRoadmapTaskRepository = Depends(get_roadmap_task_repository),
):
    """
    Get all roadmap tasks for a user.
    
    Optionally filter by plan_type ('1y', '3y', '5y').
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own roadmap tasks",
        )
    
    if plan_type:
        tasks = repository.get_by_user_and_plan(user_id, plan_type)
    else:
        tasks = repository.get_by_user_id(user_id)
    
    return [RoadmapTaskResponse.model_validate(task) for task in tasks]


@router.post("/tasks/{user_id}/complete", response_model=MarkTaskResponse)
def mark_task_complete(
    user_id: int,
    request: MarkTaskRequest,
    current_user: DomainUser = Depends(get_current_user),
    repository: SQLAlchemyRoadmapTaskRepository = Depends(get_roadmap_task_repository),
    db: Session = Depends(get_db),
):
    """
    Mark a roadmap task as completed.
    
    The task will be created if it doesn't exist yet.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own roadmap tasks",
        )
    
    try:
        # Get the product to extract task content
        product_repo = SQLAlchemyProductRepository(db)
        plan_type_map = {
            '1y': ProductType.CAREER_PLAN_1Y,
            '3y': ProductType.CAREER_PLAN_3Y,
            '5y': ProductType.CAREER_PLAN_5Y,
        }
        product_type = plan_type_map.get(request.plan_type)
        
        if product_type:
            products = product_repo.get_by_user_and_type(user_id, product_type)
            if products:
                product = products[0]  # Get the latest version
                # Extract task content from product
                content = product.content or {}
                task_content = ""
                
                if request.plan_type == '1y' and 'quarters' in content:
                    quarter_data = content.get('quarters', {}).get(request.period, {})
                    task_array = quarter_data.get(request.task_type, [])
                    if isinstance(task_array, list) and request.task_index < len(task_array):
                        task_content = task_array[request.task_index]
                
                elif request.plan_type == '3y' and 'years' in content:
                    year_data = content.get('years', {}).get(request.period, {})
                    task_array = year_data.get(request.task_type, [])
                    if isinstance(task_array, list) and request.task_index < len(task_array):
                        task_content = task_array[request.task_index]
                
                elif request.plan_type == '5y' and 'career_phases' in content:
                    phases = content.get('career_phases', [])
                    phase_data = next((p for p in phases if p.get('phase') == request.period), {})
                    task_array = phase_data.get(request.task_type, [])
                    if isinstance(task_array, list) and request.task_index < len(task_array):
                        task_content = task_array[request.task_index]
                
                # Update task content if found
                existing_task = repository.find_task(
                    user_id, request.plan_type, request.period, request.task_type, request.task_index
                )
                if existing_task and task_content:
                    existing_task.task_content = task_content
                    repository.update(existing_task)
        
        task = repository.mark_completed(
            user_id, request.plan_type, request.period, request.task_type, request.task_index
        )
        
        return MarkTaskResponse(
            success=True,
            task=RoadmapTaskResponse.model_validate(task),
            message="Task marked as completed",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark task as complete: {str(e)}",
        )


@router.post("/tasks/{user_id}/incomplete", response_model=MarkTaskResponse)
def mark_task_incomplete(
    user_id: int,
    request: MarkTaskRequest,
    current_user: DomainUser = Depends(get_current_user),
    repository: SQLAlchemyRoadmapTaskRepository = Depends(get_roadmap_task_repository),
):
    """
    Mark a roadmap task as incomplete.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own roadmap tasks",
        )
    
    try:
        task = repository.mark_incomplete(
            user_id, request.plan_type, request.period, request.task_type, request.task_index
        )
        
        return MarkTaskResponse(
            success=True,
            task=RoadmapTaskResponse.model_validate(task),
            message="Task marked as incomplete",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark task as incomplete: {str(e)}",
        )

