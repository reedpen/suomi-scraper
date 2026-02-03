# Suomi Scraper 🇫🇮

A powerful tool to scrape Finnish texts (News, LDS Scriptures), lemmatize words to their base form (using **Voikko**), translate them to English (using **Deep Translator**), and export **Anki-ready flashcards**.

## ✨ Features

- **Multi-Source Scraping**: Support for generic Finnish websites (Yle, HS) and LDS Scriptures (recursive integration).
- **Intelligent NLP**: Converts inflected words (e.g., *'taloissa'*) to base forms (*'talo'*).
- **Smart Filtering**: Automatically removes names, places, and untranslated words.
- **Translation Caching**: Saves translations locally to speed up subsequent runs.
- **GUI & CLI**: Use the visual dashboard or the command line.

## 🚀 Setup

1.  **Install System Dependencies (LibVoikko)**
    *   **Mac**: `brew install libvoikko`
    *   **Ubuntu**: `sudo apt install libvoikko1 voikko-fi`

2.  **Install Python Deps**
    ```bash
    pip install -r requirements.txt
    ```

## 🖥️ Usage

### Graphical Interface (Recommended)
Launch the visual dashboard to scrape URLs, batch process list, and edit cards before downloading.

```bash
streamlit run gui.py
```

### Command Line

**Scrape a single article/page:**
```bash
python3 main.py "https://yle.fi/uutiset/osasto/selkouutiset/"
```

**Scrape an entire book (e.g., Pearl of Great Price):**
```bash
python3 main.py "https://www.churchofjesuschrist.org/study/scriptures/pgp?lang=fin" --recursive
```

**Scrape a list of URLs:**
```bash
python3 main.py --file my_links.txt
```

## 📂 Output

The script generates a semicolon-separated CSV (`anki_deck.csv`) ready for Anki import:
- **Front**: Finnish Base Word
- **Back**: English Translation
- **Tags**: suomi-scraper
