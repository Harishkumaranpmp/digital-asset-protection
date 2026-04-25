import httpx
from bs4 import BeautifulSoup
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class GenericWebScraper:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)
        # Using a generic search engine url, duckduckgo html version is often easier to scrape
        self.search_url = "https://html.duckduckgo.com/html/"

    async def search_web(self, query: str, max_results: int = 5) -> list:
        """
        Searches the web for the given query.
        """
        results = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = await self.client.post(self.search_url, data={'q': query}, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.find_all('a', class_='result__snippet')
                
                for link in links[:max_results]:
                    href = link.get('href')
                    if href:
                        domain = urlparse(href).netloc
                        results.append({
                            'url': href,
                            'title': link.text.strip(),
                            'platform': 'website',
                            'domain': domain
                        })
        except Exception as e:
            logger.error(f"Web search failed for query '{query}': {e}")
            
        return results

    async def close(self):
        await self.client.aclose()
