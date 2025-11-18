# -*- coding: utf-8 -*-
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

from data_scraper.scrapperbase import ScrapperBase


class RedditScrapper(ScrapperBase):
    def __init__(self, user_agent: str):
        super().__init__("reddit")

        self.headers = {
            "User-Agent": user_agent
        }

    def fetch(self, query: str, limit: int = 50, subreddits: List[str] = None) -> List[Dict[str, str]]:
        if not subreddits:
            subreddits = ["all"]

        results = []

        for subreddit_name in subreddits:

            search_url = (
                f"https://old.reddit.com/r/{subreddit_name}/search/"
                f"?q={query}&restrict_sr=1&sort=relevance"
            )

            print("[INFO] Scraping:", search_url)

            try:
                response = requests.get(search_url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(response.text, "html.parser")

                posts = soup.select("div.search-result")
                count = 0

                for post in posts:
                    if count >= limit:
                        break

                    title_tag = post.select_one("a.search-title")
                    if not title_tag:
                        continue

                    title = title_tag.text.strip()
                    url = title_tag["href"]

                    snippet_tag = post.select_one("div.search-result-meta")
                    snippet = snippet_tag.text.strip() if snippet_tag else ""

                    clean_text = self.clean_text(f"{title}\n{snippet}")


                    results.append({
                        "source": "reddit",
                        "subreddit": subreddit_name,
                        "title": title,
                        "text": clean_text,
                        "url": url,
                        "score": None,
                        "num_comments": None,
                        "created_utc": None
                    })

                    count += 1
                    time.sleep(0.2)

            except Exception as e:
                print(f"[ERROR] Failed to scrape r/{subreddit_name}: {e}")

        return results
