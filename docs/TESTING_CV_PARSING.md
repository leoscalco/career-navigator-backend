# Testing CV Parsing Guide

This guide explains how to test CV parsing with a real document.

## Prerequisites

1. **Server Running**: Make sure the FastAPI server is running on `http://localhost:8000`
2. **Database Ready**: PostgreSQL should be running and migrations applied
3. **User Created**: You need a user ID. You can use an existing one or create a new user

## Supported File Formats

The CV parsing now supports multiple document formats:
- **PDF** (.pdf) - Extracts text from PDF documents
- **Word Documents** (.docx) - Extracts text from Microsoft Word documents
- **Plain Text** (.txt) - Direct text content

## Method 1: Using the Test Script (Recommended)

The easiest way to test CV parsing is using the provided test script:

```bash
# Parse CV from a PDF file
python scripts/test_cv_parsing.py --file path/to/your/cv.pdf --user-id 1

# Parse CV from a Word document
python scripts/test_cv_parsing.py --file path/to/your/cv.docx --user-id 1

# Parse CV from a text file
python scripts/test_cv_parsing.py --file path/to/your/cv.txt --user-id 1

# Parse CV with LinkedIn URL
python scripts/test_cv_parsing.py --file cv.pdf --user-id 1 --linkedin-url "https://linkedin.com/in/yourprofile"

# Show profile details after parsing
python scripts/test_cv_parsing.py --file cv.pdf --user-id 1 --show-profile
```

### Example CV File Format

Your CV file should be plain text. Here's an example structure:

```
John Doe
Software Engineer
Email: john.doe@example.com
Phone: +1-234-567-8900
Location: San Francisco, CA

CAREER GOALS
Become a senior software architect and lead technical teams.

EXPERIENCE

Senior Software Engineer
Tech Corp, San Francisco, CA
January 2020 - Present
- Led development of microservices architecture
- Reduced API response time by 40%
- Led team of 5 engineers
Skills: Python, FastAPI, PostgreSQL, Docker, AWS

Software Engineer
StartupXYZ, San Francisco, CA
June 2018 - December 2019
- Developed REST APIs and worked on database optimization
- Built payment processing system
- Improved database queries
Skills: Python, Django, PostgreSQL, Redis

EDUCATION

Bachelor of Science in Computer Science
Stanford University, Stanford, CA
September 2012 - June 2016
GPA: 3.8
Honors: Magna Cum Laude

COURSES & CERTIFICATIONS

Advanced Python Programming
Coursera - University of Michigan
Completed: March 2023
Skills: Python, Design Patterns, Async Programming

LANGUAGES
- English (Native)
- Spanish (Intermediate)
```

## Method 2: Using Swagger UI (Interactive)

### For File Upload (PDF/DOCX):

1. Open Swagger UI: http://localhost:8000/docs
2. Find the `/workflow/parse-cv-file` endpoint
3. Click "Try it out"
4. Fill in the form:
   - **file**: Click "Choose File" and select your PDF/DOCX file
   - **user_id**: Enter your user ID (e.g., 1)
   - **linkedin_url**: (Optional) Enter LinkedIn profile URL
5. Click "Execute"
6. Review the response

### For Text Content:

1. Open Swagger UI: http://localhost:8000/docs
2. Find the `/workflow/parse-cv` endpoint
3. Click "Try it out"
4. Fill in the request body:
   ```json
   {
     "user_id": 1,
     "cv_content": "Your CV content here...",
     "linkedin_url": "https://linkedin.com/in/yourprofile"  // optional
   }
   ```
5. Click "Execute"
6. Review the response

## Method 3: Using cURL

### For File Upload (PDF/DOCX):

```bash
# Upload PDF file
curl -X POST "http://localhost:8000/workflow/parse-cv-file" \
  -F "file=@/path/to/your/cv.pdf" \
  -F "user_id=1" \
  -F "linkedin_url=https://linkedin.com/in/yourprofile"

# Upload Word document
curl -X POST "http://localhost:8000/workflow/parse-cv-file" \
  -F "file=@/path/to/your/cv.docx" \
  -F "user_id=1"
```

### For Text Content:

```bash
curl -X POST "http://localhost:8000/workflow/parse-cv" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "cv_content": "Your CV content here..."
  }'
```

Or with a text file:

```bash
curl -X POST "http://localhost:8000/workflow/parse-cv" \
  -H "Content-Type: application/json" \
  -d @- << EOF
{
  "user_id": 1,
  "cv_content": "$(cat your_cv.txt | sed 's/"/\\"/g')"
}
EOF
```

## Method 4: Using Python Requests

```python
import requests

api_url = "http://localhost:8000"
user_id = 1

# Read CV from file
with open("your_cv.txt", "r") as f:
    cv_content = f.read()

# Parse CV
response = requests.post(
    f"{api_url}/workflow/parse-cv",
    json={
        "user_id": user_id,
        "cv_content": cv_content,
        "linkedin_url": "https://linkedin.com/in/yourprofile"  # optional
    }
)

result = response.json()
print(f"Profile ID: {result['profile_id']}")
print(f"Job Experiences: {len(result['job_experience_ids'])}")
print(f"Courses: {len(result['course_ids'])}")
print(f"Academic Records: {len(result['academic_record_ids'])}")
```

## What Happens After Parsing?

1. **Data Saved as Draft**: All parsed data is saved to the database with `is_draft=True`
2. **Workflow Pauses**: The workflow pauses at the `wait_confirmation` checkpoint
3. **Review Required**: You need to review and confirm the parsed data

## Next Steps After Parsing

### 1. Review Parsed Data

Check what was extracted:

```bash
# Get profile
curl http://localhost:8000/profiles/{profile_id}

# Get job experiences
curl http://localhost:8000/job-experiences?user_id={user_id}

# Get courses
curl http://localhost:8000/courses?user_id={user_id}

# Get academic records
curl http://localhost:8000/academics?user_id={user_id}
```

### 2. Edit Data (if needed)

Use the CRUD endpoints to update any incorrect data:

```bash
# Update profile
curl -X PUT "http://localhost:8000/profiles/{profile_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "career_goals": "Updated career goals",
    "hobbies": ["Reading", "Coding"],
    "additional_info": "Additional information"
  }'
```

### 3. Confirm Draft

Once you've reviewed and edited the data:

```bash
curl -X POST "http://localhost:8000/workflow/confirm-draft/{user_id}"
```

### 4. Validate Profile

Run guardrail validation:

```bash
curl -X POST "http://localhost:8000/workflow/validate/{user_id}"
```

### 5. Generate Products

After validation, you can generate products:

```bash
# Generate CV
curl -X POST "http://localhost:8000/workflow/generate-cv/{user_id}"

# Generate career path
curl -X POST "http://localhost:8000/workflow/generate-career-path/{user_id}"

# Generate career plans
curl -X POST "http://localhost:8000/workflow/generate-career-plan-1y/{user_id}"
curl -X POST "http://localhost:8000/workflow/generate-career-plan-3y/{user_id}"
curl -X POST "http://localhost:8000/workflow/generate-career-plan-5y/{user_id}"

# Generate LinkedIn export
curl -X POST "http://localhost:8000/workflow/generate-linkedin-export/{user_id}"
```

## Expected Output Format

The parsing endpoint returns:

```json
{
  "profile_id": 1,
  "job_experience_ids": [1, 2],
  "course_ids": [1],
  "academic_record_ids": [1],
  "is_draft": true,
  "message": "Data parsed and saved as draft. Please review and confirm."
}
```

## Troubleshooting

### Error: "Profile not found for user {user_id}"

**Solution**: Create a user first:

```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "user_group": "experienced_continuing"
  }'
```

### Error: "Failed to parse CV"

**Possible causes**:
1. CV content is empty or invalid
2. LLM API (Groq) is not configured or rate-limited
3. CV format is too complex for the parser

**Solution**: 
- Check that `GROQ_API_KEY` is set in your `.env` file
- Try simplifying the CV content
- Check server logs for detailed error messages

### Parsed Data is Incorrect

**Solution**: 
1. Review the parsed data via API endpoints
2. Edit incorrect fields using PUT endpoints
3. The LLM parsing is not perfect - human review is expected
4. You can improve the prompt in `career_navigator/domain/prompts/cv_parsing.py`

## Tips for Better Parsing Results

1. **Use Plain Text**: Convert PDF/Word docs to plain text first
2. **Clear Structure**: Use clear section headers (EXPERIENCE, EDUCATION, etc.)
3. **Complete Dates**: Use YYYY-MM-DD format when possible
4. **List Skills**: Clearly list skills used in each role
5. **Include Goals**: Add career goals if available

## Example: Complete Workflow

```bash
# 1. Create a user (if needed)
USER_ID=1

# 2. Parse CV
python scripts/test_cv_parsing.py --file cv.txt --user-id $USER_ID --show-profile

# 3. Review and edit data (via Swagger UI or API)

# 4. Confirm draft
curl -X POST "http://localhost:8000/workflow/confirm-draft/$USER_ID"

# 5. Validate
curl -X POST "http://localhost:8000/workflow/validate/$USER_ID"

# 6. Generate CV
curl -X POST "http://localhost:8000/workflow/generate-cv/$USER_ID"
```

## Checking Workflow Status

At any time, check the workflow status:

```bash
curl "http://localhost:8000/workflow/status/{user_id}"
```

This returns:
```json
{
  "status": "in_progress",
  "current_step": "waiting_confirmation",
  "needs_human_review": true,
  "is_draft": true,
  "is_validated": false
}
```

