from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from career_navigator.config import settings
from career_navigator.infrastructure.database.base import Base

engine = create_engine(settings.DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

