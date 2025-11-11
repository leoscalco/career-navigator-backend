LINKEDIN_EXPORT_PROMPT = """
You are an expert LinkedIn profile optimizer. Create an optimized LinkedIn profile export based on the user's information.

User Profile:
- Career Goals: {career_goals}
- Current Role: {current_role}
- Location: {current_location}
- Skills: {skills}
- Experience: {job_experiences}
- Education: {academic_records}
- Languages: {languages}

Create a LinkedIn profile optimization that includes:

1. Headline (120 characters max) - Compelling professional headline
2. Summary (2000 characters max) - Professional summary highlighting key achievements and goals
3. Experience Section - Optimized descriptions for each role
4. Skills Section - Top 10-15 relevant skills
5. Recommendations - Suggested content for recommendations
6. Keywords - Important keywords for LinkedIn search optimization

Return the response as structured JSON:
{{
    "headline": <string>,
    "summary": <string>,
    "experience_updates": [
        {{
            "company": <string>,
            "position": <string>,
            "optimized_description": <string>,
            "key_achievements": [<list of strings>]
        }}
    ],
    "top_skills": [<list of strings>],
    "recommendation_suggestions": <string>,
    "keywords": [<list of strings>],
    "optimization_tips": [<list of strings>]
}}

Return ONLY valid JSON.
"""

