# Suomi Scraper

A tool to scrape Finnish texts (News, LDS Scriptures), lemmatize words to their base form (using **Voikko**), translate them to English (using **Deep Translator**), and export **Anki-ready flashcards**.

## Features

- **Multi-Source Scraping**: Support for generic Finnish websites (Yle, HS) and LDS Scriptures (recursive integration).
- **Document Support**: Scrape text from local **PDF**, **DOCX**, and **TXT** files.
- **Strict Logic**: Automatically enforces Finnish-only filtering, discarding foreign words (e.g., English) that cannot be analyzed.
- **Vocabulary Viewer**: View your local translation cache directly.
- **Append Mode**: Add new cards to an existing deck instead of starting over.
- **Intelligent NLP**: Converts inflected words (e.g., *'taloissa'*) to base forms (*'talo'*).
- **Smart Filtering**: Automatically removes names, places, and untranslated words.
- **Translation Caching**: Saves translations locally to speed up subsequent runs.
- **GUI & CLI**: Use the visual dashboard or the command line.

##  Setup

1.  **Install System Dependencies (LibVoikko)**
    *   **Mac**: `brew install libvoikko`
    *   **Ubuntu**: `sudo apt install libvoikko1 voikko-fi`

2.  **Install Python Deps**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Graphical Interface 
Launch the visual dashboard to scrape URLs, batch process list, and edit cards before downloading.

```bash
streamlit run gui.py
```

### Command Line

**Scrape a single article/page:**
```bash
python3 main.py "https://yle.fi/uutiset/osasto/selkouutiset/"
```

**Scrape an entire book (e.g., Book of Mormon):**
```bash
python3 main.py "https://www.churchofjesuschrist.org/study/scriptures/pgp?lang=fin" --recursive
```

**Scrape a list of URLs:**
```bash
python3 main.py --file my_links.txt
```

**Process a local document (PDF/DOCX/TXT):**
```bash
python3 main.py my_document.pdf
```

**Advanced Usage:**
```bash
# Append to existing file (merging results)
python3 main.py --file links.txt --output master_deck.csv --append

# View your vocabulary cache
python3 main.py --vocab

# Clear the cache (reset vocabulary)
python3 main.py --clear-cache
```

## 📂 Output

The script generates a semicolon-separated CSV (`anki_deck.csv`) ready for Anki import:
- **Front**: Finnish Base Word
- **Back**: English Translation
- **Tags**: suomi-scraper
