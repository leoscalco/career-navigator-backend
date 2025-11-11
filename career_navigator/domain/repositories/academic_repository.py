from abc import ABC, abstractmethod
from typing import List, Optional
from career_navigator.domain.models.academic import AcademicRecord


class AcademicRepository(ABC):
    @abstractmethod
    def create(self, academic: AcademicRecord) -> AcademicRecord:
        """Create a new academic record."""
        pass

    @abstractmethod
    def get_by_id(self, academic_id: int) -> Optional[AcademicRecord]:
        """Get academic record by ID."""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> List[AcademicRecord]:
        """Get all academic records for a user."""
        pass

    @abstractmethod
    def get_all(self) -> List[AcademicRecord]:
        """Get all academic records."""
        pass

    @abstractmethod
    def update(self, academic: AcademicRecord) -> AcademicRecord:
        """Update an existing academic record."""
        pass

    @abstractmethod
    def delete(self, academic_id: int) -> bool:
        """Delete an academic record by ID."""
        pass

