from typing import Dict, Any, Optional
from career_navigator.application.workflow_graph import WorkflowGraph
from career_navigator.domain.repositories.user_repository import UserRepository
from career_navigator.domain.repositories.profile_repository import ProfileRepository
from career_navigator.domain.repositories.job_experience_repository import JobExperienceRepository
from career_navigator.domain.repositories.course_repository import CourseRepository
from career_navigator.domain.repositories.academic_repository import AcademicRepository
from career_navigator.domain.repositories.product_repository import ProductRepository
from career_navigator.domain.llm import LanguageModel
from career_navigator.domain.models.product import GeneratedProduct
from career_navigator.domain.models.product_type import ProductType


class WorkflowService:
    """Orchestrates the CV/LinkedIn parsing and CV generation workflow using LangGraph."""

    def __init__(
        self,
        llm: LanguageModel,
        user_repository: UserRepository,
        profile_repository: ProfileRepository,
        job_repository: JobExperienceRepository,
        course_repository: CourseRepository,
        academic_repository: AcademicRepository,
        product_repository: ProductRepository,
    ):
        self.llm = llm
        self.user_repository = user_repository
        self.profile_repository = profile_repository
        self.job_repository = job_repository
        self.course_repository = course_repository
        self.academic_repository = academic_repository
        self.product_repository = product_repository
        
        # Initialize the workflow graph
        self.workflow_graph = WorkflowGraph(
            llm=llm,
            user_repository=user_repository,
            profile_repository=profile_repository,
            job_repository=job_repository,
            course_repository=course_repository,
            academic_repository=academic_repository,
            product_repository=product_repository,
        )

    def parse_and_save_cv(
        self, user_id: int, cv_content: str, linkedin_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Step 1: Parse CV content and save as draft using workflow graph.
        
        Returns:
        - profile_id: ID of created/updated profile
        - job_experience_ids: List of created job experience IDs
        - course_ids: List of created course IDs
        - academic_record_ids: List of created academic record IDs
        """
        initial_state = {
            "user_id": user_id,
            "input_type": "cv",
            "cv_content": cv_content,
            "linkedin_url": linkedin_url,
            "is_confirmed": False,
        }
        
        result = self.workflow_graph.run(initial_state)
        
        if result.get("error"):
            raise ValueError(result["error"])
        
        return {
            "profile_id": result["profile_id"],
            "job_experience_ids": result["job_experience_ids"],
            "course_ids": result["course_ids"],
            "academic_record_ids": result["academic_record_ids"],
            "is_draft": result["is_draft"],
        }

    def parse_and_save_linkedin(
        self, user_id: int, linkedin_data: str, linkedin_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Step 1: Parse LinkedIn data and save as draft using workflow graph.
        """
        initial_state = {
            "user_id": user_id,
            "input_type": "linkedin",
            "linkedin_data": linkedin_data,
            "linkedin_url": linkedin_url,
            "is_confirmed": False,
        }
        
        result = self.workflow_graph.run(initial_state)
        
        if result.get("error"):
            raise ValueError(result["error"])
        
        return {
            "profile_id": result["profile_id"],
            "job_experience_ids": result["job_experience_ids"],
            "course_ids": result["course_ids"],
            "academic_record_ids": result["academic_record_ids"],
            "is_draft": result["is_draft"],
        }

    def validate_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Step 3: Validate profile data using guardrails via workflow graph.
        
        Returns validation report.
        """
        # Get current profile state
        profile = self.profile_repository.get_by_user_id(user_id)
        if not profile:
            raise ValueError(f"Profile not found for user {user_id}")
        
        # Run validation step through the graph
        initial_state = {
            "user_id": user_id,
            "input_type": "cv",  # Doesn't matter for validation
            "is_confirmed": True,  # Skip to validation
        }
        
        result = self.workflow_graph.run(initial_state)
        
        if result.get("error"):
            raise ValueError(result["error"])
        
        return result.get("validation_report", {})

    def generate_and_save_cv(self, user_id: int) -> GeneratedProduct:
        """
        Step 4: Generate CV and save as product via workflow graph.
        
        Returns the generated product.
        """
        profile = self.profile_repository.get_by_user_id(user_id)
        if not profile:
            raise ValueError(f"Profile not found for user {user_id}")
        
        if not profile.is_validated:
            raise ValueError("Profile must be validated before generating CV")
        
        # Run full workflow with confirmed and validated flags
        initial_state = {
            "user_id": user_id,
            "input_type": "cv",  # Doesn't matter, we're past parsing
            "is_confirmed": True,
        }
        
        result = self.workflow_graph.run(initial_state)
        
        if result.get("error"):
            raise ValueError(result["error"])
        
        if not result.get("product_id"):
            raise ValueError("Failed to generate CV product")
        
        # Retrieve the created product
        product = self.product_repository.get_by_id(result["product_id"])
        if not product:
            raise ValueError("Product was created but not found")
        
        return product

    def confirm_draft(self, user_id: int) -> Dict[str, Any]:
        """
        Step 2: User confirms draft data is correct.
        Moves profile from draft to ready for validation.
        """
        profile = self.profile_repository.get_by_user_id(user_id)
        if not profile:
            raise ValueError(f"Profile not found for user {user_id}")
        
        profile.is_draft = False
        updated_profile = self.profile_repository.update(profile)
        
        return {
            "profile_id": updated_profile.id,
            "is_draft": False,
            "message": "Draft confirmed, ready for validation",
        }

