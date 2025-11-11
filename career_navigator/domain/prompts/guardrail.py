GUARDRAIL_VALIDATION_PROMPT = """
You are a data validation expert. Validate the following user profile data for completeness, consistency, and accuracy.

Check for:
1. Required fields are present
2. Date consistency (start dates before end dates, no future dates in past experiences)
3. Logical consistency (e.g., experience level matches job history)
4. Data completeness (all sections have meaningful content)
5. Format correctness (dates, emails, URLs)

User Profile Data:
{profile_data}

Return a validation report as JSON:
{{
    "is_valid": <boolean>,
    "errors": [
        {{
            "field": <string>,
            "error_type": <"missing"|"invalid"|"inconsistent"|"format_error">,
            "message": <string>,
            "severity": <"critical"|"warning"|"info">
        }}
    ],
    "warnings": [
        {{
            "field": <string>,
            "message": <string>
        }}
    ],
    "completeness_score": <float 0-1>,
    "recommendations": [<list of strings>]
}}

Return ONLY valid JSON.
"""

