"""
SportShield — API Routes: Assets
Handles file upload, fingerprinting, metadata, and asset management
"""

import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.config import get_settings
from backend.database import Asset, Alert, Detection, get_db, User
from backend.ai.fingerprint import FingerprintEngine
from backend.ai.gemini_analyzer import GeminiAnalyzer
from backend.celery_app import process_asset_task

import logging

router = APIRouter(prefix="/api/assets", tags=["Assets"])
settings = get_settings()
logger = logging.getLogger("sportshield.assets")

fingerprint_engine = FingerprintEngine()
gemini = GeminiAnalyzer()

def _get_base_url(request: Request):
    return str(request.base_url).rstrip("/")


def _ensure_upload_dir():
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(f"{settings.UPLOAD_DIR}/thumbnails").mkdir(exist_ok=True)


# ─── Upload Asset ─────────────────────────────────────────────

@router.post("/upload", status_code=201)
async def upload_asset(
    request: Request,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    sport_category: Optional[str] = Form(None),
    event_name: Optional[str] = Form(None),
    protection_level: str = Form("standard"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload and fingerprint a new media asset."""
    _ensure_upload_dir()

    # Validate file type
    mime = file.content_type or ""
    is_image = mime.startswith("image/")
    is_video = mime.startswith("video/")

    if not is_image and not is_video:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {mime}")

    file_type = "image" if is_image else "video"
    
    # Check file size (FastAPI supports .size in 0.100+)
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    file_size = file.size if file.size is not None else 0
    
    if file_size > max_bytes:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Max allowed: {settings.MAX_FILE_SIZE_MB}MB"
        )
    

    # Save file with UUID (Absolute path for reliability)
    ext = Path(file.filename or "asset").suffix
    unique_filename = f"{uuid4().hex}{ext}"
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Fingerprinting & Analysis
    phash, dhash, ahash, watermark_id = None, None, None, None
    gemini_result = None
    status = "processing"

    if is_image:
        try:
            # Sync fingerprinting for images (fast)
            fp = fingerprint_engine.generate_image_fingerprint(file_path)
            phash = fp.get("phash")
            dhash = fp.get("dhash")
            ahash = fp.get("ahash")
            watermark_id = fingerprint_engine.generate_watermark_id()
            status = "protected"
            
            # Gemini analysis
            gemini_result = gemini.analyze_image(file_path)
        except Exception as e:
            logger.warning(f"Fingerprinting/Analysis failed: {e}")
    # Parse tags
    tag_list = []
    if tags:
        try:
            tag_list = json.loads(tags)
        except Exception:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    # Create DB record
    asset = Asset(
        user_id=current_user.id,
        org_id=current_user.org_id,
        filename=unique_filename,
        original_filename=file.filename or "unknown",
        file_type=file_type,
        mime_type=mime,
        file_size=file_size,
        file_path=file_path,
        phash=phash,
        dhash=dhash,
        ahash=ahash,
        watermark_id=watermark_id,
        title=title or file.filename,
        description=description,
        tags=tag_list,
        sport_category=sport_category or (gemini_result or {}).get("sport_category"),
        event_name=event_name,
        gemini_classification=gemini_result,
        protection_level=protection_level,
        status=status,
    )
    db.add(asset)
    db.flush()

    # If it's a video, or if we want background duplicate detection, enqueue task
    if is_video or status == "processing":
        try:
            process_asset_task.delay(asset.id)
        except Exception as e:
            logger.warning(f"Background task failed to enqueue: {e}. Running fallback if needed.")
            # For images we already fingerprinted, we don't strictly need the task unless for duplicate detection
    
    db.commit()
    db.refresh(asset)

    return _format_asset(asset, db, request=request, detailed=True)


# ─── List Assets ──────────────────────────────────────────────

@router.get("/")
def list_assets(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    file_type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all assets for the current user/organization."""
    query = db.query(Asset).filter(Asset.user_id == current_user.id)

    if current_user.org_id:
        query = db.query(Asset).filter(Asset.org_id == current_user.org_id)

    if status:
        query = query.filter(Asset.status == status)
    if file_type:
        query = query.filter(Asset.file_type == file_type)
    if search:
        query = query.filter(
            Asset.title.ilike(f"%{search}%") | Asset.description.ilike(f"%{search}%")
        )

    total = query.count()
    assets = query.order_by(Asset.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "assets": [_format_asset(a, db, request=request) for a in assets],
        "skip": skip,
        "limit": limit,
    }


# ─── Get Single Asset ─────────────────────────────────────────

@router.get("/{asset_id}")
def get_asset(
    asset_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed info on a specific asset."""
    asset = _get_asset_or_404(asset_id, current_user, db)
    return _format_asset(asset, db, request=request, detailed=True)


# ─── Delete Asset ─────────────────────────────────────────────

@router.delete("/{asset_id}")
def delete_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an asset and its associated files."""
    asset = _get_asset_or_404(asset_id, current_user, db)

    # Remove file
    try:
        if os.path.exists(asset.file_path):
            os.remove(asset.file_path)
    except Exception:
        pass

    db.delete(asset)
    db.commit()
    return {"message": "Asset deleted successfully"}


# ─── Download Asset ───────────────────────────────────────────

@router.get("/{asset_id}/download")
def download_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from fastapi.responses import RedirectResponse
    asset = _get_asset_or_404(asset_id, current_user, db)
    
    if not os.path.exists(asset.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(asset.file_path, filename=asset.original_filename)


# ─── Stats ────────────────────────────────────────────────────

@router.get("/stats/summary")
def asset_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get asset statistics for the dashboard."""
    base = db.query(Asset)
    if current_user.org_id:
        base = base.filter(Asset.org_id == current_user.org_id)
    else:
        base = base.filter(Asset.user_id == current_user.id)

    total = base.count()
    protected = base.filter(Asset.status == "protected").count()
    at_risk = base.filter(Asset.status == "at_risk").count()
    violated = base.filter(Asset.status == "violated").count()
    images = base.filter(Asset.file_type == "image").count()
    videos = base.filter(Asset.file_type == "video").count()

    total_detections = db.query(Detection).join(Asset).filter(
        Asset.org_id == current_user.org_id if current_user.org_id else Asset.user_id == current_user.id
    ).count()

    return {
        "total_assets": total,
        "protected": protected,
        "at_risk": at_risk,
        "violated": violated,
        "images": images,
        "videos": videos,
        "total_detections": total_detections,
        "protection_rate": round(protected / total * 100, 1) if total > 0 else 0,
    }


# ─── Helpers ──────────────────────────────────────────────────

def _get_asset_or_404(asset_id: int, user: User, db: Session) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    # Authorization check
    if asset.user_id != user.id and asset.org_id != user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return asset


def _format_asset(asset: Asset, db: Session, request: Request = None, detailed: bool = False) -> dict:
    detections_count = db.query(Detection).filter(Detection.asset_id == asset.id).count()
    
    # Generate public URL for the file
    file_url = None
    if asset.file_path:
        if asset.file_path.startswith("http"):
            file_url = asset.file_path
        elif request:
            base_url = _get_base_url(request)
            file_url = f"{base_url}/uploads/{asset.filename}"

    result = {
        "id": asset.id,
        "filename": asset.filename,
        "original_filename": asset.original_filename,
        "file_type": asset.file_type,
        "file_size": asset.file_size,
        "file_url": file_url,
        "title": asset.title,
        "description": asset.description,
        "tags": asset.tags,
        "sport_category": asset.sport_category,
        "event_name": asset.event_name,
        "status": asset.status,
        "protection_level": asset.protection_level,
        "detections_count": detections_count,
        "fingerprint": {
            "phash": asset.phash,
            "dhash": asset.dhash,
            "ahash": asset.ahash,
            "watermark_id": asset.watermark_id,
        },
        "created_at": asset.created_at,
        "updated_at": asset.updated_at,
    }
    if detailed:
        result.update({
            "gemini_classification": asset.gemini_classification,
        })
    return result
