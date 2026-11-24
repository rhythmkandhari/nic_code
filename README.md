# GovINTEL.AI – Intelligent NIC Code Finder

<p align="center">
  <img src="GovINTEL.AI.png" alt="GovINTEL.AI Logo" width="200"/>
</p>

<h3 align="center">AI-Powered National Industrial Classification Code Recommendation System</h3>

<p align="center">
  An intelligent application that leverages Large Language Models and Semantic Search to identify relevant National Industrial Classification (NIC) codes from natural-language business descriptions.
</p>

---

## About the Project

**GovINTEL.AI** is an AI-powered NIC Code Finder designed to simplify the process of identifying appropriate National Industrial Classification codes for different business activities.

The application combines Large Language Models (LLMs), Natural Language Processing (NLP), and semantic similarity techniques to understand user-provided business descriptions and recommend the most relevant NIC codes.
## Hugging Face Model

The model used in GovINTEL.AI is hosted on Hugging Face:

[Rhythm56786535/nic_code](https://huggingface.co/Rhythm56786535/nic_code)

By moving beyond traditional keyword-based searching, GovINTEL.AI provides a more intuitive way to explore industrial classifications through natural-language queries.

## Key Features

- **Intelligent NIC Code Search:** Identify relevant NIC codes using natural-language business descriptions.
- **LLM-Powered Query Understanding:** Utilizes a locally available language model to understand and refine business queries.
- **Semantic Search:** Uses Sentence Transformers to generate text embeddings and identify semantically relevant NIC descriptions.
- **Top-5 Recommendations:** Presents the five most relevant NIC code suggestions based on similarity matching.
- **Multilingual Query Support:** Facilitates business description searches through language translation.
- **Interactive Web Interface:** Provides an intuitive and user-friendly application built with Streamlit.
- **MongoDB Integration:** Supports application data management and user-related records through MongoDB.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Frontend | Streamlit |
| Large Language Model | GPT4All |
| Language Model | Llama 3.2 1B Instruct |
| NLP & Embeddings | Sentence Transformers |
| Embedding Model | all-MiniLM-L6-v2 |
| Deep Learning | PyTorch |
| Similarity Matching | Cosine Similarity |
| Database | MongoDB |
| Data Processing | Pandas, NumPy |
| Translation | Deep Translator |

## How It Works

GovINTEL.AI follows a semantic-search-based classification workflow:

1. **User Input:** The user enters a description of their business activity.
2. **Query Understanding:** The locally available LLM helps refine and understand the business description.
3. **Text Embedding:** Sentence Transformers converts the processed query into a numerical vector representation.
4. **Semantic Matching:** Cosine similarity measures the similarity between the query embedding and NIC activity descriptions.
5. **Ranking:** The matching results are ranked according to their similarity scores.
6. **Recommendations:** The application presents the top five relevant NIC codes to the user.

## System Architecture

```text
             USER
               |
               v
       STREAMLIT INTERFACE
               |
               v
       BUSINESS DESCRIPTION
               |
               v
       QUERY PROCESSING
               |
               v
        LOCAL LLM (GPT4All)
               |
               v
      SENTENCE TRANSFORMERS
               |
               v
       TEXT EMBEDDINGS
               |
               v
       COSINE SIMILARITY
               |
               v
        TOP-5 NIC RESULTS
               |
               v
        MONGODB DATABASE
```

## Project Structure

```text
nic_code/
│
├── final.py
│
├── final_k/
│   └── Application pages and supporting resources
│
├── GovINTEL.AI.png
├── govlogo.jpg
├── mospi.png
│
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.9 or above
- MongoDB
- Required Python libraries
- Locally available language model files

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/rhythmkandhari/nic_code.git
```

**2. Navigate to the project directory**

```bash
cd nic_code
```

**3. Install the required dependencies**

Install the Python packages used by the project in your environment, including Streamlit, PyMongo, GPT4All, Sentence Transformers, PyTorch and Pandas.

**4. Configure local resources**

Ensure that the locally available language model, NIC dataset and MongoDB connection are configured according to the application's existing settings.

**5. Run the application**

```bash
streamlit run final.py
```

## Application Preview

<p align="center">
  <img src="GovINTEL.AI.png" alt="GovINTEL.AI Application Branding" width="500"/>
</p>

## Project Highlights

- Integration of Large Language Models with semantic information retrieval.
- Application of NLP and vector embeddings to industrial classification.
- Local LLM integration for business-query understanding.
- Semantic similarity-based NIC code recommendations.
- MongoDB-backed application data management.
- Development of an interactive AI-powered classification application.

## Author

**Rhythm Kandhari**

GitHub: [@rhythmkandhari](https://github.com/rhythmkandhari)

**Project:** GovINTEL.AI – Intelligent NIC Code Finder

**Domain:** Artificial Intelligence | Natural Language Processing | Large Language Models | Semantic Search

---

<p align="center">
  <b>GovINTEL.AI – Making Industrial Classification Smarter.</b>
</p>
