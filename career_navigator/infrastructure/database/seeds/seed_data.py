"""
Database seeding script to populate the database with mock data.
"""
from datetime import date, datetime, timedelta
from career_navigator.infrastructure.database.session import SessionLocal
from career_navigator.infrastructure.database.models import (
    User,
    UserProfile,
    JobExperience,
    Course,
    AcademicRecord,
    GeneratedProduct,
    UserGroup,
    ProductType,
)


def seed_database():
    """Seed the database with mock data."""
    db = SessionLocal()
    
    try:
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("Clearing existing data...")
        db.query(GeneratedProduct).delete()
        db.query(AcademicRecord).delete()
        db.query(Course).delete()
        db.query(JobExperience).delete()
        db.query(UserProfile).delete()
        db.query(User).delete()
        db.commit()
        
        print("Creating mock users...")
        
        # User 1: Experienced - Continuing career path
        user1 = User(
            email="john.doe@example.com",
            username="johndoe",
            user_group=UserGroup.EXPERIENCED_CONTINUING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user1)
        db.flush()
        
        profile1 = UserProfile(
            user_id=user1.id,
            career_goals="Become a senior software architect and lead technical teams",
            short_term_goals="Complete AWS Solutions Architect certification",
            long_term_goals="Lead a team of 20+ engineers and contribute to open source",
            cv_content="Experienced Software Engineer with 8+ years in backend development...",
            linkedin_profile_url="https://linkedin.com/in/johndoe",
            age=32,
            birth_country="United States",
            birth_city="San Francisco",
            current_location="San Francisco, CA",
            desired_job_locations=["San Francisco", "Remote", "New York"],
            languages=[{"name": "English", "proficiency": "Native"}, {"name": "Spanish", "proficiency": "Intermediate"}],
            culture="American",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(profile1)
        
        # Job experiences for user1
        job1 = JobExperience(
            user_id=user1.id,
            company_name="Tech Corp",
            position="Senior Software Engineer",
            description="Led development of microservices architecture",
            start_date=date(2020, 1, 1),
            end_date=None,
            is_current=True,
            location="San Francisco, CA",
            achievements=["Reduced API response time by 40%", "Led team of 5 engineers"],
            skills_used=["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(job1)
        
        job2 = JobExperience(
            user_id=user1.id,
            company_name="StartupXYZ",
            position="Software Engineer",
            description="Developed REST APIs and worked on database optimization",
            start_date=date(2018, 6, 1),
            end_date=date(2019, 12, 31),
            is_current=False,
            location="San Francisco, CA",
            achievements=["Built payment processing system", "Improved database queries"],
            skills_used=["Python", "Django", "PostgreSQL", "Redis"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(job2)
        
        # Courses for user1
        course1 = Course(
            user_id=user1.id,
            course_name="Advanced Python Programming",
            institution="Coursera",
            provider="University of Michigan",
            description="Deep dive into Python advanced features",
            completion_date=date(2023, 3, 15),
            certificate_url="https://coursera.org/certificate/abc123",
            skills_learned=["Python", "Design Patterns", "Async Programming"],
            duration_hours=40.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(course1)
        
        # Academic records for user1
        academic1 = AcademicRecord(
            user_id=user1.id,
            institution_name="Stanford University",
            degree="Bachelor of Science",
            field_of_study="Computer Science",
            start_date=date(2012, 9, 1),
            end_date=date(2016, 6, 1),
            gpa=3.8,
            honors="Magna Cum Laude",
            description="Focus on software engineering and algorithms",
            location="Stanford, CA",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(academic1)
        
        # User 2: Experienced - Changing career
        user2 = User(
            email="sarah.smith@example.com",
            username="sarahsmith",
            user_group=UserGroup.EXPERIENCED_CHANGING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user2)
        db.flush()
        
        profile2 = UserProfile(
            user_id=user2.id,
            career_goals="Transition from marketing to product management",
            short_term_goals="Complete product management certification",
            long_term_goals="Become a VP of Product at a tech company",
            cv_content="Marketing professional with 7 years experience...",
            linkedin_profile_url="https://linkedin.com/in/sarahsmith",
            age=30,
            birth_country="Canada",
            birth_city="Toronto",
            current_location="Toronto, ON",
            desired_job_locations=["Toronto", "Remote", "Vancouver"],
            languages=[{"name": "English", "proficiency": "Native"}, {"name": "French", "proficiency": "Intermediate"}],
            culture="Canadian",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(profile2)
        
        job3 = JobExperience(
            user_id=user2.id,
            company_name="Marketing Agency Inc",
            position="Senior Marketing Manager",
            description="Led digital marketing campaigns and brand strategy",
            start_date=date(2019, 3, 1),
            end_date=None,
            is_current=True,
            location="Toronto, ON",
            achievements=["Increased brand awareness by 60%", "Managed $2M marketing budget"],
            skills_used=["Marketing Strategy", "Analytics", "Team Leadership"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(job3)
        
        # User 3: Inexperienced - With goal
        user3 = User(
            email="alex.jones@example.com",
            username="alexjones",
            user_group=UserGroup.INEXPERIENCED_WITH_GOAL,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user3)
        db.flush()
        
        profile3 = UserProfile(
            user_id=user3.id,
            career_goals="Become a full-stack web developer",
            short_term_goals="Complete bootcamp and build portfolio",
            long_term_goals="Work at a top tech company as a senior developer",
            cv_content="Recent graduate looking to start career in web development...",
            age=22,
            birth_country="United Kingdom",
            birth_city="London",
            current_location="London, UK",
            desired_job_locations=["London", "Remote", "Manchester"],
            languages=[{"name": "English", "proficiency": "Native"}],
            culture="British",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(profile3)
        
        course2 = Course(
            user_id=user3.id,
            course_name="Full Stack Web Development Bootcamp",
            institution="Code Academy",
            provider="Code Academy",
            description="Intensive 12-week bootcamp covering React, Node.js, and databases",
            completion_date=date(2024, 6, 1),
            skills_learned=["React", "Node.js", "MongoDB", "Express"],
            duration_hours=480.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(course2)
        
        academic2 = AcademicRecord(
            user_id=user3.id,
            institution_name="University of London",
            degree="Bachelor of Arts",
            field_of_study="Media Studies",
            start_date=date(2020, 9, 1),
            end_date=date(2023, 6, 1),
            gpa=3.5,
            location="London, UK",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(academic2)
        
        # User 4: Inexperienced - No goal
        user4 = User(
            email="maria.garcia@example.com",
            username="mariagarcia",
            user_group=UserGroup.INEXPERIENCED_NO_GOAL,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user4)
        db.flush()
        
        profile4 = UserProfile(
            user_id=user4.id,
            career_goals="Explore different career paths and find my passion",
            age=21,
            birth_country="Spain",
            birth_city="Madrid",
            current_location="Madrid, Spain",
            desired_job_locations=["Madrid", "Barcelona", "Remote"],
            languages=[{"name": "Spanish", "proficiency": "Native"}, {"name": "English", "proficiency": "Advanced"}],
            culture="Spanish",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(profile4)
        
        academic3 = AcademicRecord(
            user_id=user4.id,
            institution_name="Universidad Complutense de Madrid",
            degree="Bachelor's Degree",
            field_of_study="Business Administration",
            start_date=date(2021, 9, 1),
            end_date=date(2024, 6, 1),
            gpa=3.6,
            location="Madrid, Spain",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(academic3)
        
        # Generate some mock products for user1
        product1 = GeneratedProduct(
            user_id=user1.id,
            product_type=ProductType.CV,
            content={
                "version": "v2",
                "sections": ["Experience", "Education", "Skills"],
                "format": "PDF",
            },
            version=2,
            is_active=True,
            generated_at=datetime.utcnow(),
            model_used="llama-3.1-8b-instant",
            prompt_used="Generate an updated CV for a senior software engineer",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(product1)
        
        product2 = GeneratedProduct(
            user_id=user1.id,
            product_type=ProductType.CAREER_PLAN_1Y,
            content={
                "goals": ["Complete AWS certification", "Lead 2 major projects"],
                "milestones": ["Q1: Certification", "Q2: Project 1", "Q3: Project 2"],
            },
            version=1,
            is_active=True,
            generated_at=datetime.utcnow(),
            model_used="llama-3.1-8b-instant",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(product2)
        
        product3 = GeneratedProduct(
            user_id=user2.id,
            product_type=ProductType.SUGGESTED_COURSES,
            content={
                "courses": [
                    {"name": "Product Management Fundamentals", "provider": "Coursera"},
                    {"name": "Agile Product Management", "provider": "Udemy"},
                ],
            },
            version=1,
            is_active=True,
            generated_at=datetime.utcnow(),
            model_used="llama-3.1-8b-instant",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(product3)
        
        db.commit()
        print("✅ Database seeded successfully!")
        print(f"   - Created {4} users")
        print(f"   - Created {4} user profiles")
        print(f"   - Created {3} job experiences")
        print(f"   - Created {2} courses")
        print(f"   - Created {3} academic records")
        print(f"   - Created {3} generated products")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

