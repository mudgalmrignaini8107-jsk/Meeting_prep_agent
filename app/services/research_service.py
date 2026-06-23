# app/services/research_service.py

import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from loguru import logger
from app.config import settings

class ResearchService:
    def __init__(self):
        self.serp_api_url = "https://serpapi.com/search.json"

    async def search_company_news(self, company_name: str) -> List[Dict[str, str]]:
        """
        Search Google News for a company using SerpAPI.
        Returns a list of news items containing title, url, snippet, date, and source.
        """
        if not settings.SERPAPI_API_KEY:
            logger.info(f"SerpAPI API key not set. Returning mock news for: {company_name}")
            return self._get_mock_news(company_name)

        try:
            params = {
                "engine": "google",
                "q": f"{company_name} news",
                "tbm": "nws", # google news tab
                "api_key": settings.SERPAPI_API_KEY,
                "num": 5
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.serp_api_url, params=params, timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    news_results = data.get("news_results", [])
                    
                    results = []
                    for item in news_results[:5]:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "date": item.get("date", ""),
                            "source": item.get("source", "")
                        })
                    return results
                else:
                    logger.error(f"SerpAPI request failed with code {response.status_code}: {response.text}")
                    return self._get_mock_news(company_name)
        except Exception as e:
            logger.error(f"SerpAPI integration error: {e}")
            return self._get_mock_news(company_name)

    async def scrape_website(self, url: str) -> str:
        """
        Scrape a website domain, parse HTML, and return clean textual content.
        """
        if not url:
            return ""
            
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url, headers=headers, timeout=5.0)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()
                        
                    # Get clean text
                    text = soup.get_text(separator=" ")
                    # Collapse whitespace
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase for line in lines for phrase in line.split("  "))
                    clean_text = " ".join(chunk for chunk in chunks if chunk)
                    
                    return clean_text[:3000] # Cap text length to avoid token limits
                else:
                    logger.warning(f"Scraper returned status code {response.status_code} for URL: {url}")
                    return ""
        except Exception as e:
            logger.error(f"Scraper failed for URL {url}: {e}")
            return ""

    def _get_mock_news(self, company_name: str) -> List[Dict[str, str]]:
        return [
            {
                "title": f"{company_name} Expands Real-Time AI Inference Pipelines",
                "url": "https://techcrunch.com/mock-article-1",
                "snippet": f"Under the new architecture, {company_name} will support automated RAG systems natively with ultra-low latencies.",
                "date": "2 days ago",
                "source": "TechCrunch"
            },
            {
                "title": f"Venture Capital Funds leading SaaS player {company_name}",
                "url": "https://venturebeat.com/mock-article-2",
                "snippet": f"The strategic investment validates {company_name}'s developer-first tools for automated calendar analytics.",
                "date": "1 week ago",
                "source": "VentureBeat"
            }
        ]

# Export singleton instance
research_service = ResearchService()
