# PLAN-suomi-scraper: Finnish Anki Deck Builder

## 1. Overview
A Python script to scrape Finnish text (specifically LDS scriptures and General Conference, plus generic sites), normalize words to their base forms (lemmatization), fetch English translations from Glosbe, and export the result as an Anki-compatible CSV format.

## 2. Technical Stack
- **Language**: Python 3.12+
- **Scraping**: `BeautifulSoup4` + `requests` (Lightweight, robust for static content like generic sites and standard HTML).
- **NLP (Finnish)**: `Voikko` (via `libvoikko`)
    - *Rationale*: Finnish is morphologically rich. `Snowball` is only a stemmer (truncated words), and `spaCy`'s Finnish models are often experimental. `Voikko` is the industry standard for accurate Finnish lemmatization and handling compound words.
- **Translation**: `glosbe-cli` (wrapper) or direct scraping of Glosbe.
- **Data Handling**: `pandas` (for CSV manipulation/deduplication).

## 3. Architecture
```mermaid
graph TD
    A[Input: Valid URL] --> B[Scraper Module]
    B -->|Raw Text| C[NLP Processor]
    C -->|Tokenize & Filter| D[Lemmatizer (Voikko)]
    D -->|Base Forms| E[Translation Engine (Glosbe)]
    B -.->|Parallel URL| B2[English Scraper]
    B2 -->|Context EN| F
    E -->|Pairs (FI:EN)| F[Anki Formatter]
    F --> G[Output: importable.csv]
```

## 4. Components

### A. Scraper Engine
- **Generic Scraper**: Extracts main body text from arbitrary URLs.
- **LDS Specific**: 
    - Targeted selectors (`p.verse`, `p` in content).
    - **Parallel Mode**: Derives English URL (`lang=eng`) to fetch matching verses.
    - *Benefit*: Provides massive context sentences for Anki cards.

### B. NLP Pipeline
- **Tokenization**: Split text into words.
- **Normalization**: Lowercase, remove punctuation.
- **Lemmatization**: Convert inflected forms (*taloissa*) to base forms (*talo*).
- **Filtering**: Remove common stopwords (and/is/the equivalent) if desired, or keep all unique words.

### C. Translation Service
- Connect to Glosbe.
- Rate limiting handling (politeness).
- Context selection (optional: grab first 2-3 meanings).

### D. Output Generator
- Format: `Front (Finnish);Back (English)`
- Anki compatibility check (UTF-8 encoding).

## 5. Task Breakdown

### Phase 1: Foundation
- [ ] **Task 1: Environment Setup**
    - INPUT: Fresh repo
    - OUTPUT: `requirements.txt` (bs4, requests, libvoikko), `README.md`
    - VERIFY: `pip install -r requirements.txt` succeeds.

- [ ] **Task 2: Basic Generic Scraper**
    - INPUT: URL (e.g., Yle news article)
    - OUTPUT: Clean extracted text list
    - VERIFY: Script prints text content without HTML tags.

- [ ] **Task 3: LDS-Specific Scraper**
    - INPUT: URL (e.g., Book of Mormon chapter)
    - OUTPUT: Clean verse text, excluding footnotes/headers.
    - VERIFY: Compare output against raw page to ensure verses are captured cleanly.

### Phase 2: NLP & Translation
- [ ] **Task 4: Voikko Integration**
    - INPUT: List of raw Finnish words ["menen", "taloissa"]
    - OUTPUT: List of base forms ["mennä", "talo"]
    - VERIFY: Python script correctly lemmatizes complex compound words.

- [ ] **Task 5: Glosbe Integration**
    - INPUT: Finnish base word "koira"
    - OUTPUT: English string "dog"
    - VERIFY: Script fetches valid translation for 5 test words.

### Phase 3: Assembly
- [ ] **Task 6: Pipeline Orchestration**
    - INPUT: URL
    - OUTPUT: Dictionary { "finnish": "english" }
    - VERIFY: End-to-end run tracks flow from URL to dictionary.

- [ ] **Task 7: Anki Export**
    - INPUT: Dictionary data
    - OUTPUT: `anki_output.csv` (semicolon separated)
    - VERIFY: Import into Anki desktop succeeds with cards created.

## 6. Phase X: Verification Checklist
- [ ] **LDS Content**: Scraper correctly handles General Conference layout.
- [ ] **Morphology**: "Koiramme" (our dog) -> "Koira" (dog).
- [ ] **Anki Import**: File imports without encoding errors (ä/ö chars).
- [ ] **Rate Limits**: Glosbe scraping doesn't get IP banned immediately (implement delays).
