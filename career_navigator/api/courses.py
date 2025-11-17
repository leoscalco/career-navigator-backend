from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from career_navigator.infrastructure.database.session import get_db
from career_navigator.infrastructure.repositories.course_repository import SQLAlchemyCourseRepository
from career_navigator.domain.models.course import Course as DomainCourse
from career_navigator.api.schemas.course import CourseCreate, CourseUpdate, CourseResponse

router = APIRouter(prefix="/courses", tags=["Courses"])


def get_course_repository(db: Session = Depends(get_db)) -> SQLAlchemyCourseRepository:
    """Dependency to get course repository."""
    return SQLAlchemyCourseRepository(db)


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    course_data: CourseCreate,
    repository: SQLAlchemyCourseRepository = Depends(get_course_repository),
):
    """Create a new course."""
    domain_course = DomainCourse(**course_data.model_dump())
    created_course = repository.create(domain_course)
    return CourseResponse.model_validate(created_course)


@router.get("", response_model=List[CourseResponse])
def get_all_courses(
    repository: SQLAlchemyCourseRepository = Depends(get_course_repository),
):
    """Get all courses."""
    courses = repository.get_all()
    return [CourseResponse.model_validate(c) for c in courses]


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: int,
    repository: SQLAlchemyCourseRepository = Depends(get_course_repository),
):
    """Get a course by ID."""
    course = repository.get_by_id(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with id {course_id} not found",
        )
    return CourseResponse.model_validate(course)


@router.get("/user/{user_id}", response_model=List[CourseResponse])
def get_courses_by_user(
    user_id: int,
    repository: SQLAlchemyCourseRepository = Depends(get_course_repository),
):
    """Get all courses for a user."""
    courses = repository.get_by_user_id(user_id)
    return [CourseResponse.model_validate(c) for c in courses]


@router.put("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    course_data: CourseUpdate,
    repository: SQLAlchemyCourseRepository = Depends(get_course_repository),
):
    """Update a course."""
    existing_course = repository.get_by_id(course_id)
    if not existing_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with id {course_id} not found",
        )
    
    # Update only provided fields
    update_data = course_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_course, field, value)
    
    updated_course = repository.update(existing_course)
    return CourseResponse.model_validate(updated_course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    repository: SQLAlchemyCourseRepository = Depends(get_course_repository),
):
    """Delete a course."""
    success = repository.delete(course_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with id {course_id} not found",
        )

