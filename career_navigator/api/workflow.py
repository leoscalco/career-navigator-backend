from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
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
    Generate CV and save as product.
    
    Requires validated profile. Workflow will pause for human approval before saving.
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


@router.post("/generate-career-path/{user_id}", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def generate_career_path(
    user_id: int,
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """
    Generate career path suggestions and save as product.
    
    Requires validated profile. Returns career path recommendations based on user's profile.
    """
    try:
        product = workflow_service.generate_and_save_career_path(user_id)
        return ProductResponse.model_validate(product)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Career path generation failed: {str(e)}",
        )


@router.post("/generate-career-plan-1y/{user_id}", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def generate_career_plan_1y(
    user_id: int,
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """Generate 1-year career plan and save as product."""
    try:
        product = workflow_service.generate_and_save_career_plan_1y(user_id)
        return ProductResponse.model_validate(product)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"1-year career plan generation failed: {str(e)}",
        )


@router.post("/generate-career-plan-3y/{user_id}", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def generate_career_plan_3y(
    user_id: int,
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """Generate 3-year career plan and save as product."""
    try:
        product = workflow_service.generate_and_save_career_plan_3y(user_id)
        return ProductResponse.model_validate(product)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"3-year career plan generation failed: {str(e)}",
        )


@router.post("/generate-career-plan-5y/{user_id}", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def generate_career_plan_5y(
    user_id: int,
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """Generate 5+ year career plan and save as product."""
    try:
        product = workflow_service.generate_and_save_career_plan_5y(user_id)
        return ProductResponse.model_validate(product)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"5-year career plan generation failed: {str(e)}",
        )


@router.post("/generate-linkedin-export/{user_id}", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def generate_linkedin_export(
    user_id: int,
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """Generate LinkedIn profile export optimization and save as product."""
    try:
        product = workflow_service.generate_and_save_linkedin_export(user_id)
        return ProductResponse.model_validate(product)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LinkedIn export generation failed: {str(e)}",
        )


class WorkflowStatusResponse(BaseModel):
    status: str
    current_step: str
    needs_human_review: bool = False
    is_draft: bool = False
    is_validated: bool = False
    error: Optional[str] = None
    message: Optional[str] = None


class ResumeWorkflowRequest(BaseModel):
    human_decision: str  # "approve", "edit", or "reject"


@router.get("/status/{user_id}", response_model=WorkflowStatusResponse)
def get_workflow_status(
    user_id: int,
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """
    Get current workflow status for a user.
    
    Returns:
    - status: "not_started", "in_progress", "completed", "error"
    - current_step: Current step in the workflow
    - needs_human_review: Whether workflow is waiting for human input
    - is_draft: Whether profile is still a draft
    - is_validated: Whether profile has been validated
    """
    try:
        status_info = workflow_service.get_workflow_status(user_id)
        return WorkflowStatusResponse(**status_info)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow status: {str(e)}",
        )


@router.post("/resume/{user_id}", response_model=WorkflowStatusResponse)
def resume_workflow(
    user_id: int,
    request: ResumeWorkflowRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """
    Resume workflow after human decision.
    
    This endpoint resumes the workflow from a checkpoint after human review.
    
    human_decision options:
    - "approve": Approve and continue
    - "edit": User will edit data (workflow waits)
    - "reject": Reject and stop workflow
    """
    if request.human_decision not in ["approve", "edit", "reject"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="human_decision must be 'approve', 'edit', or 'reject'",
        )
    
    try:
        result = workflow_service.resume_workflow(user_id, request.human_decision)
        return WorkflowStatusResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume workflow: {str(e)}",
        )


@router.get("/graph-image", response_class=Response)
def get_workflow_graph_image(
    format: str = Query("png", regex="^(png|svg|jpg|jpeg)$", description="Image format (png, svg, jpg, jpeg)"),
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """
    Generate and download the workflow graph as an image.
    
    This endpoint creates a visual representation of the LangGraph workflow
    showing all nodes, edges, and human-in-the-loop checkpoints.
    
    Supported formats:
    - png (default)
    - svg
    - jpg/jpeg
    
    Returns:
        Image file ready for download
    """
    try:
        # Normalize format
        if format.lower() == "jpeg":
            format = "jpg"
        
        # Get graph image from workflow service
        image_bytes = workflow_service.get_workflow_graph_image(format.lower())
        
        # Determine content type
        content_types = {
            "png": "image/png",
            "svg": "image/svg+xml",
            "jpg": "image/jpeg",
        }
        content_type = content_types.get(format.lower(), "image/png")
        
        # Return image as downloadable file
        return Response(
            content=image_bytes,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="workflow_graph.{format.lower()}"',
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate graph image: {str(e)}",
        )

