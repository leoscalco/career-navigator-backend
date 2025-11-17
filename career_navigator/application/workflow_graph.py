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
    user_id: int
    input_type: Literal["cv", "linkedin"]
    cv_content: str | None
    linkedin_data: str | None
    linkedin_url: str | None
    
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
        
        # Build the graph
        self.graph = self._build_graph()

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
        
        # After confirmation, validate
        workflow.add_conditional_edges(
            "wait_confirmation",
            self._should_validate,
            {
                "validate": "validate",
                "skip": END,
            }
        )
        
        # Validate → Check validation result (GUARDRAILS VALIDATION)
        workflow.add_edge("validate", "check_validation")
        
        # Check validation → Select product type or retry
        workflow.add_conditional_edges(
            "check_validation",
            self._should_generate_product,
            {
                "generate": "select_product_type",
                "retry": "wait_confirmation",  # Go back to allow user to fix issues
                "end": END,
            }
        )
        
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
        return workflow.compile(checkpointer=self.checkpointer, interrupt_before=["wait_confirmation", "save_product"])

    def _parse_node(self, state: WorkflowState) -> WorkflowState:
        """Parse CV or LinkedIn content."""
        try:
            state["current_step"] = "parsing"
            
            if state["input_type"] == "cv":
                if not state["cv_content"]:
                    raise ValueError("CV content is required")
                prompt = CV_PARSING_PROMPT.format(cv_content=state["cv_content"])
            else:  # linkedin
                if not state["linkedin_data"]:
                    raise ValueError("LinkedIn data is required")
                prompt = LINKEDIN_PARSING_PROMPT.format(linkedin_data=state["linkedin_data"])
            
            response = self.llm.generate(prompt)
            response = self._extract_json(response)
            parsed_data = json.loads(response)
            
            state["parsed_data"] = self._structure_parsed_data(parsed_data)
            state["error"] = None
            
        except Exception as e:
            state["error"] = f"Parsing failed: {str(e)}"
            state["current_step"] = "error"
        
        return state

    def _save_draft_node(self, state: WorkflowState) -> WorkflowState:
        """
        Save parsed data as draft.
        This is a checkpoint for human-in-the-loop review.
        """
        if state.get("error"):
            return state
        
        try:
            state["current_step"] = "saving_draft"
            parsed_data = state.get("parsed_data")
            if not parsed_data:
                raise ValueError("No parsed data to save")
            
            # Get or create profile
            existing_profile = self.profile_repository.get_by_user_id(state["user_id"])
            
            profile_data = parsed_data["profile_data"]
            profile_data["user_id"] = state["user_id"]
            profile_data["is_draft"] = True
            profile_data["is_validated"] = False
            
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
                job_data["user_id"] = state["user_id"]
                job = self.job_repository.create(
                    self._dict_to_job_experience(job_data)
                )
                if job.id:
                    job_experience_ids.append(job.id)
            
            state["job_experience_ids"] = job_experience_ids
            
            # Save courses
            course_ids = []
            for course_data in parsed_data.get("courses", []):
                course_data["user_id"] = state["user_id"]
                course = self.course_repository.create(
                    self._dict_to_course(course_data)
                )
                if course.id:
                    course_ids.append(course.id)
            
            state["course_ids"] = course_ids
            
            # Save academic records
            academic_record_ids = []
            for academic_data in parsed_data.get("academic_records", []):
                academic_data["user_id"] = state["user_id"]
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
            
            response = self.llm.generate(prompt)
            response = self._extract_json(response)
            validation_report = json.loads(response)
            
            state["validation_report"] = validation_report
            state["is_validated"] = validation_report.get("is_valid", False)
            
            # Update profile validation status
            profile.is_validated = state["is_validated"]
            self.profile_repository.update(profile)
            
            state["error"] = None
            
        except Exception as e:
            state["error"] = f"Validation failed: {str(e)}"
            state["current_step"] = "error"
        
        return state

    def _generate_cv_node(self, state: WorkflowState) -> WorkflowState:
        """Generate CV using LLM."""
        if state["error"]:
            return state
        
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
            
            cv_content = self.llm.generate(prompt)
            state["generated_cv"] = cv_content.strip()
            state["error"] = None
            
        except Exception as e:
            state["error"] = f"CV generation failed: {str(e)}"
            state["current_step"] = "error"
        
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
            
            career_path = self.career_planning_service.generate_career_path(
                profile_data=profile.model_dump(),
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
            
            career_plan = self.career_planning_service.generate_career_plan_1y(
                profile_data=profile.model_dump(),
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
            
            career_plan = self.career_planning_service.generate_career_plan_3y(
                profile_data=profile.model_dump(),
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
            
            career_plan = self.career_planning_service.generate_career_plan_5y(
                profile_data=profile.model_dump(),
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
            
            response = self.llm.generate(prompt)
            response = self._extract_json(response)
            linkedin_export = json.loads(response)
            
            state["generated_linkedin_export"] = linkedin_export
            state["error"] = None
            
        except Exception as e:
            state["error"] = f"LinkedIn export generation failed: {str(e)}"
            state["current_step"] = "error"
        
        return state

    def _save_product_node(self, state: WorkflowState) -> WorkflowState:
        """
        Save generated product.
        This node is marked with interrupt_before, so workflow pauses for human review.
        """
        if state.get("error"):
            return state
        
        try:
            state["current_step"] = "saving_product"
            state["needs_human_review"] = True
            
            # Check if human has approved
            human_decision = state.get("human_decision")
            if human_decision != "approve":
                # Wait for approval
                return state
            
            from career_navigator.domain.models.product import GeneratedProduct
            
            # Determine product type and content
            product_type_str = state.get("product_type", "cv")
            product_type = ProductType(product_type_str)
            
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
            
            product = GeneratedProduct(
                user_id=state["user_id"],
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

    def _should_validate(self, state: WorkflowState) -> Literal["validate", "skip"]:
        """Conditional: Should we validate?"""
        if state["error"]:
            return "skip"
        if state["is_confirmed"]:
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
    def _extract_json(self, text: str) -> str:
        """Extract JSON from text."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def _structure_parsed_data(self, parsed_data: dict) -> dict:
        """Structure parsed data into domain models format."""
        personal_info = parsed_data.get("personal_info", {})
        
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

    def run(self, initial_state: dict, config: dict | None = None) -> dict:
        """
        Run the workflow graph with initial state.
        
        Args:
            initial_state: Initial state dictionary
            config: Optional LangGraph config (for checkpointer thread_id, etc.)
            
        Returns:
            Final state dictionary
        """
        state = WorkflowState(
            user_id=initial_state["user_id"],
            input_type=initial_state["input_type"],
            cv_content=initial_state.get("cv_content"),
            linkedin_data=initial_state.get("linkedin_data"),
            linkedin_url=initial_state.get("linkedin_url"),
            product_type=initial_state.get("product_type"),
            parsed_data=None,
            profile_id=None,
            job_experience_ids=[],
            course_ids=[],
            academic_record_ids=[],
            is_draft=True,
            is_confirmed=initial_state.get("is_confirmed", False),
            is_validated=False,
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
            error=None,
            current_step="start",
        )
        
        # Create config for checkpointer if not provided
        if config is None:
            config = {
                "configurable": {
                    "thread_id": f"user_{initial_state['user_id']}",  # Unique thread per user
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
        try:
            config = {"configurable": {"thread_id": thread_id}}
            # Get the latest checkpoint
            # Note: This is a simplified version - actual implementation depends on checkpointer API
            return None
        except Exception:
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

