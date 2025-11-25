from typing import List, Optional
from sqlalchemy.orm import Session
from career_navigator.domain.repositories.user_repository import UserRepository
from career_navigator.domain.models.user import User as DomainUser
from career_navigator.infrastructure.database.models import User as DBUser


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, user: DomainUser) -> DomainUser:
        db_user = DBUser(
            email=user.email,
            username=user.username,
            user_group=user.user_group.value,
            password_hash=user.password_hash,
            is_active=user.is_active if hasattr(user, 'is_active') else True,
            is_verified=user.is_verified if hasattr(user, 'is_verified') else False,
            oauth_provider=user.oauth_provider if hasattr(user, 'oauth_provider') else None,
            oauth_provider_id=user.oauth_provider_id if hasattr(user, 'oauth_provider_id') else None,
            oauth_access_token=user.oauth_access_token if hasattr(user, 'oauth_access_token') else None,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return self._to_domain(db_user)

    def get_by_id(self, user_id: int) -> Optional[DomainUser]:
        db_user = self.db.query(DBUser).filter(DBUser.id == user_id).first()
        return self._to_domain(db_user) if db_user else None

    def get_by_email(self, email: str) -> Optional[DomainUser]:
        db_user = self.db.query(DBUser).filter(DBUser.email == email).first()
        return self._to_domain(db_user) if db_user else None

    def get_all(self) -> List[DomainUser]:
        db_users = self.db.query(DBUser).all()
        return [self._to_domain(u) for u in db_users]

    def update(self, user: DomainUser) -> DomainUser:
        db_user = self.db.query(DBUser).filter(DBUser.id == user.id).first()
        if not db_user:
            raise ValueError(f"User with id {user.id} not found")
        
        db_user.email = user.email
        db_user.username = user.username
        db_user.user_group = user.user_group.value
        
        self.db.commit()
        self.db.refresh(db_user)
        return self._to_domain(db_user)

    def delete(self, user_id: int) -> bool:
        db_user = self.db.query(DBUser).filter(DBUser.id == user_id).first()
        if not db_user:
            return False
        
        self.db.delete(db_user)
        self.db.commit()
        return True

    def _to_domain(self, db_user: DBUser) -> DomainUser:
        from career_navigator.domain.models.user_group import UserGroup
        
        return DomainUser(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            user_group=UserGroup(db_user.user_group),
            password_hash=db_user.password_hash,
            is_active=db_user.is_active,
            is_verified=db_user.is_verified,
            oauth_provider=db_user.oauth_provider,
            oauth_provider_id=db_user.oauth_provider_id,
            oauth_access_token=db_user.oauth_access_token,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
        )

