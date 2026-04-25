"""
SportShield — Fingerprint Generator
Acts as the central orchestrator to route media assets to the appropriate 
hashing model (Image or Video) based on file type.
"""

import os
import secrets
from typing import Dict, Any

from ai_models.image_hash_model import ImageHashModel
from ai_models.video_hash_model import VideoHashModel

class FingerprintGenerator:
    """
    Central router for generating asset fingerprints. Detects file type 
    and invokes the appropriate model.
    """

    @staticmethod
    def generate_watermark_id() -> str:
        """Generate a cryptographically secure unique ID for watermarking."""
        return secrets.token_hex(16)


    @staticmethod
    def generate(file_path: str, file_type: str = None) -> Dict[str, Any]:
        """
        Generate a fingerprint for a media file.
        
        Args:
            file_path (str): Path to the uploaded media file.
            file_type (str, optional): 'image' or 'video'. If not provided, it will be inferred.
            
        Returns:
            dict: The normalized fingerprint dictionary.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Infer file type if not explicitly provided
        if not file_type:
            ext = file_path.lower().split('.')[-1]
            if ext in ['mp4', 'avi', 'mov', 'mkv', 'webm']:
                file_type = 'video'
            elif ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                file_type = 'image'
            else:
                raise ValueError(f"Unsupported file extension: {ext}")

        # Route to appropriate model
        if file_type == 'video':
            return VideoHashModel.generate(file_path)
        else:
            return ImageHashModel.generate(file_path)
