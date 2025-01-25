from pydantic import BaseModel, HttpUrl
from typing import List
import requests
from xml.etree import ElementTree
import asyncio
import json
import os
from datetime import datetime
import hashlib
from crawl4ai import AsyncWebCrawler, RateLimiter, CrawlerRunConfig, CacheMode
from crawl4ai.async_dispatcher import SemaphoreDispatcher

class CrawlerOutput(BaseModel):
    url: HttpUrl
    timestamp: datetime
    source: str
    content: str
    success: bool = True  # Defaults to True for successful crawls

class AICrawler(BaseModel):
    output_dir: str = "./output"
    project_name: str = "ai_crawler"
    max_sessions: int = 5

    def __init__(self, **data):
        super().__init__(**data)
        self.dispatcher = SemaphoreDispatcher(
            max_session_permit=self.max_sessions,  # Use max_sessions from the instance
            rate_limiter=RateLimiter(
                base_delay=(0.5, 1.0),
                max_delay=10.0
            )
        )
        self.run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            stream=True  # Enable streaming mode
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

    def save_to_json(self, output: CrawlerOutput):
        """Save CrawlerOutput to a JSON file."""
        filename = os.path.join(self.output_dir, f"{hashlib.md5(str(output.url).encode()).hexdigest()}.json")
        with open(filename, "w") as f:
            f.write(output.model_dump_json(indent=5))

    async def process_url(self, url: str):
        """Process a single URL."""
        print(f"Processing URL: {url}")
        if url.endswith("sitemap.xml"):
            sitemap_urls = self.fetch_sitemap_urls(url)
    
            async with AsyncWebCrawler() as crawler:
                async for result in await crawler.arun_many(
                        urls=sitemap_urls,
                        dispatcher=self.dispatcher,  # Use the dispatcher instance
                        config=self.run_config
                ):
                    output = CrawlerOutput(
                        url=result.url,
                        timestamp=datetime.now(),
                        source=self.project_name,
                        content=result.markdown,
                        success=result.success,
                    )
                    self.save_to_json(output)
        else:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
                output = CrawlerOutput(
                    url=result.url,
                    timestamp=datetime.now(),
                    source=self.project_name,
                    content=result.markdown,
                    success=result.success,
                )
                self.save_to_json(output)
