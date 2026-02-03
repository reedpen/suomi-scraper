import unittest
import logging
from src.scraper_generic import scrape_generic

# Configure logging to see output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestNewsScrapers(unittest.TestCase):

    def test_yle_article(self):
        url = "https://yle.fi/a/74-20153635" # Corrected URL format if needed, user provided "20-153635" which is valid for Yle new format
        # User link: https://yle.fi/a/20-153635
        # Let's use the exact link provided.
        url = "https://yle.fi/a/20-153635"
        
        logger.info(f"Testing Yle: {url}")
        content = scrape_generic(url)
        
        self.assertIsNotNone(content, "Content should not be None")
        self.assertTrue(len(content) > 100, "Content should be substantial")
        
        # Check for some known text if possible, or just print header
        snippet = content[:200].replace('\n', ' ')
        logger.info(f"Yle Snippet: {snippet}...")

    def test_hs_article(self):
        # Taking a recent HS article for testing generic scraping
        # We need a stable one. Let's try the front page or a known category if specific article is hard to find.
        # Or I can try a generic structure test.
        # Let's try to verify if it handles 'hs.fi' correctly (often paywalled/limited).
        url = "https://www.hs.fi/kotimaa/"
        
        logger.info(f"Testing HS (Category): {url}")
        content = scrape_generic(url)
        self.assertIsNotNone(content)
        self.assertTrue(len(content) > 100)
        logger.info(f"HS Snippet: {content[:200].replace('\n', ' ')}...")
        
    def test_is_article(self):
        url = "https://www.is.fi"
        logger.info(f"Testing Ilta-Sanomat: {url}")
        content = scrape_generic(url)
        self.assertIsNotNone(content)
        self.assertTrue(len(content) > 100)
        logger.info(f"IS Snippet: {content[:200].replace('\n', ' ')}...")

if __name__ == '__main__':
    unittest.main()
