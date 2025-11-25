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
        self, user_id: Optional[int], cv_content: str, linkedin_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Step 1: Parse CV content and save as draft using workflow graph.
        
        If user_id is None, a new user will be created from the parsed CV data.
        
        Returns:
        - user_id: ID of created/existing user
        - profile_id: ID of created/updated profile
        - job_experience_ids: List of created job experience IDs
        - course_ids: List of created course IDs
        - academic_record_ids: List of created academic record IDs
        """
        # Create Langfuse trace for unified tracing using OpenTelemetry
        from langfuse import Langfuse
        from career_navigator.config import settings
        from opentelemetry import trace
        
        langfuse_client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
        
        # Create trace using OpenTelemetry tracer
        tracer = langfuse_client._otel_tracer
        trace_id = langfuse_client.create_trace_id()
        
        # Start a new trace
        with tracer.start_as_current_span(
            "cv_parsing_workflow",
            attributes={
                "langfuse.trace.name": "cv_parsing_workflow",
                "langfuse.user.id": str(user_id) if user_id else "",
                "input_type": "cv",
                "has_linkedin_url": str(linkedin_url is not None),
            },
        ) as span:
            # Set trace ID in context
            span.set_attribute("langfuse.trace.id", trace_id)
            
            initial_state = {
                "user_id": user_id,  # Can be None
                "input_type": "cv",
                "cv_content": cv_content,
                "linkedin_url": linkedin_url,
                "is_confirmed": False,
                "langfuse_trace_id": trace_id,  # Store trace ID in state
            }
            
            result = self.workflow_graph.run(initial_state, trace_id=trace_id)
        
        if result.get("error"):
            raise ValueError(result["error"])
        
        if not result.get("user_id"):
            raise ValueError("User ID was not created during parsing")
        
        return {
            "user_id": result["user_id"],
            "profile_id": result["profile_id"],
            "job_experience_ids": result["job_experience_ids"],
            "course_ids": result["course_ids"],
            "academic_record_ids": result["academic_record_ids"],
            "is_draft": result["is_draft"],
        }

    def parse_and_save_linkedin(
        self, user_id: Optional[int], linkedin_data: str, linkedin_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Step 1: Parse LinkedIn data and save as draft using workflow graph.
        
        If user_id is None, a new user will be created from the parsed LinkedIn data.
        """
        # Create Langfuse trace for unified tracing using OpenTelemetry
        from langfuse import Langfuse
        from career_navigator.config import settings
        from opentelemetry import trace
        
        langfuse_client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
        
        # Create trace using OpenTelemetry tracer
        tracer = langfuse_client._otel_tracer
        trace_id = langfuse_client.create_trace_id()
        
        # Start a new trace
        with tracer.start_as_current_span(
            "linkedin_parsing_workflow",
            attributes={
                "langfuse.trace.name": "linkedin_parsing_workflow",
                "langfuse.user.id": str(user_id) if user_id else "",
                "input_type": "linkedin",
                "has_linkedin_url": str(linkedin_url is not None),
            },
        ) as span:
            # Set trace ID in context
            span.set_attribute("langfuse.trace.id", trace_id)
            
            initial_state = {
                "user_id": user_id,  # Can be None
                "input_type": "linkedin",
                "linkedin_data": linkedin_data,
                "linkedin_url": linkedin_url,
                "is_confirmed": False,
                "langfuse_trace_id": trace_id,  # Store trace ID in state
            }
            
            result = self.workflow_graph.run(initial_state, trace_id=trace_id)
        
        if result.get("error"):
            raise ValueError(result["error"])
        
        if not result.get("user_id"):
            raise ValueError("User ID was not created during parsing")
        
        return {
            "user_id": result["user_id"],
            "profile_id": result["profile_id"],
            "job_experience_ids": result["job_experience_ids"],
            "course_ids": result["course_ids"],
            "academic_record_ids": result["academic_record_ids"],
            "is_draft": result["is_draft"],
        }

    def validate_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Step 3: Validate profile data using guardrails.
        
        Returns validation report.
        """
        # Get current profile state
        profile = self.profile_repository.get_by_user_id(user_id)
        if not profile:
            raise ValueError(f"Profile not found for user {user_id}")
        
        # Try to get trace_id from workflow state (checkpointer) if available
        # This allows us to link validation to the original CV parsing trace
        from langfuse import Langfuse
        from career_navigator.config import settings
        from opentelemetry import trace
        
        langfuse_client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
        
        # Try to get trace_id from stored user trace_ids (set during CV parsing)
        trace_id = self.workflow_graph._user_trace_ids.get(user_id)
        
        # If not found, try to get from workflow state (checkpointer)
        if not trace_id:
            try:
                thread_id = f"user_{user_id}"
                workflow_state = self.workflow_graph.get_state(thread_id)
                if workflow_state:
                    trace_id = workflow_state.get("langfuse_trace_id")
            except Exception:
                pass
        
        # If still not found, try to get from the workflow's current trace
        if not trace_id:
            trace_id = self.workflow_graph._current_trace_id
        
        # If still no trace_id, create a new one (fallback)
        if not trace_id:
            trace_id = langfuse_client.create_trace_id()
        
        # Create trace using OpenTelemetry tracer
        tracer = langfuse_client._otel_tracer
        
        # Start trace for validation - use the same trace_id from CV parsing if available
        with tracer.start_as_current_span(
            "profile_validation",
            attributes={
                "langfuse.trace.name": "profile_validation",
                "langfuse.trace.id": trace_id,  # Use the same trace_id from CV parsing
                "langfuse.user.id": str(user_id),
                "linked_to_profile": str(profile.id),
            },
        ) as span:
            # Set trace ID in context
            span.set_attribute("langfuse.trace.id", trace_id)
            
            # Use workflow graph's validate node to ensure proper trace context
            initial_state = {
                "user_id": user_id,
                "input_type": "cv",  # Doesn't matter for validation
                "is_confirmed": True,  # Skip confirmation step
                "is_validated": False,  # Will be set by validation
                "langfuse_trace_id": trace_id,  # Use the same trace_id
            }
            
            # Run workflow graph - it will route: parse (skip) -> save_draft (skip) -> wait_confirmation (skip) -> validate
            result = self.workflow_graph.run(initial_state, trace_id=trace_id)
        
        # Extract validation report from result
        validation_report = result.get("validation_report")
        if not validation_report:
            # Check if there's an error in the result
            if result.get("error"):
                error_msg = result["error"]
                # Check if it's a JSON parsing error
                if "extra data" in error_msg.lower() or "json" in error_msg.lower():
                    raise ValueError(f"Validation failed: Could not parse validation response. {error_msg}")
                raise ValueError(f"Validation failed: {error_msg}")
            raise ValueError("Validation failed: No validation report generated")
        
        return validation_report

    def generate_and_save_cv(self, user_id: int) -> GeneratedProduct:
        """
        Generate CV and save as product via workflow graph.
        
        Returns the generated product.
        """
        return self._generate_product(user_id, "cv")
    
    def generate_and_save_career_path(self, user_id: int) -> GeneratedProduct:
        """Generate career path and save as product."""
        return self._generate_product(user_id, "career_path")
    
    def generate_and_save_career_plan_1y(self, user_id: int) -> GeneratedProduct:
        """Generate 1-year career plan and save as product."""
        return self._generate_product(user_id, "career_plan_1y")
    
    def generate_and_save_career_plan_3y(self, user_id: int) -> GeneratedProduct:
        """Generate 3-year career plan and save as product."""
        return self._generate_product(user_id, "career_plan_3y")
    
    def generate_and_save_career_plan_5y(self, user_id: int) -> GeneratedProduct:
        """Generate 5+ year career plan and save as product."""
        return self._generate_product(user_id, "career_plan_5y")
    
    def generate_and_save_linkedin_export(self, user_id: int) -> GeneratedProduct:
        """Generate LinkedIn export and save as product."""
        return self._generate_product(user_id, "linkedin_export")
    
    def _generate_product(self, user_id: int, product_type: str) -> GeneratedProduct:
        """
        Generic method to generate any product type.
        
        Args:
            user_id: User ID
            product_type: One of "cv", "career_path", "career_plan_1y", "career_plan_3y", "career_plan_5y", "linkedin_export"
        """
        profile = self.profile_repository.get_by_user_id(user_id)
        if not profile:
            raise ValueError(f"Profile not found for user {user_id}")
        
        if not profile.is_validated:
            raise ValueError("Profile must be validated before generating products")
        
        # Retrieve trace_id from profile if available (to link to original parsing trace)
        # For now, we'll create a new trace for product generation, but ideally we'd store trace_id in profile
        # TODO: Store langfuse_trace_id in profile when saving draft, then retrieve it here
        from langfuse import Langfuse
        from career_navigator.config import settings
        from opentelemetry import trace
        
        langfuse_client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
        
        # Create trace using OpenTelemetry tracer
        tracer = langfuse_client._otel_tracer
        trace_id = langfuse_client.create_trace_id()
        
        # Start a new trace for product generation
        with tracer.start_as_current_span(
            f"{product_type}_generation",
            attributes={
                "langfuse.trace.name": f"{product_type}_generation",
                "langfuse.user.id": str(user_id),
                "product_type": product_type,
                "linked_to_profile": str(profile.id),
            },
        ) as span:
            # Set trace ID in context
            span.set_attribute("langfuse.trace.id", trace_id)
            
            # Run workflow with product type
            # Skip parsing/validation steps and go directly to product generation
            initial_state = {
                "user_id": user_id,
                "input_type": "cv",  # Doesn't matter, we're past parsing
                "product_type": product_type,
                "is_confirmed": True,
                "is_validated": True,
                "human_decision": "approve",  # Auto-approve product saving
                "langfuse_trace_id": trace_id,  # Link to trace
            }
            
            result = self.workflow_graph.run(initial_state, trace_id=trace_id)
        
        if result.get("error"):
            error_msg = result["error"]
            current_step = result.get("current_step", "unknown")
            raise ValueError(f"Workflow error at step '{current_step}': {error_msg}")
        
        if not result.get("product_id"):
            # Provide more details about what went wrong
            current_step = result.get("current_step", "unknown")
            generated_content = result.get(f"generated_{product_type}")
            if not generated_content:
                raise ValueError(
                    f"Failed to generate {product_type} product: "
                    f"Content was not generated. Current step: {current_step}. "
                    f"State: {result.get('is_validated')=}, {result.get('is_confirmed')=}, "
                    f"{result.get('needs_human_review')=}"
                )
            else:
                raise ValueError(
                    f"Failed to generate {product_type} product: "
                    f"Product was generated but not saved. Current step: {current_step}. "
                    f"State: {result.get('is_validated')=}, {result.get('is_confirmed')=}, "
                    f"{result.get('needs_human_review')=}, human_decision={result.get('human_decision')}"
                )
        
        # Retrieve the created product
        product = self.product_repository.get_by_id(result["product_id"])
        if not product:
            raise ValueError("Product was created but not found")
        
        return product
    
    def get_workflow_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get current workflow status for a user.
        
        Returns:
            Dictionary with workflow status, current step, and pending actions
        """
        thread_id = f"user_{user_id}"
        state = self.workflow_graph.get_state(thread_id)
        
        if not state:
            # Check if profile exists
            profile = self.profile_repository.get_by_user_id(user_id)
            if not profile:
                return {
                    "status": "not_started",
                    "message": "No workflow started for this user",
                }
            
            return {
                "status": "completed",
                "current_step": "completed",
                "is_draft": profile.is_draft,
                "is_validated": profile.is_validated,
            }
        
        return {
            "status": "in_progress",
            "current_step": state.get("current_step", "unknown"),
            "needs_human_review": state.get("needs_human_review", False),
            "is_draft": state.get("is_draft", False),
            "is_validated": state.get("is_validated", False),
            "error": state.get("error"),
        }
    
    def resume_workflow(self, user_id: int, human_decision: str) -> Dict[str, Any]:
        """
        Resume workflow after human decision.
        
        Args:
            user_id: User ID
            human_decision: "approve", "edit", or "reject"
            
        Returns:
            Updated workflow state
        """
        thread_id = f"user_{user_id}"
        result = self.workflow_graph.resume_workflow(thread_id, human_decision)
        return result

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
    
    def get_workflow_graph_image(self, format: str = "png") -> bytes:
        """
        Generate a visual representation of the workflow graph.
        
        Args:
            format: Image format ("png", "svg", or "jpg")
            
        Returns:
            Image bytes
        """
        return self.workflow_graph.get_graph_image(format)

