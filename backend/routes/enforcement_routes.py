"""
SportShield — API Routes: Enforcement
DMCA notices, legal case management, and takedown workflows
"""

import secrets
import smtplib
from email.message import EmailMessage
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.utils.pdf_generator import PDFGenerator

from backend.auth import get_current_user
from backend.config import get_settings
from backend.database import Asset, Detection, EnforcementCase, Alert, User, get_db

router = APIRouter(prefix="/api/enforcement", tags=["Enforcement"])
settings = get_settings()


class CreateCaseRequest(BaseModel):
    detection_id: int
    case_type: str = "dmca"
    respondent_name: Optional[str] = None
    respondent_email: Optional[str] = None
    platform_contact: Optional[str] = None


class UpdateCaseRequest(BaseModel):
    status: Optional[str] = None
    resolution_notes: Optional[str] = None


DMCA_TEMPLATE = """DIGITAL MILLENNIUM COPYRIGHT ACT (DMCA) TAKEDOWN NOTICE

Date: {date}
Case Number: {case_number}

TO: {platform} / {respondent}
RE: Copyright Infringement Notice

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IDENTIFICATION OF INFRINGING MATERIAL

We have detected unauthorized use of our copyrighted sports media asset at the following location:

  Infringing URL: {infringing_url}
  Platform: {platform}
  Detection Date: {detection_date}
  Similarity Score: {similarity}%

IDENTIFICATION OF COPYRIGHTED WORK

  Original Asset: {asset_title}
  Owner: {owner_name} / {org_name}
  Asset ID: {asset_id}
  Fingerprint: {fingerprint}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STATEMENT OF AUTHORITY

I am the authorized representative of {org_name}, the copyright holder of the above-described work.

I have a good faith belief that the use of the copyrighted material described above is not authorized by the copyright owner, its agent, or the law (e.g., as a fair use).

The information in this notification is accurate.

Under penalty of perjury, I am authorized to act on behalf of the copyright owner.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REQUESTED ACTION

Please immediately:
1. Remove or disable access to the infringing material
2. Terminate the account responsible if policy violations are confirmed
3. Confirm removal within 48 hours of receipt

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Powered by SportShield AI Protection Platform
Generated: {generated_at}
"""

CEASE_DESIST_TEMPLATE = """CEASE AND DESIST NOTICE

Date: {date}
Case Number: {case_number}

TO: {respondent}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You are hereby notified that {org_name} holds the exclusive copyright to sports media content 
that has been found at the following URL(s) without authorization:

  URL: {infringing_url}
  Detection Score: {similarity}%

DEMAND

You are required to IMMEDIATELY:

1. CEASE all distribution, reproduction, or display of the infringing content
2. DESIST from any future unauthorized use of our protected content
3. REMOVE all copies of infringing content within 24 hours
4. CONFIRM removal in writing to our legal team

Failure to comply with this notice may result in legal action including injunctive relief 
and monetary damages under applicable copyright law.

This notice does not waive any legal rights or remedies available to {org_name}.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{org_name} Legal Department
Powered by SportShield AI Protection Platform
Generated: {generated_at}
"""


# ─── List Cases ───────────────────────────────────────────────

@router.get("/cases")
def list_cases(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all enforcement cases."""
    query = (
        db.query(EnforcementCase)
        .join(Detection)
        .join(Asset)
        .filter(
            Asset.org_id == current_user.org_id
            if current_user.org_id else Asset.user_id == current_user.id
        )
    )

    if status:
        query = query.filter(EnforcementCase.status == status)

    total = query.count()
    cases = query.order_by(EnforcementCase.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "cases": [_format_case(c, db) for c in cases],
    }


# ─── Create Case ──────────────────────────────────────────────

@router.post("/cases", status_code=201)
def create_case(
    req: CreateCaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Open an enforcement case for a detection."""
    detection = db.query(Detection).filter(Detection.id == req.detection_id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")

    # Check existing case
    existing = db.query(EnforcementCase).filter(
        EnforcementCase.detection_id == req.detection_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Enforcement case already exists for this detection")

    # Generate case number
    case_number = f"SS-{datetime.utcnow().strftime('%Y%m')}-{secrets.token_hex(3).upper()}"

    case = EnforcementCase(
        detection_id=req.detection_id,
        case_number=case_number,
        case_type=req.case_type,
        respondent_name=req.respondent_name,
        respondent_email=req.respondent_email,
        platform_contact=req.platform_contact,
        status="draft",
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    return _format_case(case, db)


# ─── Generate DMCA Notice ─────────────────────────────────────

@router.get("/cases/{case_id}/notice")
def generate_notice(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a DMCA or Cease & Desist notice for a case."""
    case = db.query(EnforcementCase).filter(EnforcementCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    detection = db.query(Detection).filter(Detection.id == case.detection_id).first()
    asset = db.query(Asset).filter(Asset.id == detection.asset_id).first()
    user = db.query(User).filter(User.id == asset.user_id).first()

    from backend.database import Organization
    org = db.query(Organization).filter(Organization.id == asset.org_id).first() if asset.org_id else None
    org_name = org.name if org else (user.full_name or user.username)

    vars = {
        "date": datetime.utcnow().strftime("%B %d, %Y"),
        "case_number": case.case_number,
        "platform": detection.platform or "Unknown Platform",
        "respondent": case.respondent_name or detection.domain or "Content Owner",
        "infringing_url": detection.detection_url,
        "detection_date": detection.detected_at.strftime("%B %d, %Y") if detection.detected_at else "Unknown",
        "similarity": int(detection.similarity_score * 100),
        "asset_title": asset.title or asset.original_filename,
        "owner_name": user.full_name or user.username,
        "org_name": org_name,
        "asset_id": str(asset.id),
        "fingerprint": asset.phash or "N/A",
        "generated_at": datetime.utcnow().isoformat(),
    }

    template = DMCA_TEMPLATE if case.case_type == "dmca" else CEASE_DESIST_TEMPLATE
    notice_text = template.format(**vars)

    # Save notice in case
    case.notice_content = notice_text
    db.commit()

    return {"case_id": case_id, "notice": notice_text, "case_type": case.case_type}


# ─── Download PDF Notice ──────────────────────────────────────

@router.get("/cases/{case_id}/pdf")
def download_notice_pdf(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download a professional PDF version of the legal notice."""
    case = db.query(EnforcementCase).filter(EnforcementCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    detection = db.query(Detection).filter(Detection.id == case.detection_id).first()
    asset = db.query(Asset).filter(Asset.id == detection.asset_id).first()
    user = db.query(User).filter(User.id == asset.user_id).first()

    from backend.database import Organization
    org = db.query(Organization).filter(Organization.id == asset.org_id).first() if asset.org_id else None
    org_name = org.name if org else (user.full_name or user.username)

    data = {
        "notice_title": "DMCA TAKEDOWN NOTICE" if case.case_type == "dmca" else "CEASE AND DESIST NOTICE",
        "date": datetime.utcnow().strftime("%B %d, %Y"),
        "case_number": case.case_number,
        "platform": detection.platform or "Unknown Platform",
        "respondent": case.respondent_name or detection.domain or "Content Owner",
        "infringing_url": detection.detection_url,
        "detection_date": detection.detected_at.strftime("%B %d, %Y") if detection.detected_at else "Unknown",
        "similarity": int(detection.similarity_score * 100),
        "asset_title": asset.title or asset.original_filename,
        "owner_name": user.full_name or user.username,
        "org_name": org_name,
        "fingerprint": asset.phash or "N/A",
        "generated_at": datetime.utcnow().isoformat(),
    }

    pdf_buffer = PDFGenerator.generate_legal_notice(data)
    
    filename = f"SportShield_Notice_{case.case_number}.pdf"
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ─── Send Notice ──────────────────────────────────────────────

@router.post("/cases/{case_id}/send")
def send_notice(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark notice as sent and update case status."""
    case = db.query(EnforcementCase).filter(EnforcementCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Send Email
    if case.notice_content and case.respondent_email and settings.SMTP_SERVER and settings.SMTP_USER:
        try:
            msg = EmailMessage()
            msg.set_content(case.notice_content)
            msg['Subject'] = f"SportShield DMCA Takedown Notice - Case {case.case_number}"
            msg['From'] = settings.SENDER_EMAIL
            msg['To'] = case.respondent_email

            server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            print(f"Warning: Failed to send email via SMTP: {e}")
            # In a real system, we might fail the request or queue it for retry
            # For this demo, we'll just print and continue

    case.status = "sent"
    case.notice_sent_at = datetime.utcnow()
    db.commit()

    # Update detection status
    detection = db.query(Detection).filter(Detection.id == case.detection_id).first()
    if detection:
        detection.status = "dmca_sent"

    # Alert
    alert = Alert(
        user_id=current_user.id,
        alert_type="dmca_sent",
        severity="info",
        title="DMCA Notice Sent",
        message=f"DMCA notice for case {case.case_number} has been marked as sent.",
        alert_metadata={"case_id": case_id}
    )
    db.add(alert)
    db.commit()

    return {"message": "Notice marked as sent", "case": _format_case(case, db)}


# ─── Update Case ──────────────────────────────────────────────

@router.patch("/cases/{case_id}")
def update_case(
    case_id: int,
    req: UpdateCaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    case = db.query(EnforcementCase).filter(EnforcementCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    valid = ["draft", "sent", "acknowledged", "resolved", "escalated"]
    if req.status and req.status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status: {valid}")

    if req.status:
        case.status = req.status
        if req.status == "resolved":
            case.resolved_at = datetime.utcnow()
    if req.resolution_notes:
        case.resolution_notes = req.resolution_notes

    db.commit()
    return _format_case(case, db)


# ─── Stats ────────────────────────────────────────────────────

@router.get("/stats")
def enforcement_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(EnforcementCase)
        .join(Detection)
        .join(Asset)
        .filter(
            Asset.org_id == current_user.org_id
            if current_user.org_id else Asset.user_id == current_user.id
        )
    )
    total = query.count()
    sent = query.filter(EnforcementCase.status == "sent").count()
    resolved = query.filter(EnforcementCase.status == "resolved").count()
    pending = query.filter(EnforcementCase.status == "draft").count()

    return {
        "total_cases": total,
        "sent": sent,
        "resolved": resolved,
        "pending": pending,
        "resolution_rate": round(resolved / total * 100, 1) if total > 0 else 0,
    }


def _format_case(case: EnforcementCase, db: Session) -> dict:
    detection = db.query(Detection).filter(Detection.id == case.detection_id).first()
    return {
        "id": case.id,
        "case_number": case.case_number,
        "case_type": case.case_type,
        "detection_id": case.detection_id,
        "detection_url": detection.detection_url if detection else None,
        "platform": detection.platform if detection else None,
        "respondent_name": case.respondent_name,
        "respondent_email": case.respondent_email,
        "status": case.status,
        "notice_sent_at": case.notice_sent_at,
        "resolved_at": case.resolved_at,
        "resolution_notes": case.resolution_notes,
        "created_at": case.created_at,
    }
