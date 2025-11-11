# Career Navigator Backend Documentation

Welcome to the Career Navigator Backend documentation. This directory contains all the technical documentation for the project.

## 📚 Documentation Index

### Getting Started
- [Main README](../README.md) - Project overview and quick start guide

### Infrastructure & Setup
- [Docker Setup](README_DOCKER.md) - PostgreSQL Docker Compose setup and usage
- [Database Schema](DATABASE_SCHEMA.md) - Complete database schema documentation

### Architecture
- [Hexagonal Architecture](../ARCHITECTURE.md) - Architecture overview and patterns (coming soon)

## 🚀 Quick Links

- **API Documentation**: http://127.0.0.1:8000/docs (when server is running)
- **Database**: PostgreSQL on port 5433 (via Docker Compose)
- **Migrations**: Managed by Alembic

## 📖 Documentation Structure

```
docs/
├── README.md              # This file - documentation index
├── README_DOCKER.md      # Docker and PostgreSQL setup
└── DATABASE_SCHEMA.md    # Database schema documentation
```

## 🔧 Common Tasks

### Start Development Environment
```bash
# Start PostgreSQL
docker-compose up -d

# Run migrations
poetry run alembic upgrade head

# Start the server
poetry run uvicorn career_navigator.main:app --reload
```

### Database Management
```bash
# View database logs
docker-compose logs -f postgres

# Connect to database
docker-compose exec postgres psql -U career_navigator -d career_navigator

# Create a new migration
poetry run alembic revision --autogenerate -m "description"
```

## 📝 Contributing

When adding new documentation:
1. Place it in the `docs/` folder
2. Update this README with a link
3. Follow the existing documentation style

