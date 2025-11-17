from typing import List, Optional
from sqlalchemy.orm import Session
from career_navigator.domain.repositories.course_repository import CourseRepository
from career_navigator.domain.models.course import Course as DomainCourse
from career_navigator.infrastructure.database.models import Course as DBCourse


class SQLAlchemyCourseRepository(CourseRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, course: DomainCourse) -> DomainCourse:
        db_course = DBCourse(
            user_id=course.user_id,
            course_name=course.course_name,
            institution=course.institution,
            provider=course.provider,
            description=course.description,
            completion_date=course.completion_date,
            certificate_url=course.certificate_url,
            skills_learned=course.skills_learned,
            duration_hours=course.duration_hours,
        )
        self.db.add(db_course)
        self.db.commit()
        self.db.refresh(db_course)
        return self._to_domain(db_course)

    def get_by_id(self, course_id: int) -> Optional[DomainCourse]:
        db_course = self.db.query(DBCourse).filter(DBCourse.id == course_id).first()
        return self._to_domain(db_course) if db_course else None

    def get_by_user_id(self, user_id: int) -> List[DomainCourse]:
        db_courses = self.db.query(DBCourse).filter(DBCourse.user_id == user_id).all()
        return [self._to_domain(c) for c in db_courses]

    def get_all(self) -> List[DomainCourse]:
        db_courses = self.db.query(DBCourse).all()
        return [self._to_domain(c) for c in db_courses]

    def update(self, course: DomainCourse) -> DomainCourse:
        db_course = self.db.query(DBCourse).filter(DBCourse.id == course.id).first()
        if not db_course:
            raise ValueError(f"Course with id {course.id} not found")
        
        db_course.course_name = course.course_name
        db_course.institution = course.institution
        db_course.provider = course.provider
        db_course.description = course.description
        db_course.completion_date = course.completion_date
        db_course.certificate_url = course.certificate_url
        db_course.skills_learned = course.skills_learned
        db_course.duration_hours = course.duration_hours
        
        self.db.commit()
        self.db.refresh(db_course)
        return self._to_domain(db_course)

    def delete(self, course_id: int) -> bool:
        db_course = self.db.query(DBCourse).filter(DBCourse.id == course_id).first()
        if not db_course:
            return False
        
        self.db.delete(db_course)
        self.db.commit()
        return True

    def _to_domain(self, db_course: DBCourse) -> DomainCourse:
        return DomainCourse(
            id=db_course.id,
            user_id=db_course.user_id,
            course_name=db_course.course_name,
            institution=db_course.institution,
            provider=db_course.provider,
            description=db_course.description,
            completion_date=db_course.completion_date,
            certificate_url=db_course.certificate_url,
            skills_learned=db_course.skills_learned,
            duration_hours=db_course.duration_hours,
            created_at=db_course.created_at,
            updated_at=db_course.updated_at,
        )

