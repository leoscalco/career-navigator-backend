from typing import List, Optional
from sqlalchemy.orm import Session
from career_navigator.domain.repositories.academic_repository import AcademicRepository
from career_navigator.domain.models.academic import AcademicRecord as DomainAcademic
from career_navigator.infrastructure.database.models import AcademicRecord as DBAcademic


class SQLAlchemyAcademicRepository(AcademicRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, academic: DomainAcademic) -> DomainAcademic:
        db_academic = DBAcademic(
            user_id=academic.user_id,
            institution_name=academic.institution_name,
            degree=academic.degree,
            field_of_study=academic.field_of_study,
            start_date=academic.start_date,
            end_date=academic.end_date,
            gpa=academic.gpa,
            honors=academic.honors,
            description=academic.description,
            location=academic.location,
        )
        self.db.add(db_academic)
        self.db.commit()
        self.db.refresh(db_academic)
        return self._to_domain(db_academic)

    def get_by_id(self, academic_id: int) -> Optional[DomainAcademic]:
        db_academic = self.db.query(DBAcademic).filter(DBAcademic.id == academic_id).first()
        return self._to_domain(db_academic) if db_academic else None

    def get_by_user_id(self, user_id: int) -> List[DomainAcademic]:
        db_academics = self.db.query(DBAcademic).filter(DBAcademic.user_id == user_id).all()
        return [self._to_domain(a) for a in db_academics]

    def get_all(self) -> List[DomainAcademic]:
        db_academics = self.db.query(DBAcademic).all()
        return [self._to_domain(a) for a in db_academics]

    def update(self, academic: DomainAcademic) -> DomainAcademic:
        db_academic = self.db.query(DBAcademic).filter(DBAcademic.id == academic.id).first()
        if not db_academic:
            raise ValueError(f"Academic record with id {academic.id} not found")
        
        db_academic.institution_name = academic.institution_name
        db_academic.degree = academic.degree
        db_academic.field_of_study = academic.field_of_study
        db_academic.start_date = academic.start_date
        db_academic.end_date = academic.end_date
        db_academic.gpa = academic.gpa
        db_academic.honors = academic.honors
        db_academic.description = academic.description
        db_academic.location = academic.location
        
        self.db.commit()
        self.db.refresh(db_academic)
        return self._to_domain(db_academic)

    def delete(self, academic_id: int) -> bool:
        db_academic = self.db.query(DBAcademic).filter(DBAcademic.id == academic_id).first()
        if not db_academic:
            return False
        
        self.db.delete(db_academic)
        self.db.commit()
        return True

    def _to_domain(self, db_academic: DBAcademic) -> DomainAcademic:
        return DomainAcademic(
            id=db_academic.id,
            user_id=db_academic.user_id,
            institution_name=db_academic.institution_name,
            degree=db_academic.degree,
            field_of_study=db_academic.field_of_study,
            start_date=db_academic.start_date,
            end_date=db_academic.end_date,
            gpa=db_academic.gpa,
            honors=db_academic.honors,
            description=db_academic.description,
            location=db_academic.location,
            created_at=db_academic.created_at,
            updated_at=db_academic.updated_at,
        )

