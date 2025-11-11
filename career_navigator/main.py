from fastapi import FastAPI

from career_navigator.api import health, career
from career_navigator.api import (
    users,
    profiles,
    job_experiences,
    courses,
    academics,
    products,
    workflow,
)

app = FastAPI(
    title="Career Navigator API",
    description="API for Career Navigator",
    version="0.1.0",
)

# Health and Career endpoints
app.include_router(health.router)
app.include_router(career.router)

# CRUD endpoints organized by table
app.include_router(users.router)
app.include_router(profiles.router)
app.include_router(job_experiences.router)
app.include_router(courses.router)
app.include_router(academics.router)
app.include_router(products.router)

# Workflow endpoints
app.include_router(workflow.router)
