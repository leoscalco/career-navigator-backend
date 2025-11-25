from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from career_navigator.domain.llm import LanguageModel
from career_navigator.domain.repositories.user_repository import UserRepository
from career_navigator.domain.repositories.profile_repository import ProfileRepository
from career_navigator.domain.repositories.job_experience_repository import JobExperienceRepository
from career_navigator.domain.repositories.course_repository import CourseRepository
from career_navigator.domain.repositories.academic_repository import AcademicRepository
from career_navigator.domain.repositories.product_repository import ProductRepository
from career_navigator.domain.prompts import (
    CV_PARSING_PROMPT,
    LINKEDIN_PARSING_PROMPT,
    GUARDRAIL_VALIDATION_PROMPT,
    CV_GENERATION_PROMPT,
    LINKEDIN_EXPORT_PROMPT,
)
from career_navigator.domain.models.product_type import ProductType
from career_navigator.application.career_planning_service import CareerPlanningService
import json
from datetime import date
from typing import Any


class WorkflowState(TypedDict):
    """State that flows through the workflow graph."""
    # Input
    user_id: int | None  # None initially, created from parsed data
    input_type: Literal["cv", "linkedin"]
    cv_content: str | None
    linkedin_data: str | None
    linkedin_url: str | None
    # User info extracted from CV (for user creation)
    user_email: str | None
    user_name: str | None
    user_group: str | None  # Will be determined or provided
    
    # Product generation request
    product_type: str | None  # "cv", "career_path", "career_plan_1y", "career_plan_3y", "career_plan_5y", "linkedin_export"
    
    # Parsed data
    parsed_data: dict | None
    profile_id: int | None
    job_experience_ids: list[int]
    course_ids: list[int]
    academic_record_ids: list[int]
    
    # Workflow status
    is_draft: bool
    is_confirmed: bool
    is_validated: bool
    validation_report: dict | None
    
    # Generated products
    generated_cv: str | None
    generated_career_path: dict | None
    generated_career_plan_1y: dict | None
    generated_career_plan_3y: dict | None
    generated_career_plan_5y: dict | None
    generated_linkedin_export: dict | None
    product_id: int | None
    
    # Human-in-the-loop
    needs_human_review: bool
    human_decision: str | None  # "approve", "edit", "reject"
    
    # Langfuse tracing
    langfuse_trace_id: str | None  # Trace ID for unified tracing across workflow
    
    # Error handling
    error: str | None
    current_step: str


class WorkflowGraph:
    """
    LangGraph-based workflow for CV/LinkedIn processing and CV generation.
    
    Uses LangGraph's interrupt mechanism for human-in-the-loop checkpoints
    and custom guardrails validation in nodes.
    """

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
        
        # Initialize career planning service
        self.career_planning_service = CareerPlanningService(llm)
        
        # Create checkpointer for human-in-the-loop (state persistence)
        self.checkpointer = MemorySaver()
        
        # Langfuse client for tracing (initialized lazily)
        self._langfuse_client = None
        self._current_trace_id = None
        # Store trace_id by user_id for unified tracing across workflow steps
        self._user_trace_ids: dict[int, str] = {}
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _get_langfuse_client(self):
        """Get or create Langfuse client."""
        if self._langfuse_client is None:
            from langfuse import Langfuse
            from career_navigator.config import settings
            self._langfuse_client = Langfuse(
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                secret_key=settings.LANGFUSE_SECRET_KEY,
                host=settings.LANGFUSE_HOST,
            )
        return self._langfuse_client
    
    def _create_span_context(self, node_name: str, trace_id: str | None = None, metadata: dict | None = None):
        """Create a Langfuse span context for a workflow node using OpenTelemetry.
        
        Returns a context manager that should be used with 'with' statement.
        The OpenTelemetry context will be automatically propagated to LangChain callbacks.
        """
        if not trace_id:
            trace_id = self._current_trace_id
        
        if not trace_id:
            # Return a no-op context manager if no trace_id
            from contextlib import nullcontext
            return nullcontext()
        
        try:
            client = self._get_langfuse_client()
            tracer = client._otel_tracer
            
            # Create span within the current trace context
            # Use start_as_current_span for proper context propagation
            # This will automatically propagate to LangChain callbacks
            span_context = tracer.start_as_current_span(
                node_name,
                attributes={
                    "langfuse.span.name": node_name,
                    "langfuse.trace.id": trace_id,
                    **(metadata or {}),
                },
            )
            return span_context
        except Exception as e:
            # If tracing fails, continue without it
            # Log error for debugging but don't break workflow
            import logging
            from contextlib import nullcontext
            logging.warning(f"Failed to create Langfuse span: {e}")
            return nullcontext()

    def _build_graph(self):
        """
        Build the LangGraph workflow graph with checkpointer for human-in-the-loop.
        
        Human-in-the-loop checkpoints:
        - After save_draft: User reviews parsed data
        - After validate: User reviews validation results
        - Before generating products: User approves generation
        - Before save_product: User reviews final product
        
        Product generation paths:
        - CV generation
        - Career path suggestions
        - Career plans (1y, 3y, 5y)
        - LinkedIn export
        """
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("parse", self._parse_node)
        workflow.add_node("save_draft", self._save_draft_node)
        workflow.add_node("wait_confirmation", self._wait_confirmation_node)
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("check_validation", self._check_validation_node)
        
        # Product generation nodes
        workflow.add_node("generate_cv", self._generate_cv_node)
        workflow.add_node("generate_career_path", self._generate_career_path_node)
        workflow.add_node("generate_career_plan_1y", self._generate_career_plan_1y_node)
        workflow.add_node("generate_career_plan_3y", self._generate_career_plan_3y_node)
        workflow.add_node("generate_career_plan_5y", self._generate_career_plan_5y_node)
        workflow.add_node("generate_linkedin_export", self._generate_linkedin_export_node)
        
        workflow.add_node("save_product", self._save_product_node)
        workflow.add_node("select_product_type", self._select_product_type_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # Define the flow
        workflow.set_entry_point("parse")
        
        # Parse → Save Draft
        workflow.add_edge("parse", "save_draft")
        
        # Save Draft → Wait for Confirmation (HUMAN-IN-THE-LOOP CHECKPOINT with interrupt)
        workflow.add_edge("save_draft", "wait_confirmation")
        
        # After confirmation, validate or skip to product generation
        workflow.add_conditional_edges(
            "wait_confirmation",
            self._should_validate_or_skip_to_product,
            {
                "validate": "validate",
                "skip_to_product": "select_product_type",  # Skip directly to product generation
                "skip": END,
            }
        )
        
        # Validate → Check validation result (GUARDRAILS VALIDATION)
        workflow.add_edge("validate", "check_validation")
        
        # Check validation → Select product type or retry
        # Also route directly to select_product_type if already validated and product_type is set
        workflow.add_conditional_edges(
            "check_validation",
            self._should_generate_product,
            {
                "generate": "select_product_type",
                "retry": "wait_confirmation",  # Go back to allow user to fix issues
                "end": END,
            }
        )
        
        # Add conditional entry point: if already validated and product_type is set, skip to select_product_type
        # This is handled by modifying parse node to check conditions
        
        # Select product type → Route to appropriate generator
        workflow.add_conditional_edges(
            "select_product_type",
            self._route_to_product_generator,
            {
                "cv": "generate_cv",
                "career_path": "generate_career_path",
                "career_plan_1y": "generate_career_plan_1y",
                "career_plan_3y": "generate_career_plan_3y",
                "career_plan_5y": "generate_career_plan_5y",
                "linkedin_export": "generate_linkedin_export",
                "end": END,
            }
        )
        
        # All generators → Save Product (HUMAN-IN-THE-LOOP CHECKPOINT)
        workflow.add_edge("generate_cv", "save_product")
        workflow.add_edge("generate_career_path", "save_product")
        workflow.add_edge("generate_career_plan_1y", "save_product")
        workflow.add_edge("generate_career_plan_3y", "save_product")
        workflow.add_edge("generate_career_plan_5y", "save_product")
        workflow.add_edge("generate_linkedin_export", "save_product")
        
        # Save Product → End
        workflow.add_edge("save_product", END)
        
        # Error handling
        workflow.add_edge("error_handler", END)
        
        # Compile with checkpointer for state persistence and interrupts
        # Note: interrupt_before will pause BEFORE executing these nodes
        # For direct product generation, we handle approval via human_decision in the node itself
        # We don't use interrupt_before for wait_confirmation because it would block direct product generation
        # Instead, we handle the interrupt logic inside wait_confirmation node itself
        return workflow.compile(checkpointer=self.checkpointer)

    def _parse_node(self, state: WorkflowState) -> WorkflowState:
        """Parse CV or LinkedIn content."""
        trace_id = state.get("langfuse_trace_id")
        span_context = self._create_span_context("parse", trace_id, {"input_type": state.get("input_type")})
        
        # Use span context manager - OpenTelemetry context will be propagated to LLM calls
        with span_context:
            try:
                state["current_step"] = "parsing"
                
                # Skip parsing if we're already past this step (e.g., for product generation)
                # If profile is validated and product_type is set, skip directly to product generation
                user_id = state.get("user_id")
                if state.get("is_validated") and state.get("product_type") and user_id:
                    profile = self.profile_repository.get_by_user_id(user_id)
                    if profile and profile.is_validated:
                        # Skip all parsing/validation steps, go directly to product generation
                        # Set parsed_data to None (not empty dict) so save_draft can detect the skip
                        state["parsed_data"] = None
                        state["is_confirmed"] = True  # Ensure confirmation is set
                        state["error"] = None
                        return state
                
                # Skip parsing if we're already past this step (e.g., for validation-only calls)
                # Check if profile already exists and we're just validating
                user_id = state.get("user_id")
                if state.get("is_confirmed") and user_id:
                    profile = self.profile_repository.get_by_user_id(user_id)
                    if profile and not state.get("cv_content") and not state.get("linkedin_data"):
                        # Skip parsing, go directly to next step
                        state["parsed_data"] = None  # None, will be skipped in save_draft
                        state["error"] = None
                        return state
                
                if state["input_type"] == "cv":
                    if not state.get("cv_content"):
                        raise ValueError("CV content is required")
                    prompt = CV_PARSING_PROMPT.format(cv_content=state["cv_content"])
                else:  # linkedin
                    if not state.get("linkedin_data"):
                        raise ValueError("LinkedIn data is required")
                    prompt = LINKEDIN_PARSING_PROMPT.format(linkedin_data=state["linkedin_data"])
                
                response = self.llm.generate(prompt, trace_id=trace_id)
                response = self._extract_json(response)
                parsed_data = json.loads(response)
                
                state["parsed_data"] = self._structure_parsed_data(parsed_data)
                state["error"] = None
                
                # Set span attributes for success
                from opentelemetry import trace
                span = trace.get_current_span()
                if span and span.is_recording():
                    span.set_attribute("status", "success")
                    span.set_attribute("has_parsed_data", "true")
                
            except Exception as e:
                state["error"] = f"Parsing failed: {str(e)}"
                state["current_step"] = "error"
                # Set span attributes for error
                from opentelemetry import trace
                span = trace.get_current_span()
                if span and span.is_recording():
                    span.set_attribute("status", "error")
                    span.set_attribute("error", str(e))
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
        
        return state

    def _save_draft_node(self, state: WorkflowState) -> WorkflowState:
        """
        Save parsed data as draft.
        Creates user from parsed data if user_id is None.
        This is a checkpoint for human-in-the-loop review.
        """
        if state.get("error"):
            return state
        
        try:
            parsed_data = state.get("parsed_data")
            user_id = state.get("user_id")
            
            # Skip if we're generating products directly (already validated, product_type set)
            # This check must come FIRST before setting current_step
            if state.get("is_validated") and state.get("product_type") and user_id:
                # Check if parsed_data is None (indicating we're skipping parsing)
                if parsed_data is None:
                    profile = self.profile_repository.get_by_user_id(user_id)
                    if profile and profile.is_validated:
                        state["profile_id"] = profile.id
                        state["is_draft"] = profile.is_draft
                        state["is_confirmed"] = True
                        state["is_validated"] = profile.is_validated
                        state["current_step"] = "skipped_draft"  # Mark as skipped
                        state["error"] = None
                        return state
            
            # Skip if we're validating an existing profile (no new parsed data)
            if parsed_data is None and state.get("is_confirmed") and user_id:
                # Profile already exists, just mark as ready for validation
                profile = self.profile_repository.get_by_user_id(user_id)
                if profile:
                    state["profile_id"] = profile.id
                    state["is_draft"] = profile.is_draft
                    state["current_step"] = "skipped_draft"  # Mark as skipped
                    state["error"] = None
                    return state
            
            # Normal flow: save parsed data
            state["current_step"] = "saving_draft"
            
            if not parsed_data:
                raise ValueError("No parsed data to save")
            
            # Get or create/update user (from parsed data)
            user_id = state.get("user_id")
            user_email = parsed_data.get("user_email") or state.get("user_email")
            user_name = parsed_data.get("user_name") or state.get("user_name")
            
            from career_navigator.domain.models.user import User as DomainUser
            from career_navigator.domain.models.user_group import UserGroup
            
            existing_user = None
            
            # First, check if user_id is provided and user exists
            if user_id:
                existing_user = self.user_repository.get_by_id(user_id)
            
            # If no user found by ID, check by email
            if not existing_user and user_email:
                existing_user = self.user_repository.get_by_email(user_email)
                if existing_user:
                    user_id = existing_user.id
            
            if existing_user:
                # Update existing user with new information from CV
                # Determine user_group based on experience
                job_experiences = parsed_data.get("job_experiences", [])
                has_experience = len(job_experiences) > 0
                has_goals = bool(parsed_data.get("career_goals") or parsed_data.get("short_term_goals") or parsed_data.get("long_term_goals"))
                
                if has_experience and has_goals:
                    updated_user_group = UserGroup.EXPERIENCED_CONTINUING
                elif has_experience and not has_goals:
                    updated_user_group = UserGroup.EXPERIENCED_CHANGING
                elif not has_experience and has_goals:
                    updated_user_group = UserGroup.INEXPERIENCED_WITH_GOAL
                else:
                    updated_user_group = UserGroup.INEXPERIENCED_NO_GOAL
                
                # Update username if we have a new name from CV
                username = existing_user.username
                if user_name and user_name.strip():
                    # Preserve the original name structure, just replace spaces with underscores for DB
                    username = "".join(c for c in user_name if c.isalnum() or c in [" ", "_", "-", ".", "'"])[:100].strip()
                    username = username.replace(" ", "_")
                    if not username:
                        username = existing_user.username or (user_email.split("@")[0] if user_email else None)
                
                # Update user with new information
                updated_user = DomainUser(
                    id=existing_user.id,
                    email=user_email or existing_user.email,
                    username=username,
                    user_group=updated_user_group,
                )
                self.user_repository.update(updated_user)
                user_id = existing_user.id
            else:
                # Create new user
                if not user_email:
                    # Generate placeholder email if not found
                    cv_content = state.get('cv_content') or state.get('linkedin_data') or ''
                    content_hash = abs(hash(str(cv_content)[:50]))
                    user_email = f"user_{content_hash}@temp.careernavigator.com"
                
                # Determine user_group based on experience (default to inexperienced_no_goal)
                user_group: UserGroup
                
                # Try to determine user group from parsed data
                job_experiences = parsed_data.get("job_experiences", [])
                has_experience = len(job_experiences) > 0
                has_goals = bool(parsed_data.get("career_goals") or parsed_data.get("short_term_goals") or parsed_data.get("long_term_goals"))
                
                if has_experience and has_goals:
                    user_group = UserGroup.EXPERIENCED_CONTINUING
                elif has_experience and not has_goals:
                    user_group = UserGroup.EXPERIENCED_CHANGING
                elif not has_experience and has_goals:
                    user_group = UserGroup.INEXPERIENCED_WITH_GOAL
                else:
                    user_group = UserGroup.INEXPERIENCED_NO_GOAL
                
                # Use the actual name from CV as username (preserve the original name as much as possible)
                # Replace spaces with underscores for database storage, but keep the original name structure
                if user_name and user_name.strip():
                    # Preserve the original name structure, just replace spaces with underscores for DB
                    # Keep letters, numbers, hyphens, underscores, periods, and apostrophes
                    username = "".join(c for c in user_name if c.isalnum() or c in [" ", "_", "-", ".", "'"])[:100].strip()
                    # Replace spaces with underscores for database storage (we'll convert back for display)
                    username = username.replace(" ", "_")
                    if not username:
                        username = user_email.split("@")[0]
                else:
                    # Fallback to email prefix if no name
                    username = user_email.split("@")[0]
                
                # Try to create user with this username
                # If it fails due to uniqueness constraint, we'll append a number
                new_user = DomainUser(
                    email=user_email,
                    username=username,  # Use the actual name (minimally cleaned)
                    user_group=user_group,
                )
                
                # Try to create - if username conflict, append number
                try:
                    created_user = self.user_repository.create(new_user)
                except Exception as e:
                    # If email or username already exists, try with appended number
                    if "unique" in str(e).lower() or "duplicate" in str(e).lower() or "constraint" in str(e).lower():
                        # Check if it's an email conflict - if so, get existing user
                        existing_by_email = self.user_repository.get_by_email(user_email)
                        if existing_by_email:
                            # Use existing user
                            created_user = existing_by_email
                        else:
                            # Username conflict, try with appended number
                            base_username = username
                            counter = 1
                            while counter < 1000:
                                username = f"{base_username}_{counter}"
                                new_user.username = username
                                try:
                                    created_user = self.user_repository.create(new_user)
                                    break
                                except Exception:
                                    counter += 1
                            if counter >= 1000:
                                # Fallback: use hash
                                username = f"{base_username}_{abs(hash(user_email)) % 10000}"
                                new_user.username = username
                                created_user = self.user_repository.create(new_user)
                    else:
                        raise
                user_id = created_user.id
            
            # Update state with user info
            state["user_id"] = user_id
            state["user_email"] = user_email
            state["user_name"] = user_name
            
            # Ensure user_id is set before proceeding
            if not user_id:
                raise ValueError("Failed to get or create user")
            
            # Get or create profile
            existing_profile = self.profile_repository.get_by_user_id(user_id)
            
            profile_data = parsed_data["profile_data"]
            profile_data["user_id"] = user_id
            profile_data["is_draft"] = True
            profile_data["is_validated"] = False
            
            # Set default career_goal_type if not provided
            if "career_goal_type" not in profile_data or not profile_data["career_goal_type"]:
                from career_navigator.domain.models.career_goal_type import CareerGoalType
                profile_data["career_goal_type"] = CareerGoalType.CONTINUE_PATH
            
            # Set default career_goals if empty
            if not profile_data.get("career_goals"):
                profile_data["career_goals"] = "Continue current career path"
            
            if state["input_type"] == "cv":
                profile_data["cv_content"] = state["cv_content"]
            else:
                profile_data["linkedin_profile_data"] = state["linkedin_data"]
            
            if state["linkedin_url"]:
                profile_data["linkedin_profile_url"] = state["linkedin_url"]
            
            from career_navigator.domain.models.profile import UserProfile
            
            if existing_profile:
                for key, value in profile_data.items():
                    setattr(existing_profile, key, value)
                profile = self.profile_repository.update(existing_profile)
            else:
                profile = self.profile_repository.create(UserProfile(**profile_data))
            
            state["profile_id"] = profile.id
            
            # Save job experiences
            job_experience_ids = []
            for job_data in parsed_data.get("job_experiences", []):
                job_data["user_id"] = user_id
                job = self.job_repository.create(
                    self._dict_to_job_experience(job_data)
                )
                if job.id:
                    job_experience_ids.append(job.id)
            
            state["job_experience_ids"] = job_experience_ids
            
            # Save courses
            course_ids = []
            for course_data in parsed_data.get("courses", []):
                course_data["user_id"] = user_id
                course = self.course_repository.create(
                    self._dict_to_course(course_data)
                )
                if course.id:
                    course_ids.append(course.id)
            
            state["course_ids"] = course_ids
            
            # Save academic records
            academic_record_ids = []
            for academic_data in parsed_data.get("academic_records", []):
                academic_data["user_id"] = user_id
                academic = self.academic_repository.create(
                    self._dict_to_academic(academic_data)
                )
                if academic.id:
                    academic_record_ids.append(academic.id)
            
            state["academic_record_ids"] = academic_record_ids
            state["is_draft"] = True
            state["error"] = None
            
        except Exception as e:
            state["error"] = f"Failed to save draft: {str(e)}"
            state["current_step"] = "error"
        
        return state

    def _wait_confirmation_node(self, state: WorkflowState) -> WorkflowState:
        """
        Wait for user confirmation (human-in-the-loop checkpoint).

        This node is marked with interrupt_before, so the workflow will pause here.
        The workflow can be resumed after human review via the API.
        """
        state["current_step"] = "waiting_confirmation"
        
        # Skip if we're generating products directly (already validated, product_type set)
        if state.get("is_validated") and state.get("product_type"):
            state["is_confirmed"] = True
            state["needs_human_review"] = False
            return state
        
        state["needs_human_review"] = True
        
        # Check if human has made a decision
        human_decision = state.get("human_decision")
        if human_decision == "approve":
            state["is_confirmed"] = True
            state["needs_human_review"] = False
        elif human_decision == "reject":
            state["error"] = "User rejected the draft data"
            state["current_step"] = "error"
        # If "edit", user will update data via CRUD APIs and call confirm again
        
        return state

    def _validate_node(self, state: WorkflowState) -> WorkflowState:
        """
        Validate profile data using guardrails.
        The GuardrailsValidationMiddleware will handle the actual validation.
        """
        if state.get("error"):
            return state
        
        trace_id = state.get("langfuse_trace_id")
        span_context = self._create_span_context("validate", trace_id)
        
        # Use span context manager - OpenTelemetry context will be propagated to LLM calls
        with span_context:
            try:
                state["current_step"] = "validating"
                
                profile = self.profile_repository.get_by_user_id(state["user_id"])
                if not profile:
                    raise ValueError(f"Profile not found for user {state['user_id']}")
                
                job_experiences = self.job_repository.get_by_user_id(state["user_id"])
                courses = self.course_repository.get_by_user_id(state["user_id"])
                academic_records = self.academic_repository.get_by_user_id(state["user_id"])
                
                # Prepare validation data for middleware
                validation_data = {
                    "profile": profile.model_dump(),
                    "job_experiences": [j.model_dump() for j in job_experiences],
                    "courses": [c.model_dump() for c in courses],
                    "academic_records": [a.model_dump() for a in academic_records],
                }
                
                # Guardrails validation using LLM
                prompt = GUARDRAIL_VALIDATION_PROMPT.format(
                    profile_data=json.dumps(validation_data, indent=2, default=str)
                )
                
                response = self.llm.generate(prompt, trace_id=trace_id)
                response = self._extract_json(response)
                validation_report = json.loads(response)
                
                state["validation_report"] = validation_report
                state["is_validated"] = validation_report.get("is_valid", False)
                
                # Update profile validation status
                profile.is_validated = state["is_validated"]
                self.profile_repository.update(profile)
                
                state["error"] = None
                
                # Set span attributes for success
                from opentelemetry import trace
                span = trace.get_current_span()
                if span and span.is_recording():
                    span.set_attribute("status", "success")
                    span.set_attribute("is_valid", str(state["is_validated"]))
                
            except Exception as e:
                state["error"] = f"Validation failed: {str(e)}"
                state["current_step"] = "error"
                # Set span attributes for error
                from opentelemetry import trace
                span = trace.get_current_span()
                if span and span.is_recording():
                    span.set_attribute("status", "error")
                    span.set_attribute("error", str(e))
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
        
        return state

    def _generate_cv_node(self, state: WorkflowState) -> WorkflowState:
        """Generate CV using LLM."""
        if state["error"]:
            return state
        
        trace_id = state.get("langfuse_trace_id")
        span_context = self._create_span_context("generate_cv", trace_id, {"product_type": "cv"})
        
        # Use span context manager - OpenTelemetry context will be propagated to LLM calls
        with span_context:
            try:
                state["current_step"] = "generating_cv"
                
                profile = self.profile_repository.get_by_user_id(state["user_id"])
                if not profile:
                    raise ValueError(f"Profile not found for user {state['user_id']}")
                
                job_experiences = self.job_repository.get_by_user_id(state["user_id"])
                courses = self.course_repository.get_by_user_id(state["user_id"])
                academic_records = self.academic_repository.get_by_user_id(state["user_id"])
                
                # Format data for CV generation
                job_experiences_text = self._format_job_experiences([j.model_dump() for j in job_experiences])
                academic_records_text = self._format_academic_records([a.model_dump() for a in academic_records])
                courses_text = self._format_courses([c.model_dump() for c in courses])
                skills = self._extract_skills([j.model_dump() for j in job_experiences], [c.model_dump() for c in courses])
                languages_text = self._format_languages(profile.languages or [])
                
                prompt = CV_GENERATION_PROMPT.format(
                    career_goals=profile.career_goals or "Not specified",
                    current_location=profile.current_location or "Not specified",
                    desired_job_locations=", ".join(profile.desired_job_locations or []),
                    job_experiences=job_experiences_text,
                    academic_records=academic_records_text,
                    courses=courses_text,
                    skills=", ".join(skills),
                    languages=languages_text,
                    additional_info=profile.additional_info or "",
                )
                
                cv_content = self.llm.generate(prompt, trace_id=trace_id)
                state["generated_cv"] = cv_content.strip()
                state["error"] = None
                
                # Set span attributes for success
                from opentelemetry import trace
                span = trace.get_current_span()
                if span and span.is_recording():
                    span.set_attribute("status", "success")
                    span.set_attribute("has_content", str(bool(cv_content)))
                
            except Exception as e:
                state["error"] = f"CV generation failed: {str(e)}"
                state["current_step"] = "error"
                # Set span attributes for error
                from opentelemetry import trace
                span = trace.get_current_span()
                if span and span.is_recording():
                    span.set_attribute("status", "error")
                    span.set_attribute("error", str(e))
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
        
        return state
    
    def _generate_career_path_node(self, state: WorkflowState) -> WorkflowState:
        """Generate career path suggestions."""
        if state.get("error"):
            return state
        
        try:
            state["current_step"] = "generating_career_path"
            
            profile = self.profile_repository.get_by_user_id(state["user_id"])
            if not profile:
                raise ValueError(f"Profile not found for user {state['user_id']}")
            
            user = self.user_repository.get_by_id(state["user_id"])
            if not user:
                raise ValueError(f"User not found: {state['user_id']}")
            
            job_experiences = self.job_repository.get_by_user_id(state["user_id"])
            courses = self.course_repository.get_by_user_id(state["user_id"])
            academic_records = self.academic_repository.get_by_user_id(state["user_id"])
            
            # Prepare profile data with normalized career_goal_type
            profile_dict = self._normalize_career_goal_type(profile.model_dump())
            
            career_path = self.career_planning_service.generate_career_path(
                profile_data=profile_dict,
                job_experiences=[j.model_dump() for j in job_experiences],
                academic_records=[a.model_dump() for a in academic_records],
                courses=[c.model_dump() for c in courses],
                user_group=user.user_group.value,
            )
            
            state["generated_career_path"] = career_path
            state["error"] = None
            
        except Exception as e:
            state["error"] = f"Career path generation failed: {str(e)}"
            state["current_step"] = "error"
        
        return state
    
    def _generate_career_plan_1y_node(self, state: WorkflowState) -> WorkflowState:
        """Generate 1-year career plan."""
        if state.get("error"):
            return state
        
        try:
            state["current_step"] = "generating_career_plan_1y"
            
            profile = self.profile_repository.get_by_user_id(state["user_id"])
            if not profile:
                raise ValueError(f"Profile not found for user {state['user_id']}")
            
            user = self.user_repository.get_by_id(state["user_id"])
            if not user:
                raise ValueError(f"User not found: {state['user_id']}")
            
            job_experiences = self.job_repository.get_by_user_id(state["user_id"])
            courses = self.course_repository.get_by_user_id(state["user_id"])
            
            # Prepare profile data with normalized career_goal_type
            profile_dict = self._normalize_career_goal_type(profile.model_dump())
            
            career_plan = self.career_planning_service.generate_career_plan_1y(
                profile_data=profile_dict,
                job_experiences=[j.model_dump() for j in job_experiences],
                courses=[c.model_dump() for c in courses],
                user_group=user.user_group.value,
            )
            
            state["generated_career_plan_1y"] = career_plan
            state["error"] = None
            
        except Exception as e:
            state["error"] = f"1-year career plan generation failed: {str(e)}"
            state["current_step"] = "error"
        
        return state
    
    def _generate_career_plan_3y_node(self, state: WorkflowState) -> WorkflowState:
        """Generate 3-year career plan."""
        if state.get("error"):
            return state
        
        try:
            state["current_step"] = "generating_career_plan_3y"
            
            profile = self.profile_repository.get_by_user_id(state["user_id"])
            if not profile:
                raise ValueError(f"Profile not found for user {state['user_id']}")
            
            user = self.user_repository.get_by_id(state["user_id"])
            if not user:
                raise ValueError(f"User not found: {state['user_id']}")
            
            job_experiences = self.job_repository.get_by_user_id(state["user_id"])
            courses = self.course_repository.get_by_user_id(state["user_id"])
            
            # Prepare profile data with normalized career_goal_type
            profile_dict = self._normalize_career_goal_type(profile.model_dump())
            
            career_plan = self.career_planning_service.generate_career_plan_3y(
                profile_data=profile_dict,
                job_experiences=[j.model_dump() for j in job_experiences],
                courses=[c.model_dump() for c in courses],
                user_group=user.user_group.value,
            )
            
            state["generated_career_plan_3y"] = career_plan
            state["error"] = None
            
        except Exception as e:
            state["error"] = f"3-year career plan generation failed: {str(e)}"
            state["current_step"] = "error"
        
        return state
    
    def _generate_career_plan_5y_node(self, state: WorkflowState) -> WorkflowState:
        """Generate 5+ year career plan."""
        if state.get("error"):
            return state
        
        try:
            state["current_step"] = "generating_career_plan_5y"
            
            profile = self.profile_repository.get_by_user_id(state["user_id"])
            if not profile:
                raise ValueError(f"Profile not found for user {state['user_id']}")
            
            user = self.user_repository.get_by_id(state["user_id"])
            if not user:
                raise ValueError(f"User not found: {state['user_id']}")
            
            job_experiences = self.job_repository.get_by_user_id(state["user_id"])
            courses = self.course_repository.get_by_user_id(state["user_id"])
            
            # Prepare profile data with normalized career_goal_type
            profile_dict = self._normalize_career_goal_type(profile.model_dump())
            
            career_plan = self.career_planning_service.generate_career_plan_5y(
                profile_data=profile_dict,
                job_experiences=[j.model_dump() for j in job_experiences],
                courses=[c.model_dump() for c in courses],
                user_group=user.user_group.value,
            )
            
            state["generated_career_plan_5y"] = career_plan
            state["error"] = None
            
        except Exception as e:
            state["error"] = f"5-year career plan generation failed: {str(e)}"
            state["current_step"] = "error"
        
        return state
    
    def _generate_linkedin_export_node(self, state: WorkflowState) -> WorkflowState:
        """Generate LinkedIn export optimization."""
        if state.get("error"):
            return state
        
        trace_id = state.get("langfuse_trace_id")
        span_context = self._create_span_context("generate_linkedin_export", trace_id, {"product_type": "linkedin_export"})
        
        # Use span context manager - OpenTelemetry context will be propagated to LLM calls
        with span_context:
            try:
                state["current_step"] = "generating_linkedin_export"
                
                profile = self.profile_repository.get_by_user_id(state["user_id"])
                if not profile:
                    raise ValueError(f"Profile not found for user {state['user_id']}")
                
                job_experiences = self.job_repository.get_by_user_id(state["user_id"])
                courses = self.course_repository.get_by_user_id(state["user_id"])
                academic_records = self.academic_repository.get_by_user_id(state["user_id"])
                
                # Determine current role
                current_role = "Not specified"
                if job_experiences:
                    current_job = job_experiences[0]
                    current_role = f"{current_job.position} at {current_job.company_name}"
                
                # Format data
                job_experiences_text = self._format_job_experiences([j.model_dump() for j in job_experiences])
                academic_records_text = self._format_academic_records([a.model_dump() for a in academic_records])
                skills = self._extract_skills([j.model_dump() for j in job_experiences], [c.model_dump() for c in courses])
                languages_text = self._format_languages(profile.languages or [])
                
                prompt = LINKEDIN_EXPORT_PROMPT.format(
                    career_goals=profile.career_goals or "Not specified",
                    current_role=current_role,
                    current_location=profile.current_location or "Not specified",
                    skills=", ".join(skills),
                    job_experiences=job_experiences_text,
                    academic_records=academic_records_text,
                    languages=languages_text,
                )
                
                response = self.llm.generate(prompt, trace_id=trace_id)
                response = self._extract_json(response)
                linkedin_export = json.loads(response)
                
                state["generated_linkedin_export"] = linkedin_export
                state["error"] = None
                
                # Set span attributes for success
                from opentelemetry import trace
                span = trace.get_current_span()
                if span and span.is_recording():
                    span.set_attribute("status", "success")
                    span.set_attribute("has_content", str(bool(linkedin_export)))
                
            except Exception as e:
                state["error"] = f"LinkedIn export generation failed: {str(e)}"
                state["current_step"] = "error"
                # Set span attributes for error
                from opentelemetry import trace
                span = trace.get_current_span()
                if span and span.is_recording():
                    span.set_attribute("status", "error")
                    span.set_attribute("error", str(e))
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
        
        return state

    def _save_product_node(self, state: WorkflowState) -> WorkflowState:
        """
        Save generated product.
        For direct product generation (when human_decision="approve" is set), auto-save.
        Otherwise, this acts as a checkpoint for human review.
        """
        if state.get("error"):
            return state
        
        try:
            state["current_step"] = "saving_product"
            
            # Check if human has approved (for direct product generation)
            human_decision = state.get("human_decision")
            if human_decision != "approve":
                # Wait for approval - set flag for human review
                state["needs_human_review"] = True
                return state
            
            # Auto-approve: proceed with saving
            state["needs_human_review"] = False
            
            from career_navigator.domain.models.product import GeneratedProduct
            
            # Determine product type and content
            # Map workflow product type strings to ProductType enum values
            product_type_str = state.get("product_type") or "cv"
            product_type_map: dict[str, ProductType] = {
                "cv": ProductType.CV,
                "career_path": ProductType.POSSIBLE_JOBS,  # career_path maps to POSSIBLE_JOBS
                "career_plan_1y": ProductType.CAREER_PLAN_1Y,
                "career_plan_3y": ProductType.CAREER_PLAN_3Y,
                "career_plan_5y": ProductType.CAREER_PLAN_5Y,
                "linkedin_export": ProductType.LINKEDIN_EXPORT,
            }
            product_type = product_type_map.get(product_type_str, ProductType.CV)
            
            content: dict[str, Any] = {}
            if product_type == ProductType.CV:
                cv_content = state.get("generated_cv")
                if cv_content:
                    content = {"cv_content": cv_content}
            elif product_type == ProductType.POSSIBLE_JOBS:
                career_path = state.get("generated_career_path")
                if career_path:
                    content = dict(career_path) if isinstance(career_path, dict) else {}
            elif product_type == ProductType.CAREER_PLAN_1Y:
                plan_1y = state.get("generated_career_plan_1y")
                if plan_1y:
                    content = dict(plan_1y) if isinstance(plan_1y, dict) else {}
            elif product_type == ProductType.CAREER_PLAN_3Y:
                plan_3y = state.get("generated_career_plan_3y")
                if plan_3y:
                    content = dict(plan_3y) if isinstance(plan_3y, dict) else {}
            elif product_type == ProductType.CAREER_PLAN_5Y:
                plan_5y = state.get("generated_career_plan_5y")
                if plan_5y:
                    content = dict(plan_5y) if isinstance(plan_5y, dict) else {}
            elif product_type == ProductType.LINKEDIN_EXPORT:
                linkedin_export = state.get("generated_linkedin_export")
                if linkedin_export:
                    content = dict(linkedin_export) if isinstance(linkedin_export, dict) else {}
            
            user_id = state.get("user_id")
            if not user_id:
                raise ValueError("User ID is required to save product")
            
            product = GeneratedProduct(
                user_id=user_id,
                product_type=product_type,
                content=content,
                is_active=True,
            )
            
            created_product = self.product_repository.create(product)
            state["product_id"] = created_product.id
            state["needs_human_review"] = False
            state["error"] = None
            
        except Exception as e:
            state["error"] = f"Failed to save product: {str(e)}"
            state["current_step"] = "error"
        
        return state

    def _check_validation_node(self, state: WorkflowState) -> WorkflowState:
        """Check validation results and decide next step."""
        state["current_step"] = "checking_validation"
        return state

    def _error_handler_node(self, state: WorkflowState) -> WorkflowState:
        """Handle errors in the workflow."""
        state["current_step"] = "error"
        return state

    def _should_validate_or_skip_to_product(self, state: WorkflowState) -> Literal["validate", "skip_to_product", "skip"]:
        """Conditional: Should we validate, skip to product generation, or skip?"""
        if state.get("error"):
            return "skip"
        
        # Skip validation and go directly to product generation if already validated and product_type is set
        if state.get("is_validated") and state.get("product_type"):
            return "skip_to_product"
        
        if state.get("is_confirmed"):
            return "validate"
        return "skip"
    
    def _should_validate(self, state: WorkflowState) -> Literal["validate", "skip"]:
        """Conditional: Should we validate?"""
        if state.get("error"):
            return "skip"
        
        if state.get("is_confirmed"):
            return "validate"
        return "skip"

    def _should_generate_product(self, state: WorkflowState) -> Literal["generate", "retry", "end"]:
        """Conditional: Should we generate product or retry?"""
        if state.get("error"):
            return "end"
        
        if state.get("is_validated"):
            return "generate"
        
        # If validation failed but not critical, allow retry
        validation_report = state.get("validation_report")
        if validation_report:
            errors = validation_report.get("errors", [])
            critical_errors = [e for e in errors if e.get("severity") == "critical"]
            
            if critical_errors:
                return "retry"  # User needs to fix critical issues
        
        return "end"
    
    def _route_to_product_generator(self, state: WorkflowState) -> Literal["cv", "career_path", "career_plan_1y", "career_plan_3y", "career_plan_5y", "linkedin_export", "end"]:
        """Route to the appropriate product generator based on product_type."""
        product_type = state.get("product_type")
        
        if not product_type:
            return "end"
        
        product_type_map: dict[str, Literal["cv", "career_path", "career_plan_1y", "career_plan_3y", "career_plan_5y", "linkedin_export", "end"]] = {
            "cv": "cv",
            "career_path": "career_path",
            "career_plan_1y": "career_plan_1y",
            "career_plan_3y": "career_plan_3y",
            "career_plan_5y": "career_plan_5y",
            "linkedin_export": "linkedin_export",
        }
        
        result = product_type_map.get(product_type, "end")
        return result
    
    def _select_product_type_node(self, state: WorkflowState) -> WorkflowState:
        """Select product type node - passes through to routing."""
        state["current_step"] = "selecting_product_type"
        return state

    # Helper methods
    def _normalize_career_goal_type(self, profile_dict: dict) -> dict:
        """Normalize career_goal_type to string value."""
        career_goal_type = profile_dict.get("career_goal_type")
        if isinstance(career_goal_type, dict):
            profile_dict["career_goal_type"] = career_goal_type.get("value", "continue_path")
        elif hasattr(career_goal_type, "value"):
            profile_dict["career_goal_type"] = career_goal_type.value
        elif not career_goal_type:
            profile_dict["career_goal_type"] = "continue_path"
        return profile_dict
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from text, handling markdown code blocks and extra text."""
        text = text.strip()
        
        # Remove markdown code blocks
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # Try to find JSON object boundaries (handle extra text before/after)
        # Look for first { and last matching } - handle nested objects
        first_brace = text.find('{')
        if first_brace == -1:
            # No JSON object found, return as-is
            return text
        
        # Find matching closing brace (handle nested objects)
        brace_count = 0
        last_brace = -1
        for i in range(first_brace, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    last_brace = i
                    break
        
        if last_brace == -1 or last_brace <= first_brace:
            # Invalid JSON structure, return as-is
            return text
        
        # Extract just the JSON object
        json_str = text[first_brace:last_brace + 1]
        return json_str.strip()

    def _structure_parsed_data(self, parsed_data: dict) -> dict:
        """Structure parsed data into domain models format."""
        personal_info = parsed_data.get("personal_info", {})
        
        # Extract user info for user creation
        user_email = personal_info.get("email")
        user_name = personal_info.get("name")
        
        profile_data = {
            "career_goals": parsed_data.get("career_goals"),
            "short_term_goals": parsed_data.get("short_term_goals"),
            "long_term_goals": parsed_data.get("long_term_goals"),
            "life_profile": parsed_data.get("life_profile"),
            "age": personal_info.get("age"),
            "birth_country": personal_info.get("birth_country"),
            "birth_city": personal_info.get("birth_city"),
            "current_location": personal_info.get("current_location"),
            "languages": personal_info.get("languages", []),
            "culture": personal_info.get("culture"),
            "hobbies": parsed_data.get("hobbies", []),
            "additional_info": parsed_data.get("additional_info"),
        }
        
        # Store user info in parsed_data for later use
        parsed_data["user_email"] = user_email
        parsed_data["user_name"] = user_name

        job_experiences = []
        for job in parsed_data.get("job_experiences", []):
            job_experiences.append({
                "company_name": job.get("company_name"),
                "position": job.get("position"),
                "description": job.get("description"),
                "start_date": self._parse_date(job.get("start_date")),
                "end_date": self._parse_date(job.get("end_date")) if job.get("end_date") else None,
                "is_current": job.get("is_current", False),
                "location": job.get("location"),
                "achievements": job.get("achievements", []),
                "skills_used": job.get("skills_used", []),
            })

        courses = []
        for course in parsed_data.get("courses", []):
            courses.append({
                "course_name": course.get("course_name"),
                "institution": course.get("institution"),
                "provider": course.get("provider"),
                "description": course.get("description"),
                "completion_date": self._parse_date(course.get("completion_date")) if course.get("completion_date") else None,
                "certificate_url": course.get("certificate_url"),
                "skills_learned": course.get("skills_learned", []),
                "duration_hours": course.get("duration_hours"),
            })

        academic_records = []
        for academic in parsed_data.get("academic_records", []):
            academic_records.append({
                "institution_name": academic.get("institution_name"),
                "degree": academic.get("degree"),
                "field_of_study": academic.get("field_of_study"),
                "start_date": self._parse_date(academic.get("start_date")) if academic.get("start_date") else None,
                "end_date": self._parse_date(academic.get("end_date")) if academic.get("end_date") else None,
                "gpa": academic.get("gpa"),
                "honors": academic.get("honors"),
                "description": academic.get("description"),
                "location": academic.get("location"),
            })

        return {
            "profile_data": profile_data,
            "job_experiences": job_experiences,
            "courses": courses,
            "academic_records": academic_records,
            # Include user info so it's available in save_draft_node
            "user_email": user_email,
            "user_name": user_name,
        }

    def _parse_date(self, date_str: str | None) -> date | None:
        """Parse date string to date object."""
        if not date_str:
            return None
        try:
            parts = date_str.split("-")
            if len(parts) == 3:
                return date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, AttributeError):
            pass
        return None

    def _dict_to_job_experience(self, data: dict):
        from career_navigator.domain.models.job_experience import JobExperience
        return JobExperience(**data)

    def _dict_to_course(self, data: dict):
        from career_navigator.domain.models.course import Course
        return Course(**data)

    def _dict_to_academic(self, data: dict):
        from career_navigator.domain.models.academic import AcademicRecord
        return AcademicRecord(**data)

    def _format_job_experiences(self, job_experiences: list[dict]) -> str:
        if not job_experiences:
            return "No job experience provided."
        formatted = []
        for job in job_experiences:
            job_text = f"Position: {job.get('position', 'N/A')}\n"
            job_text += f"Company: {job.get('company_name', 'N/A')}\n"
            job_text += f"Period: {job.get('start_date')} to {job.get('end_date') or 'Present'}\n"
            if job.get("description"):
                job_text += f"Description: {job.get('description')}\n"
            if job.get("achievements"):
                job_text += f"Achievements: {', '.join(job.get('achievements', []))}\n"
            if job.get("skills_used"):
                job_text += f"Skills: {', '.join(job.get('skills_used', []))}\n"
            formatted.append(job_text)
        return "\n---\n".join(formatted)

    def _format_academic_records(self, academic_records: list[dict]) -> str:
        if not academic_records:
            return "No academic records provided."
        formatted = []
        for academic in academic_records:
            academic_text = f"Institution: {academic.get('institution_name', 'N/A')}\n"
            if academic.get("degree"):
                academic_text += f"Degree: {academic.get('degree')}\n"
            if academic.get("field_of_study"):
                academic_text += f"Field: {academic.get('field_of_study')}\n"
            if academic.get("gpa"):
                academic_text += f"GPA: {academic.get('gpa')}\n"
            formatted.append(academic_text)
        return "\n---\n".join(formatted)

    def _format_courses(self, courses: list[dict]) -> str:
        if not courses:
            return "No courses provided."
        formatted = []
        for course in courses:
            course_text = f"Course: {course.get('course_name', 'N/A')}\n"
            if course.get("provider"):
                course_text += f"Provider: {course.get('provider')}\n"
            if course.get("skills_learned"):
                course_text += f"Skills: {', '.join(course.get('skills_learned', []))}\n"
            formatted.append(course_text)
        return "\n---\n".join(formatted)

    def _extract_skills(self, job_experiences: list[dict], courses: list[dict]) -> list[str]:
        skills = set()
        for job in job_experiences:
            skills.update(job.get("skills_used", []))
        for course in courses:
            skills.update(course.get("skills_learned", []))
        return sorted(list(skills))

    def _format_languages(self, languages: list[dict]) -> str:
        if not languages:
            return "Not specified"
        formatted = []
        for lang in languages:
            lang_text = f"{lang.get('name', 'N/A')} ({lang.get('proficiency', 'N/A')})"
            formatted.append(lang_text)
        return ", ".join(formatted)

    def run(self, initial_state: dict, config: dict | None = None, trace_id: str | None = None) -> dict:
        """
        Run the workflow graph with initial state.
        
        Args:
            initial_state: Initial state dictionary
            config: Optional LangGraph config (for checkpointer thread_id, etc.)
            trace_id: Optional Langfuse trace ID for unified tracing
            
        Returns:
            Final state dictionary
        """
        user_id = initial_state.get("user_id")
        trace_id = trace_id or initial_state.get("langfuse_trace_id")
        
        # If we have a user_id and no trace_id, try to get it from stored trace_ids
        if user_id and not trace_id:
            trace_id = self._user_trace_ids.get(user_id)
        
        # Store trace_id for use in nodes
        if trace_id:
            self._current_trace_id = trace_id
        
        # Store trace_id by user_id for later retrieval (e.g., during validation)
        if user_id and trace_id:
            self._user_trace_ids[user_id] = trace_id
        
        state = WorkflowState(
            user_id=user_id,
            input_type=initial_state["input_type"],
            cv_content=initial_state.get("cv_content"),
            linkedin_data=initial_state.get("linkedin_data"),
            linkedin_url=initial_state.get("linkedin_url"),
            user_email=initial_state.get("user_email"),
            user_name=initial_state.get("user_name"),
            user_group=initial_state.get("user_group"),
            product_type=initial_state.get("product_type"),
            parsed_data=None,
            profile_id=None,
            job_experience_ids=[],
            course_ids=[],
            academic_record_ids=[],
            is_draft=True,
            is_confirmed=initial_state.get("is_confirmed", False),
            is_validated=initial_state.get("is_validated", False),
            validation_report=None,
            generated_cv=None,
            generated_career_path=None,
            generated_career_plan_1y=None,
            generated_career_plan_3y=None,
            generated_career_plan_5y=None,
            generated_linkedin_export=None,
            product_id=None,
            needs_human_review=False,
            human_decision=initial_state.get("human_decision"),
            langfuse_trace_id=trace_id,
            error=None,
            current_step="start",
        )
        
        # Create config for checkpointer if not provided
        if config is None:
            # Use profile_id or a temporary ID for thread_id
            thread_id = f"user_{user_id}" if user_id else f"temp_{hash(str(initial_state.get('cv_content', initial_state.get('linkedin_data', ''))[:50]))}"
            config = {
                "configurable": {
                    "thread_id": thread_id,
                }
            }
        
        # Run the graph with checkpointer support
        # Use stream() to handle interrupts properly
        try:
            final_state = self.graph.invoke(state, config=config)
            return dict(final_state)
        except Exception as e:
            # If interrupted, return current state
            return {
                **dict(state),
                "error": f"Workflow interrupted: {str(e)}",
                "needs_human_review": True,
            }
    
    def get_state(self, thread_id: str) -> dict | None:
        """Get current workflow state from checkpointer."""
        # Note: MemorySaver checkpointer API is complex, so for now we rely on
        # the _user_trace_ids dict for trace_id retrieval.
        # This method can be enhanced later to properly access checkpointer state.
        return None
    
    def resume_workflow(self, thread_id: str, human_decision: str, config: dict | None = None) -> dict:
        """
        Resume workflow from checkpoint after human decision.
        
        Args:
            thread_id: Thread ID for the workflow
            human_decision: "approve", "edit", or "reject"
            config: Optional LangGraph config
            
        Returns:
            Updated state dictionary
        """
        if config is None:
            config = {"configurable": {"thread_id": thread_id}}
        
        # Get current state
        # Update with human decision
        # Continue workflow
        # This would use graph.stream() or graph.invoke() with updated state
        # For now, return empty dict - full implementation requires checkpoint API access
        return {}
    
    def get_graph_image(self, format: str = "png") -> bytes:
        """
        Generate a visual representation of the workflow graph using LangGraph's built-in visualization.
        
        Uses LangGraph's native methods:
        - draw_mermaid_png() for PNG format
        - draw_mermaid() + Mermaid API for SVG
        - draw_png() as fallback
        
        Args:
            format: Image format ("png", "svg", or "jpg")
            
        Returns:
            Image bytes
        """
        try:
            # Get the graph structure from LangGraph
            graph_structure = self.graph.get_graph()
            
            # Use LangGraph's native PNG visualization
            if format.lower() == "png":
                try:
                    # Try draw_mermaid_png first (most reliable)
                    png_bytes = graph_structure.draw_mermaid_png()
                    if png_bytes:
                        return png_bytes
                except Exception:
                    try:
                        # Fallback to draw_png
                        png_bytes = graph_structure.draw_png()
                        if png_bytes:
                            return png_bytes
                    except Exception:
                        pass
            
            # For SVG format, get Mermaid and render via API
            elif format.lower() == "svg":
                try:
                    mermaid_diagram = graph_structure.draw_mermaid()
                    if mermaid_diagram:
                        return self._create_graph_image_from_mermaid(mermaid_diagram, format)
                except Exception:
                    pass
            
            # For JPG format, get PNG and convert
            elif format.lower() in ["jpg", "jpeg"]:
                try:
                    # Get PNG from LangGraph
                    png_bytes = graph_structure.draw_mermaid_png()
                    if png_bytes:
                        # Convert PNG to JPG
                        from PIL import Image
                        import io
                        from io import BytesIO
                        
                        img = Image.open(BytesIO(png_bytes))
                        jpg_bytes = io.BytesIO()
                        img.convert("RGB").save(jpg_bytes, format="JPEG", quality=95)
                        return jpg_bytes.getvalue()
                except Exception:
                    try:
                        # Fallback: get Mermaid and render as PNG then convert
                        mermaid_diagram = graph_structure.draw_mermaid()
                        if mermaid_diagram:
                            png_bytes = self._create_graph_image_from_mermaid(mermaid_diagram, "png")
                            if png_bytes:
                                from PIL import Image
                                import io
                                from io import BytesIO
                                
                                img = Image.open(BytesIO(png_bytes))
                                jpg_bytes = io.BytesIO()
                                img.convert("RGB").save(jpg_bytes, format="JPEG", quality=95)
                                return jpg_bytes.getvalue()
                    except Exception:
                        pass
            
            # Fallback: create a simple visual representation
            return self._create_simple_graph_image(format)
        except Exception as e:
            # Ultimate fallback: return a simple text representation
            return self._create_text_graph_image(format)
    
    def _create_graph_image_from_mermaid(self, mermaid_diagram: str, format: str) -> bytes:
        """
        Create image from Mermaid diagram using Mermaid.ink API (free public service).
        
        Args:
            mermaid_diagram: Mermaid diagram syntax string
            format: Image format ("png", "svg", or "jpg")
            
        Returns:
            Image bytes
        """
        try:
            import requests  # type: ignore
            import base64
            from io import BytesIO
            
            # Encode the Mermaid diagram (base64url encoding)
            encoded_diagram = base64.urlsafe_b64encode(mermaid_diagram.encode()).decode()
            
            # For PNG format
            if format.lower() == "png":
                api_url = f"https://mermaid.ink/img/{encoded_diagram}"
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    return response.content
            
            # For SVG format
            elif format.lower() == "svg":
                api_url = f"https://mermaid.ink/svg/{encoded_diagram}"
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    return response.content
            
            # For JPG format, get PNG and convert
            elif format.lower() in ["jpg", "jpeg"]:
                api_url = f"https://mermaid.ink/img/{encoded_diagram}"
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    from PIL import Image
                    import io
                    
                    img = Image.open(BytesIO(response.content))
                    jpg_bytes = io.BytesIO()
                    img.convert("RGB").save(jpg_bytes, format="JPEG", quality=95)
                    return jpg_bytes.getvalue()
                    
        except Exception as e:
            # If Mermaid API fails, fall back to simple visualization
            pass
        
        # Fallback: create a simple visual representation
        return self._create_simple_graph_image(format)
    
    def _create_simple_graph_image(self, format: str) -> bytes:
        """Create a simple visual representation of the graph."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # Create image
            width, height = 2400, 1600
            img = Image.new("RGB", (width, height), "white")
            draw = ImageDraw.Draw(img)
            
            # Try to load a font, fallback to default if not available
            try:
                font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
                font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
                font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Define nodes and their positions
            nodes = {
                "parse": (200, 200),
                "save_draft": (200, 400),
                "wait_confirmation": (200, 600),
                "validate": (200, 800),
                "check_validation": (200, 1000),
                "select_product_type": (600, 1000),
                "generate_cv": (1000, 800),
                "generate_career_path": (1000, 1000),
                "generate_career_plan_1y": (1000, 1200),
                "generate_career_plan_3y": (1000, 1400),
                "generate_career_plan_5y": (1400, 1200),
                "generate_linkedin_export": (1400, 1000),
                "save_product": (1800, 1000),
                "END": (2000, 1000),
            }
            
            # Draw nodes
            node_width, node_height = 150, 60
            for node_name, (x, y) in nodes.items():
                # Draw rectangle
                draw.rectangle(
                    [x - node_width//2, y - node_height//2, x + node_width//2, y + node_height//2],
                    fill="lightblue" if node_name in ["wait_confirmation", "save_product"] else "lightgreen",
                    outline="black",
                    width=2
                )
                # Draw text
                text_bbox = draw.textbbox((0, 0), node_name, font=font_small)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                draw.text(
                    (x - text_width//2, y - text_height//2),
                    node_name.replace("_", "\n"),
                    fill="black",
                    font=font_small
                )
            
            # Draw edges
            edges = [
                ("parse", "save_draft"),
                ("save_draft", "wait_confirmation"),
                ("wait_confirmation", "validate"),
                ("validate", "check_validation"),
                ("check_validation", "select_product_type"),
                ("select_product_type", "generate_cv"),
                ("select_product_type", "generate_career_path"),
                ("select_product_type", "generate_career_plan_1y"),
                ("select_product_type", "generate_career_plan_3y"),
                ("select_product_type", "generate_career_plan_5y"),
                ("select_product_type", "generate_linkedin_export"),
                ("generate_cv", "save_product"),
                ("generate_career_path", "save_product"),
                ("generate_career_plan_1y", "save_product"),
                ("generate_career_plan_3y", "save_product"),
                ("generate_career_plan_5y", "save_product"),
                ("generate_linkedin_export", "save_product"),
                ("save_product", "END"),
            ]
            
            for start, end in edges:
                if start in nodes and end in nodes:
                    x1, y1 = nodes[start]
                    x2, y2 = nodes[end]
                    # Draw arrow
                    draw.line([x1 + node_width//2, y1, x2 - node_width//2, y2], fill="black", width=2)
            
            # Add title
            title = "Career Navigator Workflow Graph"
            title_bbox = draw.textbbox((0, 0), title, font=font_large)
            title_width = title_bbox[2] - title_bbox[0]
            draw.text((width//2 - title_width//2, 50), title, fill="black", font=font_large)
            
            # Add legend
            legend_y = 50
            draw.rectangle([50, legend_y, 100, legend_y + 30], fill="lightgreen", outline="black")
            draw.text((110, legend_y + 5), "Regular Node", fill="black", font=font_small)
            draw.rectangle([250, legend_y, 300, legend_y + 30], fill="lightblue", outline="black")
            draw.text((310, legend_y + 5), "Human-in-the-Loop", fill="black", font=font_small)
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format=format.upper())
            img_bytes.seek(0)
            return img_bytes.getvalue()
        except Exception as e:
            # Fallback to text representation
            return self._create_text_graph_image(format)
    
    def _create_text_graph_image(self, format: str) -> bytes:
        """Create a simple text-based graph representation."""
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # Create a simple text diagram
        diagram_text = """
Career Navigator Workflow Graph

parse → save_draft → wait_confirmation → validate → check_validation
                                                          ↓
                                              select_product_type
                                                          ↓
        ┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
        ↓              ↓              ↓              ↓              ↓              ↓
generate_cv  generate_career_path  generate_career_plan_1y  generate_career_plan_3y  generate_career_plan_5y  generate_linkedin_export
        └──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
                                                          ↓
                                                  save_product → END

Human-in-the-Loop Checkpoints: wait_confirmation, save_product
        """
        
        # Create image with text
        img = Image.new("RGB", (1200, 800), "white")
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        # Draw text
        y = 50
        for line in diagram_text.strip().split("\n"):
            draw.text((50, y), line, fill="black", font=font)
            y += 20
        
        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format=format.upper())
        img_bytes.seek(0)
        return img_bytes.getvalue()

