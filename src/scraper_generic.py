import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_generic(url: str) -> str:
    """
    Scrapes the main text content from a generic web page.
    Prioritizes text within <p> tags and common article containers.
    """
    try:
        logger.info(f"Fetching URL: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Remove unwanted elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.extract()
            
        # Strategy: extracting all paragraphs
        # This is a naive approach; could be improved with readability heuristics later
        text_blocks = []
        
        # Extract title
        if soup.title:
            text_blocks.append(soup.title.get_text())
            
        # Extract headings and paragraphs
        for element in soup.find_all(['h1', 'h2', 'h3', 'p']):
            text = element.get_text(strip=True)
            if text:
                text_blocks.append(text)
                
        full_text = "\n".join(text_blocks)
        logger.info(f"Extracted {len(full_text)} characters.")
        return full_text

    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return ""

if __name__ == "__main__":
    # Test with a sample URL
    test_url = "https://yle.fi/a/74-20067645" # Example Yle article
    print(scrape_generic(test_url))
