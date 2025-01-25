from pydantic import BaseModel, HttpUrl
from typing import List
import requests
from xml.etree import ElementTree
import asyncio
import json
import os
import datetime
import hashlib
from crawl4ai import AsyncWebCrawler, RateLimiter, CrawlerRunConfig, CacheMode
from crawl4ai.async_dispatcher import SemaphoreDispatcher

class CrawlerOutput(BaseModel):
    url: HttpUrl
    timestamp: datetime
    source: str
    content: str
    success: bool = True  # Defaults to True for successful crawls

class AICrawler:
    def __init__(self, output_dir: str = "./output", project_name: str = "ai_crawler", max_sessions: int = 5):
        self.output_dir = output_dir
        self.project_name = project_name
        self.max_sessions = max_sessions

        self.dispatcher = SemaphoreDispatcher(
            max_session_permit=self.max_sessions,
            rate_limiter=RateLimiter(
                base_delay=(0.5, 1.0),
                max_delay=10.0
            )
        )
        self.run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            stream=True
        )
        os.makedirs(self.output_dir, exist_ok=True)

    @staticmethod
    def fetch_sitemap_urls(sitemap_url: str) -> List[str]:
        """Fetch all URLs from a sitemap.xml."""
        try:
            response = requests.get(sitemap_url)
            response.raise_for_status()
            tree = ElementTree.fromstring(response.content)
            urls = [element.text for element in tree.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
            return urls
        except Exception as e:
            print(f"Error fetching sitemap URLs: {e}")
            return []

    def save_to_json(self, url: str, content: str, success: bool):
        """Save CrawlerOutput to a JSON file."""
        filename = os.path.join(self.output_dir, f"{hashlib.md5(url.encode()).hexdigest()}.json")
        output = {
            "url": url,
            "timestamp": datetime.datetime.now().isoformat(),
            "source": self.project_name,
            "content": content,
            "success": success
        }
        with open(filename, "w") as f:
            json.dump(output, f, indent=5)

    async def process_url(self, url: str):
        """Process a single URL."""
        print(f"Processing URL: {url}")
        if url.endswith("sitemap.xml"):
            sitemap_urls = self.fetch_sitemap_urls(url)

            async with AsyncWebCrawler() as crawler:
                async for result in await crawler.arun_many(
                        urls=sitemap_urls,
                        dispatcher=self.dispatcher,
                        config=self.run_config
                ):
                    self.save_to_json(result.url, result.markdown, result.success)
        else:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
                self.save_to_json(result.url, result.markdown, result.success)