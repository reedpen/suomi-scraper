import argparse
import logging
import csv
import time
import sys
from src.scraper_generic import scrape_generic
from src.scraper_lds import scrape_lds_chapter
from src.nlp_processor import VoikkoProcessor
from src.translator import TranslatorService
from src.document_loader import DocumentLoader

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
    parser.add_argument("--vocab", action="store_true", help="Print current vocabulary (translation cache)")
    parser.add_argument("--clear-cache", action="store_true", help="Clear the translation cache and exit")
    # parser.add_argument("--strict", action="store_true", help="Strict Mode: Discard words that Voikko cannot analyze (removes non-Finnish)")
    parser.add_argument("--append", action="store_true", help="Append to output file instead of overwriting")
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
    elif args.vocab or args.clear_cache:
        # Allow pass-through if only vocab/clear-cache is requested
        pass
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

    # 1b. Vocab View / Clear Cache
    if args.clear_cache:
        logger.info("Clearing vocabulary cache...")
        translator.clear_cache()
        logger.info("Cache cleared successfully.")
        return

    if args.vocab:
        logger.info("Dumping vocabulary cache...")
        vocab = translator.get_cache_as_list()
        print(f"--- Vocabulary ({len(vocab)} words) ---")
        # Print nicely or just CSV format to stdout
        writer = csv.DictWriter(sys.stdout, fieldnames=["Finnish", "English"], delimiter=';')
        writer.writeheader()
        writer.writerows(vocab)
        return

    # 2. Scrape Content
    # Iterate over all URLs and collect all sentences
    all_sentences = []
    
    for i, url in enumerate(urls):
        logger.info(f"Processing URL {i+1}/{len(urls)}: {url}")
        
        sentences = []
        try:
             # Check if local file (CLI file mode)
             # Note: current 'url' variable is just a string from the list.
             # We need to detect if it's a file path.
             import os
             if os.path.exists(url) and (url.endswith('.pdf') or url.endswith('.docx') or url.endswith('.txt')):
                 loader = DocumentLoader()
                 raw = loader.load_file(url, url)
                 sentences = [s.strip() for s in raw.split('\n') if s.strip()]
             
             elif "churchofjesuschrist.org" in url:
                 sentences = scrape_lds_chapter(url)
             else:
                 # Generic URL detected
                 raw_text = scrape_generic(url)
                 if raw_text:
                     sentences = [s.strip() for s in raw_text.split('\n') if s.strip()]

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            continue
        
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
    
    # Determine mode and whether to write header
    file_mode = 'a' if args.append else 'w'
    write_header = True
    if args.append and os.path.exists(args.output):
        # If appending to existing file, don't write header
        write_header = False

    with open(args.output, file_mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        if write_header:
            writer.writeheader()
        
        card_count = 0
        for i, sentence in enumerate(sentences):
            lemmas_in_sentence = vp.lemmatize(sentence) # Default is now strict=True
            
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
