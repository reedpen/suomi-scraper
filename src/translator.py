import json
import os
import time
import logging
from deep_translator import GoogleTranslator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranslatorService:
    def __init__(self, source_lang="fi", target_lang="en", cache_file="translation_cache.json"):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self.engine = GoogleTranslator(source=source_lang, target=target_lang)
        
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
        Fetches translation using deep-translator (Google).
        """
        word = word.strip().lower()
        if not word:
            return ""

        # Check cache first
        if word in self.cache:
            return self.cache[word]
            
        try:
            # Politeness delay (Google blocks if too fast)
            time.sleep(0.3) 
            
            logger.info(f"Translating: {word}")
            
            # GoogleTranslator call
            result = self.engine.translate(word)
            
            if not result or result == word:
                # Sometimes it returns same word if unknown.
                # We can't distinguish easily, but usually it works.
                pass

            self.cache[word] = result
            self._save_cache()
            return result

        except Exception as e:
            # 429 Too Many Requests etc.
            logger.error(f"Translation error for {word}: {e}")
            return "[Error]"

    def get_cache_as_list(self) -> list[dict]:
        """Returns the cache as a list of dicts for display."""
        return [{"Finnish": k, "English": v} for k, v in self.cache.items()]

    def clear_cache(self):
        """Clears the in-memory cache and deletes the cache file."""
        self.cache = {}
        if os.path.exists(self.cache_file):
            try:
                os.remove(self.cache_file)
                logger.info("Cache file deleted.")
            except Exception as e:
                logger.error(f"Failed to delete cache file: {e}")

if __name__ == "__main__":
    t = TranslatorService()
    words = ["koira", "talo", "epäonnistua", "vilpitön"]
    for w in words:
        print(f"{w} -> {t.translate(w)}")
