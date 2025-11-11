from abc import ABC, abstractmethod
from typing import List, Optional
from career_navigator.domain.models.user import User as DomainUser


class UserRepository(ABC):
    @abstractmethod
    def create(self, user: DomainUser) -> DomainUser:
        """Create a new user."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[DomainUser]:
        """Get user by ID."""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[DomainUser]:
        """Get user by email."""
        pass

    @abstractmethod
    def get_all(self) -> List[DomainUser]:
        """Get all users."""
        pass

    @abstractmethod
    def update(self, user: DomainUser) -> DomainUser:
        """Update an existing user."""
        pass

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Delete a user by ID."""
        pass

