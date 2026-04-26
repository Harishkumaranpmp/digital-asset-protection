"""
SportShield — Database Seed Script
Creates the initial admin user and demo organization for first launch.
Run once after the database tables are created.

Usage:
    python scripts/seed_db.py
    (or inside Docker) docker compose exec api python scripts/seed_db.py
"""

import sys
import os

# Allow importing backend modules from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import SessionLocal, create_tables, Organization, User
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed():
    print("[SportShield Seed] Initializing database tables...")
    create_tables()

    db = SessionLocal()
    try:
        # ── Seed Organization ────────────────────────────────
        org = db.query(Organization).filter(Organization.name == "SportShield Demo").first()
        if not org:
            org = Organization(
                name="SportShield Demo",
                slug="sportshield-demo",
                plan="enterprise",
                api_key="demo-api-key-12345",
                max_assets=10000,
                max_scans_per_month=50000,
            )
            db.add(org)
            db.flush()
            print(f"[Seed] Created organization: SportShield Demo (ID: {org.id})")
        else:
            print(f"[Seed] Organization already exists (ID: {org.id})")

        # ── Seed Admin User ──────────────────────────────────
        admin_email = os.getenv("ADMIN_EMAIL", "admin@sportshield.ai")
        admin_password = os.getenv("ADMIN_PASSWORD", "SportShield2024!")

        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(
                email=admin_email,
                username="admin",
                full_name="SportShield Administrator",
                password_hash=pwd_ctx.hash(admin_password),
                role="admin",
                org_id=org.id,
                is_active=True,
            )
            db.add(admin)
            print(f"[Seed] Created admin user: {admin_email}")
            print(f"[Seed] Default password: {admin_password}")
            print(f"[Seed] CHANGE THIS PASSWORD immediately after first login!")
        else:
            print(f"[Seed] Admin user already exists: {admin_email}")

        db.commit()
        print("[SportShield Seed] Database seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"[SportShield Seed] Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
