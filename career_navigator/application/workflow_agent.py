"""
LangChain Agent-based workflow with middleware for human-in-the-loop and guardrails.

This module integrates LangChain's create_agent with middleware for:
- Human-in-the-loop: Pause for human approval at key steps
- Guardrails: Validate data quality and enforce rules
"""

from typing import TypedDict, Literal, Annotated
from langchain.agents import create_agent
from langchain.agents.middleware import (
    HumanInTheLoopMiddleware,
    GuardrailsMiddleware,
    AgentMiddleware,
    AgentState,
)
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
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
)
from langchain_core.tools import tool
import json
from datetime import date


class WorkflowAgentState(TypedDict):
    """State for the workflow agent."""
    user_id: int
    input_type: Literal["cv", "linkedin"]
    cv_content: str | None
    linkedin_data: str | None
    linkedin_url: str | None
    
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
    product_id: int | None
    
    # Error handling
    error: str | None
    current_step: str


class GuardrailsValidationMiddleware(AgentMiddleware):
    """Custom middleware for guardrails validation."""
    
    def __init__(self, llm: LanguageModel):
        super().__init__()
        self.llm = llm
    
    def after_model(self, state: AgentState, runtime) -> dict | None:
        """Validate data after model calls that modify user data."""
        # Only validate at specific steps
        if state.get("current_step") != "validating":
            return None
        
        try:
            # Get validation data from state
            validation_data = state.get("validation_data")
            if not validation_data:
                return None
            
            prompt = GUARDRAIL_VALIDATION_PROMPT.format(
                profile_data=json.dumps(validation_data, indent=2, default=str)
            )
            
            response = self.llm.generate(prompt)
            response = self._extract_json(response)
            validation_report = json.loads(response)
            
            # Update state with validation results
            return {
                "validation_report": validation_report,
                "is_validated": validation_report.get("is_valid", False),
            }
        except Exception as e:
            return {
                "validation_report": {
                    "is_valid": False,
                    "errors": [{"message": f"Validation error: {str(e)}"}],
                },
                "is_validated": False,
            }
    
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


@tool
def parse_cv_tool(cv_content: str) -> str:
    """
    Parse CV content and extract structured data.
    
    Args:
        cv_content: The full CV text content
        
    Returns:
        JSON string with parsed data including profile, experiences, courses, and academic records
    """
    # This will be called by the agent with LLM
    return "Use this tool to parse CV content"


@tool
def parse_linkedin_tool(linkedin_data: str) -> str:
    """
    Parse LinkedIn profile data and extract structured data.
    
    Args:
        linkedin_data: The LinkedIn profile data (JSON or text)
        
    Returns:
        JSON string with parsed data
    """
    return "Use this tool to parse LinkedIn data"


@tool
def save_draft_tool(
    user_id: int,
    profile_data: str,
    job_experiences: str,
    courses: str,
    academic_records: str,
) -> str:
    """
    Save parsed data as draft in the database.
    
    Args:
        user_id: The user ID
        profile_data: JSON string with profile data
        job_experiences: JSON string with job experiences array
        courses: JSON string with courses array
        academic_records: JSON string with academic records array
        
    Returns:
        Success message with created IDs
    """
    return "Use this tool to save draft data"


@tool
def validate_profile_tool(user_id: int) -> str:
    """
    Validate profile data using guardrails.
    Requires human approval before proceeding.
    
    Args:
        user_id: The user ID to validate
        
    Returns:
        Validation report
    """
    return "Use this tool to validate profile data"


@tool
def generate_cv_tool(user_id: int) -> str:
    """
    Generate a professional CV from validated profile data.
    
    Args:
        user_id: The user ID
        
    Returns:
        Generated CV content
    """
    return "Use this tool to generate CV"


@tool
def save_product_tool(user_id: int, cv_content: str, product_type: str = "cv") -> str:
    """
    Save generated product (CV, career plan, etc.) to database.
    
    Args:
        user_id: The user ID
        cv_content: The generated CV content
        product_type: Type of product (cv, career_plan_1y, etc.)
        
    Returns:
        Success message with product ID
    """
    return "Use this tool to save generated product"


class WorkflowAgent:
    """LangChain Agent-based workflow with middleware."""
    
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
        
        # Create checkpointer for human-in-the-loop
        self.checkpointer = MemorySaver()
        
        # Create tools
        self.tools = [
            parse_cv_tool,
            parse_linkedin_tool,
            save_draft_tool,
            validate_profile_tool,
            generate_cv_tool,
            save_product_tool,
        ]
        
        # Create middleware
        self.middleware = [
            # Human-in-the-loop: Require approval for critical operations
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "save_draft_tool": {
                        "allowed_decisions": ["approve", "edit", "reject"],
                        "description": "Review parsed data before saving as draft",
                    },
                    "validate_profile_tool": {
                        "allowed_decisions": ["approve", "edit", "reject"],
                        "description": "Review validation results before proceeding",
                    },
                    "generate_cv_tool": {
                        "allowed_decisions": ["approve", "reject"],
                        "description": "Approve CV generation",
                    },
                    "save_product_tool": {
                        "allowed_decisions": ["approve", "reject"],
                        "description": "Review generated product before saving",
                    },
                    # Auto-approve parsing (can be reviewed after)
                    "parse_cv_tool": False,
                    "parse_linkedin_tool": False,
                }
            ),
            # Guardrails validation middleware
            GuardrailsValidationMiddleware(llm=llm),
        ]
        
        # Create the agent
        # Note: We need to convert our LanguageModel to a LangChain compatible model
        # For now, we'll create a wrapper or use the LLM directly in tool implementations
        self.agent = None  # Will be created when we have a LangChain-compatible model
    
    def create_agent_with_model(self, langchain_model):
        """Create the agent with a LangChain-compatible model."""
        self.agent = create_agent(
            model=langchain_model,
            tools=self.tools,
            middleware=self.middleware,
            checkpointer=self.checkpointer,
        )
        return self.agent

