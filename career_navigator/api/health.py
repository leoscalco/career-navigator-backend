from fastapi import APIRouter

from career_navigator.application.health_service import HealthService
from career_navigator.domain.health import Health

router = APIRouter()
health_service = HealthService()


@router.get("/health", response_model=Health, tags=["Health"])
def health_check() -> Health:
    """
    Checks the health of the application.
    """
    return health_service.get_health()
