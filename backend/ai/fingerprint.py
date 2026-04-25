"""
SportShield AI Engine — Digital Fingerprinting
Generates perceptual hashes and similarity vectors for images and videos
"""

import hashlib
import json
import os
import secrets
from pathlib import Path
from typing import Optional, Tuple
import numpy as np

try:
    import imagehash
    from PIL import Image
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    # Initialize model lazily
    clip_model = None
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class FingerprintEngine:
    """Generates multi-algorithm fingerprints for media assets."""

    # ─── Image Fingerprinting ─────────────────────────────────

    @staticmethod
    def generate_image_fingerprint(image_path: str) -> dict:
        """
        Generate comprehensive fingerprint for an image.
        Returns pHash, dHash, aHash and a composite similarity vector.
        """
        if not IMAGEHASH_AVAILABLE:
            return FingerprintEngine._fallback_hash(image_path)

        try:
            img = Image.open(image_path).convert("RGB")

            phash = str(imagehash.phash(img, hash_size=16))
            dhash = str(imagehash.dhash(img, hash_size=16))
            ahash = str(imagehash.average_hash(img, hash_size=16))
            whash = str(imagehash.whash(img))

            # Generate feature vector
            feature_vector = []
            if TRANSFORMERS_AVAILABLE:
                global clip_model
                if clip_model is None:
                    try:
                        clip_model = SentenceTransformer('clip-ViT-B-32')
                    except Exception:
                        pass
                
                if clip_model:
                    emb = clip_model.encode(img)
                    feature_vector = emb.tolist()
            
            # Fallback to DCT if CLIP fails or is not available
            if not feature_vector:
                img_resized = img.resize((64, 64))
                img_array = np.array(img_resized, dtype=np.float32)
                img_gray = np.mean(img_array, axis=2)
                dct = FingerprintEngine._dct2(img_gray)
                feature_vector = dct[:8, :8].flatten().tolist()
                
                # Normalize vector
                norm = np.linalg.norm(feature_vector)
                if norm > 0:
                    feature_vector = (np.array(feature_vector) / norm).tolist()

            return {
                "phash": phash,
                "dhash": dhash,
                "ahash": ahash,
                "whash": whash,
                "feature_vector": feature_vector,
                "composite_id": hashlib.sha256(f"{phash}{dhash}{ahash}".encode()).hexdigest()[:32],
            }

        except Exception as e:
            return FingerprintEngine._fallback_hash(image_path)

    @staticmethod
    def _dct2(block: np.ndarray) -> np.ndarray:
        """2D Discrete Cosine Transform."""
        from scipy.fft import dct as scipy_dct
        try:
            return scipy_dct(scipy_dct(block.T, norm='ortho').T, norm='ortho')
        except ImportError:
            # Manual DCT approximation without scipy
            N = block.shape[0]
            result = np.zeros_like(block)
            for u in range(N):
                for v in range(N):
                    s = 0.0
                    for x in range(N):
                        for y in range(N):
                            s += block[x, y] * np.cos((2*x+1)*u*np.pi/(2*N)) * np.cos((2*y+1)*v*np.pi/(2*N))
                    cu = (1/np.sqrt(N)) if u == 0 else np.sqrt(2/N)
                    cv = (1/np.sqrt(N)) if v == 0 else np.sqrt(2/N)
                    result[u, v] = cu * cv * s
            return result

    @staticmethod
    def _fallback_hash(file_path: str) -> dict:
        """SHA256 fallback when imagehash/PIL unavailable."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        h = sha256.hexdigest()
        return {
            "phash": h[:16],
            "dhash": h[16:32],
            "ahash": h[32:48],
            "whash": h[48:64],
            "feature_vector": [],
            "composite_id": h[:32],
        }

    # ─── Video Fingerprinting ─────────────────────────────────

    @staticmethod
    def generate_video_fingerprint(video_path: str, sample_rate: int = 30) -> dict:
        """
        Extract frame fingerprints from a video at `sample_rate` intervals.
        Returns temporal hash sequence + aggregate fingerprint.
        """
        if not OPENCV_AVAILABLE:
            return FingerprintEngine._fallback_hash(video_path)

        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            frame_hashes = []
            frame_vectors = []
            frame_idx = 0

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % sample_rate == 0:
                    # Convert frame to PIL for imagehash
                    if IMAGEHASH_AVAILABLE:
                        pil_frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        ph = str(imagehash.phash(pil_frame))
                        frame_hashes.append(ph)

                    # Extract color histogram as feature
                    hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                    hist = cv2.normalize(hist, hist).flatten().tolist()
                    frame_vectors.append(hist[:64])  # Keep 64-dim

                frame_idx += 1

            cap.release()

            # Aggregate hash
            combined = "".join(frame_hashes[:10])
            aggregate_hash = hashlib.sha256(combined.encode()).hexdigest()[:32]

            # Mean temporal vector
            if frame_vectors:
                mean_vector = np.mean(frame_vectors, axis=0).tolist()
            else:
                mean_vector = []

            return {
                "phash": aggregate_hash,
                "dhash": aggregate_hash,
                "ahash": aggregate_hash,
                "whash": aggregate_hash,
                "temporal_hashes": frame_hashes[:50],  # Store first 50 frame hashes
                "feature_vector": mean_vector,
                "duration_seconds": total_frames / fps if fps > 0 else 0,
                "total_frames": total_frames,
                "composite_id": aggregate_hash,
            }

        except Exception as e:
            return FingerprintEngine._fallback_hash(video_path)

    # ─── Watermarking ─────────────────────────────────────────

    @staticmethod
    def embed_watermark(image_path: str, watermark_id: str, output_path: str) -> bool:
        """
        Embed an invisible LSB watermark into an image.
        Each pixel's blue channel LSB encodes part of the watermark_id.
        """
        try:
            img = Image.open(image_path).convert("RGB")
            pixels = list(img.getdata())

            # Encode watermark_id as UTF-8 binary string
            binary_data = ''.join(format(ord(c), '08b') for c in watermark_id[:32])
            binary_data += '00000000'  # Null terminator

            modified_pixels = []
            data_idx = 0

            for pixel in pixels:
                r, g, b = pixel
                if data_idx < len(binary_data):
                    # Modify LSB of blue channel
                    b = (b & ~1) | int(binary_data[data_idx])
                    data_idx += 1
                modified_pixels.append((r, g, b))

            img.putdata(modified_pixels)
            img.save(output_path)
            return True

        except Exception:
            return False

    @staticmethod
    def extract_watermark(image_path: str, length: int = 32) -> Optional[str]:
        """
        Extract LSB watermark from an image.
        Returns the watermark string or None if detection fails.
        """
        try:
            img = Image.open(image_path).convert("RGB")
            pixels = list(img.getdata())

            binary_data = ""
            for pixel in pixels[:length * 8 + 8]:
                binary_data += str(pixel[2] & 1)  # Blue channel LSB

            # Decode binary to string
            chars = []
            for i in range(0, len(binary_data), 8):
                byte = binary_data[i:i+8]
                if byte == '00000000':
                    break
                chars.append(chr(int(byte, 2)))

            result = ''.join(chars)
            return result if result else None

        except Exception:
            return None

    # ─── Similarity Comparison ────────────────────────────────

    @staticmethod
    def compare_fingerprints(fp1: dict, fp2: dict) -> dict:
        """
        Compare two fingerprints and return similarity score (0-1).
        Uses multi-algorithm voting for robust detection.
        """
        scores = []

        # Hash-based similarity (Hamming distance)
        for key in ("phash", "dhash", "ahash"):
            h1 = fp1.get(key, "")
            h2 = fp2.get(key, "")
            if h1 and h2 and len(h1) == len(h2):
                hamming = sum(c1 != c2 for c1, c2 in zip(h1, h2))
                max_dist = len(h1)
                scores.append(1.0 - hamming / max_dist)

        # Vector cosine similarity
        v1 = fp1.get("feature_vector", [])
        v2 = fp2.get("feature_vector", [])
        if v1 and v2 and len(v1) == len(v2):
            a, b = np.array(v1), np.array(v2)
            norm_a, norm_b = np.linalg.norm(a), np.linalg.norm(b)
            if norm_a > 0 and norm_b > 0:
                cosine_sim = float(np.dot(a, b) / (norm_a * norm_b))
                scores.append(max(0.0, cosine_sim))

        if not scores:
            return {"similarity_score": 0.0, "match_type": "unknown", "confidence": "low"}

        avg_score = np.mean(scores)
        max_score = max(scores)

        # Determine match type
        if max_score >= 0.98:
            match_type = "exact"
        elif max_score >= 0.85:
            match_type = "modified"
        elif max_score >= 0.65:
            match_type = "partial"
        else:
            match_type = "no_match"

        confidence = "high" if len(scores) >= 3 else "medium" if len(scores) >= 2 else "low"

        return {
            "similarity_score": round(float(avg_score), 4),
            "max_score": round(float(max_score), 4),
            "match_type": match_type,
            "confidence": confidence,
            "individual_scores": {k: round(v, 4) for k, v in zip(["phash", "dhash", "ahash", "cosine"], scores)},
        }

    @staticmethod
    def generate_watermark_id() -> str:
        """Generate a unique watermark identifier."""
        return secrets.token_hex(16)
