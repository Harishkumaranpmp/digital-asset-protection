"""
SportShield AI Engine — Google Gemini Analyzer
Uses Gemini Vision API for intelligent content classification and analysis
"""

import base64
import json
import os
from pathlib import Path
from typing import Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from backend.config import get_settings

settings = get_settings()


class GeminiAnalyzer:
    """Google Gemini Vision API integration for content intelligence."""

    def __init__(self):
        if GEMINI_AVAILABLE and settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            self.available = True
        else:
            self.available = False

    def analyze_image(self, image_path: str) -> dict:
        """
        Analyze an image with Gemini Vision to extract:
        - Sport category
        - Content description
        - Key subjects / teams
        - Copyright risk assessment
        """
        if not self.available:
            return self._mock_analysis(image_path)

        try:
            with open(image_path, "rb") as f:
                image_data = f.read()

            mime_type = self._detect_mime(image_path)

            prompt = """Analyze this sports media image and return a JSON response with:
{
  "sport_category": "football|basketball|soccer|tennis|baseball|other",
  "description": "Brief description of what's happening",
  "subjects": ["list", "of", "key", "subjects"],
  "teams_mentioned": ["team names if visible"],
  "has_logos": true/false,
  "has_watermarks": true/false,
  "content_type": "game_action|portrait|stadium|celebration|training|other",
  "copyright_risk": "low|medium|high",
  "copyright_notes": "Why this risk level",
  "is_sports_media": true/false,
  "quality_score": 0.0-1.0
}
Respond ONLY with valid JSON."""

            response = self.model.generate_content([
                {"mime_type": mime_type, "data": image_data},
                prompt
            ])

            text = response.text.strip()
            # Extract JSON from response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            result = json.loads(text)
            result["analysis_source"] = "gemini"
            return result

        except Exception as e:
            return self._mock_analysis(image_path)

    def analyze_copyright_violation(self, original_path: str, suspect_path: str) -> dict:
        """
        Compare two images and assess copyright violation probability.
        """
        if not self.available:
            return {
                "violation_probability": 0.75,
                "violation_type": "unauthorized_copy",
                "analysis": "Gemini API not configured. Using fallback similarity only.",
                "legal_assessment": "Manual review recommended",
                "confidence": "low"
            }

        try:
            def load_img(path):
                with open(path, "rb") as f:
                    return f.read()

            orig_data = load_img(original_path)
            susp_data = load_img(suspect_path)
            orig_mime = self._detect_mime(original_path)
            susp_mime = self._detect_mime(suspect_path)

            prompt = """I'm showing you two images. The first is the ORIGINAL protected sports media asset. 
The second is a SUSPECTED unauthorized copy or derivative.

Analyze and return JSON:
{
  "violation_probability": 0.0-1.0,
  "violation_type": "exact_copy|cropped|color_altered|watermark_removed|composite|unrelated",
  "modifications_detected": ["list", "of", "changes"],
  "analysis": "Detailed analysis",
  "legal_assessment": "Your assessment of copyright violation",
  "confidence": "low|medium|high"
}
Respond ONLY with valid JSON."""

            response = self.model.generate_content([
                {"mime_type": orig_mime, "data": orig_data},
                {"mime_type": susp_mime, "data": susp_data},
                prompt
            ])

            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            result = json.loads(text)
            result["analysis_source"] = "gemini"
            return result

        except Exception as e:
            return {
                "violation_probability": 0.5,
                "violation_type": "unknown",
                "analysis": f"Analysis failed: {str(e)}",
                "legal_assessment": "Manual review required",
                "confidence": "low",
                "analysis_source": "fallback"
            }

    @staticmethod
    def _detect_mime(path: str) -> str:
        ext = Path(path).suffix.lower()
        return {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".webp": "image/webp",
            ".gif": "image/gif"
        }.get(ext, "image/jpeg")

    @staticmethod
    def _mock_analysis(image_path: str) -> dict:
        """Fallback analysis when Gemini is unavailable."""
        return {
            "sport_category": "sports",
            "description": "Sports media asset — Gemini API not configured",
            "subjects": [],
            "teams_mentioned": [],
            "has_logos": False,
            "has_watermarks": False,
            "content_type": "game_action",
            "copyright_risk": "medium",
            "copyright_notes": "Configure GEMINI_API_KEY for full analysis",
            "is_sports_media": True,
            "quality_score": 0.7,
            "analysis_source": "mock"
        }
