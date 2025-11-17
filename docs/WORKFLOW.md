# Career Navigator Workflow

This document describes the complete workflow for processing CV/LinkedIn data and generating career products.

## Overview

The workflow follows these steps:
1. **Parse CV/LinkedIn** - Extract structured data using LLM
2. **Human Review** - User reviews and edits draft data
3. **Guardrail Validation** - Automated validation of data quality
4. **Generate Products** - Create CV, career plans, etc.

## Workflow Steps

### Step 1: Parse CV or LinkedIn Profile

**Endpoint:** `POST /workflow/parse-cv` or `POST /workflow/parse-linkedin`

**Purpose:** Extract structured data from CV or LinkedIn profile using LLM.

**Request:**
```json
{
  "user_id": 1,
  "cv_content": "Full CV text content...",
  "linkedin_url": "https://linkedin.com/in/user" // optional
}
```

**Response:**
```json
{
  "profile_id": 1,
  "job_experience_ids": [1, 2, 3],
  "course_ids": [1, 2],
  "academic_record_ids": [1],
  "is_draft": true,
  "message": "Data parsed and saved as draft. Please review and confirm."
}
```

**What happens:**
- LLM analyzes the CV/LinkedIn content
- Extracts structured data:
  - Personal information (age, location, languages, etc.)
  - Career goals
  - Job experiences
  - Courses and certifications
  - Academic records
  - Life profile and hobbies
- Saves everything to database as **draft** (`is_draft=true`)

### Step 2: Human Review & Confirmation

**Endpoint:** `POST /workflow/confirm-draft/{user_id}`

**Purpose:** User reviews the parsed data, makes edits via CRUD APIs, then confirms.

**Process:**
1. User reviews parsed data via GET endpoints:
   - `GET /profiles/user/{user_id}`
   - `GET /job-experiences/user/{user_id}`
   - `GET /courses/user/{user_id}`
   - `GET /academics/user/{user_id}`

2. User edits data via PUT endpoints if needed:
   - `PUT /profiles/{profile_id}`
   - `PUT /job-experiences/{job_id}`
   - etc.

3. User can add additional information:
   - Career goals
   - Hobbies
   - Additional info
   - Objectives

4. User confirms draft is ready

**Response:**
```json
{
  "profile_id": 1,
  "is_draft": false,
  "message": "Draft confirmed, ready for validation"
}
```

### Step 3: Guardrail Validation

**Endpoint:** `POST /workflow/validate/{user_id}`

**Purpose:** Automated validation of data quality, completeness, and consistency.

**Response:**
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [
    {
      "field": "career_goals",
      "message": "Career goals could be more specific"
    }
  ],
  "completeness_score": 0.85,
  "recommendations": [
    "Add more details about your career goals",
    "Include more achievements in job experiences"
  ]
}
```

**What is validated:**
- Required fields presence
- Date consistency (start < end dates)
- Logical consistency
- Data completeness
- Format correctness

**If validation fails:**
- User can fix issues via PUT endpoints
- Re-run validation until it passes

### Step 4: Generate Products

Once validated, you can generate various products:

#### Generate CV

**Endpoint:** `POST /workflow/generate-cv/{user_id}`

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "product_type": "cv",
  "content": {
    "cv_content": "Generated CV text..."
  },
  "version": 1,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  ...
}
```

The generated CV is saved as a `GeneratedProduct` and can be retrieved later.

## Additional Products (Future Implementation)

The following prompts are ready but need service integration:

### Career Path Suggestions
- **Prompt:** `CAREER_PATH_PROMPT`
- **Service:** `CareerPlanningService.generate_career_path()`
- **Product Type:** `ProductType.POSSIBLE_JOBS`

### Career Plans
- **1-Year Plan:** `CAREER_PLAN_1Y_PROMPT` → `ProductType.CAREER_PLAN_1Y`
- **3-Year Plan:** `CAREER_PLAN_3Y_PROMPT` → `ProductType.CAREER_PLAN_3Y`
- **5+ Year Plan:** `CAREER_PLAN_5Y_PROMPT` → `ProductType.CAREER_PLAN_5Y`

### LinkedIn Export
- **Prompt:** `LINKEDIN_EXPORT_PROMPT`
- **Product Type:** `ProductType.LINKEDIN_EXPORT`

## Data Persistence

**Important:** All parsed data is stored in the database, so:
- You don't need to re-parse the same CV/LinkedIn
- You can generate multiple products from the same data
- Historical data is preserved for future products

## Example Complete Flow

```bash
# 1. Parse CV
curl -X POST http://localhost:8000/workflow/parse-cv \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "cv_content": "..."}'

# 2. Review and edit (via CRUD APIs)
curl http://localhost:8000/profiles/user/1
curl -X PUT http://localhost:8000/profiles/1 \
  -d '{"career_goals": "Updated goals..."}'

# 3. Confirm draft
curl -X POST http://localhost:8000/workflow/confirm-draft/1

# 4. Validate
curl -X POST http://localhost:8000/workflow/validate/1

# 5. Generate CV
curl -X POST http://localhost:8000/workflow/generate-cv/1

# 6. Get generated product
curl http://localhost:8000/products/user/1?product_type=cv
```

## Architecture

The workflow follows hexagonal architecture:

- **Domain Layer:** Prompts, domain models
- **Application Layer:** Services (ParsingService, ValidationService, CVGenerationService, WorkflowService)
- **Infrastructure Layer:** LLM adapters, repositories
- **API Layer:** REST endpoints

This separation allows:
- Easy swapping of LLM providers
- Testing without external dependencies
- Clear separation of concerns

