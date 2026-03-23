from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="company")
    jobs = relationship("Job", back_populates="company")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String)  # "admin" or "recruiter"
    is_active = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey("companies.id"))

    company = relationship("Company", back_populates="users")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    requirements = Column(JSON, nullable=True)  # List of required skills
    max_rate = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    company_id = Column(Integer, ForeignKey("companies.id"))

    company = relationship("Company", back_populates="jobs")
    candidates = relationship("Candidate", back_populates="job")

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True)
    phone = Column(String, nullable=True)
    status = Column(String)  # "Text Sent", "Interested", etc.
    match_score = Column(Integer, default=0)
    response_time = Column(String, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    resume_path = Column(String, nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))

    job = relationship("Job", back_populates="candidates")
    screening_details = relationship("ScreeningDetail", back_populates="candidate", uselist=False)

class ScreeningDetail(Base):
    __tablename__ = "screening_details"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    experience = Column(String)
    experience_tech = Column(String)
    visa = Column(String)
    visa_details = Column(String)
    rate = Column(Float)
    client_max_rate = Column(Float)
    location = Column(String)
    work_preference = Column(String)
    skills = Column(JSON)
    ai_summary = Column(String)

    candidate = relationship("Candidate", back_populates="screening_details")
