"""
SportShield Backend — Database Setup
SQLAlchemy async engine with SQLite (dev) / PostgreSQL (prod)
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import os

from backend.config import get_settings

settings = get_settings()

# Create engine — Support both SQLite and PostgreSQL (Supabase)
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Only use connection pooling for PostgreSQL (SQLite doesn't support it)
is_sqlite = "sqlite" in db_url

# For PostgreSQL, add connection parameters to force IPv4 and SSL
connect_args = {"check_same_thread": False} if is_sqlite else {}
if not is_sqlite:
    # Force IPv4 connection (Render doesn't support IPv6 outbound)
    connect_args["hostaddr"] = None  # Will be resolved as IPv4

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,  # Handle disconnected connections
    pool_size=10 if not is_sqlite else None,        # Only for PostgreSQL
    max_overflow=20 if not is_sqlite else None,     # Only for PostgreSQL
    echo=settings.DEBUG,
    # Force IPv4 by disabling IPv6 DNS resolution
    pool_recycle=3600,  # Recycle connections every hour
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─── Dependency ───────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Models ───────────────────────────────────────────────────

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    plan = Column(String(50), default="starter")  # starter, pro, enterprise
    api_key = Column(String(64), unique=True, nullable=False)
    logo_url = Column(String(500), nullable=True)
    max_assets = Column(Integer, default=100)
    max_scans_per_month = Column(Integer, default=1000)
    created_at = Column(DateTime, server_default=func.now())
    
    users = relationship("User", back_populates="organization")
    assets = relationship("Asset", back_populates="organization")


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="analyst")  # admin, manager, analyst, viewer
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    organization = relationship("Organization", back_populates="users")
    assets = relationship("Asset", back_populates="owner")
    alerts = relationship("Alert", back_populates="user")


class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (
        # Indexes for frequently queried columns
        {"sqlite_autoincrement": True},
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # File info
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # image, video
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    file_path = Column(String(1000), nullable=False)
    
    # Fingerprinting
    phash = Column(String(64), nullable=True)  # Perceptual hash
    dhash = Column(String(64), nullable=True)  # Difference hash
    ahash = Column(String(64), nullable=True)  # Average hash
    fingerprint_vector = Column(Text, nullable=True)  # JSON array
    hash_algorithm = Column(String(50), nullable=True) # E.g., imagehash, opencv
    watermark_id = Column(String(64), nullable=True)
    
    # Metadata
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    sport_category = Column(String(100), nullable=True)
    event_name = Column(String(500), nullable=True)
    capture_date = Column(DateTime, nullable=True)
    
    # AI Analysis
    gemini_classification = Column(JSON, nullable=True)
    content_rating = Column(String(20), nullable=True)
    
    # Status
    status = Column(String(50), default="processing", index=True)  # processing, protected, at_risk, violated
    protection_level = Column(String(20), default="standard")  # standard, enhanced, maximum
    thumbnail_path = Column(String(1000), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    owner = relationship("User", back_populates="assets")
    organization = relationship("Organization", back_populates="assets")
    detections = relationship("Detection", back_populates="asset")
    crawl_jobs = relationship("CrawlJob", back_populates="asset")


class Detection(Base):
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    
    # Location
    detection_url = Column(String(2000), nullable=False)
    platform = Column(String(100), nullable=True, index=True)  # youtube, instagram, twitter, website
    domain = Column(String(255), nullable=True)
    country_code = Column(String(10), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Similarity
    similarity_score = Column(Float, nullable=False)  # 0.0 - 1.0
    match_type = Column(String(50), nullable=True)  # exact, modified, partial
    diff_thumbnail_path = Column(String(1000), nullable=True)
    
    # Status
    status = Column(String(50), default="active", index=True)  # active, resolved, false_positive, dmca_sent
    severity = Column(String(20), default="medium", index=True)  # low, medium, high, critical
    
    # Timestamps
    detected_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime, nullable=True)
    
    asset = relationship("Asset", back_populates="detections")
    enforcement_case = relationship("EnforcementCase", back_populates="detection", uselist=False)


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    
    job_type = Column(String(50), nullable=False)  # web_search, social_scan, deep_scan
    target_platforms = Column(JSON, nullable=True)
    search_query = Column(String(500), nullable=True)
    
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    progress = Column(Float, default=0.0)  # 0 - 100
    pages_scanned = Column(Integer, default=0)
    results_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    asset = relationship("Asset", back_populates="crawl_jobs")


class EnforcementCase(Base):
    __tablename__ = "enforcement_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey("detections.id"), unique=True, nullable=False)
    
    case_number = Column(String(50), unique=True, nullable=False)
    case_type = Column(String(50), default="dmca")  # dmca, cease_desist, legal_action
    
    # Notice details
    respondent_name = Column(String(500), nullable=True)
    respondent_email = Column(String(255), nullable=True)
    platform_contact = Column(String(500), nullable=True)
    notice_content = Column(Text, nullable=True)
    
    # Status
    status = Column(String(50), default="draft")  # draft, sent, acknowledged, resolved, escalated
    notice_sent_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    detection = relationship("Detection", back_populates="enforcement_case")


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    alert_type = Column(String(50), nullable=False)  # new_detection, high_similarity, crawl_complete, dmca_sent
    severity = Column(String(20), default="info")  # info, warning, danger, critical
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    alert_metadata = Column(JSON, nullable=True)
    
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="alerts")


def create_tables():
    """Create all database tables."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        # In production, you might want to exit or handle this differently
        # For now, we'll log and continue (app will fail on first DB query)
        raise
