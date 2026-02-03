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
from src.document_loader import DocumentLoader

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
    # strict_mode = st.checkbox("Strict Mode (Finnish Only)", value=True, help="Discards any word Voikko cannot analyze. Removes English/Foreign words.")
    
    st.info("System Requirements: LibVoikko must be installed on the host machine.")

# --- Main Area ---
tab1, tab2, tab3, tab4 = st.tabs(["Single URL", "Batch Processing", "File Upload", "Vocabulary"])

urls_to_process = []
file_obj_to_process = None

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

with tab3:
    uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'docx', 'txt'])
    if uploaded_file:
        file_obj_to_process = uploaded_file
        file_name_to_process = uploaded_file.name
        # Clear others to avoid confusion?
        urls_to_process = [] 

with tab4:
    st.header("Vocabulary Cache")
    st.caption("All words previously translated and stored locally.")
    try:
        # We need a translator instance to get cache
        # Lazy init or just init it here?
        tmp_trans = TranslatorService()
        vocab_list = tmp_trans.get_cache_as_list()
        
        if vocab_list:
             v_df = pd.DataFrame(vocab_list)
             st.dataframe(v_df, width=1000) 
             st.metric("Total Words", len(vocab_list))
             
             if st.button("Clear Cache", type="primary", help="Permanently delete translation cache"):
                 tmp_trans.clear_cache()
                 st.success("Cache cleared!")
                 time.sleep(1)
                 st.rerun()

        else:
             st.info("Cache is empty.")
    except Exception as e:
        st.error(f"Could not load vocabulary: {e}")

# --- Action ---
# Enable button if URL list OR file is present
enable_start = bool(urls_to_process or file_obj_to_process)

if st.button("Start Scraping", type="primary", disabled=not enable_start):
    
    # Initialize Components
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    doc_loader = DocumentLoader() # Init loader
    
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
        if "LibVoikko" in str(e):
            st.error("Missing System Dependency: LibVoikko")
            st.warning("On Streamlit Cloud, make sure 'packages.txt' contains 'libvoikko1' and 'voikko-fi'.")
            st.stop()
        else:
            st.error(f"Failed to initialize components: {e}")
            st.stop()

    # Data collection
    all_cards = []
    seen_lemmas = set()
    
    # 1. Scrape & Process Loop
    # Adjust loop to handle either URLs OR the single file
    
    items_to_process = urls_to_process if urls_to_process else [file_name_to_process]
    total_steps = len(items_to_process)

    for i, item in enumerate(items_to_process):
        progress = (i / total_steps)
        progress_bar.progress(progress)
        status_text.text(f"Processing ({i+1}/{total_steps}): {item}")
        
        # Scrape / Load
        sentences = []
        try:
            if file_obj_to_process and item == file_name_to_process:
                # IT'S A FILE
                raw_text = doc_loader.load_file(file_obj_to_process, file_name_to_process)
                sentences = [s.strip() for s in raw_text.split('\n') if s.strip()]
            
            elif "churchofjesuschrist.org" in item:
                sentences = scrape_lds_chapter(item)
            else:
                raw = scrape_generic(item)
                if raw:
                    sentences = [s.strip() for s in raw.split('\n') if s.strip()]
        except Exception as e:
            st.error(f"Error processing {item}: {e}")
            continue

        # Process words
        for sentence in sentences:
            lemmas = vp.lemmatize(sentence) # Default is now strict=True
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
    edited_df = st.data_editor(df, num_rows="dynamic", width=1000)
    
    # Merge Option
    st.divider()
    st.subheader("Merge with Existing Deck")
    merge_file = st.file_uploader("Upload existing CSV to append new cards to:", type=["csv"])
    
    final_df = df
    if merge_file:
        try:
            existing_df = pd.read_csv(merge_file, sep=';')
            st.info(f"Loaded existing deck with {len(existing_df)} cards.")
            
            # Concat
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            # Remove duplicates based on 'Front'?
            combined_df.drop_duplicates(subset=['Front'], keep='last', inplace=True) # Keep new ones? Or old? Let's keep last (newest)
            
            st.success(f"Merged! Total cards: {len(combined_df)}")
            final_df = combined_df
        except Exception as e:
            st.error(f"Error merging files: {e}")

    # Convert to CSV for download
    csv = final_df.to_csv(sep=';', index=False).encode('utf-8')
    
    st.download_button(
        label="Download Anki Deck (CSV)",
        data=csv,
        file_name="anki_deck_merged.csv" if merge_file else "anki_deck.csv",
        mime="text/csv",
    )
elif 'cards' in st.session_state:
    st.warning("No valid cards found. Check your URLs or filters.")
