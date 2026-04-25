"""
SportShield — Image Hash Model
Generates perceptual hashes for image files using the imagehash library.
"""

import hashlib
import logging
from typing import Dict, Any

try:
    import imagehash
    from PIL import Image
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False
    logging.warning("imagehash or PIL not installed. Falling back to SHA256.")

class ImageHashModel:
    """
    Handles generation of multiple cryptographic and perceptual hashes for images.
    """

    @staticmethod
    def generate(image_path: str) -> Dict[str, Any]:
        """
        Generate comprehensive fingerprint for an image.
        Returns pHash (perceptual), dHash (difference), aHash (average), and a composite ID.
        
        Args:
            image_path (str): The absolute or relative path to the image file.
            
        Returns:
            dict: A dictionary containing the generated hashes and composite ID.
        """
        if not IMAGEHASH_AVAILABLE:
            return ImageHashModel._fallback_hash(image_path)

        try:
            # Convert image to RGB to handle PNGs with transparency or Grayscale
            img = Image.open(image_path).convert("RGB")

            # Generate perceptual hashes (size=16 generates a 64-character hex string)
            phash = str(imagehash.phash(img, hash_size=16))
            dhash = str(imagehash.dhash(img, hash_size=16))
            ahash = str(imagehash.average_hash(img, hash_size=16))

            # Composite ID is a unique fingerprint derived from all perceptual hashes
            composite_data = f"{phash}{dhash}{ahash}"
            composite_id = hashlib.sha256(composite_data.encode()).hexdigest()[:32]

            return {
                "phash": phash,
                "dhash": dhash,
                "ahash": ahash,
                "composite_id": composite_id,
            }

        except Exception as e:
            logging.error(f"Failed to hash image {image_path}: {e}")
            return ImageHashModel._fallback_hash(image_path)

    @staticmethod
    def _fallback_hash(file_path: str) -> Dict[str, Any]:
        """
        SHA256 fallback when imagehash/PIL are unavailable or processing fails.
        """
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    sha256.update(chunk)
            h = sha256.hexdigest()
        except Exception:
            # Absolute fallback if file cannot be read
            h = hashlib.sha256(str(file_path).encode()).hexdigest()

        return {
            "phash": h[:16],
            "dhash": h[16:32],
            "ahash": h[32:48],
            "composite_id": h[:32],
        }
