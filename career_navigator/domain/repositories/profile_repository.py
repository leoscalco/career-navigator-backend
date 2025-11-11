from abc import ABC, abstractmethod
from typing import List, Optional
from career_navigator.domain.models.profile import UserProfile


class ProfileRepository(ABC):
    @abstractmethod
    def create(self, profile: UserProfile) -> UserProfile:
        """Create a new user profile."""
        pass

    @abstractmethod
    def get_by_id(self, profile_id: int) -> Optional[UserProfile]:
        """Get profile by ID."""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> Optional[UserProfile]:
        """Get profile by user ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[UserProfile]:
        """Get all profiles."""
        pass

    @abstractmethod
    def update(self, profile: UserProfile) -> UserProfile:
        """Update an existing profile."""
        pass

    @abstractmethod
    def delete(self, profile_id: int) -> bool:
        """Delete a profile by ID."""
        pass

