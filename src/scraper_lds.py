import requests
from bs4 import BeautifulSoup
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_lds_chapter(url: str) -> list[str]:
    """
    Scrapes an LDS scripture chapter or General Conference talk.
    Returns a list of clean strings (one per verse/paragraph).
    """
    try:
        logger.info(f"Fetching LDS URL: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        extracted_texts = []
        
        # Strategy for Scriptures: look for paragraphs with class 'verse' or 'p' inside 'body-block'
        # The structure often changes, but usually verses are <p class="verse">
        
        # Remove footnotes and verse numbers from the entire soup first to clean it up
        for element in soup.select("sup.marker, span.verse-number, a.bookmark-anchor"):
            element.decompose() # Remove completely
            
        # Select verse paragraphs
        verses = soup.select("p.verse")
        
        if not verses:
             # Broader fallback: paragraphs inside role="main" or <main>
             verses = soup.select("main p, div[role='main'] p")
             
        # Filter out very short paragraphs which might be UI elements if we used broader selectors
        filtered_verses = []
        for v in verses:
             # Skip if it's likely a UI element (nav, footer check already done roughly but be safe)
             if v.find_parent(['nav', 'footer', 'header']):
                 continue
             text = v.get_text(strip=True)
             # Skip empty or very short lines (often UI artifacts) unless it's a very short verse
             if len(text) < 3: 
                continue
             filtered_verses.append(v)
             
        verses = filtered_verses

        for v in verses:
            text = v.get_text(separator=' ', strip=True)
            # Clean up extra spaces
            text = re.sub(r'\s+', ' ', text)
            if text:
                extracted_texts.append(text)
                
        logger.info(f"Extracted {len(extracted_texts)} segments.")
        return extracted_texts

    except Exception as e:
        logger.error(f"Error scraping LDS URL {url}: {e}")
        return []

def scrape_lds_parallel(url_fi: str) -> list[tuple[str, str]]:
    """
    Scrapes Finnish content and its English counterpart.
    Returns: List of (finnish_text, english_text) tuples.
    """
    # 1. Scrape Finnish
    fi_texts = scrape_lds_chapter(url_fi)
    
    # 2. Construct English URL
    # Replace 'lang=fin' with 'lang=eng'
    # If lang param is missing, append it (default is usually English but better explicit)
    if "lang=fin" in url_fi:
        url_en = url_fi.replace("lang=fin", "lang=eng")
    elif "?" in url_fi:
        url_en = url_fi + "&lang=eng"
    else:
        url_en = url_fi + "?lang=eng"
        
    logger.info(f"Derived English URL: {url_en}")
    
    # 3. Scrape English
    en_texts = scrape_lds_chapter(url_en)
    
    # 4. Zip results
    # Mismatch warning
    if len(fi_texts) != len(en_texts):
        logger.warning(f"Segment count mismatch! FI: {len(fi_texts)}, EN: {len(en_texts)}. Alignment may be off.")
        # We will zip to the shortest length to avoid crashes, but warn user
        
    pairs = list(zip(fi_texts, en_texts))
    return pairs

if __name__ == "__main__":
    # Test 1: 1 Nephi 1 (Finnish)
    url_scripture = "https://www.churchofjesuschrist.org/study/scriptures/bofm/1-ne/1?lang=fin"
    print(f"--- Testing Scripture: {url_scripture} ---")
    texts = scrape_lds_chapter(url_scripture)
    for i, t in enumerate(texts[:5]): # Print first 5
        print(f"[{i+1}] {t}")
        
    print("\n")
    
    # Test 2: General Conference (Finnish) - Validated URL
    url_gc = "https://www.churchofjesuschrist.org/study/general-conference/2024/04/11oaks?lang=fin" 
    print(f"--- Testing GC: {url_gc} ---")
    texts_gc = scrape_lds_chapter(url_gc)
    for i, t in enumerate(texts_gc[:5]):
        print(f"[{i+1}] {t}")
