"""
LinkedIn API client for fetching profile data.
"""

import requests
from typing import Optional, Dict, Any
from career_navigator.config import settings


class LinkedInAPIError(Exception):
    """Exception raised for LinkedIn API errors."""
    pass


class LinkedInAPIClient:
    """
    Client for interacting with LinkedIn API.
    
    Requires LinkedIn OAuth 2.0 access token for authentication.
    """
    
    BASE_URL = "https://api.linkedin.com/v2"
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize LinkedIn API client.
        
        Args:
            access_token: LinkedIn OAuth 2.0 access token.
                         If not provided, will use LINKEDIN_ACCESS_TOKEN from settings.
        """
        self.access_token = access_token or getattr(settings, "LINKEDIN_ACCESS_TOKEN", None)
        if not self.access_token:
            raise ValueError(
                "LinkedIn access token is required. "
                "Provide it via access_token parameter or set LINKEDIN_ACCESS_TOKEN in .env"
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
    
    def get_profile(self, profile_id: Optional[str] = None, profile_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Get LinkedIn profile data.
        
        Args:
            profile_id: LinkedIn profile ID or "me" for authenticated user's profile.
                       If None, defaults to "me".
                       Note: For LinkedIn API v2, you typically need the numeric ID or "me".
                       The username from URL cannot be directly used.
            profile_url: LinkedIn profile URL (for reference, not used for API call)
        
        Returns:
            Dictionary containing profile data
        
        Raises:
            LinkedInAPIError: If API request fails
        
        Note:
            LinkedIn API v2 requires either:
            - "me" for the authenticated user's own profile
            - A numeric profile ID (not the username from URL)
            To get other users' profiles, you need their numeric ID or use the People Search API.
        """
        if not profile_id:
            profile_id = "me"
        
        # Note: LinkedIn API v2 doesn't support fetching profiles by username from URL
        # You need either "me" (for authenticated user) or the numeric profile ID
        # If profile_url is provided but profile_id is not "me", we'll use "me" as default
        if profile_url and profile_id != "me" and not profile_id.isdigit():
            # If it's not a numeric ID, default to "me"
            profile_id = "me"
        
        # LinkedIn API v2 endpoints
        # Basic profile fields
        profile_fields = [
            "id",
            "firstName",
            "lastName",
            "headline",
            "location",
            "summary",
            "profilePicture(displayImage~:playableStreams)",
        ]
        
        # Email (requires r_emailaddress scope)
        email_fields = ["elements[0].handle~.emailAddress"]
        
        # Experience (requires r_fullprofile or r_workhistory scope)
        experience_fields = [
            "elements[0].companyName",
            "elements[0].title",
            "elements[0].description",
            "elements[0].locationName",
            "elements[0].timePeriod.start.year",
            "elements[0].timePeriod.start.month",
            "elements[0].timePeriod.end.year",
            "elements[0].timePeriod.end.month",
            "elements[0].timePeriod.end.day",
        ]
        
        # Education (requires r_fullprofile or r_education scope)
        education_fields = [
            "elements[0].schoolName",
            "elements[0].degreeName",
            "elements[0].fieldOfStudy",
            "elements[0].timePeriod.start.year",
            "elements[0].timePeriod.end.year",
        ]
        
        profile_data = {}
        
        try:
            # Get basic profile
            profile_url = f"{self.BASE_URL}/me"
            params = {
                "projection": f"({','.join(profile_fields)})"
            }
            
            response = requests.get(
                profile_url,
                headers=self._get_headers(),
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                profile_data.update(response.json())
            else:
                raise LinkedInAPIError(
                    f"Failed to fetch profile: {response.status_code} - {response.text}"
                )
            
            # Get email (if available)
            try:
                email_url = f"{self.BASE_URL}/emailAddress"
                email_params = {
                    "q": "members",
                    "projection": f"({','.join(email_fields)})"
                }
                email_response = requests.get(
                    email_url,
                    headers=self._get_headers(),
                    params=email_params,
                    timeout=10
                )
                if email_response.status_code == 200:
                    email_data = email_response.json()
                    if "elements" in email_data and len(email_data["elements"]) > 0:
                        profile_data["email"] = email_data["elements"][0].get("handle~", {}).get("emailAddress")
            except Exception as e:
                # Email might not be available (scope not granted)
                pass
            
            # Get work experience
            try:
                experience_url = f"{self.BASE_URL}/me/positions"
                experience_params = {
                    "projection": f"({','.join(experience_fields)})"
                }
                exp_response = requests.get(
                    experience_url,
                    headers=self._get_headers(),
                    params=experience_params,
                    timeout=10
                )
                if exp_response.status_code == 200:
                    profile_data["positions"] = exp_response.json().get("elements", [])
            except Exception as e:
                # Experience might not be available
                pass
            
            # Get education
            try:
                education_url = f"{self.BASE_URL}/me/educations"
                education_params = {
                    "projection": f"({','.join(education_fields)})"
                }
                edu_response = requests.get(
                    education_url,
                    headers=self._get_headers(),
                    params=education_params,
                    timeout=10
                )
                if edu_response.status_code == 200:
                    profile_data["educations"] = edu_response.json().get("elements", [])
            except Exception as e:
                # Education might not be available
                pass
            
            return profile_data
            
        except requests.exceptions.RequestException as e:
            raise LinkedInAPIError(f"LinkedIn API request failed: {str(e)}")
    
    def format_profile_for_parsing(self, profile_data: Dict[str, Any]) -> str:
        """
        Format LinkedIn profile data into a text format suitable for LLM parsing.
        
        Args:
            profile_data: Raw LinkedIn API response
        
        Returns:
            Formatted text string
        """
        lines = []
        
        # Basic info
        if "firstName" in profile_data:
            first_name = profile_data["firstName"].get("localized", {}).get("en_US", "")
            last_name = profile_data.get("lastName", {}).get("localized", {}).get("en_US", "")
            if first_name or last_name:
                lines.append(f"Name: {first_name} {last_name}".strip())
        
        if "headline" in profile_data:
            headline = profile_data["headline"].get("localized", {}).get("en_US", "")
            if headline:
                lines.append(f"Headline: {headline}")
        
        if "email" in profile_data:
            lines.append(f"Email: {profile_data['email']}")
        
        if "location" in profile_data:
            location = profile_data["location"].get("name", "")
            if location:
                lines.append(f"Location: {location}")
        
        if "summary" in profile_data:
            summary = profile_data["summary"].get("localized", {}).get("en_US", "")
            if summary:
                lines.append(f"\nSummary:\n{summary}")
        
        # Work experience
        if "positions" in profile_data:
            lines.append("\nWork Experience:")
            for pos in profile_data["positions"]:
                company = pos.get("companyName", "")
                title = pos.get("title", "")
                description = pos.get("description", "")
                location = pos.get("locationName", "")
                start = pos.get("timePeriod", {}).get("start", {})
                end = pos.get("timePeriod", {}).get("end", {})
                
                exp_line = f"\n- {title}"
                if company:
                    exp_line += f" at {company}"
                if location:
                    exp_line += f" ({location})"
                
                if start:
                    start_year = start.get("year", "")
                    start_month = start.get("month", "")
                    if start_year:
                        exp_line += f"\n  Period: {start_month or ''} {start_year}".strip()
                        if end:
                            end_year = end.get("year", "")
                            end_month = end.get("month", "")
                            if end_year:
                                exp_line += f" - {end_month or ''} {end_year}".strip()
                            else:
                                exp_line += " - Present"
                
                if description:
                    exp_line += f"\n  Description: {description}"
                
                lines.append(exp_line)
        
        # Education
        if "educations" in profile_data:
            lines.append("\nEducation:")
            for edu in profile_data["educations"]:
                school = edu.get("schoolName", "")
                degree = edu.get("degreeName", "")
                field = edu.get("fieldOfStudy", "")
                start = edu.get("timePeriod", {}).get("start", {})
                end = edu.get("timePeriod", {}).get("end", {})
                
                edu_line = f"\n- {school}"
                if degree:
                    edu_line += f", {degree}"
                if field:
                    edu_line += f" in {field}"
                
                if start and start.get("year"):
                    edu_line += f"\n  {start['year']}"
                    if end and end.get("year"):
                        edu_line += f" - {end['year']}"
                
                lines.append(edu_line)
        
        return "\n".join(lines)

