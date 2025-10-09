import praw
import time
from typing import List, Dict

from data_scraper.scrapperbase import ScrapperBase


class RedditScrapper(ScrapperBase):
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        super().__init__("reddit")
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

    def fetch(self, query: str, limit: int = 50, subreddits: List[str] = None) -> List[Dict[str, str]]:
        if not subreddits:
            subreddits = ["all"]

        results = []

        for subreddit_name in subreddits:
            subreddit = self.reddit.subreddit(subreddit_name)

            try:
                for submission in subreddit.search(query, limit=limit):
                    text = f"{submission.title}\n{submission.selftext or ''}"
                    clean_text = self.clean_text(text)

                    results.append({
                        "source": "reddit",
                        "subreddit": subreddit_name,
                        "title": submission.title,
                        "text": clean_text,
                        "url": f"https://www.reddit.com{submission.permalink}",
                        "score": submission.score,
                        "num_comments": submission.num_comments,
                        "created_utc": submission.created_utc
                    })

                    time.sleep(0.2)

            except Exception as e:
                print(f"[ERROR] Failed to fetch from r/{subreddit_name}: {e}")
        return results
