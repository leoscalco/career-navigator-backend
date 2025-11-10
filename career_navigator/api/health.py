from fastapi import APIRouter

from career_navigator.application.health_service import HealthService
from career_navigator.api.schemas.health import HealthResponse

router = APIRouter()
health_service = HealthService()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check() -> HealthResponse:
    """
    Checks the health of the application.
    """
    health = health_service.get_health()
    return HealthResponse(status=health.status)
