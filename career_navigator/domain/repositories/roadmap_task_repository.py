from abc import ABC, abstractmethod
from typing import List, Optional
from career_navigator.domain.models.roadmap_task import RoadmapTask


class RoadmapTaskRepository(ABC):
    """Abstract repository for roadmap task data access."""

    @abstractmethod
    def create(self, task: RoadmapTask) -> RoadmapTask:
        """Create a new roadmap task."""
        pass

    @abstractmethod
    def get_by_id(self, task_id: int) -> Optional[RoadmapTask]:
        """Get a roadmap task by ID."""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> List[RoadmapTask]:
        """Get all roadmap tasks for a user."""
        pass

    @abstractmethod
    def get_by_user_and_plan(self, user_id: int, plan_type: str) -> List[RoadmapTask]:
        """Get all roadmap tasks for a user and plan type."""
        pass

    @abstractmethod
    def find_task(
        self,
        user_id: int,
        plan_type: str,
        period: str,
        task_type: str,
        task_index: int,
    ) -> Optional[RoadmapTask]:
        """Find a specific task by its identifiers."""
        pass

    @abstractmethod
    def update(self, task: RoadmapTask) -> RoadmapTask:
        """Update an existing roadmap task."""
        pass

    @abstractmethod
    def delete(self, task_id: int) -> None:
        """Delete a roadmap task."""
        pass

    @abstractmethod
    def mark_completed(
        self,
        user_id: int,
        plan_type: str,
        period: str,
        task_type: str,
        task_index: int,
    ) -> RoadmapTask:
        """Mark a task as completed."""
        pass

    @abstractmethod
    def mark_incomplete(
        self,
        user_id: int,
        plan_type: str,
        period: str,
        task_type: str,
        task_index: int,
    ) -> RoadmapTask:
        """Mark a task as incomplete."""
        pass

