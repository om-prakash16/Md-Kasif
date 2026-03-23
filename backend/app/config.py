"""
RecruitAuto AI – Backend Configuration
=======================================
All app-level settings live here. Uses environment variables
with sensible defaults so the app runs out-of-the-box.
"""

import os


# --- Server ---
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))

# --- CORS ---
ALLOWED_ORIGINS: list[str] = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001"
).split(",")

# --- Upload ---
ALLOWED_EXTENSIONS: set[str] = {".pdf", ".docx", ".doc", ".txt"}
MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))

# --- Database ---
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./recruitauto.db")

# --- Auth ---
JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-key-change-me-in-production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

# --- AI Screening (simulated) ---
SCREENING_DELAY_SECONDS: float = float(os.getenv("SCREENING_DELAY_SECONDS", "1.0"))
