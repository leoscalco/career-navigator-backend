from abc import ABC, abstractmethod
from typing import List, Optional
from career_navigator.domain.models.job_experience import JobExperience


class JobExperienceRepository(ABC):
    @abstractmethod
    def create(self, job_experience: JobExperience) -> JobExperience:
        """Create a new job experience."""
        pass

    @abstractmethod
    def get_by_id(self, job_id: int) -> Optional[JobExperience]:
        """Get job experience by ID."""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> List[JobExperience]:
        """Get all job experiences for a user."""
        pass

    @abstractmethod
    def get_all(self) -> List[JobExperience]:
        """Get all job experiences."""
        pass

    @abstractmethod
    def update(self, job_experience: JobExperience) -> JobExperience:
        """Update an existing job experience."""
        pass

    @abstractmethod
    def delete(self, job_id: int) -> bool:
        """Delete a job experience by ID."""
        pass

