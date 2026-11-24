# GovINTEL.AI – Intelligent NIC Code Finder

<p align="center">
  <img src="GovINTEL.AI.png" alt="GovINTEL.AI Logo" width="200"/>
</p>

<h3 align="center">AI-powered National Industrial Classification (NIC 2008) code recommendation</h3>

<p align="center">
  Describe a business in plain language — in any language — and get the five closest
  5-digit NIC codes, ranked by semantic similarity.
</p>

---

## Features

- **Semantic search** over all 1,304 five-digit NIC 2008 codes with Sentence Transformers (`all-MiniLM-L6-v2`), with a match score for every suggestion.
- **Any language**: descriptions are auto-translated to English (Google Translate via `deep-translator`).
- **Voice input**: record in the browser; speech is transcribed and placed in the search box.
- **Optional local LLM refinement**: Llama 3.2 1B Instruct (GPT4All) rewrites the description as industry keywords before searching. Off by default.
- **Bulk mode**: upload a CSV of companies, pick the description column, download the results.
- **NIC code manager**: browse/filter by division, add, edit and delete codes. Changes are used by the search immediately.
- **Database**: SQLite out of the box (zero setup) or Oracle via `python-oracledb`. Every search and contact message is stored.
- **Accessibility**: dyslexia-friendly font switch.

## Quick start

Requires **Python 3.10+**.

```bash
git clone https://github.com/rhythmkandhari/nic_code.git
cd nic_code
python -m venv venv
venv\Scripts\activate            # Windows  (macOS/Linux: source venv/bin/activate)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
streamlit run final.py
```

Open http://localhost:8501. On the first search the embedding model (~90 MB) is downloaded; after that, searches take about a second.
The database is created automatically at `data/govintel.db` and filled from `final_k/NIC_5digit.csv`.

Translation and speech recognition call Google's free web services, so they need internet access. If translation fails, the original text is searched.

### Using Oracle instead of SQLite (optional)

1. Create a dedicated database user (don't use `SYSTEM`) and run `sql/schema_oracle.sql` as that user.
2. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and set `backend = "oracle"`, `user`, `password`, `dsn`.
3. Start the app. The NIC codes are loaded into the table on first start.

`secrets.toml` is git-ignored, so credentials never reach GitHub.

## How it works

```text
description ──► translate to English ──► (optional) LLM keyword rewrite
                                                │
NIC_CODES table ──► embeddings (cached once) ───┤
                                                ▼
                                   cosine similarity ──► top-5 codes + scores
                                                │
                                                ▼
                                   saved to RESULT_CODES
```

## Project structure

```text
nic_code/
├── final.py                 # entrypoint: page config, DB init, navigation, shared sidebar
├── govintel/
│   ├── db.py                # SQLite / Oracle connection, init + seeding
│   ├── search.py            # embeddings, LLM refinement, translation, speech-to-text
│   └── ui.py                # logo + font selector shared by all pages
├── final_k/
│   ├── home.py              # search, voice input, bulk CSV
│   ├── NCI.py               # browse / add / edit / delete NIC codes
│   ├── About.py
│   ├── contact.py
│   └── NIC_5digit.csv       # NIC 2008 5-digit codes (seed data)
├── sql/
│   ├── schema_sqlite.sql    # applied automatically
│   └── schema_oracle.sql    # run once for Oracle
├── .streamlit/secrets.toml.example
└── requirements.txt
```

## Technology stack

| Category | Technologies |
|---|---|
| Language | Python |
| Frontend | Streamlit |
| Embeddings | Sentence Transformers – all-MiniLM-L6-v2 (PyTorch, CPU) |
| Optional LLM | GPT4All – Llama 3.2 1B Instruct (Q4_0) |
| Database | SQLite (default) or Oracle (python-oracledb) |
| Translation / speech | deep-translator, SpeechRecognition |
| Data | Pandas |

## Author

**Rhythm Kandhari** · GitHub: [@rhythmkandhari](https://github.com/rhythmkandhari)

Related model on Hugging Face: [Rhythm56786535/nic_code](https://huggingface.co/Rhythm56786535/nic_code)

---

<p align="center"><b>GovINTEL.AI – Making Industrial Classification Smarter.</b></p>
