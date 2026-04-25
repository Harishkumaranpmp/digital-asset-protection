"""
SportShield — Test Suite
Basic integration tests for the core API endpoints.

Run with: pytest tests/ -v
"""

import pytest
import os
from fastapi.testclient import TestClient

# Set test environment variables before importing the app
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_sportshield.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-not-production")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-testing-only")
os.environ.setdefault("UPLOAD_DIR", "./test_uploads")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from backend.main import app
from backend.database import create_tables

os.makedirs("./test_uploads", exist_ok=True)
create_tables()

client = TestClient(app)


# ── Health Endpoints ──────────────────────────────────────────

def test_root_returns_ok():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "operational"


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_health_liveness():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


# ── Auth Endpoints ────────────────────────────────────────────

TEST_USER = {
    "email": "test@sportshield.ai",
    "username": "testuser",
    "password": "TestPassword123!",
    "full_name": "Test User",
}

def test_user_registration():
    response = client.post("/api/auth/register", json=TEST_USER)
    # 201 Created or 409 if already exists (idempotent test)
    assert response.status_code in [201, 409]


def test_user_login():
    # First ensure user exists
    client.post("/api/auth/register", json=TEST_USER)
    
    response = client.post("/api/auth/login", data={
        "username": TEST_USER["email"],
        "password": TEST_USER["password"],
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    return data["access_token"]


def test_invalid_login_rejected():
    response = client.post("/api/auth/login", data={
        "username": "wrong@email.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


def test_protected_endpoint_requires_auth():
    response = client.get("/api/assets/")
    assert response.status_code == 401


# ── AI Model Smoke Tests ──────────────────────────────────────

def test_image_hash_model_imports():
    from ai_models.image_hash_model import ImageHashModel
    assert ImageHashModel is not None


def test_video_hash_model_imports():
    from ai_models.video_hash_model import VideoHashModel
    assert VideoHashModel is not None


def test_fingerprint_generator_imports():
    from ai_models.fingerprint_generator import FingerprintGenerator
    assert FingerprintGenerator is not None


def test_duplicate_detector_imports():
    from ai_models.duplicate_detector import DuplicateDetector
    assert DuplicateDetector is not None


def test_duplicate_detector_exact_match():
    from ai_models.duplicate_detector import DuplicateDetector
    fp = {"phash": "abcdef1234567890" * 4, "dhash": "abcdef1234567890" * 4, "ahash": "abcdef1234567890" * 4}
    result = DuplicateDetector.compare(fp, fp)
    assert result["similarity_score"] == 100.0
    assert result["match_type"] == "exact"


def test_duplicate_detector_unique():
    from ai_models.duplicate_detector import DuplicateDetector
    fp1 = {"phash": "a" * 64, "dhash": "a" * 64, "ahash": "a" * 64}
    fp2 = {"phash": "b" * 64, "dhash": "b" * 64, "ahash": "b" * 64}
    result = DuplicateDetector.compare(fp1, fp2)
    assert result["match_type"] == "unique"
    assert result["similarity_score"] < 80.0
