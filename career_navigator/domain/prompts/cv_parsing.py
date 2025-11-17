CV_PARSING_PROMPT = """
You are an expert at extracting structured information from CVs and resumes.

Analyze the following CV/resume content and extract all relevant information. 
Return a JSON object with the following structure:

{{
    "personal_info": {{
        "name": <string or null>,
        "email": <string or null>,
        "age": <integer or null>,
        "birth_country": <string or null>,
        "birth_city": <string or null>,
        "current_location": <string or null>,
        "languages": [
            {{"name": <string>, "proficiency": <"Native"|"Advanced"|"Intermediate"|"Basic">}}
        ],
        "culture": <string or null>
    }},
    "career_goals": <string or null>,
    "short_term_goals": <string or null>,
    "long_term_goals": <string or null>,
    "job_experiences": [
        {{
            "company_name": <string>,
            "position": <string>,
            "description": <string or null>,
            "start_date": <"YYYY-MM-DD" format>,
            "end_date": <"YYYY-MM-DD" format or null if current>,
            "is_current": <boolean>,
            "location": <string or null>,
            "achievements": [<list of strings>],
            "skills_used": [<list of strings>]
        }}
    ],
    "courses": [
        {{
            "course_name": <string>,
            "institution": <string or null>,
            "provider": <string or null>,
            "description": <string or null>,
            "completion_date": <"YYYY-MM-DD" format or null>,
            "certificate_url": <string or null>,
            "skills_learned": [<list of strings>],
            "duration_hours": <float or null>
        }}
    ],
    "academic_records": [
        {{
            "institution_name": <string>,
            "degree": <string or null>,
            "field_of_study": <string or null>,
            "start_date": <"YYYY-MM-DD" format or null>,
            "end_date": <"YYYY-MM-DD" format or null>,
            "gpa": <float or null>,
            "honors": <string or null>,
            "description": <string or null>,
            "location": <string or null>
        }}
    ],
    "life_profile": <string or null>,
    "hobbies": [<list of strings or null>],
    "additional_info": <string or null>
}}

CV Content:
{cv_content}

Return ONLY valid JSON, no additional text or explanation.
"""

LINKEDIN_PARSING_PROMPT = """
You are an expert at extracting structured information from LinkedIn profiles.

Analyze the following LinkedIn profile data and extract all relevant information.
Return a JSON object with the same structure as CV parsing:

{{
    "personal_info": {{
        "age": <integer or null>,
        "birth_country": <string or null>,
        "birth_city": <string or null>,
        "current_location": <string or null>,
        "languages": [
            {{"name": <string>, "proficiency": <"Native"|"Advanced"|"Intermediate"|"Basic">}}
        ],
        "culture": <string or null>
    }},
    "career_goals": <string or null>,
    "short_term_goals": <string or null>,
    "long_term_goals": <string or null>,
    "job_experiences": [
        {{
            "company_name": <string>,
            "position": <string>,
            "description": <string or null>,
            "start_date": <"YYYY-MM-DD" format>,
            "end_date": <"YYYY-MM-DD" format or null if current>,
            "is_current": <boolean>,
            "location": <string or null>,
            "achievements": [<list of strings>],
            "skills_used": [<list of strings>]
        }}
    ],
    "courses": [
        {{
            "course_name": <string>,
            "institution": <string or null>,
            "provider": <string or null>,
            "description": <string or null>,
            "completion_date": <"YYYY-MM-DD" format or null>,
            "certificate_url": <string or null>,
            "skills_learned": [<list of strings>],
            "duration_hours": <float or null>
        }}
    ],
    "academic_records": [
        {{
            "institution_name": <string>,
            "degree": <string or null>,
            "field_of_study": <string or null>,
            "start_date": <"YYYY-MM-DD" format or null>,
            "end_date": <"YYYY-MM-DD" format or null>,
            "gpa": <float or null>,
            "honors": <string or null>,
            "description": <string or null>,
            "location": <string or null>
        }}
    ],
    "life_profile": <string or null>,
    "hobbies": [<list of strings or null>],
    "additional_info": <string or null>
}}

LinkedIn Profile Data:
{linkedin_data}

Return ONLY valid JSON, no additional text or explanation.
"""

