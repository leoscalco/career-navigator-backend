from typing import Dict, Any, List
from career_navigator.domain.llm import LanguageModel
from career_navigator.domain.prompts import CV_GENERATION_PROMPT


class CVGenerationService:
    """Service for generating CVs from user profile data."""

    def __init__(self, llm: LanguageModel):
        self.llm = llm

    def generate_cv(
        self,
        profile_data: Dict[str, Any],
        job_experiences: List[Dict[str, Any]],
        academic_records: List[Dict[str, Any]],
        courses: List[Dict[str, Any]],
    ) -> str:
        """
        Generate a professional CV from user profile data.
        
        Returns the CV content as a string.
        """
        # Format job experiences
        job_experiences_text = self._format_job_experiences(job_experiences)
        
        # Format academic records
        academic_records_text = self._format_academic_records(academic_records)
        
        # Format courses
        courses_text = self._format_courses(courses)
        
        # Extract skills from all sources
        skills = self._extract_skills(job_experiences, courses)
        
        # Format languages
        languages_text = self._format_languages(profile_data.get("languages", []))
        
        prompt = CV_GENERATION_PROMPT.format(
            career_goals=profile_data.get("career_goals", "Not specified"),
            current_location=profile_data.get("current_location", "Not specified"),
            desired_job_locations=", ".join(profile_data.get("desired_job_locations", [])),
            job_experiences=job_experiences_text,
            academic_records=academic_records_text,
            courses=courses_text,
            skills=", ".join(skills),
            languages=languages_text,
            additional_info=profile_data.get("additional_info", ""),
        )
        
        cv_content = self.llm.generate(prompt)
        return cv_content.strip()

    def _format_job_experiences(self, job_experiences: List[Dict[str, Any]]) -> str:
        """Format job experiences for the prompt."""
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

    def _format_academic_records(self, academic_records: List[Dict[str, Any]]) -> str:
        """Format academic records for the prompt."""
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

    def _format_courses(self, courses: List[Dict[str, Any]]) -> str:
        """Format courses for the prompt."""
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

    def _extract_skills(self, job_experiences: List[Dict[str, Any]], courses: List[Dict[str, Any]]) -> List[str]:
        """Extract unique skills from job experiences and courses."""
        skills = set()
        
        for job in job_experiences:
            skills.update(job.get("skills_used", []))
        
        for course in courses:
            skills.update(course.get("skills_learned", []))
        
        return sorted(list(skills))

    def _format_languages(self, languages: List[Dict[str, str]]) -> str:
        """Format languages for the prompt."""
        if not languages:
            return "Not specified"
        
        formatted = []
        for lang in languages:
            lang_text = f"{lang.get('name', 'N/A')} ({lang.get('proficiency', 'N/A')})"
            formatted.append(lang_text)
        
        return ", ".join(formatted)

