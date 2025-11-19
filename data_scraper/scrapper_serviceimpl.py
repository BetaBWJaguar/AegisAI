# -*- coding: utf-8 -*-
from typing import List, Dict
import time

from data_scraper.scrapper_logging import ScrapeLogger
from data_scraper.scrapper_service import ScrapperService
from data_scraper.sites.reddit_scrapper import RedditScrapper
from data_scraper.scrapper_cache import ScrapperCache


class ScrapperServiceImpl(ScrapperService):
    def __init__(self, reddit_config: dict):
        self.reddit_scrapper = RedditScrapper(
            user_agent=reddit_config["user_agent"]
        )
        self.cache = ScrapperCache(ttl=3600)
        self.logger = ScrapeLogger()

    def scrape_reddit(self, query: str, limit: int = 50, subreddits: List[str] = None) -> List[Dict[str, str]]:
        start_time = time.time()

        cached = self.cache.get(query, limit, subreddits)
        if cached:
            self.logger.log({
                "status": "cached",
                "platform": "reddit",
                "query": query,
                "result_count": len(cached),
                "source": "cache"
            })
            return cached

        try:
            data = self.reddit_scrapper.fetch(query=query, limit=limit, subreddits=subreddits)
            duration = round(time.time() - start_time, 2)
            self.logger.log_success(query, "reddit", len(data), duration)

            self.cache.set(query, limit, subreddits, data)

            return data[:limit]
        except Exception as e:
            self.logger.log_error(query, "reddit", str(e))
            raise
