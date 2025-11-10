from pydantic import BaseModel


class CareerAdviceRequest(BaseModel):
    topic: str


class CareerAdviceResponse(BaseModel):
    advice: str

