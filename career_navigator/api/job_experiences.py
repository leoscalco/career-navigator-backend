from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from career_navigator.infrastructure.database.session import get_db
from career_navigator.infrastructure.repositories.job_experience_repository import SQLAlchemyJobExperienceRepository
from career_navigator.domain.models.job_experience import JobExperience as DomainJobExperience
from career_navigator.api.schemas.job_experience import JobExperienceCreate, JobExperienceUpdate, JobExperienceResponse

router = APIRouter(prefix="/job-experiences", tags=["Job Experiences"])


def get_job_repository(db: Session = Depends(get_db)) -> SQLAlchemyJobExperienceRepository:
    """Dependency to get job experience repository."""
    return SQLAlchemyJobExperienceRepository(db)


@router.post("", response_model=JobExperienceResponse, status_code=status.HTTP_201_CREATED)
def create_job_experience(
    job_data: JobExperienceCreate,
    repository: SQLAlchemyJobExperienceRepository = Depends(get_job_repository),
):
    """Create a new job experience."""
    domain_job = DomainJobExperience(**job_data.model_dump())
    created_job = repository.create(domain_job)
    return JobExperienceResponse.model_validate(created_job)


@router.get("", response_model=List[JobExperienceResponse])
def get_all_job_experiences(
    repository: SQLAlchemyJobExperienceRepository = Depends(get_job_repository),
):
    """Get all job experiences."""
    jobs = repository.get_all()
    return [JobExperienceResponse.model_validate(j) for j in jobs]


@router.get("/{job_id}", response_model=JobExperienceResponse)
def get_job_experience(
    job_id: int,
    repository: SQLAlchemyJobExperienceRepository = Depends(get_job_repository),
):
    """Get a job experience by ID."""
    job = repository.get_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job experience with id {job_id} not found",
        )
    return JobExperienceResponse.model_validate(job)


@router.get("/user/{user_id}", response_model=List[JobExperienceResponse])
def get_job_experiences_by_user(
    user_id: int,
    repository: SQLAlchemyJobExperienceRepository = Depends(get_job_repository),
):
    """Get all job experiences for a user."""
    jobs = repository.get_by_user_id(user_id)
    return [JobExperienceResponse.model_validate(j) for j in jobs]


@router.put("/{job_id}", response_model=JobExperienceResponse)
def update_job_experience(
    job_id: int,
    job_data: JobExperienceUpdate,
    repository: SQLAlchemyJobExperienceRepository = Depends(get_job_repository),
):
    """Update a job experience."""
    existing_job = repository.get_by_id(job_id)
    if not existing_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job experience with id {job_id} not found",
        )
    
    # Update only provided fields
    update_data = job_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_job, field, value)
    
    updated_job = repository.update(existing_job)
    return JobExperienceResponse.model_validate(updated_job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_experience(
    job_id: int,
    repository: SQLAlchemyJobExperienceRepository = Depends(get_job_repository),
):
    """Delete a job experience."""
    success = repository.delete(job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job experience with id {job_id} not found",
        )

