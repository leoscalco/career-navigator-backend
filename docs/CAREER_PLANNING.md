# Career Planning Products

## Overview

Career Navigator generates comprehensive career planning products based on user's confirmed CV data, goals, and preferences. These products help users navigate their career journey with actionable plans, course recommendations, and job opportunities.

## Career Goal Types

Users can specify their career goal type, which influences the generated plans:

- **`continue_path`** (Default): Continue and advance in current career path
- **`change_career`**: Transition to a completely different career
- **`change_area`**: Change area/domain within the same career field
- **`explore_options`**: Explore different career options

If no goal type is specified, the system defaults to `continue_path`.

## Generated Products

### 1. Career Path (`/workflow/generate-career-path/{user_id}`)

Provides 3-5 potential career paths aligned with:
- User's current skills and experience
- Stated career goals and goal type
- Market demand and growth opportunities
- Target job search locations
- Educational background

**Each career path includes:**
- Career path name and description
- Required skills (what they have vs. what they need)
- Potential job titles
- Potential companies/organizations to target
- Recommended courses/certifications (with providers and relevance)
- Tips and strategies to achieve the path
- Growth potential (High/Medium/Low)
- Estimated timeline to transition
- Key steps to get there

**Response Structure:**
```json
{
  "career_paths": [
    {
      "name": "Senior Data Engineer",
      "description": "...",
      "required_skills": {
        "have": ["Python", "SQL"],
        "need": ["Apache Spark", "Cloud Platforms"]
      },
      "potential_job_titles": ["Senior Data Engineer", "Data Platform Engineer"],
      "potential_companies": ["Google", "Amazon", "Microsoft"],
      "recommended_courses": [
        {
          "course_name": "Apache Spark Fundamentals",
          "provider": "Databricks",
          "description": "...",
          "why_relevant": "..."
        }
      ],
      "tips_and_strategies": ["...", "..."],
      "growth_potential": "High",
      "estimated_timeline": "12-18 months",
      "key_steps": ["...", "..."]
    }
  ],
  "recommendations": "...",
  "market_insights": "..."
}
```

### 2. 1-Year Career Plan (`/workflow/generate-career-plan-1y/{user_id}`)

A detailed quarterly breakdown (Q1, Q2, Q3, Q4) of:
- Specific goals and objectives
- Skills to develop
- Detailed courses/certifications (with providers, descriptions, relevance, duration)
- Projects or experiences to pursue
- Networking activities
- Job search strategies and target companies
- Tips and actionable advice
- Milestones and success metrics

**Response Structure:**
```json
{
  "plan_overview": "...",
  "quarters": {
    "Q1": {
      "goals": ["..."],
      "skills_to_develop": ["..."],
      "courses": [
        {
          "course_name": "...",
          "provider": "...",
          "description": "...",
          "why_relevant": "...",
          "estimated_duration": "..."
        }
      ],
      "projects": ["..."],
      "networking": ["..."],
      "job_search": {
        "target_companies": ["..."],
        "target_positions": ["..."],
        "strategies": ["..."]
      },
      "tips": ["..."],
      "milestones": ["..."]
    },
    "Q2": {...},
    "Q3": {...},
    "Q4": {...}
  },
  "key_metrics": ["..."],
  "success_criteria": "...",
  "overall_tips": ["..."]
}
```

### 3. 3-Year Career Plan (`/workflow/generate-career-plan-3y/{user_id}`)

A comprehensive 3-year plan broken down by years (Year 1, Year 2, Year 3) with:
- Major career milestones
- Target roles or positions
- Skills and competencies to develop
- Detailed education and certifications (with providers)
- Professional development activities
- Career transitions or moves
- Target companies and organizations
- Courses and learning paths
- Tips and strategies
- Expected achievements

**Response Structure:**
```json
{
  "plan_overview": "...",
  "years": {
    "Year 1": {
      "target_role": "...",
      "major_milestones": ["..."],
      "skills_to_develop": ["..."],
      "education": [
        {
          "course_name": "...",
          "provider": "...",
          "description": "...",
          "why_relevant": "..."
        }
      ],
      "professional_development": ["..."],
      "target_companies": ["..."],
      "tips": ["..."],
      "expected_achievements": ["..."]
    },
    "Year 2": {...},
    "Year 3": {...}
  },
  "long_term_vision": "...",
  "key_metrics": ["..."],
  "overall_strategy": "..."
}
```

### 4. 5+ Year Career Plan (`/workflow/generate-career-plan-5y/{user_id}`)

A strategic long-term vision with:
- Vision statement for 5+ years
- Major career phases (Foundation, Growth, Leadership)
- Target senior roles or leadership positions
- Strategic skills and competencies
- Industry or domain expertise to develop
- Potential career pivots or transitions
- Leadership and impact goals
- Strategic learning paths and courses
- Target organizations and companies
- Tips and strategies for long-term success

**Response Structure:**
```json
{
  "vision_statement": "...",
  "career_phases": [
    {
      "phase": "Foundation",
      "duration": "Years 1-2",
      "target_role": "...",
      "key_objectives": ["..."],
      "skills_focus": ["..."],
      "strategic_learning": [
        {
          "course_name": "...",
          "provider": "...",
          "description": "...",
          "why_relevant": "..."
        }
      ],
      "target_companies": ["..."],
      "strategic_moves": ["..."],
      "tips": ["..."]
    }
  ],
  "target_senior_roles": ["..."],
  "strategic_competencies": ["..."],
  "industry_expertise": ["..."],
  "leadership_goals": ["..."],
  "long_term_impact": "...",
  "strategic_advice": ["..."]
}
```

## Workflow

1. **Parse CV** → Extract user data and create user profile
2. **User Reviews** → User can edit goals, add job search locations, etc.
3. **Confirm Draft** → User confirms data is correct
4. **Validate** → Guardrails validation runs
5. **Generate Products** → Generate career path and plans (1y, 3y, 5y)

## Setting Goals and Job Search Locations

### Via API

**Update Profile:**
```bash
PUT /profiles/{profile_id}
{
  "career_goals": "Become a senior data engineer",
  "career_goal_type": "continue_path",  # or "change_career", "change_area", "explore_options"
  "job_search_locations": ["San Francisco, CA", "Remote", "New York, NY"]
}
```

### Default Behavior

- If `career_goals` is empty → Defaults to "Continue current career path"
- If `career_goal_type` is not set → Defaults to `continue_path`
- If `job_search_locations` is empty → Uses `desired_job_locations` or "Not specified"

## API Endpoints

### Generate Career Path
```bash
POST /workflow/generate-career-path/{user_id}
```

### Generate 1-Year Plan
```bash
POST /workflow/generate-career-plan-1y/{user_id}
```

### Generate 3-Year Plan
```bash
POST /workflow/generate-career-plan-3y/{user_id}
```

### Generate 5+ Year Plan
```bash
POST /workflow/generate-career-plan-5y/{user_id}
```

All endpoints require:
- Profile to be validated (`is_validated = true`)
- User to be confirmed (`is_confirmed = true`)

## Product Content

Each generated product includes:

1. **Courses**: Specific course recommendations with:
   - Course name
   - Provider (e.g., Coursera, Udemy, university)
   - Description
   - Why it's relevant
   - Estimated duration (for 1-year plan)

2. **Tips**: Actionable advice and strategies

3. **Companies**: Target companies/organizations to apply to

4. **Job Titles**: Potential positions to target

5. **Skills**: Skills to develop, with focus areas

6. **Milestones**: Key achievements and success metrics

## Example Usage Flow

```bash
# 1. Parse CV (creates user automatically)
POST /workflow/parse-cv-file
# Returns: user_id, profile_id

# 2. Update goals and job search locations
PUT /profiles/{profile_id}
{
  "career_goal_type": "change_career",
  "career_goals": "Transition from software engineering to data science",
  "job_search_locations": ["San Francisco", "Remote"]
}

# 3. Confirm draft
POST /workflow/confirm-draft/{user_id}

# 4. Validate
POST /workflow/validate/{user_id}

# 5. Generate career path
POST /workflow/generate-career-path/{user_id}

# 6. Generate plans
POST /workflow/generate-career-plan-1y/{user_id}
POST /workflow/generate-career-plan-3y/{user_id}
POST /workflow/generate-career-plan-5y/{user_id}
```

## Notes

- Products are generated based on confirmed and validated user data
- Goals default to "continue_path" if not specified
- Job search locations influence company recommendations
- All products include courses, tips, and job/company recommendations
- Products are saved as `GeneratedProduct` records in the database

