from typing import List, Dict

from data_scraper.scrapper_service import ScrapperService
from data_scraper.sites.reddit_scrapper import RedditScrapper


class ScrapperServiceImpl(ScrapperService):
    def __init__(self, reddit_config: dict):
        self.reddit_scrapper = RedditScrapper(
            client_id=reddit_config["client_id"],
            client_secret=reddit_config["client_secret"],
            user_agent=reddit_config["user_agent"]
        )

    def scrape_reddit(self, query: str, limit: int = 50, subreddits: List[str] = None) -> List[Dict[str, str]]:
        return self.reddit_scrapper.fetch(query=query, limit=limit, subreddits=subreddits)
