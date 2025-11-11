"""
Custom guardrails middleware for workflow validation.
"""

from typing import Any
from langchain.agents.middleware import AgentMiddleware, AgentState
from career_navigator.domain.llm import LanguageModel
from career_navigator.domain.prompts.guardrail import GUARDRAIL_VALIDATION_PROMPT
import json


class GuardrailsValidationMiddleware(AgentMiddleware):
    """Middleware for guardrails validation using LLM."""
    
    def __init__(self, llm: LanguageModel):
        super().__init__()
        self.llm = llm
    
    def after_model(self, state: AgentState, runtime) -> dict[str, Any] | None:
        """
        Validate data after model calls that modify user data.
        Only runs when current_step is 'validating'.
        """
        # Check if we're in validation step
        current_step = state.get("current_step", "")
        if current_step != "validating":
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
                    "warnings": [],
                    "completeness_score": 0.0,
                    "recommendations": [],
                },
                "is_validated": False,
            }
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from text, handling markdown code blocks."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

