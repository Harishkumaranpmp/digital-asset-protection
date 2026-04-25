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
)

@celery_app.task(name="process_asset_task")
def process_asset_task(asset_id: int):
    """
    Background task to generate fingerprints and thumbnails for a newly uploaded asset.
    """
    from backend.database import SessionLocal, Asset, Detection
    from ai_models.fingerprint_generator import FingerprintGenerator
    from ai_models.duplicate_detector import DuplicateDetector
    
    db = SessionLocal()
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return {"status": "error", "message": f"Asset {asset_id} not found"}

        # Generate fingerprint using the new orchestrator
        fp = FingerprintGenerator.generate(asset.file_path, asset.file_type)

        asset.phash = fp.get("phash")
        asset.dhash = fp.get("dhash")
        asset.ahash = fp.get("ahash")
        asset.hash_algorithm = "imagehash_v1" if asset.file_type == "image" else "video_hash_v1"
        asset.status = "protected"
        
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
        loop = asyncio.get_event_loop()
        detections = loop.run_until_complete(
            crawler.scan_asset(
                asset_id=asset.id,
                phash=asset.phash,
                title=asset.title,
                tags=asset.tags
            )
        )
        loop.run_until_complete(crawler.close())

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
