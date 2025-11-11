CAREER_PLAN_1Y_PROMPT = """
You are a career planning expert. Create a detailed 1-year career plan for the user.

User Profile:
- Career Goals: {career_goals}
- Current Role: {current_role}
- Skills: {skills}
- Experience Level: {experience_level}
- User Group: {user_group}

Create a comprehensive 1-year career plan broken down by quarters (Q1, Q2, Q3, Q4).

For each quarter, include:
- Specific goals and objectives
- Skills to develop
- Courses or certifications to complete
- Projects or experiences to pursue
- Networking activities
- Milestones and success metrics

Return the response as structured JSON:
{{
    "plan_overview": <string>,
    "quarters": {{
        "Q1": {{
            "goals": [<list of strings>],
            "skills_to_develop": [<list of strings>],
            "courses": [<list of strings>],
            "projects": [<list of strings>],
            "networking": [<list of strings>],
            "milestones": [<list of strings>]
        }},
        "Q2": {{...}},
        "Q3": {{...}},
        "Q4": {{...}}
    }},
    "key_metrics": [<list of strings>],
    "success_criteria": <string>
}}

Return ONLY valid JSON.
"""

CAREER_PLAN_3Y_PROMPT = """
You are a career planning expert. Create a detailed 3-year career plan for the user.

User Profile:
- Career Goals: {career_goals}
- Long-term Goals: {long_term_goals}
- Current Role: {current_role}
- Skills: {skills}
- Experience Level: {experience_level}
- User Group: {user_group}

Create a comprehensive 3-year career plan broken down by years (Year 1, Year 2, Year 3).

For each year, include:
- Major career milestones
- Target roles or positions
- Skills and competencies to develop
- Education and certifications
- Professional development activities
- Career transitions or moves
- Expected achievements

Return the response as structured JSON:
{{
    "plan_overview": <string>,
    "years": {{
        "Year 1": {{
            "target_role": <string>,
            "major_milestones": [<list of strings>],
            "skills_to_develop": [<list of strings>],
            "education": [<list of strings>],
            "professional_development": [<list of strings>],
            "expected_achievements": [<list of strings>]
        }},
        "Year 2": {{...}},
        "Year 3": {{...}}
    }},
    "long_term_vision": <string>,
    "key_metrics": [<list of strings>]
}}

Return ONLY valid JSON.
"""

CAREER_PLAN_5Y_PROMPT = """
You are a career planning expert. Create a strategic 5+ year career plan for the user.

User Profile:
- Career Goals: {career_goals}
- Long-term Goals: {long_term_goals}
- Current Role: {current_role}
- Skills: {skills}
- Experience Level: {experience_level}
- User Group: {user_group}

Create a strategic 5+ year career plan with a long-term vision.

Structure:
- Vision statement for 5+ years
- Major career phases
- Target senior roles or leadership positions
- Strategic skills and competencies
- Industry or domain expertise to develop
- Potential career pivots or transitions
- Leadership and impact goals

Return the response as structured JSON:
{{
    "vision_statement": <string>,
    "career_phases": [
        {{
            "phase": <string (e.g., "Foundation", "Growth", "Leadership")>,
            "duration": <string>,
            "target_role": <string>,
            "key_objectives": [<list of strings>],
            "skills_focus": [<list of strings>],
            "strategic_moves": [<list of strings>]
        }}
    ],
    "target_senior_roles": [<list of strings>],
    "strategic_competencies": [<list of strings>],
    "industry_expertise": [<list of strings>],
    "leadership_goals": [<list of strings>],
    "long_term_impact": <string>
}}

Return ONLY valid JSON.
"""

