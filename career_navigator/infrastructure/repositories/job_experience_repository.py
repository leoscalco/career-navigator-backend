from typing import List, Optional
from sqlalchemy.orm import Session
from career_navigator.domain.repositories.job_experience_repository import JobExperienceRepository
from career_navigator.domain.models.job_experience import JobExperience as DomainJobExperience
from career_navigator.infrastructure.database.models import JobExperience as DBJobExperience


class SQLAlchemyJobExperienceRepository(JobExperienceRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, job_experience: DomainJobExperience) -> DomainJobExperience:
        db_job = DBJobExperience(
            user_id=job_experience.user_id,
            company_name=job_experience.company_name,
            position=job_experience.position,
            description=job_experience.description,
            start_date=job_experience.start_date,
            end_date=job_experience.end_date,
            is_current=job_experience.is_current,
            location=job_experience.location,
            achievements=job_experience.achievements,
            skills_used=job_experience.skills_used,
        )
        self.db.add(db_job)
        self.db.commit()
        self.db.refresh(db_job)
        return self._to_domain(db_job)

    def get_by_id(self, job_id: int) -> Optional[DomainJobExperience]:
        db_job = self.db.query(DBJobExperience).filter(DBJobExperience.id == job_id).first()
        return self._to_domain(db_job) if db_job else None

    def get_by_user_id(self, user_id: int) -> List[DomainJobExperience]:
        db_jobs = self.db.query(DBJobExperience).filter(DBJobExperience.user_id == user_id).all()
        return [self._to_domain(j) for j in db_jobs]

    def get_all(self) -> List[DomainJobExperience]:
        db_jobs = self.db.query(DBJobExperience).all()
        return [self._to_domain(j) for j in db_jobs]

    def update(self, job_experience: DomainJobExperience) -> DomainJobExperience:
        db_job = self.db.query(DBJobExperience).filter(DBJobExperience.id == job_experience.id).first()
        if not db_job:
            raise ValueError(f"Job experience with id {job_experience.id} not found")
        
        db_job.company_name = job_experience.company_name
        db_job.position = job_experience.position
        db_job.description = job_experience.description
        db_job.start_date = job_experience.start_date
        db_job.end_date = job_experience.end_date
        db_job.is_current = job_experience.is_current
        db_job.location = job_experience.location
        db_job.achievements = job_experience.achievements
        db_job.skills_used = job_experience.skills_used
        
        self.db.commit()
        self.db.refresh(db_job)
        return self._to_domain(db_job)

    def delete(self, job_id: int) -> bool:
        db_job = self.db.query(DBJobExperience).filter(DBJobExperience.id == job_id).first()
        if not db_job:
            return False
        
        self.db.delete(db_job)
        self.db.commit()
        return True

    def _to_domain(self, db_job: DBJobExperience) -> DomainJobExperience:
        return DomainJobExperience(
            id=db_job.id,
            user_id=db_job.user_id,
            company_name=db_job.company_name,
            position=db_job.position,
            description=db_job.description,
            start_date=db_job.start_date,
            end_date=db_job.end_date,
            is_current=db_job.is_current,
            location=db_job.location,
            achievements=db_job.achievements,
            skills_used=db_job.skills_used,
            created_at=db_job.created_at,
            updated_at=db_job.updated_at,
        )

