from fastapi import FastAPI

from career_navigator.api import health

app = FastAPI(
    title="Career Navigator API",
    description="API for Career Navigator",
    version="0.1.0",
)

app.include_router(health.router)
