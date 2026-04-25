"""
SportShield AI Engine — Web Crawler & Detection Scanner
Simulates web scanning to detect unauthorized copies of assets
"""

import asyncio
import hashlib
import random
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

import httpx

from crawler.youtube_crawler import YouTubeCrawler
from crawler.web_scraper import GenericWebScraper
from crawler.instagram_crawler import InstagramCrawler


PLATFORM_DOMAINS = {
    "youtube": ["youtube.com", "youtu.be"],
    "instagram": ["instagram.com"],
    "twitter": ["twitter.com", "x.com"],
    "facebook": ["facebook.com", "fb.com"],
    "tiktok": ["tiktok.com"],
    "reddit": ["reddit.com", "redd.it"],
}

SPORTS_SITES = [
    "espn.com", "bleacherreport.com", "cbssports.com",
    "nbcsports.com", "foxsports.com", "sportsingnews.com",
    "goal.com", "marca.com", "skysports.com"
]


def detect_platform(url: str) -> str:
    """Detect which platform a URL belongs to."""
    parsed = urlparse(url.lower())
    domain = parsed.netloc.replace("www.", "")
    for platform, domains in PLATFORM_DOMAINS.items():
        if any(d in domain for d in domains):
            return platform
    if any(s in domain for s in SPORTS_SITES):
        return "sports_site"
    return "website"


class WebCrawler:
    """
    Web crawler that searches for unauthorized copies of protected assets.
    Integrates with yt-dlp for YouTube and httpx for generic web search.
    """

    def __init__(self):
        self.youtube_crawler = YouTubeCrawler()
        self.web_scraper = GenericWebScraper()
        self.instagram_crawler = InstagramCrawler()

    async def scan_asset(
        self,
        asset_id: int,
        phash: str,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        job_id: Optional[int] = None,
        progress_callback=None
    ) -> List[dict]:
        """
        Run a comprehensive scan for unauthorized copies of an asset.
        Returns list of detection results.
        """
        detections = []

        # Build search queries
        queries = []
        if title:
            queries.append(title)
        if tags:
            queries.extend(tags[:3])
        queries.append(f"sports media {phash[:8]}")  # Hash-based query

        platforms_to_scan = list(PLATFORM_DOMAINS.keys()) + ["sports_site", "website"]
        total_steps = len(queries) * len(platforms_to_scan)
        step = 0

        for query in queries:
            for platform in platforms_to_scan:
                # Simulate scanning delay
                await asyncio.sleep(0.1)
                step += 1

                if progress_callback:
                    progress = (step / total_steps) * 100
                    await progress_callback(progress)

                # Simulate finding matches (in production: real API calls)
                matches = await self._simulate_platform_scan(
                    platform=platform,
                    query=query,
                    asset_phash=phash,
                )

                detections.extend(matches)

        # Deduplicate by URL
        seen_urls = set()
        unique = []
        for d in detections:
            if d["url"] not in seen_urls:
                seen_urls.add(d["url"])
                unique.append(d)

        return unique

    async def _simulate_platform_scan(
        self,
        platform: str,
        query: str,
        asset_phash: str,
    ) -> List[dict]:
        """
        Scan a platform using real crawlers.
        """
        results = []
        
        # Real scanning
        if platform == "youtube":
            # Run the synchronous yt-dlp in an executor
            loop = asyncio.get_event_loop()
            yt_results = await loop.run_in_executor(None, self.youtube_crawler.search_videos, query, 3)
            
            for item in yt_results:
                # Mock similarity for now, full version would download thumbnail and compare
                sim = random.uniform(0.60, 0.99)
                results.append(self._format_result(item, platform, sim))
                
        elif platform in ["sports_site", "website"]:
            web_results = await self.web_scraper.search_web(query, 3)
            for item in web_results:
                sim = random.uniform(0.60, 0.99)
                results.append(self._format_result(item, platform, sim))

        elif platform == "instagram":
            # Simulate a hashtag scan based on keywords
            tag = query.split()[0] if query else "sports"
            ig_results = await self.instagram_crawler.scan_hashtag(tag, 3)
            for item in ig_results:
                sim = random.uniform(0.60, 0.99)
                results.append(self._format_result(item, platform, sim))

        # We leave other platforms simulated or empty for now
        
        return results

    def _format_result(self, item: dict, platform: str, similarity: float) -> dict:
        severity = "critical" if similarity > 0.95 else "high" if similarity > 0.85 else "medium"
        return {
            "url": item['url'],
            "platform": platform,
            "domain": item['domain'],
            "similarity_score": round(similarity, 4),
            "match_type": "exact" if similarity > 0.95 else "modified" if similarity > 0.80 else "partial",
            "severity": severity,
            "detected_at": datetime.utcnow().isoformat(),
            "country_code": random.choice(["US", "GB", "IN", "DE", "BR", "AU", "FR", "ES"]),
            "latitude": random.uniform(-60, 70),
            "longitude": random.uniform(-180, 180),
        }

    @staticmethod
    def _generate_fake_url(platform: str, rng: random.Random) -> str:
        """Generate realistic-looking URLs for simulation."""
        slugs = [
            "watch-nba-highlights-2024", "leaked-match-footage",
            "champions-league-goals", "super-bowl-replay",
            "world-cup-moments", "nfl-best-plays",
            "sports-clips-collection", "game-highlights-hd"
        ]
        slug = rng.choice(slugs)
        ids = rng.randint(10000, 99999999)

        url_templates = {
            "youtube": f"https://youtube.com/watch?v={rng.randint(100000, 999999):07d}aB",
            "instagram": f"https://instagram.com/p/{slug[:8]}{ids}/",
            "twitter": f"https://x.com/user{ids}/status/{ids}{ids}",
            "facebook": f"https://facebook.com/video/{ids}/",
            "tiktok": f"https://tiktok.com/@sports{ids}/video/{ids}",
            "reddit": f"https://reddit.com/r/sports/comments/{slug[:6]}/{slug}/",
            "sports_site": f"https://sportclips{ids % 100}.com/videos/{slug}",
            "website": f"https://sports-stream{ids % 50}.net/{slug}-{ids}",
        }
        return url_templates.get(platform, f"https://unknown-site-{ids}.com/{slug}")

    async def close(self):
        await self.web_scraper.close()
