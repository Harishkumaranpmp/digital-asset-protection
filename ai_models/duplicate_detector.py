"""
SportShield — Duplicate Detector
Implements Hamming Distance logic to compare perceptual hashes and calculate similarity percentages.
"""

from typing import Dict, Any, List

class DuplicateDetector:
    """
    Compares two media fingerprints to determine similarity, providing match
    confidence and type based on configured threshold rules.
    """

    @staticmethod
    def compare(fp1: Dict[str, Any], fp2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two fingerprints and return similarity score and match type.
        
        Args:
            fp1 (dict): The target fingerprint (e.g., from new upload).
            fp2 (dict): The reference fingerprint (e.g., from database).
            
        Returns:
            dict: Evaluation results containing score and match type.
        """
        scores = []

        # Hash-based similarity (Hamming distance) for image/video composite hashes
        for key in ["phash", "dhash", "ahash"]:
            h1 = fp1.get(key, "")
            h2 = fp2.get(key, "")
            if h1 and h2 and len(h1) == len(h2):
                hamming = sum(c1 != c2 for c1, c2 in zip(h1, h2))
                max_dist = len(h1)
                scores.append(1.0 - (hamming / max_dist))

        if not scores:
            return {"similarity_score": 0.0, "match_type": "unique"}

        # Calculate average similarity across all evaluated hashes
        avg_score = sum(scores) / len(scores)
        score_percentage = round(avg_score * 100, 2)

        # Apply standard similarity rules
        if score_percentage >= 95.0:
            match_type = "exact"
        elif score_percentage >= 80.0:
            match_type = "near_duplicate"
        else:
            match_type = "unique"

        return {
            "similarity_score": score_percentage,
            "match_type": match_type,
            "confidence_score": score_percentage,
        }

    @staticmethod
    def scan_database(target_fp: Dict[str, Any], db_assets: List[Any]) -> List[Dict[str, Any]]:
        """
        Scan a list of database assets to find similar duplicates.
        
        Args:
            target_fp (dict): The newly generated fingerprint.
            db_assets (list): List of SQLAlchemy Asset objects from the database.
            
        Returns:
            list: List of dictionaries detailing matches that are not unique.
        """
        matches = []

        for asset in db_assets:
            # Reconstruct the reference fingerprint dictionary from the database model
            ref_fp = {
                "phash": asset.phash,
                "dhash": asset.dhash,
                "ahash": asset.ahash,
            }
            
            # Skip if database asset is missing hash data
            if not ref_fp["phash"]:
                continue

            result = DuplicateDetector.compare(target_fp, ref_fp)
            
            # If the match is exact or near duplicate, record it
            if result["match_type"] != "unique":
                matches.append({
                    "asset_id": asset.id,
                    "title": asset.title,
                    "filename": asset.original_filename,
                    "similarity_score": result["similarity_score"],
                    "match_type": result["match_type"],
                    "platform": "internal_database",
                })

        # Sort matches by similarity descending
        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        return matches
