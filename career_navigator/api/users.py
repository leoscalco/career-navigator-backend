from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from career_navigator.infrastructure.database.session import get_db
from career_navigator.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from career_navigator.domain.models.user import User as DomainUser
from career_navigator.api.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_repository(db: Session = Depends(get_db)) -> SQLAlchemyUserRepository:
    """Dependency to get user repository."""
    return SQLAlchemyUserRepository(db)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    repository: SQLAlchemyUserRepository = Depends(get_user_repository),
):
    """Create a new user."""
    domain_user = DomainUser(
        email=user_data.email,
        username=user_data.username,
        user_group=user_data.user_group,
    )
    created_user = repository.create(domain_user)
    return UserResponse.model_validate(created_user)


@router.get("", response_model=List[UserResponse])
def get_all_users(
    repository: SQLAlchemyUserRepository = Depends(get_user_repository),
):
    """Get all users."""
    users = repository.get_all()
    return [UserResponse.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    repository: SQLAlchemyUserRepository = Depends(get_user_repository),
):
    """Get a user by ID."""
    user = repository.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    repository: SQLAlchemyUserRepository = Depends(get_user_repository),
):
    """Update a user."""
    existing_user = repository.get_by_id(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )
    
    # Update only provided fields
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_user, field, value)
    
    updated_user = repository.update(existing_user)
    return UserResponse.model_validate(updated_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    repository: SQLAlchemyUserRepository = Depends(get_user_repository),
):
    """Delete a user."""
    success = repository.delete(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )

