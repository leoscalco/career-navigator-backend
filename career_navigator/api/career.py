from fastapi import APIRouter
from career_navigator.application.career_service import CareerService
from career_navigator.infrastructure.llm.groq_adapter import GroqAdapter
from career_navigator.api.schemas.career import (
    CareerAdviceRequest,
    CareerAdviceResponse,
)

router = APIRouter()

# Lazy initialization to avoid errors when API keys are not set
_groq_adapter = None
_career_service = None


def get_career_service() -> CareerService:
    global _career_service, _groq_adapter
    if _career_service is None:
        _groq_adapter = GroqAdapter()
        _career_service = CareerService(llm=_groq_adapter)
    return _career_service


@router.post(
    "/career/advice", response_model=CareerAdviceResponse, tags=["Career"]
)
def get_career_advice(request: CareerAdviceRequest) -> CareerAdviceResponse:
    """
    Get career advice on a specific topic.
    """
    career_service = get_career_service()
    advice = career_service.get_career_advice(request.topic)
    return CareerAdviceResponse(advice=advice)
