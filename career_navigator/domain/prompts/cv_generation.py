CV_GENERATION_PROMPT = """
You are an expert CV/resume writer. Create a professional, well-structured CV based on the following user profile information.

Guidelines:
- Use modern, clean formatting
- Highlight achievements and impact, not just responsibilities
- Use action verbs and quantifiable results
- Keep it concise but comprehensive
- Ensure proper chronological order
- Include relevant skills and keywords
- Format dates consistently

User Profile Information:
- Career Goals: {career_goals}
- Current Location: {current_location}
- Desired Job Locations: {desired_job_locations}

Job Experiences:
{job_experiences}

Academic Records:
{academic_records}

Courses & Certifications:
{courses}

Skills: {skills}

Languages: {languages}

Additional Information: {additional_info}

Generate a professional CV in a structured format. Return the CV content as plain text, formatted for easy reading.
Make sure to include:
1. Header with name and contact information (use placeholder if not provided)
2. Professional Summary (based on career goals and experience)
3. Work Experience (in reverse chronological order)
4. Education
5. Skills
6. Certifications/Courses (if relevant)
7. Languages

Return the CV content directly, no JSON wrapper.
"""

