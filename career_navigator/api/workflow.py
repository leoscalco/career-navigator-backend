from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
import io
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
from career_navigator.infrastructure.document_parser import DocumentParser
from career_navigator.infrastructure.linkedin_api import LinkedInAPIClient, LinkedInAPIError
from career_navigator.api.auth import get_current_user
from career_navigator.domain.models.user import User as DomainUser

router = APIRouter(prefix="/workflow", tags=["Workflow"])


class CVParseRequest(BaseModel):
    user_id: Optional[int] = None  # Optional - will be created from CV if not provided
    cv_content: str
    linkedin_url: Optional[str] = None


class CVFileParseRequest(BaseModel):
    """Request model for file-based CV parsing (used internally)."""
    user_id: int
    cv_content: str
    linkedin_url: Optional[str] = None
    filename: Optional[str] = None


class LinkedInParseRequest(BaseModel):
    user_id: Optional[int] = None  # Optional - will be created from LinkedIn data if not provided
    linkedin_profile_url: Optional[str] = None  # LinkedIn profile URL (e.g., https://linkedin.com/in/username)
    linkedin_profile_id: Optional[str] = None  # LinkedIn profile ID or "me" for authenticated user
    linkedin_access_token: Optional[str] = None  # Optional OAuth access token (uses config if not provided)
    linkedin_data: Optional[str] = None  # Optional: raw LinkedIn data (if not using API)


class ParseResponse(BaseModel):
    user_id: int  # User ID (created or existing)
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
    
    This endpoint accepts CV content as plain text.
    For PDF/Word documents, use /parse-cv-file instead.
    
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


@router.post("/parse-cv-file", response_model=ParseResponse, status_code=status.HTTP_201_CREATED)
async def parse_cv_file(
    file: UploadFile = File(..., description="CV file (PDF, DOCX, or TXT)"),
    user_id: Optional[int] = Form(None, description="Optional User ID. If not provided, uses authenticated user's ID."),
    linkedin_url: Optional[str] = Form(None, description="Optional LinkedIn profile URL"),
    current_user: DomainUser = Depends(get_current_user),  # Requires Authorization: Bearer <token> header
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """
    Step 1: Parse CV from uploaded file and save as draft.
    
    This endpoint accepts CV files in various formats:
    - PDF (.pdf)
    - Word documents (.docx)
    - Plain text (.txt)
    
    The endpoint:
    1. Extracts text from the uploaded document
    2. Parses the CV content using LLM
    3. Extracts structured data (profile, experiences, courses, academics)
    4. Saves everything as draft in the database
    5. Returns the IDs of created records
    
    Supported file formats: PDF, DOCX, TXT
    Maximum file size: 10MB (configurable)
    """
    try:
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty",
            )
        
        # Check file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size is {max_size / (1024*1024):.1f}MB",
            )
        
        # Parse document based on file type
        try:
            cv_content = DocumentParser.parse_document(file_content, file.filename or "document")
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except ImportError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Document parsing library not installed: {str(e)}",
            )
        
        if not cv_content or not cv_content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract text from the document. Please ensure the file contains readable text.",
            )
        
        # Use authenticated user's ID if not provided
        effective_user_id = user_id if user_id is not None else current_user.id
        
        # Parse CV using workflow service
        result = workflow_service.parse_and_save_cv(
            user_id=effective_user_id,
            cv_content=cv_content,
            linkedin_url=linkedin_url,
        )
        
        return ParseResponse(**result)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse CV file: {str(e)}",
        )


@router.post("/parse-linkedin", response_model=ParseResponse, status_code=status.HTTP_201_CREATED)
def parse_linkedin(
    request: LinkedInParseRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """
    Step 1: Parse LinkedIn profile data and save as draft.
    
    This endpoint can work in two modes:
    1. **LinkedIn API mode** (recommended): Provide `linkedin_profile_url` or `linkedin_profile_id`
       - Fetches profile data directly from LinkedIn API
       - Requires LinkedIn OAuth access token (via `linkedin_access_token` or `LINKEDIN_ACCESS_TOKEN` env var)
    
    2. **Manual data mode**: Provide `linkedin_data` as raw text
       - Parses the provided LinkedIn data directly
    
    The endpoint:
    1. Fetches LinkedIn profile data (if using API mode)
    2. Parses the LinkedIn content using LLM
    3. Extracts structured data (profile, experiences, courses, academics)
    4. Creates user if user_id is not provided
    5. Saves everything as draft in the database
    6. Returns the IDs of created records
    """
    try:
        linkedin_data = None
        linkedin_url = None
        
        # If LinkedIn API is requested, fetch data from API
        if request.linkedin_profile_url or request.linkedin_profile_id:
            try:
                # Initialize LinkedIn API client
                access_token = request.linkedin_access_token
                linkedin_client = LinkedInAPIClient(access_token=access_token)
                
                # Determine profile ID
                profile_id = request.linkedin_profile_id
                if not profile_id:
                    # Default to "me" for authenticated user's profile
                    # Note: LinkedIn API v2 requires numeric ID or "me", not username from URL
                    profile_id = "me"
                
                # Store the URL for reference (even if we can't use it directly for API)
                linkedin_url = request.linkedin_profile_url
                
                # Fetch profile data from LinkedIn API
                # Note: If profile_url is provided but profile_id is not numeric or "me",
                # the API client will default to "me"
                profile_data = linkedin_client.get_profile(
                    profile_id=profile_id,
                    profile_url=linkedin_url
                )
                
                # Format profile data for parsing
                linkedin_data = linkedin_client.format_profile_for_parsing(profile_data)
                # Use provided URL or construct from profile data if available
                if not linkedin_url:
                    # Try to construct URL from profile data if we have the ID
                    if "id" in profile_data:
                        linkedin_url = f"https://linkedin.com/in/{profile_data['id']}"
                
            except LinkedInAPIError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to fetch LinkedIn profile: {str(e)}",
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                )
        elif request.linkedin_data:
            # Use provided LinkedIn data directly
            linkedin_data = request.linkedin_data
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either linkedin_profile_url/linkedin_profile_id or linkedin_data must be provided",
            )
        
        # Parse LinkedIn data
        result = workflow_service.parse_and_save_linkedin(
            user_id=request.user_id,  # Can be None - will be created from LinkedIn data
            linkedin_data=linkedin_data,
            linkedin_url=linkedin_url,
        )
        return ParseResponse(**result)
        
    except HTTPException:
        raise
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
        error_msg = str(e)
        # Check if it's a "not found" error vs a validation error
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        else:
            # Validation errors should be 400, not 404
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
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


@router.get("/products/{user_id}", response_model=list[ProductResponse])
def get_user_products(
    user_id: int,
    product_type: Optional[str] = Query(None, description="Filter by product type (cv, career_path, career_plan_1y, career_plan_3y, career_plan_5y, linkedin_export)"),
    db: Session = Depends(get_db),
):
    """
    Get all generated products for a user.
    
    This endpoint retrieves all products that were generated through the workflow
    for a specific user. Optionally filter by product type.
    
    Args:
        user_id: The ID of the user
        product_type: Optional filter by product type
        
    Returns:
        List of generated products
    """
    try:
        product_repository = SQLAlchemyProductRepository(db)
        
        # If product_type filter is provided, map it to ProductType enum
        if product_type:
            from career_navigator.domain.models.product_type import ProductType
            product_type_map = {
                "cv": ProductType.CV,
                "career_path": ProductType.POSSIBLE_JOBS,
                "career_plan_1y": ProductType.CAREER_PLAN_1Y,
                "career_plan_3y": ProductType.CAREER_PLAN_3Y,
                "career_plan_5y": ProductType.CAREER_PLAN_5Y,
                "linkedin_export": ProductType.LINKEDIN_EXPORT,
            }
            
            mapped_type = product_type_map.get(product_type.lower())
            if not mapped_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid product type: {product_type}. Valid types are: {', '.join(product_type_map.keys())}",
                )
            
            products = product_repository.get_by_user_and_type(user_id, mapped_type)
        else:
            products = product_repository.get_by_user_id(user_id)
        
        return [ProductResponse.model_validate(p) for p in products]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve products: {str(e)}",
        )

