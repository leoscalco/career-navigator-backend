# Database Schema Documentation

## Overview
This document describes the PostgreSQL database schema for the Career Navigator application.

## Database Structure

### Tables

#### 1. `users`
Core user table with user group classification.

**Columns:**
- `id` (PK, Integer): Primary key
- `email` (String, Unique, Indexed): User email address
- `username` (String, Unique, Indexed): Optional username
- `user_group` (Enum): User classification:
  - `experienced_continuing`: Experienced users continuing their career path
  - `experienced_changing`: Experienced users changing careers
  - `inexperienced_with_goal`: Inexperienced users with clear career goals
  - `inexperienced_no_goal`: Inexperienced users without clear goals
- `created_at` (DateTime): Record creation timestamp
- `updated_at` (DateTime): Last update timestamp

#### 2. `user_profiles`
Extended user profile information.

**Columns:**
- `id` (PK, Integer): Primary key
- `user_id` (FK, Unique): Reference to users table
- `career_goals` (Text): General career goals
- `short_term_goals` (Text): Short-term career objectives
- `long_term_goals` (Text): Long-term career objectives
- `cv_content` (Text): Original CV content
- `linkedin_profile_url` (String): LinkedIn profile URL
- `linkedin_profile_data` (JSON): Stored LinkedIn profile data
- `life_profile` (Text): Personal background and story
- `age` (Integer): User age
- `birth_country` (String): Country of birth
- `birth_city` (String): City of birth
- `current_location` (String): Current location
- `desired_job_locations` (JSON): Array of desired job locations
- `languages` (JSON): Array of languages with proficiency levels
- `culture` (String): Cultural background
- `created_at` (DateTime): Record creation timestamp
- `updated_at` (DateTime): Last update timestamp

#### 3. `job_experiences`
User's work experience history.

**Columns:**
- `id` (PK, Integer): Primary key
- `user_id` (FK): Reference to users table
- `company_name` (String): Company name
- `position` (String): Job position/title
- `description` (Text): Job description
- `start_date` (Date): Employment start date
- `end_date` (Date): Employment end date (NULL if current)
- `is_current` (Boolean): Whether this is the current job
- `location` (String): Job location
- `achievements` (JSON): Array of achievements
- `skills_used` (JSON): Array of skills used in this role
- `created_at` (DateTime): Record creation timestamp
- `updated_at` (DateTime): Last update timestamp

#### 4. `courses`
User's completed courses and certifications.

**Columns:**
- `id` (PK, Integer): Primary key
- `user_id` (FK): Reference to users table
- `course_name` (String): Course name
- `institution` (String): Institution/provider name
- `provider` (String): Course provider (e.g., Coursera, Udemy)
- `description` (Text): Course description
- `completion_date` (Date): Course completion date
- `certificate_url` (String): URL to certificate
- `skills_learned` (JSON): Array of skills learned
- `duration_hours` (Float): Course duration in hours
- `created_at` (DateTime): Record creation timestamp
- `updated_at` (DateTime): Last update timestamp

#### 5. `academic_records`
User's academic/educational background.

**Columns:**
- `id` (PK, Integer): Primary key
- `user_id` (FK): Reference to users table
- `institution_name` (String): Educational institution name
- `degree` (String): Degree type (e.g., "Bachelor of Science")
- `field_of_study` (String): Field of study (e.g., "Computer Science")
- `start_date` (Date): Education start date
- `end_date` (Date): Education end date
- `gpa` (Float): Grade point average
- `honors` (String): Honors or distinctions
- `description` (Text): Additional description
- `location` (String): Institution location
- `created_at` (DateTime): Record creation timestamp
- `updated_at` (DateTime): Last update timestamp

#### 6. `generated_products`
LLM-generated products for users.

**Columns:**
- `id` (PK, Integer): Primary key
- `user_id` (FK): Reference to users table
- `product_type` (Enum): Type of generated product:
  - `linkedin_export`: LinkedIn profile update
  - `cv`: Generated CV
  - `suggested_courses`: Course recommendations
  - `career_plan_1y`: 1-year career plan
  - `career_plan_3y`: 3-year career plan
  - `career_plan_5y`: 5+ year career plan
  - `possible_jobs`: Job suggestions
  - `possible_companies`: Company suggestions
  - `relocation_help`: Relocation assistance
- `content` (JSON): Flexible JSON structure for product content
- `version` (Integer): Version number (for versioning CVs, plans)
- `is_active` (Boolean): Whether this is the active version
- `generated_at` (DateTime): When the product was generated
- `model_used` (String): LLM model used for generation
- `prompt_used` (Text): Prompt used for generation (for reproducibility)
- `created_at` (DateTime): Record creation timestamp
- `updated_at` (DateTime): Last update timestamp

## Relationships

- `users` 1:1 `user_profiles`
- `users` 1:N `job_experiences`
- `users` 1:N `courses`
- `users` 1:N `academic_records`
- `users` 1:N `generated_products`

## Usage

### Running Migrations

1. **Set up your database URL in `.env`:**
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/career_navigator
   ```

2. **Create the database:**
   ```bash
   createdb career_navigator
   ```

3. **Run migrations:**
   ```bash
   poetry run alembic upgrade head
   ```

4. **Create a new migration:**
   ```bash
   poetry run alembic revision --autogenerate -m "description"
   ```

5. **Rollback migration:**
   ```bash
   poetry run alembic downgrade -1
   ```

## Next Steps

- Create repository interfaces (ports) in domain layer
- Implement repository adapters in infrastructure layer
- Add database session management to FastAPI
- Create API endpoints for CRUD operations

