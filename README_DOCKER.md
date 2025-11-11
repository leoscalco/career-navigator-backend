# Docker Setup for Career Navigator

## Quick Start

### 1. Start PostgreSQL with Docker Compose

```bash
docker-compose up -d
```

This will start PostgreSQL on port **5433** (mapped from container port 5432).

### 2. Verify Database is Running

```bash
docker-compose ps
```

You should see the `career_navigator_db` container running.

### 3. Run Database Migrations

```bash
poetry run alembic upgrade head
```

### 4. Stop the Database

```bash
docker-compose down
```

### 5. Stop and Remove Data (Clean Slate)

```bash
docker-compose down -v
```

## Database Connection Details

- **Host:** localhost
- **Port:** 5433 (custom port, not default 5432)
- **Database:** career_navigator
- **Username:** career_navigator
- **Password:** career_navigator_password

## Connection String

```
postgresql://career_navigator:career_navigator_password@localhost:5433/career_navigator
```

## Environment Variables

Make sure your `.env` file contains:

```env
DATABASE_URL=postgresql://career_navigator:career_navigator_password@localhost:5433/career_navigator
```

## Useful Commands

### View Database Logs
```bash
docker-compose logs -f postgres
```

### Connect to Database via psql
```bash
docker-compose exec postgres psql -U career_navigator -d career_navigator
```

### Backup Database
```bash
docker-compose exec postgres pg_dump -U career_navigator career_navigator > backup.sql
```

### Restore Database
```bash
docker-compose exec -T postgres psql -U career_navigator career_navigator < backup.sql
```

## Troubleshooting

### Port Already in Use
If port 5433 is already in use, change it in `docker-compose.yml`:
```yaml
ports:
  - "5434:5432"  # Use 5434 instead
```

### Reset Database
```bash
docker-compose down -v
docker-compose up -d
poetry run alembic upgrade head
```

