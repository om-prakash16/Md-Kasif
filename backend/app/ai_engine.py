"""
RecruitAuto AI – Resume Parsing & Matching Engine
==================================================
Extracts text from PDF/DOCX resumes, then scores them
against a Job Description using TF-IDF cosine similarity
combined with keyword matching.
"""

from __future__ import annotations
import re
import io
from typing import List, Tuple

import fitz  # PyMuPDF
from docx import Document as DocxDocument
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ── Text Extraction ──────────────────────────────────────────
def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF file."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract all text from a DOCX file."""
    doc = DocxDocument(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs).strip()


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Route to the correct parser based on file extension."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        return extract_text_from_docx(file_bytes)
    elif ext == "txt":
        return file_bytes.decode("utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file type: .{ext}")


# ── Skill Extraction ────────────────────────────────────────
COMMON_SKILLS = [
    "python", "java", "javascript", "typescript", "react", "angular", "vue",
    "node.js", "nodejs", "express", "django", "flask", "fastapi", "spring",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
    "git", "ci/cd", "jenkins", "github actions",
    "html", "css", "tailwind", "bootstrap",
    "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "rest api", "graphql", "microservices", "agile", "scrum",
    "c++", "c#", "go", "rust", "ruby", "php", "swift", "kotlin",
    "linux", "unix", "bash", "powershell",
    "figma", "photoshop", "illustrator",
    "salesforce", "sap", "tableau", "power bi",
    ".net", "asp.net", "spring boot", "hibernate",
]


def extract_skills(text: str) -> List[str]:
    """Extract known skills from text using keyword matching."""
    text_lower = text.lower()
    found = []
    for skill in COMMON_SKILLS:
        # Use word boundary matching for short skills
        if len(skill) <= 3:
            if re.search(rf"\b{re.escape(skill)}\b", text_lower):
                found.append(skill)
        else:
            if skill in text_lower:
                found.append(skill)
    return list(set(found))


def extract_name_from_resume(text: str) -> str:
    """Try to extract a candidate name from the first lines of a resume."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return "Unknown Candidate"
    
    # The first non-empty line is often the name
    first_line = lines[0]
    # Filter out lines that look like headers or emails
    if "@" in first_line or len(first_line) > 60 or first_line.lower().startswith(("resume", "curriculum", "cv")):
        if len(lines) > 1:
            return lines[1][:50]
        return "Unknown Candidate"
    return first_line[:50]


def extract_email(text: str) -> str:
    """Extract the first email address found in text."""
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else ""


def extract_experience_years(text: str) -> str:
    """Try to extract years of experience from text."""
    patterns = [
        r"(\d+)\+?\s*years?\s*(?:of)?\s*experience",
        r"experience\s*(?:of)?\s*(\d+)\+?\s*years?",
        r"(\d+)\+?\s*yrs?\s*(?:of)?\s*experience",
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return f"{match.group(1)} Years"
    return "N/A"


# ── AI Matching ──────────────────────────────────────────────
def compute_match_score(
    resume_text: str,
    job_description: str,
    job_requirements: List[str],
) -> Tuple[int, List[str], List[str]]:
    """
    Compute a match score between a resume and a job description.
    
    Returns:
        (score 0-100, matched_skills, missing_skills)
    """
    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(job_description)
    
    # Combine JD skills with explicit requirements
    all_required = list(set(
        [s.lower() for s in jd_skills] +
        [r.lower() for r in job_requirements]
    ))
    
    # ── Keyword Match Score (40% weight) ──
    if all_required:
        matched = [s for s in all_required if s in [rs.lower() for rs in resume_skills]]
        missing = [s for s in all_required if s not in [rs.lower() for rs in resume_skills]]
        keyword_score = (len(matched) / len(all_required)) * 100
    else:
        matched = resume_skills
        missing = []
        keyword_score = 50  # Neutral if no requirements
    
    # ── TF-IDF Cosine Similarity (60% weight) ──
    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        tfidf_matrix = vectorizer.fit_transform([job_description, resume_text])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        tfidf_score = similarity * 100
    except Exception:
        tfidf_score = 50  # Fallback
    
    # ── Combine ──
    final_score = int(0.4 * keyword_score + 0.6 * tfidf_score)
    final_score = max(0, min(100, final_score))
    
    return final_score, [s.title() for s in matched], [s.title() for s in missing]
