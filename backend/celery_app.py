import asyncio
from celery import Celery
from backend.config import get_settings

settings = get_settings()

celery_app = Celery(
    "sportshield",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=False,
    broker_transport_options={'max_retries': 1, 'interval_start': 0, 'interval_step': 0, 'interval_max': 0},
    result_backend_transport_options={'max_retries': 1},
    task_always_eager=settings.CELERY_ALWAYS_EAGER,
)

@celery_app.task(name="process_asset_task")
def process_asset_task(asset_id: int):
    """
    Background task to generate fingerprints and thumbnails for a newly uploaded asset.
    """
    from backend.database import SessionLocal, Asset, Detection
    from ai_models.fingerprint_generator import FingerprintGenerator
    from ai_models.duplicate_detector import DuplicateDetector
    import cv2
    import os
    from pathlib import Path
    
    db = SessionLocal()
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return {"status": "error", "message": f"Asset {asset_id} not found"}

        # Generate fingerprint using FingerprintEngine
        from backend.ai.fingerprint import FingerprintEngine
        engine = FingerprintEngine()
        
        if asset.file_type == "image":
            fp = engine.generate_image_fingerprint(asset.file_path)
        else:
            fp = engine.generate_video_fingerprint(asset.file_path)

        asset.phash = fp.get("phash")
        asset.dhash = fp.get("dhash")
        asset.ahash = fp.get("ahash")
        asset.watermark_id = fp.get("watermark_id") or engine.generate_watermark_id()
        asset.hash_algorithm = "fingerprint_engine_v1"
        asset.status = "protected"
        
        # Generate thumbnail for videos
        if asset.file_type == "video":
            try:
                from backend.config import get_settings
                settings = get_settings()
                thumbnail_path = os.path.join(settings.UPLOAD_DIR, "thumbnails", f"{asset.filename}_thumb.jpg")
                
                # Extract first frame as thumbnail
                cap = cv2.VideoCapture(asset.file_path)
                ret, frame = cap.read()
                if ret:
                    cv2.imwrite(thumbnail_path, frame)
                    asset.thumbnail_path = thumbnail_path
                cap.release()
            except Exception as e:
                print(f"Warning: Failed to generate video thumbnail: {e}")
        
        # Trigger duplicate scan immediately against other assets in the DB
        other_assets = db.query(Asset).filter(Asset.id != asset.id).all()
        duplicates = DuplicateDetector.scan_database(fp, other_assets)
        
        # Save any found duplicates as detections
        saved_count = 0
        for dup in duplicates:
            # We treat the newly uploaded asset as the reference, 
            # or we log the newly uploaded asset as violating an existing one.
            # Usually, if we upload an asset and find it already exists, we might flag it.
            # Here we log it as a detection against the new asset.
            detection = Detection(
                asset_id=asset.id,
                detection_url=f"internal://asset/{dup['asset_id']}",
                platform="internal_database",
                similarity_score=dup["similarity_score"],
                match_type=dup["match_type"],
                status="active",
                severity="high" if dup["match_type"] == "exact" else "medium"
            )
            db.add(detection)
            saved_count += 1
            
        if saved_count > 0:
            asset.status = "at_risk"

        db.commit()

        return {"status": "success", "asset_id": asset_id, "duplicates_found": saved_count}
    except Exception as e:
        asset.status = "error"
        db.commit()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(name="run_platform_scan_task")
def run_platform_scan_task(asset_id: int, platforms: list = None):
    """
    Background task to scan platforms for stolen copies of the asset.
    """
    from backend.database import SessionLocal, Asset, Detection
    from backend.ai.crawler import WebCrawler
    
    db = SessionLocal()
    crawler = WebCrawler()
    
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return {"status": "error", "message": f"Asset {asset_id} not found"}

        # Run the crawler in a new event loop since Celery is sync
        try:
            # Python 3.10+ compatible approach
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            detections = loop.run_until_complete(
                crawler.scan_asset(
                    asset_id=asset.id,
                    phash=asset.phash,
                    title=asset.title,
                    tags=asset.tags
                )
            )
            loop.run_until_complete(crawler.close())
        finally:
            loop.close()

        # Save detections to DB
        saved_count = 0
        for d in detections:
            existing = db.query(Detection).filter(
                Detection.asset_id == asset.id,
                Detection.detection_url == d["url"]
            ).first()
            if not existing:
                new_detection = Detection(
                    asset_id=asset.id,
                    detection_url=d["url"],
                    platform=d.get("platform"),
                    domain=d.get("domain"),
                    similarity_score=d.get("similarity_score", 0.0),
                    match_type=d.get("match_type", "partial"),
                    status="pending"
                )
                db.add(new_detection)
                saved_count += 1
                
        db.commit()
        return {"status": "success", "asset_id": asset_id, "new_detections": saved_count}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
