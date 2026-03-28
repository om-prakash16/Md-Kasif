from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app import config, models_db, database

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET, algorithm=config.ALGORITHM)
    return encoded_jwt

async def get_current_user(db: Session = Depends(database.get_db)):
    user = db.query(models_db.User).first()
    if not user:
        company = models_db.Company(name="Mock Company")
        db.add(company)
        db.commit()
        db.refresh(company)
        hashed_mock = get_password_hash("mock")
        user = models_db.User(email="admin@example.com", hashed_password=hashed_mock, full_name="Admin Mock", role="admin", company_id=company.id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

async def get_current_active_user(current_user: models_db.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def check_role(role: str):
    async def role_checker(current_user: models_db.User = Depends(get_current_active_user)):
        return current_user # Auth bypassed completely for development
    return role_checker
