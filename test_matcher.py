import requests
import json
import os

BASE_URL = "http://localhost:8000/api"

def test_flow():
    # 1. Signup / Login
    import uuid
    dummy_email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    
    auth_data = {
        "email": dummy_email,
        "full_name": "Test User",
        "password": "password123",
        "company_name": "Test Company",
        "role": "admin"
    }
    
    # Try signup first
    res = requests.post(f"{BASE_URL}/auth/signup", json=auth_data)
    res.raise_for_status()
        
    try:
        token = res.json().get("accessToken", res.json().get("access_token"))
    except Exception as e:
        print(f"FAILED TO GET TOKEN. Status: {res.status_code}. Response: {res.text}")
        return
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create Job
    job_data = {
        "title": "Python Developer",
        "description": "Looking for a strong Python backend dev.",
        "requirements": ["Python", "FastAPI", "SQLAlchemy", "Docker"]
    }
    res = requests.post(f"{BASE_URL}/jobs", json=job_data, headers=headers)
    job_id = res.json()["id"]
    print(f"Created Job ID: {job_id}")

    # 3. Create dummy resume
    resume_text = "Experienced Developer\nI have 5 years of experience building APIs with Python and FastAPI. I also use Docker."
    with open("test_resume.txt", "w") as f:
        f.write(resume_text)

    # 4. Upload Resume
    with open("test_resume.txt", "rb") as f:
        files = {"file": ("test_resume.txt", f, "text/plain")}
        data = {"jobId": str(job_id)}
        res = requests.post(f"{BASE_URL}/upload-resume", files=files, data=data, headers=headers)
    
    print("\nUpload Response:", res.json())
    candidate_id = res.json()["candidateId"]

    # 5. Fetch Candidate Details
    res = requests.get(f"{BASE_URL}/candidates/{candidate_id}", headers=headers)
    candidate = res.json()
    print("\nCandidate Details:")
    print(json.dumps(candidate, indent=2))
    
    os.remove("test_resume.txt")

if __name__ == "__main__":
    test_flow()
