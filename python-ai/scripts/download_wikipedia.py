#!/usr/bin/env python3
import os
import sys
import logging
import requests
from pathlib import Path
from tqdm import tqdm
from data_processing.wikipedia_processor import WikipediaProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Wikipedia ZIM file URL (English Wikipedia, all articles, latest version)
WIKIPEDIA_ZIM_URL = "https://download.kiwix.org/zim/wikipedia/wikipedia_en_all_maxi.zim"
DATA_DIR = Path("data/wikipedia")


def download_file(url: str, destination: Path) -> bool:
    """
    Download a file with progress bar.

    Args:
        url: URL of the file to download
        destination: Path where to save the file

    Returns:
        True if download successful, False otherwise
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        block_size = 8192

        destination.parent.mkdir(parents=True, exist_ok=True)

        with open(destination, "wb") as f, tqdm(
            desc=destination.name,
            total=total_size,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for data in response.iter_content(block_size):
                size = f.write(data)
                pbar.update(size)

        return True
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return False


def main():
    # Create data directory if it doesn't exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    zim_path = DATA_DIR / "wikipedia_en_all_maxi.zim"

    # Download ZIM file if it doesn't exist
    if not zim_path.exists():
        logger.info("Downloading Wikipedia ZIM file...")
        if not download_file(WIKIPEDIA_ZIM_URL, zim_path):
            logger.error("Failed to download Wikipedia ZIM file")
            sys.exit(1)
        logger.info("Download complete!")
    else:
        logger.info("Wikipedia ZIM file already exists")

    # Initialize processor
    try:
        processor = WikipediaProcessor(str(zim_path))
        logger.info("Successfully initialized Wikipedia processor")

        # Test with a random article
        article = processor.get_random_article()
        if article:
            logger.info(f"Successfully processed test article: {article['title']}")
        else:
            logger.error("Failed to process test article")

    except Exception as e:
        logger.error(f"Error initializing Wikipedia processor: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
