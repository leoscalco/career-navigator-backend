import json
from typing import Dict, Any, List
from career_navigator.domain.llm import LanguageModel
from career_navigator.domain.prompts import (
    CAREER_PATH_PROMPT,
    CAREER_PLAN_1Y_PROMPT,
    CAREER_PLAN_3Y_PROMPT,
    CAREER_PLAN_5Y_PROMPT,
)
from career_navigator.domain.models.product_type import ProductType


class CareerPlanningService:
    """Service for generating career paths and career plans."""

    def __init__(self, llm: LanguageModel):
        self.llm = llm

    def generate_career_path(
        self,
        profile_data: Dict[str, Any],
        job_experiences: List[Dict[str, Any]],
        academic_records: List[Dict[str, Any]],
        courses: List[Dict[str, Any]],
        user_group: str,
    ) -> Dict[str, Any]:
        """
        Generate career path suggestions.
        
        Returns structured JSON with career path recommendations.
        """
        # Determine current role
        current_role = "Not specified"
        if job_experiences:
            current_job = job_experiences[0]
            current_role = f"{current_job.get('position', 'N/A')} at {current_job.get('company_name', 'N/A')}"
        
        # Extract skills
        skills = self._extract_skills(job_experiences, courses)
        
        # Format education
        education = self._format_education(academic_records)
        
        # Determine experience level
        experience_level = self._determine_experience_level(job_experiences)
        
        # Get career goal type, default to continue_path if not specified
        career_goal_type = profile_data.get("career_goal_type", "continue_path")
        if not career_goal_type or career_goal_type == "None":
            career_goal_type = "continue_path"
        
        # Get job search locations
        job_search_locations = profile_data.get("job_search_locations", [])
        if not job_search_locations:
            job_search_locations = profile_data.get("desired_job_locations", [])
        job_search_locations_str = ", ".join(job_search_locations) if job_search_locations else "Not specified"
        
        prompt = CAREER_PATH_PROMPT.format(
            current_role=current_role,
            career_goals=profile_data.get("career_goals", "Continue current career path"),
            career_goal_type=career_goal_type,
            skills=", ".join(skills),
            education=education,
            experience_level=experience_level,
            user_group=user_group,
            job_search_locations=job_search_locations_str,
        )
        
        try:
            response = self.llm.generate(prompt)
            response = self._extract_json(response)
            return json.loads(response)
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to generate career path: {str(e)}")

    def generate_career_plan_1y(
        self,
        profile_data: Dict[str, Any],
        job_experiences: List[Dict[str, Any]],
        courses: List[Dict[str, Any]],
        user_group: str,
    ) -> Dict[str, Any]:
        """Generate 1-year career plan."""
        current_role = "Not specified"
        if job_experiences:
            current_job = job_experiences[0]
            current_role = f"{current_job.get('position', 'N/A')} at {current_job.get('company_name', 'N/A')}"
        
        skills = self._extract_skills(job_experiences, courses)
        experience_level = self._determine_experience_level(job_experiences)
        
        # Get career goal type, default to continue_path if not specified
        career_goal_type = profile_data.get("career_goal_type", "continue_path")
        if not career_goal_type or career_goal_type == "None":
            career_goal_type = "continue_path"
        
        # Get job search locations
        job_search_locations = profile_data.get("job_search_locations", [])
        if not job_search_locations:
            job_search_locations = profile_data.get("desired_job_locations", [])
        job_search_locations_str = ", ".join(job_search_locations) if job_search_locations else "Not specified"
        
        prompt = CAREER_PLAN_1Y_PROMPT.format(
            career_goals=profile_data.get("career_goals", "Continue current career path"),
            career_goal_type=career_goal_type,
            current_role=current_role,
            skills=", ".join(skills),
            experience_level=experience_level,
            user_group=user_group,
            job_search_locations=job_search_locations_str,
        )
        
        try:
            response = self.llm.generate(prompt)
            response = self._extract_json(response)
            return json.loads(response)
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to generate 1-year career plan: {str(e)}")

    def generate_career_plan_3y(
        self,
        profile_data: Dict[str, Any],
        job_experiences: List[Dict[str, Any]],
        courses: List[Dict[str, Any]],
        user_group: str,
    ) -> Dict[str, Any]:
        """Generate 3-year career plan."""
        current_role = "Not specified"
        if job_experiences:
            current_job = job_experiences[0]
            current_role = f"{current_job.get('position', 'N/A')} at {current_job.get('company_name', 'N/A')}"
        
        skills = self._extract_skills(job_experiences, courses)
        experience_level = self._determine_experience_level(job_experiences)
        
        # Get career goal type, default to continue_path if not specified
        career_goal_type = profile_data.get("career_goal_type", "continue_path")
        if not career_goal_type or career_goal_type == "None":
            career_goal_type = "continue_path"
        
        # Get job search locations
        job_search_locations = profile_data.get("job_search_locations", [])
        if not job_search_locations:
            job_search_locations = profile_data.get("desired_job_locations", [])
        job_search_locations_str = ", ".join(job_search_locations) if job_search_locations else "Not specified"
        
        prompt = CAREER_PLAN_3Y_PROMPT.format(
            career_goals=profile_data.get("career_goals", "Continue current career path"),
            career_goal_type=career_goal_type,
            long_term_goals=profile_data.get("long_term_goals", "Not specified"),
            current_role=current_role,
            skills=", ".join(skills),
            experience_level=experience_level,
            user_group=user_group,
            job_search_locations=job_search_locations_str,
        )
        
        try:
            response = self.llm.generate(prompt)
            response = self._extract_json(response)
            return json.loads(response)
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to generate 3-year career plan: {str(e)}")

    def generate_career_plan_5y(
        self,
        profile_data: Dict[str, Any],
        job_experiences: List[Dict[str, Any]],
        courses: List[Dict[str, Any]],
        user_group: str,
    ) -> Dict[str, Any]:
        """Generate 5+ year career plan."""
        current_role = "Not specified"
        if job_experiences:
            current_job = job_experiences[0]
            current_role = f"{current_job.get('position', 'N/A')} at {current_job.get('company_name', 'N/A')}"
        
        skills = self._extract_skills(job_experiences, courses)
        experience_level = self._determine_experience_level(job_experiences)
        
        # Get career goal type, default to continue_path if not specified
        career_goal_type = profile_data.get("career_goal_type", "continue_path")
        if not career_goal_type or career_goal_type == "None":
            career_goal_type = "continue_path"
        
        # Get job search locations
        job_search_locations = profile_data.get("job_search_locations", [])
        if not job_search_locations:
            job_search_locations = profile_data.get("desired_job_locations", [])
        job_search_locations_str = ", ".join(job_search_locations) if job_search_locations else "Not specified"
        
        prompt = CAREER_PLAN_5Y_PROMPT.format(
            career_goals=profile_data.get("career_goals", "Continue current career path"),
            career_goal_type=career_goal_type,
            long_term_goals=profile_data.get("long_term_goals", "Not specified"),
            current_role=current_role,
            skills=", ".join(skills),
            experience_level=experience_level,
            user_group=user_group,
            job_search_locations=job_search_locations_str,
        )
        
        try:
            response = self.llm.generate(prompt)
            response = self._extract_json(response)
            return json.loads(response)
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to generate 5-year career plan: {str(e)}")

    def _extract_skills(self, job_experiences: List[Dict[str, Any]], courses: List[Dict[str, Any]]) -> List[str]:
        """Extract unique skills."""
        skills = set()
        for job in job_experiences:
            skills.update(job.get("skills_used", []))
        for course in courses:
            skills.update(course.get("skills_learned", []))
        return sorted(list(skills))

    def _format_education(self, academic_records: List[Dict[str, Any]]) -> str:
        """Format education information."""
        if not academic_records:
            return "Not specified"
        
        formatted = []
        for academic in academic_records:
            edu_text = f"{academic.get('degree', 'N/A')} in {academic.get('field_of_study', 'N/A')} from {academic.get('institution_name', 'N/A')}"
            formatted.append(edu_text)
        
        return "; ".join(formatted)

    def _determine_experience_level(self, job_experiences: List[Dict[str, Any]]) -> str:
        """Determine experience level based on job history."""
        if not job_experiences:
            return "Entry Level"
        
        total_years = 0
        for job in job_experiences:
            # Simple calculation (could be improved)
            if job.get("start_date") and job.get("end_date"):
                # Would need date parsing here, simplified for now
                total_years += 1  # Placeholder
        
        if total_years < 2:
            return "Entry Level"
        elif total_years < 5:
            return "Mid Level"
        elif total_years < 10:
            return "Senior Level"
        else:
            return "Expert Level"

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

