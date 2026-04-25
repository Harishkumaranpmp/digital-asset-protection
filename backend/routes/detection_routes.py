"""
SportShield — API Routes: Detections
Manages detected infringements, similarity scores, and threat tracking
"""

import json
import random
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
import shutil
from uuid import uuid4

from backend.auth import get_current_user
from backend.database import Asset, Detection, Alert, User, get_db
from backend.ai.fingerprint import FingerprintEngine
from backend.ai.crawler import WebCrawler
from backend.celery_app import run_platform_scan_task
from backend.config import get_settings

from ai_models.fingerprint_generator import FingerprintGenerator
from ai_models.duplicate_detector import DuplicateDetector

router = APIRouter(prefix="/api/detections", tags=["Detections"])
fingerprint_engine = FingerprintEngine()
settings = get_settings()


class DetectionUpdateRequest(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


# ─── List Detections ──────────────────────────────────────────

@router.get("/")
def list_detections(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    platform: Optional[str] = None,
    asset_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all detections for the current user's assets."""
    query = (
        db.query(Detection)
        .join(Asset)
        .filter(
            Asset.org_id == current_user.org_id
            if current_user.org_id
            else Asset.user_id == current_user.id
        )
    )

    if status:
        query = query.filter(Detection.status == status)
    if severity:
        query = query.filter(Detection.severity == severity)
    if platform:
        query = query.filter(Detection.platform == platform)
    if asset_id:
        query = query.filter(Detection.asset_id == asset_id)

    total = query.count()
    detections = query.order_by(Detection.detected_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "detections": [_format_detection(d, db) for d in detections],
    }


# ─── Get Single Detection ─────────────────────────────────────

@router.get("/{detection_id}")
def get_detection(
    detection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    return _format_detection(detection, db, detailed=True)


# ─── Update Detection Status ──────────────────────────────────

@router.patch("/{detection_id}")
def update_detection(
    detection_id: int,
    req: DetectionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")

    valid_statuses = ["active", "resolved", "false_positive", "dmca_sent"]
    if req.status and req.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be: {valid_statuses}")

    if req.status:
        detection.status = req.status
        if req.status == "resolved":
            detection.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(detection)
    return _format_detection(detection, db)


# ─── Ad-hoc Detection (Synchronous) ───────────────────────────

@router.post("/detect/upload")
async def detect_ad_hoc_upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Synchronously analyze an uploaded file against the database for duplicates.
    Does not permanently save the file to the user's asset library.
    """
    # Create temp directory if not exists
    temp_dir = os.path.join(settings.UPLOAD_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save temp file
    ext = os.path.splitext(file.filename)[1]
    temp_path = os.path.join(temp_dir, f"{uuid4().hex}{ext}")
    
    content = await file.read()
    with open(temp_path, "wb") as f:
        f.write(content)
        
    try:
        # Determine file type
        mime = file.content_type or ""
        file_type = "image" if mime.startswith("image/") else "video"
        
        # Generate fingerprint
        fp = FingerprintGenerator.generate(temp_path, file_type)
        
        # Scan database
        db_assets = db.query(Asset).filter(
            Asset.org_id == current_user.org_id if current_user.org_id else Asset.user_id == current_user.id
        ).all()
        
        duplicates = DuplicateDetector.scan_database(fp, db_assets)
        
        return {
            "status": "success",
            "message": f"Found {len(duplicates)} similar assets.",
            "matches": duplicates,
            "fingerprint": fp
        }
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ─── Get Detection History ────────────────────────────────────

@router.get("/detect/history")
def get_detection_history(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Alias for getting the full detection history of the user/org."""
    # Defers to the list_detections core logic
    return list_detections(skip=skip, limit=limit, current_user=current_user, db=db)


# ─── Get Detections by Asset ID ───────────────────────────────

@router.get("/detect/{asset_id}")
def get_detections_for_asset(
    asset_id: int,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all detections associated with a specific asset."""
    # Verify asset ownership
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    if asset.user_id != current_user.id and asset.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this asset")
        
    detections = db.query(Detection).filter(
        Detection.asset_id == asset_id
    ).order_by(Detection.detected_at.desc()).offset(skip).limit(limit).all()
    
    total = db.query(Detection).filter(Detection.asset_id == asset_id).count()
    
    return {
        "asset_id": asset_id,
        "total": total,
        "detections": [_format_detection(d, db) for d in detections],
    }


# ─── Trigger Manual Scan ──────────────────────────────────────

@router.post("/scan/{asset_id}")
async def trigger_scan(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger an immediate web scan for a specific asset."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Enqueue background scan
    try:
        run_platform_scan_task.delay(asset.id)
    except Exception as e:
        print(f"Warning: Failed to enqueue scan task: {e}")
        raise HTTPException(status_code=500, detail="Failed to start scan")

    # Create alert
    alert = Alert(
        user_id=current_user.id,
        alert_type="scan_started",
        severity="info",
        title="Web Scan Started",
        message=f"A background scan for '{asset.title}' has been initiated.",
        alert_metadata={"asset_id": asset_id}
    )
    db.add(alert)
    db.commit()

    return {
        "scanned": True,
        "message": "Scan has been started in the background.",
    }


# ─── Dashboard Stats ──────────────────────────────────────────

@router.get("/stats/overview")
def detection_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns comprehensive detection statistics for dashboard."""
    base_query = (
        db.query(Detection)
        .join(Asset)
        .filter(
            Asset.org_id == current_user.org_id
            if current_user.org_id
            else Asset.user_id == current_user.id
        )
    )

    total = base_query.count()
    active = base_query.filter(Detection.status == "active").count()
    resolved = base_query.filter(Detection.status == "resolved").count()
    critical = base_query.filter(Detection.severity == "critical").count()
    high = base_query.filter(Detection.severity == "high").count()

    # Platform breakdown
    platforms = {}
    for d in base_query.all():
        p = d.platform or "unknown"
        platforms[p] = platforms.get(p, 0) + 1

    # Recent 7 days trend
    trend = []
    for i in range(7):
        day = datetime.utcnow() - timedelta(days=6-i)
        count = base_query.filter(
            Detection.detected_at >= day.replace(hour=0, minute=0, second=0),
            Detection.detected_at < (day + timedelta(days=1)).replace(hour=0, minute=0, second=0)
        ).count()
        trend.append({"date": day.strftime("%Y-%m-%d"), "count": count})

    # Geographic distribution
    geo = {}
    for d in base_query.filter(Detection.country_code.isnot(None)).all():
        cc = d.country_code
        geo[cc] = geo.get(cc, 0) + 1

    return {
        "total": total,
        "active": active,
        "resolved": resolved,
        "critical": critical,
        "high": high,
        "platform_breakdown": platforms,
        "trend_7days": trend,
        "geographic_distribution": geo,
        "avg_similarity": _avg_or_zero(
            [d.similarity_score for d in base_query.filter(Detection.status == "active").all()]
        ),
    }


# ─── Seed Demo Detections ─────────────────────────────────────

@router.post("/demo/seed")
def seed_demo_detections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Populate dashboard with demo detection data."""
    assets = db.query(Asset).filter(Asset.user_id == current_user.id).all()
    if not assets:
        raise HTTPException(status_code=400, detail="Upload at least one asset first")

    platforms = ["youtube", "instagram", "twitter", "facebook", "tiktok", "reddit", "sports_site"]
    severities = ["low", "medium", "high", "critical"]
    countries = ["US", "GB", "IN", "DE", "BR", "AU", "FR", "ES", "JP", "CN"]

    count = 0
    for asset in assets[:5]:
        num_dets = random.randint(2, 8)
        for i in range(num_dets):
            sim = random.uniform(0.62, 0.99)
            det = Detection(
                asset_id=asset.id,
                detection_url=f"https://demo-infringement-{random.randint(1000, 9999)}.example.com/video/{i}",
                platform=random.choice(platforms),
                domain=f"demo-site-{random.randint(10, 99)}.com",
                country_code=random.choice(countries),
                latitude=random.uniform(-60, 70),
                longitude=random.uniform(-180, 180),
                similarity_score=round(sim, 4),
                match_type="exact" if sim > 0.95 else "modified" if sim > 0.80 else "partial",
                severity="critical" if sim > 0.95 else "high" if sim > 0.85 else "medium" if sim > 0.70 else "low",
                status="active",
                detected_at=datetime.utcnow() - timedelta(hours=random.randint(1, 168)),
            )
            db.add(det)
            count += 1

        asset.status = "violated" if count > 5 else "at_risk"

    db.commit()
    return {"message": f"Created {count} demo detections"}


# ─── Helpers ──────────────────────────────────────────────────

def _format_detection(detection: Detection, db: Session, detailed: bool = False) -> dict:
    asset = db.query(Asset).filter(Asset.id == detection.asset_id).first()
    result = {
        "id": detection.id,
        "asset_id": detection.asset_id,
        "asset_title": asset.title if asset else "Unknown",
        "detection_url": detection.detection_url,
        "platform": detection.platform,
        "domain": detection.domain,
        "country_code": detection.country_code,
        "latitude": detection.latitude,
        "longitude": detection.longitude,
        "similarity_score": detection.similarity_score,
        "match_type": detection.match_type,
        "severity": detection.severity,
        "status": detection.status,
        "detected_at": detection.detected_at,
        "resolved_at": detection.resolved_at,
    }
    return result


def _avg_or_zero(values):
    return round(sum(values) / len(values), 4) if values else 0.0
