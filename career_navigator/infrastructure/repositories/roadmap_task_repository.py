from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from career_navigator.domain.models.roadmap_task import RoadmapTask
from career_navigator.domain.repositories.roadmap_task_repository import RoadmapTaskRepository
from career_navigator.infrastructure.database.models import RoadmapTask as RoadmapTaskModel


class SQLAlchemyRoadmapTaskRepository(RoadmapTaskRepository):
    """SQLAlchemy implementation of RoadmapTaskRepository."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, task: RoadmapTask) -> RoadmapTask:
        db_task = RoadmapTaskModel(
            user_id=task.user_id,
            product_id=task.product_id,
            plan_type=task.plan_type,
            period=task.period,
            task_type=task.task_type,
            task_content=task.task_content,
            task_index=task.task_index,
            is_completed=task.is_completed,
            completed_at=task.completed_at,
        )
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return RoadmapTask.model_validate(db_task)

    def get_by_id(self, task_id: int) -> Optional[RoadmapTask]:
        db_task = self.db.query(RoadmapTaskModel).filter(RoadmapTaskModel.id == task_id).first()
        return RoadmapTask.model_validate(db_task) if db_task else None

    def get_by_user_id(self, user_id: int) -> List[RoadmapTask]:
        db_tasks = self.db.query(RoadmapTaskModel).filter(RoadmapTaskModel.user_id == user_id).all()
        return [RoadmapTask.model_validate(task) for task in db_tasks]

    def get_by_user_and_plan(self, user_id: int, plan_type: str) -> List[RoadmapTask]:
        db_tasks = (
            self.db.query(RoadmapTaskModel)
            .filter(RoadmapTaskModel.user_id == user_id, RoadmapTaskModel.plan_type == plan_type)
            .all()
        )
        return [RoadmapTask.model_validate(task) for task in db_tasks]

    def find_task(
        self,
        user_id: int,
        plan_type: str,
        period: str,
        task_type: str,
        task_index: int,
    ) -> Optional[RoadmapTask]:
        db_task = (
            self.db.query(RoadmapTaskModel)
            .filter(
                RoadmapTaskModel.user_id == user_id,
                RoadmapTaskModel.plan_type == plan_type,
                RoadmapTaskModel.period == period,
                RoadmapTaskModel.task_type == task_type,
                RoadmapTaskModel.task_index == task_index,
            )
            .first()
        )
        return RoadmapTask.model_validate(db_task) if db_task else None

    def update(self, task: RoadmapTask) -> RoadmapTask:
        db_task = self.db.query(RoadmapTaskModel).filter(RoadmapTaskModel.id == task.id).first()
        if not db_task:
            raise ValueError(f"Roadmap task {task.id} not found")

        db_task.is_completed = task.is_completed
        db_task.completed_at = task.completed_at
        db_task.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(db_task)
        return RoadmapTask.model_validate(db_task)

    def delete(self, task_id: int) -> None:
        db_task = self.db.query(RoadmapTaskModel).filter(RoadmapTaskModel.id == task_id).first()
        if db_task:
            self.db.delete(db_task)
            self.db.commit()

    def mark_completed(
        self,
        user_id: int,
        plan_type: str,
        period: str,
        task_type: str,
        task_index: int,
    ) -> RoadmapTask:
        task = self.find_task(user_id, plan_type, period, task_type, task_index)
        if not task:
            # Create the task if it doesn't exist
            task = RoadmapTask(
                user_id=user_id,
                plan_type=plan_type,
                period=period,
                task_type=task_type,
                task_index=task_index,
                task_content="",  # Will be populated when syncing
                is_completed=True,
                completed_at=datetime.utcnow(),
            )
            return self.create(task)
        else:
            task.is_completed = True
            task.completed_at = datetime.utcnow()
            return self.update(task)

    def mark_incomplete(
        self,
        user_id: int,
        plan_type: str,
        period: str,
        task_type: str,
        task_index: int,
    ) -> RoadmapTask:
        task = self.find_task(user_id, plan_type, period, task_type, task_index)
        if not task:
            raise ValueError("Task not found")
        task.is_completed = False
        task.completed_at = None
        return self.update(task)

