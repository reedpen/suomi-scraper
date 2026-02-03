import streamlit as st
import pandas as pd
import time
import logging
import io

# Import core logic
from src.scraper_generic import scrape_generic
from src.scraper_lds import scrape_lds_chapter
from src.nlp_processor import VoikkoProcessor
from src.translator import TranslatorService

# Configure logging to capture in UI? 
# For now, standard logging, maybe redirect to st.empty() later if needed.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Suomi Scraper", layout="wide")

st.title("🇫🇮 Suomi Scraper & Anki Builder")

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("Settings")
    
    no_translate = st.checkbox("Disable Translation (Dry Run)", value=False)
    filter_names = st.checkbox("Filter Proper Nouns", value=True)
    filter_untranslated = st.checkbox("Filter Untranslated Words", value=True)
    
    st.info("System Requirements: LibVoikko must be installed on the host machine.")

# --- Main Area ---
tab1, tab2 = st.tabs(["Single URL", "Batch Processing"])

urls_to_process = []

from src.crawler import LDSCrawler

# ... imports ...

with tab1:
    url_input = st.text_input("Enter URL to scrape:", placeholder="https://yle.fi/uutiset/...")
    recursive_mode = st.checkbox("Recursive Crawl (Find all chapters from this URL)", value=False)
    
    if url_input:
        if recursive_mode and "churchofjesuschrist.org" in url_input:
             st.info("Recursive mode active. Will crawl for chapters on start.")
             # Logic needs to happen on button press to avoid lag
             urls_to_process = [url_input] # Placeholder, will expand later
        else:
             urls_to_process = [url_input]

with tab2:
    batch_input = st.text_area("Enter URLs (one per line):", height=200, placeholder="https://site1.com\nhttps://site2.com")
    if batch_input:
        urls_to_process = [line.strip() for line in batch_input.split('\n') if line.strip()]

# --- Action ---
if st.button("Start Scraping", type="primary", disabled=not urls_to_process):
    
    # Initialize Components
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # Pre-flight: Recursive Crawl
    if recursive_mode and url_input and urls_to_process == [url_input]:
        status_text.text("Recursively crawling for chapters... (this may take a moment)")
        crawler = LDSCrawler()
        urls_to_process = crawler.crawl(url_input)
        if not urls_to_process:
            st.error("No chapters found in recursive crawl.")
            st.stop()
        st.success(f"Found {len(urls_to_process)} chapters.")
        time.sleep(1)

    status_text.text("Initializing NLP and Translator...")
    try:
        vp = VoikkoProcessor()
        translator = TranslatorService()
    except Exception as e:
        st.error(f"Failed to initialize components: {e}")
        st.stop()

    # Data collection
    all_cards = []
    seen_lemmas = set()
    
    total_steps = len(urls_to_process)
    
    # 1. Scrape & Process Loop
    for i, url in enumerate(urls_to_process):
        progress = (i / total_steps)
        progress_bar.progress(progress)
        status_text.text(f"Processing ({i+1}/{total_steps}): {url}")
        
        # Scrape
        sentences = []
        try:
            if "churchofjesuschrist.org" in url:
                sentences = scrape_lds_chapter(url)
            else:
                raw = scrape_generic(url)
                if raw:
                    sentences = [s.strip() for s in raw.split('\n') if s.strip()]
        except Exception as e:
            st.error(f"Error scraping {url}: {e}")
            continue

        # Process words
        for sentence in sentences:
            lemmas = vp.lemmatize(sentence) # This now includes name filtering if configured in NLP? 
            # Note: The NLP processor logic currently filters names hardcoded. 
            # If we want to toggle it via UI, we might need to modify VoikkoProcessor to accept a flag.
            # For now, it respects the current codebase logic which filters names.
            
            for lemma in lemmas:
                if len(lemma) < 2 or lemma in seen_lemmas:
                    continue
                seen_lemmas.add(lemma)
                
                # Translation
                translation = ""
                if not no_translate:
                    translation = translator.translate(lemma)
                else:
                    translation = "[SKIPPED]"
                
                # Filter untranslated
                if filter_untranslated and translation in ["[No translation found]", "[Not Found]", "[Error]"]:
                    continue
                    
                card = {
                    "Front": lemma,
                    "Back": translation,
                    "Tags": "suomi-scraper"
                }
                all_cards.append(card)
        
        # Politeness
        if len(urls_to_process) > 1:
            time.sleep(0.5)

    progress_bar.progress(1.0)
    status_text.text("Processing Complete!")
    
    # Store in session state to persist after reload (if any)
    st.session_state['cards'] = all_cards

# --- Results & Export ---
if 'cards' in st.session_state and st.session_state['cards']:
    st.write("### Review Cards")
    st.caption("You can edit translations directly in the table below.")
    
    df = pd.DataFrame(st.session_state['cards'])
    
    # Editable Table
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    
    # Convert to CSV for download
    csv = edited_df.to_csv(sep=';', index=False).encode('utf-8')
    
    st.download_button(
        label="Download Anki Deck (CSV)",
        data=csv,
        file_name="anki_deck.csv",
        mime="text/csv",
    )
elif 'cards' in st.session_state:
    st.warning("No valid cards found. Check your URLs or filters.")
