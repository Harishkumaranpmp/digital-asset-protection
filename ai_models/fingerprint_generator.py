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
            file_path (str): Path to the uploaded media file (or URL).
            file_type (str, optional): 'image' or 'video'.
        """
        temp_file = None
        
        # Download if it's a URL
        if file_path.startswith("http"):
            import requests
            import tempfile
            from pathlib import Path
            
            ext = Path(file_path.split("?")[0]).suffix or ".tmp"
            fd, temp_file = tempfile.mkstemp(suffix=ext)
            os.close(fd)
            
            try:
                response = requests.get(file_path, timeout=60)
                response.raise_for_status()
                with open(temp_file, "wb") as f:
                    f.write(response.content)
                file_path = temp_file
            except Exception as e:
                if temp_file and os.path.exists(temp_file):
                    os.remove(temp_file)
                raise RuntimeError(f"Failed to download asset from URL: {e}")

        try:
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
                result = VideoHashModel.generate(file_path)
            else:
                result = ImageHashModel.generate(file_path)
            
            return result
        finally:
            # Clean up temp file if we created one
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
