from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from career_navigator.infrastructure.database.session import get_db
from career_navigator.infrastructure.repositories.academic_repository import SQLAlchemyAcademicRepository
from career_navigator.domain.models.academic import AcademicRecord as DomainAcademic
from career_navigator.api.schemas.academic import AcademicRecordCreate, AcademicRecordUpdate, AcademicRecordResponse

router = APIRouter(prefix="/academics", tags=["Academic Records"])


def get_academic_repository(db: Session = Depends(get_db)) -> SQLAlchemyAcademicRepository:
    """Dependency to get academic repository."""
    return SQLAlchemyAcademicRepository(db)


@router.post("", response_model=AcademicRecordResponse, status_code=status.HTTP_201_CREATED)
def create_academic_record(
    academic_data: AcademicRecordCreate,
    repository: SQLAlchemyAcademicRepository = Depends(get_academic_repository),
):
    """Create a new academic record."""
    domain_academic = DomainAcademic(**academic_data.model_dump())
    created_academic = repository.create(domain_academic)
    return AcademicRecordResponse.model_validate(created_academic)


@router.get("", response_model=List[AcademicRecordResponse])
def get_all_academic_records(
    repository: SQLAlchemyAcademicRepository = Depends(get_academic_repository),
):
    """Get all academic records."""
    academics = repository.get_all()
    return [AcademicRecordResponse.model_validate(a) for a in academics]


@router.get("/{academic_id}", response_model=AcademicRecordResponse)
def get_academic_record(
    academic_id: int,
    repository: SQLAlchemyAcademicRepository = Depends(get_academic_repository),
):
    """Get an academic record by ID."""
    academic = repository.get_by_id(academic_id)
    if not academic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic record with id {academic_id} not found",
        )
    return AcademicRecordResponse.model_validate(academic)


@router.get("/user/{user_id}", response_model=List[AcademicRecordResponse])
def get_academic_records_by_user(
    user_id: int,
    repository: SQLAlchemyAcademicRepository = Depends(get_academic_repository),
):
    """Get all academic records for a user."""
    academics = repository.get_by_user_id(user_id)
    return [AcademicRecordResponse.model_validate(a) for a in academics]


@router.put("/{academic_id}", response_model=AcademicRecordResponse)
def update_academic_record(
    academic_id: int,
    academic_data: AcademicRecordUpdate,
    repository: SQLAlchemyAcademicRepository = Depends(get_academic_repository),
):
    """Update an academic record."""
    existing_academic = repository.get_by_id(academic_id)
    if not existing_academic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic record with id {academic_id} not found",
        )
    
    # Update only provided fields
    update_data = academic_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_academic, field, value)
    
    updated_academic = repository.update(existing_academic)
    return AcademicRecordResponse.model_validate(updated_academic)


@router.delete("/{academic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_academic_record(
    academic_id: int,
    repository: SQLAlchemyAcademicRepository = Depends(get_academic_repository),
):
    """Delete an academic record."""
    success = repository.delete(academic_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic record with id {academic_id} not found",
        )

