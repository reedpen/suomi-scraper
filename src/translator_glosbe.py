import requests
import time
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import json
import os

class GlosbeTranslator:
    def __init__(self, source_lang="fi", target_lang="en", cache_file="translation_cache.json"):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.base_url = f"https://glosbe.com/{source_lang}/{target_lang}"
        self.session = requests.Session()
        self.session.headers.update({
             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
             'Accept-Language': 'en-US,en;q=0.9',
        })
        self.cache_file = cache_file
        self.cache = self._load_cache()
        
    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
                return {}
        return {}
        
    def _save_cache(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def translate(self, word: str) -> str:
        """
        Fetches translation from Glosbe by scraping the HTML results page.
        """
        # Check cache first
        if word in self.cache:
            # logger.info(f"Cache hit for: {word}") 
            return self.cache[word]
            
        try:
            # Politeness delay
            time.sleep(0.5) 
            
            url = f"{self.base_url}/{word}"
            logger.info(f"Translating: {word}")
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 404:
                self.cache[word] = "[Not Found]"
                self._save_cache()
                return "[Not Found]"
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            result = "[No translation found]"
            
            # 1. Try finding 'translation__item__phrase' container (sometimes changed)
            trans_phrases = soup.select(".translation__item__phrase")
            if trans_phrases:
                result = trans_phrases[0].get_text(strip=True)
            else:    
                # 2. Fallback to H3 tags (heuristic)
                h3s = soup.find_all('h3')
                for h in h3s:
                    text = h.get_text(strip=True)
                    # Filter out likely UI headers if any (usually translations are short)
                    if text and len(text) < 50: 
                        result = text
                        break
                        
            if result == "[No translation found]":
                 logger.warning(f"No translation found for {word} (HTML parsed but no match)")
            
            self.cache[word] = result
            self._save_cache()
            return result

        except Exception as e:
            logger.error(f"Translation error for {word}: {e}")
            return "[Error]"

if __name__ == "__main__":
    gt = GlosbeTranslator()
    words = ["koira", "talo", "juosta", "asua"]
    for w in words:
        print(f"{w} -> {gt.translate(w)}")
