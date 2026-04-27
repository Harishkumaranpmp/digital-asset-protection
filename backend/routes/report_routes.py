"""
SportShield — API Routes: Alerts & Reports
Real-time alerts and PDF/CSV report generation
"""

import csv
import io
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import Alert, Asset, Detection, EnforcementCase, User, get_db
from backend.utils.pdf_generator import PDFGenerator

router = APIRouter(tags=["Alerts & Reports"])


# ═══════════════════════ ALERTS ═══════════════════════════════

alerts_router = APIRouter(prefix="/api/alerts")


@alerts_router.get("/")
def list_alerts(
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Alert).filter(Alert.user_id == current_user.id)
    if unread_only:
        query = query.filter(Alert.is_read == False)
    total = query.count()
    alerts = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "unread": query.filter(Alert.is_read == False).count(),
        "alerts": [_format_alert(a) for a in alerts],
    }


@alerts_router.post("/{alert_id}/read")
def mark_read(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == current_user.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    return {"message": "Marked as read"}


@alerts_router.post("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(Alert).filter(Alert.user_id == current_user.id, Alert.is_read == False).update({"is_read": True})
    db.commit()
    return {"message": "All alerts marked as read"}


def _format_alert(alert: Alert) -> dict:
    return {
        "id": alert.id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "title": alert.title,
        "message": alert.message,
        "metadata": alert.alert_metadata,
        "is_read": alert.is_read,
        "created_at": alert.created_at,
    }


# ═══════════════════════ REPORTS ══════════════════════════════

reports_router = APIRouter(prefix="/api/reports")


@reports_router.get("/csv/detections")
def export_detections_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export all detections as CSV."""
    detections = (
        db.query(Detection)
        .join(Asset)
        .filter(
            Asset.org_id == current_user.org_id
            if current_user.org_id else Asset.user_id == current_user.id
        )
        .order_by(Detection.detected_at.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Detection ID", "Asset ID", "Asset Title",
        "Infringing URL", "Platform", "Domain", "Country",
        "Similarity Score", "Match Type", "Severity", "Status",
        "Detected At", "Resolved At"
    ])

    for d in detections:
        asset = db.query(Asset).filter(Asset.id == d.asset_id).first()
        writer.writerow([
            d.id, d.asset_id, asset.title if asset else "N/A",
            d.detection_url, d.platform, d.domain, d.country_code,
            f"{d.similarity_score:.2%}", d.match_type, d.severity, d.status,
            d.detected_at.isoformat() if d.detected_at else "",
            d.resolved_at.isoformat() if d.resolved_at else "",
        ])

    output.seek(0)
    filename = f"sportshield_detections_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@reports_router.get("/csv/assets")
def export_assets_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export all assets as CSV."""
    query = db.query(Asset)
    if current_user.org_id:
        query = query.filter(Asset.org_id == current_user.org_id)
    else:
        query = query.filter(Asset.user_id == current_user.id)
    assets = query.order_by(Asset.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Asset ID", "Title", "Original Filename", "Type", "Size (KB)",
        "Sport Category", "Status", "Protection Level",
        "PHash", "Watermark ID", "Uploaded At"
    ])

    for a in assets:
        writer.writerow([
            a.id, a.title, a.original_filename, a.file_type,
            round(a.file_size / 1024, 1),
            a.sport_category, a.status, a.protection_level,
            a.phash, a.watermark_id,
            a.created_at.isoformat() if a.created_at else "",
        ])

    output.seek(0)
    filename = f"sportshield_assets_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@reports_router.get("/summary")
def executive_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate executive summary report data."""
    asset_base = db.query(Asset)
    if current_user.org_id:
        asset_base = asset_base.filter(Asset.org_id == current_user.org_id)
    else:
        asset_base = asset_base.filter(Asset.user_id == current_user.id)

    total_assets = asset_base.count()
    protected_assets = asset_base.filter(Asset.status == "protected").count()
    violated_assets = asset_base.filter(Asset.status == "violated").count()

    detection_base = (
        db.query(Detection)
        .join(Asset)
        .filter(
            Asset.org_id == current_user.org_id
            if current_user.org_id else Asset.user_id == current_user.id
        )
    )

    total_detections = detection_base.count()
    active_detections = detection_base.filter(Detection.status == "active").count()
    resolved_detections = detection_base.filter(Detection.status == "resolved").count()
    critical_threats = detection_base.filter(Detection.severity == "critical").count()

    case_base = (
        db.query(EnforcementCase)
        .join(Detection)
        .join(Asset)
        .filter(
            Asset.org_id == current_user.org_id
            if current_user.org_id else Asset.user_id == current_user.id
        )
    )
    total_cases = case_base.count()
    resolved_cases = case_base.filter(EnforcementCase.status == "resolved").count()

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": "All time",
        "assets": {
            "total": total_assets,
            "protected": protected_assets,
            "at_risk": asset_base.filter(Asset.status == "at_risk").count(),
            "violated": violated_assets,
            "protection_rate": round(protected_assets / total_assets * 100, 1) if total_assets > 0 else 100,
        },
        "detections": {
            "total": total_detections,
            "active": active_detections,
            "resolved": resolved_detections,
            "critical": critical_threats,
        },
        "enforcement": {
            "total_cases": total_cases,
            "resolved": resolved_cases,
            "resolution_rate": round(resolved_cases / total_cases * 100, 1) if total_cases > 0 else 0,
        },
        "threat_score": _calculate_threat_score(
            total_assets, violated_assets, critical_threats, active_detections
        ),
    }


@reports_router.get("/pdf/executive")
def export_executive_pdf(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download a professional Executive Summary PDF."""
    summary_data = executive_summary(current_user, db)
    pdf_buffer = PDFGenerator.generate_executive_report(summary_data)
    
    filename = f"sportshield_executive_report_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def _calculate_threat_score(total, violated, critical, active):
    """0-100 threat score for the organization."""
    if total == 0:
        return 0
    violation_rate = (violated / total) * 40
    critical_factor = min(critical * 5, 30)
    active_factor = min(active * 0.5, 30)
    return min(100, round(violation_rate + critical_factor + active_factor, 1))
