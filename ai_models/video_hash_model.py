"""
SportShield — Video Hash Model
Extracts keyframes from videos and generates temporal perceptual hashes.
"""

import hashlib
import logging
from typing import Dict, Any

try:
    import cv2
    from PIL import Image
    import imagehash
    VIDEO_HASH_AVAILABLE = True
except ImportError:
    VIDEO_HASH_AVAILABLE = False
    logging.warning("cv2, PIL, or imagehash not installed. Falling back to SHA256.")


class VideoHashModel:
    """
    Handles generation of temporal perceptual hashes for video files by sampling keyframes.
    """

    @staticmethod
    def generate(video_path: str, sample_rate: int = 30) -> Dict[str, Any]:
        """
        Extract frame fingerprints from a video at `sample_rate` intervals.
        Returns temporal hash sequence and an aggregate fingerprint.
        
        Args:
            video_path (str): The absolute or relative path to the video file.
            sample_rate (int): Process 1 out of every `sample_rate` frames.
            
        Returns:
            dict: A dictionary containing the generated hashes and temporal sequence.
        """
        if not VIDEO_HASH_AVAILABLE:
            return VideoHashModel._fallback_hash(video_path)

        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            frame_hashes = []
            frame_idx = 0

            # Read video frame by frame
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # Process only every Nth frame (sample_rate)
                if frame_idx % sample_rate == 0:
                    # Convert BGR (OpenCV) to RGB (PIL)
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_frame = Image.fromarray(rgb_frame)
                    
                    # Generate perceptual hash for this frame
                    ph = str(imagehash.phash(pil_frame, hash_size=8)) # Smaller hash for temporal speed
                    frame_hashes.append(ph)

                frame_idx += 1

            cap.release()

            if not frame_hashes:
                raise ValueError("No frames could be extracted from the video.")

            # Aggregate hash: concatenate first 10 sampled frame hashes and hash them
            # This creates a steady unique ID for the whole video
            combined = "".join(frame_hashes[:10])
            aggregate_hash = hashlib.sha256(combined.encode()).hexdigest()[:32]

            return {
                "phash": aggregate_hash,
                "dhash": aggregate_hash,  # For video, we mirror the aggregate hash for consistency
                "ahash": aggregate_hash,
                "composite_id": aggregate_hash,
                "temporal_hashes": frame_hashes[:50],  # Store up to 50 temporal hashes for partial matching
                "duration_seconds": total_frames / fps if fps > 0 else 0,
                "total_frames": total_frames,
            }

        except Exception as e:
            logging.error(f"Failed to hash video {video_path}: {e}")
            return VideoHashModel._fallback_hash(video_path)

    @staticmethod
    def _fallback_hash(file_path: str) -> Dict[str, Any]:
        """
        SHA256 fallback when dependencies are missing or processing fails.
        """
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    sha256.update(chunk)
        except Exception:
            pass
            
        h = sha256.hexdigest()
        return {
            "phash": h[:16],
            "dhash": h[16:32],
            "ahash": h[32:48],
            "composite_id": h[:32],
            "temporal_hashes": [],
            "duration_seconds": 0,
            "total_frames": 0,
        }
