from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from career_navigator.infrastructure.database.session import get_db
from career_navigator.infrastructure.repositories.profile_repository import SQLAlchemyProfileRepository
from career_navigator.domain.models.profile import UserProfile as DomainProfile
from career_navigator.api.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse

router = APIRouter(prefix="/profiles", tags=["Profiles"])


def get_profile_repository(db: Session = Depends(get_db)) -> SQLAlchemyProfileRepository:
    """Dependency to get profile repository."""
    return SQLAlchemyProfileRepository(db)


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    profile_data: ProfileCreate,
    repository: SQLAlchemyProfileRepository = Depends(get_profile_repository),
):
    """Create a new user profile."""
    domain_profile = DomainProfile(**profile_data.model_dump())
    created_profile = repository.create(domain_profile)
    return ProfileResponse.model_validate(created_profile)


@router.get("", response_model=List[ProfileResponse])
def get_all_profiles(
    repository: SQLAlchemyProfileRepository = Depends(get_profile_repository),
):
    """Get all user profiles."""
    profiles = repository.get_all()
    return [ProfileResponse.model_validate(p) for p in profiles]


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(
    profile_id: int,
    repository: SQLAlchemyProfileRepository = Depends(get_profile_repository),
):
    """Get a profile by ID."""
    profile = repository.get_by_id(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with id {profile_id} not found",
        )
    return ProfileResponse.model_validate(profile)


@router.get("/user/{user_id}", response_model=ProfileResponse)
def get_profile_by_user_id(
    user_id: int,
    repository: SQLAlchemyProfileRepository = Depends(get_profile_repository),
    db: Session = Depends(get_db),
):
    """Get a profile by user ID."""
    profile = repository.get_by_user_id(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile for user {user_id} not found",
        )
    
    # Get user information to include in response
    from career_navigator.infrastructure.database.models import User
    user = db.query(User).filter(User.id == user_id).first()
    
    # Convert profile to dict and add user info
    profile_dict = ProfileResponse.model_validate(profile).model_dump()
    if user:
        # Use username as name (it contains the actual name from CV, with spaces preserved)
        # Replace underscores back to spaces for display (since we stored it with underscores)
        name = user.username.replace("_", " ") if user.username else None
        profile_dict["name"] = name
        profile_dict["email"] = user.email
    
    return ProfileResponse(**profile_dict)


@router.put("/{profile_id}", response_model=ProfileResponse)
def update_profile(
    profile_id: int,
    profile_data: ProfileUpdate,
    repository: SQLAlchemyProfileRepository = Depends(get_profile_repository),
):
    """Update a profile."""
    existing_profile = repository.get_by_id(profile_id)
    if not existing_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with id {profile_id} not found",
        )
    
    # Update only provided fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_profile, field, value)
    
    updated_profile = repository.update(existing_profile)
    return ProfileResponse.model_validate(updated_profile)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    profile_id: int,
    repository: SQLAlchemyProfileRepository = Depends(get_profile_repository),
):
    """Delete a profile."""
    success = repository.delete(profile_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with id {profile_id} not found",
        )

