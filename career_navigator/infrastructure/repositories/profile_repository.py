from typing import List, Optional
from sqlalchemy.orm import Session
from career_navigator.domain.repositories.profile_repository import ProfileRepository
from career_navigator.domain.models.profile import UserProfile as DomainProfile
from career_navigator.infrastructure.database.models import UserProfile as DBProfile


class SQLAlchemyProfileRepository(ProfileRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, profile: DomainProfile) -> DomainProfile:
        # Ensure career_goal_type defaults to CONTINUE_PATH if not set
        career_goal_type = profile.career_goal_type
        if not career_goal_type:
            from career_navigator.domain.models.career_goal_type import CareerGoalType
            career_goal_type = CareerGoalType.CONTINUE_PATH
        
        db_profile = DBProfile(
            user_id=profile.user_id,
            is_draft=profile.is_draft,
            is_validated=profile.is_validated,
            career_goals=profile.career_goals,
            career_goal_type=career_goal_type.value if hasattr(career_goal_type, 'value') else career_goal_type,
            short_term_goals=profile.short_term_goals,
            long_term_goals=profile.long_term_goals,
            job_search_locations=profile.job_search_locations,
            cv_content=profile.cv_content,
            linkedin_profile_url=profile.linkedin_profile_url,
            linkedin_profile_data=profile.linkedin_profile_data,
            life_profile=profile.life_profile,
            age=profile.age,
            birth_country=profile.birth_country,
            birth_city=profile.birth_city,
            current_location=profile.current_location,
            desired_job_locations=profile.desired_job_locations,
            languages=profile.languages,
            culture=profile.culture,
            hobbies=profile.hobbies,
            additional_info=profile.additional_info,
        )
        self.db.add(db_profile)
        self.db.commit()
        self.db.refresh(db_profile)
        return self._to_domain(db_profile)

    def get_by_id(self, profile_id: int) -> Optional[DomainProfile]:
        db_profile = self.db.query(DBProfile).filter(DBProfile.id == profile_id).first()
        return self._to_domain(db_profile) if db_profile else None

    def get_by_user_id(self, user_id: int) -> Optional[DomainProfile]:
        db_profile = self.db.query(DBProfile).filter(DBProfile.user_id == user_id).first()
        return self._to_domain(db_profile) if db_profile else None

    def get_all(self) -> List[DomainProfile]:
        db_profiles = self.db.query(DBProfile).all()
        return [self._to_domain(p) for p in db_profiles]

    def update(self, profile: DomainProfile) -> DomainProfile:
        db_profile = self.db.query(DBProfile).filter(DBProfile.id == profile.id).first()
        if not db_profile:
            raise ValueError(f"Profile with id {profile.id} not found")
        
        db_profile.is_draft = profile.is_draft
        db_profile.is_validated = profile.is_validated
        db_profile.career_goals = profile.career_goals
        if profile.career_goal_type is not None:
            db_profile.career_goal_type = profile.career_goal_type.value if hasattr(profile.career_goal_type, 'value') else profile.career_goal_type
        db_profile.short_term_goals = profile.short_term_goals
        db_profile.long_term_goals = profile.long_term_goals
        if profile.job_search_locations is not None:
            db_profile.job_search_locations = profile.job_search_locations
        db_profile.cv_content = profile.cv_content
        db_profile.linkedin_profile_url = profile.linkedin_profile_url
        db_profile.linkedin_profile_data = profile.linkedin_profile_data
        db_profile.life_profile = profile.life_profile
        db_profile.age = profile.age
        db_profile.birth_country = profile.birth_country
        db_profile.birth_city = profile.birth_city
        db_profile.current_location = profile.current_location
        db_profile.desired_job_locations = profile.desired_job_locations
        db_profile.languages = profile.languages
        db_profile.culture = profile.culture
        db_profile.hobbies = profile.hobbies
        db_profile.additional_info = profile.additional_info
        
        self.db.commit()
        self.db.refresh(db_profile)
        return self._to_domain(db_profile)

    def delete(self, profile_id: int) -> bool:
        db_profile = self.db.query(DBProfile).filter(DBProfile.id == profile_id).first()
        if not db_profile:
            return False
        
        self.db.delete(db_profile)
        self.db.commit()
        return True

    def _to_domain(self, db_profile: DBProfile) -> DomainProfile:
        from career_navigator.domain.models.career_goal_type import CareerGoalType
        
        # Convert career_goal_type from DB enum to domain enum
        career_goal_type = CareerGoalType.CONTINUE_PATH  # Default
        if db_profile.career_goal_type:
            try:
                career_goal_type = CareerGoalType(db_profile.career_goal_type)
            except (ValueError, AttributeError):
                career_goal_type = CareerGoalType.CONTINUE_PATH
        
        return DomainProfile(
            id=db_profile.id,
            user_id=db_profile.user_id,
            is_draft=db_profile.is_draft,
            is_validated=db_profile.is_validated,
            career_goals=db_profile.career_goals,
            career_goal_type=career_goal_type,
            short_term_goals=db_profile.short_term_goals,
            long_term_goals=db_profile.long_term_goals,
            job_search_locations=db_profile.job_search_locations,
            cv_content=db_profile.cv_content,
            linkedin_profile_url=db_profile.linkedin_profile_url,
            linkedin_profile_data=db_profile.linkedin_profile_data,
            life_profile=db_profile.life_profile,
            age=db_profile.age,
            birth_country=db_profile.birth_country,
            birth_city=db_profile.birth_city,
            current_location=db_profile.current_location,
            desired_job_locations=db_profile.desired_job_locations,
            languages=db_profile.languages,
            culture=db_profile.culture,
            hobbies=db_profile.hobbies,
            additional_info=db_profile.additional_info,
            created_at=db_profile.created_at,
            updated_at=db_profile.updated_at,
        )

