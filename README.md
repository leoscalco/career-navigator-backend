# Career Navigator Backend

Backend API for Career Navigator - An AI-powered career development platform.

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Poetry
- Docker & Docker Compose

### Installation

1. **Install dependencies:**
   ```bash
   poetry install
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start PostgreSQL:**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations:**
   ```bash
   poetry run alembic upgrade head
   ```

5. **Start the development server:**
   ```bash
   poetry run uvicorn career_navigator.main:app --reload
   ```

6. **Access the API:**
   - Swagger UI: http://127.0.0.1:8000/docs
   - ReDoc: http://127.0.0.1:8000/redoc

## 📁 Project Structure

```
career_navigator/
├── api/                    # API endpoints (presentation layer)
│   ├── schemas/           # Request/response models
│   ├── career.py          # Career endpoints
│   └── health.py          # Health check endpoint
├── application/           # Application layer (use cases)
│   ├── career_service.py
│   └── health_service.py
├── domain/                # Domain layer (business logic)
│   ├── health.py
│   └── llm.py            # LLM interface
├── infrastructure/        # Infrastructure layer (adapters)
│   ├── database/         # Database models and session
│   └── llm/              # LLM implementations
├── config.py             # Configuration
└── main.py               # FastAPI application entry point
```

## 🏗️ Architecture

This project follows **Hexagonal Architecture** (Ports and Adapters):

- **Domain Layer**: Core business logic and interfaces
- **Application Layer**: Use cases and application services
- **Infrastructure Layer**: External adapters (database, LLM, APIs)
- **API Layer**: HTTP endpoints and request/response handling

## 📚 Documentation

For detailed documentation, see the [docs/](docs/) folder:

- [Docker Setup](docs/README_DOCKER.md) - PostgreSQL setup
- [Database Schema](docs/DATABASE_SCHEMA.md) - Database structure

## 🔧 Development

### Running Tests
```bash
# Coming soon
```

### Code Quality
```bash
# Coming soon
```

### Database Migrations
```bash
# Create a new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback migration
poetry run alembic downgrade -1
```

## 🌐 Environment Variables

Required environment variables (see `.env.example`):

- `LANGFUSE_PUBLIC_KEY` - Langfuse public key
- `LANGFUSE_SECRET_KEY` - Langfuse secret key
- `GROQ_API_KEY` - Groq API key
- `DATABASE_URL` - PostgreSQL connection string

## 📦 Dependencies

- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **LangChain** - LLM framework
- **Langfuse** - LLM observability
- **Groq** - LLM provider

## 🎯 Features

- ✅ Health check endpoint
- ✅ Career advice generation with LLM
- ✅ PostgreSQL database with Alembic migrations
- ✅ Docker Compose setup
- ✅ Hexagonal architecture
- ✅ Langfuse integration for LLM tracing

## 📝 License

[Add your license here]
