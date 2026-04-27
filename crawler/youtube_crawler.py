import yt_dlp
import logging

logger = logging.getLogger(__name__)

class YouTubeCrawler:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'default_search': 'ytsearch',
            'no_warnings': True,
            'ignoreerrors': True
        }

    def search_videos(self, query: str, max_results: int = 5) -> list:
        """
        Searches YouTube for the given query and returns metadata.
        """
        results = []
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                search_query = f"ytsearch{max_results}:{query}"
                info = ydl.extract_info(search_query, download=False)
                
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            results.append({
                                'url': f"https://www.youtube.com/watch?v={entry.get('id')}",
                                'title': entry.get('title'),
                                'duration': entry.get('duration'),
                                'view_count': entry.get('view_count'),
                                'uploader': entry.get('uploader'),
                                'thumbnail': entry.get('thumbnail'),
                                'platform': 'youtube',
                                'domain': 'youtube.com'
                            })
        except Exception as e:
            logger.error(f"YouTube search failed for query '{query}': {e}")
            
        return results
