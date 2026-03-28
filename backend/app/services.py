from __future__ import annotations
import asyncio
import random
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app import config, models_db, models
# ── Stats ──────────────────────────────────────────────────
def compute_stats(db: Session, company_id: int) -> models.DashboardStats:
    """Compute aggregate stats for a specific company."""
    # This is a simplified version, in a real app you'd use optimized SQL queries
    candidates = db.query(models_db.Candidate).join(models_db.Job).filter(models_db.Job.company_id == company_id).all()
    
    active = [c for c in candidates if c.status != "Archived"]
    interested = [c for c in candidates if c.status == "Interested"]
    mismatched = [c for c in candidates if c.status == "Rate Mismatch"]
    
    # Mock response time for now
    avg_time = "12 min" if active else "—"
    
    return models.DashboardStats(
        totalScreened=len(active),
        interested=len(interested),
        rateMismatch=len(mismatched),
        avgResponseTime=avg_time,
    )

# ── Recruiters ──────────────────────────────────────────────
def list_recruiters(db: Session, company_id: int):
    recruiters = db.query(models_db.User).filter(
        models_db.User.company_id == company_id,
        models_db.User.role == "recruiter"
    ).all()
    # Mocking jobs_count for now
    for r in recruiters:
        r.jobs_count = random.randint(0, 5)
    return recruiters

def create_recruiter(db: Session, recruiter_in: models.RecruiterCreate, company_id: int):
    from app import auth
    # Quick dirty hash for mock
    new_user = models_db.User(
        email=recruiter_in.email,
        hashed_password=auth.get_password_hash(recruiter_in.password),
        full_name=recruiter_in.full_name,
        role="recruiter",
        company_id=company_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    new_user.jobs_count = 0
    return new_user

# ── Jobs ────────────────────────────────────────────────────
def list_jobs(db: Session, company_id: int):
    return db.query(models_db.Job).filter(models_db.Job.company_id == company_id).all()

def create_job(db: Session, job_in: models.JobCreate, company_id: int):
    new_job = models_db.Job(
        title=job_in.title,
        description=job_in.description,
        requirements=job_in.requirements,
        max_rate=job_in.max_rate,
        company_id=company_id
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job

# ── Candidates ──────────────────────────────────────────────
def list_candidates(db: Session, company_id: int):
    return db.query(models_db.Candidate).join(models_db.Job).filter(models_db.Job.company_id == company_id).all()

def get_candidate_by_id(db: Session, candidate_id: int):
    return db.query(models_db.Candidate).filter(models_db.Candidate.id == candidate_id).first()

# ── AI Matching Logic ───────────────────────────────────────
from app.ai_engine import extract_text, extract_skills, extract_name_from_resume, extract_email, extract_experience_years, compute_match_score

async def process_resume_for_job(db: Session, job_id: int, filename: str, file_bytes: bytes) -> models.UploadResponse:
    """Process a resume against a specific job description using real AI."""
    job = db.query(models_db.Job).filter(models_db.Job.id == job_id).first()
    if not job:
        raise Exception("Job not found")

    # ── Extract text from resume ──
    try:
        resume_text = extract_text(file_bytes, filename)
    except Exception:
        resume_text = ""

    if not resume_text.strip():
        raise Exception(f"Could not extract text from {filename}")

    # ── AI Analysis ──
    jd_text = f"{job.title}\n{job.description}\n" + " ".join(job.requirements or [])
    match_score, matched_skills, missing_skills = compute_match_score(
        resume_text, jd_text, job.requirements or []
    )
    
    extracted_name = extract_name_from_resume(resume_text)
    extracted_email = extract_email(resume_text)
    extracted_exp = extract_experience_years(resume_text)
    resume_skills = extract_skills(resume_text)

    # Generate screening details
    screening = models_db.ScreeningDetail(
        experience=extracted_exp,
        experience_tech=matched_skills[0] if matched_skills else "General",
        visa="Not Specified",
        visa_details="Not extracted",
        rate=float(random.randint(60, 100)),
        client_max_rate=job.max_rate or 80.0,
        location="Not Specified",
        work_preference="Not Specified",
        skills=[s.title() for s in resume_skills],
        matched_skills=[s.title() for s in matched_skills],
        missing_skills=[s.title() for s in missing_skills],
        ai_summary=f"Match score: {match_score}%. Matched: {', '.join(matched_skills[:5])}. Missing: {', '.join(missing_skills[:5])}."
    )
    
    # Determine status
    status = "Interested" if match_score >= 70 else "Screening Complete"
    if screening.rate > screening.client_max_rate:
        status = "Rate Mismatch"

    new_candidate = models_db.Candidate(
        name=extracted_name,
        email=extracted_email or f"cand.{random.randint(1,1000)}@example.com",
        status=status,
        match_score=match_score,
        response_time="Instant",
        job_id=job_id,
        resume_path=filename
    )
    
    db.add(new_candidate)
    db.commit()
    db.refresh(new_candidate)
    
    screening.candidate_id = new_candidate.id
    db.add(screening)
    db.commit()
    
    return models.UploadResponse(
        success=True,
        message=f"Resume matched against '{job.title}' with {match_score}% score.",
        candidateId=str(new_candidate.id),
        candidateName=new_candidate.name
    )

def archive_candidate(db: Session, candidate_id: int) -> models.ActionResponse:
    candidate = db.query(models_db.Candidate).filter(models_db.Candidate.id == candidate_id).first()
    if not candidate:
        return models.ActionResponse(success=False, message="Candidate not found")
    
    candidate.status = "Archived"
    db.commit()
    return models.ActionResponse(success=True, message=f"{candidate.name} archived.")
