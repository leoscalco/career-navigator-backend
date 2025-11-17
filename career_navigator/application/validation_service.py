import json
from typing import Dict, Any, List
from career_navigator.domain.llm import LanguageModel
from career_navigator.domain.prompts.guardrail import GUARDRAIL_VALIDATION_PROMPT


class ValidationService:
    """Service for validating user profile data using guardrails."""

    def __init__(self, llm: LanguageModel):
        self.llm = llm

    def validate_profile(
        self,
        profile_data: Dict[str, Any],
        job_experiences: List[Dict[str, Any]],
        courses: List[Dict[str, Any]],
        academic_records: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Validate user profile data using LLM guardrails.
        
        Returns validation report with:
        - is_valid: boolean
        - errors: list of errors
        - warnings: list of warnings
        - completeness_score: float 0-1
        - recommendations: list of recommendations
        """
        # Prepare data for validation
        validation_data = {
            "profile": profile_data,
            "job_experiences": job_experiences,
            "courses": courses,
            "academic_records": academic_records,
        }
        
        prompt = GUARDRAIL_VALIDATION_PROMPT.format(
            profile_data=json.dumps(validation_data, indent=2, default=str)
        )
        
        try:
            response = self.llm.generate(prompt)
            response = self._extract_json(response)
            validation_report = json.loads(response)
            
            return validation_report
        except (json.JSONDecodeError, KeyError) as e:
            # If LLM validation fails, return a basic validation
            return {
                "is_valid": False,
                "errors": [
                    {
                        "field": "validation_service",
                        "error_type": "invalid",
                        "message": f"Validation service error: {str(e)}",
                        "severity": "critical",
                    }
                ],
                "warnings": [],
                "completeness_score": 0.0,
                "recommendations": ["Please review the data manually"],
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

