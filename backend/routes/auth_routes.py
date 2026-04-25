"""
SportShield — API Routes: Authentication
Handles user registration, login, profile management
"""

import secrets
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.database import get_db, User, Organization
from backend.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, RegisterRequest, LoginRequest
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class OrgSetupRequest(BaseModel):
    org_name: str
    plan: str = "starter"


# ─── Register ────────────────────────────────────────────────

@router.post("/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account and optionally create organization."""

    # Check duplicates
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create org if provided
    org = None
    if req.org_name:
        slug = req.org_name.lower().replace(" ", "-")[:50]
        # Ensure unique slug
        base_slug = slug
        counter = 1
        while db.query(Organization).filter(Organization.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        org = Organization(
            name=req.org_name,
            slug=slug,
            api_key=secrets.token_hex(32),
            plan="starter"
        )
        db.add(org)
        db.flush()

    # Create user
    user = User(
        email=req.email,
        username=req.username,
        password_hash=hash_password(req.password),
        full_name=req.full_name,
        role="admin" if req.org_name else "analyst",
        org_id=org.id if org else None,
        is_verified=True,  # Auto-verify for demo
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate token
    token = create_access_token({"sub": str(user.id), "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "org_id": user.org_id,
            "org_name": org.name if org else None,
        }
    }


# ─── Login ───────────────────────────────────────────────────

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""

    user = db.query(User).filter(User.email == req.email).first()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token({"sub": str(user.id), "role": user.role})

    org = db.query(Organization).filter(Organization.id == user.org_id).first() if user.org_id else None

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "org_id": user.org_id,
            "org_name": org.name if org else None,
        }
    }


# ─── Profile ─────────────────────────────────────────────────

@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user's profile."""
    org = db.query(Organization).filter(Organization.id == current_user.org_id).first() if current_user.org_id else None
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "org_id": current_user.org_id,
        "org_name": org.name if org else None,
        "org_plan": org.plan if org else None,
        "is_active": current_user.is_active,
        "last_login": current_user.last_login,
        "created_at": current_user.created_at,
    }


# ─── Demo User Seed ──────────────────────────────────────────

@router.post("/demo/seed", status_code=201)
def seed_demo(db: Session = Depends(get_db)):
    """Create demo user for hackathon judges."""
    if db.query(User).filter(User.email == "demo@sportshield.ai").first():
        return {"message": "Demo user already exists", "email": "demo@sportshield.ai", "password": "demo1234"}

    org = Organization(
        name="SportShield Demo",
        slug="sportshield-demo",
        api_key=secrets.token_hex(32),
        plan="enterprise",
        max_assets=10000,
    )
    db.add(org)
    db.flush()

    user = User(
        email="demo@sportshield.ai",
        username="demo_admin",
        password_hash=hash_password("demo1234"),
        full_name="Demo Administrator",
        role="admin",
        org_id=org.id,
        is_verified=True,
    )
    db.add(user)
    db.commit()

    return {
        "message": "Demo user created",
        "email": "demo@sportshield.ai",
        "password": "demo1234",
    }
