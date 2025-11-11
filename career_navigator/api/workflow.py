from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from career_navigator.infrastructure.database.session import get_db
from career_navigator.infrastructure.llm.groq_adapter import GroqAdapter
from career_navigator.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from career_navigator.infrastructure.repositories.profile_repository import SQLAlchemyProfileRepository
from career_navigator.infrastructure.repositories.job_experience_repository import SQLAlchemyJobExperienceRepository
from career_navigator.infrastructure.repositories.course_repository import SQLAlchemyCourseRepository
from career_navigator.infrastructure.repositories.academic_repository import SQLAlchemyAcademicRepository
from career_navigator.infrastructure.repositories.product_repository import SQLAlchemyProductRepository
from career_navigator.application.workflow_service import WorkflowService
from career_navigator.api.schemas.product import ProductResponse

router = APIRouter(prefix="/workflow", tags=["Workflow"])


class CVParseRequest(BaseModel):
    user_id: int
    cv_content: str
    linkedin_url: Optional[str] = None


class LinkedInParseRequest(BaseModel):
    user_id: int
    linkedin_data: str
    linkedin_url: Optional[str] = None


class ParseResponse(BaseModel):
    profile_id: int
    job_experience_ids: list[int]
    course_ids: list[int]
    academic_record_ids: list[int]
    is_draft: bool
    message: str = "Data parsed and saved as draft. Please review and confirm."


class ValidationResponse(BaseModel):
    is_valid: bool
    errors: list[dict]
    warnings: list[dict]
    completeness_score: float
    recommendations: list[str]


class ConfirmDraftResponse(BaseModel):
    profile_id: int
    is_draft: bool
    message: str


def get_workflow_service(db: Session = Depends(get_db)) -> WorkflowService:
    """Dependency to get workflow service with all dependencies."""
    llm = GroqAdapter()
    
    user_repository = SQLAlchemyUserRepository(db)
    profile_repository = SQLAlchemyProfileRepository(db)
    job_repository = SQLAlchemyJobExperienceRepository(db)
    course_repository = SQLAlchemyCourseRepository(db)
    academic_repository = SQLAlchemyAcademicRepository(db)
    product_repository = SQLAlchemyProductRepository(db)
    
    return WorkflowService(
        llm=llm,
        user_repository=user_repository,
        profile_repository=profile_repository,
        job_repository=job_repository,
        course_repository=course_repository,
        academic_repository=academic_repository,
        product_repository=product_repository,
    )


@router.post("/parse-cv", response_model=ParseResponse, status_code=status.HTTP_201_CREATED)
def parse_cv(
    request: CVParseRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """
    Step 1: Parse CV content and save as draft.
    
    This endpoint:
    1. Parses the CV content using LLM
    2. Extracts structured data (profile, experiences, courses, academics)
    3. Saves everything as draft in the database
    4. Returns the IDs of created records
    """
    try:
        result = workflow_service.parse_and_save_cv(
            user_id=request.user_id,
            cv_content=request.cv_content,
            linkedin_url=request.linkedin_url,
        )
        return ParseResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse CV: {str(e)}",
        )


@router.post("/parse-linkedin", response_model=ParseResponse, status_code=status.HTTP_201_CREATED)
def parse_linkedin(
    request: LinkedInParseRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """
    Step 1: Parse LinkedIn profile data and save as draft.
    
    Same as parse-cv but for LinkedIn data.
    """
    try:
        result = workflow_service.parse_and_save_linkedin(
            user_id=request.user_id,
            linkedin_data=request.linkedin_data,
            linkedin_url=request.linkedin_url,
        )
        return ParseResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse LinkedIn data: {str(e)}",
        )


@router.post("/confirm-draft/{user_id}", response_model=ConfirmDraftResponse)
def confirm_draft(
    user_id: int,
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """
    Step 2: User confirms draft data is correct.
    
    After human review, this endpoint:
    1. Marks the profile as no longer a draft
    2. Makes it ready for validation
    """
    try:
        result = workflow_service.confirm_draft(user_id)
        return ConfirmDraftResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/validate/{user_id}", response_model=ValidationResponse)
def validate_profile(
    user_id: int,
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """
    Step 3: Validate profile data using guardrails.
    
    This endpoint:
    1. Runs guardrail validation on all user data
    2. Checks for completeness, consistency, and accuracy
    3. Returns validation report with errors, warnings, and recommendations
    4. Updates profile validation status
    """
    try:
        validation_report = workflow_service.validate_profile(user_id)
        return ValidationResponse(**validation_report)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}",
        )


@router.post("/generate-cv/{user_id}", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def generate_cv(
    user_id: int,
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """
    Step 4: Generate CV and save as product.
    
    This endpoint:
    1. Validates that profile is validated
    2. Generates a professional CV using LLM
    3. Saves it as a GeneratedProduct
    4. Returns the created product
    """
    try:
        product = workflow_service.generate_and_save_cv(user_id)
        return ProductResponse.model_validate(product)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CV generation failed: {str(e)}",
        )

