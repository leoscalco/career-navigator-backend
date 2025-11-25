from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from career_navigator.api import health, career
from career_navigator.api import (
    auth,
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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Health and Career endpoints
app.include_router(health.router)
app.include_router(career.router)

# Authentication endpoints
app.include_router(auth.router)

# CRUD endpoints organized by table
app.include_router(users.router)
app.include_router(profiles.router)
app.include_router(job_experiences.router)
app.include_router(courses.router)
app.include_router(academics.router)
app.include_router(products.router)

# Workflow endpoints
app.include_router(workflow.router)
