import json
from typing import Dict, Any, Optional
from career_navigator.domain.llm import LanguageModel
from career_navigator.domain.prompts import CV_PARSING_PROMPT, LINKEDIN_PARSING_PROMPT
from career_navigator.domain.models.profile import UserProfile
from career_navigator.domain.models.job_experience import JobExperience
from career_navigator.domain.models.course import Course
from career_navigator.domain.models.academic import AcademicRecord
from datetime import date


class ParsingService:
    """Service for parsing CV or LinkedIn data into structured format."""

    def __init__(self, llm: LanguageModel):
        self.llm = llm

    def parse_cv(self, cv_content: str) -> Dict[str, Any]:
        """
        Parse CV content and extract structured data.
        
        Returns a dictionary with:
        - profile_data: UserProfile data
        - job_experiences: List of JobExperience data
        - courses: List of Course data
        - academic_records: List of AcademicRecord data
        """
        prompt = CV_PARSING_PROMPT.format(cv_content=cv_content)
        
        try:
            response = self.llm.generate(prompt)
            # Try to extract JSON from response (might have markdown code blocks)
            response = self._extract_json(response)
            parsed_data = json.loads(response)
            
            return self._structure_parsed_data(parsed_data)
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to parse CV: {str(e)}")

    def parse_linkedin(self, linkedin_data: str) -> Dict[str, Any]:
        """
        Parse LinkedIn profile data and extract structured data.
        
        Returns a dictionary with the same structure as parse_cv.
        """
        prompt = LINKEDIN_PARSING_PROMPT.format(linkedin_data=linkedin_data)
        
        try:
            response = self.llm.generate(prompt)
            response = self._extract_json(response)
            parsed_data = json.loads(response)
            
            return self._structure_parsed_data(parsed_data)
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to parse LinkedIn data: {str(e)}")

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text, handling markdown code blocks."""
        text = text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        return text.strip()

    def _structure_parsed_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure parsed data into domain models."""
        personal_info = parsed_data.get("personal_info", {})
        
        # Build profile data
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
            "is_draft": True,  # Always draft initially
            "is_validated": False,
        }

        # Build job experiences
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

        # Build courses
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

        # Build academic records
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

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        
        try:
            # Handle YYYY-MM-DD format
            parts = date_str.split("-")
            if len(parts) == 3:
                return date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, AttributeError):
            pass
        
        return None

