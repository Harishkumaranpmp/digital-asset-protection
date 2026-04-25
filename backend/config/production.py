"""
SportShield — Production Settings Override
Inherits base Settings and applies production-specific validation.
"""

import os
from backend.config import Settings, get_settings


class ProductionSettings(Settings):
    """
    Strictly validated production settings.
    Fails loudly if insecure defaults are detected.
    """
    DEBUG: bool = False

    def model_post_init(self, __context):
        """Validate critical security settings on startup."""
        insecure_defaults = [
            "sportshield-super-secret-change-in-production",
            "jwt-secret-key-change-in-production",
            "changeme",
            "secret",
        ]

        # Enforce strong secrets
        for insecure in insecure_defaults:
            if insecure in self.SECRET_KEY:
                raise ValueError(
                    "❌ SECRET_KEY contains an insecure default value. "
                    "Generate a strong secret: python -c \"import secrets; print(secrets.token_hex(64))\""
                )
            if insecure in self.JWT_SECRET:
                raise ValueError(
                    "❌ JWT_SECRET contains an insecure default value. "
                    "Generate a strong secret: python -c \"import secrets; print(secrets.token_hex(64))\""
                )

        # Ensure PostgreSQL is used (not SQLite) in production
        if "sqlite" in self.DATABASE_URL:
            raise ValueError(
                "❌ SQLite is not allowed in production. "
                "Set DATABASE_URL to a PostgreSQL connection string."
            )

        # Warn if CORS is wide open
        if "*" in self.ALLOWED_ORIGINS:
            import logging
            logging.getLogger("sportshield").warning(
                "⚠️  ALLOWED_ORIGINS contains '*'. "
                "Restrict this to your frontend domain in production."
            )
