import argparse
import logging
import csv
import time
from src.scraper_generic import scrape_generic
from src.scraper_lds import scrape_lds_chapter
from src.nlp_processor import VoikkoProcessor
from src.translator import TranslatorService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from src.crawler import LDSCrawler

def main():
    parser = argparse.ArgumentParser(description="Suomi Scraper & Anki Deck Builder")
    parser.add_argument("url", nargs="?", help="URL to scrape (optional if --file is used)")
    parser.add_argument("--output", default="anki_deck.csv", help="Output CSV file (semicolon separated)")
    parser.add_argument("--no-translate", action="store_true", help="Skip translation step (dry run)")
    parser.add_argument("--file", help="Text file with list of URLs to scrape (one per line)")
    parser.add_argument("--recursive", action="store_true", help="Recursively find chapters from the provided URL")
    args = parser.parse_args()
    
    urls = []
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
    elif args.url:
        if args.recursive:
            logger.info("Recursive mode enabled. Crawling for chapters...")
            crawler = LDSCrawler()
            urls = crawler.crawl(args.url)
            logger.info(f"Recursive crawl finished. Found {len(urls)} URLs.")
        else:
            urls = [args.url]
    else:
        parser.error("Must provide either URL or --file")

    # 1. Initialize Components
    logger.info("Initializing components...")
    try:
        vp = VoikkoProcessor()
        translator = TranslatorService()
    except Exception as e:
        logger.critical(f"Initialization failed: {e}")
        return

    # 2. Scrape Content

    # 2. Scrape Content
    # Iterate over all URLs and collect all sentences
    all_sentences = []
    
    for i, url in enumerate(urls):
        logger.info(f"Processing URL {i+1}/{len(urls)}: {url}")
        
        sentences = []
        if "churchofjesuschrist.org" in url:
            # logger.info("Detected LDS URL.")
            sentences = scrape_lds_chapter(url)
        else:
            # logger.info("Generic URL detected.")
            raw_text = scrape_generic(url)
            if raw_text:
                sentences = [s.strip() for s in raw_text.split('\n') if s.strip()]
        
        current_count = len(sentences)
        logger.info(f"  -> Found {current_count} segments.")
        all_sentences.extend(sentences)
        
        # Polite delay between scrapes if processing batch
        if len(urls) > 1:
            time.sleep(0.5)

    logger.info(f"Total: Found {len(all_sentences)} segments from {len(urls)} URLs.")
    
    # 3. Process Words & Build Cards
    sentences = all_sentences
    
    # 3. Process Words & Build Cards
    # We want unique words.
    # Strategy: Iterate through sentences, extract words, checking seen set.
    
    # 4. Process & Write incrementally
    logger.info(f"Processing and writing to {args.output}...")
    
    fieldnames = ["Front", "Back", "Tags"]
    
    seen_lemmas = set()
    
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        
        card_count = 0
        for i, sentence in enumerate(sentences):
            lemmas_in_sentence = vp.lemmatize(sentence)
            
            for lemma in lemmas_in_sentence:
                # Skip short words or unwanted
                if len(lemma) < 2 or lemma in seen_lemmas:
                    continue
                    
                seen_lemmas.add(lemma)
                
                # Translate
                translation = ""
                if not args.no_translate:
                    translation = translator.translate(lemma)
                else:
                    translation = "[SKIPPED]"
                
                if translation in ["[No translation found]", "[Not Found]", "[Error]"]:
                    logger.info(f"Skipping {lemma} (no translation found)")
                    continue
                
                # Create Card
                card = {
                    "Front": lemma,
                    "Back": translation,
                    "Tags": "suomi-scraper"
                }
                
                # Write immediately
                writer.writerow(card)
                f.flush() # Ensure it hits disk
                
                card_count += 1
                
                # Progress log
                if card_count % 10 == 0:
                    logger.info(f"Generated {card_count} cards...")

    logger.info(f"Done! Exported {card_count} cards.")

if __name__ == "__main__":
    main()
