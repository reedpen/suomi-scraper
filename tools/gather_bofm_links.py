import requests
from bs4 import BeautifulSoup
import logging
import re
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.churchofjesuschrist.org"
INDEX_URL = f"{BASE_URL}/study/scriptures/bofm?lang=fin"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_soup(url):
    time.sleep(0.5)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return BeautifulSoup(resp.content, 'lxml')
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None

def gather_links():
    soup = get_soup(INDEX_URL)
    if not soup:
        return []

    chapter_urls = []
    book_urls = []

    # 1. Provide initial scan of the Index
    for a in soup.find_all('a', href=True):
        href = a['href']
        # Filter strictly for BoM structure
        # Matches /study/scriptures/bofm/{book_code} or /study/scriptures/bofm/{book_code}/{chapter}
        # book_code usually lower-case, can contain numbers like 1-ne
        if '/study/scriptures/bofm/' not in href:
            continue
        
        # Exclude common non-scripture links in index (like title page, intro, etc if desired, but user said 'Entire' so maybe include them?)
        # User likely wants the text.
        # Let's verify format.
        
        full_url = href if href.startswith('http') else f"{BASE_URL}{href}"
        
        # Heuristic: Check if deep link (chapter) or book index
        # Chapter often ends in digits or has sub-parts
        parts = href.split('?')[0].split('/')
        # parts usually ['', 'study', 'scriptures', 'bofm', '1-ne'] -> length 5 (Book)
        # ['', 'study', 'scriptures', 'bofm', '1-ne', '1'] -> length 6 (Chapter)
        
        relevant_parts = [p for p in parts if p]
        # relevant: ['study', 'scriptures', 'bofm', '1-ne'] -> len 4
        
        if len(relevant_parts) == 4:
            # Likely a book index (e.g., 1-ne)
            # Verify it's not 'title-page' etc. unless we want those.
            if any(x in href for x in ['title-page', 'introduction', 'bofm-title', 'three', 'eight', 'pronunciation']):
                 # Intro pages. Let's include them if they have text?
                 # Standard chapters are safest.
                 pass
            elif full_url not in book_urls:
                book_urls.append(full_url)
        elif len(relevant_parts) == 5:
            # Likely a chapter (e.g., 1-ne/1)
            if full_url not in chapter_urls:
                chapter_urls.append(full_url)

    logger.info(f"Found {len(book_urls)} potential book indices and {len(chapter_urls)} direct chapters.")

    # 2. Visit Book Indices to get chapters
    for book_url in book_urls:
        logger.info(f"Scanning Book Index: {book_url}")
        b_soup = get_soup(book_url)
        if not b_soup:
            continue
            
        for a in b_soup.find_all('a', href=True):
             href = a['href']
             if '/study/scriptures/bofm/' not in href:
                 continue
             
             parts = href.split('?')[0].split('/')
             relevant = [p for p in parts if p]
             
             # Should be length 5 for chapters
             if len(relevant) == 5:
                 full_url = href if href.startswith('http') else f"{BASE_URL}{href}"
                 if full_url not in chapter_urls:
                     chapter_urls.append(full_url)

    # Dedup
    chapter_urls = list(set(chapter_urls))
    
    # Sort for niceness (by URL)
    # A generic sort might put 1-ne/10 before 1-ne/2, but acceptable.
    chapter_urls.sort()
    
    return chapter_urls

if __name__ == "__main__":
    links = gather_links()
    logger.info(f"Total Unique Chapters found: {len(links)}")
    
    with open("bofm_links.txt", "w") as f:
        for l in links:
            f.write(l + "\n")
