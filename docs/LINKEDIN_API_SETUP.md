# LinkedIn API Integration Setup

This guide explains how to set up and use the LinkedIn API integration for fetching profile data.

## Overview

The LinkedIn API integration allows you to fetch profile data directly from LinkedIn instead of manually providing LinkedIn data. This provides more accurate and up-to-date information.

## Prerequisites

1. **LinkedIn Developer Account**: Create an account at [LinkedIn Developer Portal](https://developer.linkedin.com/)
2. **LinkedIn Application**: Create a new application in the LinkedIn Developer Portal
3. **OAuth 2.0 Access Token**: Obtain an access token with appropriate permissions

## Setup Steps

### 1. Create LinkedIn Application

1. Go to [LinkedIn Developer Portal](https://developer.linkedin.com/)
2. Click "Create app"
3. Fill in the application details:
   - App name
   - Company page
   - Privacy policy URL
   - App logo
4. Submit for review (if required)

### 2. Configure OAuth 2.0

1. In your LinkedIn app settings, go to "Auth" tab
2. Add authorized redirect URLs (e.g., `http://localhost:8000/auth/linkedin/callback`)
3. Note your **Client ID** and **Client Secret**

### 3. Request Required Permissions

The following OAuth scopes are required:

- `r_liteprofile` or `r_basicprofile`: Access to basic profile information
- `r_emailaddress`: Access to email address (optional but recommended)
- `r_workhistory`: Access to work experience (optional but recommended)
- `r_education`: Access to education history (optional but recommended)

### 4. Obtain Access Token

#### Option A: OAuth 2.0 Authorization Code Flow (Recommended for Production)

1. Redirect user to LinkedIn authorization URL:
   ```
   https://www.linkedin.com/oauth/v2/authorization?
     response_type=code&
     client_id={CLIENT_ID}&
     redirect_uri={REDIRECT_URI}&
     state={STATE}&
     scope=r_liteprofile r_emailaddress r_workhistory r_education
   ```

2. User authorizes and gets redirected back with authorization code

3. Exchange authorization code for access token:
   ```bash
   curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
     -d "grant_type=authorization_code" \
     -d "code={AUTHORIZATION_CODE}" \
     -d "redirect_uri={REDIRECT_URI}" \
     -d "client_id={CLIENT_ID}" \
     -d "client_secret={CLIENT_SECRET}"
   ```

4. Use the returned `access_token` in API requests

#### Option B: Developer Token (For Testing Only)

For testing purposes, you can use a developer token from the LinkedIn Developer Portal (limited functionality).

### 5. Configure Environment Variables

Add to your `.env` file:

```env
# LinkedIn API Configuration
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_ACCESS_TOKEN=your_access_token_here
```

**Note**: For production, use OAuth 2.0 flow to obtain access tokens per user. The `LINKEDIN_ACCESS_TOKEN` in `.env` is mainly for testing or service accounts.

## Usage

### Using LinkedIn API (Recommended)

```bash
# Parse LinkedIn profile by URL
curl -X POST "http://localhost:8000/workflow/parse-linkedin" \
  -H "Content-Type: application/json" \
  -d '{
    "linkedin_profile_url": "https://linkedin.com/in/username",
    "linkedin_access_token": "your_access_token_here"
  }'

# Parse LinkedIn profile by ID (use "me" for authenticated user)
curl -X POST "http://localhost:8000/workflow/parse-linkedin" \
  -H "Content-Type: application/json" \
  -d '{
    "linkedin_profile_id": "me",
    "linkedin_access_token": "your_access_token_here"
  }'
```

### Using Manual Data (Fallback)

If you don't have API access, you can still provide LinkedIn data manually:

```bash
curl -X POST "http://localhost:8000/workflow/parse-linkedin" \
  -H "Content-Type: application/json" \
  -d '{
    "linkedin_data": "Name: John Doe\nHeadline: Software Engineer\n..."
  }'
```

## API Endpoint Details

### POST `/workflow/parse-linkedin`

**Request Body:**
```json
{
  "user_id": 1,  // Optional - will be created if not provided
  "linkedin_profile_url": "https://linkedin.com/in/username",  // Optional
  "linkedin_profile_id": "me",  // Optional - "me" or profile ID
  "linkedin_access_token": "token_here",  // Optional - uses env var if not provided
  "linkedin_data": "raw data..."  // Optional - manual data fallback
}
```

**Response:**
```json
{
  "user_id": 1,
  "profile_id": 1,
  "job_experience_ids": [1, 2],
  "course_ids": [1],
  "academic_record_ids": [1],
  "is_draft": true,
  "message": "Data parsed and saved as draft. Please review and confirm."
}
```

## LinkedIn API Limitations

1. **Rate Limits**: LinkedIn API has rate limits. Check [LinkedIn API Rate Limits](https://learn.microsoft.com/en-us/linkedin/shared/authentication/rate-limits) for details.

2. **Profile Access**: You can only access profiles that:
   - Belong to the authenticated user (using "me")
   - Are publicly accessible (if using public profile endpoints)
   - Have granted permission to your app

3. **Data Availability**: Some fields may not be available depending on:
   - OAuth scopes granted
   - User's privacy settings
   - Profile completeness

## Troubleshooting

### Error: "LinkedIn access token is required"

**Solution**: Ensure `LINKEDIN_ACCESS_TOKEN` is set in `.env` or provide `linkedin_access_token` in the request.

### Error: "Failed to fetch LinkedIn profile: 401 Unauthorized"

**Solution**: 
- Check if access token is valid and not expired
- Verify OAuth scopes are correct
- Regenerate access token if needed

### Error: "Invalid LinkedIn profile URL format"

**Solution**: Ensure URL format is `https://linkedin.com/in/username` or `https://www.linkedin.com/in/username`

### Error: "Profile not found"

**Solution**:
- Verify profile ID is correct
- Check if profile is accessible with current permissions
- Use "me" for authenticated user's own profile

## Security Considerations

1. **Never commit access tokens** to version control
2. **Use environment variables** for sensitive credentials
3. **Implement OAuth 2.0 flow** for production (don't hardcode tokens)
4. **Rotate access tokens** regularly
5. **Respect user privacy** and only request necessary permissions

## References

- [LinkedIn API Documentation](https://learn.microsoft.com/en-us/linkedin/shared/integrations/people/profile-api)
- [LinkedIn OAuth 2.0 Guide](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication)
- [LinkedIn Developer Portal](https://developer.linkedin.com/)

