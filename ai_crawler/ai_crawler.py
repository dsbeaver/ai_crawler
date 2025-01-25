from pydantic import BaseModel, HttpUrl
from typing import List
import requests
from xml.etree import ElementTree
import asyncio
import json
import os
import datetime
import hashlib
from crawl4ai import AsyncWebCrawler, RateLimiter, CrawlerRunConfig, CacheMode, BrowserConfig, CrawlerMonitor, DisplayMode
from crawl4ai.async_dispatcher import SemaphoreDispatcher, MemoryAdaptiveDispatcher
from time import sleep

def chunk_list(lst, size):
    """Yield successive sublists of given size."""
    for i in range(0, len(lst), size):
        yield lst[i:i + size]




class CrawlerOutput(BaseModel):
    class Config:
        arbitrary_types_allowed=True

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
        self.browser_conf = BrowserConfig(
            browser_type="chromium",
            headless=False,
            text_mode=True,
            user_agent_mode="random",
            light_mode=True,
            verbose=True

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

    async def process_urls(self, urls: list[str]):
        print(f"Processing {len(urls)} urls")
        browser_config = BrowserConfig(headless=True, verbose=False)
        run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, 
                                      check_robots_txt=True,
                                      semaphore_count=self.max_sessions )

        monitor=CrawlerMonitor(         # Optional monitoring
                max_visible_rows=15,
                display_mode=DisplayMode.DETAILED
        )
        rate_limiter=RateLimiter(       # Optional rate limiting
                base_delay=(1.0, 2.0),
                max_delay=30.0,
                max_retries=2
        ) 
        md = MemoryAdaptiveDispatcher(
            memory_threshold_percent=80.0,  # Pause if memory exceeds this
            check_interval=1.0,             # How often to check memory
            max_session_permit=10,          # Maximum concurrent tasks
            rate_limiter=rate_limiter,
            monitor=monitor
        )
        sd = SemaphoreDispatcher(
            semaphore_count=self.max_sessions,
            rate_limiter=rate_limiter,
            monitor=monitor
        )
        for chunk in chunk_list(urls, self.max_sessions):
        #     results = await AsyncWebCrawler(config=self.browser_conf).arun_many(
        #         urls=chunk,
        #         config=CrawlerRunConfig(
        #             stream=False,
        #         ),
        #         rate_limiter=RateLimiter(       # Optional rate limiting
        #             base_delay=(1.0, 2.0),
        #             max_delay=30.0,
        #             max_retries=2
        #         ),
        #     )
        
            async with AsyncWebCrawler(config=browser_config) as crawler:
                results = await crawler.arun_many(
                    chunk, 
                    config=run_config,
                    dispatcher=md
                )
                for result in results:
                    if result.success:
                        self.save_to_json(result.url, result.markdown, result.success)
                    else:
                        print(f"Failed: {result.url}")

    async def process_url(self, url: str):
        """Process a single URL."""
        print(f"Processing URL: {url}")
        if url.endswith("sitemap.xml"):
            sitemap_urls = self.fetch_sitemap_urls(url)
            await self.process_urls(sitemap_urls)
        else:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
                self.save_to_json(result.url, result.markdown, result.success)

    
