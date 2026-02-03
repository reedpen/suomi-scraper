import requests
from bs4 import BeautifulSoup
import logging
import time
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class LDSCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.visited = set()

    def get_soup(self, url):
        time.sleep(0.3) # Fast but polite
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"Failed to fetch {url}: Status {resp.status_code}")
                return None
            return BeautifulSoup(resp.content, 'lxml')
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return None

    def crawl(self, start_url: str) -> list[str]:
        """
        Recursively finds "leaf" nodes (chapters) from a given start URL.
        Logic:
        1. Parse start URL.
        2. Find all links that are 'deeper' or 'sibling' in the same book/volume.
        3. If a link looks like a chapter (ends in number), keep it.
        4. If a link looks like a book index, recurse into it.
        """
        logger.info(f"Starting crawl from: {start_url}")
        
        # Heuristic: Base path (e.g., /study/scriptures/pgp)
        # We only want links that start with this path.
        if '?' in start_url:
            base_url_clean = start_url.split('?')[0]
        else:
            base_url_clean = start_url
            
        # If it ends in a number, it's a single chapter. Return it.
        # e.g .../1-ne/1
        if base_url_clean[-1].isdigit():
             return [start_url]

        # Otherwise, assume it's a container (Volume or Book)
        # We need a queue for BFS or just recursive DFS. BFS is safer for depth/cycles.
        
        found_chapters = set()
        to_visit = [start_url]
        self.visited = set()
        
        # Domain restrict
        domain = "https://www.churchofjesuschrist.org"
        
        while to_visit:
            current_url = to_visit.pop(0)
            if current_url in self.visited:
                continue
            self.visited.add(current_url)
            
            logger.info(f"Scanning: {current_url}")
            soup = self.get_soup(current_url)
            if not soup:
                continue
                
            links = soup.find_all('a', href=True)
            for a in links:
                href = a['href']
                
                # Convert relative to absolute
                full_url = urljoin(current_url, href)
                
                # Filter: Must be within the same scope as start_url (loosely)
                # e.g. if start is /pgp, we accept /pgp/moses, /pgp/abr, /pgp/moses/1
                # We do NOT want /bofm or /bible
                
                # Simple check: does full_url start with the base_path of the start_url?
                # start: .../bofm
                # link: .../bofm/1-ne  (YES)
                # link: .../bofm/1-ne/1 (YES)
                
                # Handle lang param if present in start_url
                if "?lang=fin" in start_url and "?lang=fin" not in full_url:
                    full_url += "?lang=fin"
                    
                path = full_url.split('?')[0]
                
                if not path.startswith(base_url_clean):
                    continue
                
                # Ignore non-content
                if any(x in path for x in ['title-page', 'introduction', 'illustrations', 'pronunciation']):
                    continue

                # Heuristic: Is it a chapter?
                # Chapters in LDS URL structure usually end in a number (e.g. /1) OR are a specific single page (harder to detect).
                # New Standard: Check segments.
                # /pgp (root) -> /pgp/moses (book) -> /pgp/moses/1 (chapter)
                
                segments = path.split('/')
                # Root: len = X
                # Book: len = X+1
                # Chapter: len = X+2 (usually)
                
                # Better Heuristic: 
                # If it links to something we haven't seen, add to visit.
                # BUT we need to distinguish "Container" from "Node".
                # Visually, chapters often have class "chapter-link" or similar? No, the DOM is messy.
                # URL structure is best.
                
                # If the last segment is numeric, it's definitely a chapter.
                if segments[-1].isdigit():
                    found_chapters.add(full_url)
                else:
                    # It's potential book/container.
                    # Limit recursion depth? 
                    # If we are at /pgp/moses, valid links are /pgp/moses/1.
                    # We don't want to re-add /pgp.
                    if full_url not in self.visited and full_url not in to_visit:
                         # Anti-loop: Ensure length is increasing or same? 
                         # Actually just rely on Visited set.
                         to_visit.append(full_url)
        
        results = list(found_chapters)
        results.sort()
        logger.info(f"Crawl complete. Found {len(results)} chapters.")
        return results

if __name__ == "__main__":
    c = LDSCrawler()
    # Test on PGP
    res = c.crawl("https://www.churchofjesuschrist.org/study/scriptures/pgp?lang=fin")
    print(f"Found {len(res)} chapters.")
    for r in res[:5]:
        print(r)
