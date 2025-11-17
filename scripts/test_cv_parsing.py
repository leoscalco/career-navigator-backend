#!/usr/bin/env python3
"""
Test script for CV parsing functionality.

This script helps you test CV parsing with a real document.
You can either:
1. Pass CV content as a file path (supports PDF, DOCX, TXT)
2. Pass CV content directly as text
3. Use an existing user ID or create a new one

Usage:
    python scripts/test_cv_parsing.py --file path/to/cv.pdf --user-id 1
    python scripts/test_cv_parsing.py --file path/to/cv.docx --user-id 1
    python scripts/test_cv_parsing.py --file path/to/cv.txt --user-id 1
    python scripts/test_cv_parsing.py --text "CV content here..." --user-id 1
    python scripts/test_cv_parsing.py --file cv.txt  # Will use user_id=1 by default
"""

import argparse
import sys
import requests
import json
from pathlib import Path


def read_cv_file(file_path: str) -> str:
    """Read CV content from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Error: File '{file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        sys.exit(1)


def parse_cv_file(api_url: str, user_id: int, file_path: str, linkedin_url: str = None):
    """Call the CV parsing API endpoint with file upload."""
    url = f"{api_url}/workflow/parse-cv-file"
    
    file_ext = Path(file_path).suffix.lower()
    supported_formats = [".pdf", ".docx", ".txt", ".text"]
    
    if file_ext not in supported_formats:
        print(f"❌ Error: Unsupported file format '{file_ext}'")
        print(f"   Supported formats: {', '.join(supported_formats)}")
        sys.exit(1)
    
    print(f"📤 Uploading CV file to {url}...")
    print(f"   File: {file_path}")
    print(f"   Format: {file_ext}")
    print(f"   User ID: {user_id}")
    print()
    
    try:
        with open(file_path, 'rb') as f:
            files = {
                'file': (Path(file_path).name, f, f'application/{file_ext[1:]}')
            }
            data = {
                'user_id': user_id,
            }
            if linkedin_url:
                data['linkedin_url'] = linkedin_url
            
            response = requests.post(url, files=files, data=data, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            
            print("✅ CV parsed successfully!")
            print()
            print("📊 Parsing Results:")
            print(f"   Profile ID: {result.get('profile_id')}")
            print(f"   Job Experiences: {len(result.get('job_experience_ids', []))} found")
            print(f"   Courses: {len(result.get('course_ids', []))} found")
            print(f"   Academic Records: {len(result.get('academic_record_ids', []))} found")
            print(f"   Is Draft: {result.get('is_draft')}")
            print(f"   Message: {result.get('message')}")
            print()
            print("📝 Next Steps:")
            print("   1. Review the parsed data in the database")
            print(f"   2. Check profile: GET {api_url}/profiles/{result.get('profile_id')}")
            print(f"   3. Confirm draft: POST {api_url}/workflow/confirm-draft/{user_id}")
            print(f"   4. Validate: POST {api_url}/workflow/validate/{user_id}")
            print()
            
            return result
            
    except FileNotFoundError:
        print(f"❌ Error: File '{file_path}' not found.")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response.status_code == 400:
            try:
                error_detail = e.response.json()
                print(f"   Detail: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"   Response: {e.response.text}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
        sys.exit(1)


def parse_cv(api_url: str, user_id: int, cv_content: str, linkedin_url: str = None):
    """Call the CV parsing API endpoint with text content."""
    url = f"{api_url}/workflow/parse-cv"
    
    payload = {
        "user_id": user_id,
        "cv_content": cv_content,
    }
    
    if linkedin_url:
        payload["linkedin_url"] = linkedin_url
    
    print(f"📤 Sending CV to {url}...")
    print(f"   User ID: {user_id}")
    print(f"   CV Content Length: {len(cv_content)} characters")
    print()
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        print("✅ CV parsed successfully!")
        print()
        print("📊 Parsing Results:")
        print(f"   Profile ID: {result.get('profile_id')}")
        print(f"   Job Experiences: {len(result.get('job_experience_ids', []))} found")
        print(f"   Courses: {len(result.get('course_ids', []))} found")
        print(f"   Academic Records: {len(result.get('academic_record_ids', []))} found")
        print(f"   Is Draft: {result.get('is_draft')}")
        print(f"   Message: {result.get('message')}")
        print()
        print("📝 Next Steps:")
        print("   1. Review the parsed data in the database")
        print(f"   2. Check profile: GET {api_url}/profiles/{result.get('profile_id')}")
        print(f"   3. Confirm draft: POST {api_url}/workflow/confirm-draft/{user_id}")
        print(f"   4. Validate: POST {api_url}/workflow/validate/{user_id}")
        print()
        
        return result
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response.status_code == 400:
            try:
                error_detail = e.response.json()
                print(f"   Detail: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"   Response: {e.response.text}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
        sys.exit(1)


def get_profile_details(api_url: str, profile_id: int):
    """Get profile details after parsing."""
    url = f"{api_url}/profiles/{profile_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        profile = response.json()
        
        print("👤 Profile Details:")
        print(f"   Career Goals: {profile.get('career_goals', 'N/A')}")
        print(f"   Current Location: {profile.get('current_location', 'N/A')}")
        print(f"   Age: {profile.get('age', 'N/A')}")
        print(f"   Languages: {len(profile.get('languages', []))} languages")
        print()
        
    except Exception as e:
        print(f"⚠️  Could not fetch profile details: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Test CV parsing with a real document",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse CV from PDF file
  python scripts/test_cv_parsing.py --file cv.pdf --user-id 1
  
  # Parse CV from Word document
  python scripts/test_cv_parsing.py --file cv.docx --user-id 1
  
  # Parse CV from text file
  python scripts/test_cv_parsing.py --file cv.txt --user-id 1
  
  # Parse CV from text string
  python scripts/test_cv_parsing.py --text "John Doe\\nSoftware Engineer..." --user-id 1
  
  # Parse CV with LinkedIn URL
  python scripts/test_cv_parsing.py --file cv.pdf --user-id 1 --linkedin-url "https://linkedin.com/in/johndoe"
        """
    )
    
    parser.add_argument(
        "--file",
        type=str,
        help="Path to CV file (PDF, DOCX, or TXT format)"
    )
    
    parser.add_argument(
        "--text",
        type=str,
        help="CV content as text string"
    )
    
    parser.add_argument(
        "--user-id",
        type=int,
        default=1,
        help="User ID to associate with the CV (default: 1)"
    )
    
    parser.add_argument(
        "--linkedin-url",
        type=str,
        help="Optional LinkedIn profile URL"
    )
    
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--show-profile",
        action="store_true",
        help="Show profile details after parsing"
    )
    
    args = parser.parse_args()
    
    # Validate input
    if not args.file and not args.text:
        print("❌ Error: You must provide either --file or --text")
        parser.print_help()
        sys.exit(1)
    
    if args.file and args.text:
        print("❌ Error: Provide either --file OR --text, not both")
        parser.print_help()
        sys.exit(1)
    
    # Determine if file is PDF/DOCX (needs file upload) or TXT (can use text endpoint)
    if args.file:
        file_path = Path(args.file)
        file_ext = file_path.suffix.lower()
        
        # Use file upload endpoint for PDF and DOCX
        if file_ext in [".pdf", ".docx", ".doc"]:
            print(f"📄 Reading document from: {args.file}")
            print(f"   Format: {file_ext}")
            print()
            
            result = parse_cv_file(
                api_url=args.api_url,
                user_id=args.user_id,
                file_path=args.file,
                linkedin_url=args.linkedin_url
            )
        else:
            # Use text endpoint for TXT files
            cv_content = read_cv_file(args.file)
            print(f"📄 Reading CV from: {args.file}")
            print()
            
            result = parse_cv(
                api_url=args.api_url,
                user_id=args.user_id,
                cv_content=cv_content,
                linkedin_url=args.linkedin_url
            )
    else:
        # Use text endpoint
        cv_content = args.text
        print("📄 Using CV content from --text argument")
        print()
        
        result = parse_cv(
            api_url=args.api_url,
            user_id=args.user_id,
            cv_content=cv_content,
            linkedin_url=args.linkedin_url
        )
    
    # Show profile details if requested
    if args.show_profile and result.get('profile_id'):
        get_profile_details(args.api_url, result['profile_id'])


if __name__ == "__main__":
    main()

