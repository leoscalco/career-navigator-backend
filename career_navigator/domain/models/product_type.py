from enum import Enum


class ProductType(str, Enum):
    LINKEDIN_EXPORT = "linkedin_export"
    CV = "cv"
    SUGGESTED_COURSES = "suggested_courses"
    CAREER_PLAN_1Y = "career_plan_1y"
    CAREER_PLAN_3Y = "career_plan_3y"
    CAREER_PLAN_5Y = "career_plan_5y"
    POSSIBLE_JOBS = "possible_jobs"
    POSSIBLE_COMPANIES = "possible_companies"
    RELOCATION_HELP = "relocation_help"

