from abc import ABC, abstractmethod
from typing import List, Optional
from career_navigator.domain.models.course import Course


class CourseRepository(ABC):
    @abstractmethod
    def create(self, course: Course) -> Course:
        """Create a new course."""
        pass

    @abstractmethod
    def get_by_id(self, course_id: int) -> Optional[Course]:
        """Get course by ID."""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> List[Course]:
        """Get all courses for a user."""
        pass

    @abstractmethod
    def get_all(self) -> List[Course]:
        """Get all courses."""
        pass

    @abstractmethod
    def update(self, course: Course) -> Course:
        """Update an existing course."""
        pass

    @abstractmethod
    def delete(self, course_id: int) -> bool:
        """Delete a course by ID."""
        pass

