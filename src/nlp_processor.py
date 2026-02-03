import logging
import re
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import libvoikko; handle failure gracefully so app doesn't crash on start
LIBVOIKKO_AVAILABLE = False
try:
    import libvoikko
    LIBVOIKKO_AVAILABLE = True
except ImportError:
    logger.warning("libvoikko python package not found.")
except OSError:
    logger.warning("libvoikko shared library not found.")

class VoikkoProcessor:
    def __init__(self, lang="fi"):
        if not LIBVOIKKO_AVAILABLE:
            raise RuntimeError("LibVoikko library not found. Please ensure it is installed (apt-get install libvoikko1 voikko-fi).")
            
        try:
            self.v = libvoikko.Voikko(lang)
            logger.info("Voikko initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Voikko: {e}")
            raise e

    def lemmatize(self, text: str, strict: bool = True) -> list[str]:
        """
        Tokenizes text and returns a list of base forms (lemmas).
        Filters out punctuation and numbers.
        Args:
            strict (bool): If True, discards words that Voikko cannot analyze (e.g., foreign words). Defaults to True.
        """
        # Simple tokenization: split by whitespace and strip punctuation
        # This is a basic approach; Voikko has tokenization but it's often easier to do custom regex for Anki decks
        
        # Remove punctuation characters
        clean_text = re.sub(r'[^\w\s]', '', text)
        words = clean_text.split()
        
        lemmas = []
        possible_name_classes = {'nimi', 'etunimi', 'sukunimi', 'paikannimi'}
        
        for word in words:
            # Skip numbers
            if word.isdigit():
                continue
            
            # Check capitalization before lowercasing for analysis
            is_capitalized = word[0].isupper()
            
            # Voikko analyzes case-insensitively usually if we pass lowercase, 
            # but for name detection often good to know original.
            # We'll analyze the lowercase version to find the lemma.
            analysis_list = self.v.analyze(word.lower())
            
            if analysis_list:
                # Check the first analysis result (usually the most probable)
                first_analysis = analysis_list[0]
                word_class = first_analysis.get('CLASS', '')
                
                # Filter out known names
                if word_class in possible_name_classes:
                    continue
                    
                base_form = first_analysis.get('BASEFORM', word.lower())
                lemmas.append(base_form)
            else:
                # If unknown (e.g., proper noun or foreign word)
                if strict:
                    # In strict mode, we drop EVERYTHING that Voikko doesn't recognize.
                    # This filters English words, typos, and names Voikko didn't catch.
                    continue

                # Normal mode heuristics
                if is_capitalized:
                    continue
                    
                # If unknown and not capitalized, we might keep it or drop it.
                # Let's keep it to be safe, might be a complex inflection Voikko missed (unlikely for Voikko)
                # or a typo.
                lemmas.append(word.lower())
                
        return lemmas

    def analyze_word(self, word: str) -> dict:
        """Returns full analysis for a single word."""
        results = self.v.analyze(word)
        if results:
            return results[0]
        return {}

if __name__ == "__main__":
    vp = VoikkoProcessor()
    
    test_sentence = "Minä asuin taloissa ja juoksin metsissä."
    print(f"Original: {test_sentence}")
    print(f"Lemmas: {vp.lemmatize(test_sentence)}")
    
    complex_word = "juoksisinko"
    print(f"Word: {complex_word} -> {vp.analyze_word(complex_word).get('BASEFORM')}")
