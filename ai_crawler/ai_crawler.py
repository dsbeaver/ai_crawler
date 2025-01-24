from pydantic import BaseModel, HttpUrl, validator
from typing import List
import requests
from xml.etree import ElementTree
import asyncio
import json
import os
from datetime import datetime
import hashlib
from crawl4ai import AsyncWebCrawler  # Assuming craw4ai provides this class

class CrawlerOutput(BaseModel):
    url: HttpUrl
    timestamp: datetime
    source: str
    content: str
    success: bool = True  # Defaults to True for successful crawls

class AICrawler(BaseModel):
    output_dir: str = "./output"
    project_name: str = "ai_crawler"

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
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
                results = await crawler.arun_many(urls=sitemap_urls)
                for result in results:
                    output = CrawlerOutput(
                        url=result.url,
                        timestamp=datetime.now(),
                        source=self.project_name,
                        content=result.markdown,
                        success=result.success,
                    )
                    self.save_to_json(output)

            #for sitemap_url in sitemap_urls:
            #    await self.process_url(sitemap_url)
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

    async def process_batch(self, urls: List[str]):
        """Process a batch of URLs."""
        async with AsyncWebCrawler() as crawler:
            results = await crawler.arun_many(urls)
            for result in results:
                output = CrawlerOutput(
                    url=result.url,
                    timestamp=datetime.now(),
                    source=self.project_name,
                    content=result.markdown,
                    success=result.success,
                )
                self.save_to_json(output)


