"""
RecruitAuto AI – Pydantic Models (Schemas)
==========================================
Every request/response body is defined here as a Pydantic model.
This gives us automatic validation, serialisation, and OpenAPI docs.

Naming convention:
  • *Base   – shared fields
  • *Create – fields needed on creation
  • *Out    – fields returned in responses
"""

from __future__ import annotations
from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field


# ── Status Enum ──────────────────────────────────────────────
CandidateStatus = Literal[
    "Text Sent",
    "Screening Complete",
    "Interested",
    "Rate Mismatch",
    "Archived",
]


# ── Screening Details ───────────────────────────────────────
class ScreeningDetails(BaseModel):
    """AI-extracted answers from the screening call / form."""

    experience: str          = Field(..., example="5 Years")
    experience_tech: str     = Field(..., example="Java / Spring Boot", alias="experienceTech")
    visa: str                = Field(..., example="H1B (Transfer Needed)")
    visa_details: str        = Field(..., example="Currently employed, open to transfer", alias="visaDetails")
    rate: float              = Field(..., ge=0, example=75.0)
    client_max_rate: float   = Field(..., ge=0, example=70.0, alias="clientMaxRate")
    location: str            = Field(..., example="Remote")
    work_preference: str     = Field(..., example="New York (Remote)", alias="workPreference")
    skills: List[str]        = Field(default_factory=list, example=["Java", "Spring Boot"])
    matched_skills: Optional[List[str]] = Field(default_factory=list, alias="matchedSkills")
    missing_skills: Optional[List[str]] = Field(default_factory=list, alias="missingSkills")
    ai_summary: str          = Field(..., example="Strong backend engineer…", alias="aiSummary")

    class Config:
        populate_by_name = True


# ── Candidate ───────────────────────────────────────────────
class CandidateOut(BaseModel):
    """Single candidate returned to the frontend."""

    id: str
    name: str
    email: str
    phone: str
    job_role: str            = Field(..., alias="jobRole")
    status: CandidateStatus
    match_score: int         = Field(..., ge=0, le=100, alias="matchScore")
    response_time: str       = Field(..., alias="responseTime")
    submitted_at: datetime    = Field(..., alias="submittedAt")
    screening: Optional[ScreeningDetails] = None

    class Config:
        populate_by_name = True


# ── Dashboard Stats ─────────────────────────────────────────
class DashboardStats(BaseModel):
    """Aggregate numbers shown on the Control Center."""

    total_screened: int      = Field(..., alias="totalScreened")
    interested: int
    rate_mismatch: int       = Field(..., alias="rateMismatch")
    avg_response_time: str   = Field(..., alias="avgResponseTime")

    class Config:
        populate_by_name = True


# ── Upload Response ─────────────────────────────────────────
class UploadResponse(BaseModel):
    """Returned after a resume upload."""

    success: bool
    message: str
    candidate_id: str        = Field(..., alias="candidateId")
    candidate_name: str      = Field(..., alias="candidateName")

    class Config:
        populate_by_name = True


# ── Generic Action Response ─────────────────────────────────
class ActionResponse(BaseModel):
    """Simple success / message response for actions like archive."""

    success: bool
    message: str

# ── Job Models ──────────────────────────────────────────────
class JobBase(BaseModel):
    title: str
    description: str
    requirements: List[str] = Field(default_factory=list)
    max_rate: Optional[float] = Field(None, alias="maxRate")

    class Config:
        populate_by_name = True

class JobCreate(JobBase):
    pass

class JobOut(JobBase):
    id: int
    created_at: datetime = Field(..., alias="createdAt")
    company_id: int = Field(..., alias="companyId")

    class Config:
        from_attributes = True
        populate_by_name = True

# ── Auth Models ─────────────────────────────────────────────
class UserBase(BaseModel):
    email: str
    full_name: str = Field(..., alias="fullName")

    class Config:
        populate_by_name = True

class UserCreate(UserBase):
    password: str
    company_name: str = Field(..., alias="companyName")
    role: Literal["admin", "recruiter"] = "admin"

class UserOut(UserBase):
    id: int
    role: str
    company_id: int = Field(..., alias="companyId")
    is_active: bool = Field(True, alias="isActive")
    jobs_count: int = Field(0, alias="jobsCount")

    class Config:
        from_attributes = True
        populate_by_name = True

class RecruiterCreate(UserBase):
    password: str

class Token(BaseModel):
    access_token: str = Field(..., alias="accessToken")
    token_type: str = Field(..., alias="tokenType")
    user: UserOut

    class Config:
        populate_by_name = True
