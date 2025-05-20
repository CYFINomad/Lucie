import os
from pathlib import Path
from typing import Generator, Optional
import logging
from kiwix import Kiwix
from bs4 import BeautifulSoup
import lxml.etree as etree

logger = logging.getLogger(__name__)


class WikipediaProcessor:
    def __init__(self, zim_path: str):
        """
        Initialize the Wikipedia processor with a Kiwix ZIM file.

        Args:
            zim_path: Path to the ZIM file containing Wikipedia content
        """
        self.zim_path = Path(zim_path)
        if not self.zim_path.exists():
            raise FileNotFoundError(f"ZIM file not found at {zim_path}")

        self.kiwix = Kiwix(str(self.zim_path))

    def process_article(self, article_url: str) -> Optional[dict]:
        """
        Process a single Wikipedia article.

        Args:
            article_url: The URL of the article to process

        Returns:
            Dictionary containing processed article data or None if article not found
        """
        try:
            content = self.kiwix.get_article(article_url)
            if not content:
                return None

            # Parse HTML content
            soup = BeautifulSoup(content, "lxml")

            # Extract main content
            main_content = soup.find("div", {"id": "mw-content-text"})
            if not main_content:
                return None

            # Remove unwanted elements
            for element in main_content.find_all(["sup", "div", "table"]):
                element.decompose()

            # Extract text
            text = main_content.get_text(separator=" ", strip=True)

            # Extract title
            title = soup.find("h1", {"id": "firstHeading"})
            title_text = title.get_text() if title else article_url

            return {"title": title_text, "content": text, "url": article_url}

        except Exception as e:
            logger.error(f"Error processing article {article_url}: {str(e)}")
            return None

    def get_all_articles(self) -> Generator[dict, None, None]:
        """
        Generator that yields all articles from the ZIM file.

        Yields:
            Dictionary containing processed article data
        """
        for article_url in self.kiwix.get_article_urls():
            article_data = self.process_article(article_url)
            if article_data:
                yield article_data

    def get_random_article(self) -> Optional[dict]:
        """
        Get a random article from the ZIM file.

        Returns:
            Dictionary containing processed article data or None if no articles found
        """
        try:
            random_url = self.kiwix.get_random_article_url()
            if random_url:
                return self.process_article(random_url)
        except Exception as e:
            logger.error(f"Error getting random article: {str(e)}")
        return None
