"""
╔══════════════════════════════════════════════════════════╗
║            RecruitAuto AI  –  FastAPI Backend            ║
╚══════════════════════════════════════════════════════════╝

Entry point.  Run with:
    uvicorn main:app --reload --port 8000

Project structure:
    backend/
    ├── main.py              ← YOU ARE HERE (app factory)
    ├── requirements.txt
    └── app/
        ├── __init__.py      ← Package init
        ├── config.py        ← Environment variables & defaults
        ├── models.py        ← Pydantic schemas (request/response)
        ├── database.py      ← In-memory mock data store
        ├── services.py      ← Business logic (all the heavy lifting)
        └── routes.py        ← API route definitions (thin handlers)

Why this structure?
    1. models.py   → "What shape is the data?"
    2. database.py → "Where does the data live?"
    3. services.py → "What logic do we run on it?"
    4. routes.py   → "Which URL triggers which logic?"
    5. config.py   → "What knobs can I turn?"
    6. main.py     → "Glue it all together."
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config, models_db
from app.database import engine
from app.routes import router

# Create database tables
models_db.Base.metadata.create_all(bind=engine)


# ── Create Application ──────────────────────────────────────
app = FastAPI(
    title="RecruitAuto AI",
    description="AI-powered candidate screening & pipeline management API",
    version="1.0.0",
    docs_url="/docs",        # Swagger UI  → http://localhost:8000/docs
    redoc_url="/redoc",      # ReDoc       → http://localhost:8000/redoc
)


# ── Middleware ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Register Routes ────────────────────────────────────────
app.include_router(router)


# ── Health Check ────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    """Health-check endpoint."""
    return {
        "service": "RecruitAuto AI API",
        "status": "healthy",
        "version": "1.0.0",
        "docs": "/docs",
    }
