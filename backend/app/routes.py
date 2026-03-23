from __future__ import annotations
import os
from typing import List
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import config, services, auth, models_db, database
from app.models import (
    ActionResponse,
    CandidateOut,
    DashboardStats,
    UploadResponse,
    UserCreate,
    UserOut,
    Token,
    JobCreate,
    JobOut,
    RecruiterCreate,
)

router = APIRouter(prefix="/api")

# ── Auth ────────────────────────────────────────────────────
@router.post("/auth/signup", response_model=Token)
def signup(user_in: UserCreate, db: Session = Depends(database.get_db)):
    """Register a new user and company."""
    existing_user = db.query(models_db.User).filter(models_db.User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    company = models_db.Company(name=user_in.company_name)
    db.add(company)
    db.commit()
    db.refresh(company)
    
    hashed_pass = auth.get_password_hash(user_in.password)
    new_user = models_db.User(
        email=user_in.email,
        hashed_password=hashed_pass,
        full_name=user_in.full_name,
        role=user_in.role,
        company_id=company.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = auth.create_access_token(data={"sub": new_user.email})
    return {
        "accessToken": access_token,
        "tokenType": "bearer",
        "user": new_user
    }

@router.post("/auth/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    """Login with email and password."""
    user = db.query(models_db.User).filter(models_db.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return {
        "accessToken": access_token,
        "tokenType": "bearer",
        "user": user
    }

@router.get("/auth/me", response_model=UserOut)
def get_me(current_user: models_db.User = Depends(auth.get_current_active_user)):
    return current_user

# ── Dashboard ───────────────────────────────────────────────
@router.get("/stats", response_model=DashboardStats)
def get_stats(
    db: Session = Depends(database.get_db),
    current_user: models_db.User = Depends(auth.get_current_active_user)
):
    return services.compute_stats(db, current_user.company_id)

# ── Recruiters ──────────────────────────────────────────────
@router.get("/recruiters", response_model=List[UserOut])
def list_recruiters(
    db: Session = Depends(database.get_db),
    current_user: models_db.User = Depends(auth.get_current_active_user)
):
    return services.list_recruiters(db, current_user.company_id)

@router.post("/recruiters", response_model=UserOut)
def create_recruiter(
    recruiter_in: RecruiterCreate,
    db: Session = Depends(database.get_db),
    current_user: models_db.User = Depends(auth.get_current_active_user)
):
    existing = db.query(models_db.User).filter(models_db.User.email == recruiter_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    return services.create_recruiter(db, recruiter_in, current_user.company_id)

# ── Jobs ────────────────────────────────────────────────────
@router.get("/jobs", response_model=List[JobOut])
def list_jobs(
    db: Session = Depends(database.get_db),
    current_user: models_db.User = Depends(auth.get_current_active_user)
):
    return services.list_jobs(db, current_user.company_id)

@router.post("/jobs", response_model=JobOut)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(database.get_db),
    current_user: models_db.User = Depends(auth.check_role("admin"))
):
    return services.create_job(db, job_in, current_user.company_id)

# ── Candidates ──────────────────────────────────────────────
@router.get("/candidates", response_model=List[CandidateOut])
def list_candidates(
    db: Session = Depends(database.get_db),
    current_user: models_db.User = Depends(auth.get_current_active_user)
):
    return services.list_candidates(db, current_user.company_id)

@router.get("/candidates/{candidate_id}", response_model=CandidateOut)
def get_candidate(
    candidate_id: int,
    db: Session = Depends(database.get_db),
    current_user: models_db.User = Depends(auth.get_current_active_user)
):
    candidate = services.get_candidate_by_id(db, candidate_id)
    if not candidate or (candidate.job.company_id != current_user.company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

@router.post("/upload-resume", response_model=UploadResponse)
async def upload_resume(
    jobId: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models_db.User = Depends(auth.get_current_active_user)
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    # Check if job belongs to company
    job = db.query(models_db.Job).filter(models_db.Job.id == jobId, models_db.Job.company_id == current_user.company_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    file_bytes = await file.read()
    return await services.process_resume_for_job(db, jobId, file.filename or "resume.pdf", file_bytes)


@router.post("/upload-resumes-bulk")
async def upload_resumes_bulk(
    jobId: int = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(database.get_db),
    current_user: models_db.User = Depends(auth.get_current_active_user)
):
    """Upload multiple resumes at once for a single job."""
    job = db.query(models_db.Job).filter(models_db.Job.id == jobId, models_db.Job.company_id == current_user.company_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    results = []
    for file in files:
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in config.ALLOWED_EXTENSIONS:
            results.append({"filename": file.filename, "success": False, "message": f"Unsupported type: {ext}"})
            continue
        try:
            file_bytes = await file.read()
            result = await services.process_resume_for_job(db, jobId, file.filename or "resume.pdf", file_bytes)
            results.append({"filename": file.filename, "success": True, "message": result.message, "candidateId": result.candidate_id, "candidateName": result.candidate_name})
        except Exception as e:
            results.append({"filename": file.filename, "success": False, "message": str(e)})
    
    return {"results": results, "totalProcessed": len(results)}


@router.patch("/candidates/{candidate_id}/archive", response_model=ActionResponse)
def archive_candidate(
    candidate_id: int,
    db: Session = Depends(database.get_db),
    current_user: models_db.User = Depends(auth.get_current_active_user)
):
    return services.archive_candidate(db, candidate_id)
