from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Enum,
    JSON,
    Date,
    Float,
)
from sqlalchemy.orm import relationship
from career_navigator.infrastructure.database.base import Base


class UserGroup(str, PyEnum):
    EXPERIENCED_CONTINUING = "experienced_continuing"
    EXPERIENCED_CHANGING = "experienced_changing"
    INEXPERIENCED_WITH_GOAL = "inexperienced_with_goal"
    INEXPERIENCED_NO_GOAL = "inexperienced_no_goal"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True)
    user_group = Column(Enum(UserGroup), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    job_experiences = relationship("JobExperience", back_populates="user", cascade="all, delete-orphan")
    courses = relationship("Course", back_populates="user", cascade="all, delete-orphan")
    academic_records = relationship("AcademicRecord", back_populates="user", cascade="all, delete-orphan")
    generated_products = relationship("GeneratedProduct", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Goals and aspirations
    career_goals = Column(Text)
    short_term_goals = Column(Text)
    long_term_goals = Column(Text)

    # Documents
    cv_content = Column(Text)  # Original CV content
    linkedin_profile_url = Column(String(500))
    linkedin_profile_data = Column(JSON)  # Stored LinkedIn data
    life_profile = Column(Text)  # Personal story, background

    # Demographics
    age = Column(Integer)
    birth_country = Column(String(100))
    birth_city = Column(String(100))
    current_location = Column(String(200))
    desired_job_locations = Column(JSON)  # List of desired locations
    languages = Column(JSON)  # List of languages with proficiency levels
    culture = Column(String(100))

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="profile")


class JobExperience(Base):
    __tablename__ = "job_experiences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    company_name = Column(String(200), nullable=False)
    position = Column(String(200), nullable=False)
    description = Column(Text)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)  # NULL if current job
    is_current = Column(Boolean, default=False)
    location = Column(String(200))
    achievements = Column(JSON)  # List of achievements
    skills_used = Column(JSON)  # List of skills

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="job_experiences")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    course_name = Column(String(300), nullable=False)
    institution = Column(String(200))
    provider = Column(String(200))  # e.g., Coursera, Udemy, university name
    description = Column(Text)
    completion_date = Column(Date)
    certificate_url = Column(String(500))
    skills_learned = Column(JSON)  # List of skills
    duration_hours = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="courses")


class AcademicRecord(Base):
    __tablename__ = "academic_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    institution_name = Column(String(200), nullable=False)
    degree = Column(String(200))  # e.g., "Bachelor of Science"
    field_of_study = Column(String(200))  # e.g., "Computer Science"
    start_date = Column(Date)
    end_date = Column(Date)
    gpa = Column(Float)
    honors = Column(String(200))
    description = Column(Text)
    location = Column(String(200))

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="academic_records")


class ProductType(str, PyEnum):
    LINKEDIN_EXPORT = "linkedin_export"
    CV = "cv"
    SUGGESTED_COURSES = "suggested_courses"
    CAREER_PLAN_1Y = "career_plan_1y"
    CAREER_PLAN_3Y = "career_plan_3y"
    CAREER_PLAN_5Y = "career_plan_5y"
    POSSIBLE_JOBS = "possible_jobs"
    POSSIBLE_COMPANIES = "possible_companies"
    RELOCATION_HELP = "relocation_help"


class GeneratedProduct(Base):
    __tablename__ = "generated_products"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    product_type = Column(Enum(ProductType), nullable=False)
    content = Column(JSON)  # Flexible JSON structure for different product types
    version = Column(Integer, default=1)  # For versioning CVs, career plans, etc.
    is_active = Column(Boolean, default=True)  # For CVs, only one active version

    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    model_used = Column(String(100))  # Which LLM was used
    prompt_used = Column(Text)  # Store the prompt for reproducibility

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="generated_products")

