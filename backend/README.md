# RecruitAuto AI – Backend

FastAPI backend for AI-powered candidate screening.

## Quick Start

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open Swagger docs → [http://localhost:8000/docs](http://localhost:8000/docs)

## Project Structure

```
backend/
├── main.py              # App factory — creates FastAPI instance, adds middleware, registers routes
├── requirements.txt     # Python dependencies
└── app/
    ├── __init__.py      # Package marker
    ├── config.py        # All settings & environment variables
    ├── models.py        # Pydantic schemas (request/response validation)
    ├── database.py      # Mock data store (swap for real DB later)
    ├── services.py      # Business logic — the "brain" of the app
    └── routes.py        # API endpoints — thin wrappers around services
```

## How to Read the Code

| Start here | What you'll learn |
|---|---|
| `main.py` | How the app is assembled |
| `models.py` | What data shapes the API uses |
| `routes.py` | Which URLs exist and what they accept |
| `services.py` | How each feature actually works |
| `database.py` | Where mock data comes from |
| `config.py` | What settings you can change |

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/` | Health check |
| `GET` | `/api/stats` | Dashboard summary |
| `GET` | `/api/candidates` | List all candidates |
| `GET` | `/api/candidates/{id}` | Single candidate detail |
| `POST` | `/api/upload-resume` | Upload resume (multipart form) |
| `PATCH` | `/api/candidates/{id}/archive` | Archive a candidate |

## Swapping to a Real Database

1. Replace the `database` list in `database.py` with ORM queries (SQLAlchemy, Tortoise, etc.)
2. Update functions in `services.py` to query the DB
3. **No changes needed** in `routes.py` or `main.py`!

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | CORS origins (comma-separated) |
| `MAX_UPLOAD_SIZE_MB` | `10` | Max resume file size |
| `SCREENING_DELAY_SECONDS` | `2.0` | Simulated AI processing time |
